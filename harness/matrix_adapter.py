import asyncio

import structlog
from nio import AsyncClient, InviteMemberEvent, MatrixRoom, RoomMessageText

from message import Message

log = structlog.get_logger()


class MatrixAdapter:
    """ChannelAdapter for Matrix via matrix-nio. Buffers incoming room text
    messages onto an internal queue so receive() can be awaited one at a time,
    independent of nio's callback-driven sync loop."""

    def __init__(self, homeserver: str, user_id: str, access_token: str, device_id: str | None = None):
        self.client = AsyncClient(homeserver, user_id)
        self.client.access_token = access_token
        self.client.user_id = user_id
        self.client.device_id = device_id
        self._queue: asyncio.Queue[Message] = asyncio.Queue()
        self._sync_task: asyncio.Task | None = None
        self.client.add_event_callback(self._on_message, RoomMessageText)
        self.client.add_event_callback(self._on_invite, InviteMemberEvent)

    async def _on_invite(self, room: MatrixRoom, event: InviteMemberEvent) -> None:
        # matrix-nio does not auto-join invites (by design, per its own
        # examples) — without this callback, every invite sits pending
        # until something calls client.join() explicitly.
        if event.state_key != self.client.user_id:
            return
        await self.client.join(room.room_id)
        log.info("matrix.invite_joined", room_id=room.room_id)

    async def _on_message(self, room: MatrixRoom, event: RoomMessageText) -> None:
        if event.sender.lower() == self.client.user_id.lower():
            return
        message = Message(
            text=event.body,
            user_id=event.sender,
            room_id=room.room_id,
            platform="matrix",
            raw=event,
            power_level=room.power_levels.get_user_level(event.sender),
        )
        await self._queue.put(message)

    async def start(self) -> None:
        self._sync_task = asyncio.create_task(self.client.sync_forever(timeout=30000))
        log.info("matrix.sync_started")

    async def receive(self) -> Message:
        return await self._queue.get()

    async def send(self, response: str, context: Message) -> None:
        await self.client.room_send(
            room_id=context.room_id,
            message_type="m.room.message",
            content={"msgtype": "m.text", "body": response},
        )

    async def close(self) -> None:
        if self._sync_task:
            self._sync_task.cancel()
        await self.client.close()
