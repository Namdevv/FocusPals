"""Render pet (QLabel + QTimer), thay cho Lottie/WebEngine.

Hỗ trợ 2 format skin trong assets/pet/<skin>/ (hoặc thẳng assets/pet/ cho mặc định):

1. PNG rời:
     - 1 file:   idle.png
     - sequence: idle_1.png, idle_2.png, ...

2. Spritesheet (format petdex/agentpet): pet.json + spritesheet.(webp|png)
     pet.json: {"spritesheetPath": "spritesheet.webp", ...}
     Sheet được cắt bằng alpha-gutter detection: mỗi ROW = 1 clip (animation),
     mỗi COLUMN trong row = 1 frame. Không cần grid metadata.
     Map state -> clip: idle=0, focus=1, break=2, done=3 (clamp theo số clip).

Không tìm thấy gì -> fallback emoji.
"""
import json
import os

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QLabel

from .paths import asset
from .states import PetState

# fps theo state: focus chạy nhanh, idle chậm
FPS = {
    PetState.IDLE: 3,
    PetState.FOCUS: 8,
    PetState.BREAK: 4,
    PetState.DONE: 6,
}

EMOJI = {
    PetState.IDLE: "🐱",
    PetState.FOCUS: "🐱",
    PetState.BREAK: "😺",
    PetState.DONE: "🎉",
}

# state -> clip index khi skin là spritesheet (thứ tự row trên sheet)
CLIP_ORDER = [PetState.IDLE, PetState.FOCUS, PetState.BREAK, PetState.DONE]

SHEET_EXTS = (".webp", ".png", ".gif")


def _segments(occupancy):
    """Các dải liên tiếp True trong list bool -> [(lo, hi), ...]."""
    result = []
    start = None
    for i, filled in enumerate(occupancy):
        if filled and start is None:
            start = i
        elif not filled and start is not None:
            result.append((start, i))
            start = None
    if start is not None:
        result.append((start, len(occupancy)))
    return result


def slice_spritesheet(img: QImage, alpha_threshold: int = 16):
    """Cắt spritesheet bằng alpha gutter -> list[list[QPixmap]] (rows=clips, cols=frames).

    Port từ SpriteSlicer.swift của AgentPet (MIT, Nguyễn Thành Đạt):
    https://github.com/ntd4996/agentpet
    """
    if img.isNull():
        return []
    img = img.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = img.width(), img.height()
    if w <= 0 or h <= 0:
        return []

    bpl = img.bytesPerLine()
    buf = bytes(img.constBits())
    # bảng 0/1 theo ngưỡng alpha (so sánh ở tốc độ C qua translate)
    tbl = bytes(1 if i > alpha_threshold else 0 for i in range(256))

    def alpha_row(y):
        # các byte alpha của hàng y (đã map 0/1)
        return buf[y * bpl: y * bpl + w * 4][3::4].translate(tbl)

    rows_alpha = [alpha_row(y) for y in range(h)]
    row_has = [b"\x01" in a for a in rows_alpha]
    row_bands = _segments(row_has)
    if not row_bands:
        return []

    clips = []
    for r_lo, r_hi in row_bands:
        col_has = bytearray(w)
        for y in range(r_lo, r_hi):
            a = rows_alpha[y]
            for x in range(w):
                if a[x]:
                    col_has[x] = 1
        clip = []
        for c_lo, c_hi in _segments([bool(v) for v in col_has]):
            rect = QRect(c_lo, r_lo, c_hi - c_lo, r_hi - r_lo)
            clip.append(QPixmap.fromImage(img.copy(rect)))
        if clip:
            clips.append(clip)
    return clips


class PetAnimator(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        # mouse phải rớt xuống PetWindow để drag/click hoạt động
        self.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAlignment(Qt.AlignCenter)
        self.setScaledContents(False)

        self._skin = ""
        self._state = PetState.IDLE
        self._clips = None          # list[list[QPixmap]] nếu skin là spritesheet
        self._frames = []           # frames của state hiện tại
        self._idx = 0
        self._size = 200

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._next_frame)

        self._load_skin_assets()
        self._reload()

    # ---- public API ----
    def set_size(self, px: int):
        self._size = int(px)
        self.resize(self._size, self._size)
        if self._frames:
            self._render_current()
        else:
            self._show_emoji()

    def set_skin(self, skin: str):
        self._skin = skin or ""
        self._load_skin_assets()
        self._reload()

    def set_state(self, state: PetState):
        if state == self._state and self._frames:
            return
        self._state = state
        self._reload()

    # ---- skin loading ----
    def _skin_dir(self) -> str:
        return asset("pet", self._skin) if self._skin else asset("pet")

    def _find_spritesheet(self, d) -> str:
        """Path sheet trong folder. pet.json là optional (chỉ để chỉ đúng file)."""
        # 1. nếu có pet.json + spritesheetPath -> dùng
        manifest = os.path.join(d, "pet.json")
        if os.path.isfile(manifest):
            try:
                with open(manifest, "r", encoding="utf-8") as f:
                    path = json.load(f).get("spritesheetPath", "")
                if path and os.path.isfile(os.path.join(d, path)):
                    return os.path.join(d, path)
            except Exception:
                pass
        # 2. không có json -> tự tìm file tên spritesheet.* trong folder
        for name in sorted(os.listdir(d)):
            low = name.lower()
            if low.startswith("spritesheet") and low.endswith(SHEET_EXTS):
                return os.path.join(d, name)
        return ""

    def _load_skin_assets(self):
        """Nếu skin là spritesheet -> cắt sẵn clips (1 lần). Ngược lại self._clips=None."""
        self._clips = None
        d = self._skin_dir()
        if not os.path.isdir(d):
            return
        sheet = self._find_spritesheet(d)
        if not sheet:
            return
        img = QImage(sheet)
        clips = slice_spritesheet(img)
        if clips:
            self._clips = clips

    # ---- frame selection ----
    def _frames_for_state(self):
        if self._clips:
            idx = CLIP_ORDER.index(self._state) if self._state in CLIP_ORDER else 0
            idx = min(idx, len(self._clips) - 1)
            return self._clips[idx]
        return self._load_png_frames(self._state)

    def _load_png_frames(self, state: PetState):
        d = self._skin_dir()
        name = state.value

        single = os.path.join(d, f"{name}.png")
        if os.path.isfile(single):
            pm = QPixmap(single)
            return [pm] if not pm.isNull() else []

        frames = []
        i = 1
        while True:
            f = os.path.join(d, f"{name}_{i}.png")
            if not os.path.isfile(f):
                break
            pm = QPixmap(f)
            if not pm.isNull():
                frames.append(pm)
            i += 1
        return frames

    # ---- rendering ----
    def _reload(self):
        self._frames = self._frames_for_state()
        self._idx = 0
        self._timer.stop()

        if self._frames:
            self.setText("")
            self.setStyleSheet("background: transparent;")
            self._render_current()
            if len(self._frames) > 1:
                fps = FPS.get(self._state, 3)
                self._timer.start(max(1, int(1000 / fps)))
        else:
            self._show_emoji()

    def _next_frame(self):
        if not self._frames:
            return
        self._idx = (self._idx + 1) % len(self._frames)
        self._render_current()

    def _render_current(self):
        if not self._frames:
            return
        pm = self._frames[self._idx]
        self.setPixmap(
            pm.scaled(
                self._size,
                self._size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation,
            )
        )

    def _show_emoji(self):
        self.setPixmap(QPixmap())
        self.setText(EMOJI.get(self._state, "🐱"))
        self.setStyleSheet(
            f"font-size: {int(self._size * 0.6)}px; background: transparent;"
        )
