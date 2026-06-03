"""Gating test for Story 3.6 — walking skeleton end-to-end.

Full-stack, live canary, real seams only:
  1. Fetch the live Mother Sands canary endpoint.
  2. Read observed_at from the snapshot store → T.
  3. SPARQL-SELECT mom:observedAt from urn:mak:canary → assert == T exactly.
  4. Read canary feature's properties.observed_at from spaces.geojson → assert == T exactly.
  5. Assert that the observed_at value is a valid ISO datetime string (browser reads it).

Run with:  pytest -m network infra/link_handler/test_observed_at_skeleton_e2e.py -v
Requires: live Oxigraph at OXIGRAPH_ENDPOINT, network access to CANARY_ENDPOINT_URL.

Note: this test drives pipeline.py seams directly. The canary is just a space with
a fixed (uid, graph, subject) — the canary constants and the single-feature
materializer below are test-only scaffolding (the real heartbeat path materializes
through `_rematerialize_geojson` in main.py).
"""
import json
import os
from pathlib import Path

import pytest

from pipeline import (
    fetch_snapshot,
    write_observed_at,
    read_observed_at_from_oxigraph,
)
from snapshot_store import read_snapshot

CANARY_UID = "mother-sands"
CANARY_SUBJECT = f"urn:mak:canary/{CANARY_UID}"
CANARY_GRAPH = "urn:mak:canary"

CANARY_ENDPOINT_URL = os.environ.get(
    "CANARY_ENDPOINT_URL",
    "https://mapsofmaking.org/canary/mother-sands.json",
)
OXIGRAPH_ENDPOINT = os.environ.get("OXIGRAPH_ENDPOINT", "http://localhost:7878")


pytestmark = pytest.mark.network


def _materialize_canary_geojson(geojson_path: str, db_path: str) -> str:
    """Single-feature canary materializer — test-only scaffolding.

    The regular heartbeat path goes through `_rematerialize_geojson` in main.py
    (SQLite + Oxigraph join). This helper exists solely to exercise the
    observed_at GeoJSON seam in isolation.
    """
    snap = read_snapshot(CANARY_UID, db_path=db_path)
    if snap is None:
        raise RuntimeError("No canary snapshot in store — run fetch_snapshot first")

    observed_at = snap["observed_at"]
    payload = snap["payload"]

    loc = payload.get("location", {})
    lat = loc.get("lat")
    lon = loc.get("lon")
    if lat is None or lon is None:
        geo = payload.get("schema:geo", {})
        if isinstance(geo, list):
            geo = geo[0] if geo else {}
        lat = geo.get("schema:latitude")
        lon = geo.get("schema:longitude")

    if lat is None or lon is None:
        raise ValueError(f"Cannot extract coordinates from canary payload for {CANARY_UID}")

    canary_feature = {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [float(lon), float(lat)]},
        "properties": {
            "id": CANARY_UID,
            "uri": CANARY_SUBJECT,
            "name": payload.get("space") or payload.get("name") or "Mother Sands",
            "observed_at": observed_at,
            "last_fetch_status": snap["fetch_status"],
        },
    }

    path = Path(geojson_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    if path.exists():
        try:
            existing = json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            existing = {"type": "FeatureCollection", "features": []}
    else:
        existing = {"type": "FeatureCollection", "features": []}

    features = [f for f in existing.get("features", []) if f.get("properties", {}).get("id") != CANARY_UID]
    features.append(canary_feature)
    existing["features"] = features

    tmp = path.with_suffix(".geojson.tmp")
    tmp.write_text(json.dumps(existing, separators=(",", ":")))
    tmp.replace(path)
    return observed_at


@pytest.mark.asyncio
async def test_observed_at_skeleton_e2e(tmp_path):
    """Byte-identical observed_at at all four downstream observation points."""
    db_path = str(tmp_path / "snapshot_store.db")
    geojson_path = str(tmp_path / "spaces.geojson")

    # Step 1: clean fetch cycle against live canary
    snap, _content_changed = await fetch_snapshot(CANARY_UID, CANARY_ENDPOINT_URL, db_path=db_path)
    assert snap is not None, (
        f"fetch_snapshot returned None — canary endpoint may be unreachable: {CANARY_ENDPOINT_URL}"
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
    written_at = stored["observed_at"]
    await write_observed_at(OXIGRAPH_ENDPOINT, CANARY_GRAPH, CANARY_SUBJECT, written_at)
    assert written_at == T, (
        f"observed_at written {written_at!r} but snapshot store has {T!r}"
    )

    oxigraph_at = await read_observed_at_from_oxigraph(OXIGRAPH_ENDPOINT, CANARY_GRAPH, CANARY_SUBJECT)
    assert oxigraph_at is not None, "mom:observedAt triple not found in urn:mak:canary after write"
    assert oxigraph_at == T, (
        f"SPARQL read {oxigraph_at!r} ≠ snapshot T={T!r} — observed_at drifted at Oxigraph seam"
    )

    # Step 4: materialize GeoJSON and read back properties.observed_at
    mat_at = _materialize_canary_geojson(geojson_path, db_path=db_path)
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
