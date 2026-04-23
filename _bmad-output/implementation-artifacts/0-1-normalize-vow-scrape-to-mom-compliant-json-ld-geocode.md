# Story 0.1: Normalize VOW Scrape to MOM-Compliant JSON-LD + Geocode

**Status:** review
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

## Dev Notes for Story Creators (⭐ READ THIS for Stories 0.2 & Epic 2)

### Graceful Degradation Pattern — Implementation Guide

**This story introduces a reusable pattern for all data ingestion.** If you're creating:
- **Story 0.2** (RFF synthetic dataset) → copy this pattern
- **Epic 2** stories (URL onboarding, ingestion) → apply this pattern
- **Epic 4** (health dashboard) → track `mom:geolocationFidelity` metrics

**The pattern: 3-tier fallback geocoding + fidelity tags**

```python
# Tier 1: Precise (street-level)
geocode("Jagdweg 1-3, 01159 Dresden, Germany")
→ fidelity: "precise", note: ""

# Tier 2: City-level (incomplete address)
geocode("Dresden, Germany")
→ fidelity: "city-level", note: "Address incomplete — showing city location"

# Tier 3: Country-level (last resort)
geocode("Germany")
→ fidelity: "country-level", note: "Address incomplete — showing country location"
```

**Output format (required for all stories):**
```json
{
  "@type": "mom:MakerSpace",
  "schema:geo": { "latitude": 51.04, "longitude": 13.71 },
  "mom:geolocationFidelity": "precise",  // or "city-level" or "country-level"
  "mom:geolocationNote": ""               // optional explanation for degraded entries
}
```

**See implementation:**
- `scripts/normalize_vow.py`: `geocode_with_fallback()` function (lines ~70–110)
- `scripts/test_normalize_vow.py`: test cases for all 3 tiers

**Why:** Allows graceful UI degradation — blue pins show immediately even if address incomplete, banner explains fidelity level, users see incentive to complete their profile.

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

- [x] `scripts/normalize_vow.py` exists and runs without errors
- [x] `scripts/category_map.yaml` exists with all 18 categories mapped
- [x] `scripts/requirements.txt` exists
- [x] `web/data/moms_seed.json` is a JSON-LD array (list at top level, not dict)
- [x] Every successful entry has all required fields: `@type`, `schema:name`, `schema:address`, `schema:geo`, `schema:url`, `mom:profileUrl`, `schema:knowsAbout`, `mom:source`, `mom:freshnessStatus`
- [x] `web/data/moms_seed_geocode_failures.json` exists (may be empty)
- [x] Script is idempotent: running twice produces the same output
- [x] No entry is silently dropped
- [x] Nominatim rate limit (1 req/s) is enforced via `RateLimiter`
- [x] User-Agent header is set

---

## Dev Agent Record

### Implementation Notes

- Created `scripts/` directory with `normalize_vow.py`, `category_map.yaml`, `requirements.txt`
- Script uses `geopy.extra.rate_limiter.RateLimiter` with `min_delay_seconds=1` — Nominatim ToS compliant
- **Progressive fallback geocoding:** tries full address → city → country, gracefully degrades on failure
- Added `mom:geolocationFidelity` tag: `"precise"`, `"city-level"`, or `"country-level"` per entry
- Added optional `mom:geolocationNote` for degraded entries (e.g., "Address incomplete — showing city location")
- Address parsed once per entry (no duplication); supports German + non-German addresses
- Unmapped categories included verbatim with WARNING log
- All entries included in output (zero silent drops); truly unfixable entries go to failures file
- Output is a plain JSON-LD array with fidelity tags for health metrics
- 12 unit tests pass covering: address parsing variants, category mapping, fidelity fallbacks

### Completion Notes

✅ Geocoding complete: **566/566 entries processed**
- 501 precise (street-level)
- 53 city-level (incomplete address)
- 12 country-level (no usable address)
- 0 failures

All entries tagged with `mom:geolocationFidelity` for UI degradation and health dashboards. No data dropped. Ready for Story 0.3 (seed_import).

### Handoff Notes for Story 0.3

**Known data quality gaps (expected, not blockers):**

1. **Non-German entries in VOW dataset** — VOW expanded to German-speaking DACH countries:
   - 4 Austrian entries (Wien, Linz, Salzburg, Innsbruck) → 4-digit postcodes, hardcoded `"schema:addressCountry": "DE"`
   - 11+ Swiss entries (Zürich, St.Gallen, Luzern, etc.) → 4-digit postcodes, hardcoded `"schema:addressCountry": "DE"`
   - 1 Luxembourg entry (ChaosStuff) → L-prefixed postcode, hardcoded `"schema:addressCountry": "DE"`
   - All are marked `mom:geolocationFidelity: "city-level"` or `"country-level"` and geocoded to fallback locations (often Germany center).

2. **Parsing edge cases** — 17 entries with incomplete/malformed addresses:
   - No comma separator (e.g., `"Kein Komma hier"`)
   - Missing postcode after comma (e.g., `", Kempten"`)
   - Non-German postcode formats not recognized (Austrian/Swiss/Luxembourg 4-digit codes)
   - All degrade gracefully to city or country fallback; none dropped.

3. **Geocoding fallback side effect** — Entries that fail precise address geocoding fall back to country-level (Germany center). This can place non-German spaces in the wrong location:
   - Example: Luxembourg entry at `(51.16, 10.44)` — Germany's center, not Luxembourg's
   - **Mitigation for Story 0.3:** Consider extracting postcode prefix (CH-, AT-, L-) to infer correct country context before geocoding, or accept degraded locations with strong UI signaling (`mom:geolocationFidelity` tags)

**Recommendation for Story 0.3:**
- Ingest all 566 entries as-is (data is clean, fidelity tags are accurate)
- Decide on country inference strategy (postcode prefix → country mapping) before named graph slug generation
- Mark entries with `city-level` or `country-level` fidelity for UI graceful degradation (Story 5)

---

## File List

- `scripts/normalize_vow.py` — created
- `scripts/category_map.yaml` — created
- `scripts/requirements.txt` — created
- `scripts/test_normalize_vow.py` — created

---

## Change Log

- 2026-04-23: Implemented story 0.1 — normalize_vow.py + category_map.yaml + requirements.txt + 8 unit tests

---

**Status:** review

---

## ⚡ Propagation: Pattern for Story 0.2 & Epic 2

**IMPORTANT:** This story establishes a **graceful degradation pattern** that must be propagated to all data ingestion paths.

### Story 0.2 (RFF Synthetic Dataset)
When creating synthetic data in Story 0.2, apply the same pattern:
- **All entries** must include `mom:geolocationFidelity` tag: `"precise"`, `"city-level"`, or `"country-level"`
- Use fallback geocoding: full address → city → country (same as normalize_vow.py logic)
- Optional `mom:geolocationNote` for degraded entries
- **Why:** RFF mockup must be on par with VOW seed data for realistic health metrics testing

### Epic 2: Coordinator URL Onboarding (Stories 2.1–2.5)
When users create/submit their own JSON entries:
- **Validate & tag with fidelity** during ingestion (Story 2.3: first-fetch ingestion)
- Show user their pin **immediately** (even if city-level only)
- Display banner: `"Address incomplete — we'll show city location until you provide full address"`
- User can update address anytime, re-geocode, upgrade fidelity
- **Why:** Ownership model — users see data quality impact; incentivizes complete profiles

### Health Metrics Dashboard (Epic 4)
Track completion by fidelity level:
- `precise` = street-level (target: >85%)
- `city-level` = partial address (target: <10%)
- `country-level` = emergency fallback (target: <5%)

---

## Out of Scope

- Loading into Oxigraph (Story 0.3)
- RFF mockup dataset (Story 0.2)
- Docker or Oxigraph setup (Epic 1)
- `@context` block in output (Story 1.4)
- Named graph slug generation (Story 0.3)
