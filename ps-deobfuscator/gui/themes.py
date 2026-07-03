"""
Veritas GUI theme - "Veritas Dark": modern security-product aesthetic.

Deep blue-black surfaces, mint-green signature accent, cyan/red/amber
semantic highlights for URLs/IPs/PowerShell. Fusion + QPalette + global QSS.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

# Surfaces (blue-black slate)
COLOR_BG0: str = "#0a0e13"
COLOR_BG1: str = "#0f141b"
COLOR_BG2: str = "#141b24"
COLOR_BG3: str = "#1b2431"
COLOR_BORDER0: str = "#222c3a"
COLOR_BORDER1: str = "#2e3b4e"

# Text
COLOR_FG0: str = "#eef3f8"
COLOR_FG1: str = "#d5dde6"
COLOR_FG2: str = "#9fadbd"
COLOR_FG3: str = "#5f6f81"

# Signature accent (mint) + semantic colors
COLOR_MINT: str = "#2fd6a0"
COLOR_MINT_BRIGHT: str = "#4beab5"
COLOR_MINT_DIM: str = "#1ba57e"
COLOR_CYAN: str = "#56c2f0"
COLOR_RED: str = "#f26d6d"
COLOR_AMBER: str = "#f0b429"
COLOR_AMBER_DIM: str = "#c98f14"

# Legacy aliases (kept so older imports keep working)
COLOR_ORANGE: str = COLOR_AMBER
COLOR_ORANGE_DIM: str = COLOR_AMBER_DIM
COLOR_GREEN: str = COLOR_MINT_DIM
COLOR_GREEN_BRIGHT: str = COLOR_MINT

# Semantic aliases (widgets)
COLOR_BG = COLOR_BG0
COLOR_BG_ELEVATED = COLOR_BG1
COLOR_BG_CARD = COLOR_BG2
COLOR_BG_INPUT = COLOR_BG0
COLOR_BORDER = COLOR_BORDER0
COLOR_BORDER_FOCUS = COLOR_MINT
COLOR_ACCENT = COLOR_MINT
COLOR_ACCENT_HOVER = COLOR_MINT_BRIGHT
COLOR_ACCENT_TEXT = "#06231a"
COLOR_TEXT = COLOR_FG1
COLOR_TEXT_MUTED = COLOR_FG3
COLOR_SUCCESS = COLOR_MINT
COLOR_SUCCESS_BG = COLOR_BG2
COLOR_SUCCESS_BORDER = COLOR_MINT_DIM
COLOR_DANGER = COLOR_RED
COLOR_WARNING = COLOR_AMBER

# HTML highlighter (engine span classes)
COLOR_HL_URL: str = COLOR_CYAN
COLOR_HL_IP: str = COLOR_RED
COLOR_HL_PS: str = COLOR_AMBER

# Accent-tinted translucent fills (QSS rgba)
_ACCENT_FILL_SOFT: str = "rgba(47, 214, 160, 0.10)"
_ACCENT_FILL_MED: str = "rgba(47, 214, 160, 0.16)"
_SELECTION_BG: str = "#1f4a3c"

FONT_UI_STACK: str = '"IBM Plex Sans", "Source Sans 3", "Segoe UI", "Helvetica Neue", Arial'
FONT_MONO_STACK: str = '"JetBrains Mono", "Cascadia Code", "IBM Plex Mono", Consolas, monospace'


def mono_font(point_size: int = 12) -> QFont:
    f = QFont()
    f.setFamilies(["JetBrains Mono", "Cascadia Code", "IBM Plex Mono", "Consolas", "monospace"])
    f.setPointSize(point_size)
    f.setStyleHint(QFont.StyleHint.Monospace)
    return f


def ui_font(point_size: int = 12, bold: bool = False) -> QFont:
    f = QFont()
    f.setFamilies(["IBM Plex Sans", "Source Sans 3", "Segoe UI", "Helvetica Neue", "Arial"])
    f.setPointSize(point_size)
    if bold:
        f.setWeight(QFont.Weight.DemiBold)
    return f


def highlight_document_css() -> str:
    """QTextDocument default stylesheet for engine.highlight_final() spans."""
    return f"""
    body {{
        margin: 0;
        font-family: {FONT_MONO_STACK};
        font-size: 11pt;
        line-height: 1.55;
        color: {COLOR_FG1};
    }}
    .hl-url {{ color: {COLOR_HL_URL}; font-weight: 500; }}
    .hl-ip {{ color: {COLOR_HL_IP}; font-weight: 500; }}
    .hl-ps {{ color: {COLOR_HL_PS}; font-weight: 600; }}
    """


def build_app_stylesheet() -> str:
    return f"""
    QMainWindow {{
        background-color: {COLOR_BG0};
    }}
    QWidget {{
        color: {COLOR_FG1};
        font-family: {FONT_UI_STACK};
        font-size: 11pt;
    }}
    QWidget#mainSurface {{
        background-color: {COLOR_BG0};
    }}
    QStackedWidget {{
        background-color: {COLOR_BG0};
    }}
    QWidget#decodePage {{
        background-color: {COLOR_BG0};
    }}
    QToolTip {{
        background-color: {COLOR_BG3};
        color: {COLOR_FG1};
        border: 1px solid {COLOR_BORDER1};
        padding: 4px 8px;
    }}
    QMenuBar {{
        background-color: {COLOR_BG1};
        color: {COLOR_FG2};
        border-bottom: 1px solid {COLOR_BORDER0};
    }}
    QMenuBar::item {{
        background-color: transparent;
        padding: 6px 10px;
    }}
    QMenuBar::item:selected {{
        background-color: {COLOR_BG3};
        color: {COLOR_MINT};
    }}
    QMenu {{
        background-color: {COLOR_BG2};
        color: {COLOR_FG1};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 6px;
    }}
    QMenu::item {{
        padding: 6px 24px;
        border-radius: 4px;
    }}
    QMenu::item:selected {{
        background-color: {_ACCENT_FILL_MED};
        color: {COLOR_MINT_BRIGHT};
    }}
    QLabel {{
        background-color: transparent;
    }}
    QFrame#card {{
        background-color: {COLOR_BG2};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 10px;
    }}
    QFrame#sidebar {{
        background-color: {COLOR_BG1};
        border: none;
    }}
    QFrame#disclaimer {{
        background-color: {_ACCENT_FILL_SOFT};
        border: 1px solid {COLOR_MINT_DIM};
        border-radius: 8px;
    }}
    QFrame#statPill {{
        background-color: {COLOR_BG3};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 8px;
        min-width: 72px;
        padding: 2px;
    }}
    QLabel#pageTitle {{
        color: {COLOR_FG0};
        font-size: 19pt;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    QLabel#pageSubtitle {{
        color: {COLOR_FG3};
        font-size: 11pt;
    }}
    QLabel#brandTitle {{
        color: {COLOR_MINT};
        font-size: 20pt;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    QLabel#brandSub {{
        color: {COLOR_FG3};
        font-size: 10pt;
        letter-spacing: 0.02em;
    }}
    QLabel#navSection {{
        color: {COLOR_FG3};
        font-size: 9pt;
        font-weight: 700;
        letter-spacing: 0.12em;
    }}
    QLabel#muted {{
        color: {COLOR_FG3};
        font-size: 9pt;
    }}
    QLabel#warnBanner {{
        color: {COLOR_AMBER};
        background-color: rgba(240, 180, 41, 0.08);
        border: 1px solid {COLOR_AMBER_DIM};
        border-radius: 8px;
        padding: 8px 12px;
        font-size: 10pt;
    }}
    QLabel#statPillTitle {{
        color: {COLOR_FG3};
        font-size: 8pt;
        font-weight: 600;
        letter-spacing: 0.08em;
    }}
    QLabel#statPillValue {{
        color: {COLOR_MINT};
        font-size: 14pt;
        font-weight: 700;
    }}
    QLabel#cardSectionLabel {{
        color: {COLOR_MINT};
        font-size: 10pt;
        font-weight: 700;
        letter-spacing: 0.10em;
    }}
    QLabel#cardHint {{
        color: {COLOR_FG2};
        font-size: 10pt;
        font-weight: 600;
        letter-spacing: 0.02em;
    }}
    QPushButton#sidebarToggle {{
        background-color: transparent;
        color: {COLOR_FG2};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 6px;
        padding: 4px 8px;
        font-weight: 700;
    }}
    QPushButton#sidebarToggle:hover {{
        border-color: {COLOR_MINT_DIM};
        color: {COLOR_MINT};
        background-color: {_ACCENT_FILL_SOFT};
    }}
    QPushButton#sidebarToggle:pressed {{
        background-color: {COLOR_BG2};
        border-color: {COLOR_MINT};
    }}
    QPushButton#navActive {{
        text-align: left;
        padding: 10px 12px;
        border-radius: 8px;
        background-color: {_ACCENT_FILL_MED};
        color: {COLOR_MINT_BRIGHT};
        font-weight: 600;
        border: 1px solid {COLOR_MINT_DIM};
    }}
    QPushButton#navActive:hover {{
        background-color: {_ACCENT_FILL_MED};
        border-color: {COLOR_MINT};
    }}
    QPushButton#navInactive {{
        text-align: left;
        padding: 10px 12px;
        border-radius: 8px;
        background-color: transparent;
        color: {COLOR_FG2};
        border: 1px solid transparent;
    }}
    QPushButton#navInactive:hover {{
        background-color: {COLOR_BG2};
        color: {COLOR_FG0};
        border-color: {COLOR_BORDER0};
    }}
    QPushButton#primary {{
        background-color: {COLOR_MINT};
        color: {COLOR_ACCENT_TEXT};
        font-weight: 700;
        padding: 8px 18px;
        border-radius: 8px;
        border: 1px solid {COLOR_MINT};
        min-width: 92px;
    }}
    QPushButton#primary:hover {{
        background-color: {COLOR_MINT_BRIGHT};
        border-color: {COLOR_MINT_BRIGHT};
    }}
    QPushButton#primary:pressed {{
        background-color: {COLOR_MINT_DIM};
        border-color: {COLOR_MINT_DIM};
    }}
    QPushButton#primary:disabled {{
        background-color: {COLOR_BG3};
        color: {COLOR_FG3};
        border-color: {COLOR_BORDER0};
    }}
    QPushButton#secondary {{
        background-color: transparent;
        color: {COLOR_FG1};
        padding: 7px 14px;
        border-radius: 8px;
        border: 1px solid {COLOR_BORDER1};
        font-weight: 600;
    }}
    QPushButton#secondary:hover {{
        border-color: {COLOR_MINT_DIM};
        color: {COLOR_MINT};
        background-color: {_ACCENT_FILL_SOFT};
    }}
    QPushButton#secondary:pressed {{
        background-color: {COLOR_BG2};
        color: {COLOR_FG0};
    }}
    QPushButton#secondary:disabled {{
        color: {COLOR_FG3};
        border-color: {COLOR_BORDER0};
    }}
    QPushButton#ghost {{
        background-color: transparent;
        color: {COLOR_MINT};
        border: 1px solid transparent;
        border-radius: 6px;
        padding: 4px 10px;
        font-size: 9pt;
        font-weight: 600;
        min-width: 52px;
    }}
    QPushButton#ghost:hover {{
        border-color: {COLOR_MINT_DIM};
        background-color: {_ACCENT_FILL_SOFT};
        color: {COLOR_MINT_BRIGHT};
    }}
    QPushButton#ghost:pressed {{
        background-color: {COLOR_BG2};
        color: {COLOR_FG0};
    }}
    QTextEdit#payloadInput, QPlainTextEdit#payloadInput {{
        background-color: {COLOR_BG0};
        color: {COLOR_FG1};
        font-family: {FONT_MONO_STACK};
        border: 1px solid {COLOR_BORDER1};
        border-radius: 8px;
        padding: 8px 12px;
        selection-background-color: {_SELECTION_BG};
        selection-color: {COLOR_FG0};
    }}
    QTextEdit#payloadInput:focus, QPlainTextEdit#payloadInput:focus {{
        border-color: {COLOR_MINT};
    }}
    QPlainTextEdit#layerBody {{
        background-color: {COLOR_BG0};
        color: {COLOR_FG2};
        font-family: {FONT_MONO_STACK};
        border: none;
        border-top: 1px solid {COLOR_BORDER0};
        padding: 10px;
        selection-background-color: {_SELECTION_BG};
        selection-color: {COLOR_FG0};
    }}
    QTextBrowser#highlightView {{
        background-color: {COLOR_BG0};
        color: {COLOR_FG1};
        font-family: {FONT_MONO_STACK};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 8px;
        padding: 12px;
        selection-background-color: {_SELECTION_BG};
        selection-color: {COLOR_FG0};
    }}
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BG3};
        min-height: 28px;
        border-radius: 5px;
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLOR_BORDER1};
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
        height: 0;
    }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLOR_BG3};
        min-width: 28px;
        border-radius: 5px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
        width: 0;
    }}
    QTableWidget {{
        background-color: {COLOR_BG0};
        alternate-background-color: {COLOR_BG1};
        color: {COLOR_FG1};
        gridline-color: {COLOR_BORDER0};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 8px;
        selection-background-color: {_SELECTION_BG};
        selection-color: {COLOR_FG0};
    }}
    QTableWidget::item {{
        padding: 4px 8px;
        border: none;
    }}
    QHeaderView::section {{
        background-color: {COLOR_BG2};
        color: {COLOR_FG2};
        padding: 8px 10px;
        border: none;
        border-bottom: 2px solid {COLOR_MINT_DIM};
        font-weight: 700;
        font-size: 9pt;
        letter-spacing: 0.06em;
        text-transform: uppercase;
    }}
    QProgressBar {{
        border: none;
        border-radius: 2px;
        text-align: center;
        color: transparent;
        background-color: {COLOR_BG3};
        height: 4px;
        max-height: 4px;
    }}
    QProgressBar::chunk {{
        background-color: {COLOR_MINT};
        border-radius: 2px;
    }}
    QToolButton#accordionHeader {{
        background-color: {COLOR_BG1};
        color: {COLOR_FG1};
        border: 1px solid {COLOR_BORDER0};
        border-left: 3px solid {COLOR_BORDER1};
        border-radius: 6px;
        padding: 8px 10px;
        font-weight: 600;
        text-align: left;
    }}
    QToolButton#accordionHeader:checked {{
        border-left: 3px solid {COLOR_MINT};
        background-color: {COLOR_BG3};
        color: {COLOR_FG0};
    }}
    QToolButton#accordionHeader:hover {{
        border-color: {COLOR_MINT_DIM};
        background-color: {COLOR_BG3};
    }}
    QSplitter::handle:vertical {{
        height: 8px;
        background-color: {COLOR_BORDER0};
        border-radius: 3px;
        margin: 1px 16px;
    }}
    QSplitter::handle:vertical:hover {{
        background-color: {COLOR_MINT};
    }}
    QFrame#cardSeparator {{
        background-color: {COLOR_BORDER0};
        max-height: 1px;
        border: none;
    }}
    QScrollArea#outputBodyScroll {{
        border: none;
        background-color: transparent;
    }}
    QScrollArea#outputBodyScroll > QWidget > QWidget {{
        background-color: transparent;
    }}
    QWidget#cardOutHeader {{
        background-color: transparent;
    }}
    QWidget#cardBody {{
        background-color: transparent;
    }}
    QStackedWidget#iocStack {{
        background-color: transparent;
    }}
    QLabel#iocEmpty {{
        color: {COLOR_FG3};
        font-style: italic;
        font-size: 10pt;
        padding: 24px 16px;
        background-color: {COLOR_BG0};
        border: 1px dashed {COLOR_BORDER1};
        border-radius: 8px;
    }}
    QTableWidget#iocTable {{
        font-size: 10pt;
    }}
    QMessageBox {{
        background-color: {COLOR_BG2};
    }}
    QLabel#toast {{
        background-color: {COLOR_BG3};
        color: {COLOR_FG0};
        border: 1px solid {COLOR_MINT_DIM};
        border-radius: 8px;
        padding: 8px 18px;
        font-size: 10pt;
        font-weight: 600;
    }}
    """


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(COLOR_BG0))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(COLOR_FG1))
    pal.setColor(QPalette.ColorRole.Base, QColor(COLOR_BG0))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(COLOR_BG1))
    pal.setColor(QPalette.ColorRole.Text, QColor(COLOR_FG1))
    pal.setColor(QPalette.ColorRole.Button, QColor(COLOR_BG3))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(COLOR_FG1))
    pal.setColor(QPalette.ColorRole.Highlight, QColor(_SELECTION_BG))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(COLOR_FG0))
    pal.setColor(QPalette.ColorRole.Link, QColor(COLOR_CYAN))
    pal.setColor(QPalette.ColorRole.ToolTipBase, QColor(COLOR_BG3))
    pal.setColor(QPalette.ColorRole.ToolTipText, QColor(COLOR_FG1))
    app.setPalette(pal)
    app.setStyleSheet(build_app_stylesheet())
