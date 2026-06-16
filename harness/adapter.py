from typing import Protocol, Any

from message import Message


class ChannelAdapter(Protocol):
    async def receive(self) -> Message:
        ...

    async def send(self, response: str, context: Any) -> None:
        ...
