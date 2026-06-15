"""Bubble hình đám mây nổi trên đầu pet lúc focus.

- Hình mây dẹp, co theo chữ (vừa chữ).
- Câu động lực gõ từ từ kiểu typewriter.
- Bình thường hiện countdown; thỉnh thoảng câu động lực nháy lên rồi quay lại giờ.
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
    QTimer,
)
from PySide6.QtGui import (
    QColor,
    QGuiApplication,
    QPainter,
    QPainterPath,
    QPolygonF,
)
from PySide6.QtWidgets import (
    QLabel,
    QLayout,
    QVBoxLayout,
    QWidget,
)

TAIL_W = 14             # bề ngang đuôi tam giác
TAIL_H = 8              # chiều cao đuôi trỏ xuống pet
RADIUS = 0              # vuông góc (pixel style)
BORDER_W = 1.5          # viền
SHADOW_OFF = 3          # shadow cứng lệch phải-dưới (no blur)
PAD = 4                 # lề trong suốt quanh card (chừa chỗ shadow lệch)
# PawPause dùng "Courier New" làm font-pixel (monospace bold)
FONT_FAMILY = "'Courier New', monospace"
INK = "#181713"          # var(--ink)
LINE = "#242018"         # var(--line)

TYPE_MS = 38            # ms mỗi ký tự khi gõ chữ
FLASH_EVERY = 45        # giây giữa các lần nháy câu động lực
FLASH_DUR = 4200        # ms câu động lực hiện trước khi về giờ

# Câu động lực theo % thời gian CÒN LẠI. Mỗi mốc 1 list -> xoay vòng.
MESSAGES = [
    (0.85, ["Phần khó nhất đã qua 💪", "Một việc thôi nhé.", "Hít sâu, vào guồng."]),
    (0.60, ["Đang vào nhịp rồi đó.", "Kệ thông báo, lát xem.", "Tiến từng chút thôi."]),
    (0.35, ["Quá nửa rồi, tốt lắm!", "Phân tâm? Quay lại nào.", "Giữ phong độ nhé."]),
    (0.10, ["Sắp xong, ráng nhé!", "Về đích thôi nào.", "Một nỗ lực cuối."]),
    (0.0, ["Phút cuối, dồn lực! 🔥", "Gần chạm vạch rồi!"]),
]

BREAK_MESSAGES = [
    "Nghỉ chút nào ☕", "Vươn vai đi nào.", "Nhìn xa cho mắt nghỉ.",
    "Uống ngụm nước nhé.", "Hít thở, thư giãn.",
]


class _SpeechCard(QWidget):
    """Khung chat pixel: chữ nhật vuông + đuôi tam giác + shadow cứng lệch (no blur)."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self._bg = QColor("#ffffff")
        self._bg.setAlpha(245)
        self._line = QColor(LINE)   # viền + shadow (var(--line))

    def set_appearance(self, hex_color: str, opacity_pct: int):
        c = QColor(hex_color)
        if not c.isValid():
            c = QColor("#ffffff")
        c.setAlpha(int(max(50, min(100, opacity_pct)) / 100 * 255))
        self._bg = c
        dark = c.lightness() < 128
        # nền tối -> đường nét sáng; nền sáng -> đường nét line (var(--line))
        self._line = QColor("#f2f2f4") if dark else QColor(LINE)
        self.update()

    def _body_rect(self, w, h):
        return QRectF(1, 1, w - 1 - SHADOW_OFF, h - TAIL_H - 1 - SHADOW_OFF)

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
        body = self._body_rect(w, h)
        shape = self._shape(body)

        # 1) shadow cứng CHỈ trên hộp (box-shadow:3px 3px 0), không trên đuôi
        box = QPainterPath()
        box.addRoundedRect(body, RADIUS, RADIUS)
        p.setPen(Qt.NoPen)
        p.setBrush(self._line)
        p.translate(SHADOW_OFF, SHADOW_OFF)
        p.drawPath(box)
        p.translate(-SHADOW_OFF, -SHADOW_OFF)

        # 2) khung chính: nền + viền 1.5px (gồm cả đuôi)
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
        self._rot = 0
        self._flashing = False
        self._break_mode = False
        self._pet_rect = None
        self._anim_pos = None
        self._anim_op = None

        # typewriter
        self._type_full = ""
        self._type_i = 0
        self._type_timer = QTimer(self)
        self._type_timer.setInterval(TYPE_MS)
        self._type_timer.timeout.connect(self._type_step)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(PAD, PAD, PAD, PAD)
        outer.setSizeConstraint(QLayout.SetFixedSize)  # cửa sổ ôm sát nội dung
        self.card = _SpeechCard()
        outer.addWidget(self.card)

        # 1 label duy nhất: hiện time HOẶC câu động lực (đổi text + canh lề)
        # lề: padding 6/8 (PawPause) + chừa shadow lệch & đuôi
        cardlay = QVBoxLayout(self.card)
        cardlay.setContentsMargins(
            9, 6, 9 + SHADOW_OFF, 6 + TAIL_H + SHADOW_OFF
        )
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
        self._ink = "#f2f2f4" if dark else INK   # var(--ink); nền tối -> chữ sáng
        self.lbl.setStyleSheet(
            f"color:{self._ink}; font-family:{FONT_FAMILY};"
            "font-size:13px; font-weight:700; letter-spacing:0; background:transparent;"
        )

    # ---- API ----
    def start(self, total_secs: int, break_mode: bool = False):
        self._total = max(1, int(total_secs))
        self._rot = 0
        self._flashing = False
        self._break_mode = break_mode
        self._remaining = self._total
        self._show_time()
        QTimer.singleShot(450, self._flash)  # chào 1 câu lúc bắt đầu

    def set_remaining(self, secs: int):
        secs = max(0, int(secs))
        self._remaining = secs
        if not self._flashing:
            self._show_time()
        elapsed = self._total - secs
        if elapsed > 0 and elapsed % FLASH_EVERY == 0 and secs > 3:
            self._flash()

    def show_done(self):
        self._flashing = True
        self._type_message("Xong! Bạn giữ lời rồi 🎉")

    # ---- nội bộ ----
    def _show_time(self):
        self._type_timer.stop()
        self.lbl.setMinimumWidth(0)
        self.lbl.setAlignment(Qt.AlignCenter)
        m, s = divmod(self._remaining, 60)
        self.lbl.setText(f"{m:02d}:{s:02d}")
        self._reposition()

    def _flash(self):
        if self._remaining <= 3:
            return
        self._flashing = True
        self._type_message(self._pick_message())
        QTimer.singleShot(FLASH_DUR, self._unflash)

    def _unflash(self):
        if not self._flashing:
            return
        self._flashing = False
        self._show_time()

    def _type_message(self, full: str):
        """Chừa sẵn bề ngang theo full text (hộp không giật), gõ từng ký tự trái->phải."""
        self._type_timer.stop()
        self._type_full = full
        self._type_i = 0
        fm = self.lbl.fontMetrics()
        self.lbl.setMinimumWidth(fm.horizontalAdvance(full) + 2)
        self.lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.lbl.setText("")
        self._reposition()
        self._type_timer.start()

    def _type_step(self):
        self._type_i += 1
        self.lbl.setText(self._type_full[: self._type_i])
        if self._type_i >= len(self._type_full):
            self._type_timer.stop()

    def _pick_message(self):
        if self._break_mode:
            msg = BREAK_MESSAGES[self._rot % len(BREAK_MESSAGES)]
            self._rot += 1
            return msg
        frac = self._remaining / self._total if self._total else 0
        for thr, msgs in MESSAGES:
            if frac >= thr:
                msg = msgs[self._rot % len(msgs)]
                self._rot += 1
                return msg
        return ""

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
