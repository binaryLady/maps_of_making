"""Gating tests for Story 3.8: transformer emits mom:observedAt, no re-stamp.

Tests require live Oxigraph (localhost:7878) and a writable snapshot store.
Mark: @pytest.mark.network (live integration, not collected in hermetic CI runs).
"""
import json
import sys
import tempfile
from pathlib import Path

import httpx
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "infra" / "link_handler"))

from snapshot_store import (
    init_snapshot_db,
    write_snapshot,
    advance_observed_at,
    mint_observed_at,
)
from transformer import transform_to_sparql, build_state_only_update
from main import SpaceAPISchema

OXIGRAPH_URL = "http://localhost:7878"
MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"

BASELINE = {
    "api": "0.13",
    "space": "Test Observed At",
    "logo": "https://example.org/logo.png",
    "url": "https://example.org/",
    "location": {"lat": 51.5, "lon": 0.1, "address": "Test Street"},
    "contact": {"email": "test@example.org"},
    "state": {"open": True},
}


def _query(sparql: str) -> list[dict]:
    resp = httpx.post(
        f"{OXIGRAPH_URL}/query",
        content=sparql,
        headers={"Content-Type": "application/sparql-query",
                 "Accept": "application/sparql-results+json"},
        timeout=10.0,
    )
    resp.raise_for_status()
    return resp.json().get("results", {}).get("bindings", [])


def _update(sparql: str) -> None:
    resp = httpx.post(
        f"{OXIGRAPH_URL}/update",
        content=sparql,
        headers={"Content-Type": "application/sparql-update"},
        timeout=10.0,
    )
    resp.raise_for_status()


@pytest.fixture()
def tmp_db(tmp_path):
    db = str(tmp_path / "snapshot_store.db")
    init_snapshot_db(db)
    return db


@pytest.mark.network
class TestObservedAtRoundtrip:
    """AC 6: observed_at written to Oxigraph byte-identical to snapshot store value."""

    def test_observed_at_roundtrip_real_triplestore(self, tmp_db):
        """Write known T → transform → POST → SELECT → assert == T (byte-exact)."""
        slug = "test-observedat-roundtrip"
        space_uri = f"urn:mak:space/{slug}"
        graph_uri = f"urn:mak:space/{slug}"
        T = "2026-05-19T10:00:00Z"

        write_snapshot(slug, T, BASELINE, fetch_status="ok", db_path=tmp_db)
        schema = SpaceAPISchema(**BASELINE)
        sparql, _ = transform_to_sparql(schema, {
            "endpoint_url": "https://example.org/spaceapi.json",
            "space_id": slug,
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
        }, observed_at=T)

        _update(sparql)

        bindings = _query(f"""PREFIX mom: <{MOM}>
SELECT ?t WHERE {{ GRAPH <{graph_uri}> {{ <{space_uri}> mom:observedAt ?t }} }}""")
        assert len(bindings) == 1, "mom:observedAt should land exactly once in Oxigraph"
        assert bindings[0]["t"]["value"] == T, (
            f"Byte-identity broken: stored {bindings[0]['t']['value']!r} != minted {T!r}"
        )

        _update(f"DROP SILENT GRAPH <{graph_uri}>")

    def test_observed_at_304_unchanged(self, tmp_db):
        """304 path: advance_observed_at → build_state_only_update → SELECT → assert == T2."""
        slug = "test-observedat-304"
        space_uri = f"urn:mak:space/{slug}"
        T1 = "2026-05-19T10:00:00Z"
        T2 = "2026-05-19T10:10:00Z"

        write_snapshot(slug, T1, BASELINE, fetch_status="ok", db_path=tmp_db)
        schema = SpaceAPISchema(**BASELINE)
        sparql, _ = transform_to_sparql(schema, {
            "endpoint_url": "https://example.org/spaceapi.json",
            "space_id": slug,
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
        }, observed_at=T1)
        _update(sparql)

        # Simulate 304: advance observed_at in snapshot store, then propagate to Oxigraph.
        advance_observed_at(slug, T2, db_path=tmp_db)
        state_update = build_state_only_update(space_uri, "healthy", "confirmed",
                                               observed_at=T2)
        _update(state_update)

        bindings = _query(f"""PREFIX mom: <{MOM}>
SELECT ?t WHERE {{ GRAPH <{space_uri}> {{ <{space_uri}> mom:observedAt ?t }} }}""")
        assert len(bindings) == 1
        assert bindings[0]["t"]["value"] == T2, (
            f"After 304, observedAt should be T2={T2!r}, got {bindings[0]['t']['value']!r}"
        )

        _update(f"DROP SILENT GRAPH <{space_uri}>")

    def test_no_mom_lastfetched_or_lastupdated_in_sparql(self):
        """AC 2: CARRY items removed — no lastFetched or lastUpdated in transform output."""
        schema = SpaceAPISchema(**BASELINE)
        sparql, _ = transform_to_sparql(schema, {
            "endpoint_url": "https://example.org/spaceapi.json",
            "space_id": "test-no-carry",
            "endpoint_health": "healthy",
            "lifecycle_state": "confirmed",
        }, observed_at="2026-05-19T10:00:00Z")

        assert "lastFetched" not in sparql, "mom:lastFetched CARRY item still present"
        assert "lastUpdated" not in sparql, "mom:lastUpdated CARRY item still present"
        assert "snapshotDate" not in sparql, "mom:snapshotDate CARRY item still present"

    def test_error_path_does_not_advance_observed_at(self):
        """AC 4: error path build_state_only_update called without observed_at."""
        sparql = build_state_only_update("urn:mak:space/x", "unreachable", "confirmed")
        assert "observedAt" not in sparql, (
            "Error path must NOT update observedAt — frozen token is the staleness signal."
        )
