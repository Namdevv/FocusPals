"""Settings (JSON) + lịch sử focus (SQLite). Lưu trong %APPDATA% (writable)."""
import datetime
import json
import os
import sqlite3

APP_DIR = os.path.join(
    os.environ.get("APPDATA", os.path.expanduser("~")), "AgentPetTimer"
)
os.makedirs(APP_DIR, exist_ok=True)

SETTINGS_FILE = os.path.join(APP_DIR, "settings.json")
DB_FILE = os.path.join(APP_DIR, "history.db")

DEFAULTS = {
    "volume": 60,
    "last_music": "",
    "pet_pos": None,
    "last_minutes": 25,
}


def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        data = {}
    return {**DEFAULTS, **data}


def save_settings(data: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS focus_history ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, "
        "date TEXT NOT NULL, minutes INTEGER NOT NULL)"
    )
    return conn


def add_history(minutes: int):
    if minutes <= 0:
        return
    try:
        conn = _db()
        conn.execute(
            "INSERT INTO focus_history(date, minutes) VALUES(?, ?)",
            (datetime.date.today().isoformat(), int(minutes)),
        )
        conn.commit()
        conn.close()
    except Exception:
        pass
