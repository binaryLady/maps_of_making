"""Literal `!mom <verb>` commands — checked before the LLM intent classifier
(see Story 6.1 Dev Notes "Command parsing, not intent routing"). `!mom link`
and `!mom update` are deterministic, argument-parsed commands, not slot-filled
classifications, so they never go through router.route()/intent_classifier.
"""
import os
from typing import Optional

import httpx
import structlog

import bernard
from bot import git_ops
from bot.git_ops import NoDeployKeyError, NoEndpointError, UnsupportedHostError

log = structlog.get_logger()

LINK_HANDLER_URL = os.environ.get("LINK_HANDLER_URL", "http://mak-link-handler:8000")
# Shared secret proving this call came from the bot, not an internet caller —
# /api/ is proxied publicly, so the deploy-key endpoint requires this header
# (Story 6.1 code review finding; same value as link_handler's BOT_KEY_SECRET).
BOT_KEY_SECRET = os.environ.get("BOT_KEY_SECRET", "")


async def try_handle(text: str, user_id: str, room_id: str, session_id: str) -> Optional[str]:
    """Return a response string if `text` matches a known literal command,
    else None (caller falls through to the intent classifier)."""
    parts = text.split(maxsplit=2)
    if not parts:
        return None

    verb = parts[0]
    bound = log.bind(session_id=session_id, room_id=room_id, verb=verb)

    if verb == "link" and len(parts) >= 2:
        return await _handle_link(parts[1], room_id, bound)

    if verb == "update" and len(parts) >= 3:
        value = parts[2].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        return await _handle_update(parts[1], value, user_id, room_id, bound)

    return None


async def _handle_link(space_slug: str, room_id: str, bound) -> str:
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                f"{LINK_HANDLER_URL}/api/bot/deploy-key/{space_slug}",
                params={"room_id": room_id},
                headers={"X-Bot-Secret": BOT_KEY_SECRET},
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as e:
        bound.warning("commands.link_failed", error=str(e))
        return bernard.link_failed_ack()

    bound.info("commands.link_succeeded")
    return bernard.link_tutorial(data["public_key"], data["tutorial"])


async def _handle_update(field_path: str, value: str, authorized_by: str, room_id: str, bound) -> str:
    # No permission model, no power-level check, no field whitelist here — that's
    # Story 6.2. This story's `!mom update` is intentionally wide-open: any matrix
    # user who can type in the room can trigger it. It targets whichever space is
    # linked to the issuing room via mom:botRoom (written by `!mom link`).
    try:
        space_id = await git_ops.resolve_space_for_room(room_id)
        sha = await git_ops.commit_json(space_id, field_path, value, authorized_by)
    except NoDeployKeyError:
        bound.warning("commands.update_no_key")
        return bernard.no_deploy_key_ack()
    except (NoEndpointError, UnsupportedHostError) as e:
        bound.warning("commands.update_failed", error=str(e))
        return bernard.update_failed_ack()
    except Exception as e:
        bound.warning("commands.update_failed", error=str(e))
        return bernard.update_failed_ack()

    bound.info("commands.update_succeeded", sha=sha)
    return bernard.update_succeeded_ack(sha)
