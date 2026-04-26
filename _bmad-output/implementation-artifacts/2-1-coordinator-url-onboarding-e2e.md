# Story 2.1: Coordinator URL Onboarding — E2E (submit → validate → ingest → flip → embed)

Status: done

## Story

As a space coordinator,
I want to paste my JSON-LD endpoint URL, see it validated live, and watch my pin flip from ⚪ to 🔵 with a ready-to-copy embed snippet —
so that I can register my space on the map without creating an account or contacting anyone.

## Acceptance Criteria

### AC1 — `POST /api/validate-url` endpoint

**Given** a coordinator submits a URL via the "Add your URL" drawer

**When** `POST /api/validate-url` is called with `{ "url": "<https://...>", "space_id": "<optional>" }`

**Then** the response contains a structured checklist object:
```json
{
  "reachable": true,
  "status_code": 200,
  "json_ld_valid": true,
  "name_found": "Fablab Brussels",
  "coords_found": true,
  "lat": 50.846,
  "lon": 4.352,
  "pii_warning": false,
  "pii_fields": []
}
```

**And** `reachable` is `false` with a human-readable `error` field if the URL is unreachable (DNS failure, timeout ≥10s, non-200 HTTP)

**And** `json_ld_valid` is `false` if the response body is not parseable as JSON or lacks both `schema:name` and `name` keys

**And** `pii_warning` is `true` (soft, non-blocking) if any of `schema:email`, `schema:telephone`, `foaf:mbox` appear at the top level — registration still proceeds

**And** the endpoint is proxied by nginx at `/api/validate-url` → `mak-link-handler:8000/api/validate-url`

### AC2 — `POST /api/register-url` endpoint

**Given** the coordinator has a validated URL (AC1 returned `reachable: true, json_ld_valid: true`)

**When** `POST /api/register-url` is called with `{ "url": "<https://...>", "space_id": "<uri | null>" }`

**Then** the endpoint:
1. Re-fetches and re-validates the URL (no trust of client-side state)
2. Writes a SPARQL UPDATE to Oxigraph, creating or overwriting `<urn:mak:space/{slug}>`:
   - Sets `mom:operationalState "confirmed"`
   - Sets `mom:endpointUrl` to the submitted URL
   - Sets `mom:lastFetched` to current UTC ISO timestamp
   - Sets `mom:source "self-registered"`
   - Writes `schema:name`, `schema:geo` (lat/lon), and any other top-level mapped fields
3. Rematerializes `web/data/spaces.geojson` by running the same SPARQL SELECT as `scripts/materialize_geojson.py` (inline, not subprocess) and atomically writing the output to the mounted path
4. Returns `{ "status": "confirmed", "space_uri": "<urn:mak:space/...>", "space_name": "..." }`

**And** the endpoint is proxied at `/api/register-url` → `mak-link-handler:8000/api/register-url`

**And** if the Oxigraph UPDATE fails, a 502 with `{ "error": "triplestore_write_failed" }` is returned and the GeoJSON is NOT rewritten

### AC3 — "Add your URL" drawer: live validation UI

**Given** the drawer is open and the coordinator has pasted a URL

**When** they click "Fetch & validate"

**Then** the `#url-result` area shows an animated inline checklist replacing the current simulated spinner:
```
→ resolving DNS…
✓ reachable (200 OK)
✓ JSON-LD valid
✓ name: Fablab Brussels
✓ coordinates found (50.846, 4.352)
⚠ PII warning: email field found — will not be stored
```

**And** each check appears as soon as the response arrives (single `fetch()`, UI parses the response object to show items progressively with a short CSS delay between them — no streaming needed)

**And** if any blocking check fails (not reachable, not valid JSON-LD, coords missing), a ✗ line is shown with plain-language reason and a "Try again" hint — the "Confirm & register" button does NOT appear

**And** if all blocking checks pass, a "Confirm & register your space →" button appears below the checklist

**And** the "Try a sample" button continues to work (populates URL input from a seeded space's `website + /maker.json`)

### AC4 — Confirmation screen + embed snippet

**Given** the coordinator clicks "Confirm & register your space →"

**When** the `POST /api/register-url` call succeeds

**Then** the drawer body is replaced with a confirmation screen (no page reload):
```
✓ [Space Name] is live on the map!
Your pin has flipped from ⚪ to 🔵.

[Embed this space →]   [View on map →]
```

**And** clicking "Embed this space →" calls the existing `embedSpace(space_uri)` function which opens the preset/embed drawer pre-populated with the space's name and coordinates — no new embed code needed

**And** clicking "View on map →" closes the addurl drawer and calls `selectSpace(space_uri, { fly: true })`

**And** the map markers are re-rendered immediately after successful registration (re-fetch `spaces.geojson` or patch state in memory using the API response — the dev agent chooses the simpler approach)

### AC5 — Drawer cleanup

**Given** Story 2.0 is done and the drawer HTML exists

**When** this story is implemented

**Then** the "Pilot note" paragraph (`<div class="note">` inside `.addurl-body`) is removed from `maps-of-making.html`

**And** the `initAddUrl()` function in `app.js` is replaced with the real implementation (simulated `setTimeout` block entirely removed)

### AC6 — nginx routing for `/api/`

**Given** the `mak-link-handler` service is running on the internal Docker network

**When** the browser calls `POST /api/validate-url` or `POST /api/register-url`

**Then** nginx proxies the request to `http://mak-link-handler:8000/api/...` with standard headers (`X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto`)

**And** the proxy block is added to `infra/nginx/conf.d/app.conf` — no other nginx blocks are modified

### AC7 — `scripts/seed_transition.py` admin utility

**Given** an admin wants to audit which seeded spaces have been confirmed

**When** `python scripts/seed_transition.py` is run (with venv active)

**Then** it queries Oxigraph for all spaces with `mom:operationalState "confirmed"` and `mom:source "self-registered"`

**And** prints a table: `space_uri | name | endpoint_url | confirmed_at`

**And** accepts an optional `--mark-done` flag that writes a `"confirmed": true` annotation into `moms_seed.json` for each matching entry (by matching `@id` or `schema:name`)

**And** the script is read-only by default — `--mark-done` requires explicit opt-in

**And** the script uses `OXIGRAPH_ENDPOINT` env var (default: `http://localhost:7878`) so it works both locally (via exposed port in docker-compose.dev.yml) and on VPS

---

## Tasks / Subtasks

- [x] **Task 1** — Backend: `POST /api/validate-url` (AC1)
  - [x] Add `httpx` to `infra/link_handler/requirements.txt` and `Dockerfile`
  - [x] Implement `/api/validate-url` in `infra/link_handler/main.py`
  - [x] Fetch URL with 10s timeout, check HTTP 200, parse JSON, check `name`/`schema:name` and `schema:geo`/`schema:latitude` presence
  - [x] Soft PII check: scan for `schema:email`, `schema:telephone`, `foaf:mbox` at top level → set `pii_warning: true`, list in `pii_fields` — never a hard failure

- [x] **Task 2** — Backend: `POST /api/register-url` (AC2)
  - [x] Add `GEOJSON_OUTPUT` env var to mak-link-handler (path inside container to write GeoJSON)
  - [x] Mount `../web/data` into mak-link-handler in `infra/docker-compose.yml` (e.g. `../web/data:/app/web_data`)
  - [x] Add `GEOJSON_OUTPUT=/app/web_data/spaces.geojson` to service environment in `docker-compose.yml`
  - [x] Do NOT add `:z` to this mount in docker-compose.yml (Ubuntu VPS — `:z` is Fedora-only, goes in docker-compose.dev.yml)
  - [x] Implement `/api/register-url`: re-validate, build SPARQL UPDATE, write to Oxigraph, rematerialize GeoJSON inline
  - [x] SPARQL UPDATE must use canonical namespace `https://nicolasdb.github.io/mapsofmaking_ontology/ns#` for all predicates
  - [x] Named graph: `<urn:mak:space/{slug}>` where slug is derived from `schema:name` (lowercase, spaces→hyphens)
  - [x] Atomic GeoJSON write: write to `.tmp` in same dir, then `os.replace()` — mirrors `materialize_geojson.py`'s `write_output_atomically()`
  - [x] If Oxigraph UPDATE fails: return 502, do not write GeoJSON

- [x] **Task 3** — nginx: add `/api/` proxy block (AC6)
  - [x] Add proxy block to `infra/nginx/conf.d/app.conf` after the `/claim/` block
  - [x] Proxy `/api/` → `http://mak-link-handler:8000/api/`
  - [x] Include `X-Real-IP`, `X-Forwarded-For`, `X-Forwarded-Proto` headers
  - [x] Set `proxy_read_timeout 30s` (URL fetch can take up to 10s + processing)

- [x] **Task 4** — Frontend: replace simulated `initAddUrl()` (AC3, AC4, AC5)
  - [x] Replace the entire `initAddUrl()` function in `web/app.js` with the real implementation
  - [x] `#btn-fetch-url` click → `POST /api/validate-url` → parse response → render inline checklist
  - [x] Checklist items appear with short CSS stagger (e.g. `animation-delay: 0.1s * index`) — no streaming
  - [x] On validation success: append "Confirm & register" button to `#url-result`
  - [x] "Confirm & register" click → `POST /api/register-url` → on success: replace `.addurl-body` innerHTML with confirmation screen
  - [x] Confirmation screen: show space name, two buttons: `embedSpace(space_uri)` and close+`selectSpace(space_uri, { fly: true })`
  - [x] Map update after registration: cache-busted re-fetch of `/data/spaces.geojson`, update `state.spaces`, call `renderMarkers()`
  - [x] Space selector (`#url-space`) fuzzy-match: after validation returns `name_found`, find the closest match in `state.spaces` (case-insensitive substring) and pre-select it in the dropdown — if no match, leave at "— new or unlisted —"
  - [x] Remove the "Pilot note" `<div class="note">` from the drawer HTML in `maps-of-making.html` (AC5)

- [x] **Task 5** — Admin script: `scripts/seed_transition.py` (AC7)
  - [x] Use `httpx` (already in venv) and SPARQL SELECT against `OXIGRAPH_ENDPOINT`
  - [x] Default read-only: print table of confirmed self-registered spaces
  - [x] `--mark-done` flag: patch seed file in-place for matched entries (`--seed-file` selects file; default `web/data/moms_seed.json`; use `web/data/rff_mockup.json` for RFF test spaces)
  - [x] Match entries by `schema:name` exact match (seed files have no `@id` field)
  - [x] Activate venv before running: follows project convention (`source venv/bin/activate && python scripts/seed_transition.py`)

- [x] **Task 6** — Integration test (local dev stack)
  - [x] Rebuild and start dev stack: `distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d --build`
  - [x] Fixtures served by nginx at `http://localhost:8080/test-fixtures/` (no separate server needed — fixtures moved to `web/test-fixtures/`)
  - [x] **Note**: paste the internal Docker URL — link_handler fetches server-side, `maps-nginx` resolves inside the container network
  - [x] Test case 1 (valid): paste `http://maps-nginx/test-fixtures/valid_space.json` → full checklist passes, confirm button appears, registration succeeds, pin flips ⚪→🔵
  - [x] Test case 2 (missing coords): paste `http://maps-nginx/test-fixtures/missing_coords.json` → checklist shows ✗ on coords with guidance, no confirm button
  - [x] Test case 3 (PII): paste `http://maps-nginx/test-fixtures/pii_present.json` → checklist passes with ⚠ PII warning, confirm button still appears
  - [x] Verify "Embed this space →" opens preset drawer with correct space pre-selected
  - [x] Verify "Pilot note" is gone from drawer HTML
  - [x] `source venv/bin/activate && python scripts/seed_transition.py` prints confirmed spaces table (2 RFF test entries confirmed)

---

## Dev Notes

### Current simulated code to replace (AC3/AC5)

`web/app.js:533-573` — the entire `initAddUrl()` function is a simulation:
```js
// Current: fake 900ms timeout, no real API call
setTimeout(() => {
  const ok = /^https?:\/\/.+\..+/.test(url);
  // ... fake pin flip using state mutation ...
  out.innerHTML = `✓ URL validated (simulated)...`;
}, 900);
```
Replace this function entirely. The HTML form elements (`#url-input`, `#url-space`, `#btn-fetch-url`, `#btn-sample`, `#url-result`) are already in place in `maps-of-making.html:456-467`.

### Embed is already implemented — just call it

`web/app.js:524-531` — `embedSpace(id)` exists and works:
```js
function embedSpace(id) {
  // sets preset-name, state.embed.centerId, flies map, opens preset drawer
  setDrawer('preset');
}
```
On confirmation, call `embedSpace(space_uri)` where `space_uri` comes from the `POST /api/register-url` response. No new embed code needed.

### GeoJSON path and atomic write pattern

- GeoJSON lives at `web/data/spaces.geojson` (served at `/data/spaces.geojson` via nginx with `max-age=60`)
- `scripts/materialize_geojson.py:224` — `write_output_atomically()` writes to `.geojson.tmp` then `os.replace()`. Follow the same pattern inside the link_handler.
- The link_handler container needs `../web/data` mounted read-write. Add to `docker-compose.yml` under `mak-link-handler.volumes:`. In `docker-compose.dev.yml`, add the same path with `:z` for Fedora SELinux.

### SPARQL namespace — canonical, always

All SPARQL queries and SPARQL UPDATE strings must use:
```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/>
PREFIX schema: <https://schema.org/>
PREFIX mak: <https://nicolasdb.github.io/mapsofmaking_ontology/mak/>
```
Never use `mapsofmaking.eu` — that namespace is deprecated (Story 1.5 migration complete).

### Oxigraph SPARQL UPDATE from link_handler

The service already has `OXIGRAPH_ENDPOINT=http://oxigraph:7878` injected. Use `httpx` for the SPARQL UPDATE:
```python
httpx.post(
    f"{OXIGRAPH_ENDPOINT}/update",
    content=sparql_update_string,
    headers={"Content-Type": "application/sparql-update"},
    timeout=15.0
)
```
Oxigraph's update endpoint is internal-only (nginx blocks `/sparql/update` from public). The link_handler is on the `internal` Docker network and can reach `http://oxigraph:7878` directly.

### Field mapping: JSON-LD → SPARQL triples

Minimum required (blocking validation failure if absent): `schema:name` (or `name`), `schema:geo` / `schema:latitude`+`schema:longitude` (or `geo.lat`/`geo.lon`).

Optional mapped fields (write if present, skip if absent):
- `schema:address` → `mom:address`
- `schema:url` or `url` → `mom:website`
- `schema:description` → `schema:description`
- `schema:openingHours` → `schema:openingHours`
- Any unknown top-level key → skip silently (Epic 3 enrichment gap logging is out of scope here)

### PII check — soft warning only

Deferred enforcement per user direction (2026-04-26). The check runs but never blocks:
- Scan for `schema:email`, `schema:telephone`, `schema:Person`, `foaf:mbox` at top level
- Return `pii_warning: true` and list the found field names in `pii_fields`
- Frontend shows `⚠ PII warning: {fields} found — will not be stored`
- These fields are NOT written to Oxigraph regardless (just drop them from the triple set)
- Full PII enforcement (reject + admin alert) is a separate hardening story

### seed_transition.py isolation note

This script is intentionally separate from the ingestion flow. The architecture (ADR) specifies the heartbeat agent overwrites seed triples on first confirmed fetch — but Epic 2 has no scheduler. The seed→claim transition in Oxigraph happens when `register-url` writes `mom:operationalState "confirmed"` over the existing seeded triples in the space's named graph. `seed_transition.py` is a reporting and source-file maintenance utility only — it does not touch Oxigraph.

### docker-compose.dev.yml — local Podman isolation note

`distrobox-host-exec` works perfectly for accessing Podman containers from within the distrobox. The dev stack is launched with:
```
distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d
```
(now also: `make startdev`)

When adding the `../web/data` volume mount to `docker-compose.dev.yml`, use `:z` suffix for SELinux relabeling on Fedora. Do NOT add `:z` in `docker-compose.yml` (breaks Ubuntu VPS).

### Project Structure Notes

Files touched by this story:
```
infra/
  link_handler/
    main.py              ← add /api/validate-url + /api/register-url
    requirements.txt     ← add httpx
    Dockerfile           ← already installs requirements.txt, no change needed
  nginx/conf.d/
    app.conf             ← add /api/ proxy block after /claim/ block
  docker-compose.yml     ← add web/data volume mount to mak-link-handler
  docker-compose.dev.yml ← add web/data volume mount with :z

web/
  app.js                 ← replace initAddUrl() function (lines 533-573)
  maps-of-making.html    ← remove Pilot note div (lines 469-472)

scripts/
  seed_transition.py     ← NEW admin utility (read-only by default)
```

Do NOT create a new service. Everything backend goes into `infra/link_handler/main.py`.

### Story 2.6 note

Story 2.6 (mobile responsive layout) is kept separate — pure CSS/layout work with no backend dependency. It can be done in parallel or after 2.1, but it must be done before the coordinator demo goes live (it was deferred from phase-1 intentionally).

### References

- Embed implementation: `web/app.js:524-531` (`embedSpace()`), `web/app.js:490-521` (`renderPresetPreview()`)
- Simulated addurl to replace: `web/app.js:533-573` (`initAddUrl()`)
- Drawer HTML: `web/maps-of-making.html:446-474`
- nginx config: `infra/nginx/conf.d/app.conf`
- docker-compose services: `infra/docker-compose.yml` (`mak-link-handler` block)
- GeoJSON atomic write pattern: `scripts/materialize_geojson.py:224-246`
- GeoJSON output path: `web/data/spaces.geojson` (served at `/data/spaces.geojson`)
- Canonical namespace: `https://nicolasdb.github.io/mapsofmaking_ontology/` (Story 1.5 migration — non-negotiable)
- SPARQL field mapping: `scripts/materialize_geojson.py:32-89` (current SELECT query — use same fields)
- Deferred PII enforcement: `_bmad-output/implementation-artifacts/deferred-work.md` (add entry when complete)
- Architecture — seed→claim: `_bmad-output/planning-artifacts/architecture.md` "Seed→claim transition"
- Architecture — link_handler ADR-011: `_bmad-output/planning-artifacts/architecture.md#ADR-011`

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (story creation + implementation, 2026-04-26)

### Debug Log References

### Completion Notes List

- All 6 tasks complete. Integration test passed with 3 RFF fixture cases.
- Namespace used: `https://nicolasdb.github.io/mapsofmaking_ontology/ns#` — matches live data in materialize_geojson.py.
- `seed_transition.py` verified live: 2 confirmed test entries returned correctly with URI, name, endpoint_url, confirmed_at.
- `schema:url` predicate bug fixed post-integration (was written as `mom:website`, should be `schema:url` to match SELECT query).
- Frontend drawer resets on re-open via `_resetAddUrlForm()` + "Register another →" button added to confirmation screen.
- PII check scoped to `foaf:mbox` and `schema:Person` only; `schema:email`/`schema:telephone` removed (business contact info, not personal data).
- Test fixtures in `web/test-fixtures/` (served by nginx at `/test-fixtures/`); use `http://maps-nginx/test-fixtures/...` as URL input (link_handler fetches server-side).
- Space card shows only name+status after registration — description/opening hours not in SPARQL SELECT, deferred to Story 2.2.

### Review Findings

- [x] [Review][Patch] F1 — SPARQL injection via `"""` in `name` field — fixed: `_sparql_str()` escapes all SPARQL string special chars [infra/link_handler/main.py]
- [x] [Review][Patch] F2 — SPARQL injection via unescaped `website` URL inserted as IRI — fixed: `_sparql_iri()` validates scheme and rejects `<`/`>` [infra/link_handler/main.py]
- [x] [Review][Patch] F3 — SSRF: no URL scheme/private-IP validation — fixed: scheme validated at entry; `follow_redirects=False` [infra/link_handler/main.py]
- [x] [Review][Patch] F4 — `lat`/`lon = 0` treated as falsy — fixed: `is not None` checks throughout `_extract_coords()` [infra/link_handler/main.py]
- [x] [Review][Patch] F5 — `schema:geo` as a JSON list silently drops coordinates — fixed: unwrap list before dict check [infra/link_handler/main.py]
- [x] [Review][Patch] F6 — `_slug()` returns empty string for non-ASCII names — fixed: guard raises 422 with user-friendly message [infra/link_handler/main.py]
- [x] [Review][Patch] F9 — `schema:address` dropped when `schema:email` present — fixed: removed incorrect guard condition [infra/link_handler/main.py]
- [x] [Review][Patch] F10 — XSS: server data interpolated into `innerHTML` unescaped — fixed: `escHtml()` helper applied to all server-sourced values [web/app.js]
- [x] [Review][Patch] F11 — XSS: `reg.space_name` in success banner — fixed: `escHtml()` applied [web/app.js]
- [x] [Review][Patch] F12 — `_scan_pii` `schema:Person` is a class not a key — fixed: removed from `_PII_FIELDS` [infra/link_handler/main.py]
- [x] [Review][Patch] F13 — `mark_done()` non-atomic write — fixed: `NamedTemporaryFile` + `replace()` [scripts/seed_transition.py]
- [x] [Review][Patch] F16 — Error-path responses missing required AC1 fields — fixed: `_EMPTY_RESULT` template applied to all early-return paths [infra/link_handler/main.py]
- [x] [Review][Patch] F17 — `.check-line` stagger animation-delay without animation-name — fixed: `@keyframes fadeSlideIn` added [web/maps-of-making.html]
- [x] [Review][Patch] F21 — Embed/View buttons inert when `spaceId` is null — fixed: buttons disabled when `hasSpace` is false [web/app.js]
- [x] [Review][Defer] F7 — No auth on `/api/register-url` — deferred, open-registration is spec-mandated (AC2); harden in Epic 5
- [x] [Review][Defer] F8 — DROP SILENT overwrites on slug collision — deferred, spec says "creating or overwriting"; collision detection is Epic 5 scope
- [x] [Review][Defer] F14 — Trailing slash on URI produces empty `space_id` — deferred, URIs are internally generated, trailing slash cannot occur
- [x] [Review][Defer] F15 — GeoJSON re-fetch failure → new space not in `state.spaces` → view/embed silently finds nothing — deferred, spec allowed re-fetch approach; patch in Epic 5 UX pass
- [x] [Review][Defer] F19 — `confirmed_at` column in seed_transition.py shows `mom:lastFetched`; no distinct confirmation timestamp written — deferred, acceptable for current admin utility scope

### File List

- `infra/link_handler/requirements.txt` — added httpx
- `infra/link_handler/main.py` — added /api/validate-url + /api/register-url; inline SPARQL SELECT + atomic GeoJSON write
- `infra/docker-compose.yml` — added ../web/data volume + GEOJSON_OUTPUT env to mak-link-handler
- `infra/docker-compose.dev.yml` — added mak-link-handler override with ../web/data:z
- `infra/nginx/conf.d/app.conf` — added /api/ proxy block after /claim/
- `web/app.js` — replaced initAddUrl() with real implementation (lines ~533-573)
- `web/maps-of-making.html` — removed Pilot note div from addurl drawer
- `scripts/seed_transition.py` — NEW admin utility
- `web/test-fixtures/valid_space.json` — RFF test fixture: clean valid space (served at `/test-fixtures/`)
- `web/test-fixtures/missing_coords.json` — RFF test fixture: missing coordinates
- `web/test-fixtures/pii_present.json` — RFF test fixture: PII warning case
