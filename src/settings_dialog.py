"""Settings UI: chọn pet skin, kích thước, độ trong suốt, nhạc, autostart..."""
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

from . import autostart, storage
from .paths import asset

AUDIO_EXT = (".mp3", ".wav", ".ogg", ".m4a", ".flac")

STYLE = """
#card { background: #1e1f29; border-radius: 14px; border: 1px solid #33344a; }
QLabel { color: #c9cbe0; font-size: 12px; }
#title { color: #ffffff; font-size: 16px; font-weight: bold; }
#hint { color: #6b6d85; font-size: 11px; }
QComboBox { background: #2a2b3a; color: #eee; border: 1px solid #3c3d52;
    border-radius: 6px; padding: 4px; }
QPushButton { background: #3a3c52; color: #eee; border: none; border-radius: 6px;
    padding: 6px 10px; }
QPushButton:hover { background: #4a4d68; }
#close { background: #8be9fd; color: #11231a; font-weight: bold; }
#close:hover { background: #a6f0ff; }
QCheckBox { color: #c9cbe0; font-size: 12px; }
QSlider::groove:horizontal { height: 5px; background: #3c3d52; border-radius: 2px; }
QSlider::handle:horizontal { background: #8be9fd; width: 14px; margin: -5px 0;
    border-radius: 7px; }
"""


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

    # ---- helpers ----
    def _row(self, label_text):
        lbl = QLabel(label_text)
        self.body.addWidget(lbl)
        return lbl

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        card = QFrame()
        card.setObjectName("card")
        outer.addWidget(card)
        self.setStyleSheet(STYLE)

        self.body = QVBoxLayout(card)
        self.body.setContentsMargins(18, 18, 18, 18)
        self.body.setSpacing(8)

        title = QLabel("⚙  Cài đặt FocusPals")
        title.setObjectName("title")
        self.body.addWidget(title)

        # --- Pet skin ---
        self._row("Pet:")
        self.pet = QComboBox()
        self._load_skins()
        self.pet.currentIndexChanged.connect(self._on_pet)
        self.body.addWidget(self.pet)

        # --- Size ---
        self.size_lbl = QLabel()
        self.body.addWidget(self.size_lbl)
        self.size = QSlider(Qt.Horizontal)
        self.size.setRange(120, 360)
        self.size.setValue(int(self.s.get("pet_size", 200)))
        self.size.valueChanged.connect(self._on_size)
        self.body.addWidget(self.size)
        self._upd_size_lbl(self.size.value())

        # --- Opacity ---
        self.op_lbl = QLabel()
        self.body.addWidget(self.op_lbl)
        self.op = QSlider(Qt.Horizontal)
        self.op.setRange(30, 100)
        self.op.setValue(int(self.s.get("opacity", 100)))
        self.op.valueChanged.connect(self._on_opacity)
        self.body.addWidget(self.op)
        self._upd_op_lbl(self.op.value())

        # --- Default music ---
        self._row("Nhạc mặc định:")
        self.music = QComboBox()
        self._load_music()
        self.music.currentIndexChanged.connect(self._on_music)
        self.body.addWidget(self.music)
        add = QPushButton("➕  Thêm nhạc từ máy...")
        add.clicked.connect(self._add_music)
        self.body.addWidget(add)

        # --- Default volume ---
        self.vol_lbl = QLabel()
        self.body.addWidget(self.vol_lbl)
        self.vol = QSlider(Qt.Horizontal)
        self.vol.setRange(0, 100)
        self.vol.setValue(int(self.s.get("volume", 60)))
        self.vol.valueChanged.connect(self._on_volume)
        self.body.addWidget(self.vol)
        self._upd_vol_lbl(self.vol.value())

        # --- toggles ---
        self.top = QCheckBox("Luôn nổi trên cùng (always-on-top)")
        self.top.setChecked(bool(self.s.get("always_on_top", True)))
        self.top.toggled.connect(self._on_top)
        self.body.addWidget(self.top)

        self.auto = QCheckBox("Chạy cùng Windows khi khởi động")
        self.auto.setChecked(autostart.is_enabled())
        self.auto.toggled.connect(self._on_auto)
        self.body.addWidget(self.auto)

        # --- buttons ---
        rowb = QHBoxLayout()
        reset = QPushButton("↺  Đặt lại vị trí pet")
        reset.clicked.connect(self._reset_pos)
        close = QPushButton("Đóng")
        close.setObjectName("close")
        close.clicked.connect(self.hide)
        rowb.addWidget(reset)
        rowb.addWidget(close)
        self.body.addLayout(rowb)

        hint = QLabel("Pet skin = folder trong assets/pet/. Thiếu file → hiện emoji.")
        hint.setObjectName("hint")
        hint.setWordWrap(True)
        self.body.addWidget(hint)

    # ---- loaders ----
    def _load_skins(self):
        self.pet.blockSignals(True)
        self.pet.clear()
        self.pet.addItem("Mặc định", "")
        d = asset("pet")
        if os.path.isdir(d):
            for name in sorted(os.listdir(d)):
                p = os.path.join(d, name)
                if os.path.isdir(p):
                    self.pet.addItem("🐾  " + name, name)
        cur = self.s.get("pet_skin", "")
        i = self.pet.findData(cur)
        if i >= 0:
            self.pet.setCurrentIndex(i)
        self.pet.blockSignals(False)

    def _load_music(self):
        self.music.blockSignals(True)
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
        i = self.music.findData(last)
        if i >= 0:
            self.music.setCurrentIndex(i)
        self.music.blockSignals(False)

    # ---- label updaters ----
    def _upd_size_lbl(self, v):
        self.size_lbl.setText(f"Kích thước pet: {v}px")

    def _upd_op_lbl(self, v):
        self.op_lbl.setText(f"Độ trong suốt: {v}%")

    def _upd_vol_lbl(self, v):
        self.vol_lbl.setText(f"Âm lượng mặc định: {v}%")

    # ---- handlers (live apply + save) ----
    def _save(self, **kw):
        self.s.update(kw)
        storage.save_settings(self.s)

    def _on_pet(self):
        skin = self.pet.currentData() or ""
        self.win.apply_skin(skin)
        self._save(pet_skin=skin)

    def _on_size(self, v):
        self._upd_size_lbl(v)
        self.win.apply_size(v)
        self._save(pet_size=v)

    def _on_opacity(self, v):
        self._upd_op_lbl(v)
        self.win.apply_opacity(v)
        self._save(opacity=v)

    def _on_music(self):
        self._save(last_music=self.music.currentData() or "")

    def _on_volume(self, v):
        self._upd_vol_lbl(v)
        self.win.music.set_volume(v)
        self._save(volume=v)

    def _on_top(self, on):
        self.win.set_always_on_top(on)
        self._save(always_on_top=on)

    def _on_auto(self, on):
        ok = autostart.set_autostart(on)
        if not ok:
            self.auto.blockSignals(True)
            self.auto.setChecked(autostart.is_enabled())
            self.auto.blockSignals(False)
        else:
            self._save(autostart=on)

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

    # mở lại refresh danh sách
    def show(self):
        self._load_skins()
        self._load_music()
        super().show()
        self.raise_()
        self.activateWindow()
