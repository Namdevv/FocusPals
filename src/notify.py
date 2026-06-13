"""Toast + âm báo."""
from PySide6.QtWidgets import QApplication


def notify(title: str, msg: str, tray=None):
    shown = False
    if tray is not None:
        try:
            tray.showMessage(title, msg)
            shown = True
        except Exception:
            shown = False
    if not shown:
        try:
            from plyer import notification
            notification.notify(title=title, message=msg, timeout=5)
        except Exception:
            pass
    try:
        QApplication.beep()
    except Exception:
        pass
