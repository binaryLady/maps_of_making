import asyncio
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

MAK = "urn:mak:"
XSD = "http://www.w3.org/2001/XMLSchema#"

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


def classify_endpoint_health(
    http_status: Optional[int],
    minutes_since_last_good: float,
    consecutive_failures: int,
) -> tuple[str, str]:
    """Classify endpoint reachability into a health rung.

    Returns (health, reason). Rungs: healthy | unresponsive | warning | broken.
    Thresholds read from config.yaml endpoint_health section.
    """
    cfg = get_config().get("endpoint_health", {})
    unresponsive_min = cfg.get("unresponsive_minutes_threshold", 10)
    warning_min = cfg.get("warning_minutes_threshold", 30)
    broken_min = cfg.get("broken_minutes_threshold", 60)

    if http_status in (200, 304):
        return "healthy", "Endpoint responded successfully"

    if minutes_since_last_good >= broken_min:
        return "broken", f"No successful fetch in {minutes_since_last_good:.0f} minutes"
    if minutes_since_last_good >= warning_min:
        return "warning", f"No successful fetch in {minutes_since_last_good:.0f} minutes"
    if minutes_since_last_good >= unresponsive_min:
        return "unresponsive", f"No successful fetch in {minutes_since_last_good:.0f} minutes"
    return "healthy", "Recent successful fetch"


def classify_lifecycle(days_since_last_update: float) -> tuple[str, str]:
    """Classify space content freshness into a lifecycle state.

    Returns (state, reason) where state is one of: confirmed | aging | zombie | dead.
    Full lifecycle vocabulary: seeded (set at import) → confirmed | aging | zombie →
    closed (via Story 3.2b closure path) or dead (auto-inferred). See mom:operationalState
    for complete enumeration. Negative values (clock-skew) are clamped to 0.
    Thresholds from config.yaml.
    """
    if days_since_last_update < 0:
        logger.warning(
            "WARNING_CLOCK_SKEW: days_since_last_update=%s is negative — clamping to 0",
            days_since_last_update,
        )
        days_since_last_update = 0

    cfg = get_config().get("operational_state", {})
    aging_days = cfg.get("aging_days_threshold", 30)
    zombie_days = cfg.get("zombie_days_threshold", 90)
    dead_days = cfg.get("dead_days_threshold", 180)

    if days_since_last_update >= dead_days:
        return "dead", f"No content update in {days_since_last_update:.0f} days"
    if days_since_last_update >= zombie_days:
        return "zombie", f"No content update in {days_since_last_update:.0f} days"
    if days_since_last_update >= aging_days:
        return "aging", f"No content update in {days_since_last_update:.0f} days"
    return "confirmed", "Content recently updated"


def effective_marker(endpoint_health: str, lifecycle_state: str, open_now: bool) -> str:
    """Resolve three signals into a single public map marker status.

    Lifecycle supersedes endpoint health — a dead space whose hosting silently
    disappears should not masquerade as merely broken.
    """
    if lifecycle_state == "seeded": return "seeded"
    if lifecycle_state == "closed": return "closed"
    if lifecycle_state == "dead":   return "dead"
    if lifecycle_state == "zombie": return "zombie"
    if lifecycle_state == "aging":  return "aging"
    if endpoint_health == "broken": return "broken"
    if open_now:                    return "open"
    return "confirmed"


def _build_pii_strip_sparql(space_uri: str) -> str:
    """Build SPARQL UPDATE that strips PII contact fields and marks a space as mak:closed."""
    now = datetime.now(timezone.utc).isoformat()
    return f"""PREFIX mom: <{MOM}>
PREFIX schema: <https://schema.org/>
PREFIX mak: <{MAK}>
PREFIX xsd: <{XSD}>
DELETE {{
  GRAPH <{space_uri}> {{
    <{space_uri}> schema:contactJson ?contactJson .
    <{space_uri}> mom:operationalState ?oldState .
  }}
}}
INSERT {{
  GRAPH <{space_uri}> {{
    <{space_uri}> mom:operationalState "closed" .
    <{space_uri}> mak:closedAt "{now}"^^xsd:dateTime .
  }}
}}
WHERE {{
  GRAPH <{space_uri}> {{
    OPTIONAL {{ <{space_uri}> schema:contactJson ?contactJson }}
    OPTIONAL {{ <{space_uri}> mom:operationalState ?oldState }}
  }}
}}"""


def _build_revival_closedAt_delete(space_uri: str) -> str:
    """Build SPARQL UPDATE that removes mak:closedAt on revival."""
    return f"""PREFIX mak: <{MAK}>
DELETE {{
  GRAPH <{space_uri}> {{
    <{space_uri}> mak:closedAt ?t .
  }}
}}
WHERE {{
  GRAPH <{space_uri}> {{
    OPTIONAL {{ <{space_uri}> mak:closedAt ?t }}
  }}
}}\n"""


def detect_diff(old_snap: dict, new_snap: dict) -> dict | None:
    """Return field-level diff between two space snapshots.

    Ignores: mom:lastFetched, mom:snapshotDate, whitespace-only changes,
    and array order differences. Returns None if no material change.

    First-fetch case: if old_snap is None, returns a diff (not None) to signal
    that the initial fetch is always treated as a material change.
    """
    # First fetch: no previous snapshot to compare against
    if old_snap is None:
        return {"added": list(new_snap.keys()) if isinstance(new_snap, dict) else [], "changed": [], "removed": []}

    if new_snap is None:
        return None

    # sensors/extensions ignored — they flap for physical reasons.
    # state is intentionally NOT ignored — state.open flips are the designed freshness signal.
    _IGNORED = {"mom:lastFetched", "mom:snapshotDate", "lastFetched", "snapshotDate",
                "sensors", "extensions"}

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


def has_meaningful_change(old_snap: dict, new_snap: dict) -> bool:
    """Return True if the diff between two SpaceAPI snapshots should reset the lifecycle clock.

    Sensors and extensions are excluded (physical flapping). State.open flips ARE
    included — an open/close change is a material update. One definition; callers are
    transformer heartbeat path and canary scenario assertions.
    """
    return detect_diff(old_snap, new_snap) is not None


def _extract_open_now(state) -> Optional[bool]:
    """Extract open/closed boolean from SpaceAPI state field.

    Handles v15 object {open: bool}, v0.13 string "open"/"closed", and returns
    None for missing, unknown, or malformed values (downstream defaults to false).
    """
    if state is None:
        return None
    if isinstance(state, dict):
        val = state.get("open")
        if isinstance(val, bool):
            return val
        return None
    if isinstance(state, str):
        s = state.strip().lower()
        if s == "open":
            return True
        if s == "closed":
            return False
        return None
    return None


def _extract_last_open_change(state) -> Optional[str]:
    """Extract lastchange epoch from v15 state object, return ISO datetime or None."""
    if not isinstance(state, dict):
        return None
    ts = state.get("lastchange")
    if isinstance(ts, (int, float)) and ts > 0:
        try:
            return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
        except (OSError, OverflowError, ValueError):
            logger.warning("WARNING_INVALID_LASTCHANGE: cannot convert %s to datetime", ts)
    return None


def build_state_only_update(space_uri: str, endpoint_health: str, lifecycle_state: str,
                            graph_uri: Optional[str] = None,
                            last_fetched: Optional[str] = None) -> str:
    """Build a surgical SPARQL UPDATE that replaces endpointHealth, operationalState
    and (optionally) lastFetched.

    Used for 304 and failure paths — must NOT touch mom:lastUpdated or mom:openNow.

    When last_fetched is provided, mom:lastFetched is also refreshed. The 304 path
    passes it so the map's "fetched N ago" caption stays current even when the
    endpoint returns Not Modified and no content write happens (Story 3.4).

    Uses three-statement pattern (DELETE WHERE + INSERT DATA) instead of DELETE/INSERT/WHERE
    so the INSERT fires even when the named graph has no prior health/state triples, or
    doesn't exist yet.
    """
    if graph_uri is None:
        graph_uri = space_uri  # named graph URI == space URI (one graph per space)
    deletes = [
        f"DELETE WHERE {{ GRAPH <{graph_uri}> {{ <{space_uri}> mom:endpointHealth ?h }} }}",
        f"DELETE WHERE {{ GRAPH <{graph_uri}> {{ <{space_uri}> mom:operationalState ?s }} }}",
    ]
    inserts = [
        f'    <{space_uri}> mom:endpointHealth "{endpoint_health}" .',
        f'    <{space_uri}> mom:operationalState "{lifecycle_state}" .',
    ]
    if last_fetched:
        deletes.append(
            f"DELETE WHERE {{ GRAPH <{graph_uri}> {{ <{space_uri}> mom:lastFetched ?f }} }}"
        )
        inserts.append(
            f'    <{space_uri}> mom:lastFetched '
            f'"{last_fetched}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .'
        )
    delete_block = " ;\n".join(deletes)
    insert_block = "\n".join(inserts)
    return f"""PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
{delete_block} ;
INSERT DATA {{
  GRAPH <{graph_uri}> {{
{insert_block}
  }}
}}"""


def transform_to_sparql(
    validated_data: "SpaceAPISchema",
    metadata: dict,
    content_changed: bool = True,
) -> tuple[str, str]:
    """Build idempotent SPARQL UPDATE for a space.

    metadata keys:
      - endpoint_url (str): URL the data was fetched from
      - space_id (str, optional): override slug; derived from name if absent
      - http_status (int, optional): HTTP status of the fetch
      - snapshot_summary (str, optional): human-readable summary for snapshot
      - endpoint_health (str, optional): from classify_endpoint_health; defaults to "healthy"
      - lifecycle_state (str, optional): from classify_lifecycle; defaults to "confirmed"

    content_changed: when False, mom:lastUpdated is NOT rewritten (304 / no-diff path).

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
    # Canary space writes to its own isolated named graph, never into production space graphs.
    is_canary = slug == "mother-sands"
    graph_uri = "urn:mak:canary" if is_canary else f"urn:mak:space/{slug}"
    space_uri = f"urn:mak:canary/{slug}" if is_canary else f"urn:mak:space/{slug}"
    endpoint_url = metadata.get("endpoint_url", "")
    now = datetime.now(timezone.utc).isoformat()
    snapshot_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    snapshot_graph_uri = f"urn:mak:canary/{snapshot_date}" if is_canary else f"urn:mak:space/{slug}/{snapshot_date}"

    # Resolve activity tags to ontology IRIs
    raw_tags = validated_data.resolved_tags
    activity_iris = resolve_activities(raw_tags) if raw_tags else []

    endpoint_health = metadata.get("endpoint_health", "healthy")
    lifecycle_state = metadata.get("lifecycle_state", "confirmed")

    source = metadata.get("source", "self-registered")
    triples = [
        f"  <{space_uri}> a <{MOM}Space> .",
        f'  <{space_uri}> <{SCHEMA}name> "{_sparql_str(name)}" .',
        f"  <{space_uri}> <{SCHEMA}geo> [ <{SCHEMA}latitude> {lat} ; <{SCHEMA}longitude> {lon} ] .",
        f'  <{space_uri}> <{MOM}operationalState> "{lifecycle_state}" .',
        f'  <{space_uri}> <{MOM}endpointHealth> "{endpoint_health}" .',
        f'  <{space_uri}> <{MOM}lastFetched> "{now}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .',
        f'  <{space_uri}> <{MOM}source> "{_sparql_str(source)}" .',
    ]
    for member_uri in metadata.get("member_of", []):
        safe = _sparql_iri(member_uri)
        if safe:
            triples.append(f"  <{space_uri}> <{MOM}memberOf> <{safe}> .")

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

    # mom:lastUpdated: written fresh on a content change. On a no-diff cycle we
    # must RE-INSERT the prior value — the enclosing DROP SILENT GRAPH would
    # otherwise wipe it, leaving the space 'updated unknown' / stuck-seeded.
    if content_changed:
        triples.append(f'  <{space_uri}> <{MOM}lastUpdated> "{now}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .')
    else:
        preserved_last_updated = metadata.get("preserved_last_updated")
        if preserved_last_updated:
            triples.append(
                f'  <{space_uri}> <{MOM}lastUpdated> "{preserved_last_updated}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .'
            )

    # open/closed state from SpaceAPI state field
    open_now = _extract_open_now(validated_data.state)
    if open_now is not None:
        triples.append(
            f'  <{space_uri}> <{MOM}openNow> "{str(open_now).lower()}"^^<http://www.w3.org/2001/XMLSchema#boolean> .'
        )
    last_open_change = _extract_last_open_change(validated_data.state)
    if last_open_change is not None:
        triples.append(
            f'  <{space_uri}> <{MOM}lastOpenChange> "{last_open_change}"^^<http://www.w3.org/2001/XMLSchema#dateTime> .'
        )

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
DROP SILENT GRAPH <{snapshot_graph_uri}> ;
INSERT DATA {{
  GRAPH <{snapshot_graph_uri}> {{
{snapshot_triples_str}
  }}
}}"""
    return sparql_update, snapshot_graph_uri


def _init_heartbeat_db(db_path: str) -> None:
    """Create heartbeat_log table if absent, migrate schema if needed."""
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db_path)
    con.execute("""
        CREATE TABLE IF NOT EXISTS heartbeat_log (
            space_id TEXT PRIMARY KEY,
            etag TEXT,
            last_modified TEXT,
            last_fetched TEXT,
            consecutive_failures INTEGER DEFAULT 0,
            last_content_updated TEXT,
            consecutive_closed_cycles INTEGER DEFAULT 0,
            is_closed INTEGER DEFAULT 0,
            last_endpoint_health TEXT DEFAULT 'unknown',
            last_lifecycle_state TEXT DEFAULT 'unknown',
            last_open_now INTEGER DEFAULT NULL,
            last_effective_marker TEXT DEFAULT 'unknown'
        )
    """)
    # Migrate existing tables that lack newer columns
    cols = {r[1] for r in con.execute("PRAGMA table_info(heartbeat_log)").fetchall()}
    if "last_content_updated" not in cols:
        con.execute("ALTER TABLE heartbeat_log ADD COLUMN last_content_updated TEXT")
    if "consecutive_closed_cycles" not in cols:
        con.execute("ALTER TABLE heartbeat_log ADD COLUMN consecutive_closed_cycles INTEGER DEFAULT 0")
    if "is_closed" not in cols:
        con.execute("ALTER TABLE heartbeat_log ADD COLUMN is_closed INTEGER DEFAULT 0")
    if "last_endpoint_health" not in cols:
        con.execute("ALTER TABLE heartbeat_log ADD COLUMN last_endpoint_health TEXT DEFAULT 'unknown'")
    if "last_lifecycle_state" not in cols:
        con.execute("ALTER TABLE heartbeat_log ADD COLUMN last_lifecycle_state TEXT DEFAULT 'unknown'")
    if "last_open_now" not in cols:
        con.execute("ALTER TABLE heartbeat_log ADD COLUMN last_open_now INTEGER DEFAULT NULL")
    if "last_effective_marker" not in cols:
        con.execute("ALTER TABLE heartbeat_log ADD COLUMN last_effective_marker TEXT DEFAULT 'unknown'")
    con.commit()
    con.close()


def _read_heartbeat_row(space_id: str, resolved_db: str) -> dict:
    """Read heartbeat_log row for a space. Returns dict with defaults if absent."""
    con = sqlite3.connect(resolved_db)
    row = con.execute(
        "SELECT etag, last_modified, last_fetched, consecutive_failures, last_content_updated, "
        "consecutive_closed_cycles, is_closed, last_endpoint_health, last_lifecycle_state, "
        "last_open_now, last_effective_marker "
        "FROM heartbeat_log WHERE space_id=?", (space_id,)
    ).fetchone()
    con.close()
    if row:
        return {
            "etag": row[0],
            "last_modified": row[1],
            "last_fetched": row[2],
            "consecutive_failures": row[3] or 0,
            "last_content_updated": row[4],
            "consecutive_closed_cycles": row[5] or 0,
            "is_closed": row[6] or 0,
            "last_endpoint_health": row[7] or "unknown",
            "last_lifecycle_state": row[8] or "unknown",
            "last_open_now": row[9],
            "last_effective_marker": row[10] or "unknown",
        }
    return {"etag": None, "last_modified": None, "last_fetched": None,
            "consecutive_failures": 0, "last_content_updated": None,
            "consecutive_closed_cycles": 0, "is_closed": 0,
            "last_endpoint_health": "unknown", "last_lifecycle_state": "unknown",
            "last_open_now": None, "last_effective_marker": "unknown"}


def update_last_content_updated(space_id: str, db_path: Optional[str] = None) -> None:
    """Record that content changed for a space, resetting the lifecycle clock."""
    cfg = get_config()
    resolved_db = db_path or os.getenv("HEARTBEAT_DB_PATH") or cfg.get("bandwidth", {}).get(
        "heartbeat_log_path", "/app/tasks/heartbeat_log.db"
    )
    now = datetime.now(timezone.utc).isoformat()
    con = sqlite3.connect(resolved_db)
    con.execute(
        "UPDATE heartbeat_log SET last_content_updated=? WHERE space_id=?", (now, space_id)
    )
    con.commit()
    con.close()


async def fetch_endpoint_conditional(
    endpoint_url: str,
    space_id: str,
    db_path: Optional[str] = None,
) -> tuple:
    """Fetch an endpoint with ETag/Last-Modified conditional GET support.

    Returns (response_or_none, response_headers_dict, was_304, db_row).
    On 304: response_or_none is None, was_304 is True.
    On 200: response is the httpx.Response object, was_304 is False.
    db_row contains pre-fetch DB state: consecutive_failures, last_content_updated, etc.
    """
    cfg = get_config()
    resolved_db = db_path or os.getenv("HEARTBEAT_DB_PATH") or cfg.get("bandwidth", {}).get(
        "heartbeat_log_path", "/app/tasks/heartbeat_log.db"
    )
    _init_heartbeat_db(resolved_db)

    db_row = _read_heartbeat_row(space_id, resolved_db)

    req_headers = {}
    if db_row["etag"]:
        req_headers["If-None-Match"] = db_row["etag"]
    if db_row["last_modified"]:
        req_headers["If-Modified-Since"] = db_row["last_modified"]

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
        return None, response_headers, True, db_row
    return resp, response_headers, False, db_row


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


def _days_since(iso_ts: Optional[str]) -> float:
    """Return fractional days since an ISO datetime string, or a large sentinel if absent."""
    if not iso_ts:
        return 0.0  # no record → treat as just-confirmed
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - ts
        return delta.total_seconds() / 86400
    except (ValueError, TypeError):
        return 0.0


def _minutes_since(iso_ts: Optional[str]) -> float:
    """Return fractional minutes since an ISO datetime string, or 0 if absent/invalid."""
    if not iso_ts:
        return 0.0
    try:
        ts = datetime.fromisoformat(iso_ts.replace("Z", "+00:00"))
        delta = datetime.now(timezone.utc) - ts
        return delta.total_seconds() / 60
    except (ValueError, TypeError):
        return 0.0


async def process_one_space(
    space_uri: str,
    endpoint_url: str,
    oxigraph_endpoint: str,
) -> tuple[str, bool]:
    """Fetch, validate, transform and write one space.

    Returns (outcome, state_changed) where state_changed indicates whether any
    triple was written (drives the rematerialize-skip optimization in AC6).
    """
    from main import SpaceAPISchema, classify_subset, _build_sparql_update

    space_id = space_uri.split("/")[-1] if "/" in space_uri else space_uri
    # Canary space uses its own isolated named graph and subject URI.
    _is_canary = space_id == "mother-sands"
    _effective_space_uri = f"urn:mak:canary/{space_id}" if _is_canary else space_uri

    _cfg_early = get_config()
    resolved_db = os.getenv("HEARTBEAT_DB_PATH") or _cfg_early.get("bandwidth", {}).get(
        "heartbeat_log_path", "/app/tasks/heartbeat_log.db"
    )

    resp, _headers, was_304, db_row = await fetch_endpoint_conditional(endpoint_url, space_id)

    consecutive_failures = db_row.get("consecutive_failures", 0)
    last_fetched_ts = db_row.get("last_fetched")
    last_content_updated_ts = db_row.get("last_content_updated")
    consecutive_closed_cycles = db_row.get("consecutive_closed_cycles", 0)
    is_closed = db_row.get("is_closed", 0)

    days_since_update = _days_since(last_content_updated_ts)
    lifecycle_state, _lc_reason = classify_lifecycle(days_since_update)
    if is_closed:
        lifecycle_state = "closed"

    if was_304:
        minutes_ok = _minutes_since(last_fetched_ts)
        endpoint_health, _ = classify_endpoint_health(304, minutes_ok, consecutive_failures)
        prior_health = db_row.get("last_endpoint_health", "unknown")
        prior_lifecycle = db_row.get("last_lifecycle_state", "unknown")
        state_changed = (endpoint_health != prior_health or lifecycle_state != prior_lifecycle)
        # Always write on 304 to refresh mom:lastFetched — otherwise the map's
        # "fetched N ago" caption freezes at the last 200 response (Story 3.4).
        _now_304 = datetime.now(timezone.utc).isoformat()
        _graph = "urn:mak:canary" if _is_canary else None
        state_update = build_state_only_update(
            _effective_space_uri, endpoint_health, lifecycle_state, _graph,
            last_fetched=_now_304,
        )
        async with httpx.AsyncClient(timeout=15.0) as client:
            upd = await client.post(
                f"{oxigraph_endpoint}/update",
                content=state_update,
                headers={"Content-Type": "application/sparql-update"},
            )
            upd.raise_for_status()
        if state_changed:
            prior_open_now = db_row.get("last_open_now")
            _open_304 = bool(prior_open_now) if prior_open_now is not None else False
            _marker_304 = effective_marker(endpoint_health, lifecycle_state, _open_304)
            con = sqlite3.connect(resolved_db)
            con.execute(
                "UPDATE heartbeat_log SET last_endpoint_health=?, last_lifecycle_state=?, "
                "last_effective_marker=? WHERE space_id=?",
                (endpoint_health, lifecycle_state, _marker_304, space_id),
            )
            con.commit()
            con.close()
        logger.info("heartbeat 304 for %s (%s/%s) — lastFetched refreshed%s", space_id,
                    endpoint_health, lifecycle_state,
                    ", state written" if state_changed else "")
        return "not_modified", True

    if resp is None or resp.status_code != 200:
        status_code = resp.status_code if resp else None
        logger.warning("heartbeat fetch failed for %s: status=%s", space_id, status_code)
        # minutes_since_last_good: use large sentinel if never fetched, so health degrades correctly
        minutes_since_good = _minutes_since(last_fetched_ts) if last_fetched_ts else float("inf")
        endpoint_health, _ = classify_endpoint_health(status_code, minutes_since_good, consecutive_failures + 1)
        prior_health = db_row.get("last_endpoint_health", "unknown")
        prior_lifecycle = db_row.get("last_lifecycle_state", "unknown")
        state_changed = (endpoint_health != prior_health or lifecycle_state != prior_lifecycle)
        state_update = build_state_only_update(space_uri, endpoint_health, lifecycle_state)
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                upd = await client.post(
                    f"{oxigraph_endpoint}/update",
                    content=state_update,
                    headers={"Content-Type": "application/sparql-update"},
                )
                upd.raise_for_status()
            if state_changed:
                _marker_err = effective_marker(endpoint_health, lifecycle_state, False)
                con = sqlite3.connect(resolved_db)
                con.execute(
                    "UPDATE heartbeat_log SET last_endpoint_health=?, last_lifecycle_state=?, "
                    "last_effective_marker=? WHERE space_id=?",
                    (endpoint_health, lifecycle_state, _marker_err, space_id),
                )
                con.commit()
                con.close()
        except Exception as e:
            logger.error("state-only write failed for %s: %s", space_id, e)
        return "error", state_changed

    try:
        data = resp.json()
    except Exception:
        logger.warning("heartbeat JSON parse failed for %s", space_id)
        return "error", False

    # simulatedAge seam: canary payload may override the lifecycle clock for diagnostic testing.
    # Read from ext_mom.simulatedAge (caller-level injection, classifier stays pure).
    simulated_age = data.get("ext_mom", {}).get("simulatedAge")
    if simulated_age is not None:
        days_since_update = float(simulated_age)
        lifecycle_state, _lc_reason = classify_lifecycle(days_since_update)
        if is_closed:
            lifecycle_state = "closed"
        logger.info("canary simulatedAge=%s for %s → lifecycle=%s", simulated_age, space_id, lifecycle_state)

    endpoint_health, _ = classify_endpoint_health(200, 0, 0)

    cls: dict = {}
    old_snap: Optional[dict] = None
    open_signal: Optional[bool] = None

    # Load previous snapshot for diff detection
    cfg = get_config()

    try:
        schema_obj = SpaceAPISchema.model_validate(data)
        cls = classify_subset(schema_obj)

        # Update closed-cycle counter based on open/closed signal (200 responses only)
        open_signal = _extract_open_now(schema_obj.state)
        if open_signal is False:
            consecutive_closed_cycles += 1
        elif open_signal is True:
            consecutive_closed_cycles = 0
        # None (no signal) → leave counter unchanged

        # Detect content diff from previous snapshot if available
        content_changed = True
        if last_content_updated_ts is not None:
            # Try to get old snapshot for diff (best-effort)
            try:
                old_snap = await _fetch_last_snapshot(space_id, oxigraph_endpoint)
            except Exception:
                old_snap = None
            if old_snap is not None:
                diff = detect_diff(old_snap, data)
                content_changed = diff is not None
                if not content_changed:
                    logger.info("heartbeat no content diff for %s", space_id)

        # Revival: material content change on a closed space
        revival_sparql = None
        if is_closed and content_changed:
            revival_sparql = _build_revival_closedAt_delete(space_uri)
            is_closed = 0
            consecutive_closed_cycles = 0
            lifecycle_state = "confirmed"

        if content_changed and not is_closed:
            lifecycle_state, _ = classify_lifecycle(0)  # just updated → confirmed

        preserved = await _read_space_metadata(space_uri, oxigraph_endpoint)
        sparql_update, _ = transform_to_sparql(schema_obj, {
            "endpoint_url": endpoint_url,
            "space_id": space_id,
            "subset": cls.get("subset", ""),
            "next_unlock": cls.get("next_unlock"),
            "raw_content": resp.text,
            "endpoint_health": endpoint_health,
            "lifecycle_state": lifecycle_state,
            "source": preserved["source"],
            "member_of": preserved["member_of"],
            # Preserve mom:lastUpdated across the DROP on a no-diff cycle. The
            # heartbeat_log's last_content_updated is the authoritative record of
            # when content last changed, so it both preserves the value AND
            # recovers spaces whose triple was already wiped by the old bug.
            # Fall back to the Oxigraph-side value if the DB has no record.
            "preserved_last_updated": last_content_updated_ts or preserved["last_updated"],
        }, content_changed=content_changed)

        if revival_sparql:
            # SPARQL UPDATE operations must be ';'-separated. The revival block is a
            # DELETE/WHERE op; sparql_update starts with DROP. Without the separator
            # Oxigraph parses DROP as part of the WHERE clause and rejects the whole
            # request with 400 — freezing every triple, including mom:lastUpdated.
            sparql_update = revival_sparql.rstrip() + " ;\n" + sparql_update

    except Exception as e:
        logger.exception("transform_to_sparql failed for %s, using legacy builder: %s", space_id, e)
        _g = "urn:mak:canary" if space_id == "mother-sands" else f"urn:mak:space/{space_id}"
        _s = f"urn:mak:canary/{space_id}" if space_id == "mother-sands" else f"urn:mak:space/{space_id}"
        sparql_update = _build_sparql_update(
            _g, _s,
            data.get("space", space_id), None, None, endpoint_url, data,
            subset=cls.get("subset", ""), next_unlock=cls.get("next_unlock"),
        )
        content_changed = True

    async with httpx.AsyncClient(timeout=15.0) as client:
        upd = await client.post(
            f"{oxigraph_endpoint}/update",
            content=sparql_update,
            headers={"Content-Type": "application/sparql-update"},
        )
        upd.raise_for_status()

    # Closure trigger: threshold reached and not already closed
    cfg_closure = get_config().get("closure", {})
    closed_threshold = cfg_closure.get("closed_cycles_threshold", 6)
    if consecutive_closed_cycles >= closed_threshold and not is_closed:
        pii_strip = _build_pii_strip_sparql(space_uri)
        async with httpx.AsyncClient(timeout=15.0) as client:
            upd = await client.post(
                f"{oxigraph_endpoint}/update",
                content=pii_strip,
                headers={"Content-Type": "application/sparql-update"},
            )
            upd.raise_for_status()
        is_closed = 1
        logger.warning("closed_pii_strip space_id=%s consecutive_closed=%d", space_id, consecutive_closed_cycles)

    # Persist updated closed-cycle counter, is_closed flag, health/lifecycle, and coherence columns.
    # Wrapped in try/except: a DB failure here must not corrupt Oxigraph state already written.
    try:
        _open_now_int = (1 if open_signal else 0) if open_signal is not None else None
        _marker = effective_marker(endpoint_health, lifecycle_state, bool(open_signal))
        con = sqlite3.connect(resolved_db)
        con.execute(
            "UPDATE heartbeat_log SET consecutive_closed_cycles=?, is_closed=?, "
            "last_endpoint_health=?, last_lifecycle_state=?, "
            "last_open_now=?, last_effective_marker=? WHERE space_id=?",
            (consecutive_closed_cycles, is_closed, endpoint_health, lifecycle_state,
             _open_now_int, _marker, space_id),
        )
        con.commit()
        con.close()
    except Exception as db_err:
        logger.error("WARNING_DB_WRITE_FAILED space_id=%s: %s — Oxigraph already updated, "
                     "DB state may be stale until next cycle", space_id, db_err)

    if content_changed:
        update_last_content_updated(space_id, resolved_db)

    outcome = "refreshed" if content_changed else "not_modified_content"
    logger.info("heartbeat %s %s (%s/%s)", outcome, space_id, endpoint_health, lifecycle_state)
    return outcome, True


async def _fetch_last_snapshot(space_id: str, oxigraph_endpoint: str) -> Optional[dict]:
    """Fetch the latest raw snapshot JSON for a space from Oxigraph. Returns None if absent."""
    sparql = f"""PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
SELECT ?rawContent WHERE {{
  GRAPH ?g {{
    <urn:mak:space/{space_id}> mom:rawContent ?rawContent .
  }}
  FILTER (STRSTARTS(STR(?g), "urn:mak:space/{space_id}/"))
}}
ORDER BY DESC(?g)
LIMIT 1"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{oxigraph_endpoint}/query",
            content=sparql,
            headers={"Content-Type": "application/sparql-query",
                     "Accept": "application/sparql-results+json"},
        )
        resp.raise_for_status()
    bindings = resp.json().get("results", {}).get("bindings", [])
    if not bindings:
        return None
    raw = bindings[0].get("rawContent", {}).get("value", "")
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return None


async def _read_space_metadata(space_uri: str, oxigraph_endpoint: str) -> dict:
    """Read source, memberOf and lastUpdated from existing space graph.

    transform_to_sparql does DROP SILENT GRAPH + INSERT DATA. Any triple not
    re-inserted is lost. mom:lastUpdated is only re-inserted when content_changed
    is True — so on a no-diff (content_changed=False) cycle the DROP would wipe
    it permanently, leaving the space 'updated unknown' / stuck-seeded. We read
    the prior value here so the caller can preserve it across the DROP.
    """
    query = f"""PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
SELECT ?source ?memberOf ?lastUpdated WHERE {{
  GRAPH <{space_uri}> {{
    OPTIONAL {{ <{space_uri}> mom:source ?source }}
    OPTIONAL {{ <{space_uri}> mom:memberOf ?memberOf }}
    OPTIONAL {{ <{space_uri}> mom:lastUpdated ?lastUpdated }}
  }}
}}"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{oxigraph_endpoint}/query",
                content=query,
                headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
            )
            resp.raise_for_status()
        bindings = resp.json().get("results", {}).get("bindings", [])
        source = bindings[0].get("source", {}).get("value", "self-registered") if bindings else "self-registered"
        member_of = list({b["memberOf"]["value"] for b in bindings if "memberOf" in b})
        last_updated = bindings[0].get("lastUpdated", {}).get("value") if bindings else None
        return {"source": source, "member_of": member_of, "last_updated": last_updated}
    except Exception:
        return {"source": "self-registered", "member_of": [], "last_updated": None}


async def run_heartbeat_cycle(oxigraph_endpoint: str, rematerialize_fn) -> None:
    """Fetch all active spaces concurrently, then always rematerialize GeoJSON.

    Spaces are processed in parallel under a bounded semaphore: the slow part is
    network I/O waiting on each endpoint, so sequential processing wastes most of
    the cycle idle. The bound keeps us from opening hundreds of sockets or
    overwhelming Oxigraph / the heartbeat sqlite file at once.
    """
    try:
        spaces = await query_active_spaces(oxigraph_endpoint)
    except Exception as e:
        logger.error("heartbeat cycle: failed to query active spaces: %s", e)
        return

    cfg = get_config()
    concurrency = int(cfg.get("bandwidth", {}).get("heartbeat_concurrency", 8))
    logger.info("heartbeat cycle: %d spaces to check (concurrency=%d)", len(spaces), concurrency)
    any_change = False
    sem = asyncio.Semaphore(max(1, concurrency))

    async def _guarded(entry: dict):
        async with sem:
            return await process_one_space(
                entry["space_uri"], entry["endpoint_url"], oxigraph_endpoint
            )

    results = await asyncio.gather(*(_guarded(e) for e in spaces), return_exceptions=True)
    for entry, result in zip(spaces, results):
        if isinstance(result, Exception):
            logger.error("heartbeat cycle: error processing %s: %s", entry["space_uri"], result)
            any_change = True  # assume a change on error to be safe
        else:
            _outcome, state_changed = result
            if state_changed:
                any_change = True

    try:
        await rematerialize_fn()
        if any_change:
            logger.info("heartbeat cycle: found changes, rematerialization complete")
        else:
            logger.debug("heartbeat cycle: no endpoint changes, rematerialization complete")
    except Exception as e:
        logger.error("heartbeat cycle: rematerialization failed: %s", e)
