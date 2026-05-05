import json
import logging
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, TYPE_CHECKING

import httpx
import yaml

from utils import MOM, SCHEMA, _sparql_str, _sparql_iri, _slug

if TYPE_CHECKING:
    from main import SpaceAPISchema

logger = logging.getLogger(__name__)

_config: Optional[dict] = None
_activity_map: Optional[dict] = None


def get_config(config_path: Optional[str] = None) -> dict:
    """Load config.yaml once. Path overridable via CONFIG_PATH env var."""
    global _config
    if _config is not None:
        return _config
    path = config_path or os.getenv("CONFIG_PATH") or str(
        Path(__file__).parent / "config.yaml"
    )
    try:
        with open(path) as f:
            _config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.warning("config.yaml not found at %s, using defaults", path)
        _config = {}
    return _config


def _load_activity_map(path: Optional[str] = None) -> dict:
    global _activity_map
    if _activity_map is not None:
        return _activity_map
    cfg = get_config()
    map_path = path or os.getenv("ACTIVITY_MAP_PATH") or cfg.get(
        "activity_map_path", "/app/scripts/activity_map.yaml"
    )
    try:
        with open(map_path) as f:
            loaded = yaml.safe_load(f) or {}
        # Normalize all keys to lowercase
        _activity_map = {k.lower(): v for k, v in loaded.items()}
    except FileNotFoundError:
        logger.warning("activity_map.yaml not found at %s", map_path)
        _activity_map = {}
    return _activity_map


def _log_unmapped_tags(tags: list) -> None:
    cfg = get_config()
    gap_log = os.getenv("GAP_LOG_PATH") or cfg.get("bandwidth", {}).get(
        "gap_log_path", "/app/tasks/gap_log.txt"
    )
    now = datetime.now(timezone.utc).isoformat()
    try:
        Path(gap_log).parent.mkdir(parents=True, exist_ok=True)
        with open(gap_log, "a") as f:
            for tag in tags:
                f.write(f"{now}\tUNMAPPED_TAG\t{tag}\n")
    except Exception as e:
        logger.warning("gap_log write failed: %s", e)


def resolve_activities(raw_tags: list, activity_map_path: Optional[str] = None) -> list:
    """Map raw activity tags to ontology IRIs.

    Unknown tags fall back to the raw string (never dropped). Unmapped tags
    are appended to gap_log.txt for ontology gap tracking.
    """
    activity_map = _load_activity_map(activity_map_path)
    result = []
    unmapped = []
    seen = set()
    for tag in raw_tags:
        if not tag:
            continue
        key = tag.lower().strip()
        iri = activity_map.get(key)
        value = iri if iri else tag
        if value not in seen:
            result.append(value)
            seen.add(value)
        if not iri:
            unmapped.append(tag)
    if unmapped:
        _log_unmapped_tags(unmapped)
    return result


def classify_operational_state(
    http_status: Optional[int],
    age_days: float,
    consecutive_failures: int,
    prior_state: Optional[str],
) -> tuple[str, str]:
    """Classify an endpoint into an operational state.

    Returns (state, reason). States: confirmed | aging | zombie | dead | error.
    Thresholds are read from config.yaml (operational_state section).
    """
    cfg = get_config().get("operational_state", {})
    aging_days = cfg.get("aging_days_threshold", 30)
    zombie_days = cfg.get("zombie_days_threshold", 90)
    zombie_failures = cfg.get("zombie_failures_threshold", 3)
    dead_failures = cfg.get("dead_failures_threshold", 5)

    if http_status is None:
        return "error", "No HTTP response received"

    if http_status == 200:
        if age_days > zombie_days or consecutive_failures >= zombie_failures:
            return "zombie", f"No update in {age_days:.0f} days and {consecutive_failures} consecutive failures"
        if age_days > aging_days and consecutive_failures < zombie_failures:
            return "aging", f"No update in {age_days:.0f} days"
        return "confirmed", "Endpoint verified"

    if consecutive_failures >= dead_failures or http_status in (404, 410):
        return "dead", f"Endpoint unreachable: HTTP {http_status}"

    if http_status >= 500:
        return "error", f"Server error (HTTP {http_status})"
    if http_status >= 400:
        return "error", f"Client error (HTTP {http_status})"

    return "error", f"Unexpected HTTP {http_status}"


def detect_diff(old_snap: dict, new_snap: dict) -> dict | None:
    """Return field-level diff between two space snapshots.

    Ignores: mom:lastFetched, mom:snapshotDate, whitespace-only changes,
    and array order differences. Returns None if no material change.
    """
    _IGNORED = {"mom:lastFetched", "mom:snapshotDate", "lastFetched", "snapshotDate"}

    def _normalize(obj):
        if isinstance(obj, dict):
            return {k: _normalize(v) for k, v in sorted(obj.items()) if k not in _IGNORED}
        if isinstance(obj, list):
            normalized = [_normalize(i) for i in obj]
            try:
                return sorted(normalized, key=lambda x: json.dumps(x, sort_keys=True))
            except TypeError:
                return normalized
        if isinstance(obj, str):
            return obj.strip()
        return obj

    old_n = _normalize(old_snap)
    new_n = _normalize(new_snap)
    all_keys = set(old_n) | set(new_n)
    changed = []
    added = []
    removed = []
    for key in sorted(all_keys):
        if key in old_n and key not in new_n:
            removed.append(key)
        elif key not in old_n and key in new_n:
            added.append(key)
        elif old_n.get(key) != new_n.get(key):
            changed.append({"field": key, "old": old_n[key], "new": new_n[key]})

    if not (changed or added or removed):
        return None

    return {
        "changed": changed,
        "added": added,
        "removed": removed,
    }


def transform_to_sparql(
    validated_data: "SpaceAPISchema",
    metadata: dict,
) -> tuple[str, str]:
    """Build idempotent SPARQL UPDATE for a space.

    metadata keys:
      - endpoint_url (str): URL the data was fetched from
      - space_id (str, optional): override slug; derived from name if absent
      - http_status (int, optional): HTTP status of the fetch
      - snapshot_summary (str, optional): human-readable summary for snapshot

    Returns (sparql_update_str, snapshot_graph_uri).
    """
    name = validated_data.resolved_name
    lat = validated_data.resolved_lat
    lon = validated_data.resolved_lon

    if not name:
        raise ValueError("validated_data must have a resolved_name")
    if lat is None or lon is None:
        raise ValueError("validated_data must have resolved coordinates")

    slug = metadata.get("space_id") or _slug(name)
    graph_uri = f"urn:mak:space/{slug}"
    space_uri = f"urn:mak:space/{slug}"
    endpoint_url = metadata.get("endpoint_url", "")
    now = datetime.now(timezone.utc).isoformat()
    snapshot_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshot_graph_uri = f"urn:mak:space/{slug}/{snapshot_date}"

    # Resolve activity tags to ontology IRIs
    raw_tags = validated_data.resolved_tags
    activity_iris = resolve_activities(raw_tags) if raw_tags else []

    triples = [
        f"  <{space_uri}> a <{MOM}Space> .",
        f'  <{space_uri}> <{SCHEMA}name> "{_sparql_str(name)}" .',
        f"  <{space_uri}> <{SCHEMA}geo> [ <{SCHEMA}latitude> {lat} ; <{SCHEMA}longitude> {lon} ] .",
        f'  <{space_uri}> <{MOM}operationalState> "confirmed" .',
        f'  <{space_uri}> <{MOM}lastFetched> "{now}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .',
        f'  <{space_uri}> <{MOM}source> "self-registered" .',
    ]

    if endpoint_url:
        safe_ep = _sparql_iri(endpoint_url)
        if safe_ep:
            triples.append(f"  <{space_uri}> <{MOM}endpointUrl> <{safe_ep}> .")

    geo_fidelity = validated_data.resolved_geolocation_fidelity
    if geo_fidelity:
        triples.append(f'  <{space_uri}> <{MOM}geolocationFidelity> "{_sparql_str(geo_fidelity)}" .')

    geo_note = validated_data.geolocation_note
    if geo_note:
        triples.append(f'  <{space_uri}> <{MOM}geolocationNote> "{_sparql_str(geo_note)}"@en .')

    website = validated_data.resolved_url
    if website:
        safe_url = _sparql_iri(website)
        if safe_url:
            triples.append(f"  <{space_uri}> <{SCHEMA}url> <{safe_url}> .")
        else:
            logger.warning("non-HTTPS or unsafe URL skipped for %s: %s", slug, website)

    hours = validated_data.resolved_opening_hours
    if hours:
        triples.append(f'  <{space_uri}> <{SCHEMA}openingHours> "{_sparql_str(hours)}" .')

    if validated_data.description:
        triples.append(f'  <{space_uri}> <{SCHEMA}description> "{_sparql_str(validated_data.description)}" .')

    if validated_data.logo:
        safe_logo = _sparql_iri(validated_data.logo)
        if safe_logo:
            triples.append(f"  <{space_uri}> <{SCHEMA}logo> <{safe_logo}> .")

    if validated_data.contact and isinstance(validated_data.contact, dict):
        contact_json = json.dumps(validated_data.contact, separators=(',', ':'))
        triples.append(f'  <{space_uri}> <{SCHEMA}contactJson> "{_sparql_str(contact_json)}"^^<http://www.w3.org/2001/XMLSchema#string> .')

    triples.append(f'  <{space_uri}> <{MOM}lastUpdated> "{now}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .')

    for activity in activity_iris:
        if activity.startswith("http"):
            safe = _sparql_iri(activity)
            if safe:
                triples.append(f"  <{space_uri}> <{SCHEMA}knowsAbout> <{safe}> .")
        else:
            triples.append(f'  <{space_uri}> <{SCHEMA}knowsAbout> "{_sparql_str(activity)}" .')

    if validated_data.api_compatibility:
        for ver in validated_data.api_compatibility:
            triples.append(f'  <{space_uri}> <{MOM}apiCompatibility> "{_sparql_str(str(ver))}" .')

    if validated_data.networks:
        for net in validated_data.networks:
            triples.append(f'  <{space_uri}> <{MOM}networks> "{_sparql_str(str(net))}" .')

    loc = validated_data.location
    if loc and loc.address:
        triples.append(f'  <{space_uri}> <{MOM}address> "{_sparql_str(loc.address)}" .')

    subset = metadata.get("subset", "")
    if subset:
        triples.append(f'  <{space_uri}> <{MOM}subset> "{_sparql_str(subset)}" .')
    next_unlock = metadata.get("next_unlock")
    if next_unlock:
        triples.append(f'  <{space_uri}> <{MOM}nextUnlock> "{_sparql_str(next_unlock)}" .')

    triples_str = "\n".join(triples)
    http_status = metadata.get("http_status", 200)
    snapshot_summary = metadata.get("snapshot_summary", "Fetch successful")

    snapshot_triples = [
        f"  <{space_uri}> <{MOM}snapshotDate> \"{now}\"^^<http://www.w3.org/2001/XMLSchema#dateTime> .",
        f"  <{space_uri}> <{MOM}snapshotSummary> \"{_sparql_str(snapshot_summary)}\" .",
        f"  <{space_uri}> <{MOM}lastHttpStatus> {http_status} .",
    ]

    if metadata.get("raw_content"):
        raw = metadata.get("raw_content", "")[:50000]  # Cap at 50KB
        snapshot_triples.append(f'  <{space_uri}> <{MOM}rawContent> "{_sparql_str(raw)}"^^<http://www.w3.org/2001/XMLSchema#string> .')

    snapshot_triples_str = "\n".join(snapshot_triples)

    sparql_update = f"""DROP SILENT GRAPH <{graph_uri}> ;
INSERT DATA {{
  GRAPH <{graph_uri}> {{
{triples_str}
  }}
}} ;
INSERT DATA {{
  GRAPH <{snapshot_graph_uri}> {{
{snapshot_triples_str}
  }}
}}"""
    return sparql_update, snapshot_graph_uri


def _init_heartbeat_db(db_path: str) -> None:
    """Create heartbeat_log table if absent."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS heartbeat_log (
            space_id TEXT PRIMARY KEY,
            etag TEXT,
            last_modified TEXT,
            last_fetched TEXT,
            consecutive_failures INTEGER DEFAULT 0
        )
    """)
    con.commit()
    con.close()


async def fetch_endpoint_conditional(
    endpoint_url: str,
    space_id: str,
    db_path: Optional[str] = None,
) -> tuple:
    """Fetch an endpoint with ETag/Last-Modified conditional GET support.

    Returns (response_or_none, response_headers_dict, was_304).
    On 304: response_or_none is None, was_304 is True.
    On 200: response is the httpx.Response object, was_304 is False.
    """
    cfg = get_config()
    resolved_db = db_path or os.getenv("HEARTBEAT_DB_PATH") or cfg.get("bandwidth", {}).get(
        "heartbeat_log_path", "/app/tasks/heartbeat_log.db"
    )
    _init_heartbeat_db(resolved_db)

    con = sqlite3.connect(resolved_db)
    row = con.execute(
        "SELECT etag, last_modified FROM heartbeat_log WHERE space_id=?", (space_id,)
    ).fetchone()
    con.close()

    req_headers = {}
    if row:
        if row[0]:
            req_headers["If-None-Match"] = row[0]
        if row[1]:
            req_headers["If-Modified-Since"] = row[1]

    fetch_timeout = cfg.get("bandwidth", {}).get("heartbeat_timeout_seconds", 60.0)
    async with httpx.AsyncClient(timeout=fetch_timeout, follow_redirects=True) as client:
        resp = await client.get(endpoint_url, headers=req_headers)

    was_304 = resp.status_code == 304
    response_headers = dict(resp.headers)
    new_etag = response_headers.get("etag")
    new_lm = response_headers.get("last-modified")
    now = datetime.now(timezone.utc).isoformat()

    con = sqlite3.connect(resolved_db)
    if resp.status_code == 200:
        con.execute("""
            INSERT INTO heartbeat_log (space_id, etag, last_modified, last_fetched, consecutive_failures)
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT(space_id) DO UPDATE SET
                etag=excluded.etag,
                last_modified=excluded.last_modified,
                last_fetched=excluded.last_fetched,
                consecutive_failures=0
        """, (space_id, new_etag, new_lm, now))
    elif resp.status_code == 304:
        con.execute("""
            INSERT INTO heartbeat_log (space_id, etag, last_modified, last_fetched, consecutive_failures)
            VALUES (?, ?, ?, ?, 0)
            ON CONFLICT(space_id) DO UPDATE SET
                last_fetched=excluded.last_fetched,
                consecutive_failures=0
        """, (space_id, new_etag, new_lm, now))
    else:
        con.execute("""
            INSERT INTO heartbeat_log (space_id, etag, last_modified, last_fetched, consecutive_failures)
            VALUES (?, ?, ?, ?, 1)
            ON CONFLICT(space_id) DO UPDATE SET
                last_fetched=excluded.last_fetched,
                consecutive_failures=consecutive_failures + 1
        """, (space_id, new_etag, new_lm, now))
    con.commit()
    con.close()

    if was_304:
        logger.info("304 Not Modified for %s — bandwidth saved", space_id)
        return None, response_headers, True
    return resp, response_headers, False


_SPARQL_ACTIVE_SPACES = """PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
SELECT ?spaceUri ?endpointUrl WHERE {
  GRAPH ?g {
    ?spaceUri mom:endpointUrl ?endpointUrl .
    OPTIONAL { ?spaceUri mom:operationalState ?state }
    FILTER (!BOUND(?state) || ?state != "dead")
  }
  FILTER (STRSTARTS(STR(?g), "urn:mak:space/"))
}"""


async def query_active_spaces(oxigraph_endpoint: str) -> list[dict]:
    """Return list of {space_uri, endpoint_url} for all non-dead spaces with an endpoint."""
    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.post(
            f"{oxigraph_endpoint}/query",
            content=_SPARQL_ACTIVE_SPACES,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
        )
        resp.raise_for_status()
    bindings = resp.json().get("results", {}).get("bindings", [])
    return [
        {
            "space_uri": b["spaceUri"]["value"],
            "endpoint_url": b["endpointUrl"]["value"],
        }
        for b in bindings
    ]


async def process_one_space(
    space_uri: str,
    endpoint_url: str,
    oxigraph_endpoint: str,
) -> str:
    """Fetch, validate, transform and write one space. Returns 'refreshed' or 'not_modified'."""
    from main import SpaceAPISchema, classify_subset, _build_sparql_update

    space_id = space_uri.split("/")[-1] if "/" in space_uri else space_uri

    resp, _headers, was_304 = await fetch_endpoint_conditional(endpoint_url, space_id)
    if was_304:
        return "not_modified"

    if resp is None or resp.status_code != 200:
        logger.warning("heartbeat fetch failed for %s: status=%s", space_id,
                       resp.status_code if resp else "no response")
        return "error"

    try:
        data = resp.json()
    except Exception:
        logger.warning("heartbeat JSON parse failed for %s", space_id)
        return "error"

    cls: dict = {}
    try:
        schema_obj = SpaceAPISchema.model_validate(data)
        cls = classify_subset(schema_obj)
        sparql_update, _ = transform_to_sparql(schema_obj, {
            "endpoint_url": endpoint_url,
            "space_id": space_id,
            "subset": cls.get("subset", ""),
            "next_unlock": cls.get("next_unlock"),
            "raw_content": resp.text,
        })
    except Exception as e:
        logger.exception("transform_to_sparql failed for %s, using legacy builder: %s", space_id, e)
        sparql_update = _build_sparql_update(
            f"urn:mak:space/{space_id}", f"urn:mak:space/{space_id}",
            data.get("space", space_id), None, None, endpoint_url, data,
            subset=cls.get("subset", ""), next_unlock=cls.get("next_unlock"),
        )

    async with httpx.AsyncClient(timeout=15.0) as client:
        upd = await client.post(
            f"{oxigraph_endpoint}/update",
            content=sparql_update,
            headers={"Content-Type": "application/sparql-update"},
        )
        upd.raise_for_status()

    logger.info("heartbeat refreshed %s", space_id)
    return "refreshed"


async def run_heartbeat_cycle(oxigraph_endpoint: str, rematerialize_fn) -> None:
    """Fetch all active spaces sequentially, then rematerialize GeoJSON once."""
    try:
        spaces = await query_active_spaces(oxigraph_endpoint)
    except Exception as e:
        logger.error("heartbeat cycle: failed to query active spaces: %s", e)
        return

    logger.info("heartbeat cycle: %d spaces to check", len(spaces))
    for entry in spaces:
        try:
            await process_one_space(entry["space_uri"], entry["endpoint_url"], oxigraph_endpoint)
        except Exception as e:
            logger.error("heartbeat cycle: error processing %s: %s", entry["space_uri"], e)

    try:
        await rematerialize_fn()
        logger.info("heartbeat cycle: rematerialization complete")
    except Exception as e:
        logger.error("heartbeat cycle: rematerialization failed: %s", e)
