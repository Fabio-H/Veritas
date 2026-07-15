"""
Manual pipeline: the analyst builds a recipe of operations by hand and runs
it, overriding the automatic heuristic. Useful when the auto decoder picks
the wrong branch (e.g. XOR winning over the intended Base64).
"""

from __future__ import annotations

from functools import partial

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from gui.themes import highlight_document_css, mono_font
from gui.widgets.decode_panel import PayloadTextEdit, _LayerAccordionRow
from gui.widgets.toast import Toast
from ps_deobfuscator.engine import (
    MANUAL_OPS,
    IocRow,
    decode_with_ops,
    highlight_final,
    manual_op_label,
)


class ManualPanel(QWidget):
    """Recipe-style manual decoding: add ops -> run -> inspect layers + IOCs."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._steps: list[tuple[str, int | None]] = []
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        outer.addWidget(scroll)

        page = QWidget()
        page.setObjectName("decodePage")
        scroll.setWidget(page)
        root = QVBoxLayout(page)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(12)

        title = QLabel("Manual Pipeline")
        title.setObjectName("pageTitle")
        root.addWidget(title)
        sub = QLabel("Build your own decode recipe when the automatic heuristic picks the wrong branch")
        sub.setObjectName("pageSubtitle")
        sub.setWordWrap(True)
        root.addWidget(sub)

        # Input card
        card_in = QFrame()
        card_in.setObjectName("card")
        cin = QVBoxLayout(card_in)
        cin.setContentsMargins(16, 14, 16, 14)
        cin.setSpacing(8)
        lbl_in = QLabel("INPUT")
        lbl_in.setObjectName("cardSectionLabel")
        cin.addWidget(lbl_in)
        self._input = PayloadTextEdit()
        self._input.setMinimumHeight(120)
        cin.addWidget(self._input)
        root.addWidget(card_in)

        # Recipe builder card
        card_recipe = QFrame()
        card_recipe.setObjectName("card")
        cr = QVBoxLayout(card_recipe)
        cr.setContentsMargins(16, 14, 16, 14)
        cr.setSpacing(10)
        lbl_r = QLabel("RECIPE")
        lbl_r.setObjectName("cardSectionLabel")
        cr.addWidget(lbl_r)

        add_row = QHBoxLayout()
        add_row.setSpacing(8)
        self._op_combo = QComboBox()
        for op in MANUAL_OPS:
            self._op_combo.addItem(op.label, op.op_id)
        self._op_combo.currentIndexChanged.connect(self._on_op_changed)
        add_row.addWidget(self._op_combo, stretch=1)

        self._key_edit = QLineEdit()
        self._key_edit.setPlaceholderText("key (hex, e.g. 2A)")
        self._key_edit.setMaximumWidth(140)
        self._key_edit.setVisible(False)
        add_row.addWidget(self._key_edit)

        self._add_btn = QPushButton("+ Add step")
        self._add_btn.setObjectName("secondary")
        self._add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._add_btn.clicked.connect(self._add_step)
        add_row.addWidget(self._add_btn)
        cr.addLayout(add_row)

        self._steps_host = QWidget()
        self._steps_layout = QVBoxLayout(self._steps_host)
        self._steps_layout.setContentsMargins(0, 0, 0, 0)
        self._steps_layout.setSpacing(6)
        cr.addWidget(self._steps_host)

        self._empty_steps = QLabel("No steps yet — add operations above, then Run.")
        self._empty_steps.setObjectName("muted")
        self._empty_steps.setStyleSheet("font-style: italic; padding: 4px 2px;")
        cr.addWidget(self._empty_steps)

        run_row = QHBoxLayout()
        self._clear_btn = QPushButton("Clear recipe")
        self._clear_btn.setObjectName("secondary")
        self._clear_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._clear_btn.clicked.connect(self._clear_recipe)
        run_row.addWidget(self._clear_btn)
        run_row.addStretch(1)
        self._run_btn = QPushButton("Run pipeline")
        self._run_btn.setObjectName("primary")
        self._run_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._run_btn.clicked.connect(self._run)
        run_row.addWidget(self._run_btn)
        cr.addLayout(run_row)
        root.addWidget(card_recipe)

        # Output card
        card_out = QFrame()
        card_out.setObjectName("card")
        co = QVBoxLayout(card_out)
        co.setContentsMargins(16, 14, 16, 14)
        co.setSpacing(10)
        lbl_out = QLabel("OUTPUT")
        lbl_out.setObjectName("cardSectionLabel")
        co.addWidget(lbl_out)

        chain_hint = QLabel("Pipeline layers")
        chain_hint.setObjectName("cardHint")
        co.addWidget(chain_hint)
        self._layers_host = QWidget()
        self._layers_layout = QVBoxLayout(self._layers_host)
        self._layers_layout.setContentsMargins(0, 0, 0, 0)
        self._layers_layout.setSpacing(0)
        co.addWidget(self._layers_host)

        stream_hint = QLabel("Result")
        stream_hint.setObjectName("cardHint")
        co.addWidget(stream_hint)
        self._stream = QTextBrowser()
        self._stream.setObjectName("highlightView")
        self._stream.setMinimumHeight(120)
        self._stream.document().setDefaultStyleSheet(highlight_document_css())
        self._stream.setFont(mono_font(11))
        co.addWidget(self._stream)

        ioc_hint = QLabel("Indicators of compromise")
        ioc_hint.setObjectName("cardHint")
        co.addWidget(ioc_hint)
        self._ioc_table = QTableWidget(0, 3)
        self._ioc_table.setObjectName("iocTable")
        self._ioc_table.setHorizontalHeaderLabels(["Type", "Value", "Confidence"])
        self._ioc_table.setAlternatingRowColors(True)
        self._ioc_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._ioc_table.verticalHeader().setVisible(False)
        self._ioc_table.setMinimumHeight(120)
        hdr = self._ioc_table.horizontalHeader()
        hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        co.addWidget(self._ioc_table)
        root.addWidget(card_out)

        self._toast = Toast(self)
        self._refresh_steps_ui()

    # -- recipe management --------------------------------------------------

    def _on_op_changed(self) -> None:
        op_id = self._op_combo.currentData()
        needs_key = any(op.op_id == op_id and op.needs_key for op in MANUAL_OPS)
        self._key_edit.setVisible(needs_key)

    def _parse_key(self) -> int | None:
        raw = self._key_edit.text().strip().lower().removeprefix("0x")
        if not raw:
            return None
        try:
            value = int(raw, 16)
        except ValueError:
            return None
        return value if 0 <= value <= 255 else None

    def _add_step(self) -> None:
        op_id = self._op_combo.currentData()
        needs_key = any(op.op_id == op_id and op.needs_key for op in MANUAL_OPS)
        key: int | None = None
        if needs_key:
            key = self._parse_key()
            if key is None:
                self._toast.show_message("Enter a valid hex key (00–FF)")
                return
        self._steps.append((op_id, key))
        self._key_edit.clear()
        self._refresh_steps_ui()

    def _remove_step(self, index: int) -> None:
        if 0 <= index < len(self._steps):
            self._steps.pop(index)
            self._refresh_steps_ui()

    def _clear_recipe(self) -> None:
        self._steps.clear()
        self._refresh_steps_ui()

    def _refresh_steps_ui(self) -> None:
        while self._steps_layout.count():
            item = self._steps_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        self._empty_steps.setVisible(not self._steps)
        for i, (op_id, key) in enumerate(self._steps):
            row = QWidget()
            rl = QHBoxLayout(row)
            rl.setContentsMargins(0, 0, 0, 0)
            rl.setSpacing(8)
            label = manual_op_label(op_id)
            if key is not None:
                label = f"{label} 0x{key:02X}"
            num = QLabel(f"{i + 1}.  {label}")
            num.setStyleSheet("font-weight: 600;")
            rl.addWidget(num)
            rl.addStretch(1)
            rm = QPushButton("×")
            rm.setObjectName("ghost")
            rm.setCursor(Qt.CursorShape.PointingHandCursor)
            rm.setMaximumWidth(36)
            rm.clicked.connect(partial(self._remove_step, i))
            rl.addWidget(rm)
            self._steps_layout.addWidget(row)

    # -- run ----------------------------------------------------------------

    def _run(self) -> None:
        text = self._input.toPlainText()
        if not text.strip():
            self._toast.show_message("Paste a payload first")
            return
        if not self._steps:
            self._toast.show_message("Add at least one operation")
            return
        try:
            result, iocs = decode_with_ops(text, self._steps)
        except Exception as exc:  # noqa: BLE001 - surface any engine error to the analyst
            self._toast.show_message(f"Pipeline error: {exc}")
            return
        self._render(result.layers, result.final_text, iocs)

    def _render(self, layers: tuple, final_text: str, iocs: tuple[IocRow, ...]) -> None:
        while self._layers_layout.count():
            item = self._layers_layout.takeAt(0)
            w = item.widget()
            if w is not None:
                w.deleteLater()
        for i, layer in enumerate(layers):
            self._layers_layout.addWidget(_LayerAccordionRow(i, layer.type, layer.text))

        self._stream.setHtml(
            f"<html><head></head><body>{highlight_final(final_text)}</body></html>"
        )

        self._ioc_table.setRowCount(len(iocs))
        for r, ioc in enumerate(iocs):
            self._ioc_table.setItem(r, 0, QTableWidgetItem(ioc.tipo))
            self._ioc_table.setItem(r, 1, QTableWidgetItem(ioc.valor))
            self._ioc_table.setItem(r, 2, QTableWidgetItem(ioc.confianca or "-"))

        self._toast.show_message(f"{len(layers) - 1} step(s) · {len(iocs)} IOC(s)")

    def load_payload(self, text: str) -> None:
        """Prefill the input (e.g. handed over from Quick Decode)."""
        self._input.setPlainText(text)
        self._input._apply_terminal_spacing()
