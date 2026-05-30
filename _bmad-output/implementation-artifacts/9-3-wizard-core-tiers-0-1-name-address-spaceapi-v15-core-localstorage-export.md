# Story 9.3: Wizard Core — Tiers 0 + 1 (Name + Address → SpaceAPI v15 Core; localStorage; Export) + Nominatim Proxy

Status: ready-for-dev

<!-- Scope note (2026-05-30): per operator decision, former Story 9.4 (Nominatim proxy) is MERGED
     into this story so the wizard ships as one demoable vertical slice. Former Story 9.5 (Bernard
     voice artifact) stays separate; this story uses the calibrated lines already locked in
     bernard-bible.md §9 as draft copy. -->

## Story

As a space coordinator using the wizard at `genjson.mapsofmaking.org`,
I want to enter my space name and address and walk through the SpaceAPI core fields at my own pace, with coordinates derived automatically and my progress saved in the browser,
so that I can produce a valid SpaceAPI v15 JSON file without understanding the schema — and stop and resume without losing work.

## Acceptance Criteria

> The wizard outputs a **raw SpaceAPI v15 document** (the machine-readable endpoint format the
> heartbeat polls), NOT the `mom:` JSON-LD shape. The Epic 3 transformer converts SpaceAPI → mom
> JSON-LD downstream. Do not emit `@context` / `mom:Space` here.

### AC1 — Single-page flow with two visible tier gates
**Given** the wizard page at `genjson.mapsofmaking.org`
**When** Story 9.3 lands
**Then** `genjson.js` renders into `#wizard-root` (the scaffold from Story 9.1) a single-page flow with two tier gates visible in the UI: **Tier 0** (floor) and **Tier 1** (SpaceAPI core)
**And** Bernard names themselves **once** on entry (full Bernard on the wizard path — bible §5):
> *"Hi, I'm Bernard (they/them) from 'Mother Sands'. Let's get your space on the map."*
**And** no character imagery appears (no crab/fort/silhouette — bible §5 hard rule); Bernard is the voice of the copy only.

### AC2 — Tier 0 floor gate (name + address → coordinates)
**Given** the wizard is freshly loaded (no draft)
**When** the coordinator fills `space` (name) and the address block (`address`, `city`, `postcode`, `country_code`)
**Then** coordinates (`lat` / `lon`) are derived automatically via the geocode proxy (AC6) and displayed inline as a `{lat}, {lon}` string (mini-map tile optional — inline string satisfies the AC)
**And** the "Continue →" button to Tier 1 is **disabled** until `space` + address + derived coordinates are present
**And** if the geocode proxy returns no result (`lat: null`), the coordinator can enter `lat`/`lon` manually and the floor gate still passes
**And** if the geocode proxy returns 503, the wizard shows *"Geocoding temporarily unavailable — enter coordinates manually"* and reveals the manual lat/lon inputs
**And** the Bernard floor-gate copy renders (bible §9): *"Name and address. That's the floor. Everything else, I'll derive."*

### AC3 — Tier 1 SpaceAPI core fields
**Given** the floor gate has passed
**When** the coordinator is on Tier 1
**Then** the wizard presents these SpaceAPI v15 core fields as **optional** progressive inputs: `logo` (URL), `url` (space website), `description`, `contact.email`, `contact.website`, `contact.mastodon`
**And** `state.open` renders as a **"skip for now"** affordance only — the FSM is deferred to Story 9.7; do not build the open/closed logic here
**And** each field has a one-line label and a max two-line hint (draft copy from bible; no long paragraphs)
**And** the Tier 1 exit banner renders (bible §9): *"Core's in. Other SpaceAPI apps can read this file as-is."*

### AC4 — Export valid SpaceAPI v15 JSON
**Given** the floor gate has passed
**When** the coordinator clicks "Export JSON" (available at any point after the floor gate)
**Then** a SpaceAPI v15 document containing all filled fields + derived coordinates is produced and downloaded as `{space_name_slug}.json`
**And** the document declares v15 compatibility (`"api_compatibility": ["15"]`) and nests location/contact/state per the bundled v15 schema (see Dev Notes — confirm exact nesting against the schema, do not guess field paths)
**And** the export is validated client-side against the **bundled** SpaceAPI v15 JSON Schema (no external fetch — CSP forbids it)
**And** if validation fails, a **non-blocking** inline warning lists the invalid fields; **export is NOT blocked** (per data-integrity principle — name the gap, never silently drop)

### AC5 — localStorage auto-save & resume
**Given** the coordinator has entered any field
**When** any field value changes
**Then** `localStorage.setItem('genjson_draft', JSON.stringify(draftObject))` is called — single slot, keyed exactly `genjson_draft` (must match the key Story 9.2 drawer reads)
**And** on page load, if `localStorage.getItem('genjson_draft')` is non-null, the wizard pre-fills all fields and shows the Bernard warning (bible §9): *"Your progress is saved in this browser. Hard-refresh or clearing site data wipes it. Export at any point if you want a copy outside the browser."*
**And** a "Clear & start over" link resets the draft and form behind a confirmation dialog: *"This will erase your saved progress. Continue?"* — no accidental wipes
**And** if `?resume=1` is present but `localStorage.getItem('genjson_draft')` is null, the wizard loads at Tier 0 with no pre-fill and **no error** — `?resume=1` is a hint, not a requirement

### AC6 — Nominatim geocode proxy (merged from former Story 9.4)
**Given** `mak-link-handler` (FastAPI, `infra/link_handler/main.py`)
**When** Story 9.3 lands
**Then** a `POST /api/geocode` endpoint exists accepting `{ "address": str, "city": str, "postcode": str, "country_code": str }`
**And** the handler calls `geopy.Nominatim` with `user_agent="mapsofmaking-genjson/1.0 (contact: nicolas.de.barquin@gmail.com)"`, rate-limited to 1 req/s via a module-level geopy `RateLimiter` wrapper
**And** on success returns `{ "lat": float, "lon": float, "display_name": str }` (HTTP 200)
**And** on no-result returns `{ "lat": null, "lon": null, "display_name": null }` (HTTP 200 — not an error; wizard handles null per AC2)
**And** on Nominatim timeout/network error returns HTTP 503 with `{ "error": "geocoding_unavailable" }`
**And** the endpoint is nginx rate-limited at max 2 req/s per IP (`limit_req_zone`), returning 429 on excess
**And** `geopy` is added to `infra/link_handler/requirements.txt`
**And** the proxy follows the existing `scripts/normalize_vow.py` `geopy.Nominatim` User-Agent + rate-limit pattern — do not diverge

### AC7 — CSP same-origin routing for /api/geocode (the seam)
**Given** the genjson CSP is `default-src 'self' 'unsafe-inline'` (`infra/gateway-nginx/08-genjson-mapsofmaking.conf:46`)
**When** the wizard calls the geocode proxy
**Then** the call is **same-origin** from `genjson.mapsofmaking.org` (a relative `fetch('/api/geocode')`) — cross-origin fetch is blocked by CSP `connect-src` falling back to `'self'`
**And** nginx routes `genjson.mapsofmaking.org/api/` to `mak-link-handler` (new `location /api/` block in `08-genjson-mapsofmaking.conf` and/or the maps-nginx app.conf) so the relative fetch resolves — without this, geocoding 404s

### AC8 — Gating test + operator confirmation
**Gating test** — `test_wizard_tier0_tier1_export` (browser E2E, **Playwright** — new test infra, set up in this story): fill name + address → geocode call → lat/lon derived → fill two Tier 1 fields → click Export → validate downloaded JSON against the bundled SpaceAPI v15 schema → reload page → assert fields pre-filled from localStorage.
**And** `test_geocode_proxy` (live endpoint, real Nominatim): POST `{address:"Rue Royale 1", city:"Brussels", postcode:"1000", country_code:"BE"}` → assert `lat ≈ 50.85`, `lon ≈ 4.36`; POST an unmatchable address → assert `lat: null`; 3 rapid POSTs → third returns 429.
**And** operator visual confirmation: exported JSON validates and the map registers it correctly via the Epic 2 Story 2.1 fetch-and-validate flow.

## Tasks / Subtasks

- [ ] **Geocode proxy backend** (AC6, AC7)
  - [ ] Add `geopy` to `infra/link_handler/requirements.txt`
  - [ ] Add `POST /api/geocode` to `infra/link_handler/main.py` mirroring `scripts/normalize_vow.py` Nominatim usage (module-level `RateLimiter`, identical User-Agent)
  - [ ] Add `limit_req_zone` (2 req/s/IP) + `location /api/` proxy block routing genjson → `mak-link-handler` in nginx config
  - [ ] Write `test_geocode_proxy` (live Nominatim + rate-limit assertion)
- [ ] **Test infra** (AC8)
  - [ ] Add Playwright as devDependency in `package.json`; create `playwright.config.*`; document `npx playwright test` in story isolation notes
- [ ] **Bundle SpaceAPI v15 schema** (AC4) — obtain the official v15 JSON Schema, vendor it into `web/genjson/` (e.g. `spaceapi-v15.schema.json`), load it locally (no CDN)
- [ ] **Wizard shell + Bernard intro** (AC1) — render two-tier flow into `#wizard-root`; one-time Bernard self-intro; no imagery
- [ ] **Tier 0 floor gate** (AC2) — name + address inputs; debounced `fetch('/api/geocode')`; inline `{lat},{lon}` preview; manual fallback on null/503; gated Continue button
- [ ] **Tier 1 core fields** (AC3) — optional progressive inputs incl. nested `contact.*`; `state.open` = "skip for now" stub only; one-line labels + ≤2-line hints; exit banner
- [ ] **Export** (AC4) — assemble v15 doc (`api_compatibility:["15"]`); client-side schema validation; non-blocking warning on fail; download `{slug}.json`
- [ ] **localStorage** (AC5) — write on change (key `genjson_draft`); pre-fill + warning on load; Clear-&-start-over with confirm; `?resume=1` graceful null handling
- [ ] **Font handling under CSP** (see Dev Notes) — self-host or system-mono fallback for the `.bernard-voice` register; do NOT add a Google Fonts `<link>` (CSP will block it)
- [ ] **E2E gating test** `test_wizard_tier0_tier1_export` (AC8) + operator visual confirmation via Story 2.1 flow

## Dev Notes

### ⚠️ CSP trap — no external fonts/CDN on genjson (highest-risk item)
The genjson subdomain CSP is `default-src 'self' 'unsafe-inline'` (`infra/gateway-nginx/08-genjson-mapsofmaking.conf:46`). The MoM map (`web/maps-of-making.html:9`) loads `Special Elite` / `JetBrains Mono` via a Google Fonts `<link>` — **the wizard CANNOT do this**; the browser will block it and the `.bernard-voice` register will silently fall back. Options: (a) self-host the woff2 in `web/genjson/` and `@font-face` it from `'self'`, or (b) use a system monospace stack as the Bernard register. Canonical font is locked in Story 9.5 — pick a working CSP-safe option now and leave a note. Likewise `fetch` is restricted to same-origin (AC7).

### SpaceAPI v15 output shape (confirm against the bundled schema — do not guess)
The wizard emits raw SpaceAPI v15, not `mom:` JSON-LD. Top-level v15 fields in scope: `api_compatibility: ["15"]`, `space` (name), `logo`, `url`, `location` (carries `lat`, `lon`, `address`, `country_code`), `contact` (`email`, `website`, `mastodon`), `state` (deferred — Story 9.7). The AC names address parts as `address/city/postcode/country_code`; **the exact nesting of these inside `location` must be verified against the vendored v15 schema** before assembling the export — historically a source of silent validation failures. Existing SpaceAPI handling lives in `scripts/spaceapi_extract/` and `tests/test_spaceapi_extract*.py` (note: current fixtures are **v14** — `web/test-fixtures/spaceapi_v14_*.json`; v15 differs, treat v14 as structural reference only).

### Geocode proxy — reuse the existing pattern
`scripts/normalize_vow.py` already uses `geopy.Nominatim`. Match its User-Agent and 1-req/s rate-limit exactly (AC6) — divergence risks Nominatim blocking the contact identity. The link_handler is FastAPI (`infra/link_handler/main.py`); see `test_schema.py` / `conftest.py` for the existing test pattern.

### Bernard voice — full presence on the wizard path
Per `bernard-bible.md` §5: the wizard is **full Bernard** (vs. the drawer's ~20% bleed). Bernard names themselves **once** on entry (§9 wizard intro line), they/them always. Voice = "Ron Swanson on a North Sea fort": short sentences, **no exclamation marks**, observation over explanation, no shaming, **never rank the user's choices**. Forbidden patterns (§3): "most spaces leave this blank", "keep it simple", "you can do better than them". Use the §9 calibrated lines **verbatim** for floor gate, Tier 1 exit, and localStorage warning. Em-dash (`—`) opens Bernard's spoken lines (§4). Story 9.5 will replace draft hint copy with the curated artifact — write field hints to be easily swappable.

### Source tree
- `web/genjson/index.html` (scaffold from 9.1 — `#wizard-root` + `genjson.js`), `web/genjson/genjson.js` (currently `// placeholder` — this is the build target)
- `infra/link_handler/main.py`, `infra/link_handler/requirements.txt`
- `infra/gateway-nginx/08-genjson-mapsofmaking.conf`, `infra/nginx/conf.d/app.conf` (line ~107 `location /genjson/`)
- `package.json` (currently only cheerio/puppeteer — add Playwright)

### Previous story intelligence (9.2 — done)
- 9.2 established the drawer CTA that opens `genjson.mapsofmaking.org/?resume=1` when a `genjson_draft` exists in localStorage. **This story is the writer of that key** (9.2 only reads it). The key name `genjson_draft` and the `?resume=1` contract are fixed by 9.2 — do not rename.
- 9.2 used a `.bernard-voice` class with Special Elite (test font). On genjson that font won't load over CDN (CSP) — see font note above.
- 9.2 confirmed the em-dash dialogue convention and the 20%-bleed drawer vs. full-Bernard-wizard split.

### Project Structure Notes
- Vanilla JS, no build step, no framework (CSP `'self'`; matches the no-tracking/no-login Story 9.1 intent). Single `genjson.js` rendering into `#wizard-root`.
- Vertical slice (per CLAUDE.md): frontend + geocode backend + nginx seam ship together so the wizard is demoable end-to-end.

### References
- [Source: _bmad-output/planning-artifacts/epics.md#Story 9.3] and #Story 9.4 (merged)
- [Source: _bmad-output/planning-artifacts/bernard-bible.md §3, §4, §5, §9]
- [Source: infra/gateway-nginx/08-genjson-mapsofmaking.conf:46 — CSP]
- [Source: scripts/normalize_vow.py — Nominatim pattern]
- [Source: _bmad-output/implementation-artifacts/9-2-drawer-ux-on-mom-map-bernard-one-liner-url-input-cta.md — genjson_draft key + resume contract]
- [Source: memory/feedback_data_integrity_no_silent_drops.md — non-blocking validation warning, name the gap]

## Isolation Notes
- **Frontend:** static — serve `web/genjson/` via `python3 -m http.server` or the maps-nginx container; open `genjson.js` against `#wizard-root`. Activate venv for any Python (`source venv/bin/activate`).
- **Backend (geocode proxy):** lives in `mak-link-handler`. Local stack: `distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up`. `distrobox-host-exec` reaches the podman containers from inside the distrobox.
- **nginx changes** (rate-limit + `/api/` route): reload nginx after edit; verify same-origin fetch resolves (AC7). `:z` SELinux flag only in `docker-compose.dev.yml`, never in `docker-compose.yml`.
- **Playwright:** new dev dependency — `npx playwright install` may be needed locally.

## Out of Scope
- `state.open` FSM (open/closed cascading logic) — Story 9.7. Here it is a "skip for now" stub only.
- Tier 2 `mom:` fields (opening_hours, memberOf, sdgs) — Story 9.6.
- Tier 3 `ext_fab` fields — Story 9.10.
- Curated Bernard voice artifact + tone approval — Story 9.5 (this story uses bible draft copy).
- URL-fetch pre-fill / validator mode — Story 9.9.
- Canonical font lock — Story 9.5 (pick a CSP-safe working option now).

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
