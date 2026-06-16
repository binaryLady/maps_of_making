import asyncio
import dataclasses
import os
import uuid

from dotenv import load_dotenv
import structlog

import bernard
import llm_client
import sparql_client
from config import load_config
from matrix_adapter import MatrixAdapter
from router import route

load_dotenv()

log = structlog.get_logger()

COMMAND_PREFIX = "!mom"


async def handle_message(adapter: MatrixAdapter, message) -> None:
    if not message.text.startswith(COMMAND_PREFIX):
        return

    session_id = str(uuid.uuid4())
    bound = log.bind(session_id=session_id, adapter="matrix", room_id=message.room_id)
    bound.info("message.received", text=message.text)

    stripped = dataclasses.replace(message, text=message.text[len(COMMAND_PREFIX):].strip())
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
    device_id = os.environ.get("MATRIX_DEVICE_ID", "")
    if not (homeserver and user_id and access_token):
        raise ValueError("MATRIX_HOMESERVER/MATRIX_USER_ID/MATRIX_ACCESS_TOKEN must be set in .env or environment")

    sparql_client.OXIGRAPH_ENDPOINT = os.environ.get("OXIGRAPH_ENDPOINT", "http://localhost:7878")

    adapter = MatrixAdapter(homeserver, user_id, access_token, device_id)
    await adapter.start()
    log.info("bot.ready", platform="matrix", model=llm_client.MODEL)

    try:
        while True:
            message = await adapter.receive()
            asyncio.create_task(handle_message(adapter, message))
    finally:
        await adapter.close()


if __name__ == "__main__":
    asyncio.run(main())
