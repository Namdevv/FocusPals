"""Popup set thời gian focus + chọn nhạc + volume + countdown."""
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from . import storage
from .paths import asset

AUDIO_EXT = (".mp3", ".wav", ".ogg", ".m4a", ".flac")

STYLE = """
#card { background: #1e1f29; border-radius: 14px; border: 1px solid #33344a; }
QLabel { color: #c9cbe0; font-size: 12px; }
#title { color: #ffffff; font-size: 15px; font-weight: bold; }
#count { color: #8be9fd; font-size: 30px; font-weight: bold; }
QSpinBox, QComboBox { background: #2a2b3a; color: #eee; border: 1px solid #3c3d52;
    border-radius: 6px; padding: 4px; }
QPushButton { background: #3a3c52; color: #eee; border: none; border-radius: 6px;
    padding: 6px 10px; }
QPushButton:hover { background: #4a4d68; }
#start { background: #50fa7b; color: #11231a; font-weight: bold; }
#start:hover { background: #66ff90; }
QSlider::groove:horizontal { height: 5px; background: #3c3d52; border-radius: 2px; }
QSlider::handle:horizontal { background: #8be9fd; width: 14px; margin: -5px 0;
    border-radius: 7px; }
"""


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
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("card")
        outer.addWidget(card)
        self.setStyleSheet(STYLE)

        lay = QVBoxLayout(card)
        lay.setContentsMargins(16, 16, 16, 16)
        lay.setSpacing(10)

        title = QLabel("⏱  Focus Timer")
        title.setObjectName("title")
        lay.addWidget(title)

        # phút + preset
        row = QHBoxLayout()
        self.spin = QSpinBox()
        self.spin.setRange(1, 180)
        self.spin.setSuffix(" phút")
        self.spin.setValue(int(self.s.get("last_minutes", 25)))
        b25 = QPushButton("25")
        b50 = QPushButton("50")
        b25.clicked.connect(lambda: self.spin.setValue(25))
        b50.clicked.connect(lambda: self.spin.setValue(50))
        row.addWidget(self.spin, 1)
        row.addWidget(b25)
        row.addWidget(b50)
        lay.addLayout(row)

        # nhạc
        lay.addWidget(QLabel("Nhạc focus:"))
        self.music = QComboBox()
        lay.addWidget(self.music)
        add = QPushButton("➕  Thêm nhạc từ máy...")
        add.clicked.connect(self._add_music)
        lay.addWidget(add)
        self._load_music()

        # volume
        lay.addWidget(QLabel("Âm lượng:"))
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(int(self.s.get("volume", 60)))
        lay.addWidget(self.vol)

        # countdown
        self.count = QLabel("")
        self.count.setObjectName("count")
        self.count.setAlignment(Qt.AlignCenter)
        lay.addWidget(self.count)

        # start/stop
        self.btn = QPushButton("▶  Bắt đầu")
        self.btn.setObjectName("start")
        self.btn.clicked.connect(self._toggle)
        lay.addWidget(self.btn)

    def _load_music(self, select: str = None):
        self.music.clear()
        self.music.addItem("(Không nhạc)", "")
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

    def _toggle(self):
        if self._running:
            self.stopRequested.emit()
        else:
            self.startRequested.emit(
                self.spin.value(), self.music.currentData() or "", self.vol.value()
            )

    # gọi bởi PetWindow
    def set_running(self, on: bool):
        self._running = on
        self.btn.setText("■  Dừng" if on else "▶  Bắt đầu")
        self.spin.setEnabled(not on)
        self.music.setEnabled(not on)

    def set_remaining(self, secs: int):
        m, s = divmod(max(0, secs), 60)
        self.count.setText(f"{m:02d}:{s:02d}")

    def set_idle(self):
        self.set_running(False)
        self.count.setText("")
