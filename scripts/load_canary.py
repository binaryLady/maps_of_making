#!/usr/bin/env python3
"""Load the Mother Sands canary into Oxigraph — clean-slate skeleton (Story 3.4b).

This is a deliberately minimal, self-contained loader. It does NOT import the
heartbeat transformer: the goal of the 3.x clean-slate pivot is a tight
`json -> card` loop with a single, readable mapping that Story 3.5 will
formalize into the three-layer schema (SpaceAPI v15 core / mom: extended /
community add-ons).

What it does:
  1. Read web/canary/mother-sands.json (SpaceAPI document).
  2. Map it to exactly the triples the map's materialization query reads
     (see _SPARQL_SELECT, urn:mak:canary UNION block in main.py).
  3. DROP + INSERT the urn:mak:canary named graph in Oxigraph.

The HTTP fetch + APScheduler + heartbeat_log conditional-GET are intentionally
bypassed — those belong to the heartbeat pipeline, not the canary baseline.

Usage:  python3 scripts/load_canary.py
Env:    OXIGRAPH_URL (default http://localhost:7878)
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# ── Three named-graph model (Story 3.4b architectural decision) ──────────────
# Oxigraph holds three classes of named graph, isolated by mutation semantics:
#
#   urn:mak:space/*        live federated endpoints   — DROP + INSERT (mutable)
#   urn:mak:canary         our own diagnostic space   — DROP + INSERT (mutable)
#   urn:mak:public_ledger  immutable public records   — INSERT DATA ONLY, never DROP
#                          (tombstones, closures, skill certs, relocations)
#
# RULE: every writer touches ONLY its own graph. Ledger writers must never DROP —
# dropping the ledger destroys the trust guarantee.
#
# public_ledger is a known-unknown (TBD): the working assumption is that public
# records are minted as IPFS-IPLD dag-json files that live on IPFS, and the
# public_ledger graph stores triples *ingested* from those dag-json documents.
# Not built here — reserved so nobody squats the URI.
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("canary.loader")  # component TAG — Epic 4 monitor consumes this

REPO_ROOT = Path(__file__).parent.parent
CANARY_FILE = REPO_ROOT / "web" / "canary" / "mother-sands.json"
OXIGRAPH_URL = os.environ.get("OXIGRAPH_URL", "http://localhost:7878").rstrip("/")

MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"
SCHEMA = "https://schema.org/"
XSD_DT = "http://www.w3.org/2001/XMLSchema#dateTime"
XSD_BOOL = "http://www.w3.org/2001/XMLSchema#boolean"

GRAPH_URI = "urn:mak:canary"
SPACE_URI = "urn:mak:canary/mother-sands"


def _lit(val: str) -> str:
    """Escape a string for a SPARQL quoted literal."""
    escaped = str(val).replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
    return f'"{escaped}"'


def _classify_lifecycle(simulated_age) -> str:
    """Minimal lifecycle classifier for the canary skeleton.

    # 3.5: formalize — canonical thresholds belong in the three-layer schema.
    simulated_age is `ext_mom.simulatedAge`: None = never confirmed (seeded),
    otherwise an integer count of days since the last content change.
    """
    if simulated_age is None:
        return "seeded"
    days = float(simulated_age)
    if days <= 14:
        return "confirmed"
    if days <= 60:
        return "aging"
    if days <= 180:
        return "zombie"
    return "dead"


def build_canary_sparql(data: dict) -> str:
    """Map a SpaceAPI served.json document to the urn:mak:canary graph triples."""
    now = datetime.now(timezone.utc).isoformat()

    name = data.get("space", "Mother Sands")
    loc = data.get("location", {})
    lat, lon = loc.get("lat"), loc.get("lon")
    if lat is None or lon is None:
        raise ValueError("canary served.json missing location.lat / location.lon")

    state = data.get("state", {})
    lifecycle = _classify_lifecycle(data.get("ext_mom", {}).get("simulatedAge"))

    triples = [
        f"<{SPACE_URI}> a <{MOM}Space> .",
        f"<{SPACE_URI}> <{SCHEMA}name> {_lit(name)} .",
        f"<{SPACE_URI}> <{SCHEMA}geo> [ <{SCHEMA}latitude> {lat} ; <{SCHEMA}longitude> {lon} ] .",
        f"<{SPACE_URI}> <{MOM}operationalState> {_lit(lifecycle)} .",
        f'<{SPACE_URI}> <{MOM}endpointHealth> "healthy" .',
        f'<{SPACE_URI}> <{MOM}source> "canary" .',
        f'<{SPACE_URI}> <{MOM}lastFetched> "{now}"^^<{XSD_DT}> .',
    ]

    # mom:lastUpdated — the lifecycle clock has only started once content is
    # confirmed; a seeded canary has never had a confirmed update.
    if lifecycle != "seeded":
        triples.append(f'<{SPACE_URI}> <{MOM}lastUpdated> "{now}"^^<{XSD_DT}> .')

    if data.get("url"):
        triples.append(f"<{SPACE_URI}> <{SCHEMA}url> <{data['url']}> .")
    if data.get("logo"):
        triples.append(f"<{SPACE_URI}> <{SCHEMA}logo> <{data['logo']}> .")

    if "open" in state:
        triples.append(
            f'<{SPACE_URI}> <{MOM}openNow> "{str(bool(state["open"])).lower()}"^^<{XSD_BOOL}> .'
        )
    if "lastchange" in state:
        change_dt = datetime.fromtimestamp(state["lastchange"], tz=timezone.utc).isoformat()
        triples.append(f'<{SPACE_URI}> <{MOM}lastOpenChange> "{change_dt}"^^<{XSD_DT}> .')

    if data.get("contact"):
        contact_json = json.dumps(data["contact"], separators=(",", ":"))
        triples.append(f"<{SPACE_URI}> <{SCHEMA}contactJson> {_lit(contact_json)} .")

    logger.info("stage=map_triples space=%s lifecycle=%s count=%d",
                name, lifecycle, len(triples))
    for t in triples:
        logger.debug("triple: %s", t)

    triples_str = "\n    ".join(triples)
    return (
        f"DROP SILENT GRAPH <{GRAPH_URI}> ;\n"
        f"INSERT DATA {{\n  GRAPH <{GRAPH_URI}> {{\n    {triples_str}\n  }}\n}}"
    )


def main() -> int:
    logging.basicConfig(
        level=os.environ.get("CANARY_LOG_LEVEL", "INFO"),
        format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
    )
    logger.info("stage=start source=%s target=%s", CANARY_FILE, OXIGRAPH_URL)

    if not CANARY_FILE.exists():
        logger.error("stage=read status=fail reason=file_not_found path=%s", CANARY_FILE)
        return 1

    data = json.loads(CANARY_FILE.read_text())
    logger.info("stage=read status=ok")

    sparql = build_canary_sparql(data)

    try:
        resp = httpx.post(
            f"{OXIGRAPH_URL}/update",
            content=sparql,
            headers={"Content-Type": "application/sparql-update"},
            timeout=10.0,
        )
        resp.raise_for_status()
    except httpx.HTTPError as e:
        logger.error("stage=oxigraph_write status=fail reason=%s", e)
        return 1

    lifecycle = _classify_lifecycle(data.get("ext_mom", {}).get("simulatedAge"))
    logger.info("stage=oxigraph_write status=ok graph=%s operationalState=%s",
                GRAPH_URI, lifecycle)
    logger.info("stage=done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
