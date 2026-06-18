import asyncio
import time

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
        self._start_ts_ms: int = 0  # events older than this are pre-boot; drop them
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
        if self._start_ts_ms and event.server_timestamp < self._start_ts_ms:
            log.debug("matrix.event_skipped_pre_boot", event_id=event.event_id, ts=event.server_timestamp)
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
        # Record boot time before initial sync so _on_message can drop
        # any pre-boot events that fire during the catchup sync.
        self._start_ts_ms = int(time.time() * 1000)
        resp = await self.client.sync(timeout=0, full_state=False)
        since = getattr(resp, "next_batch", None)
        self._sync_task = asyncio.create_task(
            self.client.sync_forever(timeout=30000, since=since)
        )
        log.info("matrix.sync_started", since=since, start_ts_ms=self._start_ts_ms)

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
