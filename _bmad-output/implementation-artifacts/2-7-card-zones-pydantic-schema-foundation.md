# Story 2.7: Card Zones + Pydantic Schema Foundation

Status: ready-for-dev

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

- [ ] **Task 1** — Pydantic schema model (AC1)
  - [ ] In `infra/link_handler/main.py`, add `SpaceAPISchema` Pydantic model with `mom:required`, `mom:card`, `spaceapi:compatible` subset logic
  - [ ] Replace ad-hoc `_extract_name()` and `_extract_coords()` extraction with Pydantic parsing
  - [ ] Add `classify_subset(data: dict) -> dict` function returning `subset`, `subset_score`, `missing_card_fields`, `unlock_message`, `next_subset`, `next_unlock`
  - [ ] Wire into `_fetch_and_validate()` — subset result added to result dict
  - [ ] Both `validate_url` and `register_url` endpoints return subset info
  - [ ] Keep `_scan_pii()` as-is — orthogonal concern

- [ ] **Task 2** — Store raw JSON in snapshot (AC2)
  - [ ] In `register_url()`, after `data = result.pop("_data", {})`, serialise `data` to compact JSON string
  - [ ] Cap at 50 KB; log WARNING and substitute truncation notice if exceeded
  - [ ] Escape for SPARQL string: replace `\` → `\\`, `"` → `\"`, newlines → `\n`
  - [ ] Add `mom:rawContent` triple to the `snapshot_update` SPARQL string
  - [ ] Verify existing snapshot logic (snapshotDate, snapshotSummary, lastHttpStatus) is unchanged

- [ ] **Task 3** — `GET /api/space/{id}/raw` endpoint (AC3)
  - [ ] Add endpoint to `infra/link_handler/main.py`
  - [ ] SPARQL SELECT with `ORDER BY DESC(?snapshotDate) LIMIT 1` for rawContent
  - [ ] Parse stored JSON string back to dict before returning
  - [ ] Return 404 JSON (not HTTP 404 status — return `{"error": "no_snapshot"}` with HTTP 200 to simplify frontend handling)
  - [ ] Add nginx proxy: `location ~ ^/api/space/[^/]+/raw$` → same pattern as `/snapshots` block

- [ ] **Task 4** — Card zone restructure in `renderDetail()` (AC4, AC5, AC7)
  - [ ] Remove `Founded`, `Capacity`, `Contact` rows from Quick Facts (`app.js:412–416`)
  - [ ] Add `Description` row (newly surfaced — `s.description` field, default `""`)
  - [ ] Rename section label from `"Quick facts"` to `"Space data"`
  - [ ] For seeded spaces: replace Quick Facts content with placeholder text (AC5)
  - [ ] Replace JSON section (`app.js:449–452`) with Zone 3 async fetch to `/api/space/{id}/raw`
  - [ ] Delete `jsonForSpace()` function (`app.js:524–540`) — no longer needed
  - [ ] Zone 3 hidden on mobile via `@media (max-width: 767px) { .zone-source { display: none; } }`
  - [ ] Preserve fetch history section position (below Zone 3, above embed button)

- [ ] **Task 5** — GeoJSON: surface `description` field (AC4)
  - [ ] In `scripts/materialize_geojson.py`, add to SPARQL query (both UNION branches):
    `OPTIONAL { ?spaceUri schema:description ?description }`
  - [ ] Add to `GROUP BY` clause
  - [ ] In `binding_to_space()`: map `description` → `description` (default `""`)
  - [ ] Regenerate `web/data/spaces.geojson`: `source venv/bin/activate && python scripts/materialize_geojson.py`

- [ ] **Task 6** — Validation UI: subset progress message (AC6)
  - [ ] In `app.js` success handler for `POST /api/register-url` response, read `subset`, `unlock_message`, `next_unlock` fields
  - [ ] Render progressive unlock section below the existing "✓ live on the map!" confirmation
  - [ ] Use existing `.status-label` CSS for the subset badge
  - [ ] "See schema guide" link: `https://github.com/SpaceApi/schema`

- [ ] **Task 7** — Integration test
  - [ ] Register a test URL with `mom:required` fields only → verify subset = `"mom:required"`, unlock message shown
  - [ ] Register a URL with `mom:card` fields → verify subset = `"mom:card"`
  - [ ] Open detail drawer → verify Zone 2 shows only ingested fields, no Founded/Capacity
  - [ ] Verify Zone 3 renders actual endpoint JSON (not reconstructed)
  - [ ] Verify Zone 3 is hidden on mobile viewport (< 768px)
  - [ ] Verify seeded space shows placeholder in Zone 2, no Zone 3

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

claude-opus-4-7 (story creation, 2026-04-27)

### Debug Log References

### Completion Notes List

### File List
