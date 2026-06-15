# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

FocusPals — a Windows desktop pet + Pomodoro focus timer built on **PySide6 (Qt)**. A frameless, transparent, always-on-top pet floats on the desktop; clicking it opens a timer popup, starting focus runs a countdown that drives pet animation, focus music, a countdown bubble, and end-of-session notifications. Rendering is **PNG sprite / spritesheet via plain Qt** — deliberately *no* Chromium / QtWebEngine (excluded from builds to stay light).

UI strings and code comments are in **Vietnamese**; keep new comments/strings Vietnamese to match.

## Commands

```powershell
pip install -r requirements.txt      # PySide6, plyer, pyinstaller
python main.py                       # run (dev)

python tools/check_pet.py            # validate the default skin (assets/pet/)
python tools/check_pet.py cat        # validate assets/pet/cat/
python tools/check_pet.py path\to\skin

powershell -ExecutionPolicy Bypass -File build.ps1   # -> dist\AgentPetTimer.exe
```

Requires Python 3.10+, Windows. There is **no test suite, linter, or CI** — `tools/check_pet.py` is the only verification harness, and it validates pet asset format (exit 0 = OK, 1 = error) using the app's real slicing code so results match runtime exactly.

## Architecture

Three layers under `src/` (import direction is strictly ui → services → core; core has no UI deps):

- **`core/`** — pure logic. `states.py` (`PetState`: idle/focus/break/done), `timer.py` (`CountdownTimer`, a QObject emitting `tick(int)` / `finished()` off a 1s `QTimer`), `storage.py` (settings + history), `paths.py` (asset resolution).
- **`services/`** — system integration: `music_player.py` (QtMultimedia loop), `notify.py` (plyer toast), `autostart.py` (Windows registry run key).
- **`ui/`** — Qt widgets. `pet_window.py` is the orchestrator; the rest are leaf widgets it owns.

### `PetWindow` is the hub

`src/ui/pet_window.py` owns and wires everything: the animator, `CountdownTimer`, `MusicPlayer`, `TimerPopup`, `FocusBubble`, `SettingsDialog`, and tray. All cross-component flow goes through it — there is no separate controller/state-machine class. The focus lifecycle lives here as `_phase` (`"idle"|"focus"|"break"`) plus method chaining:

`start_focus` → timer + music + `PetState.FOCUS` + bubble → `_on_tick` updates popup & bubble → `_on_finished` (focus) records history, notifies, shows done → `_maybe_break`/`_start_break` (auto break if `last_break > 0`) → `_on_break_finished`.

The `_maybe_break`/`_after_done` guards check `timer.is_running()` to avoid clobbering a session the user manually started during the post-done delay (`QTimer.singleShot`). Preserve those guards when touching focus flow.

Mouse handling distinguishes **click vs drag** via `DRAG_THRESHOLD` (manhattan distance): release without movement = toggle popup; with movement = save position. The `PetAnimator` QLabel sets `WA_TransparentForMouseEvents` so events fall through to `PetWindow` for drag/click to work.

### Pet rendering — `pet_animator.py`

`PetAnimator` (a QLabel + QTimer) supports two skin formats found in `assets/pet/<skin>/` (or `assets/pet/` for the default), with **emoji fallback** if nothing loads:

1. **Loose PNG** — `idle.png` (single) or `idle_1.png, idle_2.png, …` (sequence) per state.
2. **Spritesheet (petdex format)** — optional `pet.json` pointing at `spritesheet.(webp|png|gif)`, else auto-found by filename prefix. Sliced by **alpha-gutter detection** in `slice_spritesheet()`: each fully-transparent-bounded **row = one clip (animation)**, each column within = one frame. No grid metadata needed. State→clip by row order: `CLIP_ORDER = [IDLE, FOCUS, BREAK, DONE]`, clamped to the last available clip.

`slice_spritesheet()` is the format contract — `tools/check_pet.py` imports it directly so any change to slicing must keep both in sync (or the checker lies). WebP slicing requires Qt's imageformats plugin.

### Persistence — `storage.py`

App data lives in `%APPDATA%\AgentPetTimer\` (created on import): `settings.json` (merged over `DEFAULTS`) and `history.db` (SQLite `focus_history`). All reads/writes swallow exceptions and fall back to defaults — settings are best-effort, never fatal. `DEFAULTS` is the source of truth for every setting key; add new settings there.

### Asset paths — `paths.py`

`asset(*parts)` / `resource_path()` resolve under `sys._MEIPASS` when frozen by PyInstaller, else the project root. Always use these for bundled assets so dev and `.exe` both work — `build.ps1` bundles via `--add-data "assets;assets"`.

## Conventions

- New UI widgets: instantiate and wire them in `PetWindow.__init__`; expose `apply_*` methods on `PetWindow` for live settings changes (see `apply_size`/`apply_opacity`/`apply_skin`/`apply_bubble`).
- Settings flow: `SettingsDialog` mutates `PetWindow.settings` and calls `storage.save_settings`; persist new keys by adding them to `DEFAULTS`.
- Keep core/ free of Qt-widget and service imports.
