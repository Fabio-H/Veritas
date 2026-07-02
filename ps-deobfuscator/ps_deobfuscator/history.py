"""
Session history store: persistent log of recent decode runs.

The store keeps the most recent decodings in a versioned JSON file under the
user's app-data location. Each entry holds a full snapshot (input, decode
layers, final text, IOCs) so the GUI can restore a past run without invoking
the decode engine again.

The module is intentionally Qt-free at runtime except for `default_history_path`,
which is the only function that touches `QStandardPaths`. This keeps the core
testable headless and matches the rule of not coupling business logic to the UI.
"""

from __future__ import annotations

import json
import os
import tempfile
import uuid
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from ps_deobfuscator.engine import DecodeLayer, DecodeResult, IocRow

SCHEMA_VERSION: int = 1
DEFAULT_MAX_ENTRIES: int = 20
_APP_FOLDER_NAME: str = "Veritas"
_HISTORY_FILENAME: str = "history.json"


@dataclass(frozen=True, slots=True)
class HistoryEntry:
    """One persisted decode run."""

    id: str
    timestamp: str
    input: str
    final_text: str
    layers: tuple[DecodeLayer, ...] = field(default_factory=tuple)
    iocs: tuple[IocRow, ...] = field(default_factory=tuple)

    @classmethod
    def from_decode(
        cls,
        *,
        input_text: str,
        result: DecodeResult,
        iocs: tuple[IocRow, ...],
    ) -> "HistoryEntry":
        return cls(
            id=uuid.uuid4().hex,
            timestamp=datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z"),
            input=input_text,
            final_text=result.final_text,
            layers=tuple(result.layers),
            iocs=tuple(iocs),
        )

    def to_decode_result(self) -> DecodeResult:
        return DecodeResult(layers=tuple(self.layers), final_text=self.final_text)

    def to_iocs(self) -> tuple[IocRow, ...]:
        return tuple(self.iocs)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "input": self.input,
            "final_text": self.final_text,
            "layers": [{"type": layer.type, "text": layer.text} for layer in self.layers],
            "iocs": [
                {"type": row.tipo, "value": row.valor, "confidence": row.confianca}
                for row in self.iocs
            ],
        }

    @classmethod
    def from_dict(cls, raw: dict[str, Any]) -> "HistoryEntry | None":
        """Build an entry from a JSON dict. Returns None if required fields are missing
        or have the wrong type; the store treats that as a corrupt record and skips it
        rather than crashing the GUI."""
        try:
            entry_id = str(raw["id"])
            timestamp = str(raw["timestamp"])
            input_text = str(raw["input"])
            final_text = str(raw["final_text"])

            raw_layers = raw.get("layers", [])
            if not isinstance(raw_layers, list):
                return None
            layers: list[DecodeLayer] = []
            for layer in raw_layers:
                if not isinstance(layer, dict):
                    return None
                layers.append(DecodeLayer(type=str(layer["type"]), text=str(layer["text"])))

            raw_iocs = raw.get("iocs", [])
            if not isinstance(raw_iocs, list):
                return None
            iocs: list[IocRow] = []
            for row in raw_iocs:
                if not isinstance(row, dict):
                    return None
                iocs.append(
                    IocRow(
                        tipo=str(row["type"]),
                        valor=str(row["value"]),
                        confianca=str(row.get("confidence", "")),
                    )
                )
        except (KeyError, TypeError, ValueError):
            return None

        return cls(
            id=entry_id,
            timestamp=timestamp,
            input=input_text,
            final_text=final_text,
            layers=tuple(layers),
            iocs=tuple(iocs),
        )


class HistoryStore:
    """Persistent ring buffer of recent decode runs, capped at `max_entries`.

    Newest entries come first. Disk writes are atomic (`tmp` + `os.replace`)
    so a crash mid-write cannot corrupt an existing history file.
    """

    def __init__(self, path: Path, max_entries: int = DEFAULT_MAX_ENTRIES) -> None:
        if max_entries < 1:
            raise ValueError("max_entries must be >= 1")
        self._path = Path(path)
        self._max_entries = max_entries
        self._entries: tuple[HistoryEntry, ...] = ()
        self.load()

    @property
    def path(self) -> Path:
        return self._path

    @property
    def max_entries(self) -> int:
        return self._max_entries

    def entries(self) -> tuple[HistoryEntry, ...]:
        return self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def load(self) -> tuple[HistoryEntry, ...]:
        """Read the history file. Tolerant of every failure mode: missing file,
        invalid JSON, unknown `schema_version`, or partially malformed records
        all reset the store to empty without raising."""
        if not self._path.exists():
            self._entries = ()
            return self._entries

        try:
            raw = self._path.read_text(encoding="utf-8")
            data = json.loads(raw)
        except (OSError, json.JSONDecodeError):
            self._entries = ()
            return self._entries

        if not isinstance(data, dict):
            self._entries = ()
            return self._entries

        if data.get("schema_version") != SCHEMA_VERSION:
            self._entries = ()
            return self._entries

        raw_entries = data.get("entries", [])
        if not isinstance(raw_entries, list):
            self._entries = ()
            return self._entries

        parsed: list[HistoryEntry] = []
        for raw_entry in raw_entries:
            if not isinstance(raw_entry, dict):
                continue
            entry = HistoryEntry.from_dict(raw_entry)
            if entry is not None:
                parsed.append(entry)

        self._entries = tuple(parsed[: self._max_entries])
        return self._entries

    def append(self, entry: HistoryEntry) -> tuple[HistoryEntry, ...]:
        """Prepend `entry`, trim to `max_entries`, persist, return updated tuple."""
        self._entries = (entry,) + self._entries
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[: self._max_entries]
        self._save_atomic()
        return self._entries

    def delete(self, entry_id: str) -> tuple[HistoryEntry, ...]:
        before = self._entries
        self._entries = tuple(e for e in self._entries if e.id != entry_id)
        if self._entries != before:
            self._save_atomic()
        return self._entries

    def clear(self) -> None:
        self._entries = ()
        self._save_atomic()

    def _save_atomic(self) -> None:
        """Serialize and replace the history file atomically.

        Writes go to a sibling temp file, then `os.replace` swaps it in. If
        the rename fails the temp file is removed so no stray `.tmp` is left
        behind on disk. The parent directory is created on demand because
        AppData/Veritas may not exist on first run."""
        payload = {
            "schema_version": SCHEMA_VERSION,
            "app": _APP_FOLDER_NAME,
            "max_entries": self._max_entries,
            "entries": [entry.to_dict() for entry in self._entries],
        }
        text = json.dumps(payload, indent=2, ensure_ascii=False)

        self._path.parent.mkdir(parents=True, exist_ok=True)

        tmp_fd, tmp_name = tempfile.mkstemp(
            prefix=self._path.name + ".",
            suffix=".tmp",
            dir=str(self._path.parent),
        )
        tmp_path = Path(tmp_name)
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as handle:
                handle.write(text)
            os.replace(tmp_path, self._path)
        except OSError:
            try:
                tmp_path.unlink(missing_ok=True)
            except OSError:
                pass
            raise


def default_history_path() -> Path:
    """Return the OS-appropriate path for the history file.

    Uses Qt's `QStandardPaths.AppDataLocation` so the file lands in the
    platform-conventional spot (Windows: `%APPDATA%\\Veritas`, Linux:
    `~/.local/share/Veritas`, macOS: `~/Library/Application Support/Veritas`).
    Falls back to the user home if Qt cannot resolve a writable location.
    """
    try:
        from PySide6.QtCore import QStandardPaths
    except ImportError:
        base = Path.home() / f".{_APP_FOLDER_NAME.lower()}"
    else:
        location = QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.AppDataLocation
        )
        if location:
            base = Path(location)
            if base.name.lower() != _APP_FOLDER_NAME.lower():
                base = base / _APP_FOLDER_NAME
        else:
            base = Path.home() / f".{_APP_FOLDER_NAME.lower()}"

    return base / _HISTORY_FILENAME
