"""Bật/tắt chạy cùng Windows qua registry HKCU\\...\\Run."""
import sys

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_NAME = "AgentPetTimer"


def _command() -> str:
    if getattr(sys, "frozen", False):
        # chạy từ exe (PyInstaller)
        return f'"{sys.executable}"'
    # dev: python main.py
    import os
    main_py = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "main.py")
    )
    return f'"{sys.executable}" "{main_py}"'


def set_autostart(enabled: bool) -> bool:
    try:
        import winreg
    except ImportError:
        return False
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
        )
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_enabled() -> bool:
    try:
        import winreg
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_READ)
        try:
            winreg.QueryValueEx(key, APP_NAME)
            return True
        except FileNotFoundError:
            return False
        finally:
            winreg.CloseKey(key)
    except Exception:
        return False
