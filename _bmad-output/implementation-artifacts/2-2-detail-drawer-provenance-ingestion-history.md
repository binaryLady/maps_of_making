# Story 2.2: Detail Drawer — Provenance + Ingestion History

Status: ready-for-dev

## Story

As a maker or coordinator,
I want the space detail drawer to show where the data came from, when it was last fetched, and a short history of changes,
so that I can trust whether the information is current — and coordinators can verify their own endpoint is being read correctly.

## Acceptance Criteria

### AC1 — Provenance section in detail drawer

**Given** a maker clicks any pin

**When** the detail drawer opens

**Then** a "Data provenance" section appears below the Quick facts block, showing:
- Source label: `"Self-registered"` if `source === "self-registered"`, `"VOW network"` if `source === "scraped-vow"`, `"RFF network"` if `source === "mock-rff"`, `"Unknown"` otherwise
- Endpoint URL: truncated to 40 chars with `…` suffix, full URL on hover (`title` attribute) and as an `<a>` that opens in a new tab
- Last fetched: human-readable relative time using existing `timeAgo()` function — e.g. "3 hours ago", "never" if `last_fetched` is empty

**And** the section uses the existing `.detail-section` + `.wf-label` + `.kv` CSS classes — no new styles needed

**And** for ⚪ seeded spaces (`s.status === 'seeded'`), the endpoint URL row shows `"—"` (no URL yet)

### AC2 — "Claim this pin" CTA for seeded spaces

**Given** a space has `status === 'seeded'` (⚪ pin, not yet confirmed)

**When** the detail drawer opens

**Then** a CTA block appears between the Quick facts section and the provenance section:
```
This space hasn't claimed its pin yet.
Are you the coordinator? [Add your URL →]
```

**And** clicking "Add your URL →" calls `setDrawer('addurl')` and closes the detail drawer (same logic as `toggleDrawer('addurl')`)

**And** the CTA uses existing `.note` CSS class for styling — no new styles

### AC3 — Error detail for broken spaces

**Given** a space has `status === 'broken'` or `status === 'error'`

**When** the detail drawer opens

**Then** the freshness line is replaced by an amber error banner showing:
- Error category in plain language: `"404 Not Found"`, `"Connection refused"`, `"Timeout (>10s)"`, `"Invalid JSON"`, `"Schema mismatch"` — derived from `s.error_type` field (see AC6)
- Last known good date: `"Last successful fetch: {timeAgo(s.last_fetched)}"` or `"No successful fetch recorded"` if empty

**And** the banner uses `class="freshness broken"` (already styled in CSS)

### AC4 — Ingestion snapshot history

**Given** a coordinator has registered their URL (Story 2.1 done) and the drawer opens

**When** the drawer renders the history section

**Then** a "Fetch history" section appears at the bottom of the drawer (above the embed button)

**And** it calls `GET /api/space/{space_id}/snapshots` and renders the response as a reverse-chronological list of up to 5 entries:
```
2026-04-26 14:32  First registration  ✓
```

**And** while loading, shows a single-line placeholder: `"Loading history…"` in `var(--muted)` color

**And** if the endpoint returns an empty array or errors (network, 404), shows: `"No fetch history yet."` — no error thrown

**And** the section only renders for confirmed or broken spaces — seeded spaces skip it entirely

### AC5 — `GET /api/space/{space_id}/snapshots` endpoint

**Given** a `space_id` (the slug portion of the space URI, e.g. `fablab-brussels`)

**When** `GET /api/space/{space_id}/snapshots` is called

**Then** the link_handler queries Oxigraph for named graphs matching `urn:mak:space/{space_id}/` pattern:

```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
SELECT ?graph ?date ?summary ?httpStatus
WHERE {
  GRAPH ?graph {
    <urn:mak:space/{space_id}> mom:snapshotDate ?date .
    OPTIONAL { <urn:mak:space/{space_id}> mom:snapshotSummary ?summary }
    OPTIONAL { <urn:mak:space/{space_id}> mom:lastHttpStatus ?httpStatus }
  }
  FILTER(STRSTARTS(STR(?graph), "urn:mak:space/{space_id}/"))
}
ORDER BY DESC(?date)
LIMIT 5
```

**And** returns JSON:
```json
[
  { "date": "2026-04-26T14:32:00Z", "summary": "First registration", "http_status": 200 }
]
```

**And** returns `[]` (empty array, HTTP 200) if no snapshots exist — never 404

**And** the endpoint is proxied at `/api/space/{space_id}/snapshots` in nginx

### AC6 — `mom:endpointUrl`, `mom:lastFetched`, `mom:errorType` in GeoJSON

**Given** `scripts/materialize_geojson.py` runs after Story 2.1 has written confirmed space triples

**When** it executes the SPARQL SELECT query

**Then** the query includes:
```sparql
OPTIONAL { ?spaceUri mom:endpointUrl ?endpointUrl }
OPTIONAL { ?spaceUri mom:lastFetched ?lastFetched }
OPTIONAL { ?spaceUri mom:lastHttpStatus ?lastHttpStatus }
OPTIONAL { ?spaceUri mom:errorType ?errorType }
```

**And** `binding_to_space()` maps these to GeoJSON properties:
- `endpoint_url` ← `mom:endpointUrl` (overrides `profileUrl` for confirmed spaces)
- `last_fetched` ← `mom:lastFetched` (ISO datetime string)
- `error_type` ← `mom:errorType` (plain string, e.g. `"404"`, `"timeout"`, `"schema_invalid"`)

**And** for seeded spaces without these triples, all three default to `""` (empty string, same as before)

**Note:** This AC requires Story 2.1 to have written `mom:endpointUrl` and `mom:lastFetched` during ingestion. Verify Story 2.1 AC2 includes these predicates before implementing.

### AC7 — Story 2.1 amendment: write snapshot named graph on registration

**Given** Story 2.1 `POST /api/register-url` writes to Oxigraph

**When** the SPARQL UPDATE runs

**Then** in addition to the current space graph `<urn:mak:space/{slug}>`, a snapshot graph is also written:

```sparql
INSERT DATA {
  GRAPH <urn:mak:space/{slug}/{iso_date}> {
    <urn:mak:space/{slug}> mom:snapshotDate "{iso_datetime}"^^xsd:dateTime ;
                            mom:snapshotSummary "First registration" ;
                            mom:lastHttpStatus 200 .
  }
}
```

**And** the snapshot graph name format is `urn:mak:space/{slug}/{YYYY-MM-DD}` (date only, not full datetime — one snapshot per day max, idempotent on same-day re-register)

**Note:** This is a small amendment to Story 2.1's implementation — not a re-story, just a dev note for the 2.1 dev agent to include. If 2.1 is already done, add a sub-task to its File List.

### AC8 — No regression on existing detail drawer

**Given** the current detail drawer renders correctly for all space types

**When** the Story 2.2 changes are applied

**Then** all existing sections (hero, freshness, quick facts, specialties, JSON, embed button) are unchanged

**And** the new sections (provenance, CTA, error banner, history) insert cleanly between existing sections without breaking layout

**And** embed CTA button remains at the bottom

---

## Tasks / Subtasks

- [ ] **Task 1** — Backend: `GET /api/space/{space_id}/snapshots` (AC5)
  - [ ] Add endpoint to `infra/link_handler/main.py`
  - [ ] SPARQL SELECT against `OXIGRAPH_ENDPOINT/query` for graphs matching `urn:mak:space/{space_id}/`
  - [ ] Return `[]` on empty result or query error (log warning, never propagate 500 to client)
  - [ ] Add nginx proxy block: `location ~ ^/api/space/[^/]+/snapshots$` → `mak-link-handler:8000/api/space/$1/snapshots` (regex location, after existing `/api/` block)

- [ ] **Task 2** — Backend: Story 2.1 amendment — write snapshot graph (AC7)
  - [ ] In `POST /api/register-url`, after the main SPARQL UPDATE, run a second INSERT to write `<urn:mak:space/{slug}/{YYYY-MM-DD}>`
  - [ ] Use `datetime.utcnow().strftime('%Y-%m-%d')` for the graph date key
  - [ ] If a snapshot for today already exists, the INSERT is a no-op (Oxigraph handles duplicate triples idempotently)

- [ ] **Task 3** — GeoJSON: extend materialize query (AC6)
  - [ ] Add `OPTIONAL { ?spaceUri mom:endpointUrl ?endpointUrl }` to both UNION branches of `SPARQL_QUERY`
  - [ ] Add `OPTIONAL { ?spaceUri mom:lastFetched ?lastFetched }` to both branches
  - [ ] Add `OPTIONAL { ?spaceUri mom:errorType ?errorType }` to both branches
  - [ ] Add all three to `GROUP BY` clause
  - [ ] In `binding_to_space()`: map `endpointUrl` → `endpoint_url` (preferred over `profileUrl` when present), `lastFetched` → `last_fetched`, `errorType` → `error_type` (default `""`)
  - [ ] Regenerate `web/data/spaces.geojson` after the code change: `python scripts/materialize_geojson.py`

- [ ] **Task 4** — Frontend: extend `renderDetail()` (AC1, AC2, AC3, AC4, AC8)
  - [ ] Insert "Claim this pin" CTA block after hero + freshness, before Quick facts — only for seeded spaces (AC2)
  - [ ] Insert "Data provenance" section after Quick facts — all spaces (AC1)
  - [ ] Update `freshnessText()` for broken spaces to use `s.error_type` for plain-language error category (AC3)
  - [ ] Insert "Fetch history" section above embed button — confirmed and broken spaces only (AC4)
  - [ ] History section: async fetch to `/api/space/{s.id}/snapshots`, render inline, handle empty/error gracefully
  - [ ] Do NOT move or remove the embed button at the bottom (AC8)

- [ ] **Task 5** — Integration test
  - [ ] Open detail drawer for a ⚪ seeded space → verify CTA appears with "Add your URL →" link
  - [ ] Click CTA → verify addurl drawer opens
  - [ ] Register a URL via Story 2.1 flow → re-open detail drawer → verify provenance section shows endpoint URL, timestamp
  - [ ] Verify "Fetch history" shows "First registration" entry
  - [ ] Open detail drawer for broken/error space (use RFF mockup data) → verify error banner shows

---

## Dev Notes

### renderDetail() structure — what exists and where to insert

Current `app.js:372-422` render order:
1. Hero (name, address, badges) — `app.js:382`
2. Freshness line — `app.js:392`
3. Quick facts (dl.kv) — `app.js:398`
4. Specialties chips — `app.js:408`
5. Raw JSON panel — `app.js:413`
6. Embed button — `app.js:418`

Target render order after Story 2.2:
1. Hero (unchanged)
2. Freshness line (updated for broken: use error_type)
3. **[NEW] Claim CTA** — seeded only
4. Quick facts (unchanged)
5. **[NEW] Provenance section** — all spaces
6. Specialties (unchanged)
7. Raw JSON panel (unchanged)
8. **[NEW] Fetch history** — confirmed/broken only
9. Embed button (unchanged)

### Fields already in `state.spaces` objects (from GeoJSON)

From `materialize_geojson.py:binding_to_space()` and `app.js` state:
- `s.id` — slug from URI (e.g. `"fablab-brussels"`)
- `s.endpoint_url` — currently `profileUrl` (VOW profile link), overridden after 2.1 for confirmed spaces
- `s.last_fetched` — currently `""` for seeded spaces
- `s.source` — `"scraped-vow"`, `"mock-rff"`, or null
- `s.status` — `"seeded"`, `"confirmed"`, `"broken"`, etc.

New fields after Task 3:
- `s.error_type` — `""` or e.g. `"404"`, `"timeout"`, `"schema_invalid"`

### `timeAgo()` — already exists

`app.js:435-444` — already handles `null`/empty → returns `"never"`. Use as-is for `last_fetched`.

### Source label mapping (AC1)

```js
const SOURCE_LABELS = {
  'scraped-vow': 'VOW network',
  'mock-rff': 'RFF network (demo)',
  'self-registered': 'Self-registered',
};
const sourceLabel = SOURCE_LABELS[s.source] ?? 'Unknown';
```

### Error type plain-language (AC3)

```js
const ERROR_LABELS = {
  '404': '404 Not Found',
  'timeout': 'Timeout (>10s)',
  'connection_refused': 'Connection refused',
  'schema_invalid': 'Schema mismatch',
  'json_invalid': 'Invalid JSON',
};
const errorLabel = ERROR_LABELS[s.error_type] || `Fetch error (${s.error_type || 'unknown'})`;
```

### History fetch — async inline pattern

The history section must not block the drawer from rendering. Pattern:
```js
const histSection = el('div', { class: 'detail-section' }, [
  el('div', { class: 'wf-label' }, ['Fetch history']),
  el('div', { id: 'hist-content', style: { color: 'var(--muted)', fontSize: '11px', padding: '6px 16px' } }, ['Loading history…'])
]);
body.appendChild(histSection);

fetch(`/api/space/${s.id}/snapshots`)
  .then(r => r.json())
  .then(snaps => {
    const content = document.getElementById('hist-content');
    if (!content) return; // drawer already closed
    if (!snaps.length) { content.textContent = 'No fetch history yet.'; return; }
    content.innerHTML = '';
    snaps.forEach(snap => {
      const d = new Date(snap.date).toLocaleDateString(undefined, { dateStyle: 'medium' });
      content.appendChild(el('div', {}, [`${d} · ${snap.summary} · HTTP ${snap.http_status}`]));
    });
  })
  .catch(() => {
    const content = document.getElementById('hist-content');
    if (content) content.textContent = 'No fetch history yet.';
  });
```

Use `id="hist-content"` but be aware multiple drawers opening in quick succession could conflict — consider scoping to the current space ID if this becomes an issue.

### nginx regex location for snapshots (AC5)

Add after the `/api/` block in `infra/nginx/conf.d/app.conf`:
```nginx
location ~ ^/api/space/[^/]+/snapshots$ {
    proxy_pass http://mak-link-handler:8000$request_uri;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_read_timeout 15s;
}
```

Regex location takes precedence over prefix location — place it BEFORE the generic `/api/` block or use `^~` modifier on the `/api/` block to avoid conflicts.

### SPARQL namespace — canonical always

```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
```
Never `mapsofmaking.eu`.

### Oxigraph SPARQL query from link_handler (AC5)

Same pattern as existing `POST /api/validate-url`:
```python
httpx.post(
    f"{OXIGRAPH_ENDPOINT}/query",
    content=sparql_select,
    headers={"Content-Type": "application/sparql-query", "Accept": "application/sparql-results+json"},
    timeout=10.0
)
```

### GeoJSON `endpoint_url` field evolution

Currently `endpoint_url` in GeoJSON is populated from `mom:profileUrl` (VOW profile link — points to VOW directory page, not a JSON-LD endpoint). After Story 2.1 ingestion writes `mom:endpointUrl`, this field will be the actual coordinator JSON URL. The `binding_to_space()` mapping should prefer `endpointUrl` over `profileUrl` when both are present:
```python
endpoint_url = (
    binding.get("endpointUrl", {}).get("value")
    or binding.get("profileUrl", {}).get("value")
    or ""
)
```

### Project Structure Notes

Files touched by this story:
```
infra/
  link_handler/
    main.py              ← add GET /api/space/{id}/snapshots; amend register-url to write snapshot graph
  nginx/conf.d/
    app.conf             ← add regex location for /api/space/.../snapshots

scripts/
  materialize_geojson.py ← extend SPARQL query + binding_to_space() with 3 new fields

web/
  app.js                 ← extend renderDetail() with provenance section, CTA, history
  data/spaces.geojson    ← regenerated after materialize_geojson.py change (not committed to git)
```

No new services, no new Docker volumes, no new HTML elements.

### Isolation note

This story is intentionally frontend-heavy and backend-light. The heavy ingestion work is in Story 2.1. Story 2.2 only reads back what 2.1 wrote. If Story 2.1 is not yet done, Tasks 1 and 4 (history section) can be skipped and the rest implemented against dummy data.

### References

- Existing `renderDetail()`: `web/app.js:372-422`
- `timeAgo()`: `web/app.js:435-444`
- `freshnessText()`: `web/app.js:424-433`
- `el()` helper: used throughout app.js — creates DOM elements
- GeoJSON binding: `scripts/materialize_geojson.py:125-200`
- SPARQL query: `scripts/materialize_geojson.py:28-90`
- Architecture: snapshot named graph topology — `_bmad-output/planning-artifacts/architecture.md` "AR-DATA1"
- Architecture: UX-DR3 (amber quiet banner), UX-DR10 (broken endpoint display)
- Original story 2.5 AC: `_bmad-output/planning-artifacts/epics.md:709-725`

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (story creation, 2026-04-26)

### Debug Log References

### Completion Notes List

### File List
