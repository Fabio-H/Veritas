#!/usr/bin/env python3
"""
Remove local build artifacts (__pycache__, .pytest_cache, PyInstaller work dirs).

Usage (from ps-deobfuscator):
  python scripts/clean.py
  python scripts/clean.py --dist     # also remove dist/ (next build is full)
  python scripts/clean.py --egg-info # remove *.egg-info (recreated by pip install -e)
"""
from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def _rm_tree(p: Path, dry: bool) -> None:
    if not p.exists():
        return
    if dry:
        print(f"would remove: {p}")
        return
    shutil.rmtree(p)
    print(f"removed: {p}")


def _rm_globs(root: Path, pattern: str, dry: bool) -> None:
    for p in root.glob(pattern):
        if p.is_dir():
            _rm_tree(p, dry)
        elif p.is_file() and not dry:
            p.unlink()
            print(f"removed: {p}")


def main() -> int:
    ap = argparse.ArgumentParser(description="Clean ps-deobfuscator build/cache artifacts.")
    ap.add_argument("--dist", action="store_true", help="Also delete dist/")
    ap.add_argument("--egg-info", action="store_true", help="Also delete *.egg-info")
    ap.add_argument("-n", "--dry-run", action="store_true")
    args = ap.parse_args()

    root = Path(__file__).resolve().parents[1]

    for name in ("build",):
        _rm_tree(root / name, args.dry_run)

    if args.dist:
        _rm_tree(root / "dist", args.dry_run)

    if args.egg_info:
        for egg in root.glob("*.egg-info"):
            _rm_tree(egg, args.dry_run)

    for sub in (root / "ps_deobfuscator", root / "gui", root):
        if sub.is_dir():
            _rm_globs(sub, "**/__pycache__", args.dry_run)

    cache = root / ".pytest_cache"
    _rm_tree(cache, args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
