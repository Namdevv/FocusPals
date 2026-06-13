"""Phát nhạc focus: loop vô hạn, chỉnh volume."""
from PySide6.QtCore import QObject, QUrl
from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer


class MusicPlayer(QObject):
    def __init__(self):
        super().__init__()
        self.out = QAudioOutput()
        self.player = QMediaPlayer()
        self.player.setAudioOutput(self.out)
        try:
            self.player.setLoops(QMediaPlayer.Loops.Infinite)
        except Exception:
            self.player.setLoops(-1)  # fallback: -1 = infinite
        self.out.setVolume(0.6)

    def set_volume(self, vol_0_100: int):
        self.out.setVolume(max(0.0, min(1.0, vol_0_100 / 100.0)))

    def play(self, path: str):
        if not path:
            return
        self.player.setSource(QUrl.fromLocalFile(path))
        self.player.play()

    def stop(self):
        self.player.stop()

    def pause(self):
        self.player.pause()

    def resume(self):
        self.player.play()
