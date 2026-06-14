"""Popup focus timer: time display lớn, preset pills, ± stepper, nhạc, volume."""
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from . import theme
from ..core import storage
from ..core.paths import asset

AUDIO_EXT = (".mp3", ".wav", ".ogg", ".m4a", ".flac")
PRESETS = [15, 25, 45, 60]
MIN_M, MAX_M, STEP_M = 1, 180, 5


class TimerPopup(QWidget):
    startRequested = Signal(int, str, int)  # minutes, music_path, volume
    stopRequested = Signal()

    def __init__(self, parent=None):
        super().__init__(None)
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.s = storage.load_settings()
        self._running = False
        self._minutes = int(self.s.get("last_minutes", 25))
        self._pills = {}
        self._build()
        self._refresh_time()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 18, 18, 18)  # chừa chỗ cho shadow
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(232)
        theme.card_shadow(card)
        outer.addWidget(card)
        self.setStyleSheet(theme.QSS)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 14, 16, 16)
        lay.setSpacing(9)

        title = QLabel("⏱  Focus")
        title.setObjectName("title")
        lay.addWidget(title)

        # time display lớn (vừa là setup vừa là countdown)
        self.time_lbl = QLabel("25:00")
        self.time_lbl.setObjectName("timeBig")
        self.time_lbl.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.time_lbl)

        # preset pills
        grid = QGridLayout()
        grid.setSpacing(6)
        for i, m in enumerate(PRESETS):
            b = QPushButton(f"{m}m")
            b.setProperty("pill", True)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, mm=m: self._set_minutes(mm))
            grid.addWidget(b, 0, i)
            self._pills[m] = b
        lay.addLayout(grid)
        self.presets_row = grid

        # custom ± stepper
        step = QHBoxLayout()
        step.setSpacing(12)
        minus = QPushButton("−")
        minus.setProperty("step", True)
        minus.setCursor(Qt.PointingHandCursor)
        minus.clicked.connect(lambda: self._set_minutes(self._minutes - STEP_M))
        plus = QPushButton("+")
        plus.setProperty("step", True)
        plus.setCursor(Qt.PointingHandCursor)
        plus.clicked.connect(lambda: self._set_minutes(self._minutes + STEP_M))
        self.custom_lbl = QLabel("tùy chỉnh")
        self.custom_lbl.setObjectName("value")
        self.custom_lbl.setAlignment(Qt.AlignCenter)
        step.addStretch()
        step.addWidget(minus)
        step.addWidget(self.custom_lbl)
        step.addWidget(plus)
        step.addStretch()
        lay.addLayout(step)
        self._stepper = [minus, plus]

        # nhạc
        sec1 = QLabel("NHẠC")
        sec1.setObjectName("section")
        lay.addWidget(sec1)
        self.music = QComboBox()
        self.music.setCursor(Qt.PointingHandCursor)
        lay.addWidget(self.music)
        add = QPushButton("➕  Thêm nhạc từ máy")
        add.setObjectName("ghost")
        add.setCursor(Qt.PointingHandCursor)
        add.clicked.connect(self._add_music)
        lay.addWidget(add)
        self._load_music()

        # volume
        vrow = QHBoxLayout()
        vsec = QLabel("ÂM LƯỢNG")
        vsec.setObjectName("section")
        self.vol_val = QLabel("")
        self.vol_val.setObjectName("value")
        self.vol_val.setAlignment(Qt.AlignRight)
        vrow.addWidget(vsec)
        vrow.addWidget(self.vol_val)
        lay.addLayout(vrow)
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(int(self.s.get("volume", 60)))
        self.vol.valueChanged.connect(lambda v: self.vol_val.setText(f"{v}%"))
        self.vol_val.setText(f"{self.vol.value()}%")
        lay.addWidget(self.vol)

        # start / stop
        self.btn = QPushButton("▶  Bắt đầu")
        self.btn.setObjectName("primary")
        self.btn.setCursor(Qt.PointingHandCursor)
        self.btn.clicked.connect(self._toggle)
        lay.addWidget(self.btn)

    # ---- minutes ----
    def _set_minutes(self, m):
        self._minutes = max(MIN_M, min(MAX_M, int(m)))
        self._refresh_time()

    def _refresh_time(self):
        if not self._running:
            self.time_lbl.setText(f"{self._minutes:02d}:00")
        is_preset = self._minutes in self._pills
        for m, b in self._pills.items():
            b.setProperty("on", m == self._minutes)
            b.style().unpolish(b)
            b.style().polish(b)
        self.custom_lbl.setText(
            "tùy chỉnh" if is_preset else f"{self._minutes} phút"
        )

    # ---- music ----
    def _load_music(self, select: str = None):
        self.music.clear()
        self.music.addItem("🔇  Không nhạc", "")
        d = asset("music")
        if os.path.isdir(d):
            for f in sorted(os.listdir(d)):
                if f.lower().endswith(AUDIO_EXT):
                    self.music.addItem("🎵  " + f, os.path.join(d, f))
        last = self.s.get("last_music", "")
        if last and os.path.isfile(last) and self.music.findData(last) < 0:
            self.music.addItem("🎵  " + os.path.basename(last), last)
        target = select or last
        if target:
            i = self.music.findData(target)
            if i >= 0:
                self.music.setCurrentIndex(i)

    def _add_music(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Chọn nhạc", "", "Audio (*.mp3 *.wav *.ogg *.m4a *.flac)"
        )
        if f:
            self.music.addItem("🎵  " + os.path.basename(f), f)
            self.music.setCurrentIndex(self.music.count() - 1)

    # ---- start/stop ----
    def _toggle(self):
        if self._running:
            self.stopRequested.emit()
        else:
            self.startRequested.emit(
                self._minutes, self.music.currentData() or "", self.vol.value()
            )

    def _set_controls_enabled(self, on: bool):
        for b in self._pills.values():
            b.setEnabled(on)
        for b in self._stepper:
            b.setEnabled(on)
        self.music.setEnabled(on)

    def set_running(self, on: bool):
        self._running = on
        if on:
            self.btn.setText("■  Dừng")
            self.btn.setObjectName("danger")
        else:
            self.btn.setText("▶  Bắt đầu")
            self.btn.setObjectName("primary")
        self.btn.style().unpolish(self.btn)
        self.btn.style().polish(self.btn)
        self._set_controls_enabled(not on)
        if not on:
            self._refresh_time()

    def set_remaining(self, secs: int):
        m, s = divmod(max(0, secs), 60)
        self.time_lbl.setText(f"{m:02d}:{s:02d}")

    def set_idle(self):
        self.set_running(False)
