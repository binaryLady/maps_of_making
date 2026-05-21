#!/usr/bin/env python3
"""One-shot scrub of legacy Story 3.10 orphan triples + snapshot graphs.

Deletes the predicates the unified pipeline no longer writes, and DROPs every
per-day snapshot graph (`urn:mak:space/<slug>/<date>`). Idempotent — safe to
re-run.

Usage:
  python3 scripts/scrub_legacy_oxigraph.py [--endpoint http://localhost:7878] [--dry-run]
"""
from __future__ import annotations

import argparse
import sys

import httpx

DEAD_PREDICATES = [
    "rawContent",
    "snapshotDate",
    "snapshotSummary",
    "lastHttpStatus",
    "rawTruncated",
    "operationalState",
    "lastFetched",
    "endpointHealth",
    "lifecycleState",
    "lastEffectiveMarker",
    "lastUpdated",  # superseded by mom:updatedAt
]

MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"


def _post(endpoint: str, sparql: str, method: str) -> None:
    url = f"{endpoint.rstrip('/')}/{method}"
    ct = "application/sparql-update" if method == "update" else "application/sparql-query"
    resp = httpx.post(url, content=sparql, headers={"Content-Type": ct,
                                                     "Accept": "application/sparql-results+json"},
                      timeout=60.0)
    resp.raise_for_status()
    if method == "query":
        return resp.json()


def delete_dead_predicates(endpoint: str, dry_run: bool) -> None:
    for pred in DEAD_PREDICATES:
        sparql = f"""PREFIX mom: <{MOM}>
DELETE WHERE {{ GRAPH ?g {{ ?s mom:{pred} ?o }} }}"""
        if dry_run:
            print(f"[dry-run] would delete all mom:{pred} triples across every graph")
        else:
            _post(endpoint, sparql, "update")
            print(f"deleted mom:{pred} triples")


def drop_snapshot_graphs(endpoint: str, dry_run: bool) -> None:
    # Enumerate every urn:mak:space/<slug>/<date> snapshot graph.
    sparql = """SELECT DISTINCT ?g WHERE {
  GRAPH ?g { ?s ?p ?o }
  FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
  FILTER(REGEX(STR(?g), "/[0-9]{4}-[0-9]{2}-[0-9]{2}$"))
}"""
    result = _post(endpoint, sparql, "query")
    graphs = [b["g"]["value"] for b in result.get("results", {}).get("bindings", [])]
    if not graphs:
        print("no snapshot graphs found")
        return
    for g in graphs:
        if dry_run:
            print(f"[dry-run] would DROP GRAPH <{g}>")
        else:
            _post(endpoint, f"DROP GRAPH <{g}>", "update")
            print(f"dropped <{g}>")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoint", default="http://localhost:7878",
                    help="Oxigraph base URL (no /update or /query suffix)")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    try:
        delete_dead_predicates(args.endpoint, args.dry_run)
        drop_snapshot_graphs(args.endpoint, args.dry_run)
    except httpx.HTTPError as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    print("✓ scrub complete")


if __name__ == "__main__":
    main()
