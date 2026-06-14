"""Pet states."""
from enum import Enum


class PetState(str, Enum):
    IDLE = "idle"
    FOCUS = "focus"
    BREAK = "break"
    DONE = "done"
