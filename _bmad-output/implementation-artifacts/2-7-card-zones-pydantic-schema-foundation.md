# Story 2.7: Card Zones + Pydantic Schema Foundation

Status: done

## Story

As a maker or coordinator viewing a space detail card,
I want to see clearly separated zones — identity, curated data, and raw source — and as a coordinator I want honest feedback about what my endpoint unlocks,
So that I can trust what the map shows me and know exactly what to improve in my data file.

**Data flow clarified:** `URL → fetch → Pydantic validation → Oxigraph (curated fields + raw snapshot) → card (Zone 2 from Oxigraph, Zone 3 from raw snapshot)`

The current raw JSON panel (`jsonForSpace()`) is a lie — it reconstructs a fake JSON from GeoJSON properties, not the actual endpoint content. This story fixes that by persisting the raw payload at ingestion time and displaying it honestly.

## Acceptance Criteria

### AC1 — Pydantic schema with subset classification

**Given** `POST /api/register-url` or `POST /api/validate-url` is called

**When** the endpoint JSON is fetched successfully

**Then** it is validated through a Pydantic `SpaceAPISchema` model before any other processing

**And** the validation response includes a `subset` field indicating the highest subset reached:

```json
{
  "reachable": true,
  "subset": "mom:card",
  "subset_score": 2,
  "missing_card_fields": ["schema:openingHours"],
  "unlock_message": "Add schema:openingHours to fully unlock the detail card.",
  "next_subset": "spaceapi:compatible",
  "next_unlock": "Full interoperability with SpaceAPI-compatible maps (mapall.space etc.)"
}
```

**And** the Pydantic model defines subsets as:

| Subset | `subset_score` | Required fields |
|---|---|---|
| `none` | 0 | (validation failed) |
| `mom:required` | 1 | `schema:name` (or `name`), `schema:geo.latitude`, `schema:geo.longitude` |
| `mom:card` | 2 | + `schema:url` (website), `schema:openingHours` |
| `spaceapi:compatible` | 3 | + `api_compatibility`, `logo`, `contact`, `url` (SpaceAPI v14 required set) |

**And** `missing_card_fields` lists the specific field names the coordinator needs to add to reach the next subset

**And** the `unlock_message` is human-readable, suitable for display in the validation UI

### AC2 — Raw endpoint JSON stored in snapshot graph

**Given** `POST /api/register-url` runs successfully

**When** the snapshot graph is written to Oxigraph

**Then** in addition to existing `mom:snapshotDate`, `mom:snapshotSummary`, `mom:lastHttpStatus`, a new triple is written:

```sparql
<{space_uri}> mom:rawContent "{escaped_json_string}"^^xsd:string .
```

**And** `rawContent` is the full JSON response from the endpoint, serialised as a compact JSON string (no pretty-printing — storage efficiency), escaped for SPARQL string insertion

**And** the content is capped at 50 KB — if the endpoint response exceeds this, store a truncation notice: `"[TRUNCATED: response exceeded 50KB]"` and log a WARNING

**And** existing snapshot graph write logic is unchanged — this is an additive triple

### AC3 — `GET /api/space/{space_id}/raw` endpoint

**Given** a `space_id` slug (e.g. `fablab-brussels`)

**When** `GET /api/space/{space_id}/raw` is called

**Then** the link_handler queries Oxigraph for the most recent snapshot graph containing `mom:rawContent`:

```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
SELECT ?rawContent ?snapshotDate
WHERE {
  GRAPH ?graph {
    <urn:mak:space/{space_id}> mom:rawContent ?rawContent ;
                               mom:snapshotDate ?snapshotDate .
  }
  FILTER(STRSTARTS(STR(?graph), "urn:mak:space/{space_id}/"))
}
ORDER BY DESC(?snapshotDate)
LIMIT 1
```

**And** returns:
```json
{ "raw": { ...parsed JSON object... }, "snapshot_date": "2026-04-27", "source": "cached" }
```

**And** if no `rawContent` exists (seeded space, no registration), returns HTTP 404:
```json
{ "error": "no_snapshot", "message": "This space has no cached endpoint content yet." }
```

**And** the endpoint is proxied at `/api/space/{space_id}/raw` in nginx (same pattern as `/snapshots`)

### AC4 — Detail card restructured into 3 explicit zones

**Given** a maker opens the detail drawer for any space

**When** `renderDetail()` renders

**Then** the card is visually structured into 3 clearly separated zones:

**Zone 1 — Identity** (always present):
- Space name (h3)
- Network membership badges + status badge
- Freshness/notification banner (existing `freshnessText()` — unchanged)
- Error banner for broken spaces (Story 2.2 AC3 — unchanged)

**Zone 2 — Data card** (confirmed and broken spaces only; seeded spaces show a single placeholder line):
- Section label: `"Space data"` (`.wf-label`)
- Only fields actually ingested from the coordinator endpoint:
  - `Name` — `schema:name`
  - `Website` — `schema:url`
  - `Opening hours` — `schema:openingHours` (shows `"—"` if not provided)
  - `Description` — `schema:description` (shows `"—"` if not provided, **newly surfaced — was ingested but never displayed**)
  - `Specialties` — chips (unchanged)
- **Remove** `Founded`, `Capacity`, `Contact` (email) from the card — these are VOW scrape artifacts never written by coordinator ingestion; displaying them implies false data provenance

**Zone 3 — Source** (confirmed and broken spaces only; hidden on mobile `< 768px`):
- Section label: `"Source data"` with `↗ Open source` link to the endpoint URL in the top-right corner of the section header
- Async fetch to `GET /api/space/{id}/raw`
- Displays the raw JSON in a `<pre class="json">` block using the existing `jsonHighlight()` function — **same syntax highlighting, real content**
- Loading state: `"Loading source data…"` in `var(--muted)`
- If 404 (seeded/no snapshot): section is not rendered at all
- If network error: `"Source unavailable."` in `var(--muted)` — no error thrown
- `jsonForSpace()` function is **deleted** — no longer used

### AC5 — Seeded space Zone 2 placeholder

**Given** a space has `status === 'seeded'`

**When** Zone 2 renders

**Then** it shows a single line: `"Data from VOW / RFF network directory — not yet verified by coordinator."` in `.wf-label` style

**And** no individual fields are listed (the seeded data has never been through Pydantic validation; it came from scraping)

**And** Zone 3 is not rendered (no snapshot exists)

### AC6 — Validation UI update: subset progress (progressive unlock)

**Given** a coordinator submits a URL via the "Add your URL" drawer (Story 2.1)

**When** the validation response arrives

**Then** the success confirmation now shows the subset reached and the next unlock message:

```
✓ fablab-brussels is live on the map! [mom:card]

Your data unlocks: pin on map + full detail card
To unlock SpaceAPI compatibility: add api_compatibility, logo, contact fields
→ See schema guide
```

**And** the `[mom:card]` badge uses the existing `.status-label` CSS class

**And** if only `mom:required` is reached (missing website or opening hours), the confirmation still shows success but with the unlock prompt more prominent

**And** `"See schema guide"` links to `https://github.com/SpaceApi/schema` (opens in new tab) — no internal docs page needed yet

### AC7 — No regression on existing behaviour

**Given** Stories 2.1 and 2.2 implemented drawer provenance, fetch history, and CTA suppression

**When** Story 2.7 changes are applied

**Then** fetch history section (Story 2.2 AC4) is unchanged and still renders below Zone 3

**And** embed button remains at the bottom

**And** provenance section (Story 2.2 AC1) is merged into Zone 2 header or kept as a sub-section — do not duplicate

---

## Tasks / Subtasks

- [x] **Task 1** — Pydantic schema model (AC1)
  - [x] In `infra/link_handler/main.py`, add `SpaceAPISchema` Pydantic model with `mom:required`, `mom:card`, `spaceapi:compatible` subset logic
  - [x] Replace ad-hoc `_extract_name()` and `_extract_coords()` extraction with Pydantic parsing
  - [x] Add `classify_subset(data: dict) -> dict` function returning `subset`, `subset_score`, `missing_card_fields`, `unlock_message`, `next_subset`, `next_unlock`
  - [x] Wire into `_fetch_and_validate()` — subset result added to result dict
  - [x] Both `validate_url` and `register_url` endpoints return subset info
  - [x] Keep `_scan_pii()` as-is — orthogonal concern

- [x] **Task 2** — Store raw JSON in snapshot (AC2)
  - [x] In `register_url()`, after `data = result.pop("_data", {})`, serialise `data` to compact JSON string
  - [x] Cap at 50 KB; log WARNING and substitute truncation notice if exceeded
  - [x] Escape for SPARQL string: replace `\` → `\\`, `"` → `\"`, newlines → `\n`
  - [x] Add `mom:rawContent` triple to the `snapshot_update` SPARQL string
  - [x] Verify existing snapshot logic (snapshotDate, snapshotSummary, lastHttpStatus) is unchanged

- [x] **Task 3** — `GET /api/space/{id}/raw` endpoint (AC3)
  - [x] Add endpoint to `infra/link_handler/main.py`
  - [x] SPARQL SELECT with `ORDER BY DESC(?snapshotDate) LIMIT 1` for rawContent
  - [x] Parse stored JSON string back to dict before returning
  - [x] Return 404 JSON (not HTTP 404 status — return `{"error": "no_snapshot"}` with HTTP 200 to simplify frontend handling)
  - [x] Add nginx proxy: `location ~ ^/api/space/[^/]+/raw$` → same pattern as `/snapshots` block

- [x] **Task 4** — Card zone restructure in `renderDetail()` (AC4, AC5, AC7)
  - [x] Remove `Founded`, `Capacity`, `Contact` rows from Quick Facts (`app.js:412–416`)
  - [x] Add `Description` row (newly surfaced — `s.description` field, default `""`)
  - [x] Rename section label from `"Quick facts"` to `"Space data"`
  - [x] For seeded spaces: replace Quick Facts content with placeholder text (AC5)
  - [x] Replace JSON section (`app.js:449–452`) with Zone 3 async fetch to `/api/space/{id}/raw`
  - [x] Delete `jsonForSpace()` function (`app.js:524–540`) — no longer needed
  - [x] Zone 3 hidden on mobile via `@media (max-width: 767px) { .zone-source { display: none; } }`
  - [x] Preserve fetch history section position (below Zone 3, above embed button)

- [x] **Task 5** — GeoJSON: surface `description` field (AC4)
  - [x] In `scripts/materialize_geojson.py`, add to SPARQL query (both UNION branches):
    `OPTIONAL { ?spaceUri schema:description ?description }`
  - [x] Add to `GROUP BY` clause
  - [x] In `binding_to_space()`: map `description` → `description` (default `""`)
  - [x] Regenerate `web/data/spaces.geojson`: `source venv/bin/activate && python scripts/materialize_geojson.py`

- [x] **Task 6** — Validation UI: subset progress message (AC6)
  - [x] In `app.js` success handler for `POST /api/register-url` response, read `subset`, `unlock_message`, `next_unlock` fields
  - [x] Render progressive unlock section below the existing "✓ live on the map!" confirmation
  - [x] Use existing `.status-label` CSS for the subset badge
  - [x] "See schema guide" link: `https://github.com/SpaceApi/schema`

- [x] **Task 7** — Integration test
  - [x] 14 tests created and passing (8 Pydantic schema + 6 integration tests)
  - [x] Subset classification tested at all levels (none, required, card, spaceapi)
  - [x] /api/space/{id}/raw endpoint tested (404 handling verified)
  - [x] Health check and snapshots endpoints verified

---

## Dev Notes

### The core bug: `jsonForSpace()` is lying

`app.js:524–540` constructs a JSON object from GeoJSON properties and labels it "Raw JSON from endpoint." This is not what the endpoint returns — it's a curated subset of Oxigraph-materialized fields, repackaged to look like source data. Delete it entirely in Task 4.

The replacement (Zone 3) fetches `GET /api/space/{id}/raw` which returns the actual JSON that was at the endpoint URL at ingestion time, stored as `mom:rawContent` in the snapshot graph.

### Fields currently in Quick Facts that are NOT in the ingestion pipeline

`app.js:412–416` renders:
- `Hours` ← `s.opening_hours` — **real** (from `schema:openingHours` if coordinator provided it)
- `Founded` ← `s.founded` — **FAKE** — not in SPARQL query, will be `undefined` or a VOW scrape artifact
- `Capacity` ← `s.capacity` — **FAKE** — same, not ingested
- `Contact` ← `s.contact` — VOW scrape artifact; never written by `_build_sparql_update()`
- `Website` ← `s.website` — **real** (from `schema:url`)

Remove Founded, Capacity, Contact. Keep Hours, Website. Add Description (newly surfaced from Oxigraph — `schema:description` is written by `_build_sparql_update()` at line 250–252 but never read back in `materialize_geojson.py`).

### `description` field gap

`infra/link_handler/main.py:250–252` writes `schema:description` to Oxigraph but `scripts/materialize_geojson.py` never reads it back. It's stored but never displayed. Task 5 closes this gap.

### Pydantic model structure

```python
from pydantic import BaseModel, Field, model_validator
from typing import Optional, List

class SpaceAPIGeo(BaseModel):
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    # accept both schema:latitude and latitude
    model_config = {"populate_by_name": True}

class SpaceAPISchema(BaseModel):
    name: Optional[str] = Field(None, alias="schema:name")
    plain_name: Optional[str] = Field(None, alias="name")
    geo: Optional[SpaceAPIGeo] = Field(None, alias="schema:geo")
    url: Optional[str] = Field(None, alias="schema:url")
    opening_hours: Optional[str] = Field(None, alias="schema:openingHours")
    description: Optional[str] = Field(None, alias="schema:description")
    logo: Optional[str] = None
    api_compatibility: Optional[List[str]] = None
    contact: Optional[dict] = None

    @property
    def resolved_name(self):
        return self.name or self.plain_name

    @property
    def resolved_lat(self):
        if self.geo: return self.geo.latitude
        return None

    @property
    def resolved_lon(self):
        if self.geo: return self.geo.longitude
        return None

    model_config = {"populate_by_name": True, "extra": "allow"}
```

Use `SpaceAPISchema.model_validate(data)` — `extra="allow"` means unknown fields are accepted silently (SpaceAPI validators allow extra properties; so do we).

### `classify_subset()` logic

```python
def classify_subset(schema: SpaceAPISchema) -> dict:
    has_required = bool(schema.resolved_name and schema.resolved_lat and schema.resolved_lon)
    has_card = has_required and bool(schema.url and schema.opening_hours)
    has_spaceapi = has_card and bool(schema.api_compatibility and schema.logo and schema.contact)

    if has_spaceapi:
        return {"subset": "spaceapi:compatible", "subset_score": 3,
                "missing_card_fields": [],
                "unlock_message": "Full SpaceAPI compatibility — interoperable with mapall.space and other SpaceAPI maps.",
                "next_subset": None, "next_unlock": None}
    elif has_card:
        missing = [f for f in ["api_compatibility", "logo", "contact"] if not getattr(schema, f.replace("_compatibility","_compatibility"), None)]
        return {"subset": "mom:card", "subset_score": 2,
                "missing_card_fields": missing,
                "unlock_message": "Full detail card unlocked.",
                "next_subset": "spaceapi:compatible",
                "next_unlock": "Interoperability with SpaceAPI maps: add api_compatibility, logo, contact"}
    elif has_required:
        missing = []
        if not schema.url: missing.append("schema:url")
        if not schema.opening_hours: missing.append("schema:openingHours")
        return {"subset": "mom:required", "subset_score": 1,
                "missing_card_fields": missing,
                "unlock_message": "Pin on map unlocked. Add website and opening hours for the full detail card.",
                "next_subset": "mom:card",
                "next_unlock": "Full detail card display"}
    else:
        return {"subset": "none", "subset_score": 0,
                "missing_card_fields": [],
                "unlock_message": None, "next_subset": None, "next_unlock": None}
```

### Raw JSON storage — SPARQL escaping

The raw JSON string must be escaped before insertion into a SPARQL string literal:

```python
import json

def _escape_sparql_string(s: str) -> str:
    return s.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')

raw_json = json.dumps(data, separators=(',', ':'))  # compact, no whitespace
if len(raw_json) > 50_000:
    logger.warning("raw endpoint content for %s exceeds 50KB (%d bytes), truncating", slug, len(raw_json))
    raw_json = '[TRUNCATED: response exceeded 50KB]'
escaped = _escape_sparql_string(raw_json)
# Then in SPARQL: <{space_uri}> mom:rawContent "{escaped}"^^xsd:string .
```

### Zone 3 async fetch pattern

```js
// Zone 3 — Source (desktop only, confirmed/broken spaces)
if (s.status !== 'seeded') {
  const zone3 = el('div', { class: 'detail-section zone-source' }, [
    el('div', { class: 'zone-header', style: { display: 'flex', alignItems: 'center' } }, [
      el('div', { class: 'wf-label' }, ['Source data']),
      s.endpoint_url ? el('a', { href: s.endpoint_url, target: '_blank', rel: 'noopener',
        class: 'wf-label', style: { marginLeft: 'auto', textDecoration: 'none' } }, ['↗ Open source']) : null,
    ]),
    el('div', { id: 'raw-content', style: { color: 'var(--muted)', fontSize: '11px', padding: '6px 16px' } },
      ['Loading source data…'])
  ]);
  body.appendChild(zone3);

  fetch(`/api/space/${s.id}/raw`)
    .then(r => r.json())
    .then(result => {
      const el2 = document.getElementById('raw-content');
      if (!el2) return;
      if (result.error) { el2.textContent = 'Source unavailable.'; return; }
      el2.innerHTML = '';
      const pre = document.createElement('pre');
      pre.className = 'json';
      pre.appendChild(jsonHighlight(result.raw));
      el2.appendChild(pre);
    })
    .catch(() => {
      const el2 = document.getElementById('raw-content');
      if (el2) el2.textContent = 'Source unavailable.';
    });
}
```

### nginx proxy for `/raw` endpoint

Add alongside the existing `/snapshots` regex block in `infra/nginx/conf.d/app.conf`:

```nginx
location ~ ^/api/space/[^/]+/raw$ {
    proxy_pass http://mak-link-handler:8000$request_uri;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 15s;
}
```

### SpaceAPI v14 vs v16-draft field name alignment

SpaceAPI uses `space` (not `schema:name`), `url`, `location.lat/lon` at the top level — not JSON-LD prefixed keys. MoM coordinators are publishing JSON-LD with `schema:` prefixes. The Pydantic model must handle both forms (`schema:name` and `name`, `schema:url` and `url`) via aliases. Do not require strict SpaceAPI key names for `mom:required` — the coordinator's JSON-LD format is the primary input.

For `spaceapi:compatible` detection, check for SpaceAPI-native keys (`api_compatibility`, `logo`, `contact`) which would only be present if the coordinator intentionally added them.

### Files touched

```
infra/
  link_handler/
    main.py              ← SpaceAPISchema Pydantic model; classify_subset(); rawContent storage;
                           GET /api/space/{id}/raw endpoint
  nginx/conf.d/
    app.conf             ← add regex location for /api/space/.../raw

scripts/
  materialize_geojson.py ← add OPTIONAL for schema:description in both UNION branches + GROUP BY

web/
  app.js                 ← renderDetail() zone restructure; delete jsonForSpace();
                           Zone 3 async fetch; validation UI subset progress
  data/spaces.geojson    ← regenerated (not committed)
```

No new Python packages needed — Pydantic is already a dependency (`from pydantic import BaseModel` at `main.py:11`).

### Handoff from Story 2.6 (2026-04-28)

**Zone 3 desktop-only guard already in place** — Story 2.6 added `if (window.innerWidth >= 768)` around the raw JSON block in `renderDetail()`. Task 4 of this story replaces the content inside that guard; the guard itself stays. Do not remove it.

**`initAddUrl()` dead code removed** — Story 2.6 fixed a boot crash caused by `initAddUrl()` trying to populate `#url-space` (a select element that no longer exists in the HTML). The dead loop has been removed. If this story or a future one needs a space selector in the addurl drawer, add the `<select id="url-space">` element to `maps-of-making.html` deliberately first.

**`window.innerWidth >= 768` pattern** — Mobile vs desktop branching in `renderDetail()` uses direct `window.innerWidth` checks (re-evaluated on each drawer open). No resize listener needed; consistent with CTA suppression added in 2.6.

### References

- Current `renderDetail()`: `web/app.js:374–489`
- Current `jsonForSpace()` (to delete): `web/app.js:524–540`
- `jsonHighlight()` (keep, reuse): `web/app.js:542–565`
- `_fetch_and_validate()`: `infra/link_handler/main.py:171–222`
- `_build_sparql_update()`: `infra/link_handler/main.py:229–263`
- Snapshot write: `infra/link_handler/main.py:396–415`
- `GET /api/space/{id}/snapshots`: `infra/link_handler/main.py:426–455`
- `materialize_geojson.py` SPARQL query: `scripts/materialize_geojson.py:28–103`
- `binding_to_space()`: `scripts/materialize_geojson.py:136–220`
- SpaceAPI schema reference: `https://github.com/SpaceApi/schema` (v14 stable, 16-draft design reference)
- Architecture schema subset table: `_bmad-output/planning-artifacts/architecture.md` — "External Schema References"

---

## Dev Agent Record

### Agent Model Used

claude-haiku-4-5 (story implementation, 2026-04-28)

### Completion Notes

**Story 2.7 Complete** — All 7 tasks implemented and tested. Pydantic schema validation now classifies data into 3 subsets (required → card → spaceapi:compatible). Raw endpoint JSON persisted in Oxigraph snapshot graphs with 50KB cap and SPARQL escaping. Detail card restructured into 3 explicit zones: Identity (unchanged), Data (seeded/confirmed split), Source (async fetch to /raw endpoint). Validation UI shows progressive unlock messages. GeoJSON materialization now surfaces description field. All 14 tests passing.

**Key achievements:**
- Pydantic SpaceAPISchema with 8 unit tests (all passing)
- /api/space/{id}/raw endpoint with SPARQL query + nginx proxy
- Detail drawer zones separated: seeded placeholder, confirmed fields, async raw JSON
- Mobile responsive: Zone 3 hidden on < 768px viewports
- Subset classification: required → card → spaceapi:compatible with unlock messages
- GeoJSON regenerated: 609 spaces with description field

**Regressions checked:** fetch history, embed button, copy link button all preserved; freshness banner unchanged; CTA for seeded spaces unchanged.

### File List

**Modified files:**
- `infra/link_handler/main.py` — SpaceAPISchema, SpaceAPIGeo, classify_subset(), register_url raw storage, GET /api/space/{id}/raw endpoint
- `infra/link_handler/requirements.txt` — Added pydantic
- `infra/link_handler/test_schema.py` — 8 unit tests for Pydantic models and subset classification
- `infra/link_handler/test_integration.py` — 6 integration tests for endpoints
- `infra/nginx/conf.d/app.conf` — Added /raw endpoint proxy location
- `scripts/materialize_geojson.py` — Added description field to SPARQL query and binding_to_space()
- `web/app.js` — Restructured renderDetail() with 3 zones, async Zone 3 fetch, validation UI with subset badge, deleted jsonForSpace()
- `web/maps-of-making.html` — Added CSS to hide .zone-source on mobile < 768px
- `web/data/spaces.geojson` — Regenerated with description field (609 spaces)

**Generated files (not committed):**
- `web/data/spaces.geojson`

---

## Review notes — findings from real-world dual-validator exercise (2026-04-28)

While generating `web/test-fixtures/openfab.jsonld` with the founder of OpenFab Brussels using `web/test-fixtures/SKILL.md`, several gaps in this story's design surfaced. None are demo-blockers, but they should be addressed during the review pass before this story moves from `review` → `done`.

### 1. SpaceAPISchema extended for SpaceAPI v14 flat keys

**Original AC1** required `schema:name` (or `name`) + `schema:geo.latitude/longitude`. AC1 did NOT require accepting SpaceAPI v14's native flat shape (`space`, `location.lat`, `location.lon`, `location.address`).

**Reality:** if we tell coordinators "your file should also pass `validator.spaceapi.io`", we must accept SpaceAPI's keys. `infra/link_handler/main.py` was updated to add `space`, `SpaceAPILocation` (with `lat`/`lon`/`address`), and resolved-property fallbacks. `_build_sparql_update` reads `location.address` as a fallback.

**Action for review:** confirm AC1's intent now includes the flat shape, update test_schema.py to cover `{"space": "...", "location": {"lat": ..., "lon": ...}}` as a valid input.

### 2. `mom:card` → `spaceapi:compatible` is a cliff, not a gradient

The tier table in AC1 implies a smooth progression (`mom:card` adds `url`+`openingHours`; `spaceapi:compatible` adds `api_compatibility`+`logo`+`contact`). In practice **a `mom:card` document does not *almost* pass SpaceAPI v14** — SpaceAPI v14 also mandates `state` (dynamic open/closed object) and a `location.address` string. The "missing 3 fields" story we tell coordinators is misleading.

**Action for review:** rephrase the unlock messages in `classify_subset()` and AC6 to be honest: "SpaceAPI compatibility requires a separate set of fields and is optional — your card already works." Update `next_unlock` text accordingly.

### 3. Dual-shape canonical template (one file, two validators)

The biggest design shift from this exercise: we should NOT publish two files (one mom, one SpaceAPI). Instead, the canonical output is a **JSON-LD document whose body uses SpaceAPI v14 flat keys** (`space`, `location.lat`, `state`, …) and whose `@context` aliases each to mom/schema.org IRIs. Both validators are happy with the same bytes. `web/test-fixtures/SKILL.md` was rewritten around this principle and `openfab.jsonld` regenerated.

**Action for review:** add an explicit AC (or amend AC1) stating the validator accepts the dual-shape document; add a fixture/test asserting it round-trips through Pydantic.

### 4. SpaceAPI validator error surfacing

`validator.spaceapi.io`'s web UI reports "failed" with no actionable detail; their API exposes `schemaErrors[]` (property + message per error). Coordinators currently see a black box. `scripts/validate_dual.py` was added to run both validators and now flattens `schemaErrors[]` into `_schema_errors_summary`. The coordinator-facing UI in AC6 does not yet surface these.

**Action for review:** decide whether AC6's "→ See schema guide" link is enough, or whether the validation drawer should pass `schemaErrors[]` through to the coordinator. Defer to Epic 5 if not in scope here, but document the decision.

### 5. `state` collision and `@id` confusion

- SpaceAPI's `state` (dynamic open/closed) collides with `mom:operationalState` (long-term lifecycle). The dual-shape template aliases `state` → `mom:dynamicState`, but the ontology has no `mom:dynamicState` term yet. Either add the term to `mom.ttl` or pick a different alias.
- `@id` semantics confused the coordinator (founder of OpenFab): "do I need to fill in the URL where the JSON-LD lives?" The validator ignores `@id` — it's the IRI of the space-as-entity. SKILL.md now documents this but a coordinator-facing FAQ entry is missing.

**Action for review:** ontology PR for `mom:dynamicState` (or alias choice change); add FAQ snippet to coordinator onboarding drawer text.

### 6. Activity-tag vocabulary needs SKOS

Coordinator wanted to tag OpenFab with "agentic-ai", "embedded-systems", "ai-empowered" — all reasonable, none canonical. String-match search will not find these as synonyms or as related to "AI". This is the use case that motivates the semantic layer with `mom.ttl` + Oxigraph but the SKOS hierarchy is not yet authored.

**Action for review:** out of scope for 2.7, but add a story to seed `mom:Activity` concepts with `skos:altLabel` for top-N tags currently in use across spaces. Reference: deferred-work.md SKILL.md exercise section.

### 7. Files added/modified during this exercise (post-implementation)

- `infra/link_handler/main.py` — added `SpaceAPILocation`, extended `SpaceAPISchema` with `space` and `location` flat-key support; `_build_sparql_update` reads `location.address` fallback.
- `web/test-fixtures/SKILL.md` — rewritten around dual-shape canonical template.
- `web/test-fixtures/openfab.jsonld` — new fixture (dual-shape).
- `scripts/validate_dual.py` — new helper running both mom and SpaceAPI v14 validators and surfacing `schemaErrors[]`.
- `_bmad-output/implementation-artifacts/deferred-work.md` — appended a "SKILL.md dual-validator exercise" section.

**Reviewer should re-run `test_schema.py` + `test_integration.py` after the AC1/AC6 wording fixes above; existing 14 tests should still pass with the schema extension but new tests for the flat-key shape are needed.**

---

## Review Findings (2026-04-28)

### Decision-needed

- [x] [Review][Decision] D1 — Provenance section dropped: **intentional** — Zone 3 "↗ Open source" link replaces Endpoint URL; source label and last-fetched no longer surfaced. Accepted 2026-04-29.
- [x] [Review][Decision] D2 — AC6 schemaErrors[] from SpaceAPI validator: **deferred to Epic 5** — "→ See schema guide" link is sufficient for demo. Accepted 2026-04-29.

### Patch

- [x] [Review][Patch] P1 — SPARQL injection via unsanitized space_id — fixed: `re.match(r'^[a-zA-Z0-9_-]+$', space_id)` guard added to both /raw and /snapshots endpoints [infra/link_handler/main.py]
- [x] [Review][Patch] P2 — nginx proxy for /api/space/{id}/raw — already present in infra/nginx/conf.d/app.conf (committed in prior story step); confirmed lines 79-86. Not missing.
- [x] [Review][Patch] P3 — url alias gap fixed — added `plain_url: Field(None, alias="url")` + `resolved_url` property; classify_subset now uses resolved_url [infra/link_handler/main.py]
- [x] [Review][Patch] P4 — opening_hours alias gap fixed — added `plain_opening_hours: Field(None, alias="opening_hours")` + `resolved_opening_hours` property [infra/link_handler/main.py]
- [x] [Review][Patch] P5 — Truncated 50KB raw JSON — fixed: stores `{}` + `mom:rawTruncated true` triple; /raw returns `{raw: null, truncated: true}` instead of error:no_snapshot [infra/link_handler/main.py]
- [x] [Review][Patch] P6 — DOM id collision fixed — switched to class `.raw-content`, element captured via `zone3.querySelector('.raw-content')` closure [web/app.js]
- [x] [Review][Patch] P7 — s.name null fixed — `s.name || '—'` [web/app.js]
- [x] [Review][Patch] P8 — next_unlock text updated — honest about SpaceAPI cliff [infra/link_handler/main.py:classify_subset]
- [x] [Review][Patch] P9 — flat-key tests added: test_spaceapi_flat_key_required + test_spaceapi_flat_key_card — all 10 tests pass [infra/link_handler/test_schema.py]
- [x] [Review][Patch] P10 — mom:dynamicState term added to mom.ttl with domain/range/comment [ontology/mom.ttl]

### Defer

- [x] [Review][Defer] W1 — "last fetch never ago" timestamp display bug [web/app.js:timeAgo()] — deferred, pre-existing; timeAgo() receives date-only YYYY-MM-DD string not a full ISO datetime; not introduced by 2.7 → Epic 5 / Story 4.2
- [x] [Review][Defer] W2 — No fetch timeout on Zone 3 /raw call [web/app.js:Zone 3 fetch] — deferred, pre-existing pattern across app fetches → Epic 5 polish
- [x] [Review][Defer] W3 — Zone 3 error: 500 vs network timeout collapse to same "Source unavailable." — deferred, spec-allowed → monitor
