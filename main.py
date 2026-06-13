"""Agent Pet Timer - entry point."""
import os
import sys

# src lên path để import package
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6.QtCore import QCoreApplication, Qt
# QtWebEngine cần share OpenGL contexts -> set TRƯỚC khi tạo QApplication
QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_ShareOpenGLContexts)

from PySide6.QtWidgets import QApplication

from src.pet_window import PetWindow
from src.tray import make_tray


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Agent Pet Timer")
    app.setQuitOnLastWindowClosed(False)  # đóng popup không thoát app

    window = PetWindow()
    window.tray = make_tray(app, window)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
