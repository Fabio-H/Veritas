"""
Layout stress-test for the Veritas GUI.

Run from the ps-deobfuscator/ directory:

    python scripts/check_gui_layout.py

The script:
  1. Starts QApplication in offscreen (or software-raster) mode.
  2. Instantiates MainWindow.
  3. Resizes the window through a range of widths and heights.
  4. Asserts output body scroll viewport stays usable at common window sizes.
  5. Asserts that key widget pairs do not overlap.
  6. Prints a pass/fail summary with geometry diagnostics on failure.

Exit code 0 = all checks passed.
Exit code 1 = one or more checks failed.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

# ── resolve project root ───────────────────────────────────────────────────
_HERE = Path(__file__).resolve().parent
_ROOT = _HERE.parent
sys.path.insert(0, str(_ROOT))

# Force offscreen rendering so the script works on CI / headless environments.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QRect  # noqa: E402
from PySide6.QtWidgets import QApplication  # noqa: E402

# ── helpers ────────────────────────────────────────────────────────────────

_FAILURES: list[str] = []
_PASSES: int = 0


def _global_rect(widget) -> QRect:
    """Return widget's bounding rect in global (screen) coordinates."""
    tl = widget.mapToGlobal(widget.rect().topLeft())
    return QRect(tl, widget.size())


def _check_no_overlap(label_a: str, wa, label_b: str, wb) -> None:
    """Assert that two widgets' global rects do not intersect."""
    global _PASSES
    ra = _global_rect(wa)
    rb = _global_rect(wb)
    if ra.intersects(rb):
        _FAILURES.append(
            f"OVERLAP  {label_a} {ra}  ×  {label_b} {rb}"
        )
    else:
        _PASSES += 1


def _check_visible_and_positive(label: str, w) -> None:
    global _PASSES
    if not w.isVisible():
        _FAILURES.append(f"NOT VISIBLE  {label}")
        return
    if w.width() <= 0 or w.height() <= 0:
        _FAILURES.append(f"ZERO SIZE  {label}  {w.size()}")
    else:
        _PASSES += 1


def _process_events(app: QApplication) -> None:
    app.processEvents()
    app.processEvents()


# ── main ───────────────────────────────────────────────────────────────────

def main() -> int:
    global _PASSES
    app = QApplication(sys.argv)

    # Import after QApplication is created (some Qt bindings require this).
    from gui.main_window import MainWindow
    from gui.themes import apply_theme

    apply_theme(app)
    win = MainWindow()
    win.show()
    _process_events(app)

    panel = win._decode_panel  # type: ignore[attr-defined]

    # Convenient widget references
    input_edit = panel._input
    decode_btn = panel._decode_btn
    paste_btn = panel._paste_btn
    ioc_stack = panel._ioc_stack
    output_body_scroll = getattr(panel, "_output_body_scroll", None)

    # ── size matrix ────────────────────────────────────────────────────────
    sizes = [
        (860, 600),
        (960, 700),
        (1100, 800),
        (1280, 900),
        (1440, 1024),
        (860, 600),   # back to minimum
        (1920, 1080),
    ]

    for w, h in sizes:
        win.resize(w, h)
        _process_events(app)

        _check_visible_and_positive(f"input_edit @{w}x{h}", input_edit)
        _check_visible_and_positive(f"decode_btn @{w}x{h}", decode_btn)
        _check_visible_and_positive(f"paste_btn  @{w}x{h}", paste_btn)
        _check_no_overlap(
            f"input_edit @{w}x{h}", input_edit,
            f"decode_btn @{w}x{h}", decode_btn,
        )
        _check_no_overlap(
            f"input_edit @{w}x{h}", input_edit,
            f"paste_btn  @{w}x{h}", paste_btn,
        )

    # ── output IOC viewport / splitter-free layout ──────────────────────────
    if output_body_scroll is None:
        _FAILURES.append("DecodePanel missing _output_body_scroll attribute")
    else:
        win.resize(1280, 820)
        _process_events(app)
        vp0 = output_body_scroll.viewport().size()
        if vp0.height() < 140:
            _FAILURES.append(
                f"TINY OUTPUT VIEWPORT @1280x820  viewport_h={vp0.height()} viewport_w={vp0.width()}"
            )
        else:
            _PASSES += 1

        win.resize(1280, 520)
        _process_events(app)
        vp_small = output_body_scroll.viewport().size()
        if vp_small.height() < 72:
            _FAILURES.append(
                f"TINY OUTPUT VIEWPORT @short win  viewport_h={vp_small.height()} ioc_stack_h={ioc_stack.height()}"
            )

        win.resize(1280, 820)
        _process_events(app)

    # ── sidebar collapse/expand while at minimum window size ───────────────
    win.resize(860, 600)
    _process_events(app)

    win._toggle_sidebar()  # type: ignore[attr-defined]
    _process_events(app)
    _check_visible_and_positive("decode_btn (sidebar collapsed)", decode_btn)
    _check_no_overlap("input_edit (collapsed)", input_edit, "decode_btn (collapsed)", decode_btn)

    win._toggle_sidebar()  # type: ignore[attr-defined]
    _process_events(app)
    _check_visible_and_positive("decode_btn (sidebar expanded)", decode_btn)

    # ── results ────────────────────────────────────────────────────────────
    print(f"\nLayout check: {_PASSES} passed, {len(_FAILURES)} failed\n")
    for msg in _FAILURES:
        print(f"  FAIL  {msg}")

    return 1 if _FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
