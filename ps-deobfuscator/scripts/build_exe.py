#!/usr/bin/env python3
"""
Build the Windows GUI bundle (PyInstaller) and copy it to PROJETO/release/ for easy access.

Run from ps-deobfuscator directory:
  python scripts/build_exe.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path


def _roots() -> tuple[Path, Path]:
    ps_deb = Path(__file__).resolve().parents[1]
    projeto = ps_deb.parent
    return ps_deb, projeto


def main() -> int:
    ps_deb, projeto = _roots()
    sys.path.insert(0, str(ps_deb))

    from ps_deobfuscator.app_info import APP_EXE_NAME, APP_NAME, APP_VERSION

    print("[1/5] build_app_icon.py ...")
    r = subprocess.run(
        [sys.executable, str(ps_deb / "scripts" / "build_app_icon.py")],
        cwd=ps_deb,
    )
    if r.returncode != 0:
        return r.returncode
    ico = ps_deb / "gui" / "resources" / "app_icon.ico"
    if not ico.is_file():
        print("warning: app_icon.ico missing; PyInstaller --icon may fail.", file=sys.stderr)

    print("[2/5] unit tests ...")
    r = subprocess.run(
        [sys.executable, "-m", "unittest", "discover", "-s", "tests"],
        cwd=ps_deb,
    )
    if r.returncode != 0:
        return r.returncode

    print("[3/5] import main_gui ...")
    r = subprocess.run(
        [sys.executable, "-c", "import main_gui; print('ok')"],
        cwd=ps_deb,
    )
    if r.returncode != 0:
        return r.returncode

    print("[4/5] PyInstaller ...")
    # Bundles the whole gui/resources tree, including resources/fonts/*.ttf
    # (Inter), so the embedded typography ships inside the .exe.
    add_data = (
        "gui/resources;gui/resources"
        if sys.platform == "win32"
        else "gui/resources:gui/resources"
    )
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--windowed",
        "--clean",
        "--name",
        APP_EXE_NAME,
        "--icon",
        str(ps_deb / "gui" / "resources" / "app_icon.ico"),
        "--add-data",
        add_data,
        "--collect-all",
        "PySide6",
        "--hidden-import",
        "PySide6.QtSvg",
        "--hidden-import",
        "ps_deobfuscator.engine",
        str(ps_deb / "main_gui.py"),
    ]

    r = subprocess.run(cmd, cwd=ps_deb)
    if r.returncode != 0:
        return r.returncode

    bundle = ps_deb / "dist" / APP_EXE_NAME
    if not bundle.is_dir():
        print(f"Expected bundle not found: {bundle}", file=sys.stderr)
        return 1

    print("[5/5] Copy to PROJETO/release/ and zip ...")
    release_dir = projeto / "release"
    release_root = release_dir / APP_EXE_NAME
    release_dir.mkdir(parents=True, exist_ok=True)
    if release_root.exists():
        shutil.rmtree(release_root)
    shutil.copytree(bundle, release_root)

    zip_base = release_dir / f"{APP_NAME}-v{APP_VERSION}-windows"
    zip_path = Path(f"{zip_base}.zip")
    if zip_path.exists():
        zip_path.unlink()
    shutil.make_archive(str(zip_base), "zip", root_dir=release_dir, base_dir=APP_EXE_NAME)

    exe = release_root / f"{APP_EXE_NAME}.exe"
    print(f"Done.\n  Source dist: {bundle}\n  Release copy: {exe}\n  Release zip: {zip_path}")
    if exe.is_file():
        print(f"  Executable size: {exe.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
