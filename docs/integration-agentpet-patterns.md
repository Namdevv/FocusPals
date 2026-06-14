# Tích hợp Pattern từ AgentPet — Pet Window & State Animation

Tài liệu này hướng dẫn cách áp dụng kiến trúc pet window, state system, và asset loading từ **agentpet** (macOS SwiftUI) vào **agent_pet_timer** (Windows Python/PySide6).

---

## 1. Window Architecture (Transparent, Always-on-Top, Draggable)

### AgentPet (Swift)
```swift
// PetWindowController.swift
panel = NSPanel(
    styleMask: [.borderless, .nonactivatingPanel]
)
panel.level = .floating
panel.isOpaque = false
panel.backgroundColor = .clear
panel.isMovableByWindowBackground = true
panel.becomesKeyOnlyIfNeeded = true
```

**Ý tưởng**: Borderless, non-opaque, always-on-top, không steal focus, kéo được.

### Agent Pet Timer (Python + PySide6)

**Implement trong `src/pet_window.py`:**

```python
from PySide6.QtWidgets import QWidget, QVBoxLayout
from PySide6.QtCore import Qt, QPoint
from PySide6.QtGui import QCursor

class PetWindow(QWidget):
    def __init__(self):
        super().__init__()
        
        # Borderless, always-on-top
        self.setWindowFlags(
            Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.Tool  # không activate/steal focus
        )
        
        # Transparent background
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")
        
        # Layout
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(self.layout)
        
        # Dragging
        self.drag_start = None
        
    def mousePressEvent(self, event):
        """Lưu vị trí khi bắt đầu kéo"""
        if event.button() == Qt.LeftButton:
            self.drag_start = event.globalPosition().toPoint() - self.pos()
    
    def mouseMoveEvent(self, event):
        """Di chuyển window"""
        if self.drag_start is not None:
            self.move(event.globalPosition().toPoint() - self.drag_start)
    
    def mouseReleaseEvent(self, event):
        """Kết thúc kéo, lưu vị trí"""
        if event.button() == Qt.LeftButton:
            self.drag_start = None
            # Lưu position vào settings
            self.save_position()
    
    def save_position(self):
        """Lưu vị trí pet vào config"""
        from src.storage import Storage
        Storage.save_pet_position(self.pos())
    
    def restore_position(self):
        """Khôi phục vị trí pet từ lần lần trước"""
        from src.storage import Storage
        pos = Storage.load_pet_position()
        if pos:
            self.move(pos)
        else:
            # Default: bottom-right
            screen = self.screen().availableGeometry()
            self.move(screen.right() - self.width() - 16, screen.top() + 24)
```

---

## 2. State System (Mood Enum)

### AgentPet (Swift)

```swift
// PetMood.swift
public enum PetMood: String, Codable {
    case idle      // không agent nào chạy
    case working   // agent đang chạy
    case waiting   // agent chờ input
    case done      // agent xong
    case celebrate // transient animation
}

// PetController.swift
@Published var mood: PetMood = .idle

func setMood(_ m: PetMood) {
    self.mood = m
}
```

### Agent Pet Timer (Python)

**`src/states.py`:**

```python
from enum import Enum
from typing import Optional

class PetState(Enum):
    """Trạng thái pet đối với timer"""
    IDLE = "idle"           # không timer nào chạy
    FOCUS = "focus"         # đang focus/countdown
    BREAK = "break"         # đang break
    DONE = "done"           # timer hết giờ (trạng thái cuối)
    CELEBRATE = "celebrate" # animation ăn mừng (transient, 3 giây)

    @property
    def is_transient(self) -> bool:
        """Có phải transient (tự hết)?"""
        return self == PetState.CELEBRATE

# Mapping color/icon cho debug
STATE_COLORS = {
    PetState.IDLE: "#808080",
    PetState.FOCUS: "#4CAF50",
    PetState.BREAK: "#2196F3",
    PetState.DONE: "#FF9800",
    PetState.CELEBRATE: "#FFD700",
}
```

**`src/pet_controller.py`:**

```python
from PySide6.QtCore import QObject, Signal
from src.states import PetState
from typing import Optional

class PetController(QObject):
    """Quản lý trạng thái + animation pet"""
    
    mood_changed = Signal(PetState)  # emit khi state thay đổi
    
    def __init__(self):
        super().__init__()
        self._mood = PetState.IDLE
        self._celebrate_timer: Optional[QTimer] = None
    
    @property
    def mood(self) -> PetState:
        return self._mood
    
    def set_mood(self, mood: PetState):
        """Đặt mood, emit signal"""
        if self._mood == mood:
            return
        
        # Cancel celebrate timer nếu có
        if self._celebrate_timer:
            self._celebrate_timer.stop()
            self._celebrate_timer = None
        
        self._mood = mood
        self.mood_changed.emit(mood)
        
        # Nếu vào celebrate, tự hết sau 3 giây
        if mood == PetState.CELEBRATE:
            from PySide6.QtCore import QTimer
            self._celebrate_timer = QTimer()
            self._celebrate_timer.setSingleShot(True)
            self._celebrate_timer.timeout.connect(lambda: self.set_mood(PetState.IDLE))
            self._celebrate_timer.start(3000)  # 3 sec
    
    def update_from_timer_state(self, timer_running: bool, timer_done: bool):
        """Cập nhật mood từ timer state"""
        if timer_done:
            self.set_mood(PetState.DONE)
        elif timer_running:
            # Detect focus vs break dựa vào timer context
            # (có thể từ Timer object, check trạng thái hiện tại)
            if self._mood not in [PetState.FOCUS, PetState.BREAK]:
                self.set_mood(PetState.FOCUS)  # default
        else:
            if self._mood != PetState.IDLE:
                self.set_mood(PetState.IDLE)
```

---

## 3. Pet Animation Binding (Mood → Frame)

### AgentPet (Swift)

```swift
// PetBindings.swift
struct PetBindings {
    var byMood: [String: Int]  // "idle" → 0, "focus" → 1, ...
}

// Mặc định: mood 0→idle, 1→focus, 2→waiting, 3→done, 4→celebrate
static func defaults(clipCount: Int) -> PetBindings {
    let order: [PetMood] = [.idle, .working, .waiting, .done, .celebrate]
    var map: [String: Int] = [:]
    for (i, mood) in order.enumerated() {
        map[mood.rawValue] = min(i, clipCount - 1)
    }
    return PetBindings(byMood: map)
}

func clipIndex(for mood: PetMood) -> Int {
    byMood[mood.rawValue] ?? 0
}
```

**Ý tưởng**: Mỗi pet pack có N clips (png files), mood map tới clip index.

### Agent Pet Timer (Python)

**`src/pet_bindings.py`:**

```python
from src.states import PetState
from typing import Dict, Optional
import json
from pathlib import Path

class PetBindings:
    """Ánh xạ PetState → clip index trong pet pack"""
    
    def __init__(self, by_mood: Optional[Dict[str, int]] = None):
        self.by_mood = by_mood or {
            PetState.IDLE.value: 0,
            PetState.FOCUS.value: 1,
            PetState.BREAK.value: 2,
            PetState.DONE.value: 3,
            PetState.CELEBRATE.value: 4,
        }
    
    def clip_index(self, mood: PetState) -> int:
        """Trả về clip index cho mood"""
        return self.by_mood.get(mood.value, 0)
    
    def set_clip(self, mood: PetState, clip_index: int):
        """Cập nhật binding: mood → clip_index"""
        self.by_mood[mood.value] = clip_index
    
    @staticmethod
    def defaults(clip_count: int) -> "PetBindings":
        """Tạo binding mặc định: spread clips qua states"""
        order = [
            PetState.IDLE,
            PetState.FOCUS,
            PetState.BREAK,
            PetState.DONE,
            PetState.CELEBRATE,
        ]
        by_mood = {}
        for i, state in enumerate(order):
            by_mood[state.value] = min(i, clip_count - 1)
        return PetBindings(by_mood)
    
    def to_dict(self) -> Dict[str, int]:
        """Serialize để lưu"""
        return self.by_mood
    
    @staticmethod
    def from_dict(d: Dict[str, int]) -> "PetBindings":
        """Deserialize từ JSON"""
        return PetBindings(d)
```

**`src/storage.py` — thêm persist bindings:**

```python
import json
from pathlib import Path
from src.pet_bindings import PetBindings

class Storage:
    @staticmethod
    def save_pet_bindings(pet_name: str, bindings: PetBindings):
        """Lưu binding (pet_name → state→clip mapping)"""
        config_dir = Path.home() / "AppData" / "Local" / "AgentPetTimer"
        config_dir.mkdir(parents=True, exist_ok=True)
        
        bindings_file = config_dir / f"bindings_{pet_name}.json"
        with open(bindings_file, "w") as f:
            json.dump(bindings.to_dict(), f)
    
    @staticmethod
    def load_pet_bindings(pet_name: str, default_clip_count: int) -> PetBindings:
        """Load binding, nếu không có dùng default"""
        config_dir = Path.home() / "AppData" / "Local" / "AgentPetTimer"
        bindings_file = config_dir / f"bindings_{pet_name}.json"
        
        if bindings_file.exists():
            with open(bindings_file) as f:
                data = json.load(f)
                return PetBindings.from_dict(data)
        
        return PetBindings.defaults(default_clip_count)
```

---

## 4. Asset Loading (Pet Packs)

### AgentPet (Swift)

```swift
// ImagePetStore.swift — Load từ ~/.agentpet/pets/
// Mỗi folder = 1 pet pack
// Pack format:
// ├─ idle.png / idle_1.png, idle_2.png, ... (spritesheet hoặc frames)
// ├─ focus.png / focus_1.png, ...
// ├─ break.png
// ├─ done.png
// └─ celebrate.png

packs = entries
    .compactMap { SpriteSlicer.loadPack(directory: $0) }
```

### Agent Pet Timer (Python)

**`src/pet_loader.py`:**

```python
from pathlib import Path
from typing import Dict, List, Optional
from PySide6.QtGui import QPixmap
from src.states import PetState
from src.pet_bindings import PetBindings

class PetPack:
    """Một pet pack = folder chứa animation frames cho từng state"""
    
    def __init__(self, directory: Path):
        self.id = directory.name
        self.directory = directory
        self.images: Dict[str, List[QPixmap]] = {}
        
        # Load frames cho từng state
        for state in PetState:
            self.images[state.value] = self._load_frames(state)
        
        # Load bindings
        self.bindings = PetBindings.defaults(self.clip_count)
    
    def _load_frames(self, state: PetState) -> List[QPixmap]:
        """Load frames cho một state: idle.png hoặc idle_1.png, idle_2.png, ..."""
        frames = []
        state_name = state.value
        
        # Pattern 1: single file (idle.png)
        single_file = self.directory / f"{state_name}.png"
        if single_file.exists():
            frames.append(QPixmap(str(single_file)))
            return frames
        
        # Pattern 2: multiple frames (idle_1.png, idle_2.png, ...)
        i = 1
        while True:
            frame_file = self.directory / f"{state_name}_{i}.png"
            if not frame_file.exists():
                break
            frames.append(QPixmap(str(frame_file)))
            i += 1
        
        # Fallback: empty pixmap nếu không tìm thấy
        if not frames:
            frames.append(QPixmap())
        
        return frames
    
    def frames(self, state: PetState, binding_idx: Optional[int] = None) -> List[QPixmap]:
        """Trả về frames cho state (hoặc clip index nếu có binding)"""
        return self.images.get(state.value, [QPixmap()])
    
    @property
    def clip_count(self) -> int:
        """Tổng số clips/states"""
        return len(self.images)


class PetStore:
    """Load và quản lý pet packs từ ~/AppData/.../AgentPetTimer/pets/"""
    
    def __init__(self):
        self.pets_dir = Path.home() / "AppData" / "Local" / "AgentPetTimer" / "pets"
        self.packs: Dict[str, PetPack] = {}
        self.selected_pet_id: Optional[str] = None
        self.reload()
    
    def reload(self):
        """Scan pets_dir, load tất cả pet packs"""
        self.packs = {}
        
        if not self.pets_dir.exists():
            self.pets_dir.mkdir(parents=True, exist_ok=True)
            self._create_default_pet()
            return
        
        for pet_dir in sorted(self.pets_dir.iterdir()):
            if pet_dir.is_dir():
                try:
                    pack = PetPack(pet_dir)
                    self.packs[pack.id] = pack
                except Exception as e:
                    print(f"Failed to load pet {pet_dir.name}: {e}")
    
    def _create_default_pet(self):
        """Tạo default pet fallback (emoji/placeholder)"""
        default_dir = self.pets_dir / "default"
        default_dir.mkdir(exist_ok=True)
        # Có thể copy từ assets/pets/default
    
    def get_pet(self, pet_id: str) -> Optional[PetPack]:
        """Lấy pet pack"""
        return self.packs.get(pet_id)
    
    def select_pet(self, pet_id: str):
        """Chọn pet, lưu vào config"""
        if pet_id in self.packs:
            self.selected_pet_id = pet_id
            self._save_selected()
    
    def _save_selected(self):
        """Lưu pet ID được chọn"""
        from src.storage import Storage
        Storage.save_selected_pet(self.selected_pet_id)
    
    def load_selected(self):
        """Khôi phục pet được chọn từ lần lần trước"""
        from src.storage import Storage
        self.selected_pet_id = Storage.load_selected_pet()
        if self.selected_pet_id and self.selected_pet_id not in self.packs:
            # Fallback tới pet đầu tiên nếu không tìm thấy
            self.selected_pet_id = next(iter(self.packs)) if self.packs else None
```

---

## 5. Animation Rendering (Mood-Driven Frames)

### AgentPet (Swift)

```swift
// ImageSpriteView.swift
struct ImageSpriteView: View {
    let frames: [NSImage]
    let mood: PetMood
    var size: CGFloat = 110
    
    var body: some View {
        TimelineView(.animation(minimumInterval: 1.0 / 12.0)) { context in
            let t = context.date.timeIntervalSinceReferenceDate
            let frameIndex = Int(t * fps) % frames.count
            
            Image(nsImage: frames[frameIndex])
                .resizable()
                .frame(width: size, height: size)
        }
    }
    
    private var fps: Double {
        switch mood {
        case .working: return 8    // chạy nhanh
        case .waiting: return 4    // chạy chậm
        case .celebrate: return 8
        default: return 3          // idle
        }
    }
}
```

### Agent Pet Timer (Python)

**`src/pet_animator.py`:**

```python
from PySide6.QtWidgets import QLabel
from PySide6.QtCore import QTimer, pyqtSignal
from PySide6.QtGui import QPixmap
from src.states import PetState
from src.pet_loader import PetPack, PetStore
from src.pet_bindings import PetBindings
from typing import Optional

class PetAnimator(QLabel):
    """QLabel hiển thị pet animation"""
    
    # FPS map theo mood
    FPS_MAP = {
        PetState.IDLE: 3,
        PetState.FOCUS: 8,        # nhanh khi focus
        PetState.BREAK: 4,        # chậm khi break
        PetState.DONE: 6,
        PetState.CELEBRATE: 8,
    }
    
    def __init__(self, pet_store: PetStore, pet_size: int = 120):
        super().__init__()
        self.pet_store = pet_store
        self.pet_size = pet_size
        self.current_mood = PetState.IDLE
        self.current_pack: Optional[PetPack] = None
        self.current_frames = []
        self.frame_index = 0
        
        # Animation timer
        self.anim_timer = QTimer()
        self.anim_timer.timeout.connect(self._next_frame)
        
        # Style
        self.setScaledContents(False)
        self.setAlignment(Qt.AlignCenter)
        
        # Load selected pet
        self.load_pet()
    
    def load_pet(self):
        """Load pet pack được chọn"""
        if not self.pet_store.selected_pet_id:
            self.show_placeholder()
            return
        
        self.current_pack = self.pet_store.get_pet(self.pet_store.selected_pet_id)
        if not self.current_pack:
            self.show_placeholder()
            return
        
        self.set_mood(self.current_mood)
    
    def show_placeholder(self):
        """Hiển thị placeholder nếu không có pet"""
        # Emoji hoặc icon
        pixmap = QPixmap(self.pet_size, self.pet_size)
        pixmap.fill("transparent")
        self.setPixmap(pixmap)
    
    def set_mood(self, mood: PetState):
        """Thay đổi trạng thái pet"""
        if self.current_mood == mood:
            return
        
        self.current_mood = mood
        self.frame_index = 0
        
        # Load frames cho mood này
        if self.current_pack:
            self.current_frames = self.current_pack.frames(mood)
        else:
            self.current_frames = []
        
        # Set FPS
        fps = self.FPS_MAP.get(mood, 3)
        interval_ms = int(1000 / fps)
        self.anim_timer.stop()
        self.anim_timer.setInterval(interval_ms)
        self.anim_timer.start()
        
        # Draw first frame
        self._draw_frame(0)
    
    def _next_frame(self):
        """Frame timer tick"""
        if not self.current_frames:
            return
        
        self.frame_index = (self.frame_index + 1) % len(self.current_frames)
        self._draw_frame(self.frame_index)
    
    def _draw_frame(self, idx: int):
        """Draw frame tại index"""
        if not self.current_frames or idx >= len(self.current_frames):
            return
        
        pixmap = self.current_frames[idx]
        scaled = pixmap.scaledToWidth(
            self.pet_size,
            Qt.SmoothTransformation
        )
        self.setPixmap(scaled)
    
    def set_pet_size(self, size: int):
        """Resize pet"""
        self.pet_size = size
        self._draw_frame(self.frame_index)
```

---

## 6. Integration Flow (Luồng chính)

```
main.py
  ↓
create PetWindow (transparent, draggable)
create PetStore (load pets từ ~/AppData/.../pets/)
create PetController (quản lý mood)
create PetAnimator (hiển thị animation)
  ↓
connect PetController.mood_changed → PetAnimator.set_mood()
  ↓
Timer starts (focus/break)
  ↓
Timer.update() → PetController.update_from_timer_state()
  ↓
PetController.set_mood(FOCUS) → Signal emit
  ↓
PetAnimator.set_mood(FOCUS)
  → Load frames_focus từ current_pet_pack
  → Start timer với FPS=8 (nhanh)
  → Draw frame loop
  ↓
Timer ends
  ↓
PetController.set_mood(DONE)
  → PetAnimator loads frames_done
  ↓
(2 giây sau)
  ↓
PetController.set_mood(CELEBRATE)
  → Play celebrate animation (3 giây)
  ↓
Auto-revert to IDLE
```

---

## 7. Asset Structure (Pet Pack Format)

```
~/AppData/Local/AgentPetTimer/pets/
├─ default/
│  ├─ idle.png           (hoặc idle_1.png, idle_2.png, ...)
│  ├─ focus.png
│  ├─ break.png
│  ├─ done.png
│  └─ celebrate.png
├─ my_custom_pet/
│  ├─ idle.png
│  ├─ focus.png
│  ├─ break.png
│  ├─ done.png
│  └─ celebrate.png
└─ ...
```

**Mỗi file có thể là:**
- Single PNG: `idle.png` (whole animation in 1 image)
- Frames: `idle_1.png`, `idle_2.png`, `idle_3.png` (sequence)

---

## 8. Connections (Signal/Slot)

```python
# main.py
pet_controller = PetController()
pet_animator = PetAnimator(pet_store)

pet_controller.mood_changed.connect(pet_animator.set_mood)

timer_controller = TimerController()
timer_controller.timer_updated.connect(
    lambda: pet_controller.update_from_timer_state(
        timer_running=timer_controller.is_running,
        timer_done=timer_controller.is_done
    )
)
```

---

## Tóm tắt

| Thành phần | AgentPet | Agent Pet Timer |
|---|---|---|
| Window | NSPanel (borderless, float) | QWidget (frameless, tool) |
| State | PetMood enum | PetState enum |
| Controller | PetController (Observable) | PetController (QObject + Signal) |
| Binding | PetBindings (mood→clip) | PetBindings (mood→clip) |
| Asset Load | ImagePetStore (folder scan) | PetStore (folder scan) |
| Animation | ImageSpriteView (TimelineView) | PetAnimator (QTimer + frames) |
| Render | NSImage frames | QPixmap frames |

Áp dụng từng module: `states.py` → `pet_controller.py` → `pet_loader.py` → `pet_animator.py`.
