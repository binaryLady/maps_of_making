# Story 2.0: UI Dataset Toggle and User Preferences Persistence

Status: ready-for-dev

## Story

As a user browsing the map,
I want to toggle the RFF mockup dataset on/off and have my display preferences remembered across visits,
so that I can control what I see on the map and not lose my settings every time I reload.

## Acceptance Criteria

### AC1 — Dataset source field in materialized data

**Given** `scripts/materialize_geojson.py` runs a SPARQL query against Oxigraph

**When** the query executes

**Then** each space feature's `properties` includes a `source` field:
- VOW spaces: `"source": "scraped-vow"`
- RFF mockup spaces: `"source": "mock-rff"`
- Any space without `mom:source`: `"source": null`

### AC2 — Dataset toggle in the Tweaks panel

**Given** the Tweaks drawer is open

**When** the user clicks the "Show health network" toggle

**Then** spaces with `source === "mock-rff"` are hidden from the map (and included when toggled back on)

**And** the count in the top bar updates to reflect visible spaces only

**And** the toggle state is clearly shown (pressed/unpressed visual feedback matching existing tweak button style)

### AC3 — Default state: mock data visible

**Given** no stored preference exists

**When** the map loads

**Then** the dataset toggle defaults to `on` (mock-rff spaces are visible)

**Why:** Demo contexts need RFF mockup visible by default; users can opt out. Epic 4 admin dashboard gets a separate SPARQL-level toggle (Story 4.4); this is the public map layer switch.

### AC4 — localStorage persistence for tweaks

**Given** the user changes any tweak setting (mapStyle, density, pulse) or the dataset toggle

**When** the page is reloaded

**Then** the map restores the user's last values for all tweaks and the dataset toggle

**And** the Tweaks panel buttons reflect the restored state (correct `aria-pressed` values)

### AC5 — Graceful fallback for missing/corrupt localStorage

**Given** localStorage is unavailable (private mode) or contains malformed JSON

**When** the map loads

**Then** it silently falls back to defaults with no error

**And** no exception propagates to the user

### AC6 — No regression on existing UX

**Given** the patches from Story 1.5 code review are applied (GeoJSON FeatureCollection format)

**When** all changes for this story are applied

**Then** all existing filters (country, specialty, status, network), search, detail drawer, and graceful failure banner work identically to Story 1.5

---

## Tasks / Subtasks

### Phase 1: Backend — add `source` to materialized GeoJSON (AC1)

- [ ] Add `mom:source` to SPARQL query in `scripts/materialize_geojson.py` (AC: 1)
  - [ ] Add `?source` to SELECT clause
  - [ ] Add `OPTIONAL { ?spaceUri mom:source ?source }` inside the `GRAPH ?spaceGraph` block
  - [ ] Add `?source` to GROUP BY clause
  - [ ] Add `source` field to `binding_to_space()` return value: `binding.get("source", {}).get("value")` (Python `None` if absent)
- [ ] Re-run `python scripts/materialize_geojson.py` and verify `source` field present in output (AC: 1)
  - [ ] Spot-check: 40 RFF features have `"source": "mock-rff"`, 566 VOW have `"source": "scraped-vow"`

### Phase 2: Frontend — dataset toggle UI (AC2, AC3)

- [ ] Add `showMockData: true` to `state.tweaks` in `web/app.js` (AC: 3)
- [ ] Update `filteredSpaces()` to check `state.tweaks.showMockData` (AC: 2)
  - [ ] Add: `if (!state.tweaks.showMockData && s.source === 'mock-rff') return false;`
  - [ ] Place BEFORE other filter checks (fast short-circuit)
- [ ] Add toggle row to tweaks panel in `web/maps-of-making.html` (AC: 2)
  - [ ] Add a new `<div class="tweak-row">` after the "Show pulse" row:
    ```html
    <div class="tweak-row">
      <label>Health network (RFF mockup)</label>
      <div class="opts" data-tweak="showMockData">
        <button data-val="true" aria-pressed="true">show</button>
        <button data-val="false" aria-pressed="false">hide</button>
      </div>
    </div>
    ```
  - [ ] Note: `data-val="true"/"false"` are strings — the existing wireUI() tweak handler sets `state.tweaks[key] = b.dataset.val` (string). `filteredSpaces()` must compare `state.tweaks.showMockData !== 'false'` (not `=== true`)
- [ ] Verify `updateCounts()` correctly reflects filtered count when toggle is off (AC: 2)

### Phase 3: localStorage persistence (AC4, AC5)

- [ ] Add `loadPreferences()` function to `web/app.js` (AC: 4, 5)
  - [ ] Key: `'mom_preferences'`
  - [ ] Try/catch around `JSON.parse(localStorage.getItem('mom_preferences'))` (AC: 5)
  - [ ] Merge loaded values into `state.tweaks` (only known keys: mapStyle, density, pulse, showMockData)
  - [ ] Call `loadPreferences()` at boot, BEFORE `buildFilterChips()` and `applyTweaks()`
- [ ] Add `savePreferences()` function (AC: 4)
  - [ ] Writes `JSON.stringify(state.tweaks)` to `localStorage.setItem('mom_preferences', ...)`
  - [ ] Try/catch to handle storage quota exceeded or private mode (AC: 5)
- [ ] Call `savePreferences()` whenever a tweak changes (AC: 4)
  - [ ] In `wireUI()` tweaks event handler: add `savePreferences()` call after `applyTweaks()`
  - [ ] The existing handler already covers all tweaks including the new toggle (data-tweak="showMockData")
- [ ] Sync Tweaks panel button `aria-pressed` states after `loadPreferences()` (AC: 4)
  - [ ] Add `syncTweakButtons()` helper that reads `state.tweaks` and updates all `.opts button[aria-pressed]` in the tweaks panel
  - [ ] Call after `loadPreferences()` in boot

### Phase 4: Integration test (AC6)

- [ ] Start local stack: `distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up`
- [ ] Re-run materialization: `python scripts/materialize_geojson.py`
- [ ] Open `http://localhost:8080/`: verify map loads 606 pins (566 VOW + 40 RFF)
- [ ] Toggle "hide" → verify pin count drops by 40, RFF spaces disappear
- [ ] Toggle back "show" → verify 606 pins return
- [ ] Change map style → reload page → verify style is restored
- [ ] Open DevTools → Application → localStorage → verify `mom_preferences` key exists with correct JSON
- [ ] Verify graceful fallback: corrupt `mom_preferences` manually in DevTools, reload → defaults apply, no error

---

## Dev Notes

### `mom:source` in Oxigraph

Both seed files already contain `mom:source` as an RDF property:
- VOW spaces (`web/data/moms_seed.json`): `"mom:source": "scraped-vow"`
- RFF mockup (`web/data/rff_mockup.json`): `"mom:source": "mock-rff"`

SPARQL addition (place inside `GRAPH ?spaceGraph` block, alongside other OPTIONAL clauses):
```sparql
OPTIONAL { ?spaceUri mom:source ?source }
```

Also add to GROUP BY: `?source`

### Tweak value types: string not boolean

The existing tweak wireUI handler in `app.js` stores button `data-val` directly as a string into `state.tweaks`:
```js
state.tweaks[key] = b.dataset.val;   // always a string
```

So `state.tweaks.showMockData` will be `"true"` or `"false"` (strings), not JS booleans.

The `filteredSpaces()` filter must use:
```js
if (state.tweaks.showMockData === 'false' && s.source === 'mock-rff') return false;
```

The initial state sets `showMockData: true` (boolean), but after first user interaction it becomes a string. After localStorage restore it's also a string. Make `filteredSpaces()` robust to both:
```js
if (String(state.tweaks.showMockData) === 'false' && s.source === 'mock-rff') return false;
```

### localStorage key and structure

```js
// Stored value (example):
{
  "mapStyle": "dark",
  "density": "compact",
  "pulse": "off",
  "showMockData": "false"
}
```

### syncTweakButtons() pattern

After `loadPreferences()`, the tweaks panel HTML buttons need their `aria-pressed` synced to reflect restored state:

```js
function syncTweakButtons() {
  $$('.tweaks .opts').forEach((group) => {
    const key = group.dataset.tweak;
    const val = String(state.tweaks[key]);
    group.querySelectorAll('button').forEach((b) => {
      b.setAttribute('aria-pressed', b.dataset.val === val ? 'true' : 'false');
    });
  });
}
```

Call order in boot:
```js
loadPreferences();    // merge stored tweaks into state.tweaks
initMap();
buildFilterChips();
initAddUrl();
wireUI();
syncTweakButtons();   // sync button states AFTER wireUI adds event listeners
updateCounts();
applyTweaks();        // apply restored style/density/pulse
```

### Files to modify

```
maps_of_making/
├── scripts/
│   └── materialize_geojson.py   ← Add mom:source to SPARQL + binding_to_space()
├── web/
│   ├── app.js                   ← Add showMockData filter, loadPreferences, savePreferences, syncTweakButtons
│   ├── data/spaces.geojson      ← Regenerated (not committed — runtime artifact)
│   └── maps-of-making.html      ← Add "Health network" tweak row
```

### SPARQL prefix reminder

All SPARQL queries must include PREFIX declarations. Current set in `materialize_geojson.py`:
```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
```

`mom:source` uses the `mom:` prefix — already declared. No new prefixes needed.

### No new dependencies

All changes are in vanilla JS and Python stdlib + httpx. No new packages.

### Local dev environment

[Source: memory/infra_local_dev.md]
- Start stack: `distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up`
- Materialize: `source venv/bin/activate && python scripts/materialize_geojson.py`
- Map: `http://localhost:8080/`

### venv

Never create or activate venv from scripts. User manages venv externally. Always `source venv/bin/activate` before Python commands.

### Handoff to Epic 2

This story does NOT implement the Epic 4 admin "Show mock data" SPARQL-level toggle (Story 4.4). That toggle switches which named graphs are queried at the backend. This story is a frontend-only layer visibility switch using the `source` property already in the materialized GeoJSON.

Epic 2 stories (2-1 through 2-5) require no changes from this story — they add new spaces via URL ingestion, not via the mock dataset.

### References

- [Source: _bmad-output/implementation-artifacts/1-5-map-reads-from-oxigraph-geojson-materialization.md — GeoJSON format, SPARQL pattern, binding_to_space()]
- [Source: web/data/rff_mockup.json — `mom:source: "mock-rff"` field confirmed]
- [Source: web/data/moms_seed.json — `mom:source: "scraped-vow"` field confirmed]
- [Source: _bmad-output/planning-artifacts/epics.md — UX-DR19 (admin health toggle), Epic 0 sequencing note (RFF graph isolation)]
- [Source: _bmad-output/planning-artifacts/epics.md — FR9 (session-persistent filter state, Epic 5)]
- [Source: web/maps-of-making.html:503-532 — Tweaks panel structure]
- [Source: web/app.js:88-98 — tweaks wireUI handler pattern]

---

## Dev Agent Record

### Agent Model Used

_to be filled by dev agent_

### Completion Notes List

### File List
