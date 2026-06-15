"""Tạo / kiểm tra pet skin từ file user upload (dùng QImage, không cần Pillow).

- strip_checkerboard: xoá nền caro/đặc về alpha 0 (để slicer alpha-gutter cắt được).
- inspect_sheet: chạy đúng slice_spritesheet của app -> kết quả khớp 100% runtime.
- save_sheet_skin / save_png_skin: lưu vào user pets dir (%APPDATA%/pets/<tên>/).
"""
import os
import shutil

from PySide6.QtGui import QImage

from ..core import skins
from ..core.states import PetState
from .pet_animator import CLIP_ORDER, slice_spritesheet

# tông nền caro hay gặp (trắng + xám nhạt) — khớp tools/remove_checkerboard.py
_BG = [(255, 255, 255), (207, 212, 218)]


def _is_bg(r, g, b, tol):
    return any(
        abs(r - cr) <= tol and abs(g - cg) <= tol and abs(b - cb) <= tol
        for cr, cg, cb in _BG
    )


def alpha_range(img: QImage):
    rgba = img.convertToFormat(QImage.Format.Format_RGBA8888)
    a = bytes(rgba.constBits())[3::4]
    return (min(a), max(a)) if a else (0, 0)


def strip_checkerboard(img: QImage, tol: int = 22):
    """Set pixel trùng tông nền caro về alpha 0. Trả (QImage mới, số px đã xoá)."""
    img = img.convertToFormat(QImage.Format.Format_RGBA8888)
    w, h = img.width(), img.height()
    bpl = img.bytesPerLine()
    buf = bytearray(img.constBits())
    cleared = 0
    for y in range(h):
        base = y * bpl
        for x in range(w):
            i = base + x * 4
            if buf[i + 3] == 0:
                continue
            if _is_bg(buf[i], buf[i + 1], buf[i + 2], tol):
                buf[i + 3] = 0
                cleared += 1
    out = QImage(bytes(buf), w, h, bpl, QImage.Format.Format_RGBA8888)
    return out.copy(), cleared


def inspect_sheet(img: QImage) -> dict:
    """Kiểm tra 1 spritesheet. Trả dict: ok, errors, warnings, lines, clips."""
    res = {"ok": False, "errors": [], "warnings": [], "lines": [], "clips": []}
    if img.isNull():
        res["errors"].append("Không đọc được ảnh (sai format / thiếu plugin webp).")
        return res
    res["lines"].append(f"Kích thước: {img.width()}×{img.height()}")
    amin, amax = alpha_range(img)
    if amin == 255:
        res["errors"].append(
            "Nền KHÔNG trong suốt (alpha toàn 255) → bật 'Tự xoá nền caro'."
        )
    else:
        res["lines"].append(f"Alpha {amin}..{amax} — có vùng trong suốt ✓")

    clips = slice_spritesheet(img)
    res["clips"] = clips
    n = len(clips)
    if n == 0:
        res["errors"].append("Cắt được 0 clip → pet sẽ ra emoji fallback.")
    else:
        for i, clip in enumerate(clips):
            st = CLIP_ORDER[i].value if i < len(CLIP_ORDER) else "(thừa, bỏ qua)"
            res["lines"].append(f"row {i} → {st}: {len(clip)} frame")
        if n == 1:
            res["errors"].append("Chỉ 1 clip → 4 state trùng 1 animation.")
        elif n < 4:
            res["warnings"].append(f"{n} clip < 4 → state thiếu clamp dùng clip cuối.")
    res["ok"] = not res["errors"]
    return res


def save_sheet_skin(name: str, img: QImage) -> str:
    """Lưu spritesheet (đã xử lý) thành 1 skin user. Trả path folder."""
    d = os.path.join(skins.user_dir(), name)
    os.makedirs(d, exist_ok=True)
    img.save(os.path.join(d, "spritesheet.png"), "PNG")
    with open(os.path.join(d, "pet.json"), "w", encoding="utf-8") as f:
        f.write('{"spritesheetPath": "spritesheet.png"}\n')
    return d


_STATE_TOKENS = [s.value for s in PetState]  # idle / focus / break / done


def match_state(path: str) -> str:
    """Tên file chứa token state nào -> trả state đó ("" nếu không khớp)."""
    base = os.path.basename(path).lower()
    for st in _STATE_TOKENS:
        if st in base:
            return st
    return ""


def save_png_skin(name: str, files: list):
    """Copy PNG rời theo tên state (idle/focus/break/done). Trả (path, [state lưu])."""
    d = os.path.join(skins.user_dir(), name)
    os.makedirs(d, exist_ok=True)
    saved = []
    for f in files:
        st = match_state(f)
        if st:
            shutil.copyfile(f, os.path.join(d, f"{st}.png"))
            saved.append(st)
    return d, saved
