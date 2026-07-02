#!/usr/bin/env python3
"""
Generate a local debug snapshot with the app's vital code.

This file is intended for local debugging only and should not be part of
release artifacts or version control history.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "local-debug"
OUT_FILE = OUT_DIR / "debug_vital_code.txt"

# Curated list of files that represent core app behavior.
VITAL_FILES = [
    "main_gui.py",
    "ps_deobfuscator/app_info.py",
    "ps_deobfuscator/engine.py",
    "ps_deobfuscator/cli.py",
    "ps_deobfuscator/history.py",
    "gui/main_window.py",
    "gui/widgets/decode_panel.py",
    "gui/widgets/history_panel.py",
    "tests/test_engine.py",
]


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        return f"[ERROR reading file: {exc}]"


def build_snapshot() -> str:
    ts = datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    parts: list[str] = []
    parts.append("Veritas local debug snapshot")
    parts.append(f"generated_at_utc: {ts}")
    parts.append(f"project_root: {ROOT}")
    parts.append("for_local_debug_only: true")
    parts.append("")

    for rel in VITAL_FILES:
        p = ROOT / rel
        parts.append("=" * 90)
        parts.append(f"FILE: {rel}")
        parts.append("=" * 90)
        parts.append(_read_text(p))
        parts.append("")

    return "\n".join(parts)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    OUT_FILE.write_text(build_snapshot(), encoding="utf-8")
    print(f"wrote: {OUT_FILE}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
