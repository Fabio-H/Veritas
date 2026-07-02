"""
Veritas GUI theme - dark, premium RE / malware-analysis aesthetic.

Gruvbox-adjacent: near-black base, warm amber/orange accents, muted olive.
No bright cyan; Fusion + QPalette + global QSS.
"""

from __future__ import annotations

from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication

# Surfaces
COLOR_BG0: str = "#0d0d0c"
COLOR_BG1: str = "#141312"
COLOR_BG2: str = "#1b1a18"
COLOR_BG3: str = "#242220"
COLOR_BORDER0: str = "#2e2c29"
COLOR_BORDER1: str = "#3a3834"

# Text
COLOR_FG0: str = "#fbf1c7"
COLOR_FG1: str = "#e8e4dc"
COLOR_FG2: str = "#b8b2a8"
COLOR_FG3: str = "#7a756c"

# Accents (warm)
COLOR_AMBER: str = "#d79921"
COLOR_AMBER_DIM: str = "#b57614"
COLOR_ORANGE: str = "#fe8019"
COLOR_ORANGE_DIM: str = "#d65d0e"
COLOR_GREEN: str = "#98971a"
COLOR_GREEN_BRIGHT: str = "#b8bb26"
COLOR_RED: str = "#cc241d"

# Semantic aliases (widgets)
COLOR_BG = COLOR_BG0
COLOR_BG_ELEVATED = COLOR_BG1
COLOR_BG_CARD = COLOR_BG2
COLOR_BG_INPUT = COLOR_BG0
COLOR_BORDER = COLOR_BORDER0
COLOR_BORDER_FOCUS = COLOR_AMBER
COLOR_ACCENT = COLOR_AMBER
COLOR_ACCENT_HOVER = COLOR_AMBER_DIM
COLOR_ACCENT_TEXT = COLOR_BG0
COLOR_TEXT = COLOR_FG1
COLOR_TEXT_MUTED = COLOR_FG3
COLOR_SUCCESS = COLOR_GREEN_BRIGHT
COLOR_SUCCESS_BG = "#1b1a18"
COLOR_SUCCESS_BORDER = COLOR_GREEN
COLOR_DANGER = COLOR_RED
COLOR_WARNING = COLOR_ORANGE

# HTML highlighter (engine span classes)
COLOR_HL_URL: str = COLOR_AMBER
COLOR_HL_IP: str = "#ea6962"
COLOR_HL_PS: str = COLOR_ORANGE

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
    .hl-ip {{ color: {COLOR_HL_IP}; }}
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
        color: {COLOR_AMBER};
    }}
    QMenu {{
        background-color: {COLOR_BG2};
        color: {COLOR_FG1};
        border: 1px solid {COLOR_BORDER0};
    }}
    QMenu::item {{
        padding: 6px 24px;
    }}
    QMenu::item:selected {{
        background-color: {COLOR_BG3};
        color: {COLOR_AMBER};
    }}
    QLabel {{
        background-color: transparent;
    }}
    QFrame#card {{
        background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {COLOR_BG3}, stop:1 {COLOR_BG2});
        border: 1px solid {COLOR_BORDER0};
        border-radius: 8px;
    }}
    QFrame#sidebar {{
        background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {COLOR_BG1}, stop:1 {COLOR_BG0});
        border: none;
    }}
    QFrame#disclaimer {{
        background-color: {COLOR_BG2};
        border: 1px solid {COLOR_BORDER1};
        border-radius: 6px;
    }}
    QFrame#statPill {{
        background-color: {COLOR_BG3};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 6px;
        min-width: 72px;
        padding: 2px;
    }}
    QLabel#pageTitle {{
        color: {COLOR_FG0};
        font-size: 18pt;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    QLabel#pageSubtitle {{
        color: {COLOR_FG3};
        font-size: 11pt;
    }}
    QLabel#brandTitle {{
        color: {COLOR_AMBER};
        font-size: 20pt;
        font-weight: 700;
        letter-spacing: -0.02em;
    }}
    QLabel#brandSub {{
        color: {COLOR_FG3};
        font-size: 11pt;
    }}
    QLabel#navSection {{
        color: {COLOR_FG3};
        font-size: 9pt;
        font-weight: 700;
        letter-spacing: 0.1em;
    }}
    QLabel#muted {{
        color: {COLOR_FG3};
        font-size: 9pt;
    }}
    QLabel#statPillTitle {{
        color: {COLOR_FG3};
        font-size: 8pt;
        font-weight: 600;
        letter-spacing: 0.06em;
    }}
    QLabel#statPillValue {{
        color: {COLOR_FG0};
        font-size: 14pt;
        font-weight: 700;
    }}
    QLabel#cardSectionLabel {{
        color: {COLOR_AMBER};
        font-size: 10pt;
        font-weight: 700;
        letter-spacing: 0.04em;
    }}
    QLabel#cardHint {{
        color: {COLOR_FG3};
        font-size: 10pt;
        font-weight: 600;
    }}
    QPushButton#sidebarToggle {{
        background-color: {COLOR_BG3};
        color: {COLOR_FG2};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 5px;
        padding: 4px 8px;
        font-weight: 700;
    }}
    QPushButton#sidebarToggle:hover {{
        border-color: {COLOR_AMBER};
        color: {COLOR_AMBER};
        background-color: {COLOR_BG2};
    }}
    QPushButton#sidebarToggle:pressed {{
        background-color: {COLOR_BG1};
        border-color: {COLOR_ORANGE};
    }}
    QPushButton#navActive {{
        text-align: left;
        padding: 10px 12px;
        border-radius: 6px;
        background-color: {COLOR_BG3};
        color: {COLOR_FG0};
        font-weight: 600;
        border: 1px solid {COLOR_AMBER};
    }}
    QPushButton#navActive:hover {{
        background-color: {COLOR_BG2};
        border-color: {COLOR_ORANGE};
    }}
    QPushButton#navInactive {{
        text-align: left;
        padding: 10px 12px;
        border-radius: 6px;
        background-color: transparent;
        color: {COLOR_FG3};
        border: 1px solid transparent;
    }}
    QPushButton#navInactive:hover {{
        background-color: {COLOR_BG2};
        color: {COLOR_FG1};
        border-color: {COLOR_BORDER0};
    }}
    QPushButton#primary {{
        background-color: {COLOR_BG3};
        color: {COLOR_FG0};
        font-weight: 700;
        padding: 8px 16px;
        border-radius: 6px;
        border: 1px solid {COLOR_BORDER1};
        min-width: 92px;
    }}
    QPushButton#primary:hover {{
        border-color: {COLOR_AMBER};
        background-color: {COLOR_BG2};
    }}
    QPushButton#primary:pressed {{
        border-color: {COLOR_ORANGE};
        background-color: {COLOR_BG1};
    }}
    QPushButton#primary:disabled {{
        background-color: {COLOR_BG1};
        color: {COLOR_FG3};
        border-color: {COLOR_BORDER0};
    }}
    QPushButton#secondary {{
        background-color: transparent;
        color: {COLOR_FG2};
        padding: 7px 12px;
        border-radius: 6px;
        border: 1px solid {COLOR_BORDER0};
        font-weight: 600;
    }}
    QPushButton#secondary:hover {{
        border-color: {COLOR_AMBER};
        color: {COLOR_AMBER};
        background-color: {COLOR_BG2};
    }}
    QPushButton#secondary:pressed {{
        background-color: {COLOR_BG1};
        color: {COLOR_FG0};
    }}
    QPushButton#ghost {{
        background-color: transparent;
        color: {COLOR_AMBER};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 4px;
        padding: 4px 10px;
        font-size: 9pt;
        font-weight: 600;
        min-width: 52px;
    }}
    QPushButton#ghost:hover {{
        border-color: {COLOR_ORANGE};
        color: {COLOR_ORANGE};
        background-color: {COLOR_BG2};
    }}
    QPushButton#ghost:pressed {{
        background-color: {COLOR_BG1};
        border-color: {COLOR_AMBER};
        color: {COLOR_FG0};
    }}
    QTextEdit#payloadInput, QPlainTextEdit#payloadInput {{
        background-color: {COLOR_BG0};
        color: {COLOR_FG1};
        font-family: {FONT_MONO_STACK};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 6px;
        padding: 8px 12px;
        selection-background-color: #3c3828;
        selection-color: {COLOR_FG0};
    }}
    QTextEdit#payloadInput:focus, QPlainTextEdit#payloadInput:focus {{
        border-color: {COLOR_AMBER};
    }}
    QPlainTextEdit#layerBody {{
        background-color: {COLOR_BG0};
        color: {COLOR_FG2};
        font-family: {FONT_MONO_STACK};
        border: none;
        border-top: 1px solid {COLOR_BORDER0};
        padding: 10px;
    }}
    QTextBrowser#highlightView {{
        background-color: {COLOR_BG0};
        color: {COLOR_FG1};
        font-family: {FONT_MONO_STACK};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 6px;
        padding: 12px;
    }}
    QScrollArea {{
        border: none;
        background-color: transparent;
    }}
    QScrollArea > QWidget > QWidget {{
        background-color: transparent;
    }}
    QScrollBar:vertical {{
        background: {COLOR_BG0};
        width: 10px;
        margin: 0;
    }}
    QScrollBar::handle:vertical {{
        background: {COLOR_BG3};
        min-height: 28px;
        border-radius: 4px;
        border: 1px solid {COLOR_BORDER0};
    }}
    QScrollBar::handle:vertical:hover {{
        background: {COLOR_BORDER1};
    }}
    QScrollBar:horizontal {{
        background: {COLOR_BG0};
        height: 10px;
    }}
    QScrollBar::handle:horizontal {{
        background: {COLOR_BG3};
        min-width: 28px;
        border-radius: 4px;
        border: 1px solid {COLOR_BORDER0};
    }}
    QTableWidget {{
        background-color: {COLOR_BG0};
        alternate-background-color: {COLOR_BG2};
        color: {COLOR_FG1};
        gridline-color: {COLOR_BORDER0};
        border: 1px solid {COLOR_BORDER0};
        border-radius: 6px;
        selection-background-color: #504945;
        selection-color: {COLOR_FG0};
    }}
    QTableWidget::item {{
        padding: 4px 8px;
        border: none;
    }}
    QHeaderView::section {{
        background-color: {COLOR_BG3};
        color: {COLOR_AMBER};
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid {COLOR_BORDER0};
        font-weight: 600;
        font-size: 10pt;
    }}
    QProgressBar {{
        border: 1px solid {COLOR_BORDER0};
        border-radius: 3px;
        text-align: center;
        color: transparent;
        background-color: {COLOR_BG0};
        height: 4px;
        max-height: 4px;
    }}
    QProgressBar::chunk {{
        background-color: {COLOR_AMBER};
        border-radius: 2px;
    }}
    QToolButton#accordionHeader {{
        background-color: {COLOR_BG2};
        color: {COLOR_FG1};
        border: 1px solid {COLOR_BORDER0};
        border-left: 3px solid transparent;
        border-radius: 6px;
        padding: 8px 10px;
        font-weight: 600;
        text-align: left;
    }}
    QToolButton#accordionHeader:checked {{
        border-left: 3px solid {COLOR_AMBER};
        background-color: {COLOR_BG3};
        border-color: {COLOR_BORDER1};
    }}
    QToolButton#accordionHeader:hover {{
        border-color: {COLOR_FG3};
        background-color: {COLOR_BG3};
    }}
    QSplitter::handle:vertical {{
        height: 8px;
        background-color: {COLOR_BORDER0};
        border-radius: 3px;
        margin: 1px 16px;
    }}
    QSplitter::handle:vertical:hover {{
        background-color: {COLOR_AMBER};
        cursor: ns-resize;
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
        border: 1px solid {COLOR_BORDER0};
        border-radius: 6px;
    }}
    QTableWidget#iocTable {{
        font-size: 10pt;
    }}
    """


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    pal = QPalette()
    pal.setColor(QPalette.ColorRole.Window, QColor(COLOR_BG0))
    pal.setColor(QPalette.ColorRole.WindowText, QColor(COLOR_FG1))
    pal.setColor(QPalette.ColorRole.Base, QColor(COLOR_BG0))
    pal.setColor(QPalette.ColorRole.AlternateBase, QColor(COLOR_BG2))
    pal.setColor(QPalette.ColorRole.Text, QColor(COLOR_FG1))
    pal.setColor(QPalette.ColorRole.Button, QColor(COLOR_BG3))
    pal.setColor(QPalette.ColorRole.ButtonText, QColor(COLOR_FG1))
    pal.setColor(QPalette.ColorRole.Highlight, QColor("#504945"))
    pal.setColor(QPalette.ColorRole.HighlightedText, QColor(COLOR_FG0))
    app.setPalette(pal)
    app.setStyleSheet(build_app_stylesheet())
