"""Canary-flavored wrappers around the unified pipeline (Story 3.10 Step 2).

The canary is just another space with a fixed (uid, graph, subject). All real
work now lives in pipeline.py; this module exists to preserve the
fetch_canary_snapshot / write_canary_* / run_canary_pipeline import surface
used by main.py and test_observed_at_skeleton_e2e.py until Step 4 cuts the
last caller over to run_space_pipeline directly.

When that happens, this file can be deleted.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Optional

from snapshot_store import read_snapshot
from pipeline_helpers import _extract_open_now, _extract_last_open_change  # re-exported
from pipeline import (
    MOM_NS,
    XSD_DT,
    fetch_snapshot,
    write_observed_at,
    write_updated_at,
    write_open_now,
    read_observed_at_from_oxigraph,
    run_space_pipeline,
    _space_is_claimed,
)

logger = logging.getLogger(__name__)

CANARY_UID = "mother-sands"
CANARY_SUBJECT = f"urn:mak:canary/{CANARY_UID}"
CANARY_GRAPH = "urn:mak:canary"


async def fetch_canary_snapshot(
    endpoint_url: str,
    db_path: Optional[str] = None,
) -> tuple[Optional[dict], bool]:
    return await fetch_snapshot(CANARY_UID, endpoint_url, db_path=db_path)


async def write_canary_to_oxigraph(
    oxigraph_endpoint: str,
    db_path: Optional[str] = None,
) -> str:
    snap = read_snapshot(CANARY_UID, db_path=db_path)
    if snap is None:
        raise RuntimeError("No canary snapshot in store — run fetch_canary_snapshot first")
    observed_at = snap["observed_at"]
    await write_observed_at(oxigraph_endpoint, CANARY_GRAPH, CANARY_SUBJECT, observed_at)
    return observed_at


async def read_canary_observed_at_from_oxigraph(oxigraph_endpoint: str) -> Optional[str]:
    return await read_observed_at_from_oxigraph(oxigraph_endpoint, CANARY_GRAPH, CANARY_SUBJECT)


async def write_canary_open_now_to_oxigraph(
    oxigraph_endpoint: str,
    open_now: Optional[bool],
    last_open_change: Optional[str],
) -> None:
    await write_open_now(oxigraph_endpoint, CANARY_GRAPH, CANARY_SUBJECT, open_now, last_open_change)


async def write_canary_updated_at_to_oxigraph(
    oxigraph_endpoint: str,
    updated_at: str,
) -> None:
    await write_updated_at(oxigraph_endpoint, CANARY_GRAPH, CANARY_SUBJECT, updated_at)


async def _canary_is_claimed(oxigraph_endpoint: str) -> bool:
    return await _space_is_claimed(oxigraph_endpoint, CANARY_GRAPH, CANARY_SUBJECT)


def materialize_canary_geojson(
    geojson_path: str,
    db_path: Optional[str] = None,
) -> str:
    """Single-feature canary materializer used by the observed_at skeleton test.

    The regular heartbeat path goes through `_rematerialize_geojson` in main.py
    (SQLite + Oxigraph join). This helper is kept solely for the skeleton test.
    """
    snap = read_snapshot(CANARY_UID, db_path=db_path)
    if snap is None:
        raise RuntimeError("No canary snapshot in store — run fetch_canary_snapshot first")

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

    logger.info("canary feature materialized in %s: observed_at=%s", geojson_path, observed_at)
    return observed_at


async def run_canary_pipeline(
    endpoint_url: str,
    oxigraph_endpoint: str,
    geojson_path: str,
    db_path: Optional[str] = None,
) -> Optional[str]:
    """Compatibility shim — delegates to run_space_pipeline.

    geojson_path is ignored (the materializer is invoked by the caller / driver).
    """
    return await run_space_pipeline(
        uid=CANARY_UID,
        endpoint_url=endpoint_url,
        graph_uri=CANARY_GRAPH,
        subject=CANARY_SUBJECT,
        oxigraph_endpoint=oxigraph_endpoint,
        db_path=db_path,
    )


# Re-export detect_diff for any legacy importers
from pipeline_helpers import detect_diff  # noqa: E402,F401
