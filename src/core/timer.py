"""Countdown timer dựa trên QTimer."""
from PySide6.QtCore import QObject, QTimer, Signal


class CountdownTimer(QObject):
    tick = Signal(int)      # giây còn lại
    finished = Signal()

    def __init__(self):
        super().__init__()
        self._t = QTimer()
        self._t.setInterval(1000)
        self._t.timeout.connect(self._on_tick)
        self.remaining = 0

    def start(self, seconds: int):
        self.remaining = max(0, int(seconds))
        self.tick.emit(self.remaining)
        self._t.start()

    def stop(self):
        self._t.stop()
        self.remaining = 0

    def is_running(self) -> bool:
        return self._t.isActive()

    def _on_tick(self):
        self.remaining -= 1
        if self.remaining <= 0:
            self.remaining = 0
            self._t.stop()
            self.tick.emit(0)
            self.finished.emit()
        else:
            self.tick.emit(self.remaining)
