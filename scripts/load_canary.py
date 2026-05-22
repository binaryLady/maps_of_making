#!/usr/bin/env python3
"""Load the Mother Sands canary into Oxigraph — clean-slate skeleton (Story 3.4b).

What it does:
  1. Read web/canary/mother-sands.json (SpaceAPI document).
  2. Map it to triples via the bundle-aligned extractor (spaceapi_extract).
  3. DROP + INSERT the urn:mak:canary named graph in Oxigraph.

The HTTP fetch + APScheduler + heartbeat_log conditional-GET are intentionally
bypassed — those belong to the heartbeat pipeline, not the canary baseline.
Freshness axis predicates (observedAt, updatedAt, openNow, lastOpenChange) are
written by the heartbeat pipeline; this loader seeds the payload fields only.

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

sys.path.insert(0, str(Path(__file__).parent))
from spaceapi_extract import escape_literal, extract_core, extract_mom, triples_for

# ── Three named-graph model (Story 3.4b architectural decision) ──────────────
# Oxigraph holds three classes of named graph, isolated by mutation semantics:
#
#   urn:mak:space/*        live federated endpoints   — DROP + INSERT (mutable)
#   urn:mak:canary         our own diagnostic space   — DROP + INSERT (mutable)
#   urn:mak:public_ledger  immutable public records   — INSERT DATA ONLY, never DROP
#
# RULE: every writer touches ONLY its own graph. Ledger writers must never DROP.
# ─────────────────────────────────────────────────────────────────────────────

logger = logging.getLogger("canary.loader")

REPO_ROOT = Path(__file__).parent.parent
CANARY_FILE = REPO_ROOT / "web" / "canary" / "mother-sands.json"
OXIGRAPH_URL = os.environ.get("OXIGRAPH_URL", "http://localhost:7878").rstrip("/")

MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"
XSD_DT = "http://www.w3.org/2001/XMLSchema#dateTime"

GRAPH_URI = "urn:mak:canary"
SPACE_URI = "urn:mak:canary/mother-sands"
CANARY_ENDPOINT = os.environ.get(
    "CANARY_ENDPOINT_URL",
    "https://mapsofmaking.org/canary/mother-sands.json",
)


def _classify_lifecycle(simulated_age) -> str:
    """Minimal lifecycle classifier for the canary skeleton.

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
    """Map a SpaceAPI document to the urn:mak:canary graph triples.

    Uses the bundle-aligned extractor for payload fields. Loader-owned
    envelope triples (operationalState, source, endpointUrl, lastFetched)
    are assembled separately. Freshness axis predicates (observedAt, updatedAt,
    openNow, lastOpenChange) are the heartbeat pipeline's responsibility.
    """
    loc = data.get("location", {})
    lat, lon = loc.get("lat"), loc.get("lon")
    if lat is None or lon is None:
        raise ValueError("canary served.json missing location.lat / location.lon")

    now = datetime.now(timezone.utc).isoformat()
    lifecycle = _classify_lifecycle(data.get("ext_mom", {}).get("simulatedAge"))

    # Loader-owned envelope — not extractable from the payload
    envelope = [
        f"<{SPACE_URI}> a <{MOM}Space> .",
        f"<{SPACE_URI}> <{MOM}operationalState> {escape_literal(lifecycle)} .",
        f'<{SPACE_URI}> <{MOM}endpointHealth> "healthy" .',
        f'<{SPACE_URI}> <{MOM}source> "canary" .',
        f"<{SPACE_URI}> <{MOM}endpointUrl> <{CANARY_ENDPOINT}> .",
        f'<{SPACE_URI}> <{MOM}lastFetched> "{now}"^^<{XSD_DT}> .',
    ]
    if lifecycle != "seeded":
        # mom:updatedAt (Axis B) bootstrapped at load time; heartbeat overwrites on content change
        envelope.append(f'<{SPACE_URI}> <{MOM}updatedAt> "{now}"^^<{XSD_DT}> .')

    # Payload fields via extractor (core + mom)
    core_fields = extract_core(data)
    mom_fields = extract_mom(data)
    payload_triples = triples_for(SPACE_URI, core_fields) + triples_for(SPACE_URI, mom_fields)

    all_triples = envelope + payload_triples

    logger.info("stage=map_triples space=%s lifecycle=%s count=%d",
                data.get("space", "Mother Sands"), lifecycle, len(all_triples))
    for t in all_triples:
        logger.debug("triple: %s", t)

    triples_str = "\n    ".join(all_triples)
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
