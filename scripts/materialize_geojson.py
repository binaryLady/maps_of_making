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


def effective_marker(endpoint_health: str, lifecycle_state: str, open_now: bool) -> str:
    """Resolve three signals into a single public map marker status.

    Duplicated from infra/link_handler/transformer.py — keep in sync.
    Lifecycle supersedes endpoint health.
    """
    if lifecycle_state == "dead":   return "dead"
    if lifecycle_state == "zombie": return "zombie"
    if lifecycle_state == "aging":  return "aging"
    if endpoint_health == "broken": return "broken"
    if open_now:                    return "open"
    return "confirmed"


SPARQL_QUERY = """PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?spaceUri ?name ?latitude ?longitude ?operationalState ?endpointHealth
       ?geolocationFidelity ?geolocationNote
       ?street ?postcode ?city ?country ?address ?website ?profileUrl ?openNow ?lastOpenChange
       ?source ?endpointUrl ?lastFetched ?errorType ?description ?logo ?contactJson
       ?lastUpdated ?subset ?nextUnlock
       (GROUP_CONCAT(DISTINCT ?specialty; separator="|") AS ?specialties)
       (COALESCE(GROUP_CONCAT(DISTINCT STR(?network); separator="|"), "") AS ?networkMemberships)
WHERE {
  {
    # VOW spaces (one space per named graph)
    GRAPH ?spaceGraph {
      ?spaceUri a mom:Space ;
        schema:name ?name ;
        schema:geo [
          schema:latitude ?latitude ;
          schema:longitude ?longitude
        ] .
      OPTIONAL { ?spaceUri mom:operationalState ?operationalState }
      OPTIONAL { ?spaceUri mom:endpointHealth ?endpointHealth }
      OPTIONAL { ?spaceUri mom:geolocationFidelity ?geolocationFidelity }
      OPTIONAL { ?spaceUri mom:geolocationNote ?geolocationNote }
      OPTIONAL { ?spaceUri schema:streetAddress ?street }
      OPTIONAL { ?spaceUri schema:postalCode ?postcode }
      OPTIONAL { ?spaceUri schema:addressLocality ?city }
      OPTIONAL { ?spaceUri schema:addressCountry ?country }
      OPTIONAL { ?spaceUri mom:address ?address }
      OPTIONAL { ?spaceUri schema:url ?website }
      OPTIONAL { ?spaceUri mom:profileUrl ?profileUrl }
      OPTIONAL { ?spaceUri schema:knowsAbout ?specialty }
      OPTIONAL { ?spaceUri mom:source ?source }
      OPTIONAL { ?spaceUri mom:endpointUrl ?endpointUrl }
      OPTIONAL { ?spaceUri mom:lastFetched ?lastFetched }
      OPTIONAL { ?spaceUri mom:errorType ?errorType }
      OPTIONAL { ?spaceUri schema:description ?description }
      OPTIONAL { ?spaceUri mom:memberOf ?network }
      OPTIONAL { ?spaceUri schema:logo ?logo }
      OPTIONAL { ?spaceUri schema:contactJson ?contactJson }
      OPTIONAL { ?spaceUri mom:lastUpdated ?lastUpdated }
      OPTIONAL { ?spaceUri mom:openNow ?openNow }
      OPTIONAL { ?spaceUri mom:lastOpenChange ?lastOpenChange }
      OPTIONAL { ?spaceUri mom:subset ?subset }
      OPTIONAL { ?spaceUri mom:nextUnlock ?nextUnlock }
    }
    FILTER (STRSTARTS(STR(?spaceGraph), "urn:mak:space/"))
  }
  UNION
  {
    # RFF mockup spaces (all in consolidated rff-health graph)
    GRAPH <urn:mak:mock/rff-health> {
      ?spaceUri a mom:Space ;
        schema:name ?name ;
        schema:geo [
          schema:latitude ?latitude ;
          schema:longitude ?longitude
        ] .
      OPTIONAL { ?spaceUri mom:operationalState ?operationalState }
      OPTIONAL { ?spaceUri mom:endpointHealth ?endpointHealth }
      OPTIONAL { ?spaceUri mom:geolocationFidelity ?geolocationFidelity }
      OPTIONAL { ?spaceUri mom:geolocationNote ?geolocationNote }
      OPTIONAL { ?spaceUri schema:streetAddress ?street }
      OPTIONAL { ?spaceUri schema:postalCode ?postcode }
      OPTIONAL { ?spaceUri schema:addressLocality ?city }
      OPTIONAL { ?spaceUri schema:addressCountry ?country }
      OPTIONAL { ?spaceUri mom:address ?address }
      OPTIONAL { ?spaceUri schema:url ?website }
      OPTIONAL { ?spaceUri mom:profileUrl ?profileUrl }
      OPTIONAL { ?spaceUri schema:knowsAbout ?specialty }
      OPTIONAL { ?spaceUri mom:source ?source }
      OPTIONAL { ?spaceUri mom:endpointUrl ?endpointUrl }
      OPTIONAL { ?spaceUri mom:lastFetched ?lastFetched }
      OPTIONAL { ?spaceUri mom:errorType ?errorType }
      OPTIONAL { ?spaceUri schema:description ?description }
      OPTIONAL { ?spaceUri mom:memberOf ?network }
      OPTIONAL { ?spaceUri schema:logo ?logo }
      OPTIONAL { ?spaceUri schema:contactJson ?contactJson }
      OPTIONAL { ?spaceUri mom:lastUpdated ?lastUpdated }
      OPTIONAL { ?spaceUri mom:openNow ?openNow }
      OPTIONAL { ?spaceUri mom:lastOpenChange ?lastOpenChange }
      OPTIONAL { ?spaceUri mom:subset ?subset }
      OPTIONAL { ?spaceUri mom:nextUnlock ?nextUnlock }
    }
  }
}
GROUP BY ?spaceUri ?name ?latitude ?longitude ?operationalState ?endpointHealth
         ?geolocationFidelity ?geolocationNote
         ?street ?postcode ?city ?country ?address ?website ?profileUrl ?openNow ?lastOpenChange
         ?source ?endpointUrl ?lastFetched ?errorType ?description ?logo ?contactJson
         ?lastUpdated ?subset ?nextUnlock
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
    lat_raw = binding.get("latitude", {}).get("value")
    lon_raw = binding.get("longitude", {}).get("value")
    if lat_raw is None or lon_raw is None:
        log.warning(f"WARNING_MISSING_COORDINATES: space {space_uri!r} has no lat/lon — skipped")
        return None
    latitude = float(lat_raw)
    longitude = float(lon_raw)

    operational_state = binding.get("operationalState", {}).get("value", "seeded")
    endpoint_health_raw = binding.get("endpointHealth", {}).get("value", "healthy")
    fidelity = binding.get("geolocationFidelity", {}).get("value", "")
    geo_note = binding.get("geolocationNote", {}).get("value", "")
    street = binding.get("street", {}).get("value", "")
    postcode = binding.get("postcode", {}).get("value", "")
    city = binding.get("city", {}).get("value", "")
    country = binding.get("country", {}).get("value", "")
    website = binding.get("website", {}).get("value", "")
    # Prefer endpointUrl over profileUrl for confirmed spaces; fall back to profileUrl for seeded
    endpoint_url = binding.get("endpointUrl", {}).get("value") or binding.get("profileUrl", {}).get("value", "")
    open_now_raw = binding.get("openNow", {}).get("value")
    open_now = open_now_raw.lower() == "true" if open_now_raw is not None else False
    last_open_change = binding.get("lastOpenChange", {}).get("value", "")
    resolved_status = effective_marker(endpoint_health_raw, operational_state, open_now)
    raw_specialties = binding.get("specialties", {}).get("value", "")
    specialties = [s for s in raw_specialties.split("|") if s] if raw_specialties else []
    raw_networks = binding.get("networkMemberships", {}).get("value", "")
    network_memberships = [n for n in raw_networks.split("|") if n] if raw_networks else []
    source = binding.get("source", {}).get("value")
    last_fetched = binding.get("lastFetched", {}).get("value", "")
    error_type = binding.get("errorType", {}).get("value", "")
    description = binding.get("description", {}).get("value", "")
    logo = binding.get("logo", {}).get("value", "")
    contact_raw = binding.get("contactJson", {}).get("value")
    try:
        contact = json.loads(contact_raw) if contact_raw else None
    except (json.JSONDecodeError, TypeError):
        contact = None
    last_updated = binding.get("lastUpdated", {}).get("value", "")
    subset = binding.get("subset", {}).get("value", "")
    next_unlock = binding.get("nextUnlock", {}).get("value", "")

    raw_address = binding.get("address", {}).get("value", "")
    if raw_address:
        address = raw_address
    else:
        address_parts = [p for p in [street, f"{postcode} {city}".strip()] if p]
        address = ", ".join(address_parts)

    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [longitude, latitude],
        },
        "properties": {
            "id": space_id,
            "uri": space_uri,
            "name": name,
            "status": resolved_status,
            "endpoint_health": endpoint_health_raw,
            "operational_state": operational_state,
            "geolocationFidelity": fidelity,
            "geolocationNote": geo_note,
            "address": address,
            "city": city,
            "country": country,
            "website": website,
            "description": description,
            "endpoint_url": endpoint_url,
            "specialties": specialties,
            "open_now": open_now,
            "last_open_change": last_open_change,
            "source": source,
            "network_memberships": network_memberships,
            "logo": logo,
            "contact": contact,
            "last_updated": last_updated,
            "subset": subset,
            "next_unlock": next_unlock,
            "opening_hours": "",
            "founded": "",
            "capacity": 0,
            "open_for_hosting": False,
            "last_fetched": last_fetched,
            "error_type": error_type,
        },
    }


def materialize_spaces() -> dict:
    """
    Materialize spaces as GeoJSON FeatureCollection from Oxigraph.

    Returns:
        RFC 7946 GeoJSON FeatureCollection
    """
    log.info(f"Querying Oxigraph at {OXIGRAPH_URL}")
    bindings = fetch_spaces_from_oxigraph()

    features = [binding_to_space(b) for b in bindings]
    features = [f for f in features if f is not None]
    log.info(f"Materialized {len(features)} spaces")

    return {
        "type": "FeatureCollection",
        "features": features,
    }


def write_output_atomically(data: dict) -> None:
    """
    Write GeoJSON FeatureCollection to file atomically (write to temp file, then rename).

    Args:
        data: RFC 7946 GeoJSON FeatureCollection
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
