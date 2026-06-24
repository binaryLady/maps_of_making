from dataclasses import dataclass, field
from typing import Any


@dataclass
class Message:
    text: str
    user_id: str
    room_id: str
    platform: str
    raw: Any
    power_level: int = 0
    event_id: str = ""
    thread_id: str = ""  # thread root event_id; set when message arrives inside a Matrix thread
