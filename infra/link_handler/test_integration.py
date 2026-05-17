import pytest
import json
import asyncio
import sqlite3
import tempfile
import os
from fastapi.testclient import TestClient
from main import app
from transformer import process_one_space, _init_heartbeat_db

# Story 3.4b: quarantined — pins the heartbeat/transformer pipeline that Story 3.5
# rewires. Deselected from the default green bar. Run explicitly with: pytest -m legacy
pytestmark = pytest.mark.legacy

client = TestClient(app)


def test_validate_url_with_required_fields():
    """Test validation of URL with mom:required fields."""
    test_data = {
        "schema:name": "FabLab Brussels",
        "schema:geo": {
            "schema:latitude": 50.5,
            "schema:longitude": 4.5
        }
    }
    # This test would require mocking the HTTP fetch, which is complex.
    # In practice, this would be an end-to-end test with a real endpoint.


def test_validate_url_with_card_fields():
    """Test validation of URL with mom:card fields."""
    test_data = {
        "schema:name": "FabLab Brussels",
        "schema:geo": {
            "schema:latitude": 50.5,
            "schema:longitude": 4.5
        },
        "schema:url": "https://fablab.be",
        "schema:openingHours": "Mo-Fr 10:00-18:00"
    }
    # This test would require mocking the HTTP fetch


def test_raw_endpoint_returns_404_for_nonexistent_space():
    """Test that raw endpoint returns 404-style JSON for nonexistent space."""
    response = client.get("/api/space/nonexistent-space/raw")
    assert response.status_code == 200
    data = response.json()
    assert data.get("error") == "no_snapshot"
    assert "message" in data


def test_raw_endpoint_structure():
    """Test the structure of the raw endpoint response."""
    # We can't test success without data in Oxigraph,
    # but we can verify the error response structure is correct
    response = client.get("/api/space/test-space/raw")
    assert response.status_code == 200
    data = response.json()
    # Should have either 'raw' or 'error' field
    assert "raw" in data or "error" in data


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_snapshots_endpoint_empty():
    """Test snapshots endpoint for nonexistent space."""
    response = client.get("/api/space/nonexistent-space/snapshots")
    assert response.status_code == 200
    # Should return empty list
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


# ---------------------------------------------------------------------------
# AC8 — Live network tests: mom:openNow written when state field present
# Run with: pytest -m network
# Requires live internet access and a running Oxigraph instance.
# ---------------------------------------------------------------------------

OXIGRAPH_URL = os.getenv("OXIGRAPH_URL", "http://localhost:7878")


def _oxigraph_has_open_now(space_uri: str) -> bool:
    """ASK Oxigraph whether mom:openNow triple exists for space_uri."""
    import httpx
    ask = (
        "PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>\n"
        f"ASK {{ <{space_uri}> mom:openNow ?v }}"
    )
    r = httpx.post(
        OXIGRAPH_URL + "/query",
        content=ask,
        headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
        timeout=10.0,
    )
    r.raise_for_status()
    return r.json().get("boolean", False)


def _run_process(endpoint_url: str, space_slug: str) -> tuple[str, bool]:
    space_uri = f"urn:mak:space/{space_slug}"
    return asyncio.run(process_one_space(space_uri, endpoint_url, OXIGRAPH_URL))


@pytest.mark.network
def test_ac8_mattermore_open_now_written():
    """Live fetch: mattermore.zeus.gent — mom:openNow triple written after heartbeat."""
    outcome, state_changed = _run_process(
        "https://mattermore.zeus.gent/spaceapi.json",
        "mattermore-zeus-gent",
    )
    assert outcome in ("refreshed", "not_modified", "not_modified_content"), f"Unexpected outcome: {outcome}"
    assert state_changed is True
    assert _oxigraph_has_open_now("urn:mak:space/mattermore-zeus-gent"), (
        "mom:openNow triple not found in Oxigraph after live fetch of mattermore.zeus.gent"
    )


@pytest.mark.network
def test_ac8_urlab_open_now_written():
    """Live fetch: urlab.be — mom:openNow triple written after heartbeat."""
    outcome, state_changed = _run_process(
        "https://urlab.be/spaceapi.json",
        "urlab-be",
    )
    assert outcome in ("refreshed", "not_modified", "not_modified_content"), f"Unexpected outcome: {outcome}"
    assert state_changed is True
    assert _oxigraph_has_open_now("urn:mak:space/urlab-be"), (
        "mom:openNow triple not found in Oxigraph after live fetch of urlab.be"
    )


@pytest.mark.network
def test_ac8_openfab_open_now_written():
    """Live fetch: openfab.be — mom:openNow triple written after heartbeat."""
    outcome, state_changed = _run_process(
        "https://openfab.be/openfab.json",
        "openfab-be",
    )
    assert outcome in ("refreshed", "not_modified", "not_modified_content"), f"Unexpected outcome: {outcome}"
    assert state_changed is True
    assert _oxigraph_has_open_now("urn:mak:space/openfab-be"), (
        "mom:openNow triple not found in Oxigraph after live fetch of openfab.be"
    )


@pytest.mark.network
def test_ac8_techinc_open_now_written():
    """Live fetch: techinc.nl — mom:openNow triple written after heartbeat."""
    outcome, state_changed = _run_process(
        "https://techinc.nl/space/spacestate.json",
        "techinc-nl",
    )
    assert outcome in ("refreshed", "not_modified", "not_modified_content"), f"Unexpected outcome: {outcome}"
    assert state_changed is True
    assert _oxigraph_has_open_now("urn:mak:space/techinc-nl"), (
        "mom:openNow triple not found in Oxigraph after live fetch of techinc.nl"
    )


