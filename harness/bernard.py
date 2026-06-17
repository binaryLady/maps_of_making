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


def _bot(key: str, default: str, **kwargs) -> str:
    text = load_voice().get("bot", {}).get(key, default)
    return text.format(**kwargs) if kwargs else text


def ping_ack() -> str:
    return _bot("ping_ack", "Still here.")


def unknown_ack() -> str:
    return _bot("unknown_ack", "Not sure what you mean by that.")


def link_tutorial(public_key: str, tutorial_md: str) -> str:
    return _bot("link_tutorial", "{tutorial}", public_key=public_key, tutorial=tutorial_md)


def link_failed_ack() -> str:
    return _bot("link_failed_ack", "I couldn't generate a key for that space — check the space slug is registered, then try again.")


def no_deploy_key_ack() -> str:
    return _bot("no_deploy_key_ack", "I can read your profile but I can't edit it yet — run `!mom link` first so I get write access.")


def update_failed_ack() -> str:
    return _bot("update_failed_ack", "That update didn't go through — check the field path and value, then try again.")


def update_succeeded_ack(sha: str) -> str:
    return _bot("update_succeeded_ack", "Done. Committed as {sha}.", sha=sha[:8])


def update_committed_ack(sha: str, field_path: str, value: str) -> str:
    return _bot("update_committed_ack", "Saved — committed as {sha}. Waiting for CDN propagation…", sha=sha[:8])


def propagation_confirmed_ack(refresh_note: str) -> str:
    return _bot("propagation_confirmed_ack", "Map updated. {refresh_note} Hard-refresh your browser.", refresh_note=refresh_note)


def propagation_timeout_ack(sha: str) -> str:
    return _bot("propagation_timeout_ack", "Commit {sha} landed but CDN hasn't propagated after 10 minutes — the map will catch up on its own.", sha=sha[:8])


def open_ack(sha: str) -> str:
    return _bot("open_ack", "Marked as open — committed as {sha}. Waiting for CDN propagation…", sha=sha[:8])


def close_ack(sha: str) -> str:
    return _bot("close_ack", "Marked as closed — committed as {sha}. Waiting for CDN propagation…", sha=sha[:8])


def read_only_ack() -> str:
    return _bot("read_only_ack", "That's a write command — only the space coordinator can make changes.")


def field_not_allowed_ack(fields: list) -> str:
    return _bot("field_not_allowed_ack", "That field isn't editable through me.", fields=", ".join(fields))


def invalid_bool_ack() -> str:
    return _bot("invalid_bool_ack", "state.open needs to be `true`, `false`, or `null`.")


def invalid_matrix_id_ack() -> str:
    return _bot("invalid_matrix_id_ack", "contact.matrix should look like `@username:server`.")


def status_report(verify: dict) -> str:
    if verify["ok"]:
        return _bot(
            "status_ok_ack",
            "Everything looks set up.\n• Remote: {remote}\n• Branch: {branch}\n• File: {file_path}",
            remote=verify.get("remote", ""),
            branch=verify.get("branch", ""),
            file_path=verify.get("file_path", ""),
        )
    error_list = verify.get("errors", [])
    errors = "\n".join(f"• {e}" for e in error_list)
    template = load_voice().get("bot", {}).get(
        "status_error_ack",
        "Setup check found {n} issue(s):\n{errors}\nRun `!mom link` to fix the key or re-register with the correct URL.",
    )
    return template.replace("{n}", str(len(error_list))).replace("{errors}", errors)
