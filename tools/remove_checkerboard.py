"""Xoá nền caro (checkerboard) bị vẽ chết thành pixel đặc -> trả lại alpha trong suốt.

Nhiều sheet xuất ra kèm caro "giả trong suốt" (2 tông trắng + xám nhạt) vẽ thẳng
vào PNG nên alpha=255 -> slicer alpha-gutter không cắt được. Tool này set những
pixel khớp tông nền về alpha 0.

Cách dùng:
    python tools/remove_checkerboard.py assets/pet/cat/spritesheet.png
    python tools/remove_checkerboard.py <in.png> -o <out.png>   # không ghi đè
    python tools/remove_checkerboard.py <in.png> --tol 30        # nới dung sai

Mặc định: backup <file>.bak.png rồi ghi đè file gốc.
"""
import argparse
import os
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

from PIL import Image

# 2 tông caro hay gặp (trắng + xám-xanh nhạt). Thêm tông khác nếu cần.
BG_COLORS = [
    (255, 255, 255),
    (207, 212, 218),
]


def _is_bg(r, g, b, tol):
    for cr, cg, cb in BG_COLORS:
        if abs(r - cr) <= tol and abs(g - cg) <= tol and abs(b - cb) <= tol:
            return True
    return False


def remove(in_path, out_path, tol, light=0):
    im = Image.open(in_path).convert("RGBA")
    w, h = im.size
    px = im.load()
    cleared = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if not a:
                continue
            # light mode: mọi pixel sáng (kể cả tông biên caro) -> nền
            bg = (min(r, g, b) >= light) if light else _is_bg(r, g, b, tol)
            if bg:
                px[x, y] = (r, g, b, 0)
                cleared += 1
    im.save(out_path)
    total = w * h
    print(f"{in_path} -> {out_path}")
    print(f"  xoá {cleared}/{total} pixel ({cleared * 100 // total}%) về trong suốt")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input")
    ap.add_argument("-o", "--output", help="file ra (mặc định ghi đè input)")
    ap.add_argument("--tol", type=int, default=22, help="dung sai màu nền (mặc định 22)")
    ap.add_argument("--light", type=int, default=0, metavar="N",
                    help="xoá MỌI pixel sáng có min(r,g,b)>=N (vd 185). Bỏ caro nhiều tông tốt hơn --tol.")
    ap.add_argument("--no-backup", action="store_true")
    a = ap.parse_args()

    if not os.path.isfile(a.input):
        print(f"không thấy file: {a.input}")
        sys.exit(1)

    out = a.output or a.input
    if out == a.input and not a.no_backup:
        # .bak (KHÔNG .png) để không bị app/validator nhận nhầm là sheet
        bak = a.input + ".bak"
        if not os.path.exists(bak):
            Image.open(a.input).save(bak, "PNG")
            print(f"backup -> {bak}")

    remove(a.input, out, a.tol, a.light)


if __name__ == "__main__":
    main()
