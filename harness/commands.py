"""Literal `!mom <verb>` commands — checked before the LLM intent classifier
(see Story 6.1 Dev Notes "Command parsing, not intent routing"). `!mom link`
and `!mom update` are deterministic, argument-parsed commands, not slot-filled
classifications, so they never go through router.route()/intent_classifier.
"""
import asyncio
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

ALLOWED_FIELDS = frozenset({"state.open", "contact.irc", "contact.matrix", "contact.twitter"})


def _can_write(power_level: int, field_path: str) -> tuple[bool, str]:
    """Single permission gate for all write commands. Returns (allowed, reason).
    Future: swap body to also check per-user grants from Oxigraph."""
    if power_level < 100:
        return False, "read_only"
    if field_path not in ALLOWED_FIELDS:
        return False, "field_not_allowed"
    return True, "ok"


def _validate_value(field_path: str, value: str) -> tuple[bool, str]:
    """Field-specific value validation. Returns (valid, error_message)."""
    if field_path == "state.open":
        if value.lower() not in ("true", "false", "null"):
            return False, bernard.invalid_bool_ack()
    elif field_path == "contact.matrix":
        import re
        if not re.match(r"^@[^:]+:[^:]+$", value):
            return False, bernard.invalid_matrix_id_ack()
    else:
        if not value.strip():
            return False, f"Value for {field_path} cannot be empty."
    return True, ""


def _coerce_value(field_path: str, value: str):
    """Convert string value to the appropriate Python type for the field."""
    if field_path == "state.open":
        if value.lower() == "true":
            return True
        if value.lower() == "false":
            return False
        return None  # "null"
    return value


def _to_raw_url(endpoint_url: str) -> str:
    """Return a raw-content URL for polling CDN propagation."""
    if "raw.githubusercontent.com" in endpoint_url:
        return endpoint_url
    if "raw.gitea." in endpoint_url or "codeberg.org/raw" in endpoint_url:
        return endpoint_url
    if "/-/raw/" in endpoint_url:
        return endpoint_url
    raise ValueError(f"Cannot derive a raw polling URL from: {endpoint_url}")


def _extract_field(data: dict, field_path: str):
    """Navigate a dotted field path into a dict."""
    parts = field_path.split(".")
    for part in parts:
        if not isinstance(data, dict):
            return None
        data = data.get(part)
    return data


def _values_match(actual, expected_str: str) -> bool:
    """Compare the actual JSON value to the expected string value."""
    if expected_str.lower() == "null":
        return actual is None
    if expected_str.lower() == "true":
        return actual is True
    if expected_str.lower() == "false":
        return actual is False
    return str(actual) == expected_str


async def _trigger_heartbeat(space_id: str) -> str:
    url = f"{LINK_HANDLER_URL}/api/heartbeat-space/{space_id}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(url)
        if r.status_code == 200:
            return "Endpoint refresh triggered."
        if r.status_code == 429:
            try:
                retry = r.json().get("retry_after_seconds", 60)
            except Exception:
                retry = 60
            return f"A refresh was already triggered recently — re-ingest will complete within {retry}s."
        return f"Endpoint refresh returned {r.status_code} — map will re-ingest on next scheduled cycle (every ~60s+)."
    except httpx.HTTPError as e:
        return f"Endpoint refresh unreachable ({e}) — map will re-ingest on next scheduled cycle."


async def _poll_and_refresh(space_id: str, field_path: str, value: str, sha: str, adapter, context) -> None:
    try:
        endpoint_url = await git_ops._lookup_endpoint_url(space_id)
        raw_url = _to_raw_url(endpoint_url)

        delay, budget, elapsed, confirmed = 5.0, 600.0, 0.0, False
        while elapsed < budget:
            await asyncio.sleep(delay)
            elapsed += delay
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    r = await client.get(raw_url)
                if r.status_code == 200:
                    actual = _extract_field(r.json(), field_path)
                    if _values_match(actual, value):
                        confirmed = True
                        break
            except Exception:
                pass
            delay = min(delay * 2, 60.0)

        if confirmed:
            refresh_note = await _trigger_heartbeat(space_id)
            await adapter.send(bernard.propagation_confirmed_ack(refresh_note), context)
        else:
            await adapter.send(bernard.propagation_timeout_ack(sha), context)
    except Exception as e:
        log.warning("commands.poll_and_refresh_failed", error=str(e))
        try:
            await adapter.send(bernard.propagation_timeout_ack(sha), context)
        except Exception:
            pass


async def try_handle(text: str, user_id: str, room_id: str, session_id: str, *, adapter=None, context=None) -> Optional[str]:
    """Return a response string if `text` matches a known literal command,
    else None (caller falls through to the intent classifier)."""
    parts = text.split(maxsplit=2)
    if not parts:
        return None

    verb = parts[0]
    bound = log.bind(session_id=session_id, room_id=room_id, verb=verb)

    power_level = getattr(context, "power_level", 0) if context is not None else 0

    if verb == "link" and len(parts) >= 2:
        return await _handle_link(parts[1], room_id, bound)

    if verb == "update" and len(parts) >= 3:
        field_path = parts[1]
        value = parts[2].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in ("'", '"'):
            value = value[1:-1]
        return await _handle_update(field_path, value, user_id, room_id, power_level, bound, adapter, context)

    if verb == "open":
        return await _handle_open_close("state.open", "true", user_id, room_id, power_level, bound, adapter, context)

    if verb == "close":
        return await _handle_open_close("state.open", "false", user_id, room_id, power_level, bound, adapter, context)

    if verb == "status":
        return await _handle_status(room_id, power_level, bound)

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
    tutorial_msg = bernard.link_tutorial(data["public_key"], data["tutorial"])

    # Auto-verify: catch the GitHub-Pages-URL bug immediately
    try:
        verify = await git_ops.verify_setup(space_slug)
        tutorial_msg += "\n\n" + bernard.status_report(verify)
    except Exception:
        pass  # verify failure is non-fatal here; !mom status covers it
    return tutorial_msg


async def _handle_update(field_path: str, value: str, authorized_by: str, room_id: str, power_level: int, bound, adapter, context) -> str:
    allowed, reason = _can_write(power_level, field_path)
    if not allowed:
        if reason == "read_only":
            return bernard.read_only_ack()
        if reason == "field_not_allowed":
            return bernard.field_not_allowed_ack(sorted(ALLOWED_FIELDS))
        return bernard.update_failed_ack()

    valid, err = _validate_value(field_path, value)
    if not valid:
        return err

    coerced = _coerce_value(field_path, value)
    try:
        space_id = await git_ops.resolve_space_for_room(room_id)
        sha = await git_ops.commit_json(space_id, field_path, coerced, authorized_by)
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
    if adapter is not None and context is not None:
        asyncio.create_task(_poll_and_refresh(space_id, field_path, value, sha, adapter, context))
    return bernard.update_committed_ack(sha, field_path, value)


async def _handle_open_close(field_path: str, value: str, authorized_by: str, room_id: str, power_level: int, bound, adapter, context) -> str:
    allowed, reason = _can_write(power_level, field_path)
    if not allowed:
        if reason == "read_only":
            return bernard.read_only_ack()
        return bernard.field_not_allowed_ack(sorted(ALLOWED_FIELDS))

    coerced = _coerce_value(field_path, value)
    try:
        space_id = await git_ops.resolve_space_for_room(room_id)
        # Build commit message with open/close shorthand voice
        sha = await git_ops.commit_json(space_id, field_path, coerced, authorized_by)
    except NoDeployKeyError:
        bound.warning("commands.open_close_no_key")
        return bernard.no_deploy_key_ack()
    except (NoEndpointError, UnsupportedHostError) as e:
        bound.warning("commands.open_close_failed", error=str(e))
        return bernard.update_failed_ack()
    except Exception as e:
        bound.warning("commands.open_close_failed", error=str(e))
        return bernard.update_failed_ack()

    bound.info("commands.open_close_succeeded", sha=sha, action=value)
    if adapter is not None and context is not None:
        asyncio.create_task(_poll_and_refresh(space_id, field_path, value, sha, adapter, context))
    if value == "true":
        return bernard.open_ack(sha)
    return bernard.close_ack(sha)


async def _handle_status(room_id: str, power_level: int, bound) -> str:
    if power_level < 100:
        return bernard.read_only_ack()
    try:
        space_id = await git_ops.resolve_space_for_room(room_id)
    except NoEndpointError:
        return bernard.update_failed_ack()

    verify = await git_ops.verify_setup(space_id)
    bound.info("commands.status_checked", ok=verify["ok"])
    return bernard.status_report(verify)
