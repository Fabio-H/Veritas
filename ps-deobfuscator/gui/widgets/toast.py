"""
Toast: transient confirmation message that fades in near the bottom of its
parent and fades out on its own ("Copied to clipboard", "Report exported").
"""

from __future__ import annotations

from PySide6.QtCore import QPropertyAnimation, Qt, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect, QLabel, QWidget


class Toast(QLabel):
    _FADE_IN_MS = 140
    _FADE_OUT_MS = 260
    _BOTTOM_MARGIN = 28

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setObjectName("toast")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.hide()

        self._effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self._effect)
        self._anim = QPropertyAnimation(self._effect, b"opacity", self)
        self._anim.finished.connect(self._on_anim_finished)
        self._fading_out = False

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._fade_out)

    def show_message(self, text: str, duration_ms: int = 1500) -> None:
        self._hide_timer.stop()
        self._anim.stop()
        self._fading_out = False

        self.setText(text)
        self.adjustSize()
        parent = self.parentWidget()
        if parent is not None:
            self.move(
                (parent.width() - self.width()) // 2,
                parent.height() - self.height() - self._BOTTOM_MARGIN,
            )

        self._effect.setOpacity(0.0)
        self.show()
        self.raise_()
        self._anim.setDuration(self._FADE_IN_MS)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(1.0)
        self._anim.start()
        self._hide_timer.start(duration_ms)

    def _fade_out(self) -> None:
        self._fading_out = True
        self._anim.stop()
        self._anim.setDuration(self._FADE_OUT_MS)
        self._anim.setStartValue(self._effect.opacity())
        self._anim.setEndValue(0.0)
        self._anim.start()

    def _on_anim_finished(self) -> None:
        if self._fading_out:
            self.hide()
