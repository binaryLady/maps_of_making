#!/usr/bin/env python3

from pathlib import Path
import argparse
import hashlib
import httpx
import json
import logging
import os
import sys

REPO_ROOT = Path(__file__).parent.parent
VOW_FILE = REPO_ROOT / "web" / "data" / "moms_seed.json"
RFF_FILE = REPO_ROOT / "web" / "data" / "rff_mockup.json"
OXIGRAPH_ENDPOINT = os.getenv("OXIGRAPH_ENDPOINT", "http://localhost:7878")
UPDATE_URL = f"{OXIGRAPH_ENDPOINT}/update"
ASK_URL = f"{OXIGRAPH_ENDPOINT}/query"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


def space_id(entry: dict) -> str:
    """Stable ID from space name + locality, URL-safe slug."""
    name = entry.get("schema:name", "")
    city = entry.get("schema:address", {}).get("schema:addressLocality", "")
    raw = f"{name}|{city}".lower().strip()
    return hashlib.sha256(raw.encode()).hexdigest()[:12]


def sparql_str(val: str) -> str:
    """Escape and quote string literals for SPARQL."""
    if val is None:
        return '""'
    escaped = str(val).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def graph_exists(client: httpx.Client, graph_uri: str) -> bool:
    """Check if named graph has any triples."""
    query = f"ASK {{ GRAPH <{graph_uri}> {{ ?s ?p ?o }} }}"
    try:
        resp = client.post(
            ASK_URL,
            data=query,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
        )
        resp.raise_for_status()
        return resp.json().get("boolean", False)
    except httpx.HTTPError as e:
        log.error(f"Error checking graph existence: {e}")
        raise


def load_vow_data() -> list:
    """Load VOW seed data."""
    with open(VOW_FILE, "r") as f:
        return json.load(f)


def load_rff_data() -> list:
    """Load RFF mockup data."""
    with open(RFF_FILE, "r") as f:
        return json.load(f)


def build_vow_insert(entry: dict) -> tuple[str, str]:
    """Build SPARQL INSERT statement for VOW entry and return (graph_uri, insert_query)."""
    sid = space_id(entry)
    graph_uri = f"urn:mak:space/{sid}"

    name = entry.get("schema:name", "")
    address = entry.get("schema:address", {})
    locality = address.get("schema:addressLocality", "")
    country = address.get("schema:addressCountry", "")
    geo = entry.get("schema:geo", {})
    latitude = geo.get("schema:latitude")
    longitude = geo.get("schema:longitude")
    url = entry.get("schema:url")
    profile_url = entry.get("mom:profileUrl")
    knows_about = entry.get("schema:knowsAbout", [])
    source = entry.get("mom:source", "mak:scraped-vow")
    freshness = entry.get("mom:freshnessStatus", "mak:seeded")
    fidelity = entry.get("mom:geolocationFidelity", "")

    subject = f"<urn:mak:space/{sid}>"
    triples = f"{subject} a mom:MakerSpace"

    if name:
        triples += f" ;\n    schema:name {sparql_str(name)}@en"

    if locality:
        triples += f" ;\n    schema:addressLocality {sparql_str(locality)}"

    if country:
        triples += f" ;\n    schema:addressCountry {sparql_str(country)}"

    if latitude is not None and longitude is not None:
        triples += f" ;\n    schema:geo [\n      schema:latitude {latitude} ;\n      schema:longitude {longitude}\n    ]"

    if url:
        triples += f" ;\n    schema:url <{url}>"

    if profile_url:
        triples += f" ;\n    mom:profileUrl <{profile_url}>"

    if knows_about:
        for item in knows_about:
            triples += f" ;\n    schema:knowsAbout {sparql_str(item)}"

    triples += f" ;\n    mom:source {source}"
    triples += f" ;\n    mom:freshnessStatus {freshness}"

    if fidelity:
        triples += f" ;\n    mom:geolocationFidelity {sparql_str(fidelity)}"

    triples += " ."

    insert_query = f"""PREFIX schema: <https://schema.org/>
PREFIX mom: <https://mapsofmaking.eu/ns#>
PREFIX mak: <https://mapsofmaking.eu/resource/>
INSERT DATA {{
  GRAPH <{graph_uri}> {{
    {triples}
  }}
}}"""

    return graph_uri, insert_query


def build_rff_insert(entries: list) -> tuple[str, str]:
    """Build SPARQL INSERT statement for all RFF entries."""
    graph_uri = "urn:mak:mock/rff-health"
    triples_list = []

    for entry in entries:
        subject = f"<urn:mak:space/{entry.get('@id', 'rff-unknown')}>"
        entry_triples = f"{subject} a mom:MakerSpace"

        if "schema:name" in entry:
            entry_triples += f" ;\n      schema:name {sparql_str(entry['schema:name'])}@en"

        if "schema:address" in entry:
            addr = entry["schema:address"]
            if isinstance(addr, dict):
                if "schema:addressLocality" in addr:
                    entry_triples += (
                        f" ;\n      schema:addressLocality {sparql_str(addr['schema:addressLocality'])}"
                    )
                if "schema:addressCountry" in addr:
                    entry_triples += (
                        f" ;\n      schema:addressCountry {sparql_str(addr['schema:addressCountry'])}"
                    )

        if "schema:geo" in entry:
            geo = entry["schema:geo"]
            if isinstance(geo, dict):
                lat = geo.get("schema:latitude")
                lon = geo.get("schema:longitude")
                if lat is not None and lon is not None:
                    entry_triples += f" ;\n      schema:geo [\n        schema:latitude {lat} ;\n        schema:longitude {lon}\n      ]"

        if "schema:url" in entry:
            entry_triples += f" ;\n      schema:url <{entry['schema:url']}>"

        if "mom:profileUrl" in entry:
            entry_triples += f" ;\n      mom:profileUrl <{entry['mom:profileUrl']}>"

        if "schema:knowsAbout" in entry:
            for item in entry.get("schema:knowsAbout", []):
                entry_triples += f" ;\n      schema:knowsAbout {sparql_str(item)}"

        entry_triples += f" ;\n      mom:source {entry.get('mom:source', 'mak:rff-mockup')}"
        entry_triples += f" ;\n      mom:freshnessStatus {entry.get('mom:freshnessStatus', 'mak:seeded')}"

        if "mom:healthState" in entry:
            entry_triples += f" ;\n      mom:healthState {entry['mom:healthState']}"

        if "mom:lastFetched" in entry:
            entry_triples += f" ;\n      mom:lastFetched {sparql_str(entry['mom:lastFetched'])}"

        if "mom:lastFetchError" in entry:
            entry_triples += f" ;\n      mom:lastFetchError {sparql_str(entry['mom:lastFetchError'])}"

        if "mom:geolocationFidelity" in entry:
            entry_triples += f" ;\n      mom:geolocationFidelity {sparql_str(entry['mom:geolocationFidelity'])}"

        entry_triples += " ."
        triples_list.append(entry_triples)

    triples = "\n    ".join(triples_list)
    insert_query = f"""PREFIX schema: <https://schema.org/>
PREFIX mom: <https://mapsofmaking.eu/ns#>
PREFIX mak: <https://mapsofmaking.eu/resource/>
INSERT DATA {{
  GRAPH <{graph_uri}> {{
    {triples}
  }}
}}"""

    return graph_uri, insert_query


def insert_vow_data(client: httpx.Client) -> tuple[int, int, int, int]:
    """Load VOW data and insert into Oxigraph. Returns (loaded, skipped_existing, corrupt, failed)."""
    try:
        data = load_vow_data()
    except FileNotFoundError:
        log.error(f"VOW file not found: {VOW_FILE}")
        raise

    loaded = 0
    skipped = 0
    corrupt = 0
    failed = 0

    for entry in data:
        try:
            # Story 0.1 guarantees all entries have schema:geo — this should never fire.
            # If it does, it means data pipeline contract was broken upstream.
            if "schema:geo" not in entry or not entry["schema:geo"]:
                log.warning(
                    f"UNEXPECTED: VOW entry missing schema:geo — Story 0.1 contract violated. "
                    f"Entry: {entry.get('schema:name', 'unknown')} "
                    f"(fidelity: {entry.get('mom:geolocationFidelity', 'absent')}). "
                    f"Entry NOT loaded — investigate upstream pipeline."
                )
                corrupt += 1
                continue

            graph_uri, insert_query = build_vow_insert(entry)

            # Check idempotency
            if graph_exists(client, graph_uri):
                log.debug(f"Graph already exists, skipping: {graph_uri}")
                skipped += 1
                continue

            # Insert
            resp = client.post(
                UPDATE_URL,
                data=insert_query,
                headers={"Content-Type": "application/sparql-update"},
            )
            resp.raise_for_status()
            log.debug(f"Loaded VOW space: {graph_uri}")
            loaded += 1

        except Exception as e:
            log.error(f"Error loading VOW entry: {e}")
            failed += 1

    return loaded, skipped, corrupt, failed


def insert_rff_data(client: httpx.Client, force: bool = False) -> tuple[int, int]:
    """Load RFF data into shared graph. Returns (loaded, skipped)."""
    try:
        data = load_rff_data()
    except FileNotFoundError:
        log.error(f"RFF file not found: {RFF_FILE}")
        raise

    graph_uri = "urn:mak:mock/rff-health"

    # Check if graph exists
    if graph_exists(client, graph_uri):
        if not force:
            log.info("RFF graph already loaded — use --force to reload")
            return 0, len(data)
        else:
            log.info("RFF graph exists but --force given, clearing and reloading...")
            clear_query = f"CLEAR GRAPH <{graph_uri}>"
            resp = client.post(
                UPDATE_URL,
                data=clear_query,
                headers={"Content-Type": "application/sparql-update"},
            )
            resp.raise_for_status()

    try:
        _, insert_query = build_rff_insert(data)
        resp = client.post(
            UPDATE_URL,
            data=insert_query,
            headers={"Content-Type": "application/sparql-update"},
        )
        resp.raise_for_status()
        log.debug(f"Loaded RFF graph: {graph_uri}")
        return len(data), 0
    except Exception as e:
        log.error(f"Error loading RFF data: {e}")
        raise


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Load VOW and RFF seed datasets into Oxigraph"
    )
    parser.add_argument(
        "--force", action="store_true", help="Reload RFF graph even if already loaded"
    )
    args = parser.parse_args()

    try:
        with httpx.Client() as client:
            log.info(f"Connecting to Oxigraph at {OXIGRAPH_ENDPOINT}...")

            # Insert VOW data
            vow_loaded, vow_skipped, vow_corrupt, vow_failed = insert_vow_data(client)

            # Insert RFF data
            rff_loaded, rff_skipped = insert_rff_data(client, args.force)

            # Summary
            summary = (
                f"{vow_loaded} VOW spaces loaded, {vow_skipped} skipped (already loaded), "
                f"{rff_loaded} RFF mockup spaces loaded, {rff_skipped} RFF skipped (already loaded)"
            )
            log.info(summary)

            if vow_corrupt > 0:
                log.warning(
                    f"DATA INTEGRITY: {vow_corrupt} VOW entries had no schema:geo "
                    f"(Story 0.1 contract violation) — investigate upstream pipeline"
                )

            if vow_failed > 0:
                log.warning(f"{vow_failed} VOW entries failed to load due to errors")
                return 1

            return 0

    except Exception as e:
        log.error(f"Fatal error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
