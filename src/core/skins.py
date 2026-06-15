"""Pet skins: gộp skin bundled (assets/pet/) + skin user tự tạo (%APPDATA%/pets/).

Skin user ưu tiên vì ghi được cả khi chạy exe (assets/ trong bundle là read-only).
"""
import os

from .paths import asset
from .storage import APP_DIR

USER_PETS_DIR = os.path.join(APP_DIR, "pets")


def bundled_dir() -> str:
    return asset("pet")


def user_dir() -> str:
    os.makedirs(USER_PETS_DIR, exist_ok=True)
    return USER_PETS_DIR


def skin_dir(name: str) -> str:
    """Folder của 1 skin theo tên. "" = mặc định (file ở assets/pet/ gốc).

    User dir ưu tiên (ghi được), không có thì fallback bundled.
    """
    if not name:
        return bundled_dir()
    u = os.path.join(USER_PETS_DIR, name)
    if os.path.isdir(u):
        return u
    return os.path.join(bundled_dir(), name)


def list_skins() -> list:
    """Tên các skin (folder con) ở cả bundled lẫn user, không trùng, đã sort."""
    names = []
    seen = set()
    for d in (bundled_dir(), USER_PETS_DIR):
        if not os.path.isdir(d):
            continue
        for n in sorted(os.listdir(d)):
            if n not in seen and os.path.isdir(os.path.join(d, n)):
                seen.add(n)
                names.append(n)
    return names
