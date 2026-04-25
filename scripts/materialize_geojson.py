#!/usr/bin/env python3
"""
Materialize spaces GeoJSON from Oxigraph SPARQL query.

Fetches space data from the federated Oxigraph dataset and writes a static
GeoJSON FeatureCollection for the SPA to consume. Called by the scheduler
after each ingest cycle (Epic 3) and on-demand during ingestion (Epic 2).
"""

import json
import logging
import os
import sys
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).parent.parent
OUTPUT_FILE = REPO_ROOT / "web" / "data" / "spaces.geojson"
OXIGRAPH_URL = os.getenv("OXIGRAPH_URL", "http://localhost:7878").rstrip("/")
if not OXIGRAPH_URL.endswith("/query"):
    OXIGRAPH_URL = OXIGRAPH_URL + "/query"

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger(__name__)


SPARQL_QUERY = """PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX mak: <https://nicolasdb.github.io/mapsofmaking_ontology/resource/>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?spaceUri ?name ?latitude ?longitude ?status ?lastChecked ?geolocationFidelity
WHERE {
  GRAPH ?spaceGraph {
    ?spaceUri a mom:Space ;
      schema:name ?name ;
      schema:geo [
        schema:latitude ?latitude ;
        schema:longitude ?longitude
      ] .
    OPTIONAL {
      ?spaceUri mom:geolocationFidelity ?geolocationFidelity
    }
  }
  FILTER (STRSTARTS(STR(?spaceGraph), "urn:mak:space/"))

  OPTIONAL {
    GRAPH <urn:mak:status> {
      ?spaceUri mak:healthStatus ?status ;
        mak:lastChecked ?lastChecked
    }
  }
}
ORDER BY ?spaceUri"""


def fetch_spaces_from_oxigraph() -> list[dict]:
    """
    Execute SPARQL query and return results as list of bindings.

    Returns:
        List of SPARQL result bindings

    Raises:
        httpx.HTTPError: If query execution fails
        httpx.ConnectError: If Oxigraph is unreachable
    """
    try:
        response = httpx.post(
            OXIGRAPH_URL,
            content=SPARQL_QUERY,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
            timeout=30.0,
        )
        response.raise_for_status()
        result = response.json()
        return result.get("results", {}).get("bindings", [])
    except httpx.ConnectError as e:
        log.error(f"Cannot connect to Oxigraph at {OXIGRAPH_URL}: {e}")
        raise
    except httpx.HTTPStatusError as e:
        log.error(f"SPARQL query failed: HTTP {e.response.status_code}: {e.response.text}")
        raise


def binding_to_space(binding: dict) -> dict:
    """
    Transform SPARQL binding into space object compatible with SPA.

    Wraps minimal Oxigraph data in the structure expected by web/app.js.
    Fields not yet in Oxigraph use defaults (will be populated by Epic 2 ingestion).

    Args:
        binding: SPARQL result binding

    Returns:
        Space object with all fields app.js expects
    """
    # Extract values from SPARQL bindings
    space_uri = binding.get("spaceUri", {}).get("value", "")
    # Use last component of URI as id (format: urn:mak:space/{id})
    space_id = space_uri.split("/")[-1] if "/" in space_uri else space_uri

    name = binding.get("name", {}).get("value", "")
    latitude = float(binding.get("latitude", {}).get("value", 0))
    longitude = float(binding.get("longitude", {}).get("value", 0))

    # Status defaults to 'seeded' if not present
    status = binding.get("status", {}).get("value", "mak:seeded")
    if status.startswith("mak:"):
        status = status[4:]  # Strip 'mak:' prefix

    # last_fetched (mak:lastChecked) — ISO 8601 timestamp
    last_fetched = binding.get("lastChecked", {}).get("value", "")

    # geolocationFidelity from mom:geolocationFidelity
    fidelity = binding.get("geolocationFidelity", {}).get("value", "")
    # Strip quotes if present (SPARQL string literal)
    if fidelity.startswith('"') and fidelity.endswith('"'):
        fidelity = fidelity[1:-1]

    # Return space object compatible with app.js
    # Fields from Oxigraph are populated; others default to empty/false
    return {
        "id": space_id,
        "name": name,
        "coordinates": {"lat": latitude, "lon": longitude},
        "status": status,
        "last_fetched": last_fetched,
        "geolocationFidelity": fidelity,
        # Defaults for fields not yet in Oxigraph (populated by Epic 2 ingestion)
        "address": "",
        "city": "",
        "country": "",
        "opening_hours": "",
        "founded": "",
        "capacity": 0,
        "contact": "",
        "website": "",
        "specialties": [],
        "network_memberships": [],
        "open_for_hosting": False,
        "open_now": False,
        "endpoint_url": "",
    }


def materialize_spaces() -> dict:
    """
    Materialize spaces list from Oxigraph.

    Returns:
        Object with 'spaces' array, compatible with app.js loadData()
    """
    log.info(f"Querying Oxigraph at {OXIGRAPH_URL}")
    bindings = fetch_spaces_from_oxigraph()

    spaces = [binding_to_space(b) for b in bindings]
    log.info(f"Materialized {len(spaces)} spaces")

    return {
        "spaces": spaces,
    }


def write_output_atomically(data: dict) -> None:
    """
    Write spaces data to file atomically (write to temp file, then rename).

    Args:
        data: Data structure with 'spaces' array
    """
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file first
    temp_file = OUTPUT_FILE.with_suffix(".geojson.tmp")
    with open(temp_file, "w") as f:
        json.dump(data, f, separators=(",", ":"))

    # Atomic rename
    temp_file.replace(OUTPUT_FILE)
    log.info(f"Wrote {OUTPUT_FILE}")


def main() -> int:
    """Main entry point."""
    try:
        spaces_data = materialize_spaces()
        write_output_atomically(spaces_data)
        return 0
    except Exception as e:
        log.error(f"Materialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
