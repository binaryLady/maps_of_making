# Story 5.0: GL Rendering Substrate + World View Unlock

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a map viewer anywhere in the world,
I want the map to render spaces using a GL-native layer that clusters at continental zoom and opens to the full world,
so that the map feels alive at every scale — from a maker's street corner to a continental field of light — and embeds load at the right place from the first frame.

## Acceptance Criteria

### AC1 — Single GL GeoJSON source replaces DOM markers
**Given** `spaces.geojson` is fetched on map load
**When** the map initialises
**Then** all spaces are loaded into a single MapLibre GL GeoJSON source (`map.addSource('spaces', { type: 'geojson', data })`) — **NOT clustered**: every space is its own point at every zoom (the continental view is a *field of individually-coloured dots*, not aggregated blobs)
**And** the existing `renderMarkers()` DOM-marker loop is removed — no individual `maplibregl.Marker` elements are created for spaces
**And** `createMarkerSVG()` is removed (DOM SVG construction per space)
**And** `computeMarker()` logic is preserved and reused to map space state → GL paint property values (`circle-color`, `circle-radius`)
**And** `filteredSpaces()` drives a GL filter / source-data update instead of a DOM tear-down + re-mount
**And** `selectSpace()` / `highlightSelected()` use the GL feature-state API instead of DOM `classList`

### AC2 — Continental / world scale: zoom-scaled point field + label dissolve
**Visual reference:** the MapTiler `helpers/point` example (`docs.maptiler.com/leaflet/examples/helpers-point/`) — see `/home/nicolas/Images/Screenshots/screencap_0606_151757.png` and `screencap_0606_110737.png`. That helper renders *every* point individually on a dark field, sizing and colouring each dot by a data value — **no aggregation**. We reproduce that field in vanilla MapLibre GL (the helper is a thin wrapper over `circle` paint expressions — no MapTiler SDK needed).
**Given** the map is at continental / world scale (zoom ≤ ~7)
**When** the point field renders
**Then** each space is a small GL circle, `circle-color` driven by its `computeMarker()` state via the `state-colour-ladder`. The ladder has two surfaces — Daylight (parchment) and Depth (dark) — **selected by the existing tweaks-panel theme toggle (light/dark/grayscale), NOT by zoom level.** The dark field in the visual references is one theme, not a requirement; the point field must read correctly on whichever basemap flavour is active.
**And** `circle-radius` is a zoom-interpolated expression: small dots at world zoom (the "field of light"), growing as the viewer zooms in — a single continuous radius ramp, not a cluster/dot swap
**And** the `labels-places` symbol layer (`web/app.js` `buildStyle()`) fades to `text-opacity` 0 below ~z6–7 — coastlines and landmass remain, named place labels dissolve (Overview Effect: geography + points only at altitude)
**And** no network or country colouring is applied — spaces are kin by aliveness, not by directory

### AC3 — Street scale: full colour ladder + pulse
**Given** the map is at city / street scale (zoom ≥ ~8)
**When** the same point field renders at larger radius
**Then** each space renders as a GL circle with colour and radius driven by its `computeMarker()` state (same ladder, same theme-selected surface as AC2 — only the radius has grown)
**And** the open-pulse animation is reproduced via a `requestAnimationFrame`-driven `circle-opacity` / `circle-radius` paint update (no CSS `@keyframes`, no DOM)
**And** the full colour ladder is honoured: `open` (bright algae + pulse), `shut` (**dimmed green — NOT black**), `confirmed` (blue), `aging` (amber), `zombie` (faint ghost), `dead` (grey tombstone, admin only), `broken` (red ×), `seeded` (neutral)

### AC4 — World view unlocked (drop EU box)
**Given** the EU `maxBounds` constraint currently set in `initMap()` (`web/app.js:182`)
**When** Story 5.0 lands
**Then** `maxBounds` is removed — the map is navigable worldwide
**And** the default `center`/`zoom` is updated from the FR/DE midpoint (`[4.8, 49.5]` zoom 4.3) to a world-overview start (center `[10, 20]`, zoom 2) so the full continental field is visible on first load
**And** at world zoom the ladder-coloured point field keeps the map alive and legible rather than sparse — the field of light is the first impression, never empty continents

### AC5 — Viewport-first init for deep links
**Given** a visitor loads `/?space=openfab&lat=51.50&lon=-0.12`
**When** `initMap()` runs
**Then** the map initialises AT `[lon, lat]` zoom 13 — first tile fetch is the local area, not the world overview
**And** when data is ready, the space is selected and its drawer opens **without any `flyTo`** on cold load
**And** the share button (`web/app.js:606`) generates URLs with coordinates appended: `/?space={id}&lat={lat}&lon={lon}`
**And** embed snippets generated via the preset/embed path (`renderPresetPreview()` / `embedSpace()`) include the same coordinate params

### AC6 — Legacy embed graceful fallback
**Given** old embed snippets arrive without coordinates (`/?space=openfab&embed=1` or `?space=...&bbox=...`)
**When** the page loads
**Then** the map falls back gracefully to the existing post-load behaviour at the space's location once data loads (no crash, no blank map)
*(Server-side 301 redirect for legacy embeds is a follow-up task — explicitly NOT in this story's scope.)*

## Tasks / Subtasks

- [ ] **Task 1 — Stand up the GL GeoJSON source** (AC: 1)
  - [ ] In `initMap()` (or a new `addSpacesSource()` called from `ready()`), build a FeatureCollection from `state.spaces` (skip invalid coords — reuse the validation guard currently in `renderMarkers()` at `web/app.js:270`) and `map.addSource('spaces', { type:'geojson', data })` — **no clustering** (every space is its own point at every zoom)
  - [ ] Stamp each feature's `properties` with its computed `kind = computeMarker(s)` and the `id` so paint expressions and feature-state can key off it
  - [ ] Delete `renderMarkers()` and `createMarkerSVG()`; remove `state.markers` Map and its `.forEach(m => m.remove())` teardown
  - [ ] Replace the three `renderMarkers()` call sites: `ready()` (`web/app.js:201`), the `styledata` re-render (`web/app.js:1433`), and any filter/tweak handlers — with a single `refreshSpacesLayer()` that calls `getSource('spaces').setData(...)`
- [ ] **Task 2 — Individual-dot circle layer + colour ladder** (AC: 3)
  - [ ] Add `unclustered-point` circle layer with `filter: ['!', ['has','point_count']]`; `circle-color` = `match`/`get` expression on the `kind` property mapping each state to its ladder colour
  - [ ] Source the ladder colours from `state-colour-ladder.html` (authoritative). Critically: `shut` → dimmed/desaturated green, **never `--ink`/black** — this retires the `web/maps-of-making.html:178` `.map-marker.shut .marker-fill { fill: var(--ink) }` bug
  - [ ] `circle-radius` interpolated by zoom; honour `state.tweaks.density` (compact vs comfortable) as a radius multiplier
  - [ ] Reproduce the open-pulse: a `requestAnimationFrame` loop updating a paint property (e.g. `circle-radius`/`circle-opacity`) on the open-subset layer or via feature-state; respect `state.tweaks.pulse === 'off'`
  - [ ] Add the `broken` × treatment: **a GL symbol layer is required** (not optional) for `broken` — a `×` text glyph centred on the circle satisfies NFR-A4 (colour must not be the sole differentiator). Similarly, `dead` / `zombie` / `aging` must carry a visual marker beyond colour (a small text glyph or distinct circle stroke pattern). GL has no DOM emoji — use short text strings (`×`, `!`, `…`) in a symbol layer filtered by `kind`. Confirm glyphs render in the OpenFreeMap font stack (`Noto Sans Regular`) before finalising.
- [ ] **Task 3 — Zoom-scaled point field (continental → street is one continuous ramp)** (AC: 2)
  - [ ] The SAME `unclustered-point` circle layer from Task 2 serves both scales — there is no separate cluster layer and no dot/cluster swap. The only thing that changes with zoom is `circle-radius`.
  - [ ] `circle-radius`: a single `interpolate(['linear'], ['zoom'], …)` ramp — small (e.g. 2–3px) at world zoom (z2) so dense regions read as a *field of light*, growing to the street-scale radius (e.g. 8–10px) by z12. Tune the stops against the visual references (`screencap_0606_151757.png`, `screencap_0606_110737.png`).
  - [ ] **Retro-engineer the MapTiler `helpers/point` behaviour** before tuning: it scales size *and* colour by a data value over a dense field. Confirm whether it applies any opacity/blur falloff or radius-by-density that we want to reproduce. We are NOT using the MapTiler SDK — replicate the *look* with vanilla GL `circle-radius` / `circle-opacity` / `circle-color` expressions. If a pure-GL expression can't reproduce a desired effect, note it for Nicolas rather than pulling in the SDK.
  - [ ] At very high density, consider `circle-opacity` < 1 so overlapping dots build visual weight (the screenshots show this additive-glow effect). Optional; confirm against the references.
  - [ ] No `clusterProperties`, no count labels, no cluster-expansion click handler — none of the clustering machinery is used.
- [ ] **Task 4 — Label dissolve at altitude** (AC: 2)
  - [ ] In `buildStyle()` (`web/app.js:165`), change the `labels-places` layer `text-opacity` to a zoom `interpolate` expression: 0 below the continental threshold (~z6), ramping to full by ~z8. Coastline/water/landcover layers untouched.
  - [ ] Verify across all three style flavors (`light`/`dark`/`grayscale`)
- [ ] **Task 5 — World view unlock** (AC: 4)
  - [ ] Remove `maxBounds` from the `new maplibregl.Map()` options (`web/app.js:182`)
  - [ ] Change default `center: [4.8, 49.5], zoom: 4.3` → `center: [10, 20], zoom: 2`
  - [ ] Confirm clusters render at world zoom so first impression is a field of light, not empty continents
- [ ] **Task 6 — Viewport-first deep-link init** (AC: 5)
  - [ ] In `initMap()`, read `lat`/`lon` from the URL BEFORE constructing the map; if present, use them as `center` + zoom 13 (overrides the world default) so the first tile fetch is local — no `flyTo`
  - [ ] In `applyUrlParams()` (`web/app.js:957`), when `lat`/`lon` were consumed by `initMap()`, select the space on data-ready WITHOUT `flyTo` (pass `{ fly: false }`); keep the legacy `flyTo` path only when coords are absent (AC6)
  - [ ] Share-URL builder (`web/app.js:606`): append `&lat=...&lon=...` from the space's coordinates
  - [ ] Embed/preset builder (`renderPresetPreview()` `web/app.js:1014`, `embedSpace()`): append the same coord params alongside `space=`
- [ ] **Task 7 — Regression sweep** (AC: 1, 5, 6)
  - [ ] Verify `bbox` and `center` deep links still work (they share the `map.once('load')` timing in `applyUrlParams()`)
  - [ ] Verify embed-mode popup path (`showEmbedPopup`) still fires — it currently keys off marker click; reattach to the GL layer `click` handler
  - [ ] Verify filters/search re-render via `setData`, not DOM rebuild; verify `updateCounts()`/results-list still reflect `filteredSpaces()`
  - [ ] Verify post-registration auto-zoom (`selectSpace(..., {fly:true})`) still works for the non-deep-link path

## Dev Notes

### Why this story exists (context the dev MUST hold)
This is the **prerequisite foundation for all of Epic 5** (5.1–5.5 assume GL has landed). It is a **pure browser-consumption-layer change**: the data contract — `spaces.geojson` + the `thresholds` header shipped from `config.yaml` — is **unchanged**. The ingestion pipeline, Oxigraph, the three-token freshness model: all untouched. If you find yourself editing anything outside `web/`, stop — you've left scope.

The "meaning" of the continental view is not decoration. Read `_bmad-output/planning-artifacts/overview-effect-north-stars.md` before coding the cluster/label behaviour: borders AND place-names dissolve at altitude (astronaut Overview Effect), freshness = fragility (the thin blue line), restraint/quiet, never colour by network/country at altitude. Visual deviations from `state-colour-ladder.html` are **bugs, not preferences**.

### Files being modified — current state (read these, do not guess)

**`web/app.js`** (1561 lines) — the map SPA. Key anchors:
- `initMap()` `:176` — constructs `new maplibregl.Map()` with `center:[4.8,49.5]`, `zoom:4.3`, `maxBounds:[[-25,34],[45,72]]` (`:182`). Already has an **idempotent `ready()`** (`:199`) called from `styledata` + `load` + a 1500ms fallback — the loader-jank race from the quick-dev doc is already fixed. `ready()` currently calls `renderMarkers()`; rewire to `refreshSpacesLayer()`.
- `buildStyle(flavor)` `:136` — returns the MapLibre style. The place-label layer is **`labels-places`** at `:165` (`source-layer:'place'`), `text-color:c.label`. This is the layer to fade in Task 4. Three flavors: `light`/`dark`/`grayscale`.
- `createMarkerSVG()` `:220` + `renderMarkers()` `:262` — the DOM machinery to **delete**. Note the coord-validity guard at `:270` (lat/lon numeric + in-range) — preserve this logic when building the FeatureCollection. Note emoji/glyph map at `:240` (`broken:'×', aging:'⚠️', zombie:'🧟', dead:'🪦'`) — GL has no DOM emoji; decide colour-only vs symbol-glyph per the ladder.
- `computeMarker(s)` `:395` — **PRESERVE.** Precedence: B(dead/zombie/aging) → A(broken) → C(open/shut) → confirmed → seeded. Calls `computeAxisA/B/C` (`:351`/`:367`/`:386`) against `state.thresholds`. This is the single source of a space's `kind`. Note `computeAxisC` comment at `:384` still says "black dot" for shut — that comment and the CSS it describes are exactly what this story retires.
- `highlightSelected()` `:408` + `selectSpace(id, opts)` `:416` — currently DOM `classList` on `m.getElement()`; port to GL feature-state. `selectSpace` does `map.flyTo(... zoom: max(getZoom(),8))` when `opts.fly`.
- `filteredSpaces()` `:429` — pure filter over `state.spaces` by networks/countries/statuses(via `computeMarker`)/specialties/search. Keep as-is; it now feeds `setData` instead of the DOM loop.
- `showEmbedPopup()` `:299` — embed-mode lightweight popup; currently triggered from marker click in `renderMarkers()` (`:281`). Reattach to GL layer click.
- `applyUrlParams()` `:957` — reads `networks/country/status/specialty/q/bbox/center/space`; viewport + space applied inside `map.once('load')` at `:969`. **Note: `space` IS now read here (`:967`)** — the quick-dev deep-link fix already landed. This story upgrades it to viewport-first (read `lat`/`lon` in `initMap()` so there's no `flyTo` on cold load).
- Share URL `:606` (`/?space=` + id); preset/embed share URL assembled at `:1013`, single-space embed adds `space=` at `:1016`.
- Loader/`styledata` re-render at `:1433` (`map.once('styledata', () => renderMarkers())`).

**`web/maps-of-making.html`** (794 lines) — the host page + CSS. The black-dot bug is `.map-marker.shut .marker-fill { fill: var(--ink); stroke: var(--paper); }` at `:178` (`--ink` = `#1a1a1a`). Once `renderMarkers()` is gone these `.map-marker.*` rules are dead CSS — remove them, but first lift the **intended** colours into the GL paint expression. CSS vars to reuse for the ladder: `--paper #f7f2e7`, `--ink #1a1a1a`, `--green oklch(60% 0.14 150)`, `--accent oklch(62% 0.18 25)`, `--yellow`, `--muted`, `--faint`, `--rule`.

### GL design decisions already locked (ADR-017)
- **Full-GL, one system** — GeoJSON source + GL layers; no DOM/GL hybrid.
- **Vanilla MapLibre GL — NO MapTiler SDK.** No API key, no vendor coupling (the MapTiler `helpers/point` link was a *Leaflet* example, n/a). Use `addSource`/`addLayer` directly. Consistent with OpenFreeMap-dev / PMTiles-prod tile strategy.
- **Status-weighted clusters are the headline lens**, not plain count. This is the differentiator — a health map of the movement. Plain count is an available baseline toggle, not the default.
- **GL does not speed first load** (tile-bound, still OpenFreeMap) — it makes re-render/filter/zoom GPU-cheap and atomic. Don't expect a cold-load speedup; expect interaction smoothness.

### Performance / scale note
111 spaces today. `clusterProperties` aggregation + `step`/`interpolate` paint expressions are the right tool — they keep cluster colour computation off the per-frame path. The rAF pulse should touch only the open subset and should be a single paint update per frame, not per-feature.

### Testing standards
- No unit-test harness for `web/` front-end JS in this repo — verification is **manual against real data on the VPS** (consistent with prior map stories; the project's DoD gate distinguishes pytest-vs-live). 
- Manual matrix: (a) cold load shows world view with status-weighted clusters; (b) zoom in → clusters split → individual dots with correct ladder colours, `shut` is dimmed-green not black; (c) place labels faded at altitude, present at street; (d) `/?space=openfab&lat=..&lon=..` opens local-first, no flyTo, drawer open; (e) legacy `/?space=openfab` still resolves gracefully; (f) filters/search repaint without DOM churn (watch DevTools — no marker DOM nodes); (g) embed popup still fires; (h) all three style flavors fade labels correctly.

### Project Structure Notes
- All changes confined to `web/app.js` and `web/maps-of-making.html`. No pipeline, no `scripts/`, no `infra/` (except the optional, out-of-scope legacy-embed 301 which is a follow-up).
- No new dependencies — MapLibre GL is already loaded; clustering is native to it.
- `pmtiles` protocol is wired (`web/app.js:1438` per prior notes) but PMTiles is parked; stay on OpenFreeMap (`TILES_URL`).

### References
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-017] — Full-GL substrate decision, source config, zoom-tier table, viewport-first init, retired/preserved lists
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-004] — Pin visual grammar, 8-state colour table, "darkness reserved for absence", continental view
- [Source: _bmad-output/planning-artifacts/state-colour-ladder.html] — Authoritative colour model (Daylight/Depth surfaces = street/continental tiers). Visual deviation = bug.
- [Source: _bmad-output/planning-artifacts/overview-effect-north-stars.md] — Continental UX intent: borders + names dissolve, freshness = fragility, restraint
- [Source: _bmad-output/planning-artifacts/spike-brief-map-viz-lenses.md] — Lens modes (count / status-weighted / heatmap) + 3 zoom states for mockups
- [Source: _bmad-output/planning-artifacts/epics.md#Story 5.0] — Originating epic ACs
- [Source: _bmad-output/implementation-artifacts/quick-dev-first-load-fixes.md] — Quick-dev fixes already landed (cache, `?space=` read, loader race); this story carries the tagged viewport-first follow-up
- [Source: architecture.md#Epic 3.5 — Three-Token Freshness Model] — `observed_at`/`updated_at`/`state.lastchange` computed in browser; what the status-weighted cluster surfaces at altitude

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
