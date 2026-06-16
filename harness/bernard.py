from pathlib import Path

import structlog
import yaml

log = structlog.get_logger()

_voice: dict | None = None

VOICE_PATH = Path(__file__).parent / "bernard_voice.yaml"


def load_voice() -> dict:
    """Load Bernard's bot-voice strings at startup. Only the graceful-ack
    path lands here; the full voice audit is Story 6.5."""
    global _voice
    if _voice is not None:
        return _voice
    if VOICE_PATH.exists():
        with open(VOICE_PATH) as f:
            _voice = yaml.safe_load(f) or {}
    else:
        log.warning("bernard_voice.yaml not found", path=str(VOICE_PATH))
        _voice = {}
    return _voice


def ping_ack() -> str:
    return load_voice().get("bot", {}).get("ping_ack", "Still here.")


def unknown_ack() -> str:
    return load_voice().get("bot", {}).get("unknown_ack", "Not sure what you mean by that.")


def link_tutorial(public_key: str, tutorial_md: str) -> str:
    template = load_voice().get("bot", {}).get(
        "link_tutorial", "{tutorial}"
    )
    return template.format(public_key=public_key, tutorial=tutorial_md)


def link_failed_ack() -> str:
    return load_voice().get("bot", {}).get(
        "link_failed_ack",
        "I couldn't generate a key for that space — check the space slug is registered, then try again.",
    )


def no_deploy_key_ack() -> str:
    return load_voice().get("bot", {}).get(
        "no_deploy_key_ack",
        "I can read your profile but I can't edit it yet — run `!mom link {space}` first so I get write access.",
    )


def update_failed_ack() -> str:
    return load_voice().get("bot", {}).get(
        "update_failed_ack",
        "That update didn't go through — check the field path and value, then try again.",
    )


def update_succeeded_ack(sha: str) -> str:
    template = load_voice().get("bot", {}).get(
        "update_succeeded_ack", "Done. Committed as {sha}."
    )
    return template.format(sha=sha[:8])
