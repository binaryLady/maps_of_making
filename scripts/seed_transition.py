#!/usr/bin/env python3
"""
Admin utility: audit self-registered spaces in Oxigraph.

Default (read-only): print table of spaces confirmed via coordinator URL onboarding.
--mark-done: annotate matching entries in a seed file with "confirmed": true.

Usage:
  source venv/bin/activate
  python scripts/seed_transition.py
  python scripts/seed_transition.py --mark-done --seed-file web/data/rff_mockup.json
"""

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path

import httpx

REPO_ROOT = Path(__file__).parent.parent
OXIGRAPH_ENDPOINT = os.getenv("OXIGRAPH_ENDPOINT", "http://localhost:7878")

_QUERY = """PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>

SELECT ?spaceUri ?name ?endpointUrl ?lastFetched
WHERE {
  GRAPH ?g {
    ?spaceUri mom:operationalState "confirmed" ;
              mom:source "self-registered" .
    OPTIONAL { ?spaceUri schema:name ?name }
    OPTIONAL { ?spaceUri mom:endpointUrl ?endpointUrl }
    OPTIONAL { ?spaceUri mom:lastFetched ?lastFetched }
  }
  FILTER (STRSTARTS(STR(?g), "urn:mak:space/"))
}
ORDER BY ?spaceUri"""


def fetch_confirmed() -> list[dict]:
    url = OXIGRAPH_ENDPOINT.rstrip("/") + "/query"
    resp = httpx.post(
        url,
        content=_QUERY,
        headers={
            "Content-Type": "application/sparql-query",
            "Accept": "application/sparql-results+json",
        },
        timeout=30.0,
    )
    resp.raise_for_status()
    return resp.json().get("results", {}).get("bindings", [])


def print_table(bindings: list[dict]) -> None:
    if not bindings:
        print("No self-registered confirmed spaces found.")
        return
    col_w = [50, 30, 60, 30]
    header = f"{'space_uri':<{col_w[0]}} {'name':<{col_w[1]}} {'endpoint_url':<{col_w[2]}} {'confirmed_at':<{col_w[3]}}"
    print(header)
    print("-" * sum(col_w))
    for b in bindings:
        uri = b.get("spaceUri", {}).get("value", "")
        name = b.get("name", {}).get("value", "")
        ep = b.get("endpointUrl", {}).get("value", "")
        ts = b.get("lastFetched", {}).get("value", "")
        print(f"{uri:<{col_w[0]}} {name:<{col_w[1]}} {ep:<{col_w[2]}} {ts:<{col_w[3]}}")


def mark_done(bindings: list[dict], seed_file: Path) -> None:
    if not seed_file.exists():
        print(f"ERROR: seed file not found: {seed_file}", file=sys.stderr)
        sys.exit(1)

    entries = json.loads(seed_file.read_text())
    confirmed_names = {b.get("name", {}).get("value", "") for b in bindings if b.get("name")}

    patched = 0
    for entry in entries:
        entry_name = entry.get("schema:name", "")
        if entry_name in confirmed_names:
            if not entry.get("confirmed"):
                entry["confirmed"] = True
                patched += 1

    # Atomic write: write to a temp file in the same directory, then rename
    content = json.dumps(entries, indent=2, ensure_ascii=False)
    with tempfile.NamedTemporaryFile("w", dir=seed_file.parent, suffix=".tmp", delete=False, encoding="utf-8") as tf:
        tf.write(content)
        tmp_path = Path(tf.name)
    tmp_path.replace(seed_file)
    print(f"Patched {patched} entries in {seed_file} with \"confirmed\": true")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--mark-done", action="store_true", help="Annotate matched seed entries with confirmed=true")
    parser.add_argument("--seed-file", default="web/data/moms_seed.json",
                        help="Path to seed JSON file to patch (relative to repo root). "
                             "Use web/data/rff_mockup.json for test/RFF spaces.")
    args = parser.parse_args()

    try:
        bindings = fetch_confirmed()
    except Exception as e:
        print(f"ERROR querying Oxigraph at {OXIGRAPH_ENDPOINT}: {e}", file=sys.stderr)
        return 1

    print_table(bindings)

    if args.mark_done:
        seed_path = REPO_ROOT / args.seed_file
        mark_done(bindings, seed_path)

    return 0


if __name__ == "__main__":
    sys.exit(main())
