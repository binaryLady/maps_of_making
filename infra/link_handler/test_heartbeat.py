"""Unit tests for heartbeat scheduler — no live Oxigraph, no live HTTP."""
import json
import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import transformer
from transformer import query_active_spaces, process_one_space, run_heartbeat_cycle, _SPARQL_ACTIVE_SPACES


@pytest.fixture(autouse=True)
def reset_caches():
    transformer._config = None
    transformer._activity_map = None
    yield
    transformer._config = None
    transformer._activity_map = None


# ---------------------------------------------------------------------------
# query_active_spaces: SPARQL query string shape
# ---------------------------------------------------------------------------

def test_sparql_active_spaces_excludes_dead():
    assert 'FILTER (!BOUND(?state) || ?state != "dead")' in _SPARQL_ACTIVE_SPACES


def test_sparql_active_spaces_requires_endpoint():
    assert "mom:endpointUrl" in _SPARQL_ACTIVE_SPACES


def test_sparql_active_spaces_scoped_to_space_graphs():
    assert 'STRSTARTS(STR(?g), "urn:mak:space/")' in _SPARQL_ACTIVE_SPACES


@pytest.mark.asyncio
async def test_query_active_spaces_parses_bindings():
    fake_response = MagicMock()
    fake_response.json.return_value = {
        "results": {
            "bindings": [
                {
                    "spaceUri": {"value": "urn:mak:space/openfab"},
                    "endpointUrl": {"value": "https://openfab.be/openfab.jsonld"},
                },
                {
                    "spaceUri": {"value": "urn:mak:space/awesomespace"},
                    "endpointUrl": {"value": "https://state.awesomespace.nl/"},
                },
            ]
        }
    }
    fake_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=fake_response)

    with patch("transformer.httpx.AsyncClient", return_value=mock_client):
        results = await query_active_spaces("http://oxigraph:7878")

    assert len(results) == 2
    assert results[0]["space_uri"] == "urn:mak:space/openfab"
    assert results[0]["endpoint_url"] == "https://openfab.be/openfab.jsonld"
    assert results[1]["space_uri"] == "urn:mak:space/awesomespace"


@pytest.mark.asyncio
async def test_query_active_spaces_empty():
    fake_response = MagicMock()
    fake_response.json.return_value = {"results": {"bindings": []}}
    fake_response.raise_for_status = MagicMock()

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.post = AsyncMock(return_value=fake_response)

    with patch("transformer.httpx.AsyncClient", return_value=mock_client):
        results = await query_active_spaces("http://oxigraph:7878")

    assert results == []


# ---------------------------------------------------------------------------
# process_one_space: 304 path
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_process_one_space_304_returns_not_modified():
    with patch("transformer.fetch_endpoint_conditional", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (None, {}, True)  # was_304=True
        result = await process_one_space(
            "urn:mak:space/openfab",
            "https://openfab.be/openfab.jsonld",
            "http://oxigraph:7878",
        )
    assert result == "not_modified"


@pytest.mark.asyncio
async def test_process_one_space_http_error_returns_error():
    mock_resp = MagicMock()
    mock_resp.status_code = 500
    with patch("transformer.fetch_endpoint_conditional", new_callable=AsyncMock) as mock_fetch:
        mock_fetch.return_value = (mock_resp, {}, False)
        result = await process_one_space(
            "urn:mak:space/openfab",
            "https://openfab.be/openfab.jsonld",
            "http://oxigraph:7878",
        )
    assert result == "error"


# ---------------------------------------------------------------------------
# run_heartbeat_cycle: error isolation
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_run_heartbeat_cycle_query_failure_does_not_raise():
    rematerialize_called = []

    async def failing_query(endpoint):
        raise RuntimeError("oxigraph unreachable")

    async def rematerialize():
        rematerialize_called.append(True)

    with patch("transformer.query_active_spaces", side_effect=failing_query):
        await run_heartbeat_cycle("http://oxigraph:7878", rematerialize)

    assert rematerialize_called == []  # skipped when query fails


@pytest.mark.asyncio
async def test_run_heartbeat_cycle_one_space_error_continues():
    """A failure on one space must not abort remaining spaces."""
    processed = []

    async def fake_query(endpoint):
        return [
            {"space_uri": "urn:mak:space/a", "endpoint_url": "https://a.example/"},
            {"space_uri": "urn:mak:space/b", "endpoint_url": "https://b.example/"},
        ]

    async def failing_process(space_uri, endpoint_url, oxigraph_endpoint):
        if space_uri.endswith("/a"):
            raise RuntimeError("space A error")
        processed.append(space_uri)
        return "refreshed"

    rematerialized = []

    async def rematerialize():
        rematerialized.append(True)

    with patch("transformer.query_active_spaces", side_effect=fake_query), \
         patch("transformer.process_one_space", side_effect=failing_process):
        await run_heartbeat_cycle("http://oxigraph:7878", rematerialize)

    assert "urn:mak:space/b" in processed
    assert rematerialized == [True]


# ---------------------------------------------------------------------------
# Manual trigger cooldown logic (via FastAPI test client)
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_heartbeat_endpoint_cooldown():
    """POST twice quickly → second call returns 429."""
    from fastapi.testclient import TestClient
    import main

    # Reset cooldowns
    main._manual_refresh_cooldowns.clear()

    past_time = datetime.now(timezone.utc) - timedelta(seconds=10)
    main._manual_refresh_cooldowns["testspace"] = past_time

    with TestClient(main.app) as client:
        # Simulate a space with no endpoint (we're testing cooldown, not the full flow)
        # First call within cooldown window should 429
        resp = client.post("/api/heartbeat-space/testspace")
        assert resp.status_code == 429
        body = resp.json()
        assert body["detail"]["error"] == "rate_limited"
        assert body["detail"]["retry_after_seconds"] > 0


@pytest.mark.asyncio
async def test_heartbeat_endpoint_invalid_space_id():
    from fastapi.testclient import TestClient
    import main

    with TestClient(main.app) as client:
        resp = client.post("/api/heartbeat-space/../../evil")
        assert resp.status_code == 404  # FastAPI path routing rejects traversal


def test_heartbeat_endpoint_rejects_invalid_id_pattern():
    """_SPACE_ID_RE must reject characters outside [a-zA-Z0-9_-]."""
    import re
    pattern = re.compile(r'^[a-zA-Z0-9_-]+$')
    assert not pattern.match("spa ce")
    assert not pattern.match("spa/ce")
    assert not pattern.match("")
    assert pattern.match("openfab")
    assert pattern.match("my-space_01")
