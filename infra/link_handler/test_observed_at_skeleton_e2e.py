"""Gating test for Story 3.6 — walking skeleton end-to-end.

Full-stack, live canary, real seams only:
  1. Fetch the live Mother Sands canary endpoint.
  2. Read observed_at from the snapshot store → T.
  3. SPARQL-SELECT mom:observedAt from urn:mak:canary → assert == T exactly.
  4. Read canary feature's properties.observed_at from spaces.geojson → assert == T exactly.
  5. Assert that the observed_at value is a valid ISO datetime string (browser reads it).

Run with:  pytest -m network infra/link_handler/test_observed_at_skeleton_e2e.py -v
Requires: live Oxigraph at OXIGRAPH_ENDPOINT, network access to CANARY_ENDPOINT_URL.
"""
import asyncio
import json
import os
import tempfile
import pytest

from canary_pipeline import (
    fetch_canary_snapshot,
    write_canary_to_oxigraph,
    materialize_canary_geojson,
    read_canary_observed_at_from_oxigraph,
    CANARY_UID,
)
from snapshot_store import read_snapshot

CANARY_ENDPOINT_URL = os.environ.get(
    "CANARY_ENDPOINT_URL",
    "https://mapsofmaking.org/canary/mother-sands.json",
)
OXIGRAPH_ENDPOINT = os.environ.get("OXIGRAPH_ENDPOINT", "http://localhost:7878")


pytestmark = pytest.mark.network


@pytest.mark.asyncio
async def test_observed_at_skeleton_e2e(tmp_path):
    """Byte-identical observed_at at all four downstream observation points."""
    db_path = str(tmp_path / "snapshot_store.db")
    geojson_path = str(tmp_path / "spaces.geojson")

    # Step 1: clean fetch cycle against live canary
    snap, _content_changed = await fetch_canary_snapshot(CANARY_ENDPOINT_URL, db_path=db_path)
    assert snap is not None, (
        f"fetch_canary_snapshot returned None — canary endpoint may be unreachable: {CANARY_ENDPOINT_URL}"
    )

    # Step 2: read T from snapshot store
    stored = read_snapshot(CANARY_UID, db_path=db_path)
    assert stored is not None, "Snapshot not persisted after fetch"
    T = stored["observed_at"]
    assert T, "observed_at is empty in snapshot store"

    # Basic sanity: looks like an ISO datetime
    from datetime import datetime
    dt = datetime.fromisoformat(T.replace("Z", "+00:00"))
    assert dt.tzinfo is not None, "observed_at must be timezone-aware"

    # Step 3: write to Oxigraph and read back mom:observedAt
    written_at = await write_canary_to_oxigraph(OXIGRAPH_ENDPOINT, db_path=db_path)
    assert written_at == T, (
        f"write_canary_to_oxigraph returned {written_at!r} but snapshot store has {T!r}"
    )

    oxigraph_at = await read_canary_observed_at_from_oxigraph(OXIGRAPH_ENDPOINT)
    assert oxigraph_at is not None, "mom:observedAt triple not found in urn:mak:canary after write"
    assert oxigraph_at == T, (
        f"SPARQL read {oxigraph_at!r} ≠ snapshot T={T!r} — observed_at drifted at Oxigraph seam"
    )

    # Step 4: materialize GeoJSON and read back properties.observed_at
    mat_at = materialize_canary_geojson(geojson_path, db_path=db_path)
    assert mat_at == T, (
        f"materialize returned {mat_at!r} but T={T!r} — observed_at drifted at GeoJSON seam"
    )

    geojson_data = json.loads(open(geojson_path).read())
    canary_features = [
        f for f in geojson_data.get("features", [])
        if f.get("properties", {}).get("id") == CANARY_UID
    ]
    assert canary_features, "Canary feature not found in spaces.geojson"
    geojson_at = canary_features[0]["properties"].get("observed_at")
    assert geojson_at == T, (
        f"GeoJSON has {geojson_at!r} but T={T!r} — observed_at drifted at GeoJSON feature seam"
    )

    # Step 5: assert the value is suitable for browser timeAgo() (ISO string)
    # timeAgo() in app.js reads properties.observed_at and calls new Date(iso)
    assert isinstance(geojson_at, str) and len(geojson_at) > 15, (
        "observed_at in GeoJSON is not a usable ISO string for browser age display"
    )
