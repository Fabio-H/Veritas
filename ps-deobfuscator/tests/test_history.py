from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ps_deobfuscator.engine import DecodeLayer, DecodeResult, IocRow
from ps_deobfuscator.history import (
    DEFAULT_MAX_ENTRIES,
    SCHEMA_VERSION,
    HistoryEntry,
    HistoryStore,
)


def _sample_result(tag: str = "x") -> DecodeResult:
    return DecodeResult(
        layers=(
            DecodeLayer("Raw input", f"raw-{tag}"),
            DecodeLayer("Base64 -> UTF-8", f"plain-{tag}"),
        ),
        final_text=f"plain-{tag}",
    )


def _sample_iocs(tag: str = "x") -> tuple[IocRow, ...]:
    return (
        IocRow("URL", f"http://example.com/{tag}", ""),
        IocRow("Domain", "example.com", "high"),
    )


def _make_entry(tag: str = "x") -> HistoryEntry:
    return HistoryEntry.from_decode(
        input_text=f"input-{tag}",
        result=_sample_result(tag),
        iocs=_sample_iocs(tag),
    )


class HistoryStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmpdir = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmpdir.cleanup)
        self.path = Path(self._tmpdir.name) / "history.json"

    def test_load_returns_empty_when_file_missing(self) -> None:
        store = HistoryStore(self.path)
        self.assertEqual(store.entries(), ())
        self.assertFalse(self.path.exists())

    def test_append_persists_and_round_trips(self) -> None:
        store = HistoryStore(self.path)
        entry = _make_entry("a")

        store.append(entry)

        self.assertTrue(self.path.exists())

        reloaded = HistoryStore(self.path)
        self.assertEqual(len(reloaded), 1)
        roundtrip = reloaded.entries()[0]

        self.assertEqual(roundtrip.id, entry.id)
        self.assertEqual(roundtrip.input, entry.input)
        self.assertEqual(roundtrip.final_text, entry.final_text)
        self.assertEqual(roundtrip.layers, entry.layers)
        self.assertEqual(roundtrip.iocs, entry.iocs)

    def test_to_decode_result_reconstructs_original_objects(self) -> None:
        result = _sample_result("rt")
        iocs = _sample_iocs("rt")
        entry = HistoryEntry.from_decode(input_text="payload", result=result, iocs=iocs)

        self.assertEqual(entry.to_decode_result(), result)
        self.assertEqual(entry.to_iocs(), iocs)

    def test_append_trims_to_max_entries_keeping_newest_first(self) -> None:
        store = HistoryStore(self.path, max_entries=3)

        ids = []
        for i in range(5):
            entry = _make_entry(str(i))
            store.append(entry)
            ids.append(entry.id)

        kept = store.entries()
        self.assertEqual(len(kept), 3)
        self.assertEqual([e.id for e in kept], [ids[4], ids[3], ids[2]])

        on_disk = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["max_entries"], 3)
        self.assertEqual(len(on_disk["entries"]), 3)

    def test_delete_removes_entry_and_persists(self) -> None:
        store = HistoryStore(self.path)
        first = _make_entry("a")
        second = _make_entry("b")
        store.append(first)
        store.append(second)

        store.delete(first.id)

        self.assertEqual([e.id for e in store.entries()], [second.id])
        reloaded = HistoryStore(self.path)
        self.assertEqual([e.id for e in reloaded.entries()], [second.id])

    def test_clear_empties_store_and_file(self) -> None:
        store = HistoryStore(self.path)
        store.append(_make_entry("a"))
        store.append(_make_entry("b"))

        store.clear()

        self.assertEqual(store.entries(), ())
        on_disk = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(on_disk["entries"], [])

    def test_corrupt_file_resets_to_empty_store(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text("{not valid json", encoding="utf-8")

        store = HistoryStore(self.path)

        self.assertEqual(store.entries(), ())

    def test_unknown_schema_version_is_ignored(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION + 99,
                    "entries": [_make_entry("a").to_dict()],
                }
            ),
            encoding="utf-8",
        )

        store = HistoryStore(self.path)

        self.assertEqual(store.entries(), ())

    def test_malformed_entry_is_skipped(self) -> None:
        valid = _make_entry("ok")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(
                {
                    "schema_version": SCHEMA_VERSION,
                    "entries": [
                        {"id": "broken"},
                        valid.to_dict(),
                    ],
                }
            ),
            encoding="utf-8",
        )

        store = HistoryStore(self.path)

        self.assertEqual([e.id for e in store.entries()], [valid.id])

    def test_atomic_save_leaves_no_tmp_when_replace_fails(self) -> None:
        store = HistoryStore(self.path)

        with patch("ps_deobfuscator.history.os.replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                store.append(_make_entry("a"))

        leftover = list(self.path.parent.glob(self.path.name + ".*.tmp"))
        self.assertEqual(leftover, [], f"leftover temp files: {leftover}")

    def test_default_max_entries_is_twenty(self) -> None:
        self.assertEqual(DEFAULT_MAX_ENTRIES, 20)


if __name__ == "__main__":
    unittest.main()
