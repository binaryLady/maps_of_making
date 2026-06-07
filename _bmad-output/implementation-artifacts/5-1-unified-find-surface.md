# Story 5.1: Unified "Find" Surface — Search + Filter Merged, Results Visible on the Map

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a maker browsing the map,
I want a single "Find" surface where typing a name and toggling category chips both
refine the same set of spaces — with matches made clearly visible on the map and
clickable from the results list,
so that I can locate a space whether I know its name or only know the kind of place
I'm after, and I never lose my matches in a sea of tiny dots or a drawer I forgot to open.

## Context & Decisions

- Search and filter today are the **same client-side mechanism** (`filteredSpaces()`
  over the cached `spaces.geojson`; the SPA never queries Oxigraph — Story 1.5 contract)
  split across **two disconnected drawers**: the text input sits in `#drawer-search`,
  the clickable results in `#drawer-filters`. Typing filters the map but the clickable
  list is buried — results *feel* unclickable though `selectSpace(id,{fly:true})` is
  already wired.
- At world zoom (z2) matches vanish: `refreshSpacesLayer()` rebuilds the GL source from
  matches only, leaving 2–3px dots lost in the field.
- **Decision (Nicolas, 2026-06-07):** collapse search + filter into ONE "Find" surface
  (text input + faceted chips + one shared results list + one shared map treatment).
  Two doors — *recall* (type) and *browse* (chips) — into the same flat-data room.
- **"Ask the map"** (natural-language → SPARQL over Oxigraph) is the distinct **third**
  tool, Epic 6 — explicitly NOT this story.
- **Out of scope (stays deferred → Epic 5):** splitting the status filter into orthogonal
  health-vs-door-state axes (deferred-work.md); any materialiser/backend change; moving
  the SPA to live SPARQL.
- **Known data gaps confirmed in the geojson** (worked around client-side here, not by
  backend change): `country` full-name empty on all 875 features (only `country_code`
  populated, 677/875); search not accent-tolerant.

## Acceptance Criteria

### AC1 — One Find surface replaces the two drawers
**Given** the map is loaded
**When** I open Find from the topbar
**Then** a single panel shows, in order: a text input, the faceted chips
(Network / Country / Status / Specialty) with real counts from the dataset, a result
count, a Reset control, and the clickable results list
**And** the separate top "Search" drawer and its topbar button no longer exist
**And** typing in the input and toggling any chip both refine the **same** live result
set (count, list, and map update together with no reload)

### AC2 — Matches are visible on the map at every zoom
**Given** a Find is active (text and/or chips)
**When** the map renders
**Then** non-matching spaces are **dimmed to a low-opacity ghost field** (kept for
geographic context) rather than removed, and matching spaces keep full colour
**And** matched dots honour a **minimum radius floor** so they remain visible and
clickable even at world zoom (z2)
**And** the camera **auto-fits to the match set** when 2–~60 spaces match (padded,
sensible max zoom); a single match flies to it; zero or very large sets leave the
camera where it is
**And** camera movement is debounced so per-keystroke typing does not yank the view
**And** `prefers-reduced-motion` is respected

### AC3 — Results list is clickable from the Find surface
**Given** the Find results list is showing matches
**When** I click a result row
**Then** that space is selected, its detail drawer opens, and the map flies to and
highlights it
**And** the currently selected row is visually indicated in the list

### AC4 — Search is accent-tolerant and country-aware
**Given** I type a query
**When** results compute
**Then** matching is case-insensitive and **accent-insensitive** ("électronique"
matches "electronique" and vice-versa) across name, city, specialties, and network
**And** a country query matches by both full name and code (e.g. "France" and "FR"
both surface French spaces), despite the empty `country` field, by falling back to
`country_code` → label
**And** the result row meta no longer renders an empty `", "` when city/country are
blank

### AC5 — Empty state nudges instead of dead-ending
**Given** a Find produces zero results
**When** the results list renders
**Then** it shows "No spaces match — try widening your Find" paired with a working
**Reset** control that clears all text + chip filters (FR10, UX-DR11)

### AC6 — Shareable + session-persistent Find state
**Given** I have an active Find
**When** I copy the preset/share URL or reload with `?q=…&country=…&status=…&specialty=…&networks=…`
**Then** the text query and chip selections are encoded in the URL and restored on load
(FR8)
**And** Find state persists across closing and reopening the panel within the session
(FR9)

## Tasks / Subtasks

- [ ] **Task 1 — Merge the two drawers into one Find panel** (AC1)
  - [ ] `web/maps-of-making.html`: move `#search-input` (+ hints) to the top of the
        Find drawer body above the chips; rename head to "Find"; delete the
        `#drawer-search` block; collapse the topbar two-button seg to one **Find**
        button (keep `#results-count`).
  - [ ] `web/app.js`: remove `#btn-search`/`drawer-search` open + esc handlers and the
        `search` case in `setDrawer()`; keep the input listener driving `state.search`.
- [ ] **Task 2 — Hide→dim + visibility floor on the GL field** (AC2)
  - [ ] `refreshSpacesLayer()`: build the FC from **all** `state.spaces`; compute the
        match set via `filteredSpaces()`; apply `match` feature-state per feature.
  - [ ] `spaces-point` paint: opacity `case` (match 1 / non-match ~0.12, only when a
        Find is active); matched radius floor (~5px min) wrapping `radiusExpr`; matched
        stroke emphasis; mirror in `applyLadderPaint()` after setStyle.
- [ ] **Task 3 — Auto-fit camera to matches** (AC2)
  - [ ] `fitToMatches()`: fitBounds for 2–~60 matches (pad ~80, maxZoom ~11), flyTo
        z13 for a single match, no-op otherwise; debounce (~350ms); call from input +
        chip handlers (not on cold load).
- [ ] **Task 4 — Accent-tolerant + country-aware search** (AC4)
  - [ ] `filteredSpaces()`: NFD-strip-diacritics normalise for query + haystack; replace
        dead `s.country` with `countryLabel(s.country_code)` + raw code.
  - [ ] `renderResultsList()`: guard the row meta against empty city/country.
- [ ] **Task 5 — Empty-state nudge** (AC5)
  - [ ] `renderResultsList()` zero-result branch: nudge copy + inline Reset reusing the
        existing reset action.
- [ ] **Task 6 — Verify URL + persistence** (AC6)
  - [ ] Confirm `q`/chips round-trip through `applyUrlParams()` + preset builder with the
        merged input; confirm in-memory state survives panel close/reopen. (Expected:
        already satisfied — verify, don't rebuild.)

## Dev Notes

### Confirmed code locations (verified 2026-06-07)

**`web/app.js`** (1673 lines):
- `buildFeatureCollection(spaces)` — line 272. Receives an array of spaces, builds GL
  FeatureCollection. **Critical:** currently called with `filteredSpaces()` result only —
  the dim approach requires calling it with **all** `state.spaces` and adding a `match`
  boolean property per feature.
- `refreshSpacesLayer()` — line 384. Entry point: calls `buildFeatureCollection(filteredSpaces())`,
  sets source data, calls `applyLadderPaint()`. **Must change:** pass all spaces, compute
  match set separately, set feature-state `match` per feature after source is updated.
- `ensureSpacesLayers()` — line 314. Adds `spaces-glow`, `spaces-point`, `spaces-glyph`.
  Current `circle-opacity: 1.0` (line 344) — flat, no dim. This is where dim paint lives
  after the change (or override via `applyLadderPaint()`). Feature-state `selected` is
  already used at line 346 — `match` follows the same pattern.
- `applyLadderPaint()` — line 373. Called after every `setStyle`. Sets `circle-color`,
  `circle-radius`, `circle-stroke-color`. **Add** `circle-opacity` case here too so it
  survives basemap theme changes.
- `radiusExpr(DOT_SCALE)` — line 304. `RADIUS_STOPS` at line 302; `DOT_SCALE = 0.5`.
  The matched-radius floor (AC2) needs a `case` wrapping this: if match → max(radiusExpr, floor),
  else radiusExpr. Use a `['max', radiusExpr(DOT_SCALE), MIN_FLOOR_PX]` expression —
  MapLibre GL supports `['max', ...]` in paint expressions.
- `filteredSpaces()` — line 573. Returns filtered array. Haystack line 585 uses
  `s.country` (always empty) + `s.country_code` (populated). Accent-tolerance fix: use
  `str.normalize('NFD').replace(/[̀-ͯ]/g, '')` on both query and haystack.
- `renderResultsList(visible)` — line 673. Zero-result branch at line 676: update to nudge
  copy (AC5). Meta line 686: `${s.city}, ${s.country}` — `s.country` is always `""`,
  replace with `countryLabel(s.country_code)` and guard against empty city.
- `setDrawer(name)` — line 1414. Map object at line 1420: `'filters': 'drawer-filters'`,
  `'search': 'drawer-search'`. Rename strategy: add `'find': 'drawer-find'`, repurpose
  the existing `drawer-filters` element as `drawer-find` (or rename its id).
- `syncTopbar()` — line 1454. Sets aria-pressed for `#btn-filters` and `#btn-search`.
  Update to single `#btn-find` after merger.
- `wireUI()` — line 1464. Buttons wired at line 1473–1474. Search input handler at line
  1551. Reset handler at line 1557 (already clears `state.search` + chips — keep as-is).
- `applyUrlParams()` — line 1132. Already handles `q`/`country`/`status`/`specialty`/
  `networks` round-trip. Task 6 is a verify-only task — don't rebuild.
- `countryLabel(c)` — line 668. Already maps code → labelled string. Use for search
  haystack country fallback.

**`web/maps-of-making.html`** (715 lines):
- Topbar buttons at line 530–535: two-button `seg` (`#btn-filters`, `#btn-search`).
  Collapse to one `#btn-find`.
- `#drawer-search` — line 553: top-positioned `div.search-drawer` with just `#search-input`
  + hints. **Delete this block.**
- `#drawer-filters` — line 562: left `aside.drawer` with drawer-head, chips, reset, and
  `#results-list`. **Move** `#search-input` + hints to top of `drawer-body` above the
  chips; rename id to `drawer-find`; update `aria-label`; update drawer-head title to "Find".
- `#btn-reset-filters` — line 586. Keep id (JS handler at line 1557 uses it); or rename
  to `#btn-reset-find` if you also update the JS reference.
- `#results-list` — line 589. Already inside `drawer-filters`; stays in the merged drawer.

### GL dim + match feature-state pattern

The existing `selected` feature-state (line 346) is the model. After calling `src.setData(fc)`:

```js
// Clear all match states first, then set matching ones
state.spaces.forEach(s => map.setFeatureState({ source: 'spaces', id: s.id }, { match: false }));
matchSet.forEach(s => map.setFeatureState({ source: 'spaces', id: s.id }, { match: true }));
```

Then in paint (inside `ensureSpacesLayers` or applied via `applyLadderPaint`):
```js
'circle-opacity': ['case',
  ['boolean', ['feature-state', 'match'], true],  // default true → full opacity when no find active
  1.0,
  0.12
]
```

"No find active" detection: when `state.search === ''` AND all filter sets are empty,
skip setting feature-states and use flat opacity 1.0 (existing behaviour). Only dim when
a find is actually active.

### fitToMatches sketch

```js
function fitToMatches(matches) {
  if (!matches.length || matches.length > 60) return; // no-op for 0 or large sets
  if (matches.length === 1) {
    map.flyTo({ center: [matches[0].coordinates.lon, matches[0].coordinates.lat], zoom: 13 });
    return;
  }
  const lons = matches.map(s => s.coordinates.lon);
  const lats = matches.map(s => s.coordinates.lat);
  map.fitBounds([[Math.min(...lons), Math.min(...lats)], [Math.max(...lons), Math.max(...lats)]],
    { padding: 80, maxZoom: 11 });
}
```
Debounce: use a module-level `let _fitTimer` + `clearTimeout`/`setTimeout(fn, 350)` in
the input handler. Do NOT call on cold load (`applyUrlParams` initial run) — only on
user input.

### No backend, materialiser, or SPARQL changes.
The empty `country` full-name field is a data/materialiser concern — noted, not fixed here.
Visual treatment (dim opacity value, matched radius floor, fit maxZoom) is first-pass —
**tune live, slice-reviewed with Nicolas before sign-off.**

## Verification

1. Local stack up, 875 spaces over cached geojson.
2. Open Find — one panel: input + chips (real counts) + count + Reset + results.
3. `électro` and `electro` → same matches highlight; field dims; camera fits; list updates.
4. `france` and `FR` → both surface French spaces.
5. At z2, 3-result search → matches visibly larger and clickable; row click flies + opens drawer.
6. Chip-only Find (no text) → same dim + fit + list behaviour.
7. Zero results → "try widening your Find" + working Reset.
8. Reload `?q=wood&country=DE` → restored; share/preset URL round-trips.
9. `prefers-reduced-motion` honoured.
