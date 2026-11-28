"""The WormsPy look: a quiet, cool graphite instrument panel with one GFP-green accent.

Every colour in the UI comes from these tokens. The accent marks the few things that matter:
the wordmark, primary actions, the tracked point, focus and "all is well" states. Red is
reserved for recording and alarms, amber for warnings. Greys carry a slight blue cast so the
feeds' neutral greys read as the image, not as UI.
"""

import pyqtgraph as pg
from PySide6.QtGui import QColor, QFont, QFontDatabase, QPalette
from PySide6.QtWidgets import QApplication

GROUND = "#0e1013"      # window background
PANEL = "#161a1e"       # control cards
RAISED = "#1f2429"      # inputs and buttons
HOVER = "#282e34"
BORDER = "#2a3037"
BORDER_STRONG = "#3b434c"
TEXT = "#e3e7eb"
MUTED = "#8b949e"
FAINT = "#555d66"       # disabled text
# GFP / GCaMP green: the hue of their ~510 nm emission (spectral sRGB #00ff4a, hue 137°),
# slightly softened for a dark screen. Every accent shade shares that hue.
ACCENT = "#37e669"
ACCENT_DIM = "#28713d"
ACCENT_BG = "#132f1b"   # accent-tinted fill for primary buttons and "live" chips
ACCENT_HOVER = "#193e23"
RED = "#ff5c61"
RED_DIM = "#7d2e31"
RED_BG = "#361719"
AMBER = "#f2b544"
AMBER_BG = "#3a2e12"
FEED_BACKGROUND = "#07080a"


def rgba(colour: str, alpha: int) -> tuple[int, int, int, int]:
    """A token as an (r, g, b, a) tuple, for pyqtgraph pens and brushes."""
    c = QColor(colour)
    return c.red(), c.green(), c.blue(), alpha


def mono_font(point_size: int = 11) -> QFont:
    font = QFontDatabase.systemFont(QFontDatabase.SystemFont.FixedFont)
    font.setPointSize(point_size)
    return font


STYLESHEET = f"""
QWidget {{ color: {TEXT}; }}
QMainWindow, QWidget#central {{ background: {GROUND}; }}
QStatusBar {{ background: {GROUND}; color: {MUTED}; }}
QToolTip {{ background: {RAISED}; color: {TEXT}; border: 1px solid {BORDER_STRONG};
            padding: 4px 8px; }}

/* Cards: the title sits inside the card, with room around every edge. */
QGroupBox {{
    background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px;
    margin-top: 0; padding: 25px 10px 9px 10px;
    font-size: 10px; font-weight: 700; letter-spacing: 1.5px;   /* the title only */
}}
QGroupBox::title {{
    subcontrol-origin: padding; subcontrol-position: top left; left: 12px; top: 9px;
    color: {MUTED};
}}

QPushButton {{
    background: {RAISED}; border: 1px solid {BORDER}; border-radius: 5px;
    padding: 5px 10px; min-height: 18px;
}}
QPushButton:hover {{ background: {HOVER}; border-color: {BORDER_STRONG}; }}
QPushButton:pressed {{ background: {BORDER}; }}
QPushButton:focus {{ border-color: {ACCENT_DIM}; }}
QPushButton:disabled {{ color: {FAINT}; background: {PANEL}; border-color: {BORDER}; }}
QPushButton[role="primary"] {{
    background: {ACCENT_BG}; border-color: {ACCENT_DIM}; color: {ACCENT}; font-weight: 600; }}
QPushButton[role="primary"]:hover {{ background: {ACCENT_HOVER}; border-color: {ACCENT}; }}
QPushButton[role="primary"]:disabled {{
    background: {PANEL}; border-color: {BORDER}; color: {FAINT}; }}
QPushButton[role="danger"] {{
    background: {RED_BG}; border-color: {RED_DIM}; color: {RED}; font-weight: 600; }}
QPushButton[role="danger"]:hover {{ background: #45191c; border-color: {RED}; }}

QLineEdit, QPlainTextEdit, QComboBox, QDoubleSpinBox {{
    background: {RAISED}; border: 1px solid {BORDER}; border-radius: 5px;
    padding: 4px 7px; min-height: 18px;
    selection-background-color: {ACCENT_DIM}; selection-color: {TEXT};
}}
QPlainTextEdit {{ padding: 2px 5px; }}
QLineEdit:hover, QPlainTextEdit:hover, QComboBox:hover, QDoubleSpinBox:hover {{
    border-color: {BORDER_STRONG}; }}
QLineEdit:focus, QPlainTextEdit:focus, QComboBox:focus, QDoubleSpinBox:focus {{
    border-color: {ACCENT_DIM}; }}
QLineEdit:disabled, QPlainTextEdit:disabled, QComboBox:disabled, QDoubleSpinBox:disabled {{
    color: {FAINT}; background: {PANEL}; }}
QComboBox QAbstractItemView {{
    background: {RAISED}; border: 1px solid {BORDER_STRONG}; padding: 4px;
    selection-background-color: {ACCENT_BG}; selection-color: {ACCENT}; outline: none;
}}

QCheckBox {{ spacing: 7px; }}
QCheckBox::indicator {{ width: 13px; height: 13px; border: 1px solid {BORDER_STRONG};
                        background: {RAISED}; border-radius: 3px; }}
QCheckBox::indicator:hover {{ border-color: {ACCENT_DIM}; }}
QCheckBox::indicator:checked {{ background: {ACCENT}; border-color: {ACCENT}; }}

QLabel#chip {{
    border-radius: 10px; padding: 3px 11px; font-weight: 700; font-size: 11px;
    letter-spacing: 1px; background: {RAISED}; color: {MUTED}; border: 1px solid {BORDER};
}}
QLabel#chip[tone="live"] {{ background: {ACCENT_BG}; color: {ACCENT}; border-color: {ACCENT_DIM}; }}
QLabel#chip[tone="rec"] {{ background: {RED_BG}; color: {RED}; border-color: {RED_DIM}; }}
QLabel#chip[tone="warn"] {{ background: {AMBER_BG}; color: {AMBER}; border-color: #6b5420; }}

/* The live readouts in the header: captioned tiles in one strip. */
QFrame#readouts {{ background: {PANEL}; border: 1px solid {BORDER}; border-radius: 8px; }}
QFrame#readoutDivider {{ background: {BORDER}; border: none; }}
QFrame#sectionDivider {{ background: {BORDER}; border: none; }}
QLabel#readoutCaption {{ color: {MUTED}; font-size: 9px; font-weight: 700;
                         letter-spacing: 1.2px; }}
QLabel#readout {{ color: {TEXT}; }}
QLabel#muted {{ color: {MUTED}; }}
QLabel#feedTitle {{ color: {TEXT}; font-size: 11px; font-weight: 700; letter-spacing: 1.5px; }}
"""


def apply(app: QApplication) -> None:
    """Dark Fusion palette + the stylesheet, and matching pyqtgraph colours."""
    app.setStyle("Fusion")
    palette = QPalette()
    for role, colour in (
            (QPalette.ColorRole.Window, GROUND), (QPalette.ColorRole.WindowText, TEXT),
            (QPalette.ColorRole.Base, RAISED), (QPalette.ColorRole.AlternateBase, PANEL),
            (QPalette.ColorRole.Text, TEXT), (QPalette.ColorRole.Button, RAISED),
            (QPalette.ColorRole.ButtonText, TEXT), (QPalette.ColorRole.Highlight, ACCENT_DIM),
            (QPalette.ColorRole.HighlightedText, TEXT), (QPalette.ColorRole.ToolTipBase, PANEL),
            (QPalette.ColorRole.ToolTipText, TEXT), (QPalette.ColorRole.PlaceholderText, MUTED)):
        palette.setColor(role, QColor(colour))
    app.setPalette(palette)
    app.setStyleSheet(STYLESHEET)
    pg.setConfigOptions(background=FEED_BACKGROUND, foreground=MUTED)


def repolish(widget) -> None:
    """Re-apply the stylesheet after changing a dynamic property (role/tone)."""
    widget.style().unpolish(widget)
    widget.style().polish(widget)
