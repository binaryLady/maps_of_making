# Story 0.1: Normalize VOW Scrape to MOM-Compliant JSON-LD + Geocode

**Status:** ready-for-dev
**Epic:** 0 — Pilot Seed Data Pipeline
**Story Key:** 0-1-normalize-vow-scrape-to-mom-compliant-json-ld-geocode
**Created:** 2026-04-23

---

## User Story

As a maker or coordinator,
I want the map to show real German open workshop spaces (from the VOW / offene-werkstaetten.org network) as ⚪ seeded pins,
So that the pilot map has credible density in Germany and coordinators can recognise their own space rather than seeing synthetic placeholder data.

---

## Context

This is Story 0.1, the first story in Epic 0 (Pilot Seed Data Pipeline). It is a **standalone data-processing task** — it does NOT depend on Oxigraph running yet (that's Epic 1). The output `web/data/moms_seed.json` will replace the current Phase 1 placeholder file with a proper JSON-LD array. Story 0.3 will load this output into Oxigraph.

### What already exists

- **`web/data/vow_workshops.json`** — 566 entries, already on disk. Fields per entry:
  ```json
  {
    "index": 1,
    "name": "#Rosenwerk",
    "profileUrl": "https://offene-werkstaetten.org/werkstatt/rosenwerk",
    "address": "Jagdweg 1-3, 01159 Dresden",
    "website": "https://konglomerat.org/",
    "categories": ["3D-Druck", "CNC-Fräse", "Elektronik", "Holz", ...]
  }
  ```
- **`web/data/moms_seed.json`** — currently a Phase 1 placeholder in a different format. **This file will be completely overwritten** by this story.
- **`scripts/`** directory — does NOT yet exist. This story creates it.
- No existing geocoding or normalize scripts.

### All 18 unique categories in vow_workshops.json

`3D-Druck`, `Biologie/Chemie`, `CNC-Fräse`, `Druckverfahren`, `Elektronik`, `Fahrrad`, `Fotolabor`, `Holz`, `Keramik/Töpfern`, `Kunststoff`, `Laserschneiden`, `Lebensmittel`, `Malerei`, `Metall`, `Programmieren`, `Stein`, `Textil`, `digitale Medien`

---

## Acceptance Criteria

**Given** `web/data/vow_workshops.json` contains 566 entries with fields: `name`, `address`, `website`, `profileUrl`, `categories`
**When** `scripts/normalize_vow.py` is run
**Then** it produces `web/data/moms_seed.json` as a **JSON-LD array** (not a dict) where each entry maps to:

```json
{
  "@type": "mom:MakerSpace",
  "schema:name": "<name>",
  "schema:address": {
    "@type": "schema:PostalAddress",
    "schema:streetAddress": "<street>",
    "schema:postalCode": "<postcode>",
    "schema:addressLocality": "<city>",
    "schema:addressCountry": "DE"
  },
  "schema:geo": {
    "@type": "schema:GeoCoordinates",
    "schema:latitude": 51.05,
    "schema:longitude": 13.73
  },
  "schema:url": "<website>",
  "mom:profileUrl": "<profileUrl>",
  "schema:knowsAbout": ["wood", "electronics"],
  "mom:source": "mak:scraped-vow",
  "mom:freshnessStatus": "mak:seeded"
}
```

**And** `scripts/category_map.yaml` maps all 18 German category strings to canonical English tags.

**And** entries that fail geocoding are written to `web/data/moms_seed_geocode_failures.json` (not dropped silently).

**And** the script is idempotent: re-running overwrites `moms_seed.json` cleanly.

**And** unmapped categories are logged as `WARNING` and included verbatim (never silently dropped).

---

## Technical Requirements

### Files to Create

| File | Purpose |
|------|---------|
| `scripts/normalize_vow.py` | Main normalization + geocoding script |
| `scripts/category_map.yaml` | German→English category mapping |
| `scripts/requirements.txt` | Python deps for scripts (separate from harness) |

### Files to Overwrite

| File | Note |
|------|------|
| `web/data/moms_seed.json` | Replace Phase 1 placeholder with JSON-LD array |

### New Files Created by Script at Runtime

| File | Purpose |
|------|---------|
| `web/data/moms_seed_geocode_failures.json` | Entries where Nominatim returned no result |

### Python Version and Dependencies

- Python 3.12 (matches harness Dockerfile base: `python:3.12-slim`)
- `geopy` — Nominatim geocoder (standard library for OSM geocoding)
- `pyyaml` — read `category_map.yaml`
- `requests` not needed — `geopy` handles HTTP internally

```
# scripts/requirements.txt
geopy>=2.4.0
pyyaml>=6.0
```

### Geocoding Rules (Nominatim)

- Rate limit: **1 request/second** (Nominatim ToS — mandatory)
- User-Agent header: set to `"maps-of-making-seed-pipeline/1.0 (nicolas.de.barquin@gmail.com)"` — Nominatim requires a real contact
- Query strategy: try `"<address>, Germany"` as the full query string (addresses are already German)
- On HTTP error or empty result: write entry to failures file, continue
- Do NOT use `geopy.geocoders.GoogleV3` or any paid service

```python
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter

geolocator = Nominatim(user_agent="maps-of-making-seed-pipeline/1.0 (nicolas.de.barquin@gmail.com)")
geocode = RateLimiter(geolocator.geocode, min_delay_seconds=1)
```

### Address Parsing

VOW addresses are free-form strings like `"Jagdweg 1-3, 01159 Dresden"`. Parse heuristically:
- Split on `,` — last part is `postcode + city`, first part is `streetAddress`
- Postcode regex: `\d{5}` in German addresses
- If parsing fails, put the entire string in `schema:streetAddress` and log a WARNING

### Category Mapping

All 18 categories must be covered in `scripts/category_map.yaml`:

```yaml
# German VOW category → canonical English tag
"3D-Druck": "3d-printing"
"Biologie/Chemie": "biology-chemistry"
"CNC-Fräse": "cnc-milling"
"Druckverfahren": "printing"
"Elektronik": "electronics"
"Fahrrad": "bicycle-repair"
"Fotolabor": "photography"
"Holz": "wood"
"Keramik/Töpfern": "ceramics"
"Kunststoff": "plastics"
"Laserschneiden": "laser-cutting"
"Lebensmittel": "food"
"Malerei": "painting"
"Metall": "metalworking"
"Programmieren": "programming"
"Stein": "stone"
"Textil": "textiles"
"digitale Medien": "digital-media"
```

Unmapped categories: log `WARNING: unmapped category '<cat>' — including verbatim`, add to output as-is.

### JSON-LD Output Structure

The output `web/data/moms_seed.json` must be a **top-level JSON array** (not a dict with a `spaces` key — that's the old Phase 1 format). This is consumed directly by Story 0.3's `seed_import.py`.

```json
[
  {
    "@type": "mom:MakerSpace",
    "schema:name": "...",
    ...
  },
  ...
]
```

### Naming Conventions (from Architecture)

- Python files: `snake_case` throughout
- No `@context` block in `moms_seed.json` — context is defined in `ontology/context/space.jsonld` (Story 1.4). The seed file uses prefixed names directly.
- Named graph IDs (for Story 0.3): will be `<urn:mak:space/{slug}>` where slug = kebab-case of name. The normalize script does NOT need to compute slugs — that's Story 0.3's job.

### Idempotency

Script must be safe to re-run:
- Always overwrites `web/data/moms_seed.json` completely
- Always overwrites `web/data/moms_seed_geocode_failures.json` completely
- No partial state / no caching of geocode results between runs (keep it simple for PoC)

### Logging

Use Python's standard `logging` module, not `print`:
- `INFO`: progress every 50 entries (`"Processed 50/566"`)
- `INFO`: summary on completion (`"Done: 540 geocoded, 26 failures"`)
- `WARNING`: unmapped categories, address parse failures
- `ERROR`: unexpected exceptions per entry (continue processing remaining)

---

## Anti-Pattern Prevention

- **Do NOT use the existing `moms_seed.json` format** (dict with `$schema`, `version`, `spaces` keys) — that was Phase 1 only. Output must be a plain JSON-LD array.
- **Do NOT use `requests` directly for geocoding** — use `geopy` with `RateLimiter`.
- **Do NOT skip or silently drop failed entries** — write to failures file.
- **Do NOT add `@context` to the output** — context is managed at the ontology layer.
- **Do NOT use `geopy.geocoders.Nominatim` without a user-agent** — Nominatim will block anonymous requests.
- **Do NOT store geocode cache state** — idempotency means always re-geocoding on each run (acceptable for 500 spaces at pilot scale).
- **Do NOT create a `scripts/venv/`** — user manages venv externally per `CLAUDE.md`.

---

## Implementation Notes

### Script Entry Point

```python
if __name__ == "__main__":
    import sys
    sys.exit(main())
```

Make the script runnable as `python scripts/normalize_vow.py` from the repo root.

### Progress Visibility

With 566 entries at 1 req/s, the full run takes ~10 minutes. Show progress so the user knows it's working:

```python
logging.info("Geocoding %d entries at 1 req/s — estimated %d minutes", total, total // 60)
```

### Error Handling Philosophy

Per entry: catch exceptions, log ERROR with entry name, add to failures list, continue.
Do NOT abort on individual geocode failures.

---

## Definition of Done

- [ ] `scripts/normalize_vow.py` exists and runs without errors
- [ ] `scripts/category_map.yaml` exists with all 18 categories mapped
- [ ] `scripts/requirements.txt` exists
- [ ] `web/data/moms_seed.json` is a JSON-LD array (list at top level, not dict)
- [ ] Every successful entry has all required fields: `@type`, `schema:name`, `schema:address`, `schema:geo`, `schema:url`, `mom:profileUrl`, `schema:knowsAbout`, `mom:source`, `mom:freshnessStatus`
- [ ] `web/data/moms_seed_geocode_failures.json` exists (may be empty)
- [ ] Script is idempotent: running twice produces the same output
- [ ] No entry is silently dropped
- [ ] Nominatim rate limit (1 req/s) is enforced via `RateLimiter`
- [ ] User-Agent header is set

---

## Out of Scope

- Loading into Oxigraph (Story 0.3)
- RFF mockup dataset (Story 0.2)
- Docker or Oxigraph setup (Epic 1)
- `@context` block in output (Story 1.4)
- Named graph slug generation (Story 0.3)
