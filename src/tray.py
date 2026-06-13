"""System tray: toggle timer, dừng focus, thoát."""
import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QMenu, QStyle, QSystemTrayIcon

from .paths import asset


def make_tray(app, window):
    icon_path = asset("icon.ico")
    if os.path.isfile(icon_path):
        icon = QIcon(icon_path)
    else:
        icon = app.style().standardIcon(QStyle.StandardPixmap.SP_ComputerIcon)

    tray = QSystemTrayIcon(icon, app)
    tray.setToolTip("Agent Pet Timer")

    menu = QMenu()
    menu.addAction("Mở / đóng Timer", window.toggle_popup)
    menu.addAction("Dừng focus", window.stop_focus)
    menu.addSeparator()
    menu.addAction("Thoát", app.quit)
    tray.setContextMenu(menu)

    # click trái vào tray cũng mở popup
    def _activated(reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            window.toggle_popup()

    tray.activated.connect(_activated)
    tray.show()
    return tray
