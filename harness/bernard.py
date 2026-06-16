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
