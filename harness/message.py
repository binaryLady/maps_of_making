from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    text: str
    user_id: str
    room_id: str
    platform: str
    raw: Any
