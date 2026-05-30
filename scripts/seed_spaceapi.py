#!/usr/bin/env python3
"""Seed local Oxigraph from a SpaceAPI endpoint list.

Default source: https://directory.spaceapi.io/ (a name → endpoint URL map).
Override with --list <url-or-path> to seed from any other list. Two shapes are
accepted:
  * {name: url}                          — SpaceAPI directory shape
  * [{"name": ..., "url": ..., "network": ...}, ...]   — extended array shape

Each entry becomes a seeded mom:Space graph tagged with mom:memberOf
<urn:mak:network/{network}> (renders as a filter chip). Per-entry `network`
overrides the --network CLI default (default: "spaceapi"). Heartbeat picks the
spaces up on its next cycle to populate Zone 3 / track liveness.

PII rule: only public fields (name, geo, website, endpoint URL) are stored.
contact.email / phone / etc. are discarded — same policy as Story 3.2b.

Coordinator-registered graphs (mom:source = "self-registered") are protected
from overwrite even with --force, mirroring seed_import.py behaviour.
"""

from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any

import httpx

sys.path.insert(0, str(Path(__file__).parent))
from spaceapi_extract import escape_literal, extract_core, triples_for

OXIGRAPH_ENDPOINT = os.getenv("OXIGRAPH_ENDPOINT", "http://localhost:7878")
UPDATE_URL = f"{OXIGRAPH_ENDPOINT}/update"
QUERY_URL = f"{OXIGRAPH_ENDPOINT}/query"

DIRECTORY_URL = "https://directory.spaceapi.io/"
DEFAULT_NETWORK = "spaceapi"
MOM_NS = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"


def network_uri(slug: str) -> str:
    return f"urn:mak:network/{slug}"


def source_tag(slug: str) -> str:
    return f"{slug}-directory"

FETCH_CONCURRENCY = 20
PER_ENDPOINT_TIMEOUT = 10.0

# Match the map maxBounds from app.js: [[-25, 34], [45, 72]]
BBOX_WEST, BBOX_SOUTH, BBOX_EAST, BBOX_NORTH = -25, 34, 45, 72

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("seed_spaceapi")


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


def build_insert(name: str, endpoint_url: str, payload: dict, network: str) -> tuple[str, str]:
    """Build a minimal seed INSERT for a SpaceAPI endpoint.

    Uses extract_core(payload) only — seed time is a minimal anchor; contact,
    specialties, and mom address fields are intentionally excluded (the heartbeat
    re-extracts payload fields on the first confirmed fetch via write_payload_fields).
    """
    sid = space_id(name, endpoint_url)
    graph_uri = f"urn:mak:space/{sid}"
    subject_uri = graph_uri

    # Seed envelope — identity + provenance
    envelope = [
        f"<{subject_uri}> a <{MOM_NS}Space> .",
        f"<{subject_uri}> <{MOM_NS}endpointUrl> <{endpoint_url}> .",
        f"<{subject_uri}> <{MOM_NS}source> {escape_literal(source_tag(network))} .",
        f"<{subject_uri}> <{MOM_NS}memberOf> <{network_uri(network)}> .",
    ]

    # Payload fields — core only; no contact/specialties at seed time
    fields = extract_core(payload)
    fields["schema:name"] = name  # use validated/chosen name
    for skip in ("schema:contactJson", "schema:knowsAbout", "mom:memberOf"):
        fields.pop(skip, None)

    payload_triples = triples_for(subject_uri, fields)

    all_triples = envelope + payload_triples
    triples_str = "\n    ".join(all_triples)
    insert_query = f"INSERT DATA {{\n  GRAPH <{graph_uri}> {{\n    {triples_str}\n  }}\n}}"
    return graph_uri, insert_query


async def fetch_endpoint(
    name: str,
    endpoint_url: str,
    network: str,
    client: httpx.AsyncClient,
    sem: asyncio.Semaphore,
) -> tuple[str, str, str, dict[str, Any] | None, str | None]:
    """Return (name, endpoint_url, network, payload_or_none, error_kind_or_none)."""
    async with sem:
        try:
            resp = await client.get(endpoint_url, timeout=PER_ENDPOINT_TIMEOUT, follow_redirects=True)
            resp.raise_for_status()
            try:
                payload = resp.json()
            except (json.JSONDecodeError, ValueError):
                return name, endpoint_url, network, None, "invalid_json"
            if not isinstance(payload, dict):
                return name, endpoint_url, network, None, "invalid_json"
            return name, endpoint_url, network, payload, None
        except httpx.HTTPError:
            return name, endpoint_url, network, None, "fetch_failed"
        except Exception:
            return name, endpoint_url, network, None, "fetch_failed"


async def fetch_all(
    entries: list[tuple[str, str, str]],
) -> list[tuple[str, str, str, dict[str, Any] | None, str | None]]:
    sem = asyncio.Semaphore(FETCH_CONCURRENCY)
    async with httpx.AsyncClient(headers={"User-Agent": "MapsOfMaking-seed/1.0"}) as client:
        tasks = [fetch_endpoint(name, url, net, client, sem) for name, url, net in entries]
        return await asyncio.gather(*tasks)


def _normalize_list(data: Any, default_network: str) -> list[tuple[str, str, str]]:
    """Accept either {name: url} or [{name, url, network?}, ...] and return
    a list of (name, url, network) tuples."""
    entries: list[tuple[str, str, str]] = []
    if isinstance(data, dict):
        for k, v in data.items():
            if isinstance(k, str) and isinstance(v, str):
                entries.append((k, v, default_network))
        return entries
    if isinstance(data, list):
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                log.warning(f"entry {i}: not an object, skipping")
                continue
            name = item.get("name")
            url = item.get("url")
            net = item.get("network") or default_network
            if not (isinstance(name, str) and isinstance(url, str) and isinstance(net, str)):
                log.warning(f"entry {i}: missing name/url, skipping")
                continue
            entries.append((name, url, net))
        return entries
    raise RuntimeError(f"Unexpected list format: {type(data).__name__}")


def load_list(source: str, default_network: str) -> list[tuple[str, str, str]]:
    """Load a list from an HTTP(S) URL or local file path."""
    if source.startswith(("http://", "https://")):
        log.info(f"Fetching list: {source}")
        resp = httpx.get(source, timeout=20.0)
        resp.raise_for_status()
        data = resp.json()
    else:
        path = Path(source)
        log.info(f"Loading list: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
    return _normalize_list(data, default_network)


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed Oxigraph from a SpaceAPI endpoint list")
    parser.add_argument(
        "--list",
        dest="list_source",
        default=DIRECTORY_URL,
        help=f"List source: URL or local path (default: {DIRECTORY_URL})",
    )
    parser.add_argument(
        "--network",
        default=DEFAULT_NETWORK,
        help=f"Network slug for filter chip + source tag (default: {DEFAULT_NETWORK})",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing seeded graphs (still skips coordinator-registered)",
    )
    args = parser.parse_args()

    try:
        entries = load_list(args.list_source, args.network)
    except Exception as e:
        log.error(f"List load failed: {e}")
        return 1

    log.info(f"List has {len(entries)} entries — fetching with concurrency={FETCH_CONCURRENCY}")
    results = asyncio.run(fetch_all(entries))

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
        for name, endpoint_url, network, payload, err in results:
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

            graph_uri, insert_query = build_insert(chosen_name, endpoint_url, payload, network)

            try:
                existing_source = graph_source(client, graph_uri)
            except httpx.HTTPError as e:
                log.error(f"ASK failed for {graph_uri}: {e}")
                counters["write_failed"] += 1
                continue

            if existing_source == "self-registered":
                counters["skipped_coordinator"] += 1
                continue

            # Cross-network protect: never overwrite a graph whose source tag was
            # written by a different seeder (e.g. seed_bundle.py / scraped-vow).
            current_tag = source_tag(args.network)
            if existing_source is not None and existing_source != current_tag:
                counters["skipped_existing"] += 1
                continue

            if existing_source == current_tag:
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
