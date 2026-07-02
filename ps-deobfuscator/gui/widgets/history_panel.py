"""
Session History panel: lists recent decode runs and restores them on demand.

Decode payloads are reconstructed from the stored snapshot, never re-decoded,
so opening an old entry is instant and produces the exact same output the
engine produced at capture time.
"""

from __future__ import annotations

from functools import partial

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ps_deobfuscator.history import HistoryEntry, HistoryStore


_PREVIEW_CHARS: int = 90


def _make_preview(text: str) -> str:
    """Single-line, length-bounded preview suitable for a narrow table cell."""
    flattened = " ".join(text.split())
    if len(flattened) <= _PREVIEW_CHARS:
        return flattened
    return flattened[: _PREVIEW_CHARS - 3] + "..."


class HistoryPanel(QWidget):
    """Lists `HistoryStore` entries with per-row restore/delete and a clear-all action."""

    entry_selected = Signal(object)

    def __init__(self, store: HistoryStore, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._store = store
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._page_scroll = QScrollArea()
        self._page_scroll.setObjectName("pageScroll")
        self._page_scroll.setWidgetResizable(True)
        self._page_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._page_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        outer.addWidget(self._page_scroll)

        page = QWidget()
        page.setObjectName("decodePage")
        page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self._page_scroll.setWidget(page)

        root = QVBoxLayout(page)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("History")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        sub = QLabel(
            f"Last {store.max_entries} decodings - click Restore to re-render an entry. "
            "Stored locally next to your app data."
        )
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        root.addWidget(sub)

        self._location = QLabel(str(store.path))
        self._location.setObjectName("muted")
        self._location.setWordWrap(True)
        self._location.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        root.addWidget(self._location)

        card = QFrame()
        card.setObjectName("card")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        card_lay = QVBoxLayout(card)
        card_lay.setContentsMargins(16, 14, 16, 14)
        card_lay.setSpacing(10)

        header_row = QHBoxLayout()
        header_row.setContentsMargins(0, 0, 0, 0)
        header_row.setSpacing(8)
        lbl = QLabel("SESSION HISTORY")
        lbl.setObjectName("cardSectionLabel")
        header_row.addWidget(lbl)
        header_row.addStretch(1)

        self._clear_btn = QPushButton("Clear history")
        self._clear_btn.setObjectName("secondary")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.setMinimumWidth(120)
        self._clear_btn.clicked.connect(self._on_clear_clicked)
        header_row.addWidget(self._clear_btn)
        card_lay.addLayout(header_row)

        self._stack = QStackedWidget()
        self._stack.setObjectName("iocStack")
        self._stack.setMinimumHeight(220)
        self._stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        self._empty = QLabel(
            "No decodings yet. Successful Quick Decode runs will appear here automatically."
        )
        self._empty.setObjectName("iocEmpty")
        self._empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty.setWordWrap(True)
        self._stack.addWidget(self._empty)

        self._table = QTableWidget(0, 6)
        self._table.setObjectName("iocTable")
        self._table.setHorizontalHeaderLabels(
            ["Time", "Input preview", "Layers", "IOCs", "Output chars", ""]
        )
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setWordWrap(False)
        self._table.verticalHeader().setVisible(False)
        self._table.verticalHeader().setDefaultSectionSize(32)
        self._table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        hdr = self._table.horizontalHeader()
        hdr.setStretchLastSection(False)
        hdr.setMinimumSectionSize(56)
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        hdr.resizeSection(5, 168)

        self._table.cellDoubleClicked.connect(self._on_cell_double_clicked)
        self._stack.addWidget(self._table)

        card_lay.addWidget(self._stack, stretch=1)
        root.addWidget(card, stretch=1)

        self.refresh()

    def refresh(self) -> None:
        entries = self._store.entries()
        if not entries:
            self._stack.setCurrentIndex(0)
            self._clear_btn.setEnabled(False)
            self._table.setRowCount(0)
            return

        self._clear_btn.setEnabled(True)
        self._stack.setCurrentIndex(1)
        self._table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            time_item = QTableWidgetItem(entry.timestamp)
            time_item.setToolTip(entry.timestamp)
            self._table.setItem(row, 0, time_item)

            preview = _make_preview(entry.input)
            preview_item = QTableWidgetItem(preview)
            preview_item.setToolTip(entry.input[:1000])
            self._table.setItem(row, 1, preview_item)

            layers_item = QTableWidgetItem(str(len(entry.layers)))
            layers_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 2, layers_item)

            iocs_item = QTableWidgetItem(str(len(entry.iocs)))
            iocs_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self._table.setItem(row, 3, iocs_item)

            chars_item = QTableWidgetItem(f"{len(entry.final_text):,}")
            chars_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            self._table.setItem(row, 4, chars_item)

            self._table.setCellWidget(row, 5, self._build_actions_cell(entry))

    def _build_actions_cell(self, entry: HistoryEntry) -> QWidget:
        host = QWidget()
        lay = QHBoxLayout(host)
        lay.setContentsMargins(4, 2, 4, 2)
        lay.setSpacing(6)

        restore_btn = QPushButton("Restore")
        restore_btn.setObjectName("ghost")
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.setToolTip("Reopen this decode in Quick Decode")
        restore_btn.clicked.connect(partial(self._emit_selected, entry))
        lay.addWidget(restore_btn)

        delete_btn = QPushButton("Delete")
        delete_btn.setObjectName("ghost")
        delete_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        delete_btn.setToolTip("Remove this entry from history")
        delete_btn.clicked.connect(partial(self._on_delete_clicked, entry.id))
        lay.addWidget(delete_btn)

        return host

    def _emit_selected(self, entry: HistoryEntry) -> None:
        self.entry_selected.emit(entry)

    def _on_cell_double_clicked(self, row: int, _column: int) -> None:
        entries = self._store.entries()
        if 0 <= row < len(entries):
            self._emit_selected(entries[row])

    def _on_delete_clicked(self, entry_id: str) -> None:
        self._store.delete(entry_id)
        self.refresh()

    def _on_clear_clicked(self) -> None:
        confirm = QMessageBox.question(
            self,
            "Clear history",
            "Remove all entries from the local history file?\n"
            "Stored payload snapshots will be deleted from disk.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
            QMessageBox.StandardButton.Cancel,
        )
        if confirm != QMessageBox.StandardButton.Yes:
            return
        self._store.clear()
        self.refresh()
