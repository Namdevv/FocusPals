"""Pet window: frameless, trong suốt, always-on-top, drag/click, render Lottie."""
import os

from PySide6.QtCore import QPoint, Qt, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QApplication, QMenu, QWidget

from . import storage
from .music_player import MusicPlayer
from .notify import notify
from .paths import resource_path
from .settings_dialog import SettingsDialog
from .states import PetState
from .timer import CountdownTimer
from .timer_popup import TimerPopup

PET_SIZE = 200
DRAG_THRESHOLD = 5


class _Overlay(QWidget):
    """Lớp trong suốt phủ lên QWebEngineView để bắt mouse (web view nuốt event)."""

    def __init__(self, win):
        super().__init__(win)
        self.win = win
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.win.on_press(e.globalPosition().toPoint())
        elif e.button() == Qt.RightButton:
            self.win.show_context_menu(e.globalPosition().toPoint())

    def mouseMoveEvent(self, e):
        if e.buttons() & Qt.LeftButton:
            self.win.on_move(e.globalPosition().toPoint())

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.win.on_release()


class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.tray = None
        self.settings = storage.load_settings()
        self._session_minutes = 0
        self._drag_off = None
        self._press_pos = None
        self._moved = False
        self._size = int(self.settings.get("pet_size", PET_SIZE))

        self._apply_flags(bool(self.settings.get("always_on_top", True)))
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setWindowOpacity(int(self.settings.get("opacity", 100)) / 100.0)
        self.resize(self._size, self._size)

        # web view render Lottie
        self.view = QWebEngineView(self)
        self.view.setAttribute(Qt.WA_TranslucentBackground)
        self.view.page().setBackgroundColor(Qt.GlobalColor.transparent)
        self.view.setContextMenuPolicy(Qt.NoContextMenu)
        s = self.view.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.view.setGeometry(0, 0, self._size, self._size)
        html = resource_path(os.path.join("src", "pet_view.html"))
        self.view.loadFinished.connect(self._on_loaded)
        self.view.load(QUrl.fromLocalFile(html))

        # overlay bắt mouse
        self.overlay = _Overlay(self)
        self.overlay.setGeometry(0, 0, self._size, self._size)
        self.overlay.raise_()

        # core
        self.timer = CountdownTimer()
        self.music = MusicPlayer()
        self.music.set_volume(int(self.settings.get("volume", 60)))
        self.timer.tick.connect(self._on_tick)
        self.timer.finished.connect(self._on_finished)

        self.popup = TimerPopup(self)
        self.popup.startRequested.connect(self.start_focus)
        self.popup.stopRequested.connect(self.stop_focus)

        self.settings_dialog = SettingsDialog(self)

        self._restore_pos()

    def _on_loaded(self, ok):
        # áp skin đã lưu sau khi trang load xong
        skin = self.settings.get("pet_skin", "")
        if skin:
            self.apply_skin(skin)

    def _apply_flags(self, on_top: bool):
        flags = Qt.FramelessWindowHint | Qt.Tool
        if on_top:
            flags |= Qt.WindowStaysOnTopHint
        self.setWindowFlags(flags)

    # ---- vị trí ----
    def _restore_pos(self):
        pos = self.settings.get("pet_pos")
        if pos and isinstance(pos, (list, tuple)) and len(pos) == 2:
            x, y = int(pos[0]), int(pos[1])
            screen = QGuiApplication.screenAt(QPoint(x, y))
            area = (screen or QGuiApplication.primaryScreen()).availableGeometry()
            x = max(area.left(), min(x, area.right() - self._size))
            y = max(area.top(), min(y, area.bottom() - self._size))
            self.move(x, y)
        else:
            area = QGuiApplication.primaryScreen().availableGeometry()
            self.move(area.right() - self._size - 40, area.bottom() - self._size - 60)

    # ---- drag / click ----
    def on_press(self, gpos):
        self._drag_off = gpos - self.frameGeometry().topLeft()
        self._press_pos = gpos
        self._moved = False

    def on_move(self, gpos):
        if self._press_pos is None:
            return
        if (gpos - self._press_pos).manhattanLength() > DRAG_THRESHOLD:
            self._moved = True
        if self._drag_off is not None:
            self.move(gpos - self._drag_off)

    def on_release(self):
        if not self._moved:
            self.toggle_popup()
        else:
            self.settings["pet_pos"] = [self.x(), self.y()]
            storage.save_settings(self.settings)
        self._press_pos = None
        self._drag_off = None

    # ---- popup ----
    def _place_near_pet(self, widget):
        """Đặt widget LÊN TRÊN đầu pet, canh giữa, clamp trong màn hình."""
        widget.adjustSize()
        pet = self.frameGeometry()
        screen = QGuiApplication.screenAt(pet.center()) or QGuiApplication.primaryScreen()
        area = screen.availableGeometry()
        ww, wh = widget.width(), widget.height()

        # canh giữa ngang theo pet
        x = pet.center().x() - ww // 2
        x = max(area.left(), min(x, area.right() - ww))

        # ưu tiên phía trên pet, không đủ chỗ thì xuống dưới
        y = pet.top() - wh + 8
        if y < area.top():
            y = pet.bottom() - 8
        y = max(area.top(), min(y, area.bottom() - wh))

        widget.move(x, y)

    def toggle_popup(self):
        if self.popup.isVisible():
            self.popup.hide()
            return
        self.settings_dialog.hide()      # mở Timer -> tắt Settings
        self._place_near_pet(self.popup)
        self.popup.show()
        self.popup.raise_()
        self.popup.activateWindow()

    # ---- pet state ----
    def set_state(self, state: PetState):
        self.view.page().runJavaScript(f"setState('{state.value}')")

    # ---- settings apply (gọi từ SettingsDialog, live) ----
    def show_context_menu(self, gpos):
        menu = QMenu()
        menu.addAction("Mở / đóng Timer", self.toggle_popup)
        if self.timer.is_running():
            menu.addAction("Dừng focus", self.stop_focus)
        menu.addSeparator()
        menu.addAction("⚙  Cài đặt", self.open_settings)
        menu.addSeparator()
        menu.addAction("Thoát", QApplication.quit)
        menu.exec(gpos)

    def open_settings(self):
        if self.settings_dialog.isVisible():
            self.settings_dialog.hide()
            return
        self.popup.hide()                # mở Settings -> tắt Timer
        self.settings_dialog.show()
        self._place_near_pet(self.settings_dialog)

    def apply_size(self, px: int):
        self._size = int(px)
        self.resize(self._size, self._size)
        self.view.setGeometry(0, 0, self._size, self._size)
        self.overlay.setGeometry(0, 0, self._size, self._size)

    def apply_opacity(self, pct: int):
        self.setWindowOpacity(max(0.3, min(1.0, pct / 100.0)))

    def apply_skin(self, skin: str):
        safe = (skin or "").replace("'", "\\'")
        self.view.page().runJavaScript(f"setSkin('{safe}')")

    def set_always_on_top(self, on: bool):
        pos = self.pos()
        self._apply_flags(on)
        self.move(pos)
        self.show()  # re-apply flags cần show lại

    # ---- focus flow ----
    def start_focus(self, minutes: int, music_path: str, volume: int):
        self._session_minutes = minutes
        self.music.set_volume(volume)
        self.settings.update(
            {"volume": volume, "last_music": music_path, "last_minutes": minutes}
        )
        storage.save_settings(self.settings)

        self.set_state(PetState.FOCUS)
        if music_path:
            self.music.play(music_path)
        self.timer.start(minutes * 60)
        self.popup.set_running(True)

    def stop_focus(self):
        self.timer.stop()
        self.music.stop()
        self.set_state(PetState.IDLE)
        self.popup.set_idle()

    def _on_tick(self, remaining: int):
        self.popup.set_remaining(remaining)

    def _on_finished(self):
        self.music.stop()
        self.set_state(PetState.DONE)
        storage.add_history(self._session_minutes)
        notify(
            "Focus xong! 🎉",
            f"Hoàn thành {self._session_minutes} phút focus.",
            self.tray,
        )
        self.popup.set_idle()
        QTimer.singleShot(5000, lambda: self.set_state(PetState.IDLE))
