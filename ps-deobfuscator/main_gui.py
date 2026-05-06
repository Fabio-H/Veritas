#!/usr/bin/env python3
"""
Launch the PySide6 desktop GUI for ps-deobfuscator.

Usage (from the ps-deobfuscator directory):
  pip install -e ".[gui]"
  python main_gui.py
"""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def main() -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtWidgets import QApplication

    from gui.app_icon import load_application_icon
    from gui.main_window import MainWindow
    from gui.themes import apply_theme
    from ps_deobfuscator.app_info import APP_NAME, APP_VERSION

    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setApplicationVersion(APP_VERSION)
    app.setOrganizationName(APP_NAME)
    app_icon = load_application_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    apply_theme(app)
    win = MainWindow()
    win.show()
    raise SystemExit(app.exec())


def run_app() -> None:
    """Entry point for setuptools console_scripts."""
    main()


if __name__ == "__main__":
    main()
