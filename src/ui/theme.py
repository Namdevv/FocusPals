"""Theme dùng chung cho popup + settings: palette tối, mềm, bo tròn."""
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QGraphicsDropShadowEffect

# palette
BG = "#16171f"        # nền cửa sổ
CARD = "#1b1c26"      # nền nhóm (giữa BG & SURFACE)
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

/* focus bubble nổi trên đầu pet (nhỏ gọn) */
#bubbleTime {{ color: {SKY}; font-size: 17px; font-weight: 800;
    letter-spacing: 1px; }}
#bubbleMsg {{ color: {TEXT}; font-size: 11px; font-weight: 600; }}

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

/* ---- settings window (sidebar + stacked pages) ---- */
#settingsWindow {{ background: {BG}; }}
#stack {{ background: {BG}; }}

#nav {{
    background: {SURFACE}; border: none; outline: none; padding: 10px 8px;
}}
#nav::item {{
    color: {SUBTEXT}; padding: 11px 14px; border-radius: 10px;
    margin: 2px 2px; font-size: 13px;
}}
#nav::item:hover {{ background: {SURFACE2}; color: {TEXT}; }}
#nav::item:selected {{ background: {ACCENT}; color: white; font-weight: 600; }}

QLineEdit {{
    background: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 10px;
    padding: 8px 11px; font-size: 12px;
}}
QLineEdit:focus {{ border: 1px solid {ACCENT}; }}

#result {{
    background: {SURFACE}; color: {TEXT};
    border: 1px solid {BORDER}; border-radius: 10px;
    padding: 8px; font-size: 11px;
}}
#preview {{
    background: {SURFACE}; border: 1px solid {BORDER}; border-radius: 12px;
}}

/* nhóm cài đặt (card nhô trên nền cửa sổ) */
#group {{
    background: {CARD}; border: 1px solid {BORDER}; border-radius: 14px;
}}

QScrollArea {{ background: transparent; border: none; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QScrollBar:vertical {{
    background: transparent; width: 10px; margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: {SURFACE2}; border-radius: 5px; min-height: 28px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}

/* ---- font lớn hơn riêng trong settings (không đụng popup/bubble) ---- */
#settingsWindow QLabel {{ font-size: 14px; }}
#settingsWindow #title {{ font-size: 19px; font-weight: 700; }}
#settingsWindow #section {{ font-size: 12px; letter-spacing: 1px; }}
#settingsWindow #hint {{ font-size: 12px; }}
#settingsWindow #value {{ font-size: 13px; }}
#settingsWindow QComboBox {{ font-size: 14px; padding: 9px 12px; }}
#settingsWindow QLineEdit {{ font-size: 14px; padding: 9px 12px; }}
#settingsWindow QCheckBox {{ font-size: 14px; }}
#settingsWindow QPushButton {{ font-size: 14px; }}
#settingsWindow #result {{ font-size: 13px; }}
#nav::item {{ font-size: 14px; }}
"""


def card_shadow(widget):
    eff = QGraphicsDropShadowEffect(widget)
    eff.setBlurRadius(44)
    eff.setColor(QColor(0, 0, 0, 170))
    eff.setOffset(0, 10)
    widget.setGraphicsEffect(eff)
