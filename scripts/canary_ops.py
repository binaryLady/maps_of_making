#!/usr/bin/env python3
"""Canary mutation primitives — single mechanism for local + VPS.

Runs INSIDE the link-handler container (local: `podman exec`, VPS: `ssh … docker exec`).
The only thing that differs between environments is how this script is invoked; the logic
is identical. Replaces the inline `curl localhost:7878` / `podman exec python -c` blocks
that used to live in the Makefile (which only ever hit the LOCAL Oxigraph).

All Oxigraph/API targets are env-driven so the same call works in either environment:
  OXIGRAPH_URL          default http://oxigraph:7878   (container-internal)
  API_BASE              default http://localhost:8000  (link-handler self)
  CANARY_FILE           default /app/web/canary/mother-sands.json
  CANARY_ENDPOINT_URL   default https://mapsofmaking.org/canary/mother-sands.json (public — intended)

Subcommands:
  load            seed the canary graph from CANARY_FILE (runs load_canary.py)
  set-endpoint    [URL]   add mom:endpointUrl (simulate "claiming")
  clear-endpoint          remove mom:endpointUrl (back to seeded)
  backdate <days>         rewrite mom:updatedAt to now-N days, then rematerialize
  declare-closed          set mom:operatorDeclaredClosed=true, then rematerialize
  wipe-snapshot           delete the snapshot_store row for the canary
  clear-etag              NULL etag/last_modified so next heartbeat fetches unconditionally
  heartbeat               POST /api/heartbeat/run
  rematerialize           POST /api/rematerialize
"""
from __future__ import annotations

import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone

import httpx

# snapshot_store lives at /app (link-handler image root), not /app/scripts
sys.path.insert(0, "/app")

OXIGRAPH_URL = os.environ.get("OXIGRAPH_URL", "http://oxigraph:7878").rstrip("/")
API_BASE = os.environ.get("API_BASE", "http://localhost:8000").rstrip("/")
CANARY_FILE = os.environ.get("CANARY_FILE", "/app/web/canary/mother-sands.json")
CANARY_ENDPOINT_URL = os.environ.get(
    "CANARY_ENDPOINT_URL", "https://mapsofmaking.org/canary/mother-sands.json"
)

MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"
XSD_DT = "http://www.w3.org/2001/XMLSchema#dateTime"
XSD_BOOL = "http://www.w3.org/2001/XMLSchema#boolean"
GRAPH = "urn:mak:canary"
SPACE = "urn:mak:canary/mother-sands"
UID = "mother-sands"


def _sparql_update(update: str) -> None:
    resp = httpx.post(
        f"{OXIGRAPH_URL}/update",
        content=update,
        headers={"Content-Type": "application/sparql-update"},
        timeout=10.0,
    )
    resp.raise_for_status()


def _api_post(path: str, timeout: float) -> None:
    r = httpx.post(f"{API_BASE}{path}", timeout=timeout)
    print(f"{path}: {r.status_code}")


def _snapshot_db():
    from snapshot_store import _get_db_path  # noqa: WPS433

    return _get_db_path()


def cmd_load() -> int:
    # load_canary.py honors CANARY_FILE / OXIGRAPH_URL / CANARY_ENDPOINT_URL from env.
    # PYTHONPATH spans /app (pipeline_helpers, snapshot_store) + /app/scripts (spaceapi_extract).
    # Force OXIGRAPH_URL to our resolved container-internal value (load_canary defaults to
    # localhost, which is wrong inside the container).
    env = dict(os.environ)
    env["PYTHONPATH"] = "/app:/app/scripts" + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    env["OXIGRAPH_URL"] = OXIGRAPH_URL
    env["CANARY_FILE"] = CANARY_FILE
    env["CANARY_ENDPOINT_URL"] = CANARY_ENDPOINT_URL
    return subprocess.call([sys.executable, "/app/scripts/load_canary.py"], env=env)


def cmd_set_endpoint(url: str | None) -> int:
    target = url or CANARY_ENDPOINT_URL
    _sparql_update(
        f"PREFIX mom: <{MOM}> "
        f"DELETE WHERE {{ GRAPH <{GRAPH}> {{ <{SPACE}> mom:endpointUrl ?u }} }} ; "
        f"INSERT DATA {{ GRAPH <{GRAPH}> {{ <{SPACE}> mom:endpointUrl <{target}> }} }}"
    )
    print(f"✓ endpointUrl set to {target}")
    return 0


def cmd_clear_endpoint() -> int:
    _sparql_update(
        f"PREFIX mom: <{MOM}> "
        f"DELETE WHERE {{ GRAPH <{GRAPH}> {{ <{SPACE}> mom:endpointUrl ?u }} }} ; "
        f"DELETE WHERE {{ GRAPH <{GRAPH}> {{ <{SPACE}> mom:updatedAt ?t }} }} ; "
        f"DELETE WHERE {{ GRAPH <{GRAPH}> {{ <{SPACE}> mom:observedAt ?o }} }}"
    )
    print("✓ endpointUrl + freshness tokens removed — canary is seeded")
    return 0


def cmd_backdate(days: int) -> int:
    ts = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%dT%H:%M:%SZ")
    _sparql_update(
        f"PREFIX mom: <{MOM}> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> "
        f"DELETE WHERE {{ GRAPH <{GRAPH}> {{ <{SPACE}> mom:updatedAt ?t }} }} ; "
        f'INSERT DATA {{ GRAPH <{GRAPH}> {{ <{SPACE}> mom:updatedAt "{ts}"^^xsd:dateTime }} }}'
    )
    print(f"✓ mom:updatedAt back-dated to {ts} ({days}d ago)")
    _api_post("/api/rematerialize", 30.0)
    return 0


def cmd_declare_closed() -> int:
    _sparql_update(
        f"PREFIX mom: <{MOM}> PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> "
        f"DELETE WHERE {{ GRAPH <{GRAPH}> {{ <{SPACE}> mom:operatorDeclaredClosed ?c }} }} ; "
        f'INSERT DATA {{ GRAPH <{GRAPH}> {{ <{SPACE}> mom:operatorDeclaredClosed "true"^^xsd:boolean }} }}'
    )
    print("✓ mom:operatorDeclaredClosed=true (terminal-by-declaration)")
    _api_post("/api/rematerialize", 30.0)
    return 0


def _sqlite_exec(sql: str, label: str) -> int:
    import sqlite3

    db = _snapshot_db()
    try:
        con = sqlite3.connect(db)
        con.execute(sql)
        con.commit()
        con.close()
        print(f"✓ {label}")
    except Exception as e:  # noqa: BLE001
        print(f"  ({label} skipped — {e})")
    return 0


def cmd_wipe_snapshot() -> int:
    return _sqlite_exec(
        f"DELETE FROM snapshots WHERE uid='{UID}'", "snapshot_store row cleared"
    )


def cmd_clear_etag() -> int:
    return _sqlite_exec(
        f"UPDATE snapshots SET etag=NULL, last_modified=NULL WHERE uid='{UID}'",
        "snapshot ETag/Last-Modified cleared (next fetch unconditional)",
    )


def cmd_heartbeat() -> int:
    _api_post("/api/heartbeat/run", 180.0)
    return 0


def cmd_rematerialize() -> int:
    _api_post("/api/rematerialize", 30.0)
    return 0


def main(argv: list[str]) -> int:
    if not argv:
        print(__doc__)
        return 1
    cmd, rest = argv[0], argv[1:]
    dispatch = {
        "load": lambda: cmd_load(),
        "set-endpoint": lambda: cmd_set_endpoint(rest[0] if rest else None),
        "clear-endpoint": lambda: cmd_clear_endpoint(),
        "backdate": lambda: cmd_backdate(int(rest[0])),
        "declare-closed": lambda: cmd_declare_closed(),
        "wipe-snapshot": lambda: cmd_wipe_snapshot(),
        "clear-etag": lambda: cmd_clear_etag(),
        "heartbeat": lambda: cmd_heartbeat(),
        "rematerialize": lambda: cmd_rematerialize(),
    }
    if cmd not in dispatch:
        print(f"unknown command: {cmd}\n{__doc__}")
        return 2
    return dispatch[cmd]()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
