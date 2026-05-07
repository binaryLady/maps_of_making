#!/usr/bin/env python3
"""Seed local Oxigraph from the SpaceAPI federation directory.

Fetches https://directory.spaceapi.io/ (a name → endpoint URL map), fetches each
SpaceAPI endpoint concurrently, and writes seeded mom:Space graphs tagged with
mom:memberOf <urn:mak:network/spaceapi> (renders as the "SPACEAPI" filter chip).

Heartbeat picks the spaces up on its next cycle to populate Zone 3 / track liveness.

PII rule: only public fields (name, geo, website, endpoint URL) are stored.
contact.email / phone / etc. are discarded — same policy as Story 3.2b.

Coordinator-registered graphs (mom:source = "self-registered") are protected from
overwrite even with --force, mirroring seed_import.py behaviour.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
from typing import Any

import httpx

OXIGRAPH_ENDPOINT = os.getenv("OXIGRAPH_ENDPOINT", "http://localhost:7878")
UPDATE_URL = f"{OXIGRAPH_ENDPOINT}/update"
QUERY_URL = f"{OXIGRAPH_ENDPOINT}/query"

DIRECTORY_URL = "https://directory.spaceapi.io/"
NETWORK_URI = "urn:mak:network/spaceapi"
SOURCE_TAG = "spaceapi-directory"

FETCH_CONCURRENCY = 20
PER_ENDPOINT_TIMEOUT = 10.0

# Match the map maxBounds from app.js: [[-25, 34], [45, 72]]
BBOX_WEST, BBOX_SOUTH, BBOX_EAST, BBOX_NORTH = -25, 34, 45, 72

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("seed_spaceapi")


def sparql_str(val: str | None) -> str:
    if val is None:
        return '""'
    escaped = str(val).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def space_id(name: str, endpoint_url: str) -> str:
    raw = f"{name}|{endpoint_url}".lower().strip()
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def graph_source(client: httpx.Client, graph_uri: str) -> str | None:
    """Return the mom:source literal of an existing graph, or None if not present."""
    query = (
        "PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#> "
        f"SELECT ?src WHERE {{ GRAPH <{graph_uri}> {{ ?s mom:source ?src }} }} LIMIT 1"
    )
    resp = client.post(
        QUERY_URL,
        data=query,
        headers={
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        },
    )
    resp.raise_for_status()
    bindings = resp.json().get("results", {}).get("bindings", [])
    if not bindings:
        return None
    return bindings[0].get("src", {}).get("value")


def extract_fields(payload: dict[str, Any]) -> tuple[str | None, float | None, float | None, str | None]:
    """Extract (name, lat, lon, website) from a SpaceAPI v14/v15 payload."""
    name = payload.get("space")
    url = payload.get("url")
    loc = payload.get("location") or {}
    lat = loc.get("lat")
    lon = loc.get("lon")
    try:
        lat = float(lat) if lat is not None else None
        lon = float(lon) if lon is not None else None
    except (TypeError, ValueError):
        lat = lon = None
    return (name if isinstance(name, str) and name else None, lat, lon, url if isinstance(url, str) and url else None)


def build_insert(name: str, lat: float, lon: float, website: str | None, endpoint_url: str) -> tuple[str, str]:
    sid = space_id(name, endpoint_url)
    graph_uri = f"urn:mak:space/{sid}"
    subject = f"<{graph_uri}>"
    triples = f"{subject} a mom:Space"
    triples += f" ;\n    schema:name {sparql_str(name)}@en"
    triples += f" ;\n    schema:geo [\n      schema:latitude {lat} ;\n      schema:longitude {lon}\n    ]"
    if website:
        triples += f" ;\n    schema:url <{website}>"
    triples += f" ;\n    mom:endpointUrl <{endpoint_url}>"
    triples += f" ;\n    mom:source {sparql_str(SOURCE_TAG)}"
    triples += f" ;\n    mom:operationalState {sparql_str('seeded')}"
    triples += f" ;\n    mom:memberOf <{NETWORK_URI}>"
    triples += " ."

    insert_query = (
        "PREFIX schema: <https://schema.org/>\n"
        "PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>\n"
        f"INSERT DATA {{\n  GRAPH <{graph_uri}> {{\n    {triples}\n  }}\n}}"
    )
    return graph_uri, insert_query


async def fetch_endpoint(
    name: str,
    endpoint_url: str,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
) -> tuple[str, str, dict[str, Any] | None, str | None]:
    """Return (name, endpoint_url, payload_or_none, error_kind_or_none)."""
    async with sem:
        try:
            resp = await client.get(endpoint_url, timeout=PER_ENDPOINT_TIMEOUT, follow_redirects=True)
            resp.raise_for_status()
            try:
                payload = resp.json()
            except (json.JSONDecodeError, ValueError):
                return name, endpoint_url, None, "invalid_json"
            if not isinstance(payload, dict):
                return name, endpoint_url, None, "invalid_json"
            return name, endpoint_url, payload, None
        except httpx.HTTPError:
            return name, endpoint_url, None, "fetch_failed"
        except Exception:
            return name, endpoint_url, None, "fetch_failed"


async def fetch_all(directory: dict[str, str]) -> list[tuple[str, str, dict[str, Any] | None, str | None]]:
    sem = asyncio.Semaphore(FETCH_CONCURRENCY)
    async with httpx.AsyncClient(headers={"User-Agent": "MapsOfMaking-seed/1.0"}) as client:
        tasks = [fetch_endpoint(name, url, client, sem) for name, url in directory.items()]
        return await asyncio.gather(*tasks)


def fetch_directory() -> dict[str, str]:
    log.info(f"Fetching directory: {DIRECTORY_URL}")
    resp = httpx.get(DIRECTORY_URL, timeout=20.0)
    resp.raise_for_status()
    data = resp.json()
    if not isinstance(data, dict):
        raise RuntimeError(f"Unexpected directory format: {type(data).__name__}")
    return {k: v for k, v in data.items() if isinstance(k, str) and isinstance(v, str)}


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Oxigraph from SpaceAPI federation directory")
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing spaceapi-sourced graphs (still skips coordinator-registered)",
    )
    args = parser.parse_args()

    try:
        directory = fetch_directory()
    except Exception as e:
        log.error(f"Directory fetch failed: {e}")
        return 1

    log.info(f"Directory has {len(directory)} entries — fetching with concurrency={FETCH_CONCURRENCY}")
    results = asyncio.run(fetch_all(directory))

    counters = {
        "imported": 0,
        "updated": 0,
        "skipped_existing": 0,
        "skipped_coordinator": 0,
        "fetch_failed": 0,
        "invalid_json": 0,
        "no_geo": 0,
        "no_name": 0,
        "write_failed": 0,
    }

    with httpx.Client(timeout=15.0) as client:
        for name, endpoint_url, payload, err in results:
            if err == "fetch_failed":
                counters["fetch_failed"] += 1
                continue
            if err == "invalid_json":
                counters["invalid_json"] += 1
                continue

            extracted_name, lat, lon, website = extract_fields(payload)
            chosen_name = extracted_name or name
            if not chosen_name:
                counters["no_name"] += 1
                continue
            if lat is None or lon is None or not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                counters["no_geo"] += 1
                continue
            if not (BBOX_SOUTH <= lat <= BBOX_NORTH and BBOX_WEST <= lon <= BBOX_EAST):
                counters["no_geo"] += 1
                continue

            graph_uri, insert_query = build_insert(chosen_name, lat, lon, website, endpoint_url)

            try:
                existing_source = graph_source(client, graph_uri)
            except httpx.HTTPError as e:
                log.error(f"ASK failed for {graph_uri}: {e}")
                counters["write_failed"] += 1
                continue

            if existing_source == "self-registered":
                counters["skipped_coordinator"] += 1
                continue

            if existing_source is not None:
                if not args.force:
                    counters["skipped_existing"] += 1
                    continue
                clear = client.post(
                    UPDATE_URL,
                    data=f"CLEAR GRAPH <{graph_uri}>",
                    headers={"Content-Type": "application/sparql-update"},
                )
                if clear.status_code >= 400:
                    log.error(f"CLEAR failed for {graph_uri}: {clear.status_code}")
                    counters["write_failed"] += 1
                    continue
                counters["updated"] += 1
            else:
                counters["imported"] += 1

            try:
                resp = client.post(
                    UPDATE_URL,
                    data=insert_query,
                    headers={"Content-Type": "application/sparql-update"},
                )
                resp.raise_for_status()
            except httpx.HTTPError as e:
                log.error(f"INSERT failed for {graph_uri}: {e}")
                counters["write_failed"] += 1
                # roll back the count we just incremented
                if existing_source is not None:
                    counters["updated"] -= 1
                else:
                    counters["imported"] -= 1

    log.info(
        "summary: "
        f"imported={counters['imported']} "
        f"updated={counters['updated']} "
        f"skipped_existing={counters['skipped_existing']} "
        f"skipped_coordinator={counters['skipped_coordinator']} "
        f"fetch_failed={counters['fetch_failed']} "
        f"invalid_json={counters['invalid_json']} "
        f"no_geo={counters['no_geo']} "
        f"no_name={counters['no_name']} "
        f"write_failed={counters['write_failed']}"
    )
    return 0 if counters["write_failed"] == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
