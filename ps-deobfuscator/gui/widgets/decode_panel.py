"""
Primary decode workspace: terminal-style input, async decode, layers, highlight, IOCs, export.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, QTimer, Signal, Slot
from PySide6.QtGui import QKeySequence, QShortcut, QTextBlockFormat, QTextCursor
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSplitter,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QTextEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from ps_deobfuscator.engine import (
    DecodeResult,
    IocRow,
    MAX_PAYLOAD_CHARS,
    PayloadTooLargeError,
    decode_payload,
    format_txt_report,
    highlight_final,
    iocs_as_dicts,
    layers_as_dicts,
)
from ps_deobfuscator.app_info import APP_NAME, APP_VERSION

from gui.themes import highlight_document_css, mono_font, ui_font


class StatPill(QFrame):
    """Compact analysis metric (SIEM-style)."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("statPill")
        self.setMinimumWidth(0)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(2)
        t = QLabel(title.upper())
        t.setObjectName("statPillTitle")
        t.setWordWrap(True)
        self._val = QLabel("—")
        self._val.setObjectName("statPillValue")
        lay.addWidget(t)
        lay.addWidget(self._val)

    def set_value(self, text: str) -> None:
        self._val.setText(text)


class PayloadTextEdit(QTextEdit):
    """Terminal-like editor: mono, line spacing, drag-and-drop."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("payloadInput")
        self.setAcceptDrops(True)
        self.setPlaceholderText(
            "Paste or drop a payload here — Base64, Hex, URL, GZIP, one-liners… "
            "Press Ctrl+Enter to decode."
        )
        self.setFont(mono_font(12))
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setTabStopDistance(self.fontMetrics().horizontalAdvance(" ") * 4)
        self._apply_terminal_spacing()

    def _apply_terminal_spacing(self) -> None:
        bf = QTextBlockFormat()
        height_type = QTextBlockFormat.LineHeightTypes.ProportionalHeight
        height_type_id = height_type.value if hasattr(height_type, "value") else int(height_type)
        bf.setLineHeight(160.0, height_type_id)
        c = QTextCursor(self.document())
        c.select(QTextCursor.SelectionType.Document)
        c.mergeBlockFormat(bf)
        c.clearSelection()

    def dragEnterEvent(self, event) -> None:  # type: ignore[override]
        md = event.mimeData()
        if md.hasUrls() or md.hasText():
            event.acceptProposedAction()
        else:
            super().dragEnterEvent(event)

    def dragMoveEvent(self, event) -> None:  # type: ignore[override]
        md = event.mimeData()
        if md.hasUrls() or md.hasText():
            event.acceptProposedAction()
        else:
            super().dragMoveEvent(event)

    def dropEvent(self, event) -> None:  # type: ignore[override]
        md = event.mimeData()
        if md.hasUrls():
            for url in md.urls():
                path = url.toLocalFile()
                if not path:
                    continue
                p = Path(path)
                if p.is_file():
                    try:
                        text = p.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    self.setPlainText(text)
                    self._apply_terminal_spacing()
                    event.acceptProposedAction()
                    return
        if md.hasText():
            self.setPlainText(md.text())
            self._apply_terminal_spacing()
            event.acceptProposedAction()
            return
        super().dropEvent(event)


class DecodeWorker(QObject):
    """Runs decode_payload off the GUI thread."""

    finished = Signal(object, object)
    failed = Signal(str)

    @Slot(str)
    def run_decode(self, payload: str) -> None:
        try:
            result, iocs = decode_payload(payload)
        except PayloadTooLargeError as exc:
            self.failed.emit(str(exc))
            return
        except Exception as exc:  # noqa: BLE001
            self.failed.emit(str(exc))
            return
        self.finished.emit(result, iocs)


class _LayerAccordionRow(QWidget):
    """Single decode layer: collapsible header + read-only body."""

    def __init__(self, index: int, layer_type: str, text: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 10)
        outer.setSpacing(0)

        header = QToolButton()
        header.setObjectName("accordionHeader")
        header.setCheckable(True)
        header.setChecked(True)
        header.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        header.setArrowType(Qt.ArrowType.DownArrow)
        header.setText(f"  Layer {index + 1}: {layer_type}")
        header.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        header.setCursor(Qt.CursorShape.PointingHandCursor)
        header.setFont(ui_font(11, bold=True))

        body = QPlainTextEdit()
        body.setObjectName("layerBody")
        body.setReadOnly(True)
        body.setPlainText(text)
        body.setFont(mono_font(10))
        body.setMinimumHeight(72)
        body.setMaximumHeight(480)
        body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)

        def on_toggled(checked: bool) -> None:
            body.setVisible(checked)
            header.setArrowType(Qt.ArrowType.DownArrow if checked else Qt.ArrowType.RightArrow)

        header.toggled.connect(on_toggled)
        outer.addWidget(header)
        outer.addWidget(body)


class DecodePanel(QWidget):
    """Quick Decode pipeline: input → decode → layers / output / IOCs."""

    _DECODE_SLOW_MS = 15_000

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._busy = False
        self._thread: QThread | None = None
        self._worker: DecodeWorker | None = None
        self._last_result: DecodeResult | None = None
        self._last_iocs: tuple[IocRow, ...] = ()
        self._slow_decode_warned = False

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
        # MinimumExpanding: page grows to fill viewport when there is room,
        # but the scroll area provides at least minimumSizeHint() height —
        # this is what enables the page to scroll instead of compressing its children.
        page.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)
        self._page_scroll.setWidget(page)

        root = QVBoxLayout(page)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Quick Decode")
        title.setObjectName("pageTitle")
        root.addWidget(title)

        sub = QLabel("Pipeline · URL · Hex · Base64 · GZIP · zlib · IOC extraction")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        root.addWidget(sub)

        self._status = QLabel(
            f"Ready · Max input {MAX_PAYLOAD_CHARS:,} chars · Static analysis only"
        )
        self._status.setObjectName("muted")
        self._status.setWordWrap(True)
        root.addWidget(self._status)

        self._splitter = QSplitter(Qt.Orientation.Vertical)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setHandleWidth(8)
        self._splitter.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # —— Input card ——
        # Do NOT set an explicit minimumHeight here — let the layout compute it from
        # its children so Qt and the splitter agree on the enforced minimum.
        card_in = QFrame()
        card_in.setObjectName("card")
        card_in.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Preferred)
        cin = QVBoxLayout(card_in)
        cin.setContentsMargins(16, 14, 16, 14)
        cin.setSpacing(8)
        lbl_in = QLabel("INPUT")
        lbl_in.setObjectName("cardSectionLabel")
        cin.addWidget(lbl_in)

        self._input = PayloadTextEdit()
        # 80 px == ~3 visible lines at 11pt mono — readable without wasting space.
        self._input.setMinimumHeight(80)
        self._input.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        cin.addWidget(self._input, stretch=1)

        # Action row: [Paste]  ···stretch···  [progress bar]  [Decode]
        # QHBoxLayout is simpler and more resize-stable than QGridLayout here.
        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(8)
        self._paste_btn = QPushButton("Paste")
        self._paste_btn.setObjectName("secondary")
        self._paste_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._paste_btn.setMinimumWidth(72)
        self._paste_btn.clicked.connect(self._paste_clipboard)
        row.addWidget(self._paste_btn)

        row.addStretch(1)

        self._progress = QProgressBar()
        self._progress.setRange(0, 0)
        self._progress.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self._progress.setMinimumWidth(24)
        self._progress.setMaximumWidth(180)
        self._progress.setFixedHeight(4)
        self._progress.setTextVisible(False)
        self._progress.setVisible(False)
        row.addWidget(self._progress)

        self._decode_btn = QPushButton("Decode")
        self._decode_btn.setObjectName("primary")
        self._decode_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._decode_btn.setMinimumWidth(96)
        self._decode_btn.clicked.connect(self._start_decode)
        row.addWidget(self._decode_btn)
        cin.addLayout(row)
        self._splitter.addWidget(card_in)

        # —— Results card ——
        # Architecture: fixed header (OUTPUT label + stat pills) always visible,
        # plus a dedicated QScrollArea for the body so that squeezing the splitter
        # never causes content overlap — the body simply scrolls instead.
        card_out = QFrame()
        card_out.setObjectName("card")
        # Minimum matches the fixed header height only; body scrolls below it.
        card_out.setMinimumHeight(110)
        card_out.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        cout_outer = QVBoxLayout(card_out)
        cout_outer.setContentsMargins(0, 0, 0, 0)
        cout_outer.setSpacing(0)

        # ·· Fixed header (always visible) ··
        _hdr = QWidget()
        _hdr.setObjectName("cardOutHeader")
        _hdr.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        _hdr_lay = QVBoxLayout(_hdr)
        _hdr_lay.setContentsMargins(16, 14, 16, 8)
        _hdr_lay.setSpacing(8)

        lbl_out = QLabel("OUTPUT")
        lbl_out.setObjectName("cardSectionLabel")
        _hdr_lay.addWidget(lbl_out)

        stats = QHBoxLayout()
        stats.setSpacing(8)
        self._pill_layers = StatPill("Layers")
        self._pill_iocs = StatPill("IOCs")
        self._pill_chars = StatPill("Output chars")
        stats.addWidget(self._pill_layers)
        stats.addWidget(self._pill_iocs)
        stats.addWidget(self._pill_chars)
        stats.addStretch(1)
        _hdr_lay.addLayout(stats)
        cout_outer.addWidget(_hdr)

        # Thin separator between fixed header and scrollable body
        _sep = QFrame()
        _sep.setFrameShape(QFrame.Shape.HLine)
        _sep.setObjectName("cardSeparator")
        cout_outer.addWidget(_sep)

        # ·· Scrollable body ··
        # When the splitter squeezes card_out below its natural preferred height,
        # this scroll area absorbs the difference — nothing ever overlaps.
        _body_scroll = QScrollArea()
        _body_scroll.setObjectName("outputBodyScroll")
        _body_scroll.setFrameShape(QFrame.Shape.NoFrame)
        _body_scroll.setWidgetResizable(True)
        _body_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        _body_scroll.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        _body = QWidget()
        _body.setObjectName("cardBody")
        # MinimumExpanding: the body fills the scroll-area viewport when there is
        # room (so the stream and table use all available height), and the scroll
        # area provides at least minimumSizeHint() height when the card is squeezed.
        _body.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.MinimumExpanding)

        cout = QVBoxLayout(_body)
        cout.setContentsMargins(16, 10, 16, 14)
        cout.setSpacing(10)

        layers_header = QLabel("Decode chain")
        layers_header.setObjectName("cardHint")
        cout.addWidget(layers_header)

        self._layers_host = QWidget()
        self._layers_layout = QVBoxLayout(self._layers_host)
        self._layers_layout.setContentsMargins(0, 0, 0, 0)
        self._layers_layout.setSpacing(0)
        # No inner QScrollArea wrapper — the outer _body_scroll handles overflow.
        # Individual layer bodies keep their own scrollbars (setMaximumHeight below).
        cout.addWidget(self._layers_host)

        hl_label = QLabel("Deobfuscated stream")
        hl_label.setObjectName("cardHint")
        cout.addWidget(hl_label)

        self._highlight = QTextBrowser()
        self._highlight.setObjectName("highlightView")
        self._highlight.setOpenExternalLinks(False)
        self._highlight.setMinimumHeight(120)
        self._highlight.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self._highlight.document().setDefaultStyleSheet(highlight_document_css())
        self._highlight.setFont(mono_font(11))
        cout.addWidget(self._highlight, stretch=3)

        ioc_label = QLabel("Indicators of compromise")
        ioc_label.setObjectName("cardHint")
        cout.addWidget(ioc_label)

        # Stack: index 0 = empty-state label, index 1 = data table.
        # Switching between them keeps the layout stable regardless of IOC count.
        self._ioc_stack = QStackedWidget()
        self._ioc_stack.setObjectName("iocStack")
        self._ioc_stack.setMinimumHeight(160)   # header + ~5 rows
        self._ioc_stack.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # ── Empty state ──
        self._ioc_empty = QLabel("No IOCs detected in the decoded output.")
        self._ioc_empty.setObjectName("iocEmpty")
        self._ioc_empty.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._ioc_empty.setWordWrap(True)
        self._ioc_stack.addWidget(self._ioc_empty)   # index 0

        # ── IOC table ──
        self._ioc_table = QTableWidget(0, 4)
        self._ioc_table.setObjectName("iocTable")
        self._ioc_table.setHorizontalHeaderLabels(["Type", "Value", "Confidence", ""])
        self._ioc_table.setAlternatingRowColors(True)
        self._ioc_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._ioc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._ioc_table.setWordWrap(False)
        self._ioc_table.verticalHeader().setVisible(False)
        # Comfortable row height — fits text + cell padding without feeling cramped.
        self._ioc_table.verticalHeader().setDefaultSectionSize(30)
        self._ioc_table.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._ioc_table.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        _hdr = self._ioc_table.horizontalHeader()
        _hdr.setStretchLastSection(False)
        _hdr.setMinimumSectionSize(56)
        # Type: auto-fit to cell content (short strings like "IPv4", ".NET Library")
        _hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        # Value: stretches to fill remaining width
        _hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        # Confidence: user-resizable with a comfortable starting width
        _hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.Interactive)
        _hdr.resizeSection(2, 150)
        # Copy button column: fixed compact width
        _hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        _hdr.resizeSection(3, 76)

        self._ioc_stack.addWidget(self._ioc_table)   # index 1
        cout.addWidget(self._ioc_stack, stretch=1)

        export_row = QHBoxLayout()
        self._export_txt = QPushButton("Export TXT")
        self._export_txt.setObjectName("secondary")
        self._export_txt.setEnabled(False)
        self._export_txt.setMinimumWidth(92)
        self._export_txt.clicked.connect(self._export_txt_file)
        self._export_json = QPushButton("Export JSON")
        self._export_json.setObjectName("secondary")
        self._export_json.setEnabled(False)
        self._export_json.setMinimumWidth(104)
        self._export_json.clicked.connect(self._export_json_file)
        export_row.addWidget(self._export_txt)
        export_row.addWidget(self._export_json)
        export_row.addStretch(1)
        cout.addLayout(export_row)

        _body_scroll.setWidget(_body)
        cout_outer.addWidget(_body_scroll, stretch=1)

        self._splitter.addWidget(card_out)
        self._splitter.setCollapsible(0, False)
        self._splitter.setCollapsible(1, False)
        self._splitter.setStretchFactor(0, 1)
        self._splitter.setStretchFactor(1, 3)
        # Input card gets ~30 % of initial space; output card gets ~70 %.
        self._splitter.setSizes([220, 520])
        self._splitter.splitterMoved.connect(self._on_splitter_moved)

        root.addWidget(self._splitter, stretch=1)

        sc = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Return), self)
        sc.activated.connect(self._start_decode)
        sc2 = QShortcut(QKeySequence(Qt.Modifier.CTRL | Qt.Key.Key_Enter), self)
        sc2.activated.connect(self._start_decode)

        self._clear_results_ui()

    def _on_splitter_moved(self, _pos: int, _index: int) -> None:
        """Keep splitter children at or above their layout minimums.

        Qt's setCollapsible(False) prevents the handle from collapsing a pane
        entirely, but it does not guarantee the child's minimumSizeHint() is
        respected during fast drags.  This slot corrects any violation immediately
        after each move so content never overlaps.
        """
        sizes = self._splitter.sizes()
        if len(sizes) < 2:
            return
        s0, s1 = sizes
        min0 = max(self._splitter.widget(0).minimumSizeHint().height(), 1)
        min1 = max(self._splitter.widget(1).minimumSizeHint().height(), 1)
        total = s0 + s1
        if s0 < min0:
            s0 = min0
            s1 = max(total - s0, min1)
        elif s1 < min1:
            s1 = min1
            s0 = max(total - s1, min0)
        if [s0, s1] != sizes:
            self._splitter.setSizes([s0, s1])

    @staticmethod
    def _copy_value(value: str) -> None:
        QApplication.clipboard().setText(value)

    def _paste_clipboard(self) -> None:
        clip = QApplication.clipboard()
        if clip is not None and clip.text():
            self._input.setPlainText(clip.text())
            self._input._apply_terminal_spacing()

    def _clear_results_ui(self) -> None:
        while self._layers_layout.count():
            item = self._layers_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._highlight.clear()
        self._highlight.setHtml(
            "<html><body><span style='color:#7a756c;'>Decoded output will appear here.</span></body></html>"
        )
        self._ioc_table.setRowCount(0)
        self._ioc_stack.setCurrentIndex(0)   # show empty-state label
        self._export_txt.setEnabled(False)
        self._export_json.setEnabled(False)
        self._pill_layers.set_value("—")
        self._pill_iocs.set_value("—")
        self._pill_chars.set_value("—")
        self._status.setText(f"Ready · Max input {MAX_PAYLOAD_CHARS:,} chars · Static analysis only")

    def _start_decode(self) -> None:
        if self._busy:
            return
        payload = self._input.toPlainText()
        if not payload.strip():
            QMessageBox.information(self, "Veritas", "Paste or drop a payload first.")
            return
        if len(payload) > MAX_PAYLOAD_CHARS:
            QMessageBox.warning(
                self,
                "Input too large",
                (
                    f"This input has {len(payload):,} characters.\n"
                    f"Veritas limits analysis to {MAX_PAYLOAD_CHARS:,} characters "
                    "to keep the desktop app responsive."
                ),
            )
            return

        self._busy = True
        self._slow_decode_warned = False
        self._decode_btn.setEnabled(False)
        self._decode_btn.setText("Decoding…")
        self._progress.setVisible(True)
        self._status.setText("Decoding in background…")

        self._thread = QThread()
        self._worker = DecodeWorker()
        self._worker.moveToThread(self._thread)

        self._thread.started.connect(lambda p=payload: self._worker.run_decode(p))  # type: ignore[union-attr]
        self._worker.finished.connect(self._on_decode_finished)
        self._worker.failed.connect(self._on_decode_failed)
        self._thread.finished.connect(self._on_thread_finished)

        self._thread.start()
        QTimer.singleShot(self._DECODE_SLOW_MS, self._warn_if_decode_is_slow)

    def _warn_if_decode_is_slow(self) -> None:
        if not self._busy or self._slow_decode_warned:
            return
        self._slow_decode_warned = True
        self._status.setText(
            "Still decoding… large or highly nested input can take longer, but analysis remains bounded."
        )

    @Slot(object, object)
    def _on_decode_finished(self, result: object, iocs: object) -> None:
        if not isinstance(result, DecodeResult):
            if self._thread is not None:
                self._thread.quit()
            return
        rows: tuple[IocRow, ...] = iocs if isinstance(iocs, tuple) else ()
        self._last_result = result
        self._last_iocs = rows
        self._apply_results(result, self._last_iocs)
        if self._thread is not None:
            self._thread.quit()

    @Slot(str)
    def _on_decode_failed(self, message: str) -> None:
        self._status.setText("Decode failed.")
        QMessageBox.warning(self, "Decode failed", message)
        if self._thread is not None:
            self._thread.quit()

    @Slot()
    def _on_thread_finished(self) -> None:
        self._decode_btn.setEnabled(True)
        self._decode_btn.setText("Decode")
        self._progress.setVisible(False)
        self._busy = False
        if self._thread is not None:
            self._thread.deleteLater()
            self._thread = None
        if self._worker is not None:
            self._worker.deleteLater()
            self._worker = None

    def _apply_results(self, result: DecodeResult, iocs: tuple[IocRow, ...]) -> None:
        self._clear_results_ui()

        self._pill_layers.set_value(str(len(result.layers)))
        self._pill_iocs.set_value(str(len(iocs)))
        self._pill_chars.set_value(f"{len(result.final_text):,}")

        if not result.layers:
            empty = QLabel("No intermediate transforms — blob may already be plaintext.")
            empty.setObjectName("muted")
            empty.setStyleSheet("font-style: italic; padding: 8px;")
            self._layers_layout.addWidget(empty)
        else:
            for i, layer in enumerate(result.layers):
                self._layers_layout.addWidget(_LayerAccordionRow(i, layer.type, layer.text))

        html_body = highlight_final(result.final_text)
        self._highlight.setHtml(f"<html><head></head><body>{html_body}</body></html>")

        self._ioc_table.setRowCount(len(iocs))
        if iocs:
            for r, row in enumerate(iocs):
                type_item = QTableWidgetItem(row.tipo)
                type_item.setToolTip(row.tipo)
                self._ioc_table.setItem(r, 0, type_item)

                val_item = QTableWidgetItem(row.valor)
                val_item.setToolTip(row.valor)   # full value on hover for long strings
                self._ioc_table.setItem(r, 1, val_item)

                conf = row.confianca if row.confianca else "—"
                conf_item = QTableWidgetItem(conf)
                conf_item.setToolTip(conf)
                self._ioc_table.setItem(r, 2, conf_item)

                copy_btn = QPushButton("Copy")
                copy_btn.setObjectName("ghost")
                copy_btn.setCursor(Qt.CursorShape.PointingHandCursor)
                copy_btn.setToolTip("Copy value to clipboard")
                copy_btn.clicked.connect(partial(DecodePanel._copy_value, row.valor))
                self._ioc_table.setCellWidget(r, 3, copy_btn)

            # Resize Type column to actual content after all rows are inserted.
            self._ioc_table.horizontalHeader().setSectionResizeMode(
                0, QHeaderView.ResizeMode.ResizeToContents
            )
            self._ioc_stack.setCurrentIndex(1)   # show table
        else:
            self._ioc_stack.setCurrentIndex(0)   # show empty-state label

        self._export_txt.setEnabled(True)
        self._export_json.setEnabled(True)
        self._status.setText(
            f"Complete · {len(result.layers)} layer(s) · {len(iocs)} IOC(s) · "
            f"{len(result.final_text):,} output chars"
        )

    def _export_txt_file(self) -> None:
        if self._last_result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export report",
            "veritas-decode-report.txt",
            "Text files (*.txt);;All files (*.*)",
        )
        if not path:
            return
        try:
            text = format_txt_report(self._last_result, self._last_iocs)
            Path(path).write_text(text, encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))

    def _export_json_file(self) -> None:
        if self._last_result is None:
            return
        path, _ = QFileDialog.getSaveFileName(
            self,
            "Export JSON",
            "veritas-decode-report.json",
            "JSON (*.json);;All files (*.*)",
        )
        if not path:
            return
        data = {
            "metadata": {
                "app": APP_NAME,
                "version": APP_VERSION,
                "generated_at": datetime.now(UTC)
                .isoformat(timespec="seconds")
                .replace("+00:00", "Z"),
                "mode": "static defensive analysis",
                "layers": len(self._last_result.layers),
                "iocs": len(self._last_iocs),
            },
            "final_text": self._last_result.final_text,
            "layers": layers_as_dicts(self._last_result),
            "iocs": iocs_as_dicts(self._last_iocs),
        }
        try:
            Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        except OSError as exc:
            QMessageBox.warning(self, "Export failed", str(exc))
