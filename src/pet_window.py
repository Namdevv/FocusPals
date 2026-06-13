"""Pet window: frameless, trong suốt, always-on-top, drag/click, render Lottie."""
import os

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtWebEngineCore import QWebEngineSettings
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWidgets import QWidget

from . import storage
from .music_player import MusicPlayer
from .notify import notify
from .paths import resource_path
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

        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.resize(PET_SIZE, PET_SIZE)

        # web view render Lottie
        self.view = QWebEngineView(self)
        self.view.setAttribute(Qt.WA_TranslucentBackground)
        self.view.page().setBackgroundColor(Qt.GlobalColor.transparent)
        self.view.setContextMenuPolicy(Qt.NoContextMenu)
        s = self.view.settings()
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessFileUrls, True)
        s.setAttribute(QWebEngineSettings.WebAttribute.LocalContentCanAccessRemoteUrls, True)
        self.view.setGeometry(0, 0, PET_SIZE, PET_SIZE)
        html = resource_path(os.path.join("src", "pet_view.html"))
        self.view.load(QUrl.fromLocalFile(html))

        # overlay bắt mouse
        self.overlay = _Overlay(self)
        self.overlay.setGeometry(0, 0, PET_SIZE, PET_SIZE)
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

        self._restore_pos()

    # ---- vị trí ----
    def _restore_pos(self):
        pos = self.settings.get("pet_pos")
        if pos and isinstance(pos, (list, tuple)) and len(pos) == 2:
            self.move(int(pos[0]), int(pos[1]))
        else:
            geo = QGuiApplication.primaryScreen().availableGeometry()
            self.move(geo.right() - PET_SIZE - 40, geo.bottom() - PET_SIZE - 60)

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
    def toggle_popup(self):
        if self.popup.isVisible():
            self.popup.hide()
            return
        self.popup.adjustSize()
        geo = self.frameGeometry()
        x = geo.left() - self.popup.width() - 12
        if x < 0:
            x = geo.right() + 12
        self.popup.move(x, geo.top())
        self.popup.show()
        self.popup.raise_()
        self.popup.activateWindow()

    # ---- pet state ----
    def set_state(self, state: PetState):
        self.view.page().runJavaScript(f"setState('{state.value}')")

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
