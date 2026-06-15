"""Bubble hình chat nhỏ nổi trên đầu pet lúc focus.

- Chỉ hiện countdown MM:SS (monospace nên bề ngang cố định, box không giật).
- Khung bo góc mềm, viền mảnh, đổ bóng nhẹ -> dịu mắt, không nổi bật.
- Nền + độ mờ + màu chữ tương phản tuỳ chỉnh.

Frameless, trong suốt, on-top, click xuyên qua. PetWindow gọi:
    bubble.start(total_secs[, break_mode]); bubble.animate_in(pet_rect)
    bubble.set_remaining(secs); bubble.place_above(pet_rect)
    bubble.show_done(); bubble.hide()
    bubble.set_appearance(hex_color, opacity_pct)
"""
from PySide6.QtCore import (
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRectF,
    Qt,
)
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QGraphicsDropShadowEffect,
    QLabel,
    QLayout,
    QVBoxLayout,
    QWidget,
)

TAIL_W = 13            # bề ngang đuôi tam giác
TAIL_H = 7             # chiều cao đuôi trỏ xuống pet
RADIUS = 9             # bo góc mềm
BORDER_W = 1.0         # viền mảnh
PAD = 14               # lề trong suốt quanh card (chừa chỗ đổ bóng mềm)
FONT_FAMILY = "'Courier New', monospace"
INK = "#33312b"        # chữ dịu (ngả nâu nhạt, không đen gắt)


class _SpeechCard(QWidget):
    """Khung chat: chữ nhật bo góc + đuôi tam giác, viền mảnh, nền tuỳ chỉnh."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._bg = QColor("#ffffff")
        self._bg.setAlpha(235)
        self._line = QColor(0, 0, 0, 38)   # viền hairline dịu

    def set_appearance(self, hex_color: str, opacity_pct: int):
        c = QColor(hex_color)
        if not c.isValid():
            c = QColor("#ffffff")
        c.setAlpha(int(max(50, min(100, opacity_pct)) / 100 * 255))
        self._bg = c
        dark = c.lightness() < 128
        # nền tối -> viền sáng mờ; nền sáng -> viền tối mờ (hairline)
        self._line = QColor(255, 255, 255, 46) if dark else QColor(0, 0, 0, 38)
        self.update()

    def _body_rect(self, w, h):
        m = BORDER_W
        return QRectF(m, m, w - 2 * m, h - TAIL_H - 2 * m)

    def _shape(self, body):
        path = QPainterPath()
        path.setFillRule(Qt.WindingFill)
        path.addRoundedRect(body, RADIUS, RADIUS)
        cx = body.center().x()
        tail = QPolygonF([
            QPointF(cx - TAIL_W / 2, body.bottom() - 1),
            QPointF(cx + TAIL_W / 2, body.bottom() - 1),
            QPointF(cx, body.bottom() + TAIL_H),
        ])
        tpath = QPainterPath()
        tpath.addPolygon(tail)
        return path.united(tpath)

    def paintEvent(self, _e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()
        if w < 8 or h < 8:
            return
        shape = self._shape(self._body_rect(w, h))
        qpen = p.pen()
        qpen.setColor(self._line)
        qpen.setWidthF(BORDER_W)
        p.setPen(qpen)
        p.setBrush(self._bg)
        p.drawPath(shape)


class FocusBubble(QWidget):
    def __init__(self, parent=None):
        super().__init__(None)
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

        self._total = 0
        self._remaining = 0
        self._break_mode = False
        self._pet_rect = None
        self._anim_pos = None
        self._anim_op = None

        outer = QVBoxLayout(self)
        outer.setContentsMargins(PAD, PAD, PAD, PAD)
        outer.setSizeConstraint(QLayout.SetFixedSize)  # cửa sổ ôm sát nội dung
        self.card = _SpeechCard()
        outer.addWidget(self.card)

        # đổ bóng mềm, nhẹ (thay shadow cứng cũ) -> dịu, không gắt
        shadow = QGraphicsDropShadowEffect(self.card)
        shadow.setBlurRadius(16)
        shadow.setColor(QColor(0, 0, 0, 55))
        shadow.setOffset(0, 3)
        self.card.setGraphicsEffect(shadow)

        cardlay = QVBoxLayout(self.card)
        cardlay.setContentsMargins(11, 6, 11, 6 + TAIL_H)
        self.lbl = QLabel("25:00")
        self.lbl.setAlignment(Qt.AlignCenter)
        cardlay.addWidget(self.lbl)

        self._ink = INK
        self.set_appearance("#ffffff", 95)

    # ---- màu / độ mờ / chữ ----
    def set_appearance(self, hex_color: str, opacity_pct: int):
        self.card.set_appearance(hex_color, opacity_pct)
        c = QColor(hex_color)
        if not c.isValid():
            c = QColor("#ffffff")
        dark = c.lightness() < 128
        self._ink = "#f0f0f2" if dark else INK   # nền tối -> chữ sáng dịu
        self.lbl.setStyleSheet(
            f"color:{self._ink}; font-family:{FONT_FAMILY};"
            "font-size:13px; font-weight:600; letter-spacing:0.5px;"
            "background:transparent;"
        )

    # ---- API ----
    def start(self, total_secs: int, break_mode: bool = False):
        self._total = max(1, int(total_secs))
        self._break_mode = break_mode
        self._remaining = self._total
        self._show_time()

    def set_remaining(self, secs: int):
        self._remaining = max(0, int(secs))
        self._show_time()

    def show_done(self):
        self.lbl.setText("Xong 🎉")
        self._reposition()

    # ---- nội bộ ----
    def _show_time(self):
        m, s = divmod(self._remaining, 60)
        self.lbl.setText(f"{m:02d}:{s:02d}")
        self._reposition()

    # ---- animation xuất hiện: trượt xuống + mờ dần vào ----
    def animate_in(self, pet_rect):
        self._pet_rect = pet_rect
        self._show_time()
        target = self.pos()
        self.move(target.x(), target.y() - 16)
        self.setWindowOpacity(0.0)
        self.show()
        self.raise_()

        self._anim_pos = QPropertyAnimation(self, b"pos", self)
        self._anim_pos.setDuration(320)
        self._anim_pos.setStartValue(QPoint(target.x(), target.y() - 16))
        self._anim_pos.setEndValue(target)
        self._anim_pos.setEasingCurve(QEasingCurve.OutBack)

        self._anim_op = QPropertyAnimation(self, b"windowOpacity", self)
        self._anim_op.setDuration(260)
        self._anim_op.setStartValue(0.0)
        self._anim_op.setEndValue(1.0)
        self._anim_op.setEasingCurve(QEasingCurve.OutCubic)

        self._anim_pos.start()
        self._anim_op.start()

    # ---- vị trí ----
    def place_above(self, pet_rect):
        self._pet_rect = pet_rect
        self._reposition()

    def _reposition(self):
        if self._pet_rect is None:
            return
        self.adjustSize()
        screen = (
            QGuiApplication.screenAt(self._pet_rect.center())
            or QGuiApplication.primaryScreen()
        )
        area = screen.availableGeometry()
        ww, wh = self.width(), self.height()
        x = self._pet_rect.center().x() - ww // 2
        x = max(area.left(), min(x, area.right() - ww))
        y = max(area.top(), self._pet_rect.top() - wh + PAD + 4)
        self.move(x, y)
