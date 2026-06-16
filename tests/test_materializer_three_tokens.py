"""Test three-token freshness model in materializer (Epic 3.5, Story 3.9).

Validates that GeoJSON materialization correctly joins SQLite (observed_at)
and Oxigraph (updated_at, last_open_change) into each feature.

Repointed 2026-06-16 (Story 6.0 dev-story session): scripts/materialize_geojson.py
was deleted 2026-06-03 (commit 6ddf9db, honest-inventory triage) as a hand-synced
duplicate of the live `_rematerialize_geojson` in infra/link_handler/main.py — these
tests (and their `live_stack` fixture, which never had an implementation anywhere in
the repo) were never repointed at the time, so they only ever errored at collection.
"""
import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "infra" / "link_handler"))
sys.path.insert(0, str(REPO_ROOT))

OXIGRAPH_URL = os.getenv("OXIGRAPH_URL", "http://localhost:7878").rstrip("/")
if OXIGRAPH_URL.endswith("/query"):
    OXIGRAPH_URL = OXIGRAPH_URL[: -len("/query")]


def _oxigraph_alive() -> bool:
    try:
        r = httpx.post(
            f"{OXIGRAPH_URL}/query",
            content="ASK { ?s ?p ?o }",
            headers={"Content-Type": "application/sparql-query",
                     "Accept": "application/sparql-results+json"},
            timeout=2.0,
        )
        return r.status_code == 200
    except Exception:
        return False


class _OxigraphHandle:
    def insert(self, uri: str, sparql: str) -> None:
        r = httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=sparql,
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )
        r.raise_for_status()


class _LiveStack:
    def __init__(self):
        self.oxigraph = _OxigraphHandle()


@pytest.fixture
def live_stack(monkeypatch, tmp_path):
    """Minimal live-stack handle: real Oxigraph + isolated SQLite snapshot store.

    Skips if Oxigraph isn't reachable — this fixture never existed in the repo
    before; these tests only ever errored at collection (`fixture 'live_stack'
    not found`), so there is no prior behaviour to preserve, only the contract
    described in the test docstrings.
    """
    if not _oxigraph_alive():
        pytest.skip(f"Oxigraph not reachable at {OXIGRAPH_URL} — run `make up` first")
    monkeypatch.setenv("SNAPSHOT_DB_PATH", str(tmp_path / "snapshot_store.db"))
    yield _LiveStack()


def _materialize_spaces() -> dict:
    """Drive the live async materializer and return the GeoJSON dict.

    Mirrors tests/test_canary_three_axis_e2e.py::_materialize_feature — see
    that helper's docstring for why this indirection exists.
    """
    import asyncio

    import main as link_handler_main

    link_handler_main.OXIGRAPH_ENDPOINT = OXIGRAPH_URL
    fd, out_path = tempfile.mkstemp(suffix=".geojson")
    os.close(fd)
    link_handler_main.GEOJSON_OUTPUT = out_path
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        loop.run_until_complete(link_handler_main._rematerialize_geojson())
        return json.loads(Path(out_path).read_text())
    finally:
        Path(out_path).unlink(missing_ok=True)


@pytest.mark.live_integration
class TestThreeTokensMaterializer:
    """Live integration tests for GeoJSON materialization with three tokens."""

    @pytest.mark.live_integration
    def test_three_tokens_all_present(self, live_stack):
        """Seed spaces with three tokens and verify materializer includes them.

        Given: Oxigraph has a test space with mom:updatedAt and mom:lastOpenChange
        And: SQLite snapshot store has observed_at for that space
        When: Scripts/materialize_geojson.py runs
        Then: GeoJSON includes all three tokens in feature properties
        And: GeoJSON includes thresholds and generated_at at top level
        """
        space_id = "test-three-tokens-all"
        space_uri = f"urn:mak:space/{space_id}"
        now = datetime.now(timezone.utc).isoformat()
        last_change = "1700000000"  # Unix timestamp

        # Seed space into Oxigraph with three tokens
        live_stack.oxigraph.insert(
            space_uri,
            f"""
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
INSERT DATA {{
  GRAPH <{space_uri}> {{
    <{space_uri}> a mom:Space ;
      schema:name "Test Space All Tokens" ;
      schema:geo [
        schema:latitude 51.5 ;
        schema:longitude 0.1
      ] ;
      mom:updatedAt "{now}"^^<http://www.w3.org/2001/XMLSchema#dateTime> ;
      mom:lastOpenChange "{last_change}"^^<http://www.w3.org/2001/XMLSchema#integer> ;
      mom:openNow "true"^^<http://www.w3.org/2001/XMLSchema#boolean> .
  }}
}}
            """
        )

        # Write observed_at to SQLite snapshot store
        from snapshot_store import write_snapshot
        observed_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        write_snapshot(
            uid=space_id,
            observed_at=observed_at,
            payload={"test": "data"},
            fetch_status="ok"
        )

        # Run materialization
        geojson = _materialize_spaces()

        # Verify three tokens present in feature
        feature = next(
            (f for f in geojson["features"] if f["properties"]["id"] == space_id),
            None
        )
        assert feature is not None, f"Space {space_id} not found in GeoJSON"
        props = feature["properties"]

        assert props.get("observed_at") == observed_at, "observed_at from SQLite"
        assert props.get("updated_at") == now, "updated_at from Oxigraph"
        assert props.get("last_open_change") == last_change, "last_open_change from Oxigraph"
        assert props.get("open_now") is True, "open_now from Oxigraph"

        # Verify top-level metadata
        assert "generated_at" in geojson, "GeoJSON missing generated_at"
        assert "thresholds" in geojson, "GeoJSON missing thresholds"
        assert "endpoint_health" in geojson["thresholds"]
        assert "operational_state" in geojson["thresholds"]

    @pytest.mark.live_integration
    @pytest.mark.skip(
        reason="Tests a CLI contract (sys.exit(1) on zero-token space) that belonged "
        "only to the deleted scripts/materialize_geojson.py standalone script. The "
        "live _rematerialize_geojson() in infra/link_handler/main.py was deliberately "
        "designed fail-silent for the async/heartbeat path per Story 3.9 Dev Notes "
        "('fail-silent for async heartbeat, fail-loud for batch script') — it logs "
        "THREE_TOKENS_MISSING and continues, it never raises/exits. There is no "
        "longer a standalone batch entrypoint to assert a nonzero exit code against."
    )
    def test_three_tokens_missing_exits_nonzero(self, live_stack):
        """Verify standalone script exits non-zero if all three tokens missing.

        Given: A space with NO observed_at in SQLite, NO updated_at in Oxigraph,
               and NO lastOpenChange in Oxigraph (zero tokens)
        When: scripts/materialize_geojson.py runs
        Then: Exit code is non-zero
        And: THREE_TOKENS_MISSING logged
        """
        space_id = "test-zero-tokens"
        space_uri = f"urn:mak:space/{space_id}"

        # Seed space with NO three-token fields
        live_stack.oxigraph.insert(
            space_uri,
            f"""
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
INSERT DATA {{
  GRAPH <{space_uri}> {{
    <{space_uri}> a mom:Space ;
      schema:name "Test Space No Tokens" ;
      schema:geo [
        schema:latitude 51.5 ;
        schema:longitude 0.1
      ] .
  }}
}}
            """
        )

        # DO NOT write to snapshot store — leave observed_at missing

        # Run materialization (should exit non-zero)
        import subprocess
        result = subprocess.run(
            ["python", "scripts/materialize_geojson.py"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        assert result.returncode != 0, "Expected non-zero exit for zero-token space"
        assert "THREE_TOKENS_MISSING" in result.stderr or "THREE_TOKENS_MISSING" in result.stdout

    @pytest.mark.live_integration
    def test_observed_at_from_sqlite_not_oxigraph(self, live_stack):
        """Verify observed_at is read from SQLite, not Oxigraph.

        Given: A space with NO mom:observedAt in Oxigraph
        And: SQLite snapshot store has observed_at value
        When: Materialization runs
        Then: GeoJSON feature carries the SQLite observed_at value
        (Not null, not from Oxigraph)
        """
        space_id = "test-sqlite-observed-at"
        space_uri = f"urn:mak:space/{space_id}"
        now = datetime.now(timezone.utc).isoformat()
        last_change = "1700000001"

        # Seed space with updated_at and lastOpenChange but NO mom:observedAt
        live_stack.oxigraph.insert(
            space_uri,
            f"""
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
INSERT DATA {{
  GRAPH <{space_uri}> {{
    <{space_uri}> a mom:Space ;
      schema:name "Test Space SQLite Observed" ;
      schema:geo [
        schema:latitude 52.0 ;
        schema:longitude 0.2
      ] ;
      mom:updatedAt "{now}"^^<http://www.w3.org/2001/XMLSchema#dateTime> ;
      mom:lastOpenChange "{last_change}"^^<http://www.w3.org/2001/XMLSchema#integer> .
  }}
}}
            """
        )

        # Write observed_at ONLY to SQLite
        from snapshot_store import write_snapshot
        sqlite_observed_at = "2026-05-19T10:30:45Z"
        write_snapshot(
            uid=space_id,
            observed_at=sqlite_observed_at,
            payload={"test": "data"},
            fetch_status="ok"
        )

        # Run materialization
        geojson = _materialize_spaces()

        # Verify observed_at comes from SQLite
        feature = next(
            (f for f in geojson["features"] if f["properties"]["id"] == space_id),
            None
        )
        assert feature is not None
        assert feature["properties"]["observed_at"] == sqlite_observed_at
        assert feature["properties"]["updated_at"] == now
