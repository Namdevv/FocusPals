"""Đường dẫn asset tương thích cả dev lẫn PyInstaller bundle."""
import os
import sys


def resource_path(rel: str) -> str:
    """Trả về path tuyệt đối tới resource.

    - Khi chạy từ exe (PyInstaller): base = sys._MEIPASS.
    - Khi dev: base = thư mục gốc project (file ở src/core/ -> lùi 2 cấp).
    """
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    return os.path.join(base, rel)


def asset(*parts: str) -> str:
    return resource_path(os.path.join("assets", *parts))
