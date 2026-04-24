# Story 1.2: Scope Basemap to Europe + Update Loader Copy

**Status:** done
**Epic:** 1 — Federated Backend Foundation
**Story Key:** 1-2-scope-basemap-to-europe-update-loader-copy
**Created:** 2026-04-24

---

## User Story

As a maker browsing the map,
I want the map to restrict panning to the Europe region and show accurate loader copy,
So that the initial tile batch is minimal (no tiles loading for unreachable world regions) and the loader text reflects the actual data being loaded rather than hardcoded synthetic copy.

---

## Acceptance Criteria

**Given** the map SPA is loading
**When** MapLibre initialises
**Then** `maxBounds` is set to approximately `[[-25, 34], [45, 72]]` (Atlantic west coast to Ural, North Africa to Scandinavia), preventing tile requests outside Europe
**And** the loader copy no longer reads "loading 40 synthetic spaces · FR + DE" — it reads a neutral variant that does not hardcode a space count or data description
**And** the map still centres on `[4.8, 49.5]` zoom 4.3 (FR/DE/BE pilot midpoint)
**And** the `<div class="loader">` second line is either removed or replaced with a version driven by actual data count once available
**And** the reduced-motion media query and 1500ms fallback dismissal remain untouched

---

## Tasks / Subtasks

- [x] **Task 1: Add `maxBounds` to MapLibre init** — `web/app.js:102`
  - [x] Add `maxBounds: [[-25, 34], [45, 72]]` to the `new maplibregl.Map({…})` call
  - [x] Verify `center` and `zoom` are still `[4.8, 49.5]` / `4.3`

- [x] **Task 2: Remove hardcoded loader copy** — `web/maps-of-making.html:314`
  - [x] Delete `<div class="mono" style="color: var(--muted);">loading 40 synthetic spaces · FR + DE</div>`
  - [x] Leave first line `<div class="hand">unrolling the map…</div>` intact

- [x] **Task 3: Sanity-check results-count and drawer-count initial values** — `web/maps-of-making.html:329,360`
  - [x] The static `40` in `id="results-count"` and `id="drawer-count"` are overwritten by JS on load — no change needed (confirm by grep)

- [x] **Task 4: Visual verification**
  - [x] Open `web/maps-of-making.html` in browser (or local server), confirm map loads centred on FR/DE/BE
  - [x] Try panning past the Atlantic / Urals — should be blocked
  - [x] Confirm loader shows only "unrolling the map…" before dismissing

---

## Technical Requirements

### Files to Modify

| File | Line(s) | Change |
|------|---------|--------|
| `web/app.js` | 102–109 | Add `maxBounds` to `new maplibregl.Map({…})` |
| `web/maps-of-making.html` | 314 | Remove the second `<div class="mono">` inside `.loader` |

### Do NOT touch

- `web/app.js:125` — 1500ms fallback dismissal (`setTimeout(() => { … dismissLoader(); }, 1500)`)
- Any CSS under `.loader` in `maps-of-making.html`
- The reduced-motion media query (wherever it lives in the HTML `<style>` block)
- `web/test_embed.html`, nginx config, seed data files

---

## Architecture Compliance

- All Phase 1 SPA logic lives in `web/app.js` — this change is purely in-file, no new modules
- MapLibre GL JS `maxBounds` is the canonical way to restrict panning — no custom event listeners needed
- This story makes no networking, SPARQL, or harness changes

---

## Context from Story 1.1 / Epic 0 Handoffs

- **Isolation note:** Oxigraph (`distrobox-host-exec podman compose -f infra/docker-compose.yml up -d oxigraph`) is not involved in this story — this is a pure frontend change
- **Venv note:** No Python changes — do not activate venv for this story
- **Tile source:** Phase 1 uses OpenFreeMap tiles (configured in `app.js:buildStyle`). No tile source changes in this story

---

## Definition of Done

- [x] `web/app.js` `maplibregl.Map` constructor includes `maxBounds: [[-25, 34], [45, 72]]`
- [x] `web/maps-of-making.html` loader `<div class="mono">` line with synthetic copy is removed
- [x] Map still centres on `[4.8, 49.5]` at zoom 4.3
- [x] Panning is blocked outside Europe bounds
- [x] Loader shows only "unrolling the map…", no hardcoded counts or geography
- [x] 1500ms fallback dismissal and reduced-motion query untouched
- [x] No regressions in filters, search, drawers, or embed snippet

---

## File List

- `web/app.js` (MODIFY — add `maxBounds`)
- `web/maps-of-making.html` (MODIFY — remove loader second line)

---

## Dev Agent Record

### Completion Notes

- Added `maxBounds: [[-25, 34], [45, 72]]` to `maplibregl.Map` constructor at `web/app.js:107`; `center` and `zoom` remain `[4.8, 49.5]` / `4.3`
- Removed second `.loader` div (synthetic copy line) from `web/maps-of-making.html:314`; first line `unrolling the map…` preserved
- Confirmed `results-count` and `drawer-count` static `40` values are overwritten at runtime by `app.js:256-257` — no HTML change needed
- 1500ms fallback dismissal (`app.js:126`) and `prefers-reduced-motion` media query (`maps-of-making.html:289`) untouched

---

## Change Log

- 2026-04-24: Story created
- 2026-04-24: Implemented — maxBounds added to MapLibre init; hardcoded loader copy removed
