import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

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
       (GROUP_CONCAT(?specialty; separator="|") AS ?specialties)
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
ORDER BY ?spaceUri"""

# Only flag fields that are unambiguously personal data (not business contact info).
# schema:email and schema:telephone on a LocalBusiness are public organizational contacts — not PII.
# schema:Person is a class value (appears under @type), not a property key — excluded.
_PII_FIELDS = {"foaf:mbox"}


class UrlRequest(BaseModel):
    url: str
    space_id: Optional[str] = None


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

    name = _extract_name(data)
    lat, lon = _extract_coords(data)
    pii_found = _scan_pii(data)

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
    if "schema:address" in data:
        addr = _sparql_str(str(data["schema:address"]))
        triples.append(f'  <{space_uri}> <{MOM}address> "{addr}" .')
    website = data.get("schema:url") or data.get("url")
    safe_website = _sparql_iri(str(website)) if website else None
    if safe_website:
        triples.append(f"  <{space_uri}> <{SCHEMA}url> <{safe_website}> .")
    desc = data.get("schema:description")
    if desc:
        triples.append(f'  <{space_uri}> <{SCHEMA}description> "{_sparql_str(str(desc))}" .')
    hours = data.get("schema:openingHours")
    if hours:
        triples.append(f'  <{space_uri}> <{SCHEMA}openingHours> "{_sparql_str(str(hours))}" .')

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
            "opening_hours": "",
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

    try:
        await _rematerialize_geojson()
    except Exception as e:
        logger.error("GeoJSON rematerialization failed (non-fatal): %s", e)

    logger.info("registered space: %s (%s)", name, space_uri)
    return {"status": "confirmed", "space_uri": space_uri, "space_name": name}
