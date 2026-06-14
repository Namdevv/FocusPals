"""Theme dùng chung cho popup + settings: palette tối, mềm, bo tròn."""
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# palette
BG = "#16171f"        # nền card
SURFACE = "#21232e"   # input nền
SURFACE2 = "#2b2d3a"  # hover / pill
BORDER = "#2f3142"
TEXT = "#eceef5"
SUBTEXT = "#8a8da3"
ACCENT = "#7c6cff"    # indigo-violet
ACCENT_HI = "#9486ff"
SKY = "#56d4f0"       # countdown
DANGER = "#ff6b81"

QSS = f"""
#card {{
    background: {BG};
    border-radius: 18px;
    border: 1px solid {BORDER};
}}
QLabel {{ color: {TEXT}; font-size: 12px; }}
#title {{ color: {TEXT}; font-size: 14px; font-weight: 700; }}
#section {{ color: {SUBTEXT}; font-size: 10px; font-weight: 600;
    letter-spacing: 1px; }}
#hint {{ color: {SUBTEXT}; font-size: 10px; }}
#value {{ color: {SUBTEXT}; font-size: 11px; font-weight: 600; }}

#timeBig {{ color: {TEXT}; font-size: 36px; font-weight: 800; }}

/* preset pills */
QPushButton[pill="true"] {{
    background: {SURFACE};
    color: {SUBTEXT};
    border: 1px solid {BORDER};
    border-radius: 13px;
    padding: 6px 0;
    font-size: 12px; font-weight: 600;
}}
QPushButton[pill="true"]:hover {{ background: {SURFACE2}; color: {TEXT}; }}
QPushButton[pill="true"][on="true"] {{
    background: {ACCENT};
    color: white;
    border: 1px solid {ACCENT};
}}

/* stepper round */
QPushButton[step="true"] {{
    background: {SURFACE};
    color: {TEXT};
    border: 1px solid {BORDER};
    border-radius: 13px;
    font-size: 16px; font-weight: 700;
    min-width: 26px; max-width: 26px; min-height: 26px; max-height: 26px;
}}
QPushButton[step="true"]:hover {{ background: {SURFACE2}; }}

/* primary / danger */
QPushButton#primary {{
    background: {ACCENT}; color: white;
    border: none; border-radius: 11px;
    padding: 9px; font-size: 13px; font-weight: 700;
}}
QPushButton#primary:hover {{ background: {ACCENT_HI}; }}
QPushButton#danger {{
    background: {DANGER}; color: #2a0c12;
    border: none; border-radius: 11px;
    padding: 9px; font-size: 13px; font-weight: 700;
}}
QPushButton#danger:hover {{ background: #ff8497; }}

/* ghost / secondary */
QPushButton#ghost {{
    background: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 11px;
    padding: 8px 12px; font-size: 12px;
}}
QPushButton#ghost:hover {{ background: {SURFACE2}; }}

/* combo */
QComboBox {{
    background: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 10px;
    padding: 7px 11px; font-size: 12px;
}}
QComboBox:hover {{ border: 1px solid {ACCENT}; }}
QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox QAbstractItemView {{
    background: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 8px;
    selection-background-color: {ACCENT}; outline: none;
    padding: 4px;
}}

/* slider */
QSlider::groove:horizontal {{
    height: 6px; background: {SURFACE2}; border-radius: 3px;
}}
QSlider::sub-page:horizontal {{ background: {ACCENT}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: white; width: 16px; height: 16px;
    margin: -6px 0; border-radius: 8px;
}}

/* checkbox */
QCheckBox {{ color: {TEXT}; font-size: 13px; spacing: 8px; }}
QCheckBox::indicator {{
    width: 18px; height: 18px; border-radius: 6px;
    border: 1px solid {BORDER}; background: {SURFACE};
}}
QCheckBox::indicator:checked {{ background: {ACCENT}; border: 1px solid {ACCENT}; }}
"""


def card_shadow(widget):
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(44)
    eff.setColor(QColor(0, 0, 0, 170))
    eff.setOffset(0, 10)
    widget.setGraphicsEffect(eff)
