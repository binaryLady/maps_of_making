import asyncio
import dataclasses
import os
import re
import uuid

from dotenv import load_dotenv
import structlog

import bernard
import commands
import llm_client
import sparql_client
from config import load_config
from matrix_adapter import MatrixAdapter
from router import route

load_dotenv()

log = structlog.get_logger()

COMMAND_PREFIX = "!mom"


def _log_task_exception(task: asyncio.Task) -> None:
    exc = task.exception() if not task.cancelled() else None
    if exc:
        log.error("handle_message.failed", exc_info=exc)


def _is_bernard_mention(text: str) -> bool:
    """Match @bernard or display-name mention at start of message."""
    return bool(re.match(r"^@?bernard[\s,:]+", text, re.IGNORECASE))


async def handle_message(adapter: MatrixAdapter, message) -> None:
    # @bernard mention stub — intercept before !mom prefix check (NL deferred to 6.4)
    if message.text and _is_bernard_mention(message.text):
        await adapter.send(bernard.bernard_nl_stub_ack(), message)
        return

    if not message.text.startswith(COMMAND_PREFIX):
        return

    session_id = str(uuid.uuid4())
    bound = log.bind(session_id=session_id, adapter="matrix", room_id=message.room_id)
    bound.info("message.received", text=message.text)

    stripped = dataclasses.replace(message, text=message.text[len(COMMAND_PREFIX):].strip())

    # Literal !mom <verb> commands (link, update) are matched before the LLM
    # intent classifier — see Story 6.1 Dev Notes "Command parsing, not intent
    # routing". Only messages that don't match a known verb fall through to route().
    response = await commands.try_handle(
        stripped.text, message.user_id, message.room_id, session_id,
        adapter=adapter, context=message,
    )
    if response is None:
        response = await route(stripped, session_id)

    bound.info("message.responded", response=response)
    await adapter.send(response, message)


async def main() -> None:
    config = load_config()
    bot_cfg = config.get("bot", {})

    llm_client.MODEL = bot_cfg.get("model") or llm_client.DEFAULT_MODEL
    bernard.load_voice()

    homeserver = os.environ.get("MATRIX_HOMESERVER") or bot_cfg.get("matrix_homeserver")
    user_id = os.environ.get("MATRIX_USER_ID")
    access_token = os.environ.get("MATRIX_ACCESS_TOKEN")
    device_id = os.environ.get("MATRIX_DEVICE_ID") or None
    if not (homeserver and user_id and access_token):
        raise ValueError("MATRIX_HOMESERVER/MATRIX_USER_ID/MATRIX_ACCESS_TOKEN must be set in .env or environment")

    sparql_client.OXIGRAPH_ENDPOINT = os.environ.get("OXIGRAPH_ENDPOINT", "http://localhost:7878")

    adapter = MatrixAdapter(homeserver, user_id, access_token, device_id)
    try:
        await adapter.start()
        log.info("bot.ready", platform="matrix", model=llm_client.MODEL)

        while True:
            try:
                message = await adapter.receive()
            except Exception:
                log.exception("adapter.receive_failed")
                continue
            task = asyncio.create_task(handle_message(adapter, message))
            task.add_done_callback(_log_task_exception)
    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(main())
