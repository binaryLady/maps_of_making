"""Clean canary pipeline for Epic 3.5 — Story 3.6 walking skeleton.

Stages:
  1. fetch_canary_snapshot  — HTTP GET, mint observed_at once, write to snapshot_store
  2. write_canary_to_oxigraph — carry observed_at from store, write mom:observedAt triple
  3. materialize_canary_geojson — carry observed_at from store, update canary feature

observed_at is never re-generated after stage 1. Every stage reads it from the store.

The legacy heartbeat_log / transformer path is untouched.
"""
import json
import logging
import os
from pathlib import Path
from typing import Optional

import httpx

from snapshot_store import mint_observed_at, write_snapshot, read_snapshot

logger = logging.getLogger(__name__)

CANARY_UID = "mother-sands"
CANARY_SUBJECT = f"urn:mak:canary/{CANARY_UID}"
CANARY_GRAPH = "urn:mak:canary"
MOM_NS = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"
XSD_DT = "http://www.w3.org/2001/XMLSchema#dateTime"


async def fetch_canary_snapshot(
    endpoint_url: str,
    db_path: Optional[str] = None,
) -> Optional[dict]:
    """Fetch the canary endpoint, mint observed_at once, persist snapshot.

    Returns the snapshot dict {uid, observed_at, payload, etag, last_modified}
    on HTTP 200, or None on non-200 (error handling is Story 3.7).
    """
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
        resp = await client.get(endpoint_url)

    if resp.status_code != 200:
        logger.warning("canary fetch returned %s — skipping snapshot mint", resp.status_code)
        return None

    observed_at = mint_observed_at()  # minted exactly once, right here
    payload = resp.json()
    etag = resp.headers.get("etag")
    last_modified = resp.headers.get("last-modified")

    write_snapshot(
        uid=CANARY_UID,
        observed_at=observed_at,
        payload=payload,
        etag=etag,
        last_modified=last_modified,
        db_path=db_path,
    )
    logger.info("canary snapshot minted: uid=%s observed_at=%s", CANARY_UID, observed_at)
    return read_snapshot(CANARY_UID, db_path=db_path)


async def write_canary_to_oxigraph(
    oxigraph_endpoint: str,
    db_path: Optional[str] = None,
) -> str:
    """Read observed_at from snapshot store, write mom:observedAt to urn:mak:canary.

    Returns the observed_at value written (for assertion in tests).
    Never calls datetime.now() — copies only.
    """
    snap = read_snapshot(CANARY_UID, db_path=db_path)
    if snap is None:
        raise RuntimeError("No canary snapshot in store — run fetch_canary_snapshot first")

    observed_at = snap["observed_at"]  # copied, never re-minted

    sparql = f"""PREFIX mom: <{MOM_NS}>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

DELETE WHERE {{
  GRAPH <{CANARY_GRAPH}> {{
    <{CANARY_SUBJECT}> mom:observedAt ?t .
  }}
}} ;
INSERT DATA {{
  GRAPH <{CANARY_GRAPH}> {{
    <{CANARY_SUBJECT}> mom:observedAt "{observed_at}"^^xsd:string .
  }}
}}"""

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{oxigraph_endpoint}/update",
            content=sparql,
            headers={"Content-Type": "application/sparql-update"},
        )
        resp.raise_for_status()

    logger.info("canary observedAt written to Oxigraph: %s", observed_at)
    return observed_at


async def read_canary_observed_at_from_oxigraph(oxigraph_endpoint: str) -> Optional[str]:
    """SPARQL-SELECT mom:observedAt for the canary subject. Returns the string value or None."""
    sparql = f"""PREFIX mom: <{MOM_NS}>
SELECT ?t WHERE {{
  GRAPH <{CANARY_GRAPH}> {{
    <{CANARY_SUBJECT}> mom:observedAt ?t .
  }}
}}"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{oxigraph_endpoint}/query",
            content=sparql,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
        )
        resp.raise_for_status()
    bindings = resp.json().get("results", {}).get("bindings", [])
    if not bindings:
        return None
    return bindings[0].get("t", {}).get("value")


def materialize_canary_geojson(
    geojson_path: str,
    db_path: Optional[str] = None,
) -> str:
    """Read observed_at from snapshot store, update canary feature in spaces.geojson.

    Writes only render-critical fields to the canary feature: geolocation, uid,
    properties.observed_at. observed_at is copied from snapshot, never regenerated.

    Returns observed_at written.
    """
    snap = read_snapshot(CANARY_UID, db_path=db_path)
    if snap is None:
        raise RuntimeError("No canary snapshot in store — run fetch_canary_snapshot first")

    observed_at = snap["observed_at"]  # copied, never re-minted
    payload = snap["payload"]

    # Extract coordinates from SpaceAPI payload
    loc = payload.get("location", {})
    lat = loc.get("lat")
    lon = loc.get("lon")
    # Fallback to JSON-LD shape
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
            "observed_at": observed_at,  # copied from snapshot
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

    # Replace or append the canary feature
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
    """Run all three clean pipeline stages for the canary. Returns observed_at or None on fetch failure."""
    snap = await fetch_canary_snapshot(endpoint_url, db_path=db_path)
    if snap is None:
        return None
    await write_canary_to_oxigraph(oxigraph_endpoint, db_path=db_path)
    materialize_canary_geojson(geojson_path, db_path=db_path)
    return snap["observed_at"]
