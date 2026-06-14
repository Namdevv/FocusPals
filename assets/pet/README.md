# Pet animation (PNG sprite)

Bỏ PNG vào đây (đặt thẳng trong `assets/pet/` = skin mặc định, hoặc tạo
sub-folder `assets/pet/<tên_skin>/` cho skin riêng — sẽ tự hiện trong Cài đặt).

Mỗi state là **1 trong 2 dạng**:

- Ảnh tĩnh: `idle.png`
- Animation (đổi frame theo fps): `idle_1.png`, `idle_2.png`, `idle_3.png`, ...

4 state cần có:

- `idle`  — pet đứng yên (mặc định)
- `focus` — lúc đang focus (chạy fps cao)
- `break` — lúc nghỉ
- `done`  — lúc hoàn thành

PNG nền trong suốt (RGBA). Nên xuất ~@2x kích thước pet (400px) cho nét khi scale.

Chưa có PNG cho state nào → app vẫn chạy, hiện emoji thay thế.

---

## Hoặc: spritesheet (format petdex)

Thả nguyên folder pet tải từ petdex vào đây, ví dụ `assets/pet/11/`:

```
11/
├─ pet.json          (OPTIONAL — petdex kèm sẵn, chỉ đường tới sheet)
└─ spritesheet.webp  (hoặc .png)
```

`pet.json` không bắt buộc: chỉ cần đặt tên file sheet là `spritesheet.webp`
(hoặc `.png`) là app tự nhận. Có json thì nó đọc `spritesheetPath`.

Sheet được cắt tự động bằng alpha-gutter (không cần khai báo grid):
**mỗi hàng = 1 clip (animation), mỗi cột trong hàng = 1 frame.**

Map state → clip theo thứ tự hàng: `idle=0, focus=1, break=2, done=3`
(clamp nếu ít clip hơn). webp cần Qt imageformats plugin (có sẵn trong PySide6).

---

## Tạo pet mới bằng AI (4 state đủ dùng)

Timer chỉ cần 4 state, đúng thứ tự hàng từ trên xuống:

| Hàng | State | Khi nào | Animation gợi ý |
|---|---|---|---|
| 0 | `idle`  | không chạy timer | đứng yên, chớp mắt, thở nhẹ |
| 1 | `focus` | đang focus       | tập trung, gõ phím, cắm cúi |
| 2 | `break` | nghỉ giữa giờ    | duỗi người, uống nước, thư giãn |
| 3 | `done`  | xong phiên       | ăn mừng 🎉, nhảy, giơ tay |

Slicer cắt theo **alpha gutter** → AI **bắt buộc** chừa khoảng trong suốt giữa
mỗi frame và mỗi hàng, nền trong suốt hoàn toàn. Đổi `[MÔ TẢ PET]` rồi đưa vào
model ảnh (Nano Banana, GPT-Image, Midjourney, SDXL...):

```
A 2D pixel-art character spritesheet of [MÔ TẢ PET — e.g. a chubby orange cat],
arranged as a strict 4-row grid on a FULLY TRANSPARENT background (RGBA, no
backdrop, no shadow plane, no color fill).

Layout rules (critical):
- Exactly 4 rows, top to bottom, each row = one animation:
  Row 1 = IDLE: standing still, breathing, occasional blink.
  Row 2 = FOCUS: concentrating / working hard (e.g. typing, head down).
  Row 3 = BREAK: relaxing / stretching / sipping a drink.
  Row 4 = DONE: celebrating, arms up, happy jump, confetti optional.
- 6 frames per row, left to right, as a smooth looping animation.
- Leave clear EMPTY TRANSPARENT GAPS between every frame (columns) and
  between every row — visible gutters, frames never touch or overlap.
- Same character, same art style, same canvas size and same vertical
  baseline in every frame (character centered, feet aligned).
- Clean alpha edges, no anti-alias halo, no background grid lines, no labels.

Style: cute, simple, bold outlines, flat colors, game asset.
Output: single PNG, transparent background.
```

**Lưu ý:**
- Frame dính nhau / có nền → slicer cắt sai. Thêm: *"each frame inside its own
  clearly separated transparent cell, generous spacing"*.
- Ra nền trắng thay vì trong suốt → tách nền (remove.bg / Photopea) trước khi bỏ vào.
- Giữ frame **đều chiều cao** (feet aligned) để render không giật.
- Ra nhiều hơn 4 hàng cũng được — app chỉ dùng 4 hàng đầu.
