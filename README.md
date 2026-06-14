# Agent Pet Timer

Desktop pet cho Windows. Click pet → set thời gian focus → đếm ngược, phát nhạc, báo khi xong.

## Chạy (dev)

```powershell
pip install -r requirements.txt
python main.py
```

## Dùng

- **Click** pet → mở/đóng popup timer.
- **Kéo** pet → di chuyển (nhớ vị trí).
- Popup: chọn phút (preset 25/50 hoặc tùy chỉnh), chọn nhạc, chỉnh âm lượng, **Bắt đầu**.
- Hết giờ: pet ăn mừng 🎉, nhạc dừng, có toast + tiếng báo.
- **Tray icon**: mở timer / dừng / thoát.

## Art & nhạc (tùy chọn)

- Pet art: bỏ vào `assets/pet/<tên_skin>/` — hỗ trợ PNG rời (`idle/focus/break/done.png`) hoặc spritesheet (1 ảnh `spritesheet.webp`, kiểu petdex/agentpet). Xem [assets/pet/README.md](assets/pet/README.md). Thiếu thì hiện emoji.
- Nhạc preset: bỏ file vào `assets/music/`.

## Build exe

```powershell
powershell -ExecutionPolicy Bypass -File build.ps1
```

Ra `dist/AgentPetTimer.exe`.

## Cấu trúc

Xem [docs/planning.md](docs/planning.md).

Settings + lịch sử focus lưu tại `%APPDATA%\AgentPetTimer\`.
