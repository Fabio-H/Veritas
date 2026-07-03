# ps-deobfuscator (Veritas desktop)

Application **Python** / **PySide6** for recursive deobfuscation of PowerShell-oriented payloads (URL, Hex, Base64, GZIP, zlib) and IOC extraction. The decoding engine lives in `ps_deobfuscator/engine.py`.

## Quality gates

```bash
python -m unittest discover -s tests
python -c "import main_gui; print('ok')"
```

## Run from source

```bash
cd ps-deobfuscator
pip install -e ".[gui]"
python main_gui.py
```

Or after install: `ps-deobfuscator-gui` — registered as a **GUI script**, so it
opens the app directly with no console window. The `Veritas.lnk` shortcut
(repo root / Desktop) points to it with the app icon.

## Build Windows executable

Install build dependencies, then run **one** of:

```powershell
pip install -e ".[gui,dev,build]"
python scripts\build_exe.py
```

```powershell
.\build_windows.bat
```

```powershell
.\scripts\pyinstaller_gui.ps1
```

Outputs:

| Location | Description |
|----------|-------------|
| `ps-deobfuscator/dist/ps-deobfuscator-gui/` | PyInstaller output (full folder). |
| `../release/ps-deobfuscator-gui/` | Copy at repo root for easy access (whole folder required at runtime). |
| `../release/Veritas-vX.Y.Z-windows.zip` | Versioned release archive for sharing. |

Icons: `python scripts/build_app_icon.py` generates `gui/resources/app_icon.ico` from `app_icon.svg`.

## Clean build artifacts

```bash
python scripts/clean.py
python scripts/clean.py --dist
```

## CLI (no GUI)

```bash
pip install -e .
ps-deobfuscator decode --help
```

## Layout

```
ps-deobfuscator/
  main_gui.py          # Qt entry
  pyproject.toml
  ps_deobfuscator/     # Engine + CLI
  gui/                 # Themes, main window, widgets, resources (icons)
  scripts/             # build_app_icon, build_exe, clean, pyinstaller helper
  tests/               # unittest regression and smoke tests
```

## Safety defaults

- Static analysis only: payloads are decoded and inspected, never executed.
- Inputs larger than 1,000,000 characters are rejected to keep the app responsive.
- GZIP/zlib expansion is bounded to avoid accidental decompression bombs.
- TXT/JSON exports include app/version/timestamp metadata.

## Local-only scope

This project is desktop/CLI local software only. No web interface is required in this repository.

## Local debug snapshot

Generate an always-updated local TXT with the app's vital code:

```bash
python scripts/export_debug_vital.py
```

Output:
- `local-debug/debug_vital_code.txt`

This file is for local debugging only and is ignored by git.
