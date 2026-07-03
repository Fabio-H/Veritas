"""
Main application shell: collapsible sidebar + stacked content (decode panel).
"""

from __future__ import annotations

from PySide6.QtCore import (
    QAbstractAnimation,
    QEasingCurve,
    QParallelAnimationGroup,
    QPropertyAnimation,
    QSettings,
    Qt,
    QTimer,
)
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsOpacityEffect,
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
from gui.widgets.history_panel import HistoryPanel
from ps_deobfuscator.app_info import APP_DESCRIPTION, APP_NAME, APP_PACKAGE, APP_VERSION
from ps_deobfuscator.engine import DecodeResult, IocRow
from ps_deobfuscator.history import HistoryEntry, HistoryStore, default_history_path


class MainWindow(QMainWindow):
    """Gruvbox-inspired shell: sidebar rail + main workspace."""

    _SIDEBAR_EXPANDED = 252
    _SIDEBAR_COLLAPSED = 56
    _AUTO_COLLAPSE_WIDTH = 900
    _AUTO_EXPAND_WIDTH = 1080

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION} - {APP_PACKAGE}")
        # Keep a practical floor but allow compact screens.
        # Individual pages rely on internal QScrollArea containers for overflow.
        self.setMinimumSize(640, 480)
        self.resize(1280, 820)
        app_icon = load_application_icon()
        if not app_icon.isNull():
            self.setWindowIcon(app_icon)

        self._sidebar_collapsed = False
        self._sidebar_user_collapsed = False

        self._history_store = HistoryStore(default_history_path())

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
        self._history_panel = HistoryPanel(self._history_store)
        self._stack.addWidget(self._decode_panel)
        self._stack.addWidget(self._history_panel)
        layout.addWidget(self._stack, stretch=1)

        self._decode_panel.decode_completed.connect(self._on_decode_completed)
        self._history_panel.entry_selected.connect(self._on_history_entry_selected)

        self._sidebar_anim: QParallelAnimationGroup | None = None
        self._page_anim: QPropertyAnimation | None = None

        # Restore window size/position and sidebar state from the last session.
        self._settings = QSettings("Veritas", "Veritas")
        geometry = self._settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        if self._settings.value("sidebar/collapsed", False, type=bool):
            self._set_sidebar_collapsed(True, remember_user=True, animate=False)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._settings.setValue("window/geometry", self.saveGeometry())
        self._settings.setValue("sidebar/collapsed", self._sidebar_collapsed)
        super().closeEvent(event)

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

        self._nav_history = self._make_nav_button("  History", active=False)
        self._nav_history.setToolTip("Session history")
        self._nav_history.clicked.connect(self._show_history)
        v.addWidget(self._nav_history)

        v.addStretch(1)

        self._foot = QLabel("URL | Hex | Base64 | GZIP | zlib")
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

    def _set_nav_active(self, active: QPushButton) -> None:
        """Swap object names and re-polish so QSS rules for navActive/navInactive apply."""
        for btn in (self._nav_decode, self._nav_history):
            target = "navActive" if btn is active else "navInactive"
            if btn.objectName() != target:
                btn.setObjectName(target)
                btn.style().unpolish(btn)
                btn.style().polish(btn)

    def _fade_to(self, widget: QWidget) -> None:
        """Switch the stacked page with a short crossfade."""
        if self._stack.currentWidget() is widget:
            return
        self._stack.setCurrentWidget(widget)
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        anim = QPropertyAnimation(effect, b"opacity", self)
        anim.setDuration(160)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        anim.finished.connect(lambda w=widget: w.setGraphicsEffect(None))
        self._page_anim = anim
        anim.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)

    def _show_decode(self) -> None:
        self._fade_to(self._decode_panel)
        self._set_nav_active(self._nav_decode)

    def _show_history(self) -> None:
        self._history_panel.refresh()
        self._fade_to(self._history_panel)
        self._set_nav_active(self._nav_history)

    def _on_decode_completed(
        self,
        input_text: str,
        result: object,
        iocs: object,
    ) -> None:
        if not isinstance(result, DecodeResult):
            return
        rows = iocs if isinstance(iocs, tuple) else ()
        typed_rows: tuple[IocRow, ...] = tuple(r for r in rows if isinstance(r, IocRow))
        entry = HistoryEntry.from_decode(
            input_text=input_text,
            result=result,
            iocs=typed_rows,
        )
        try:
            self._history_store.append(entry)
        except OSError as exc:
            QMessageBox.warning(
                self,
                "History save failed",
                f"Could not write the session history file:\n{exc}",
            )
            return
        self._history_panel.refresh()

    def _on_history_entry_selected(self, entry: object) -> None:
        if not isinstance(entry, HistoryEntry):
            return
        self._decode_panel.load_from_history(entry)
        self._stack.setCurrentWidget(self._decode_panel)
        self._set_nav_active(self._nav_decode)

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

    def _set_sidebar_collapsed(
        self, collapsed: bool, *, remember_user: bool, animate: bool = True
    ) -> None:
        if remember_user:
            self._sidebar_user_collapsed = collapsed
        self._sidebar_collapsed = collapsed
        end = self._SIDEBAR_COLLAPSED if collapsed else self._SIDEBAR_EXPANDED

        if collapsed:
            self._collapse_btn.setText("⟩")
            self._collapse_btn.setToolTip("Expand sidebar")
            self._brand_title.setText("V")
            self._nav_decode.setText(" ◈ ")
            self._nav_history.setText(" ◷ ")
            for w in (self._brand_sub, self._disc, self._nav_lbl, self._foot, self._ver):
                w.setVisible(False)
        else:
            self._collapse_btn.setText("⟨")
            self._collapse_btn.setToolTip("Collapse sidebar")
            self._brand_title.setText(APP_NAME)
            self._nav_decode.setText("  Quick Decode")
            self._nav_history.setText("  History")
            for w in (self._brand_sub, self._disc, self._nav_lbl, self._foot, self._ver):
                w.setVisible(True)

        if not animate:
            self._sidebar.setFixedWidth(end)
            return
        self._animate_sidebar_width(end)

    def _animate_sidebar_width(self, end: int) -> None:
        if self._sidebar_anim is not None:
            self._sidebar_anim.stop()
        group = QParallelAnimationGroup(self)
        # Animate min and max together: the layout follows both bounds, so the
        # rail slides instead of snapping.
        for prop in (b"minimumWidth", b"maximumWidth"):
            anim = QPropertyAnimation(self._sidebar, prop)
            anim.setDuration(200)
            anim.setStartValue(self._sidebar.width())
            anim.setEndValue(end)
            anim.setEasingCurve(QEasingCurve.Type.OutCubic)
            group.addAnimation(anim)
        group.finished.connect(lambda: self._sidebar.setFixedWidth(end))
        self._sidebar_anim = group
        group.start(QAbstractAnimation.DeletionPolicy.KeepWhenStopped)
