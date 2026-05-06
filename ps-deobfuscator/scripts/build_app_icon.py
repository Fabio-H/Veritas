#!/usr/bin/env python3
"""
Render ``gui/resources/app_icon.svg`` into ``gui/resources/app_icon.ico``.

Requires PySide6 (QtSvg) and Pillow. Run from repo root:

  python scripts/build_app_icon.py
"""

from __future__ import annotations

import os
import sys
import tempfile
from io import BytesIO
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))


def _qimage_to_png_bytes(img: object) -> bytes | None:
    """Encode QImage to PNG bytes; QIODevice path first, temp-file fallback for picky PySide6 builds."""
    from PySide6.QtCore import QBuffer, QByteArray, QIODevice

    blob = QByteArray()
    buf = QBuffer(blob)
    if not buf.open(QIODevice.OpenModeFlag.WriteOnly | QIODevice.OpenModeFlag.Truncate):
        return None
    fmt = QByteArray(b"PNG")
    try:
        ok = img.save(buf, fmt, -1)
    except (TypeError, ValueError):
        ok = False
    buf.close()
    if ok and blob.size() > 0:
        return bytes(blob)

    fd, path_str = tempfile.mkstemp(suffix=".png")
    os.close(fd)
    path = Path(path_str)
    try:
        if not img.save(str(path)):
            return None
        return path.read_bytes()
    finally:
        path.unlink(missing_ok=True)


def main() -> int:
    try:
        from PIL import Image
    except ImportError:
        print("Install Pillow: pip install pillow", file=sys.stderr)
        return 1

    from PySide6.QtCore import QRectF, Qt
    from PySide6.QtGui import QImage, QPainter
    from PySide6.QtSvg import QSvgRenderer

    svg = _ROOT / "gui" / "resources" / "app_icon.svg"
    out = _ROOT / "gui" / "resources" / "app_icon.ico"
    if not svg.is_file():
        print(f"Missing {svg}", file=sys.stderr)
        return 1

    renderer = QSvgRenderer(str(svg))
    sizes = (16, 24, 32, 48, 64, 128, 256)
    images: list[Image.Image] = []

    for size in sizes:
        img = QImage(size, size, QImage.Format.Format_ARGB32)
        img.fill(Qt.GlobalColor.transparent)
        painter = QPainter(img)
        renderer.render(painter, QRectF(0, 0, size, size))
        painter.end()

        png_bytes = _qimage_to_png_bytes(img)
        if not png_bytes:
            print(f"Failed to encode {size}x{size} PNG", file=sys.stderr)
            return 1
        with Image.open(BytesIO(png_bytes)) as opened:
            images.append(opened.convert("RGBA").copy())

    first, *rest = images
    first.save(out, format="ICO", append_images=rest)
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
