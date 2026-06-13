"""Settings UI: pet skin, kích thước, độ trong suốt, nhạc, autostart."""
import os

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from . import autostart, storage, theme
from .paths import asset

AUDIO_EXT = (".mp3", ".wav", ".ogg", ".m4a", ".flac")


class SettingsDialog(QWidget):
    def __init__(self, window):
        super().__init__(None)
        self.win = window
        self.s = window.settings
        self.setWindowFlags(
            Qt.Tool | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowTitle("Cài đặt")
        self._build()

    # ---- builders ----
    def _section(self, text):
        lbl = QLabel(text)
        lbl.setObjectName("section")
        self.body.addWidget(lbl)

    def _slider_row(self, title, lo, hi, val):
        row = QHBoxLayout()
        t = QLabel(title)
        t.setObjectName("section")
        v = QLabel("")
        v.setObjectName("value")
        v.setAlignment(Qt.AlignRight)
        row.addWidget(t)
        row.addWidget(v)
        self.body.addLayout(row)
        sl = QSlider(Qt.Horizontal)
        sl.setRange(lo, hi)
        sl.setValue(val)
        self.body.addWidget(sl)
        return sl, v

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(22, 22, 22, 22)
        card = QFrame()
        card.setObjectName("card")
        card.setFixedWidth(320)
        theme.card_shadow(card)
        outer.addWidget(card)
        self.setStyleSheet(theme.QSS)

        self.body = QVBoxLayout(card)
        self.body.setContentsMargins(22, 20, 22, 22)
        self.body.setSpacing(12)

        title = QLabel("⚙  Cài đặt")
        title.setObjectName("title")
        self.body.addWidget(title)

        # pet
        self._section("PET")
        self.pet = QComboBox()
        self.pet.setCursor(Qt.PointingHandCursor)
        self.pet.currentIndexChanged.connect(self._on_pet)
        self.body.addWidget(self.pet)
        self._load_skins()

        # size
        self.size, self.size_v = self._slider_row("KÍCH THƯỚC", 120, 360,
                                                   int(self.s.get("pet_size", 200)))
        self.size.valueChanged.connect(self._on_size)
        self._on_size(self.size.value(), save=False)

        # opacity
        self.op, self.op_v = self._slider_row("ĐỘ TRONG SUỐT", 30, 100,
                                              int(self.s.get("opacity", 100)))
        self.op.valueChanged.connect(self._on_opacity)
        self._on_opacity(self.op.value(), save=False)

        # music
        self._section("NHẠC MẶC ĐỊNH")
        self.music = QComboBox()
        self.music.setCursor(Qt.PointingHandCursor)
        self.music.currentIndexChanged.connect(self._on_music)
        self.body.addWidget(self.music)
        add = QPushButton("➕  Thêm nhạc từ máy")
        add.setObjectName("ghost")
        add.setCursor(Qt.PointingHandCursor)
        add.clicked.connect(self._add_music)
        self.body.addWidget(add)
        self._load_music()

        # volume
        self.vol, self.vol_v = self._slider_row("ÂM LƯỢNG", 0, 100,
                                               int(self.s.get("volume", 60)))
        self.vol.valueChanged.connect(self._on_volume)
        self.vol_v.setText(f"{self.vol.value()}%")

        # toggles
        self.top = QCheckBox("Luôn nổi trên cùng")
        self.top.setChecked(bool(self.s.get("always_on_top", True)))
        self.top.toggled.connect(self._on_top)
        self.body.addWidget(self.top)

        self.auto = QCheckBox("Chạy cùng Windows")
        self.auto.setChecked(autostart.is_enabled())
        self.auto.toggled.connect(self._on_auto)
        self.body.addWidget(self.auto)

        # buttons
        rowb = QHBoxLayout()
        rowb.setSpacing(8)
        reset = QPushButton("↺  Đặt lại vị trí")
        reset.setObjectName("ghost")
        reset.setCursor(Qt.PointingHandCursor)
        reset.clicked.connect(self._reset_pos)
        close = QPushButton("Xong")
        close.setObjectName("primary")
        close.setCursor(Qt.PointingHandCursor)
        close.clicked.connect(self.hide)
        rowb.addWidget(reset)
        rowb.addWidget(close)
        self.body.addLayout(rowb)

    # ---- loaders ----
    def _load_skins(self):
        self.pet.blockSignals(True)
        self.pet.clear()
        self.pet.addItem("🐱  Mặc định", "")
        d = asset("pet")
        if os.path.isdir(d):
            for name in sorted(os.listdir(d)):
                if os.path.isdir(os.path.join(d, name)):
                    self.pet.addItem("🐾  " + name, name)
        i = self.pet.findData(self.s.get("pet_skin", ""))
        if i >= 0:
            self.pet.setCurrentIndex(i)
        self.pet.blockSignals(False)

    def _load_music(self):
        self.music.blockSignals(True)
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
        i = self.music.findData(last)
        if i >= 0:
            self.music.setCurrentIndex(i)
        self.music.blockSignals(False)

    # ---- handlers ----
    def _save(self, **kw):
        self.s.update(kw)
        storage.save_settings(self.s)

    def _on_pet(self):
        skin = self.pet.currentData() or ""
        self.win.apply_skin(skin)
        self._save(pet_skin=skin)

    def _on_size(self, v, save=True):
        self.size_v.setText(f"{v}px")
        self.win.apply_size(v)
        if save:
            self._save(pet_size=v)

    def _on_opacity(self, v, save=True):
        self.op_v.setText(f"{v}%")
        self.win.apply_opacity(v)
        if save:
            self._save(opacity=v)

    def _on_music(self):
        self._save(last_music=self.music.currentData() or "")

    def _on_volume(self, v):
        self.vol_v.setText(f"{v}%")
        self.win.music.set_volume(v)
        self._save(volume=v)

    def _on_top(self, on):
        self.win.set_always_on_top(on)
        self._save(always_on_top=on)

    def _on_auto(self, on):
        if autostart.set_autostart(on):
            self._save(autostart=on)
        else:
            self.auto.blockSignals(True)
            self.auto.setChecked(autostart.is_enabled())
            self.auto.blockSignals(False)

    def _add_music(self):
        f, _ = QFileDialog.getOpenFileName(
            self, "Chọn nhạc", "", "Audio (*.mp3 *.wav *.ogg *.m4a *.flac)"
        )
        if f:
            self.music.addItem("🎵  " + os.path.basename(f), f)
            self.music.setCurrentIndex(self.music.count() - 1)

    def _reset_pos(self):
        self.s["pet_pos"] = None
        storage.save_settings(self.s)
        self.win._restore_pos()

    def show(self):
        self._load_skins()
        self._load_music()
        super().show()
        self.raise_()
        self.activateWindow()
