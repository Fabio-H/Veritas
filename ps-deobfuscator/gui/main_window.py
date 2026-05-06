"""
Main application shell: collapsible sidebar + stacked content (decode panel).
"""

from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from gui.app_icon import load_application_icon
from gui.themes import COLOR_BORDER0, COLOR_GREEN_BRIGHT
from gui.widgets.decode_panel import DecodePanel
from ps_deobfuscator.app_info import APP_DESCRIPTION, APP_NAME, APP_PACKAGE, APP_VERSION


class MainWindow(QMainWindow):
    """Gruvbox-inspired shell: sidebar rail + main workspace."""

    _SIDEBAR_EXPANDED = 252
    _SIDEBAR_COLLAPSED = 56
    _AUTO_COLLAPSE_WIDTH = 900
    _AUTO_EXPAND_WIDTH = 1080

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION} — {APP_PACKAGE}")
        # 860 × 600 is the smallest size at which both cards fit without scrolling
        # at default font sizes.  The outer page QScrollArea handles anything smaller.
        self.setMinimumSize(860, 600)
        self.resize(1280, 820)
        app_icon = load_application_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self._sidebar_collapsed = False
        self._sidebar_user_collapsed = False
        self._build_menu()

        root = QWidget()
        root.setObjectName("mainSurface")
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self._sidebar = self._build_sidebar()
        self._sidebar.setFixedWidth(self._SIDEBAR_EXPANDED)
        layout.addWidget(self._sidebar)

        divider = QFrame()
        divider.setFixedWidth(1)
        divider.setStyleSheet(f"background-color: {COLOR_BORDER0};")
        layout.addWidget(divider)

        self._stack = QStackedWidget()
        self._decode_panel = DecodePanel()
        self._stack.addWidget(self._decode_panel)
        layout.addWidget(self._stack, stretch=1)

    def _build_sidebar(self) -> QFrame:
        bar = QFrame()
        bar.setObjectName("sidebar")
        v = QVBoxLayout(bar)
        v.setContentsMargins(14, 20, 12, 20)
        v.setSpacing(0)

        top_row = QHBoxLayout()
        self._collapse_btn = QPushButton("⟨")
        self._collapse_btn.setObjectName("sidebarToggle")
        self._collapse_btn.setToolTip("Collapse sidebar")
        self._collapse_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._collapse_btn.setFixedSize(36, 32)
        self._collapse_btn.setFlat(False)
        self._collapse_btn.clicked.connect(self._toggle_sidebar)
        top_row.addWidget(self._collapse_btn)
        top_row.addStretch(1)
        v.addLayout(top_row)
        v.addSpacing(12)

        self._brand_title = QLabel(APP_NAME)
        self._brand_title.setObjectName("brandTitle")
        v.addWidget(self._brand_title)

        self._brand_sub = QLabel(APP_PACKAGE)
        self._brand_sub.setObjectName("brandSub")
        v.addWidget(self._brand_sub)
        v.addSpacing(14)

        self._disc = QFrame()
        self._disc.setObjectName("disclaimer")
        dv = QVBoxLayout(self._disc)
        dv.setContentsMargins(10, 10, 10, 10)
        dl = QLabel("Defensive analysis only")
        dl.setWordWrap(True)
        dl.setStyleSheet(f"color: {COLOR_GREEN_BRIGHT}; font-size: 10pt;")
        dv.addWidget(dl)
        v.addWidget(self._disc)
        v.addSpacing(18)

        self._nav_lbl = QLabel("NAVIGATION")
        self._nav_lbl.setObjectName("navSection")
        v.addWidget(self._nav_lbl)
        v.addSpacing(8)

        self._nav_decode = self._make_nav_button("  Quick Decode", active=True)
        self._nav_decode.setToolTip("Quick Decode")
        self._nav_decode.clicked.connect(self._show_decode)
        v.addWidget(self._nav_decode)

        v.addStretch(1)

        self._foot = QLabel("URL · Hex · Base64 · GZIP · zlib")
        self._foot.setObjectName("muted")
        self._foot.setWordWrap(True)
        v.addWidget(self._foot)

        self._ver = QLabel(f"v{APP_VERSION}")
        self._ver.setObjectName("muted")
        v.addWidget(self._ver)

        return bar

    def _build_menu(self) -> None:
        help_menu = self.menuBar().addMenu("&Help")
        about = QAction(f"About {APP_NAME}", self)
        about.triggered.connect(self._show_about)
        help_menu.addAction(about)

    def _show_about(self) -> None:
        QMessageBox.about(
            self,
            f"About {APP_NAME}",
            (
                f"<b>{APP_NAME}</b> {APP_VERSION}<br>"
                f"{APP_DESCRIPTION}<br><br>"
                "Defensive static analysis only. Veritas decodes text and extracts IOCs; "
                "it does not execute payloads."
            ),
        )

    def _make_nav_button(self, text: str, *, active: bool) -> QPushButton:
        btn = QPushButton(text)
        btn.setObjectName("navActive" if active else "navInactive")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        return btn

    def _show_decode(self) -> None:
        self._stack.setCurrentWidget(self._decode_panel)

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        super().resizeEvent(event)
        if not hasattr(self, "_collapse_btn"):
            return
        # Defer the sidebar toggle to the next event-loop iteration.
        # Calling setFixedWidth() synchronously inside resizeEvent triggers a
        # second layout pass before the first one finishes, which causes flicker
        # and can leave widgets in inconsistent intermediate states.
        w = self.width()
        if w < self._AUTO_COLLAPSE_WIDTH and not self._sidebar_collapsed:
            QTimer.singleShot(0, lambda: self._set_sidebar_collapsed(True, remember_user=False))
        elif (
            w >= self._AUTO_EXPAND_WIDTH
            and self._sidebar_collapsed
            and not self._sidebar_user_collapsed
        ):
            QTimer.singleShot(0, lambda: self._set_sidebar_collapsed(False, remember_user=False))

    def _toggle_sidebar(self) -> None:
        self._set_sidebar_collapsed(not self._sidebar_collapsed, remember_user=True)

    def _set_sidebar_collapsed(self, collapsed: bool, *, remember_user: bool) -> None:
        if remember_user:
            self._sidebar_user_collapsed = collapsed
        self._sidebar_collapsed = collapsed
        end = self._SIDEBAR_COLLAPSED if collapsed else self._SIDEBAR_EXPANDED

        if collapsed:
            self._collapse_btn.setText("⟩")
            self._collapse_btn.setToolTip("Expand sidebar")
            self._brand_title.setText("V")
            self._nav_decode.setText(" ◈ ")
            for w in (self._brand_sub, self._disc, self._nav_lbl, self._foot, self._ver):
                w.setVisible(False)
        else:
            self._collapse_btn.setText("⟨")
            self._collapse_btn.setToolTip("Collapse sidebar")
            self._brand_title.setText(APP_NAME)
            self._nav_decode.setText("  Quick Decode")
            for w in (self._brand_sub, self._disc, self._nav_lbl, self._foot, self._ver):
                w.setVisible(True)

        self._sidebar.setFixedWidth(end)
