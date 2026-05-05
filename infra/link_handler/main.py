import json
import logging
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional, List

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, ConfigDict

from utils import MOM, SCHEMA, _ALLOWED_SCHEMES, _sparql_str, _sparql_iri, _slug

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Maps of Making Link Handler")

_TOKEN_RE = re.compile(r'^[A-Za-z0-9_\-]{8,255}$')

OXIGRAPH_ENDPOINT = os.getenv("OXIGRAPH_ENDPOINT", "http://oxigraph:7878")
GEOJSON_OUTPUT = os.getenv("GEOJSON_OUTPUT", "/app/web_data/spaces.geojson")


# Same SELECT query as scripts/materialize_geojson.py — kept in sync intentionally
_SPARQL_SELECT = """PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>

SELECT ?spaceUri ?name ?latitude ?longitude ?status ?geolocationFidelity ?geolocationNote
       ?street ?postcode ?city ?country ?website ?profileUrl ?openNow ?source
       ?openingHours ?description ?logo ?contactJson ?lastUpdated ?subset ?nextUnlock
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
      OPTIONAL { ?spaceUri schema:logo ?logo }
      OPTIONAL { ?spaceUri schema:contactJson ?contactJson }
      OPTIONAL { ?spaceUri mom:lastUpdated ?lastUpdated }
      OPTIONAL { ?spaceUri mom:subset ?subset }
      OPTIONAL { ?spaceUri mom:nextUnlock ?nextUnlock }
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
      OPTIONAL { ?spaceUri schema:logo ?logo }
      OPTIONAL { ?spaceUri schema:contactJson ?contactJson }
      OPTIONAL { ?spaceUri mom:lastUpdated ?lastUpdated }
      OPTIONAL { ?spaceUri mom:subset ?subset }
      OPTIONAL { ?spaceUri mom:nextUnlock ?nextUnlock }
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
         ?openingHours ?description ?logo ?contactJson ?lastUpdated ?subset ?nextUnlock
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
    model_config = ConfigDict(populate_by_name=True, extra="allow", validate_default=True)

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
    # Full SpaceAPI v14 tier
    state: Optional[Any] = None  # SpaceAPI v14 `state` may be a string ("open"/"closed"/"unknown") or an object {open: bool, lastchange: int, message: str, ...}. Accept either; classify_subset only checks truthiness.
    networks: Optional[List[str]] = None
    tags: Optional[List[str]] = Field(None, alias="schema:knowsAbout")
    plain_tags: Optional[List[str]] = Field(None, alias="knowsAbout")
    # MOM geolocation enrichment
    geolocation_fidelity: Optional[str] = Field(None, alias="mom:geolocationFidelity")
    geolocation_note: Optional[str] = Field(None, alias="mom:geolocationNote")
    # Extended address fields (AC1 extended tier)
    address_locality: Optional[str] = Field(None, alias="schema:addressLocality")
    postal_code: Optional[str] = Field(None, alias="schema:postalCode")
    street_address: Optional[str] = Field(None, alias="schema:streetAddress")
    address_country: Optional[str] = Field(None, alias="schema:addressCountry")

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

    @property
    def resolved_tags(self) -> List[str]:
        raw = self.tags or self.plain_tags or []
        if isinstance(raw, str):
            return [raw]
        return list(raw)

    @property
    def resolved_geolocation_fidelity(self) -> Optional[str]:
        return self.geolocation_fidelity


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
    """Classify the subset level reached by the endpoint data.

    api_compatibility is intentionally excluded from tier checks — it is a SpaceAPI
    interop signal with no MoM-specific feature unlock. Logo and contact are sufficient
    for the spaceapi:compatible tier on MoM.
    """
    has_required = bool(schema.resolved_name and schema.resolved_lat is not None and schema.resolved_lon is not None)
    has_card = has_required and bool(schema.resolved_url and schema.resolved_opening_hours)
    has_spaceapi = has_card and bool(schema.logo and schema.contact)

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
        if not schema.logo:
            missing.append("logo")
        if not schema.contact:
            missing.append("contact")
        if not schema.logo:
            next_unlock = "Add logo to unlock SpaceAPI compatibility"
        elif not schema.contact:
            next_unlock = "Add contact to unlock SpaceAPI compatibility"
        else:
            next_unlock = None
        return {
            "subset": "mom:card",
            "subset_score": 2,
            "missing_card_fields": missing,
            "unlock_message": "Full detail card unlocked.",
            "next_subset": "spaceapi:compatible",
            "next_unlock": next_unlock,
        }
    elif has_required:
        missing = []
        if not schema.resolved_url:
            missing.append("schema:url")
        if not schema.resolved_opening_hours:
            missing.append("schema:openingHours")
        if not schema.resolved_url:
            next_unlock = "Add schema:url (website) to unlock the full detail card"
        elif not schema.resolved_opening_hours:
            next_unlock = "Add schema:openingHours to unlock the full detail card"
        else:
            next_unlock = None
        return {
            "subset": "mom:required",
            "subset_score": 1,
            "missing_card_fields": missing,
            "unlock_message": "Pin on map unlocked.",
            "next_subset": "mom:card",
            "next_unlock": next_unlock,
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
        result["error"] = "Name not found — expected 'space' (SpaceAPI) or 'schema:name' / 'name' (JSON-LD)"
    elif lat is None or lon is None:
        result["coords_error"] = "Coordinates not found — expected location.lat/lon (SpaceAPI) or schema:geo (JSON-LD)"
    return result


def _build_sparql_update(graph_uri: str, space_uri: str, name: str, lat: float, lon: float,
                          endpoint_url: str, data: dict,
                          subset: str = "", next_unlock: Optional[str] = None) -> str:
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

    logo_val = data.get("schema:logo") or data.get("logo")
    if logo_val:
        triples.append(f'  <{space_uri}> <{SCHEMA}logo> "{_sparql_str(str(logo_val))}" .')

    contact_val = data.get("contact")
    if contact_val and isinstance(contact_val, dict):
        contact_json = json.dumps(contact_val, separators=(',', ':'))
        triples.append(f'  <{space_uri}> <{SCHEMA}contactJson> "{_sparql_str(contact_json)}"^^<http://www.w3.org/2001/XMLSchema#string> .')

    triples.append(f'  <{space_uri}> <{MOM}lastUpdated> "{now}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .')

    if subset:
        triples.append(f'  <{space_uri}> <{MOM}subset> "{_sparql_str(subset)}" .')
    if next_unlock:
        triples.append(f'  <{space_uri}> <{MOM}nextUnlock> "{_sparql_str(next_unlock)}" .')

    triples_str = "\n".join(triples)
    return f"""DROP SILENT GRAPH <{graph_uri}> ;
INSERT DATA {{
  GRAPH <{graph_uri}> {{
{triples_str}
  }}
}}"""


def _parse_contact_json(raw: Optional[str]) -> Optional[dict]:
    if not raw:
        return None
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


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
            "logo": b.get("logo", {}).get("value", ""),
            "contact": _parse_contact_json(b.get("contactJson", {}).get("value")),
            "last_updated": b.get("lastUpdated", {}).get("value", ""),
            "subset": b.get("subset", {}).get("value", ""),
            "next_unlock": b.get("nextUnlock", {}).get("value", ""),
            "founded": "",
            "capacity": 0,
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

    from transformer import transform_to_sparql
    cls: dict = {}
    try:
        schema_obj = SpaceAPISchema.model_validate(data)
        cls = classify_subset(schema_obj)
        sparql_update, _ = transform_to_sparql(schema_obj, {
            "endpoint_url": req.url, "space_id": slug,
            "subset": cls.get("subset", ""), "next_unlock": cls.get("next_unlock"),
        })
    except Exception as e:
        logger.exception("transform_to_sparql failed, falling back to legacy builder: %s", e)
        sparql_update = _build_sparql_update(
            graph_uri, space_uri, name, lat, lon, req.url, data,
            subset=cls.get("subset", ""), next_unlock=cls.get("next_unlock"),
        )

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
