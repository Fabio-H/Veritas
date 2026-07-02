"""Bundled window / taskbar icon: ICO preferred; SVG rasterized when needed (Windows-friendly)."""

from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap


def _package_resources_dir() -> Path:
    """Directory containing ``app_icon.svg`` / ``app_icon.ico`` for this install."""
    here = Path(__file__).resolve().parent
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass:
            bundled = Path(meipass) / "gui" / "resources"
            if bundled.is_dir():
                return bundled
    return here / "resources"


def resolve_app_icon() -> Path | None:
    """
    Path to ``app_icon.ico`` or ``app_icon.svg`` if present.

    Prefer :func:`load_application_icon` for ``QIcon``; Windows often won't show SVG via
    ``QIcon(str(path))`` unless rasterized.
    """
    d = _package_resources_dir()
    for name in ("app_icon.ico", "app_icon.svg"):
        p = d / name
        if p.is_file():
            return p
    return None


def load_application_icon() -> QIcon:
    """
    Build a ``QIcon`` from bundled assets.

    - Uses multi-size ``.ico`` when available (best on Windows).
    - Otherwise rasterizes ``.svg`` with ``QSvgRenderer`` (PySide6) so the taskbar/title bar work.
    """
    d = _package_resources_dir()
    ico = d / "app_icon.ico"
    if ico.is_file():
        icon = QIcon(str(ico))
        if not icon.isNull():
            return icon

    svg = d / "app_icon.svg"
    if not svg.is_file():
        return QIcon()

    try:
        from PySide6.QtSvg import QSvgRenderer
    except ImportError:
        return QIcon(str(svg))

    renderer = QSvgRenderer(str(svg))
    if not renderer.isValid():
        return QIcon()

    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        pm = QPixmap(size, size)
        pm.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pm)
        renderer.render(painter, QRectF(0, 0, float(size), float(size)))
        painter.end()
        icon.addPixmap(pm)
    return icon
