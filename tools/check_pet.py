"""Kiểm tra 1 pet/skin có đúng định dạng app đọc được không.

Dùng đúng slice_spritesheet của app -> kết quả khớp 100% với lúc chạy thật.

Cách dùng:
    python tools/check_pet.py                 # check skin mặc định (assets/pet/)
    python tools/check_pet.py cat             # check assets/pet/cat/
    python tools/check_pet.py assets/pet/cat  # check theo path

Exit code 0 = OK, 1 = có lỗi.
"""
import os
import sys

# console Windows hay là cp1252 -> ép utf-8 cho emoji/tiếng Việt
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

# cho phép import src.* khi chạy thẳng file này
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

# slice_spritesheet dùng QPixmap -> cần QGuiApplication. Chạy headless offscreen.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtGui import QGuiApplication, QImage  # noqa: E402

_app = QGuiApplication.instance() or QGuiApplication(sys.argv[:1])

from src.core.states import PetState  # noqa: E402
from src.ui.pet_animator import (  # noqa: E402
    CLIP_ORDER,
    SHEET_EXTS,
    slice_spritesheet,
)

OK = "✅"
BAD = "❌"
WARN = "⚠️ "


def _resolve_dir(arg: str) -> str:
    """arg -> folder skin thật."""
    if not arg:
        return os.path.join(_ROOT, "assets", "pet")
    if os.path.isdir(arg):
        return os.path.abspath(arg)
    return os.path.join(_ROOT, "assets", "pet", arg)


def _find_sheet(d: str) -> str:
    """Tìm sheet giống _find_spritesheet của app (pet.json optional)."""
    import json
    manifest = os.path.join(d, "pet.json")
    if os.path.isfile(manifest):
        try:
            with open(manifest, "r", encoding="utf-8") as f:
                p = json.load(f).get("spritesheetPath", "")
            if p and os.path.isfile(os.path.join(d, p)):
                return os.path.join(d, p)
        except Exception:
            pass
    for name in sorted(os.listdir(d)):
        low = name.lower()
        if low.startswith("spritesheet") and low.endswith(SHEET_EXTS):
            return os.path.join(d, name)
    return ""


def _has_png_states(d: str):
    """PNG rời mode: trả list (state, frame_count)."""
    out = []
    for st in PetState:
        name = st.value
        if os.path.isfile(os.path.join(d, f"{name}.png")):
            out.append((name, 1))
            continue
        n = 0
        i = 1
        while os.path.isfile(os.path.join(d, f"{name}_{i}.png")):
            n += 1
            i += 1
        if n:
            out.append((name, n))
    return out


def check(arg: str) -> bool:
    d = _resolve_dir(arg)
    print(f"Pet folder: {d}")
    if not os.path.isdir(d):
        print(f"{BAD} folder không tồn tại")
        return False

    errors = 0
    warns = 0

    sheet = _find_sheet(d)
    pngs = _has_png_states(d)

    # ---- mode spritesheet ----
    if sheet:
        print(f"{OK} tìm thấy sheet: {os.path.basename(sheet)}")
        img = QImage(sheet)
        if img.isNull():
            print(f"{BAD} không đọc được ảnh (sai format / thiếu Qt imageformats plugin cho webp)")
            return False

        rgba = img.convertToFormat(QImage.Format.Format_RGBA8888)
        w, h = rgba.width(), rgba.height()
        print(f"   size: {w}x{h}, mode hasAlpha={img.hasAlphaChannel()}")

        # check nền trong suốt
        bpl = rgba.bytesPerLine()
        buf = bytes(rgba.constBits())
        alphas = buf[3::4]
        amin = min(alphas)
        amax = max(alphas)
        if amin == 255:
            print(f"{BAD} nền KHÔNG trong suốt (alpha toàn 255). Slicer alpha-gutter sẽ coi cả ảnh = 1 frame.")
            print("    -> tách nền (remove.bg / Photopea) ra RGBA trước khi bỏ vào.")
            errors += 1
        else:
            print(f"{OK} có vùng trong suốt (alpha {amin}..{amax})")

        clips = slice_spritesheet(img)
        n = len(clips)
        if n == 0:
            print(f"{BAD} cắt được 0 clip -> pet sẽ ra emoji fallback")
            errors += 1
        else:
            print(f"   cắt được {n} clip (row). Cần ≥4 cho đủ 4 state.")
            for i, clip in enumerate(clips):
                st = CLIP_ORDER[i].value if i < len(CLIP_ORDER) else f"(thừa, bỏ qua)"
                tag = OK if len(clip) >= 1 else BAD
                anim = "animation" if len(clip) > 1 else "tĩnh (1 frame)"
                print(f"     row {i} -> {st:6} : {len(clip)} frame ({anim}) {tag}")
            if n == 1:
                print(f"{BAD} chỉ 1 clip -> 4 state map về cùng 1 animation (thường do nền đặc / không phải lưới 4 hàng).")
                errors += 1
            elif n < 4:
                print(f"{WARN} {n} clip < 4 -> state thiếu sẽ clamp dùng clip cuối.")
                warns += 1
            else:
                print(f"{OK} đủ ≥4 clip cho 4 state.")

    # ---- mode PNG rời ----
    elif pngs:
        print(f"{OK} mode PNG rời:")
        have = {name for name, _ in pngs}
        for name, cnt in pngs:
            anim = "animation" if cnt > 1 else "tĩnh"
            print(f"     {name:6}: {cnt} frame ({anim})")
        for st in PetState:
            if st.value not in have:
                print(f"{WARN} thiếu state '{st.value}' -> sẽ ra emoji fallback.")
                warns += 1

    else:
        print(f"{BAD} không thấy spritesheet.* lẫn PNG state nào -> pet ra emoji fallback.")
        errors += 1

    print()
    if errors:
        print(f"{BAD} {errors} lỗi, {warns} cảnh báo — pet CHƯA chạy đúng.")
        return False
    if warns:
        print(f"{WARN} OK nhưng có {warns} cảnh báo.")
        return True
    print(f"{OK} định dạng hợp lệ.")
    return True


def main():
    args = sys.argv[1:] or [""]
    ok = True
    for a in args:
        if len(args) > 1 or args[0]:
            print("=" * 50)
        ok = check(a) and ok
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
