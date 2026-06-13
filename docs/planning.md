# Desktop Pet + Focus Timer — Planning

## Context
Mục tiêu: app desktop pet cho Windows. Con pet hiển thị trên màn hình, click vào để set thời gian focus + đếm ngược. Có chọn/phát nhạc trong lúc focus. Phải build ra `.exe` cài về Windows chạy.

---

## 1. Lottie với Python — kết luận

Qt **không render Lottie native**. Lựa chọn:

| Cách | Format tải | Ưu / Nhược |
|---|---|---|
| **QWebEngineView + lottie-web** ⭐ (chất lượng cao) | `.json` | render đẹp, alpha trong suốt tốt, mượt. Nhược: kéo theo Chromium → exe nặng (+~100MB) |
| **QML LottieAnimation** (Qt Lottie) | `.json` | nhẹ hơn. Nhược: experimental, thiếu vài effect |
| **Convert → GIF/sprite + QMovie** (đơn giản/nhẹ) | export `.gif` hoặc PNG sprite sheet | dễ nhất, exe nhẹ. Nhược: GIF mất alpha mượt, file to |

**Tải định dạng**: `.json` (Lottie / Bodymovin). Giữ bản `.json` gốc → đổi cách render lúc nào cũng được. `.lottie` (dotLottie nén) cũng OK.

**QUYẾT ĐỊNH**: dùng **QWebEngineView + lottie-web** ngay từ MVP → animation đẹp + alpha trong suốt mượt. Chấp nhận exe nặng (+~100MB). User tự cung cấp file art (GIF/Lottie `.json`).

Cần thêm lib: `PySide6-Addons` (chứa QtWebEngine). Render: 1 file HTML nhỏ nhúng `lottie-web`, load `.json`, nền `transparent`. QWebEngineView set `setAttribute(Qt.WA_TranslucentBackground)` + `page().setBackgroundColor(Qt.transparent)`.

---

## 2. Tech stack (Python)

| Phần | Lib | Lý do |
|---|---|---|
| GUI / Pet window | **PySide6 (Qt6)** | transparent + frameless + always-on-top native, animation, tray, media — gói chung 1 framework |
| Pet animation | **QWebEngineView + lottie-web** | render Lottie `.json` đẹp + alpha mượt. Cần `PySide6-Addons` |
| Nhạc | **QMediaPlayer + QAudioOutput** (PySide6) | mp3/wav, playlist, volume, loop. **Cả preset bundle + user add file** |
| Storage | **JSON** (settings) + **sqlite3** built-in (history/streak) | đủ dùng, không cần lib ngoài |
| Notification | **QSystemTrayIcon.showMessage** hoặc **plyer** | toast khi hết giờ |
| Tray | **QSystemTrayIcon** (Qt sẵn) | menu, quick-start, quit |
| Auto-start | ghi registry `HKCU\Software\Microsoft\Windows\CurrentVersion\Run` | chạy cùng Windows (tùy chọn) |
| Build exe | **PyInstaller** `--onefile --windowed` | ra 1 file `.exe` |

---

## 3. Features

### MVP (v1)
- Pet window: frameless, nền trong suốt, always-on-top, drag di chuyển.
- Pet animation theo state: `idle` / `focus` / `break` / `done`.
- Click pet → popup set thời gian focus (preset 25/50 + custom).
- Đếm ngược + hiển thị thời gian còn lại.
- **Nhạc**: preset bundle sẵn + cho user add file mp3/wav riêng; **play khi focus**, stop/pause khi hết giờ.
- **Volume slider**.
- Toast + âm báo khi hết giờ.
- Build `.exe`.

### v2
- System tray (quick-start, settings, quit).
- Settings: opacity, kích thước pet, vị trí, volume mặc định.
- Lịch sử focus + streak (chuỗi ngày) lưu SQLite.
- Pomodoro auto-break (focus → break → focus).
- Nhớ nhạc + cài đặt lần trước.

### v3
- Preset nhạc bundle sẵn (Lofi, Rain, White noise, Forest).
- Gamify: pet "đói" nếu skip focus; mở khóa skin theo tổng giờ focus.
- Biểu đồ thống kê tuần/tháng.
- Break mode nhạc khác / tắt nhạc.

### v4
- Chặn app/web blacklist khi focus (đọc process list, kill).
- Auto-start cùng Windows.

---

## 4. Kiến trúc thư mục

```
agent_pet_timer/
├─ main.py                # entry, khởi tạo app + windows
├─ src/
│  ├─ pet_window.py       # QWidget frameless, transparent, on-top, drag; chứa QWebEngineView render Lottie
│  ├─ pet_view.html       # HTML nhúng lottie-web, nền transparent, đổi animation theo state qua JS bridge
│  ├─ timer_popup.py      # set time, start/stop, chọn nhạc, volume slider
│  ├─ timer.py            # QTimer đếm ngược, signal hết giờ / tick
│  ├─ music_player.py     # QMediaPlayer: play/pause/loop/volume/playlist
│  ├─ tray.py             # QSystemTrayIcon menu (v2)
│  ├─ storage.py          # JSON settings + sqlite3 history/streak
│  ├─ notify.py           # toast + âm báo
│  └─ states.py           # enum PetState (idle/focus/break/done)
├─ assets/
│  ├─ pet/                # idle.json, focus.json, break.json, done.json (Lottie - user cung cấp)
│  ├─ lottie/             # lottie-web.min.js (bundle offline)
│  ├─ music/              # preset bundle: lofi.mp3, rain.mp3, whitenoise.mp3 ...
│  └─ icon.ico
├─ docs/
│  └─ planning.md         # bản planning này
├─ requirements.txt       # PySide6, PySide6-Addons, pyinstaller, plyer
└─ build.ps1              # script PyInstaller build exe
```

### Luồng chính
```
main → tạo PetWindow (idle)
click pet → mở TimerPopup → set time + chọn nhạc + start
start → Timer chạy, PetWindow.set_state(focus), MusicPlayer.play()
tick → cập nhật hiển thị
hết giờ → PetWindow.set_state(done), MusicPlayer.stop(), notify(), lưu history
(v2) → tự chuyển break → focus
```

---

## 5. Build exe (Windows)

```powershell
pip install -r requirements.txt
pyinstaller --onefile --windowed --icon=assets/icon.ico `
  --add-data "assets;assets" `
  --name AgentPetTimer main.py
```
- `--windowed`: ẩn console.
- `--add-data "assets;assets"`: nhớ Windows dùng `;`. Trong code load asset qua đường dẫn tương thích PyInstaller (`sys._MEIPASS`).
- Output: `dist/AgentPetTimer.exe`.
- (Tùy chọn) installer: dùng **Inno Setup** đóng gói `.exe` → setup wizard.

Lưu ý code asset path:
```python
import sys, os
def resource_path(rel):
    base = getattr(sys, "_MEIPASS", os.path.abspath("."))
    return os.path.join(base, rel)
```

---

## 6. Quyết định đã chốt
1. **Pet art**: user tự cung cấp file Lottie `.json` (hoặc GIF).
2. **Nhạc**: cả hai — preset bundle sẵn + cho user add file riêng.
3. **Render pet**: QWebEngineView + lottie-web ngay từ MVP (đẹp, alpha mượt, exe nặng +100MB).

---

## 7. Verification (sau khi code)
- Chạy `python main.py`: pet hiện trong suốt, on-top, drag được.
- Click pet → set 1 phút → đếm ngược chạy, nhạc phát.
- Hết giờ → pet `done`, nhạc dừng, có toast.
- Build `pyinstaller ...` → chạy `dist/AgentPetTimer.exe` trên máy Windows sạch (không cài Python) → app chạy đủ chức năng.
