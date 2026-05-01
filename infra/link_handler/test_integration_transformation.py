"""Integration tests for transformer.py — require a running Oxigraph instance.

Skipped automatically when Oxigraph is not reachable.
To run: start the stack with docker-compose, then run pytest test_integration_transformation.py -v

Isolation note: use `distrobox-host-exec podman compose` on Fedora to start Oxigraph.
"""
import json
import os
import pytest
import asyncio
from datetime import datetime, timezone

import httpx

OXIGRAPH_ENDPOINT = os.getenv("OXIGRAPH_ENDPOINT", "http://localhost:7878")


def _oxigraph_available() -> bool:
    try:
        r = httpx.post(
            f"{OXIGRAPH_ENDPOINT}/query",
            content="ASK {}",
            headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
            timeout=2.0,
        )
        return r.status_code == 200
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _oxigraph_available(),
    reason="Oxigraph not reachable — start the stack to run integration tests",
)


@pytest.fixture
def test_space_id(request):
    """Return a unique test space_id and clean up after the test."""
    space_id = f"test-integration-{request.node.name.replace('[', '').replace(']', '').replace('/', '-')}"
    yield space_id
    # Cleanup: drop test graphs
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    for graph in [f"urn:mak:space/{space_id}", f"urn:mak:space/{space_id}/{today}"]:
        try:
            httpx.post(
                f"{OXIGRAPH_ENDPOINT}/update",
                content=f"DROP SILENT GRAPH <{graph}>",
                headers={"Content-Type": "application/sparql-update"},
                timeout=5.0,
            )
        except Exception:
            pass


@pytest.fixture
def sparql_client():
    """Simple synchronous SPARQL client for test assertions."""
    class SparqlClient:
        def select(self, query: str) -> list:
            r = httpx.post(
                f"{OXIGRAPH_ENDPOINT}/query",
                content=query,
                headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
                timeout=10.0,
            )
            r.raise_for_status()
            return r.json().get("results", {}).get("bindings", [])

        def update(self, sparql: str) -> None:
            r = httpx.post(
                f"{OXIGRAPH_ENDPOINT}/update",
                content=sparql,
                headers={"Content-Type": "application/sparql-update"},
                timeout=10.0,
            )
            r.raise_for_status()

    return SparqlClient()


def test_transform_and_write_to_oxigraph(test_space_id, sparql_client):
    """Full pipeline: schema → transform_to_sparql → Oxigraph write → SELECT verify."""
    from main import SpaceAPISchema
    from transformer import transform_to_sparql

    data = {
        "schema:name": "Integration Test Space",
        "schema:geo": {"schema:latitude": 52.5, "schema:longitude": 13.4},
        "schema:url": "https://example.com/integration",
        "schema:openingHours": "Mo-Fr 10:00-18:00",
    }
    schema = SpaceAPISchema.model_validate(data)
    sparql, snapshot_uri = transform_to_sparql(schema, {"endpoint_url": "https://example.com/api", "space_id": test_space_id})

    sparql_client.update(sparql)

    results = sparql_client.select(f"""
PREFIX schema: <https://schema.org/>
SELECT ?name WHERE {{
  GRAPH <urn:mak:space/{test_space_id}> {{
    <urn:mak:space/{test_space_id}> schema:name ?name .
  }}
}}
""")
    assert len(results) == 1
    assert results[0]["name"]["value"] == "Integration Test Space"


def test_transform_idempotent_double_write(test_space_id, sparql_client):
    """Writing the same space twice should not create duplicate triples."""
    from main import SpaceAPISchema
    from transformer import transform_to_sparql

    data = {
        "schema:name": "Idempotent Space",
        "schema:geo": {"schema:latitude": 48.8, "schema:longitude": 2.35},
    }
    schema = SpaceAPISchema.model_validate(data)
    meta = {"endpoint_url": "https://example.com/api", "space_id": test_space_id}

    sparql1, _ = transform_to_sparql(schema, meta)
    sparql_client.update(sparql1)
    sparql2, _ = transform_to_sparql(schema, meta)
    sparql_client.update(sparql2)

    results = sparql_client.select(f"""
PREFIX schema: <https://schema.org/>
SELECT ?name WHERE {{
  GRAPH <urn:mak:space/{test_space_id}> {{
    <urn:mak:space/{test_space_id}> schema:name ?name .
  }}
}}
""")
    assert len(results) == 1, "Idempotent write should not duplicate triples"


@pytest.mark.asyncio
async def test_fetch_endpoint_conditional_first_fetch(test_space_id, tmp_path):
    """First fetch of a URL should return the response, not 304."""
    from transformer import fetch_endpoint_conditional

    db_path = str(tmp_path / "heartbeat.db")
    resp, headers, was_304 = await fetch_endpoint_conditional(
        "https://example.com", test_space_id, db_path=db_path
    )
    assert was_304 is False
    assert resp is not None


@pytest.mark.skip(reason="Live endpoint test — run manually during dev")
async def test_real_endpoint_openfab_brussels():
    """Fetch the real OpenFab Brussels endpoint and validate the schema."""
    from transformer import fetch_endpoint_conditional
    from main import SpaceAPISchema
    from transformer import classify_operational_state

    endpoint_url = "https://openfab.be/spaces/openfab.jsonld"
    resp, headers, was_304 = await fetch_endpoint_conditional(endpoint_url, "openfab-brussels")

    assert was_304 is False
    assert resp is not None
    assert resp.status_code == 200

    data = resp.json()
    schema = SpaceAPISchema.model_validate(data)
    assert schema.resolved_name is not None
    assert schema.resolved_lat is not None

    from main import classify_subset
    subset_info = classify_subset(schema)
    assert subset_info["subset_score"] >= 1
