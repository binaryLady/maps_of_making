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


def query_failed_ack() -> str:
    return _bot("query_failed_ack", "Couldn't reach the directory right now — try again in a moment.")


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


def status_no_link_ack() -> str:
    return _bot("status_no_link_ack", "This room isn't linked to a space yet. Register one with `!mom link {slug}` first.")


def status_lifecycle_ack(name: str, state_line: str, updated_at: str, subset: str = "", unlock_line: str = "") -> str:
    text = _bot("status_lifecycle", "**{name}** · {state_line}\nLast updated: {updated_at}\n{unlock_line}",
                name=name, state_line=state_line, updated_at=updated_at, unlock_line=unlock_line)
    if subset:
        text += f"\nTier: {subset}"
    return text.strip()


def hours_found_ack(name: str, hours: str) -> str:
    return _bot("hours_found", "**{name}** opens: {hours}", name=name, hours=hours)


def hours_missing_ack(name: str) -> str:
    return _bot("hours_missing", "**{name}** hasn't listed opening hours yet.", name=name)


def find_results_ack(count: int, tag: str, city: str, list_text: str) -> str:
    return _bot("find_results", "Found {count} confirmed space(s) matching '{tag}' in {city}:\n{list}",
                count=count, tag=tag, city=city, list=list_text)


def find_empty_ack(tag: str, city: str, seeded_note: str = "") -> str:
    return _bot("find_empty", "No confirmed spaces match '{tag}' in {city}. {seeded_note}",
                tag=tag, city=city, seeded_note=seeded_note)


def nearby_results_ack(radius: int, city: str, count: int, list_text: str) -> str:
    return _bot("nearby_results", "Within {radius}km of {city} — {count} confirmed space(s):\n{list}",
                radius=radius, city=city, count=count, list=list_text)


def nearby_empty_ack(radius: int, city: str, seeded_note: str = "") -> str:
    return _bot("nearby_empty", "Nothing confirmed within {radius}km of {city}. {seeded_note}",
                radius=radius, city=city, seeded_note=seeded_note)


def network_results_ack(network: str, count: int, list_text: str) -> str:
    return _bot("network_results", "**{network}** — {count} confirmed member(s):\n{list}",
                network=network, count=count, list=list_text)


def network_empty_ack(network: str) -> str:
    return _bot("network_empty", "No confirmed spaces list '{network}' as a network. Check the exact name.",
                network=network)


def _fmt_hours(hours: float) -> str:
    mins = round(hours * 60)
    if mins < 60:
        return f"{mins}min"
    h = mins // 60
    m = mins % 60
    return f"{h}h{m:02d}min" if m else f"{h}h"


_MODE_LABELS = {
    "driving-car": "car",
    "cycling-regular": "bike",
    "foot-walking": "foot",
}


def travel_results_ack(hours: float, origin: str, mode: str, count: int, list_text: str, seeded_note: str = "") -> str:
    label = _MODE_LABELS.get(mode, mode)
    return _bot("travel_results",
                "Within {hours} of {origin} by {mode} — {count} confirmed space(s):\n{list}\n{seeded_note}",
                hours=_fmt_hours(hours), origin=origin, mode=label, count=count, list=list_text, seeded_note=seeded_note)


def travel_timeout_ack(fallback_result: str) -> str:
    return _bot("travel_timeout", "ORS took too long — falling back to a bounding box. {fallback_result}",
                fallback_result=fallback_result)


def travel_ors_unavailable_ack(fallback_result: str = "") -> str:
    return _bot("travel_ors_unavailable", "Travel search is temporarily unavailable. {fallback_result}",
                fallback_result=fallback_result)


def seeded_note_ack(count: int) -> str:
    return _bot("seeded_note",
                "{count} seeded space(s) also fall in range — they haven't registered an endpoint yet. Want me to list them?",
                count=count)


def result_cap_note_ack(n: int) -> str:
    return _bot("result_cap_note", "Showing first {n} results — use `!mom find` with a tag and city to narrow down.", n=n)


def did_you_mean_ack(verb: str, suggestion: str) -> str:
    return _bot("did_you_mean", "There's no `{verb}`. Did you mean `!mom {suggestion}`?",
                verb=verb, suggestion=suggestion)


def unknown_command_ack(verb: str) -> str:
    return _bot("unknown_command", "I don't know `{verb}`. Try `!mom help`.", verb=verb)


def bernard_nl_stub_ack() -> str:
    return _bot("bernard_nl_stub", "Natural-language questions are on the roadmap. For now: `!mom help` lists what I can do.")


def help(power_level: int, verb_arg: str, registry: dict) -> str:
    """Render !mom help output. If verb_arg is a known verb, show details for just that verb."""
    if verb_arg and verb_arg in registry:
        min_pl, description, arg_shape = registry[verb_arg]
        arg_str = f" {arg_shape}" if arg_shape else ""
        return f"`!mom {verb_arg}{arg_str}` — {description}"

    header = _bot("help_header", "Here's what I do.")
    read_lines = []
    write_lines = []
    for verb, (min_pl, description, arg_shape) in registry.items():
        arg_str = f" {arg_shape}" if arg_shape else ""
        line = f"• `!mom {verb}{arg_str}` — {description}"
        if min_pl < 100:
            read_lines.append(line)
        else:
            write_lines.append(line)

    parts = [header, "", "**Look things up:**", "\n".join(read_lines)]
    if power_level >= 100:
        parts += ["", "**Changes things:**", "\n".join(write_lines)]
    else:
        parts += ["", "**Changes things** (coordinator only — not available to you):",
                  "\n".join(write_lines)]
    return "\n".join(parts)


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
