# Story 0.2: Generate RFF Mockup Dataset for Health-Layer Demo

**Status:** ready-for-dev
**Epic:** 0 — Pilot Seed Data Pipeline
**Story Key:** 0-2-generate-rff-mockup-dataset-for-health-layer-demo
**Created:** 2026-04-23

---

## User Story

As a network admin viewing the dashboard demo,
I want the admin dashboard to show a realistic spread of endpoint health states (confirmed, stale, broken, aging) attributed to the RFF France network,
So that the demo communicates the fleet-health value proposition without polluting the real VOW onboarding data with synthetic entries.

---

## Context

This is Story 0.2, second story in Epic 0. It is a **standalone data-generation task** — no Oxigraph required (that's Epic 1 / Story 0.3). The output `web/data/rff_mockup.json` will be consumed by Story 0.3's `seed_import.py` alongside the real VOW seed.

### What already exists (from Story 0.1)

- `scripts/normalize_vow.py` — pattern reference for JSON-LD output structure and geolocationFidelity tagging
- `scripts/category_map.yaml` — canonical English category tags (reference for RFF mockup entries)
- `scripts/requirements.txt` — already has `geopy>=2.4.0` and `pyyaml>=6.0`
- `web/data/moms_seed.json` — plain JSON-LD array, 566 entries (real VOW data, do NOT touch)
- `web/data/moms_seed_geocode_failures.json` — failures log (do NOT touch)

### What this story creates

- `scripts/generate_rff_mockup.py` — generates the RFF synthetic dataset
- `web/data/rff_mockup.json` — ~20–30 synthetic French maker spaces

### Dependency note

Story 0.2 does NOT depend on Story 0.3 or Epic 1. It runs standalone. Story 0.3 will consume both `moms_seed.json` and `rff_mockup.json`.

---

## Acceptance Criteria

**Given** the `scripts/` directory exists (created in Story 0.1)
**When** `python scripts/generate_rff_mockup.py` is run from the repo root
**Then** it produces `web/data/rff_mockup.json` as a **plain JSON-LD array** (same top-level format as `moms_seed.json` — not a dict) containing ~20–30 synthetic French maker spaces with:

- Realistic French names, cities, and addresses spread across: Paris, Lyon, Marseille, Bordeaux, Toulouse
- A deliberate mix of health states:
  - ~10 `mak:confirmed` (🔵) — recent successful fetch, `last_fetched` within 7 days
  - ~8 `mak:seeded` (⚪) — never claimed, no endpoint URL
  - ~5 `mak:aging` — `last_fetched` 30–45 days ago
  - ~4 `mak:error` (🔴) — last fetch returned HTTP 404 or timeout
  - ~2 `mak:zombie` — `last_fetched` 90+ days ago
- `mom:source: "mak:mock-rff"` on **every** entry (explicit provenance flag)
- Named graph target: `"mom:namedGraph": "<urn:mak:mock/rff-health>"` on every entry
- `mom:geolocationFidelity` tag on every entry: `"precise"`, `"city-level"`, or `"country-level"` (see below)

**And** every entry has all required JSON-LD fields matching the `moms_seed.json` schema:
```
@type, schema:name, schema:address, schema:geo, schema:url, mom:profileUrl,
schema:knowsAbout, mom:source, mom:freshnessStatus, mom:geolocationFidelity,
mom:namedGraph, mom:healthState, mom:lastFetched
```

**And** the script includes this comment block at the top:
```python
# DEMO ONLY — drop this graph before production:
# docker exec oxigraph sparql --update "DROP GRAPH <urn:mak:mock/rff-health>"
```

**And** the admin dashboard demo-toggle (Epic 4, Story 4.4) can include/exclude this graph via a SPARQL `FROM NAMED <urn:mak:mock/rff-health>` clause.

**And** the script is idempotent: re-running overwrites `rff_mockup.json` cleanly.

**And** the script logs a summary on completion: `"Done: {n} RFF mockup spaces written to web/data/rff_mockup.json"`.

---

## Technical Requirements

### Files to Create

| File | Purpose |
|------|---------|
| `scripts/generate_rff_mockup.py` | Generates synthetic RFF dataset |

### Files to Write (output)

| File | Note |
|------|------|
| `web/data/rff_mockup.json` | Plain JSON-LD array of ~20–30 synthetic French spaces |

### Files to NOT Touch

| File | Reason |
|------|--------|
| `web/data/moms_seed.json` | Real VOW data — never modified by this story |
| `scripts/normalize_vow.py` | Story 0.1 script — do not modify |
| `scripts/category_map.yaml` | Read-only reference |

---

## JSON-LD Output Structure

Output must be a **top-level JSON array** — same contract as `moms_seed.json`:

```json
[
  {
    "@type": "mom:MakerSpace",
    "schema:name": "FabLab Lyon",
    "schema:address": {
      "@type": "schema:PostalAddress",
      "schema:streetAddress": "12 Rue de la République",
      "schema:postalCode": "69001",
      "schema:addressLocality": "Lyon",
      "schema:addressCountry": "FR"
    },
    "schema:geo": {
      "@type": "schema:GeoCoordinates",
      "schema:latitude": 45.7597,
      "schema:longitude": 4.8422
    },
    "schema:url": "https://fablab-lyon.example.fr",
    "mom:profileUrl": "https://repaircafe-france.org/espaces/fablab-lyon",
    "schema:knowsAbout": ["electronics", "3d-printing", "wood"],
    "mom:source": "mak:mock-rff",
    "mom:freshnessStatus": "mak:confirmed",
    "mom:namedGraph": "<urn:mak:mock/rff-health>",
    "mom:healthState": "mak:confirmed",
    "mom:lastFetched": "2026-04-16T10:00:00Z",
    "mom:geolocationFidelity": "precise"
  }
]
```

### No `@context` block — same as `moms_seed.json`

Context is managed at the ontology layer (Story 1.4). Use prefixed names directly.

---

## Health State Spec

Synthetic timestamps must be plausible relative to generation date (2026-04-23):

| Health State | Count | `mom:healthState` | `mom:lastFetched` | `schema:url` |
|---|---|---|---|---|
| confirmed | ~10 | `mak:confirmed` | within 7 days | valid HTTPS URL |
| seeded | ~8 | `mak:seeded` | absent (null/omit) | absent (null/omit) |
| aging | ~5 | `mak:aging` | 30–45 days ago | valid HTTPS URL |
| error | ~4 | `mak:error` | 7–14 days ago (last attempted) | 404 URL pattern |
| zombie | ~2 | `mak:zombie` | 90–120 days ago | valid HTTPS URL |

**Seeded entries:** omit `schema:url`, `mom:profileUrl`, and `mom:lastFetched` — these spaces have never claimed their endpoint. Use `mom:freshnessStatus: "mak:seeded"`.

**Error entries:** include a `mom:lastFetchError` field: `"HTTP 404"` or `"Connection timeout"`.

---

## Geolocation Fidelity Pattern (CRITICAL — from Story 0.1 propagation)

**Every entry must include `mom:geolocationFidelity`** — this was established in Story 0.1 and must be propagated to all data ingestion paths.

```python
# Assign based on address quality of the synthetic entry:
# - Full street address + postcode → "precise"
# - City only (seeded entries often lack full address) → "city-level"
# - Country fallback only → "country-level"
```

For synthetic data, most entries can be `"precise"` (you're generating them). Deliberately set ~3 seeded entries to `"city-level"` (address unknown, showing city center) to exercise the degraded UI path.

Optional `mom:geolocationNote` for city-level entries: `"Address unknown — showing city location"`.

**Why this matters:** The health metrics dashboard (Epic 4) tracks fidelity distribution:
- `precise` = target >85%
- `city-level` = target <10%
- `country-level` = target <5%

RFF mockup data must be realistic enough to populate these metrics meaningfully.

---

## French City Coordinates (use these directly — no geocoding needed)

Since this is synthetic data, hardcode realistic coordinates:

| City | Latitude | Longitude | Postcode prefix |
|------|----------|-----------|-----------------|
| Paris | 48.8566 | 2.3522 | 75xxx |
| Lyon | 45.7597 | 4.8422 | 69xxx |
| Marseille | 43.2965 | 5.3698 | 13xxx |
| Bordeaux | 44.8378 | -0.5792 | 33xxx |
| Toulouse | 43.6047 | 1.4442 | 31xxx |

Add ±0.02 jitter per entry to spread pins within each city (avoid exact stacking):
```python
import random
lat = base_lat + random.uniform(-0.02, 0.02)
lon = base_lon + random.uniform(-0.02, 0.02)
```

Set `mom:geolocationFidelity: "precise"` for entries with full street address.
Set `mom:geolocationFidelity: "city-level"` for seeded entries (no address → show city center).

---

## Category Selection

Use canonical English tags from `scripts/category_map.yaml`. Each space should have 2–5 tags. Example selections:

```python
FRENCH_SPACE_CATEGORIES = [
    ["electronics", "programming", "3d-printing"],
    ["wood", "metalworking", "cnc-milling"],
    ["textiles", "ceramics", "printing"],
    ["laser-cutting", "electronics"],
    ["bicycle-repair", "metalworking"],
    ["digital-media", "programming"],
    ["food", "biology-chemistry"],
    ["3d-printing", "plastics", "laser-cutting"],
]
```

---

## Naming Conventions (from Architecture)

- Python files: `snake_case` throughout
- Output file: `web/data/rff_mockup.json`
- Named graph: `<urn:mak:mock/rff-health>` (stored as string in JSON-LD field)
- `mom:source` value: `"mak:mock-rff"` (string, not a URI object)
- No `@context` block in output

---

## Script Design

The script generates data **statically** — no network calls, no geocoding API. All coordinates are hardcoded with jitter. This makes it instant and deterministic.

```python
# DEMO ONLY — drop this graph before production:
# docker exec oxigraph sparql --update "DROP GRAPH <urn:mak:mock/rff-health>"

import json
import random
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

OUTPUT_PATH = Path("web/data/rff_mockup.json")

CITIES = {
    "Paris":     {"lat": 48.8566, "lon": 2.3522,  "postcode_prefix": "750"},
    "Lyon":      {"lat": 45.7597, "lon": 4.8422,  "postcode_prefix": "690"},
    "Marseille": {"lat": 43.2965, "lon": 5.3698,  "postcode_prefix": "130"},
    "Bordeaux":  {"lat": 44.8378, "lon": -0.5792, "postcode_prefix": "330"},
    "Toulouse":  {"lat": 43.6047, "lon": 1.4442,  "postcode_prefix": "310"},
}
```

### Entry Point

```python
if __name__ == "__main__":
    import sys
    sys.exit(main())
```

### Idempotency

Always overwrites `web/data/rff_mockup.json` completely. Use `random.seed(42)` at the top of `main()` for reproducible output across runs.

---

## Anti-Pattern Prevention

- **Do NOT call Nominatim or any geocoding API** — synthetic data uses hardcoded coordinates with jitter.
- **Do NOT use the `moms_seed.json` format with a `spaces` key** — output must be a plain JSON-LD array.
- **Do NOT omit `mom:geolocationFidelity`** — every entry must have it (Story 0.1 propagation requirement).
- **Do NOT use `"schema:addressCountry": "DE"`** — French spaces must use `"FR"`.
- **Do NOT omit `mom:namedGraph`** — Story 0.3 uses this field to route entries to the correct Oxigraph named graph.
- **Do NOT add `@context`** — context is managed at the ontology layer (Story 1.4).
- **Do NOT generate random seeds per run** — use `random.seed(42)` for reproducible/idempotent output.
- **Do NOT create `scripts/venv/`** — user manages venv externally per CLAUDE.md.
- **Do NOT touch `web/data/moms_seed.json`** — that is real VOW data.

---

## Definition of Done

- [ ] `scripts/generate_rff_mockup.py` exists and runs without errors from repo root
- [ ] `web/data/rff_mockup.json` is a plain JSON-LD array (list at top level, not dict)
- [ ] ~20–30 entries present
- [ ] Health state distribution: ~10 confirmed, ~8 seeded, ~5 aging, ~4 error, ~2 zombie
- [ ] Every entry has `mom:geolocationFidelity` (`"precise"` or `"city-level"`)
- [ ] Every entry has `mom:source: "mak:mock-rff"`
- [ ] Every entry has `mom:namedGraph: "<urn:mak:mock/rff-health>"`
- [ ] All entries use `"schema:addressCountry": "FR"`
- [ ] Script is idempotent: running twice produces identical output (uses `random.seed(42)`)
- [ ] DEMO ONLY comment block present at top of script
- [ ] No geocoding API calls — all coordinates hardcoded with jitter
- [ ] Logging summary on completion: `"Done: {n} RFF mockup spaces written..."`

---

## Dev Agent Record

### Implementation Notes

_(to be filled by dev agent)_

### Completion Notes

_(to be filled by dev agent)_

### Handoff Notes for Story 0.3

_(to be filled by dev agent — note any field naming decisions, health state representation choices, or data quality flags that Story 0.3's seed_import.py needs to handle)_

---

## File List

- `scripts/generate_rff_mockup.py` — to create
- `web/data/rff_mockup.json` — to create (script output)

---

## Change Log

- 2026-04-23: Story created — RFF mockup generator for health-layer demo

---

## Out of Scope

- Loading into Oxigraph (Story 0.3)
- VOW data normalization (Story 0.1 — complete)
- Docker or Oxigraph setup (Epic 1)
- `@context` block in output (Story 1.4)
- Named graph slug generation (Story 0.3)
- Real RFF data scraping (this is synthetic/mockup only)
