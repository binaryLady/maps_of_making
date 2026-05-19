"""Test three-token freshness model in materializer (Epic 3.5, Story 3.9).

Validates that GeoJSON materialization correctly joins SQLite (observed_at)
and Oxigraph (updated_at, last_open_change) into each feature.
"""
import json
import pytest
from datetime import datetime, timezone
from pathlib import Path


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
        from scripts.materialize_geojson import materialize_spaces
        geojson = materialize_spaces()

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
        from scripts.materialize_geojson import materialize_spaces
        geojson = materialize_spaces()

        # Verify observed_at comes from SQLite
        feature = next(
            (f for f in geojson["features"] if f["properties"]["id"] == space_id),
            None
        )
        assert feature is not None
        assert feature["properties"]["observed_at"] == sqlite_observed_at
        assert feature["properties"]["updated_at"] == now
