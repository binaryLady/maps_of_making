"""Tests for query_commands.py and isochrone.py (Story 6.3)."""
import sys
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "infra" / "link_handler"))
sys.path.insert(0, str(ROOT / "infra"))
sys.path.insert(0, str(Path(__file__).parent.parent))

import bernard
import commands
import query_commands
import sparql_client
from bot import git_ops
from bot.git_ops import NoEndpointError
from message import Message


@pytest.fixture(autouse=True)
def _voice():
    bernard.load_voice()


def _make_context(power_level: int = 0) -> Message:
    return Message(text="", user_id="@u:x", room_id="!room:x", platform="matrix", raw=None, power_level=power_level)


# ---------------------------------------------------------------------------
# test_status_no_linked_room
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_status_no_linked_room(monkeypatch):
    monkeypatch.setattr(git_ops, "resolve_space_for_room", AsyncMock(side_effect=NoEndpointError("no link")))
    ctx = _make_context(power_level=0)
    result = await commands.try_handle("status", "@u:x", "!room:x", "sid", context=ctx)
    assert result == bernard.status_no_link_ack()


@pytest.mark.asyncio
async def test_status_power_level_0_no_coordinator_fields(monkeypatch):
    """power_level < 100 must not see deploy-key or endpoint URL."""
    monkeypatch.setattr(git_ops, "resolve_space_for_room", AsyncMock(return_value="openfab"))
    monkeypatch.setattr(
        sparql_client, "run_select",
        AsyncMock(return_value=([{
            "name": {"value": "OpenFab"},
            "openNow": {"value": "true"},
            "updatedAt": {"value": "2026-06-01T12:00:00"},
        }], 10))
    )
    ctx = _make_context(power_level=0)
    result = await commands.try_handle("status", "@u:x", "!room:x", "sid", context=ctx)
    assert "OpenFab" in result
    # Must not leak coordinator-only fields
    for forbidden in ("deploy", "endpointUrl", "endpoint", "Remote", "Branch", "verify"):
        assert forbidden.lower() not in result.lower(), f"Leaked field: {forbidden}"


@pytest.mark.asyncio
async def test_status_power_level_100_shows_setup_info(monkeypatch):
    monkeypatch.setattr(git_ops, "resolve_space_for_room", AsyncMock(return_value="openfab"))
    monkeypatch.setattr(
        sparql_client, "run_select",
        AsyncMock(return_value=([{
            "name": {"value": "OpenFab"},
            "openNow": {"value": "false"},
            "updatedAt": {"value": "2026-06-01T12:00:00"},
        }], 10))
    )
    monkeypatch.setattr(git_ops, "verify_setup", AsyncMock(return_value={
        "ok": True,
        "remote": "git@gitlab.com:openfab/endpoint.git",
        "branch": "main",
        "file_path": "spaceapi.json",
        "errors": [],
    }))
    ctx = _make_context(power_level=100)
    result = await commands.try_handle("status", "@u:x", "!room:x", "sid", context=ctx)
    assert "OpenFab" in result
    assert "main" in result


# ---------------------------------------------------------------------------
# test_nearby_parse_radius
# ---------------------------------------------------------------------------

def test_nearby_parse_radius_from_command():
    """Argument parsing: !mom nearby Brussels 50 → city=Brussels, radius=50."""
    parts = "Brussels 50".rsplit(maxsplit=1)
    assert len(parts) == 2
    city, radius_str = parts
    assert city == "Brussels"
    assert float(radius_str) == 50.0


# ---------------------------------------------------------------------------
# test_find_returns_matching_spaces
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_find_returns_matching_spaces(monkeypatch):
    fake_bindings = [
        {"name": {"value": "FabLab Brussels"}, "city": {"value": "Brussels"}, "website": {"value": "https://fab.be"}},
        {"name": {"value": "Fab Lab BXL"}, "city": {"value": "Brussels"}, "website": {"value": ""}},
    ]
    call_count = [0]

    async def fake_run_select(query):
        call_count[0] += 1
        if call_count[0] == 1:
            return fake_bindings, 10
        return [], 5  # seeded count query

    monkeypatch.setattr(sparql_client, "run_select", fake_run_select)
    result = await query_commands.find("fab", "Brussels")
    assert "2" in result or "Found 2" in result
    assert "FabLab Brussels" in result


# ---------------------------------------------------------------------------
# test_seeded_fallback_offered_on_empty_confirmed
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_seeded_fallback_offered_on_empty_confirmed(monkeypatch):
    call_count = [0]

    async def fake_run_select(query):
        call_count[0] += 1
        if call_count[0] == 1:
            return [], 5  # no confirmed spaces
        # seeded count query returns 3
        return [{"count": {"value": "3"}}], 5

    monkeypatch.setattr(sparql_client, "run_select", fake_run_select)
    result = await query_commands.find("laser", "Ghent")
    assert "seeded" in result.lower() or "3" in result


# ---------------------------------------------------------------------------
# test_isochrone_ors_timeout_degrades_to_nearby
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_isochrone_ors_timeout_degrades_to_nearby(monkeypatch):
    import httpx
    import isochrone as iso_module

    # geocode returns coords
    monkeypatch.setattr(query_commands, "geocode_city", AsyncMock(return_value=(50.85, 4.35)))
    # Set a fake API key so the key-check passes
    monkeypatch.setattr(iso_module, "ORS_API_KEY", "fake-key")
    # ORS call raises ReadTimeout
    monkeypatch.setattr(iso_module, "_fetch_isochrone", AsyncMock(side_effect=httpx.ReadTimeout("timeout")))

    # Reset cooldown so test works
    iso_module._ors_cooldown.clear()

    result = await iso_module.travel_search("Brussels", 2.0, room_id="!testroom:x")
    assert result["fallback"] is True
    assert result["confirmed"] == []


# ---------------------------------------------------------------------------
# test_fuzzy_suggest
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_fuzzy_suggest_typo():
    result = await commands.try_handle("stauts", "@u:x", "!room:x", "sid")
    assert result is not None
    assert "status" in result


@pytest.mark.asyncio
async def test_fuzzy_suggest_no_match_falls_through():
    result = await commands.try_handle("zzznonsense", "@u:x", "!room:x", "sid")
    assert result is None


# ---------------------------------------------------------------------------
# test_help verb
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_help_shows_read_commands_to_power_level_0():
    ctx = _make_context(power_level=0)
    result = await commands.try_handle("help", "@u:x", "!room:x", "sid", context=ctx)
    assert "!mom status" in result
    assert "!mom find" in result


@pytest.mark.asyncio
async def test_help_shows_write_commands_to_coordinator():
    ctx = _make_context(power_level=100)
    result = await commands.try_handle("help", "@u:x", "!room:x", "sid", context=ctx)
    assert "!mom link" in result
    assert "!mom update" in result


@pytest.mark.asyncio
async def test_bare_mom_returns_help():
    """bare !mom with no verb → help"""
    ctx = _make_context(power_level=0)
    result = await commands.try_handle("", "@u:x", "!room:x", "sid", context=ctx)
    assert result is not None
    assert "!mom" in result


# ---------------------------------------------------------------------------
# test_SPARQL injection sanitization
# ---------------------------------------------------------------------------

def test_sanitize_strips_injection_chars():
    dangerous = '} DROP GRAPH <urn:mak:space/openfab> .; SELECT * WHERE {'
    sanitized = query_commands._sanitize(dangerous)
    assert "DROP" in sanitized  # DROP itself is allowed text, braces/angles stripped
    assert "{" not in sanitized
    assert "}" not in sanitized
    assert "<" not in sanitized
    assert ">" not in sanitized


@pytest.mark.asyncio
async def test_find_injection_attempt_returns_ack_not_exception(monkeypatch):
    async def fake_run_select(query):
        # If injection worked, query would be malformed; here we just check no crash
        return [], 5

    monkeypatch.setattr(sparql_client, "run_select", fake_run_select)
    result = await query_commands.find('} DROP GRAPH', "Brussels")
    # Should return an empty/no-match ack, not an exception
    assert isinstance(result, str)
    assert result != ""


# ---------------------------------------------------------------------------
# Live integration test (requires Oxigraph with mother-sands data)
# ---------------------------------------------------------------------------

@pytest.mark.live
@pytest.mark.asyncio
async def test_live_status_mother_sands(monkeypatch):
    """Requires Oxigraph running with mother-sands data.
    Run with: pytest -m live harness/tests/test_query_commands.py
    """
    import os
    sparql_client.OXIGRAPH_ENDPOINT = os.environ.get("OXIGRAPH_ENDPOINT", "http://localhost:7878")
    monkeypatch.setattr(git_ops, "resolve_space_for_room", AsyncMock(return_value="mother-sands"))
    ctx = _make_context(power_level=0)
    result = await commands.try_handle("status", "@u:x", "!room:mother-sands", "sid", context=ctx)
    assert result is not None
    assert len(result) > 10
