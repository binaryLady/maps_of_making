import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Maps of Making Link Handler")

_TOKEN_RE = re.compile(r'^[A-Za-z0-9_\-]{8,255}$')
_ALLOWED_SCHEMES = {"http", "https"}

OXIGRAPH_ENDPOINT = os.getenv("OXIGRAPH_ENDPOINT", "http://oxigraph:7878")
GEOJSON_OUTPUT = os.getenv("GEOJSON_OUTPUT", "/app/web_data/spaces.geojson")

MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"
SCHEMA = "https://schema.org/"


def _sparql_str(s: str) -> str:
    """Escape a string for use in a SPARQL double-quoted literal."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r")


def _sparql_iri(url: str) -> Optional[str]:
    """Validate and return a safe IRI string, or None if invalid."""
    from urllib.parse import urlparse
    parsed = urlparse(url)
    if parsed.scheme not in _ALLOWED_SCHEMES:
        return None
    # IRIs must not contain unencoded < or >
    if "<" in url or ">" in url or " " in url:
        return None
    return url

# Same SELECT query as scripts/materialize_geojson.py — kept in sync intentionally
_SPARQL_SELECT = """PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?spaceUri ?name ?latitude ?longitude ?status ?geolocationFidelity ?geolocationNote
       ?street ?postcode ?city ?country ?website ?profileUrl ?openNow ?source
       ?openingHours ?description
       (GROUP_CONCAT(DISTINCT ?specialty; separator="|") AS ?specialties)
WHERE {
  {
    GRAPH ?spaceGraph {
      ?spaceUri a mom:Space ;
        schema:name ?name ;
        schema:geo [
          schema:latitude ?latitude ;
          schema:longitude ?longitude
        ] .
      OPTIONAL { ?spaceUri mom:operationalState ?status }
      OPTIONAL { ?spaceUri mom:geolocationFidelity ?geolocationFidelity }
      OPTIONAL { ?spaceUri mom:geolocationNote ?geolocationNote }
      OPTIONAL { ?spaceUri schema:streetAddress ?street }
      OPTIONAL { ?spaceUri schema:postalCode ?postcode }
      OPTIONAL { ?spaceUri schema:addressLocality ?city }
      OPTIONAL { ?spaceUri schema:addressCountry ?country }
      OPTIONAL { ?spaceUri schema:url ?website }
      OPTIONAL { ?spaceUri mom:profileUrl ?profileUrl }
      OPTIONAL { ?spaceUri schema:knowsAbout ?specialty }
      OPTIONAL { ?spaceUri mom:source ?source }
      OPTIONAL { ?spaceUri schema:openingHours ?openingHours }
      OPTIONAL { ?spaceUri schema:description ?description }
    }
    FILTER (STRSTARTS(STR(?spaceGraph), "urn:mak:space/"))
  }
  UNION
  {
    GRAPH <urn:mak:mock/rff-health> {
      ?spaceUri a mom:Space ;
        schema:name ?name ;
        schema:geo [
          schema:latitude ?latitude ;
          schema:longitude ?longitude
        ] .
      OPTIONAL { ?spaceUri mom:operationalState ?status }
      OPTIONAL { ?spaceUri mom:geolocationFidelity ?geolocationFidelity }
      OPTIONAL { ?spaceUri mom:geolocationNote ?geolocationNote }
      OPTIONAL { ?spaceUri schema:streetAddress ?street }
      OPTIONAL { ?spaceUri schema:postalCode ?postcode }
      OPTIONAL { ?spaceUri schema:addressLocality ?city }
      OPTIONAL { ?spaceUri schema:addressCountry ?country }
      OPTIONAL { ?spaceUri schema:url ?website }
      OPTIONAL { ?spaceUri mom:profileUrl ?profileUrl }
      OPTIONAL { ?spaceUri schema:knowsAbout ?specialty }
      OPTIONAL { ?spaceUri mom:source ?source }
      OPTIONAL { ?spaceUri schema:openingHours ?openingHours }
      OPTIONAL { ?spaceUri schema:description ?description }
    }
  }
  OPTIONAL {
    GRAPH <urn:mak:presence> {
      ?spaceUri mom:openNow ?openNow .
    }
  }
}
GROUP BY ?spaceUri ?name ?latitude ?longitude ?status ?geolocationFidelity ?geolocationNote
         ?street ?postcode ?city ?country ?website ?profileUrl ?openNow ?source
         ?openingHours ?description
ORDER BY ?spaceUri"""

# Only flag fields that are unambiguously personal data (not business contact info).
# schema:email and schema:telephone on a LocalBusiness are public organizational contacts — not PII.
# schema:Person is a class value (appears under @type), not a property key — excluded.
_PII_FIELDS = {"foaf:mbox"}


class UrlRequest(BaseModel):
    url: str
    space_id: Optional[str] = None


class SpaceAPIGeo(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    latitude: Optional[float] = Field(None, alias="schema:latitude")
    longitude: Optional[float] = Field(None, alias="schema:longitude")


class SpaceAPILocation(BaseModel):
    """SpaceAPI v14 flat `location` object: { lat, lon, address }."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    lat: Optional[float] = None
    lon: Optional[float] = None
    address: Optional[str] = None


class SpaceAPISchema(BaseModel):
    """Accepts both mom JSON-LD (`schema:name`, `schema:geo.schema:latitude`)
    and SpaceAPI v14 flat shape (`space`, `location.lat/lon`). One document,
    two validators — see web/test-fixtures/SKILL.md."""
    model_config = ConfigDict(populate_by_name=True, extra="allow")

    name: Optional[str] = Field(None, alias="schema:name")
    plain_name: Optional[str] = Field(None, alias="name")
    space: Optional[str] = None  # SpaceAPI v14 flat key for name
    geo: Optional[SpaceAPIGeo] = Field(None, alias="schema:geo")
    location: Optional[SpaceAPILocation] = None  # SpaceAPI v14 flat key for coords
    url: Optional[str] = Field(None, alias="schema:url")
    plain_url: Optional[str] = Field(None, alias="url")  # SpaceAPI v14 flat key
    opening_hours: Optional[str] = Field(None, alias="schema:openingHours")
    plain_opening_hours: Optional[str] = Field(None, alias="opening_hours")  # SpaceAPI v14 flat key
    description: Optional[str] = Field(None, alias="schema:description")
    logo: Optional[str] = None
    api_compatibility: Optional[List[str]] = None
    contact: Optional[dict] = None

    @property
    def resolved_name(self) -> Optional[str]:
        return self.name or self.plain_name or self.space

    @property
    def resolved_url(self) -> Optional[str]:
        return self.url or self.plain_url

    @property
    def resolved_opening_hours(self) -> Optional[str]:
        return self.opening_hours or self.plain_opening_hours

    @property
    def resolved_lat(self) -> Optional[float]:
        if self.geo and self.geo.latitude is not None:
            return self.geo.latitude
        if self.location and self.location.lat is not None:
            return self.location.lat
        return None

    @property
    def resolved_lon(self) -> Optional[float]:
        if self.geo and self.geo.longitude is not None:
            return self.geo.longitude
        if self.location and self.location.lon is not None:
            return self.location.lon
        return None


def _extract_name(data: dict) -> Optional[str]:
    return data.get("schema:name") or data.get("name")


def _extract_coords(data: dict) -> tuple[Optional[float], Optional[float]]:
    # Normalise schema:geo — may be a dict or a single-element list
    raw_geo = data.get("schema:geo")
    if isinstance(raw_geo, list):
        raw_geo = raw_geo[0] if raw_geo else {}
    geo = raw_geo if isinstance(raw_geo, dict) else {}

    # Use `is not None` throughout — lat/lon of 0 is valid (equator / prime meridian)
    lat = geo.get("schema:latitude") if geo.get("schema:latitude") is not None else geo.get("latitude")
    lon = geo.get("schema:longitude") if geo.get("schema:longitude") is not None else geo.get("longitude")
    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon)
        except (TypeError, ValueError):
            pass

    # Flat-key fallback (less common encodings)
    lat = data.get("schema:latitude")
    lon = data.get("schema:longitude")
    if lat is None and lon is None:
        plain_geo = data.get("geo")
        if isinstance(plain_geo, dict):
            lat = plain_geo.get("lat")
            lon = plain_geo.get("lon")
    if lat is not None and lon is not None:
        try:
            return float(lat), float(lon)
        except (TypeError, ValueError):
            pass
    return None, None


def _scan_pii(data: dict) -> list[str]:
    return [f for f in _PII_FIELDS if f in data]


def classify_subset(schema: SpaceAPISchema) -> dict:
    """Classify the subset level reached by the endpoint data."""
    has_required = bool(schema.resolved_name and schema.resolved_lat is not None and schema.resolved_lon is not None)
    has_card = has_required and bool(schema.resolved_url and schema.resolved_opening_hours)
    has_spaceapi = has_card and bool(schema.api_compatibility and schema.logo and schema.contact)

    if has_spaceapi:
        return {
            "subset": "spaceapi:compatible",
            "subset_score": 3,
            "missing_card_fields": [],
            "unlock_message": "Full SpaceAPI compatibility — interoperable with mapall.space and other SpaceAPI maps.",
            "next_subset": None,
            "next_unlock": None,
        }
    elif has_card:
        missing = []
        if not schema.api_compatibility:
            missing.append("api_compatibility")
        if not schema.logo:
            missing.append("logo")
        if not schema.contact:
            missing.append("contact")
        return {
            "subset": "mom:card",
            "subset_score": 2,
            "missing_card_fields": missing,
            "unlock_message": "Full detail card unlocked.",
            "next_subset": "spaceapi:compatible",
            "next_unlock": "SpaceAPI compatibility is optional and requires several additional fields (api_compatibility, logo, contact, state, and more) — your card is already fully functional.",
        }
    elif has_required:
        missing = []
        if not schema.resolved_url:
            missing.append("schema:url")
        if not schema.resolved_opening_hours:
            missing.append("schema:openingHours")
        return {
            "subset": "mom:required",
            "subset_score": 1,
            "missing_card_fields": missing,
            "unlock_message": "Pin on map unlocked. Add website and opening hours for the full detail card.",
            "next_subset": "mom:card",
            "next_unlock": "Full detail card display",
        }
    else:
        return {
            "subset": "none",
            "subset_score": 0,
            "missing_card_fields": [],
            "unlock_message": None,
            "next_subset": None,
            "next_unlock": None,
        }


_EMPTY_RESULT = {
    "reachable": False,
    "status_code": None,
    "json_ld_valid": False,
    "name_found": None,
    "coords_found": False,
    "lat": None,
    "lon": None,
    "pii_warning": False,
    "pii_fields": [],
}


async def _fetch_and_validate(url: str) -> dict:
    """Fetch URL and return validation result dict."""
    from urllib.parse import urlparse
    if urlparse(url).scheme not in _ALLOWED_SCHEMES:
        return {**_EMPTY_RESULT, "error": f"URL scheme not allowed; use http or https"}

    try:
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=False) as client:
            resp = await client.get(url)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        return {**_EMPTY_RESULT, "error": str(e)}
    except httpx.HTTPError as e:
        return {**_EMPTY_RESULT, "error": str(e)}

    if resp.status_code != 200:
        return {
            **_EMPTY_RESULT,
            "status_code": resp.status_code,
            "error": f"HTTP {resp.status_code}",
        }

    try:
        data = resp.json()
    except Exception:
        return {
            "reachable": True,
            "status_code": resp.status_code,
            "json_ld_valid": False,
            "error": "Response is not valid JSON",
        }

    # Validate through Pydantic schema
    try:
        schema = SpaceAPISchema.model_validate(data)
    except Exception as e:
        logger.warning("Pydantic validation failed: %s", e)
        schema = SpaceAPISchema()

    name = schema.resolved_name
    lat = schema.resolved_lat
    lon = schema.resolved_lon
    pii_found = _scan_pii(data)
    subset_info = classify_subset(schema)

    result = {
        "reachable": True,
        "status_code": resp.status_code,
        "json_ld_valid": bool(name),
        "name_found": name,
        "coords_found": lat is not None and lon is not None,
        "lat": lat,
        "lon": lon,
        "pii_warning": bool(pii_found),
        "pii_fields": pii_found,
        "subset": subset_info["subset"],
        "subset_score": subset_info["subset_score"],
        "missing_card_fields": subset_info["missing_card_fields"],
        "unlock_message": subset_info["unlock_message"],
        "next_subset": subset_info["next_subset"],
        "next_unlock": subset_info["next_unlock"],
        "_data": data,  # internal — stripped before response
    }
    if not name:
        result["error"] = "Missing schema:name or name field"
    elif lat is None or lon is None:
        result["coords_error"] = "Missing coordinates — add schema:geo with schema:latitude and schema:longitude"
    return result


def _slug(name: str) -> str:
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', name.lower())).strip('-')


def _build_sparql_update(graph_uri: str, space_uri: str, name: str, lat: float, lon: float,
                          endpoint_url: str, data: dict) -> str:
    now = datetime.now(timezone.utc).isoformat()
    triples = [
        f"  <{space_uri}> a <{MOM}Space> .",
        f'  <{space_uri}> <{SCHEMA}name> "{_sparql_str(name)}" .',
        f"  <{space_uri}> <{SCHEMA}geo> [ <{SCHEMA}latitude> {lat} ; <{SCHEMA}longitude> {lon} ] .",
        f'  <{space_uri}> <{MOM}operationalState> "confirmed" .',
        f'  <{space_uri}> <{MOM}endpointUrl> <{endpoint_url}> .',
        f'  <{space_uri}> <{MOM}lastFetched> "{now}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .',
        f'  <{space_uri}> <{MOM}source> "self-registered" .',
    ]

    # Optional fields — skip PII; validate IRIs before inserting
    addr_value = data.get("schema:address")
    if addr_value is None:
        loc = data.get("location")
        if isinstance(loc, dict):
            addr_value = loc.get("address")
    if isinstance(addr_value, dict):
        # Structured PostalAddress: write each component as the schema.org property
        for json_key, schema_prop in (
            ("schema:streetAddress", "streetAddress"),
            ("schema:postalCode", "postalCode"),
            ("schema:addressLocality", "addressLocality"),
            ("schema:addressCountry", "addressCountry"),
        ):
            v = addr_value.get(json_key)
            if v:
                triples.append(f'  <{space_uri}> <{SCHEMA}{schema_prop}> "{_sparql_str(str(v))}" .')
    elif addr_value:
        # Flat address string (SpaceAPI v14 style): keep on mom:address
        triples.append(f'  <{space_uri}> <{MOM}address> "{_sparql_str(str(addr_value))}" .')
    website = data.get("schema:url") or data.get("url")
    safe_website = _sparql_iri(str(website)) if website else None
    if safe_website:
        triples.append(f"  <{space_uri}> <{SCHEMA}url> <{safe_website}> .")
    desc = data.get("schema:description")
    if desc:
        triples.append(f'  <{space_uri}> <{SCHEMA}description> "{_sparql_str(str(desc))}" .')
    hours = data.get("schema:openingHours") or data.get("opening_hours")
    if hours:
        triples.append(f'  <{space_uri}> <{SCHEMA}openingHours> "{_sparql_str(str(hours))}" .')

    # Specialties (schema:knowsAbout) — JSON-LD array OR SpaceAPI flat "knowsAbout"
    specialties = data.get("schema:knowsAbout") or data.get("knowsAbout") or []
    if isinstance(specialties, str):
        specialties = [specialties]
    for sp in specialties:
        if sp:
            triples.append(f'  <{space_uri}> <{SCHEMA}knowsAbout> "{_sparql_str(str(sp))}" .')

    triples_str = "\n".join(triples)
    return f"""DROP SILENT GRAPH <{graph_uri}> ;
INSERT DATA {{
  GRAPH <{graph_uri}> {{
{triples_str}
  }}
}}"""


def _binding_to_feature(b: dict) -> Optional[dict]:
    space_uri = b.get("spaceUri", {}).get("value", "")
    space_id = space_uri.split("/")[-1] if "/" in space_uri else space_uri
    name = b.get("name", {}).get("value", "")
    lat_raw = b.get("latitude", {}).get("value")
    lon_raw = b.get("longitude", {}).get("value")
    if lat_raw is None or lon_raw is None:
        return None
    try:
        lat, lon = float(lat_raw), float(lon_raw)
    except (TypeError, ValueError):
        return None

    status = b.get("status", {}).get("value", "seeded")
    raw_specialties = b.get("specialties", {}).get("value", "")
    specialties = [s for s in raw_specialties.split("|") if s] if raw_specialties else []
    open_now_raw = b.get("openNow", {}).get("value")
    open_now = open_now_raw.lower() == "true" if open_now_raw is not None else False
    street = b.get("street", {}).get("value", "")
    postcode = b.get("postcode", {}).get("value", "")
    city = b.get("city", {}).get("value", "")
    address_parts = [p for p in [street, f"{postcode} {city}".strip()] if p]

    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [lon, lat]},
        "properties": {
            "id": space_id,
            "uri": space_uri,
            "name": name,
            "status": status,
            "geolocationFidelity": b.get("geolocationFidelity", {}).get("value", ""),
            "geolocationNote": b.get("geolocationNote", {}).get("value", ""),
            "address": ", ".join(address_parts),
            "city": city,
            "country": b.get("country", {}).get("value", ""),
            "website": b.get("website", {}).get("value", ""),
            "endpoint_url": b.get("profileUrl", {}).get("value", ""),
            "specialties": specialties,
            "open_now": open_now,
            "source": b.get("source", {}).get("value"),
            "opening_hours": b.get("openingHours", {}).get("value", ""),
            "description": b.get("description", {}).get("value", ""),
            "founded": "",
            "capacity": 0,
            "contact": "",
            "network_memberships": [],
            "open_for_hosting": False,
            "last_fetched": "",
        },
    }


async def _rematerialize_geojson() -> None:
    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(
            f"{OXIGRAPH_ENDPOINT}/query",
            content=_SPARQL_SELECT,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
        )
        resp.raise_for_status()
        bindings = resp.json().get("results", {}).get("bindings", [])

    features = [_binding_to_feature(b) for b in bindings]
    features = [f for f in features if f is not None]
    geojson = {"type": "FeatureCollection", "features": features}

    out_path = Path(GEOJSON_OUTPUT)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = out_path.with_suffix(".geojson.tmp")
    tmp_path.write_text(json.dumps(geojson, separators=(",", ":")))
    tmp_path.replace(out_path)
    logger.info("rematerialized %d spaces → %s", len(features), out_path)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/claim/{token}")
async def claim_link(token: str):
    if not _TOKEN_RE.match(token):
        logger.warning("claim attempt rejected — invalid token format: %.40s", token)
        raise HTTPException(status_code=400, detail="Invalid token format")
    logger.info("claim attempt: %s", token)
    raise HTTPException(status_code=422, detail="Not implemented yet")


@app.post("/api/validate-url")
async def validate_url(req: UrlRequest):
    result = await _fetch_and_validate(req.url)
    result.pop("_data", None)
    # Subset info already in result from _fetch_and_validate
    return result


@app.post("/api/register-url")
async def register_url(req: UrlRequest):
    result = await _fetch_and_validate(req.url)
    data = result.pop("_data", {})

    if not result.get("reachable") or not result.get("json_ld_valid") or not result.get("coords_found"):
        raise HTTPException(status_code=422, detail={"validation": result})

    name = result["name_found"]
    lat = result["lat"]
    lon = result["lon"]

    slug = _slug(name)
    if not slug:
        raise HTTPException(status_code=422, detail={"error": "space name contains no ASCII-compatible characters; cannot generate a URI slug"})
    graph_uri = f"urn:mak:space/{slug}"
    space_uri = f"urn:mak:space/{slug}"

    sparql_update = _build_sparql_update(graph_uri, space_uri, name, lat, lon, req.url, data)

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            upd = await client.post(
                f"{OXIGRAPH_ENDPOINT}/update",
                content=sparql_update,
                headers={"Content-Type": "application/sparql-update"},
            )
            upd.raise_for_status()
    except Exception as e:
        logger.error("Oxigraph UPDATE failed: %s", e)
        raise HTTPException(status_code=502, detail={"error": "triplestore_write_failed"})

    # Write snapshot graph with ingestion metadata
    snapshot_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshot_graph = f"urn:mak:space/{slug}/{snapshot_date}"

    # Serialize raw JSON — cap at 50 KB
    raw_json = json.dumps(data, separators=(",", ":"))
    raw_truncated = False
    if len(raw_json) > 50_000:
        logger.warning("raw endpoint content for %s exceeds 50KB (%d bytes), dropping raw storage", slug, len(raw_json))
        raw_json = "{}"
        raw_truncated = True

    # Escape for SPARQL string literal
    escaped_raw = raw_json.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")

    truncated_triple = f'    <{space_uri}> <{MOM}rawTruncated> "true"^^<http://www.w3.org/2001/XMLSchema#boolean> .\n' if raw_truncated else ""
    snapshot_update = f"""INSERT DATA {{
  GRAPH <{snapshot_graph}> {{
    <{space_uri}> <{MOM}snapshotDate> "{snapshot_date}" .
    <{space_uri}> <{MOM}snapshotSummary> "First registration" .
    <{space_uri}> <{MOM}lastHttpStatus> 200 .
    <{space_uri}> <{MOM}rawContent> "{escaped_raw}"^^<http://www.w3.org/2001/XMLSchema#string> .
{truncated_triple}  }}
}}"""
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            snap = await client.post(
                f"{OXIGRAPH_ENDPOINT}/update",
                content=snapshot_update,
                headers={"Content-Type": "application/sparql-update"},
            )
            snap.raise_for_status()
    except Exception as e:
        logger.warning("Snapshot graph write failed (non-fatal): %s", e)

    try:
        await _rematerialize_geojson()
    except Exception as e:
        logger.error("GeoJSON rematerialization failed (non-fatal): %s", e)

    logger.info("registered space: %s (%s)", name, space_uri)
    return {
        "status": "confirmed",
        "space_uri": space_uri,
        "space_name": name,
        "subset": result.get("subset"),
        "subset_score": result.get("subset_score"),
        "unlock_message": result.get("unlock_message"),
        "next_subset": result.get("next_subset"),
        "next_unlock": result.get("next_unlock"),
    }


@app.get("/api/space/{space_id}/snapshots")
async def get_space_snapshots(space_id: str):
    """Fetch ingestion history snapshots for a space."""
    if not re.match(r'^[a-zA-Z0-9_-]+$', space_id):
        return []
    sparql_query = f"""PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>

SELECT ?graph ?snapshotDate ?snapshotSummary ?lastHttpStatus
WHERE {{
  GRAPH ?graph {{
    ?space <{MOM}snapshotDate> ?snapshotDate ;
           <{MOM}snapshotSummary> ?snapshotSummary .
    OPTIONAL {{ ?space <{MOM}lastHttpStatus> ?lastHttpStatus }}
  }}
  FILTER (STRSTARTS(STR(?graph), "urn:mak:space/{space_id}/"))
}}
ORDER BY DESC(?snapshotDate)
"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{OXIGRAPH_ENDPOINT}/query",
                content=sparql_query,
                headers={
                    "Content-Type": "application/sparql-query",
                    "Accept": "application/sparql-results+json",
                },
            )
            resp.raise_for_status()
            bindings = resp.json().get("results", {}).get("bindings", [])
    except Exception as e:
        logger.warning("Failed to fetch snapshots for space %s: %s", space_id, e)
        return []

    snapshots = []
    for b in bindings:
        snapshot = {
            "date": b.get("snapshotDate", {}).get("value", ""),
            "summary": b.get("snapshotSummary", {}).get("value", ""),
            "http_status": int(b.get("lastHttpStatus", {}).get("value", 0)) if b.get("lastHttpStatus", {}).get("value") else 0,
        }
        snapshots.append(snapshot)

    return snapshots


@app.get("/api/space/{space_id}/raw")
async def get_space_raw(space_id: str):
    """Fetch raw endpoint JSON for a space from the cached snapshot.

    Note: live re-fetch is intentionally NOT done here — endpoint freshness is
    the responsibility of the periodic heartbeat (Epic 3), which flips the space
    to broken/stale states when the endpoint stops responding.
    """
    if not re.match(r'^[a-zA-Z0-9_-]+$', space_id):
        return {"error": "no_snapshot", "message": "This space has no cached endpoint content yet."}

    sparql_query = f"""PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>

SELECT ?rawContent ?snapshotDate
WHERE {{
  GRAPH ?graph {{
    <urn:mak:space/{space_id}> <{MOM}rawContent> ?rawContent ;
                                 <{MOM}snapshotDate> ?snapshotDate .
  }}
  FILTER (STRSTARTS(STR(?graph), "urn:mak:space/{space_id}/"))
}}
ORDER BY DESC(?snapshotDate)
LIMIT 1
"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{OXIGRAPH_ENDPOINT}/query",
                content=sparql_query,
                headers={
                    "Content-Type": "application/sparql-query",
                    "Accept": "application/sparql-results+json",
                },
            )
            resp.raise_for_status()
            bindings = resp.json().get("results", {}).get("bindings", [])
    except Exception as e:
        logger.warning("Failed to fetch raw content for space %s: %s", space_id, e)
        return {"error": "no_snapshot", "message": "This space has no cached endpoint content yet."}

    if not bindings:
        return {"error": "no_snapshot", "message": "This space has no cached endpoint content yet."}

    binding = bindings[0]
    raw_json_str = binding.get("rawContent", {}).get("value", "")
    snapshot_date = binding.get("snapshotDate", {}).get("value", "")

    try:
        raw_obj = json.loads(raw_json_str)
    except (json.JSONDecodeError, TypeError):
        logger.warning("Failed to parse raw content JSON for space %s", space_id)
        return {"error": "no_snapshot", "message": "This space has no cached endpoint content yet."}

    return {
        "raw": raw_obj if raw_obj != {} else None,
        "truncated": raw_obj == {},
        "snapshot_date": snapshot_date,
        "source": "cached"
    }
