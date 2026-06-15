"""Settings: cửa sổ đầy đủ (sidebar trái + trang nội dung), không phải popup.

Trang: Pet · Hiển thị · Khung chat · Nhạc · Tạo pet · Hệ thống · Thông tin.
Trang "Tạo pet": upload spritesheet/PNG → tự xoá nền caro → check → lưu skin.
"""
import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPixmap
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QPushButton,
    QScrollArea,
    QSlider,
    QStackedWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from . import pet_builder, theme
from ..core import skins, storage
from ..core.paths import asset
from ..services import autostart

AUDIO_EXT = (".mp3", ".wav", ".ogg", ".m4a", ".flac")
IMG_FILTER = "Ảnh (*.png *.webp *.gif *.jpg *.jpeg)"

NAV = [
    "🐾  Pet",
    "🖥  Hiển thị",
    "💬  Khung chat",
    "🎵  Nhạc",
    "✨  Tạo pet",
    "⚙  Hệ thống",
    "ℹ  Thông tin",
]


class SettingsDialog(QWidget):
    def __init__(self, window):
        super().__init__(None)
        self.win = window
        self.s = window.settings
        self._bubble_color = str(self.s.get("bubble_color", "#ffffff"))
        # state trang Tạo pet
        self._create_mode = ""        # "sheet" | "png"
        self._sheet_img = None        # QImage đã xử lý chờ lưu
        self._png_files = []
        self._centered = False

        self.setObjectName("settingsWindow")
        self.setWindowTitle("FocusPals — Cài đặt")
        self.setMinimumSize(760, 540)
        self.setStyleSheet(theme.QSS)
        self._build()

    # ---- layout gốc: sidebar + stack ----
    def _build(self):
        root = QHBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.nav = QListWidget()
        self.nav.setObjectName("nav")
        self.nav.setFixedWidth(190)
        self.nav.addItems(NAV)
        self.nav.setCurrentRow(0)
        self.nav.currentRowChanged.connect(lambda i: self.stack.setCurrentIndex(i))
        root.addWidget(self.nav)

        self.stack = QStackedWidget()
        self.stack.setObjectName("stack")
        root.addWidget(self.stack, 1)

        for builder in (
            self._page_pet,
            self._page_display,
            self._page_bubble,
            self._page_music,
            self._page_create,
            self._page_system,
            self._page_info,
        ):
            self.stack.addWidget(self._scroll(builder))

    def _scroll(self, builder):
        """Bọc 1 page trong QScrollArea (page dài vẫn cuộn được)."""
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(28, 24, 28, 24)
        box.setSpacing(12)
        builder(box)
        box.addStretch(1)

        sc = QScrollArea()
        sc.setWidgetResizable(True)
        sc.setWidget(page)
        return sc

    # ---- widget helper ----
    def _title(self, box, text):
        lbl = QLabel(text)
        lbl.setObjectName("title")
        box.addWidget(lbl)

    def _section(self, box, text):
        lbl = QLabel(text)
        lbl.setObjectName("section")
        box.addWidget(lbl)

    def _hint(self, box, text):
        lbl = QLabel(text)
        lbl.setObjectName("hint")
        lbl.setWordWrap(True)
        box.addWidget(lbl)

    def _slider_row(self, box, title, lo, hi, val):
        row = QHBoxLayout()
        t = QLabel(title)
        t.setObjectName("section")
        v = QLabel("")
        v.setObjectName("value")
        v.setAlignment(Qt.AlignRight)
        row.addWidget(t)
        row.addWidget(v)
        box.addLayout(row)
        sl = QSlider(Qt.Horizontal)
        sl.setRange(lo, hi)
        sl.setValue(val)
        box.addWidget(sl)
        return sl, v

    # ======== PAGES ========
    def _page_pet(self, box):
        self._title(box, "🐾  Pet")
        self._section(box, "CHỌN SKIN")
        self.pet = QComboBox()
        self.pet.setCursor(Qt.PointingHandCursor)
        self.pet.currentIndexChanged.connect(self._on_pet)
        box.addWidget(self.pet)
        self._hint(box, "Skin mới tạo ở trang “Tạo pet” sẽ hiện ở đây.")
        self._load_skins()

    def _page_display(self, box):
        self._title(box, "🖥  Hiển thị")
        self.size, self.size_v = self._slider_row(
            box, "KÍCH THƯỚC", 120, 360, int(self.s.get("pet_size", 200))
        )
        self.size.valueChanged.connect(self._on_size)
        self._on_size(self.size.value(), save=False)

        self.op, self.op_v = self._slider_row(
            box, "ĐỘ TRONG SUỐT", 30, 100, int(self.s.get("opacity", 100))
        )
        self.op.valueChanged.connect(self._on_opacity)
        self._on_opacity(self.op.value(), save=False)

        self.top = QCheckBox("Luôn nổi trên cùng")
        self.top.setChecked(bool(self.s.get("always_on_top", True)))
        self.top.toggled.connect(self._on_top)
        box.addSpacing(6)
        box.addWidget(self.top)

    def _page_bubble(self, box):
        self._title(box, "💬  Khung chat")
        self._hint(box, "Khung đếm ngược + câu động lực nổi trên đầu pet lúc focus.")
        crow = QHBoxLayout()
        cl = QLabel("MÀU NỀN")
        cl.setObjectName("section")
        self.color_btn = QPushButton()
        self.color_btn.setCursor(Qt.PointingHandCursor)
        self.color_btn.clicked.connect(self._on_bubble_color)
        self._update_color_btn()
        crow.addWidget(cl)
        crow.addWidget(self.color_btn)
        box.addLayout(crow)

        self.bop, self.bop_v = self._slider_row(
            box, "ĐỘ MỜ NỀN", 50, 100, int(self.s.get("bubble_opacity", 95))
        )
        self.bop.valueChanged.connect(self._on_bubble_opacity)
        self.bop_v.setText(f"{self.bop.value()}%")

    def _page_music(self, box):
        self._title(box, "🎵  Nhạc")
        self._section(box, "NHẠC MẶC ĐỊNH")
        self.music = QComboBox()
        self.music.setCursor(Qt.PointingHandCursor)
        self.music.currentIndexChanged.connect(self._on_music)
        box.addWidget(self.music)
        add = QPushButton("➕  Thêm nhạc từ máy")
        add.setObjectName("ghost")
        add.setCursor(Qt.PointingHandCursor)
        add.clicked.connect(self._add_music)
        box.addWidget(add)
        self._load_music()

        self.vol, self.vol_v = self._slider_row(
            box, "ÂM LƯỢNG", 0, 100, int(self.s.get("volume", 60))
        )
        self.vol.valueChanged.connect(self._on_volume)
        self.vol_v.setText(f"{self.vol.value()}%")

    def _page_system(self, box):
        self._title(box, "⚙  Hệ thống")
        self.auto = QCheckBox("Chạy cùng Windows")
        self.auto.setChecked(autostart.is_enabled())
        self.auto.toggled.connect(self._on_auto)
        box.addWidget(self.auto)

        box.addSpacing(8)
        reset = QPushButton("↺  Đặt lại vị trí pet")
        reset.setObjectName("ghost")
        reset.setCursor(Qt.PointingHandCursor)
        reset.clicked.connect(self._reset_pos)
        box.addWidget(reset)

    def _page_info(self, box):
        self._title(box, "ℹ  Thông tin")
        self._section(box, "ỨNG DỤNG")
        self._hint(box, "FocusPals — desktop pet + Pomodoro. Render PNG sprite (Qt thuần).")
        self._section(box, "DỮ LIỆU")
        self._hint(box, f"Settings & lịch sử: {storage.APP_DIR}")
        self._hint(box, f"Pet bundled: {skins.bundled_dir()}")
        self._hint(box, f"Pet tự tạo: {skins.USER_PETS_DIR}")
        self._section(box, "ĐỊNH DẠNG PET (petdex)")
        self._hint(
            box,
            "Spritesheet cắt bằng alpha-gutter: mỗi HÀNG = 1 clip "
            "(idle/focus/break/done), mỗi CỘT = 1 frame. Nền phải trong suốt.",
        )
        self._section(box, "CREDITS")
        self._hint(box, "Tương thích pet pack format petdex. MIT © 2026 Nam TRAN.")

    # ======== PAGE: TẠO PET ========
    def _page_create(self, box):
        self._title(box, "✨  Tạo pet")
        self._hint(
            box,
            "Upload spritesheet (1 file) hoặc PNG rời (tên chứa idle/focus/break/done). "
            "App tự xoá nền caro, kiểm tra rồi lưu thành skin.",
        )

        self._section(box, "TÊN SKIN")
        self.create_name = QLineEdit()
        self.create_name.setPlaceholderText("vd: my_cat")
        box.addWidget(self.create_name)

        self.auto_clean = QCheckBox("Tự xoá nền caro / nền đặc (alpha → trong suốt)")
        self.auto_clean.setChecked(True)
        box.addWidget(self.auto_clean)

        prow = QHBoxLayout()
        prow.setSpacing(8)
        b_sheet = QPushButton("🖼  Chọn spritesheet")
        b_sheet.setObjectName("ghost")
        b_sheet.setCursor(Qt.PointingHandCursor)
        b_sheet.clicked.connect(self._pick_sheet)
        b_png = QPushButton("🗂  Chọn PNG rời")
        b_png.setObjectName("ghost")
        b_png.setCursor(Qt.PointingHandCursor)
        b_png.clicked.connect(self._pick_pngs)
        prow.addWidget(b_sheet)
        prow.addWidget(b_png)
        box.addLayout(prow)

        # preview + kết quả check
        mid = QHBoxLayout()
        mid.setSpacing(12)
        self.preview = QLabel("preview")
        self.preview.setObjectName("preview")
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setFixedSize(120, 120)
        mid.addWidget(self.preview)
        self.create_result = QTextEdit()
        self.create_result.setObjectName("result")
        self.create_result.setReadOnly(True)
        self.create_result.setMinimumHeight(120)
        mid.addWidget(self.create_result, 1)
        box.addLayout(mid)

        self.create_btn = QPushButton("✨  Tạo pet")
        self.create_btn.setObjectName("primary")
        self.create_btn.setCursor(Qt.PointingHandCursor)
        self.create_btn.setEnabled(False)
        self.create_btn.clicked.connect(self._create_pet)
        box.addWidget(self.create_btn)

    # ---- create handlers ----
    def _set_result(self, res: dict, header: str = ""):
        lines = []
        if header:
            lines.append(header)
        lines += res.get("lines", [])
        for w in res.get("warnings", []):
            lines.append(f"⚠️  {w}")
        for e in res.get("errors", []):
            lines.append(f"❌  {e}")
        if res.get("ok"):
            lines.append("✅  Định dạng hợp lệ.")
        self.create_result.setPlainText("\n".join(lines))

    def _set_preview(self, pm: QPixmap):
        if pm and not pm.isNull():
            self.preview.setPixmap(
                pm.scaled(116, 116, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            )
        else:
            self.preview.setText("—")

    def _pick_sheet(self):
        f, _ = QFileDialog.getOpenFileName(self, "Chọn spritesheet", "", IMG_FILTER)
        if not f:
            return
        img = QImage(f)
        cleaned = ""
        if not img.isNull() and self.auto_clean.isChecked():
            amin, _amax = pet_builder.alpha_range(img)
            if amin == 255:
                img, n = pet_builder.strip_checkerboard(img)
                cleaned = f"🧹  Đã xoá nền caro: {n} pixel → trong suốt.\n"
        res = pet_builder.inspect_sheet(img)
        self._sheet_img = img if res["clips"] else None
        self._create_mode = "sheet" if res["clips"] else ""
        clips = res.get("clips")
        self._set_preview(clips[0][0] if clips and clips[0] else QPixmap())
        if not self.create_name.text().strip():
            self.create_name.setText(os.path.splitext(os.path.basename(f))[0])
        self._set_result(res, cleaned + f"Nguồn: {os.path.basename(f)}")
        self.create_btn.setEnabled(res["ok"])

    def _pick_pngs(self):
        files, _ = QFileDialog.getOpenFileNames(
            self, "Chọn PNG rời (idle/focus/break/done)", "", "PNG (*.png)"
        )
        if not files:
            return
        matched = [(pet_builder.match_state(f), f) for f in files]
        good = [(st, f) for st, f in matched if st]
        self._png_files = [f for _st, f in good]
        self._create_mode = "png" if good else ""
        lines = []
        for st, f in matched:
            tag = f"→ {st}" if st else "→ (bỏ qua, tên không khớp state)"
            lines.append(f"{os.path.basename(f)}  {tag}")
        ok = bool(good)
        if not ok:
            lines.append("❌  Không file nào khớp idle/focus/break/done.")
        first = next((f for st, f in good if st == "idle"), good[0][1] if good else "")
        self._set_preview(QPixmap(first) if first else QPixmap())
        self.create_result.setPlainText("\n".join(lines))
        self.create_btn.setEnabled(ok)

    def _create_pet(self):
        name = "".join(
            c for c in self.create_name.text().strip() if c not in '\\/:*?"<>|'
        ).strip()
        if not name:
            self.create_result.append("\n❌  Nhập tên skin hợp lệ.")
            return
        if self._create_mode == "sheet" and self._sheet_img is not None:
            d = pet_builder.save_sheet_skin(name, self._sheet_img)
            msg = f"✅  Đã tạo skin '{name}' (spritesheet)\n{d}"
        elif self._create_mode == "png" and self._png_files:
            d, saved = pet_builder.save_png_skin(name, self._png_files)
            msg = f"✅  Đã tạo skin '{name}' — state: {', '.join(saved)}\n{d}"
        else:
            self.create_result.append("\n❌  Chưa chọn file hợp lệ.")
            return

        self._load_skins()
        i = self.pet.findData(name)
        if i >= 0:
            self.pet.setCurrentIndex(i)   # apply skin mới luôn
        self.create_result.setPlainText(msg)
        self.create_btn.setEnabled(False)
        self._sheet_img = None
        self._png_files = []
        self._create_mode = ""

    # ---- loaders ----
    def _load_skins(self):
        self.pet.blockSignals(True)
        self.pet.clear()
        self.pet.addItem("🐱  Mặc định", "")
        for name in skins.list_skins():
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

    def _update_color_btn(self):
        c = QColor(self._bubble_color)
        if not c.isValid():
            c = QColor("#ffffff")
        txt = "#ffffff" if c.lightness() < 128 else "#1a1a1a"
        self.color_btn.setText(self._bubble_color.upper())
        self.color_btn.setStyleSheet(
            f"background:{c.name()}; color:{txt};"
            f"border:1px solid {theme.BORDER}; border-radius:10px;"
            "padding:7px 14px; font-size:12px; font-weight:600;"
        )

    def _on_bubble_color(self):
        col = QColorDialog.getColor(QColor(self._bubble_color), self, "Màu khung chat")
        if col.isValid():
            self._bubble_color = col.name()
            self._update_color_btn()
            self.win.apply_bubble(self._bubble_color, self.bop.value())
            self._save(bubble_color=self._bubble_color)

    def _on_bubble_opacity(self, v):
        self.bop_v.setText(f"{v}%")
        self.win.apply_bubble(self._bubble_color, v)
        self._save(bubble_opacity=v)

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

    # ---- show: refresh + center 1 lần ----
    def show(self):
        self._load_skins()
        self._load_music()
        super().show()
        if not self._centered:
            scr = QGuiApplication.primaryScreen().availableGeometry()
            self.move(scr.center().x() - self.width() // 2,
                      scr.center().y() - self.height() // 2)
            self._centered = True
        self.raise_()
        self.activateWindow()
