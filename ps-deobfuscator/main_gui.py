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


_SINGLE_INSTANCE_NAME = "veritas-ps-deobfuscator"


def main() -> None:
    from PySide6.QtCore import Qt
    from PySide6.QtNetwork import QLocalServer, QLocalSocket
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

    # Single instance: launching the shortcut again activates the running
    # window instead of opening a second copy.
    probe = QLocalSocket()
    probe.connectToServer(_SINGLE_INSTANCE_NAME)
    if probe.waitForConnected(200):
        probe.write(b"activate")
        probe.flush()
        probe.waitForBytesWritten(200)
        probe.disconnectFromServer()
        return
    QLocalServer.removeServer(_SINGLE_INSTANCE_NAME)  # clear stale socket
    server = QLocalServer()
    server.listen(_SINGLE_INSTANCE_NAME)

    # Dark native title bar on Windows (Qt 6.8+): the window frame matches
    # the app theme instead of staying white.
    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    except AttributeError:
        pass

    app_icon = load_application_icon()
    if not app_icon.isNull():
        app.setWindowIcon(app_icon)
    apply_theme(app)
    win = MainWindow()

    def _activate_existing_window() -> None:
        conn = server.nextPendingConnection()
        if conn is not None:
            conn.close()
        win.showNormal()
        win.raise_()
        win.activateWindow()

    server.newConnection.connect(_activate_existing_window)

    win.show()
    raise SystemExit(app.exec())


def run_app() -> None:
    """Entry point for setuptools console_scripts."""
    main()


if __name__ == "__main__":
    main()
