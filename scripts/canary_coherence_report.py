"""Mother Sands canary coherence-diff report.

Queries all four layers after a scenario injection and flags where reality diverges
from the injected intent. Never a boolean pass/fail — shows per-layer values so the
operator can pinpoint which layer is at fault.

Layers:
  1. Endpoint file  — what data/canary/served.json contains
  2. Heartbeat log  — what heartbeat_log.db persisted (health, lifecycle, open_now, marker)
  3. Oxigraph SPARQL — mom:operationalState, mom:dynamicState in <urn:mak:canary>
  4. GeoJSON         — what materialize_geojson produces (last materialized spaces.json)

Usage:
  python3 scripts/canary_coherence_report.py [--scenario SCENARIO_NAME]
  make canary-report
"""
import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

# Allow importing from infra/link_handler
sys.path.insert(0, str(Path(__file__).parent.parent / "infra" / "link_handler"))

import httpx
from transformer import classify_endpoint_health, classify_lifecycle, effective_marker

REPO_ROOT = Path(__file__).parent.parent
SERVED_FILE = REPO_ROOT / "data" / "canary" / "served.json"
BASELINE_FILE = REPO_ROOT / "data" / "canary" / "baseline.json"
GEOJSON_FILE = REPO_ROOT / "web" / "data" / "spaces.geojson"

CANARY_SPACE_ID = "mother-sands"
CANARY_GRAPH = "urn:mak:canary"
OXIGRAPH_URL = os.environ.get("OXIGRAPH_URL", "http://localhost:7878")

MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"

GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"


def _ok(msg):
    return f"{GREEN}✓{RESET} {msg}"


def _fail(msg):
    return f"{RED}✗{RESET} {msg}"


def _warn(msg):
    return f"{YELLOW}?{RESET} {msg}"


# ── Layer 1: Endpoint file ────────────────────────────────────────────────────

def read_endpoint_file() -> dict:
    served = SERVED_FILE if SERVED_FILE.exists() else BASELINE_FILE
    return json.loads(served.read_text())


def extract_endpoint_state(payload: dict) -> dict:
    state = payload.get("state", {})
    if isinstance(state, dict):
        open_now = state.get("open")
    elif isinstance(state, str):
        open_now = state == "open"
    else:
        open_now = None
    simulated_age = payload.get("ext_mom", {}).get("simulatedAge")
    operator_closed = payload.get("ext_mom", {}).get("operatorDeclaredClosed", False)
    return {
        "open_now": open_now,
        "simulated_age": simulated_age,
        "operator_declared_closed": operator_closed,
    }


# ── Layer 2: Heartbeat log ─────────────────────────────────────────────────────

def read_heartbeat_log(db_path: str) -> dict | None:
    if not Path(db_path).exists():
        return None
    try:
        con = sqlite3.connect(db_path)
        row = con.execute(
            "SELECT last_endpoint_health, last_lifecycle_state, last_open_now, last_effective_marker, last_fetched "
            "FROM heartbeat_log WHERE space_id=?", (CANARY_SPACE_ID,)
        ).fetchone()
        con.close()
    except Exception as e:
        return {"error": str(e)}
    if not row:
        return None
    return {
        "endpoint_health": row[0] or "unknown",
        "lifecycle_state": row[1] or "unknown",
        "open_now": bool(row[2]) if row[2] is not None else None,
        "effective_marker": row[3] or "unknown",
        "last_fetched": row[4] or "—",
    }


# ── Layer 3: Oxigraph SPARQL ──────────────────────────────────────────────────

def read_oxigraph(space_id: str = CANARY_SPACE_ID) -> dict | None:
    sparql = f"""
PREFIX mom: <{MOM}>
SELECT ?operationalState ?dynamicState ?endpointHealth WHERE {{
  GRAPH <{CANARY_GRAPH}> {{
    ?space mom:operationalState ?operationalState .
    OPTIONAL {{ ?space mom:dynamicState ?dynamicState }}
    OPTIONAL {{ ?space mom:endpointHealth ?endpointHealth }}
    FILTER(CONTAINS(STR(?space), "{space_id}"))
  }}
}}
"""
    try:
        resp = httpx.get(
            f"{OXIGRAPH_URL}/query",
            params={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        bindings = data.get("results", {}).get("bindings", [])
        if not bindings:
            return None
        b = bindings[0]
        return {
            "operational_state": b.get("operationalState", {}).get("value"),
            "dynamic_state": b.get("dynamicState", {}).get("value"),
            "endpoint_health": b.get("endpointHealth", {}).get("value"),
        }
    except httpx.ConnectError:
        return {"error": f"Cannot reach Oxigraph at {OXIGRAPH_URL}"}
    except Exception as e:
        return {"error": str(e)}


# ── Layer 4: Rendered GeoJSON ─────────────────────────────────────────────────

def read_geojson(space_id: str = CANARY_SPACE_ID) -> dict | None:
    if not GEOJSON_FILE.exists():
        return None
    try:
        data = json.loads(GEOJSON_FILE.read_text())
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            if props.get("id") == space_id:
                return {
                    "status": props.get("status"),
                    "open_now": props.get("open_now"),
                    "operational_state": props.get("operational_state"),
                    "endpoint_health": props.get("endpoint_health"),
                    "last_updated": props.get("last_updated"),
                    "last_fetched": props.get("last_fetched"),
                }
        return None
    except Exception as e:
        return {"error": str(e)}


# ── Isolation check ───────────────────────────────────────────────────────────

def check_isolation() -> tuple[bool, str]:
    """Verify no canary triples leaked into production space graphs."""
    sparql = """
SELECT (COUNT(?s) AS ?count) WHERE {
  GRAPH ?g {
    ?s ?p ?o .
    FILTER(CONTAINS(STR(?s), "canary"))
  }
  FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
}
"""
    try:
        resp = httpx.get(
            f"{OXIGRAPH_URL}/query",
            params={"query": sparql},
            headers={"Accept": "application/sparql-results+json"},
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
        bindings = data.get("results", {}).get("bindings", [])
        count = int(bindings[0]["count"]["value"]) if bindings else 0
        if count == 0:
            return True, "No canary triples in production graphs"
        return False, f"{count} canary triples found in production space graphs — LEAK!"
    except httpx.ConnectError:
        return None, f"Cannot reach Oxigraph at {OXIGRAPH_URL}"
    except Exception as e:
        return None, str(e)


# ── Report ────────────────────────────────────────────────────────────────────

def render_report(db_path: str) -> None:
    print(f"\n{BOLD}━━ Mother Sands Canary Coherence Report ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")

    # Layer 1
    print(f"\n{BOLD}[1] Endpoint file{RESET}  ({SERVED_FILE.relative_to(REPO_ROOT)})")
    payload = read_endpoint_file()
    ep = extract_endpoint_state(payload)
    print(f"    space: {payload.get('space')}")
    print(f"    state.open: {ep['open_now']}")
    print(f"    simulatedAge: {ep['simulated_age']}")
    print(f"    operatorDeclaredClosed: {ep['operator_declared_closed']}")

    # Layer 2
    print(f"\n{BOLD}[2] Heartbeat log{RESET}  ({db_path})")
    hb = read_heartbeat_log(db_path)
    if hb is None:
        print(f"    {_warn('No row for mother-sands — has heartbeat run yet?')}")
    elif "error" in hb:
        print(f"    {_fail(hb['error'])}")
    else:
        print(f"    endpoint_health:  {hb['endpoint_health']}")
        print(f"    lifecycle_state:  {hb['lifecycle_state']}")
        print(f"    open_now:         {hb['open_now']}")
        print(f"    effective_marker: {hb['effective_marker']}")
        print(f"    last_fetched:     {hb['last_fetched']}")

    # Layer 3
    print(f"\n{BOLD}[3] Oxigraph SPARQL{RESET}  (GRAPH <{CANARY_GRAPH}>)")
    ox = read_oxigraph()
    if ox is None:
        print(f"    {_warn('No data in <urn:mak:canary> — canary not seeded into Oxigraph yet')}")
    elif "error" in ox:
        print(f"    {_fail(ox['error'])}")
    else:
        print(f"    mom:operationalState: {ox['operational_state']}")
        print(f"    mom:dynamicState:     {ox['dynamic_state']}")
        print(f"    mom:endpointHealth:   {ox['endpoint_health']}")

    # Layer 4
    print(f"\n{BOLD}[4] Rendered GeoJSON{RESET}  ({GEOJSON_FILE.relative_to(REPO_ROOT)})")
    geo = read_geojson()
    if geo is None:
        print(f"    {_warn('mother-sands not found in spaces.geojson — not yet materialized')}")
    elif "error" in geo:
        print(f"    {_fail(geo['error'])}")
    else:
        print(f"    status:            {geo['status']}")
        print(f"    open_now:          {geo['open_now']}")
        print(f"    operational_state: {geo['operational_state']}")
        print(f"    endpoint_health:   {geo['endpoint_health']}")

    # Isolation check
    print(f"\n{BOLD}[isolation]{RESET}")
    isolated, iso_msg = check_isolation()
    if isolated is True:
        print(f"    {_ok(iso_msg)}")
    elif isolated is False:
        print(f"    {_fail(iso_msg)}")
    else:
        print(f"    {_warn(iso_msg)}")

    # Divergence detection
    print(f"\n{BOLD}━━ Divergence analysis ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{RESET}")
    divergences = []
    if ox and "error" in ox:
        print(f"  {_warn('Oxigraph unavailable — heartbeat↔Oxigraph divergence check skipped')}")
    if hb and "error" not in hb and ox and "error" not in ox:
        if hb["lifecycle_state"] != ox.get("operational_state"):
            divergences.append(
                f"lifecycle: heartbeat_log={hb['lifecycle_state']!r} vs "
                f"Oxigraph={ox.get('operational_state')!r}"
            )
        if hb["endpoint_health"] != ox.get("endpoint_health"):
            divergences.append(
                f"endpoint_health: heartbeat_log={hb['endpoint_health']!r} vs "
                f"Oxigraph={ox.get('endpoint_health')!r}"
            )
    if hb and "error" not in hb and geo and "error" not in geo:
        if hb["lifecycle_state"] != geo.get("operational_state"):
            divergences.append(
                f"lifecycle: heartbeat_log={hb['lifecycle_state']!r} vs "
                f"GeoJSON={geo.get('operational_state')!r}"
            )
        if hb["effective_marker"] != geo.get("status"):
            divergences.append(
                f"marker: heartbeat_log={hb['effective_marker']!r} vs "
                f"GeoJSON status={geo.get('status')!r}"
            )

    if divergences:
        for d in divergences:
            print(f"  {_fail(d)}")
    else:
        print(f"  {_ok('No layer divergences detected')}")

    print()


def main():
    parser = argparse.ArgumentParser(description="Mother Sands canary coherence report")
    parser.add_argument("--db", default=None, help="Path to heartbeat_log.db")
    args = parser.parse_args()

    db_path = args.db or os.environ.get("HEARTBEAT_DB_PATH") or str(
        REPO_ROOT / "data" / "tasks" / "heartbeat_log.db"
    )
    render_report(db_path)


if __name__ == "__main__":
    main()
