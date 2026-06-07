# Story 5.0: GL Rendering Substrate + World View Unlock

Status: review

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

- [x] **Task 1 — Stand up the GL GeoJSON source** (AC: 1)
  - [x] `buildFeatureCollection()` builds the FC from `filteredSpaces()`, reusing the invalid-coord guard from the retired `renderMarkers()`. Source added in `ensureSpacesLayers()` via `map.addSource('spaces', { type:'geojson', data, promoteId:'id' })` — **no clustering**.
  - [x] Each feature carries `properties.id` + `properties.kind = computeMarker(s)` (plus name/city/country for the popup); `promoteId:'id'` exposes `id` to feature-state.
  - [x] Deleted `renderMarkers()`, `createMarkerSVG()`, `SVG_NS`, and `state.markers`.
  - [x] All `renderMarkers()` call sites now call `refreshSpacesLayer()` (ready, styledata re-render, filter/search/reset/tweaks handlers, register/refresh/poll).
- [x] **Task 2 — Individual-dot circle layer + colour ladder** (AC: 3)
  - [x] `spaces-point` circle layer; `circle-color` = `match` on the `kind` property → ladder colour (`colorMatchExpr`). No cluster filter needed (no clustering).
  - [x] Ladder colours lifted from `state-colour-ladder.html` into the `LADDER` table (Daylight + Depth surfaces). `shut` → dimmed green (`#2D7A5A` day / `#1D9E75` depth), **never black** — retires the black-dot bug (CSS rule removed; legend swatch fixed too).
  - [x] `circle-radius` zoom-interpolated; `state.tweaks.density` applied as a multiplier (`compact` → 0.7×).
  - [x] Open-pulse reproduced via a single `requestAnimationFrame` loop driving `circle-opacity`/`circle-radius` on the open-subset `spaces-pulse` halo layer; respects `tweaks.pulse === 'off'` AND `prefers-reduced-motion`.
  - [x] `spaces-glyph` symbol layer carries non-colour markers (NFR-A4): `broken` `×`, `aging` `!`, `zombie` `…`, `dead` `+`, in `Noto Sans Regular`. Seeded/dead/zombie also read via distinct stroke colours.
- [x] **Task 3 — Zoom-scaled point field (one continuous ramp)** (AC: 2)
  - [x] The single `spaces-point` layer serves all scales — no cluster layer, no dot/cluster swap. Only `circle-radius` changes with zoom.
  - [x] `circle-radius` = one `interpolate(linear, zoom)` ramp: 2.2px @ z2 (field of light) → 9px @ z12 → 12px @ z16. Stops are a first pass — **tune against the screenshots during live review.**
  - [x] No MapTiler SDK (ADR-017). The dense-field "glow" is approximated with `circle-opacity: 0.9` so overlaps build weight; a true blur/density falloff is not native to GL `circle` — noted for Nicolas if more glow is wanted.
  - [x] No `clusterProperties`, no count labels, no expansion click handler.
- [x] **Task 4 — Label dissolve at altitude** (AC: 2)
  - [x] `labels-places` `text-opacity` → `interpolate(linear, zoom, 5→0, 7→1)`. Coastline/water/landcover untouched. Lives in `buildStyle()` so it applies to all three flavors.
- [x] **Task 5 — World view unlock** (AC: 4)
  - [x] `maxBounds` removed; default `center:[10,20] zoom:2`.
- [x] **Task 6 — Viewport-first deep-link init** (AC: 5)
  - [x] `initMap()` reads `?lat/?lon` BEFORE constructing the map → used as `center` + zoom 13, sets `state._initialViewport`. No `flyTo` on cold load.
  - [x] `applyUrlParams()` selects the space with `{ fly: !viewportFirst }` — no fly when coords were consumed, legacy fly otherwise (AC6).
  - [x] Share-URL builder appends `&lat=&lon=` from the space's coords.
  - [x] Preset/embed builder appends the same coord params alongside `space=`.
- [x] **Task 7 — Regression sweep** (AC: 1, 5, 6) — *code paths preserved; live matrix is the review gate*
  - [x] `bbox`/`center` deep links untouched (still inside `applyUrlParams()` `map.once('load')`).
  - [x] `showEmbedPopup` reattached to the `spaces-point` GL `click` handler (`wireSpacesClick`).
  - [x] Filters/search/reset repaint via `setData` (no DOM rebuild); `updateCounts()`/results-list still driven by `filteredSpaces()`.
  - [x] Post-registration auto-zoom path uses `selectSpace(id, {fly:true})` unchanged (non-deep-link).

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

claude-opus-4-8 (Amelia / dev-story)

### Debug Log References

- `node --check web/app.js` → OK (syntax clean after refactor)
- Symbol-uniqueness scan: `refreshSpacesLayer`, `ensureSpacesLayers`, `buildFeatureCollection`, `startPulse`, `LADDER` each defined exactly once.
- Stale-reference scan: no remaining `state.markers` / `createMarkerSVG` / `renderMarkers(` call usages (only retired-reference comments).

### Completion Notes List

**What landed (pure browser-consumption-layer change — nothing outside `web/`):**
- Replaced the per-space DOM `maplibregl.Marker` system with a single GL GeoJSON source (`spaces`, `promoteId:'id'`) feeding three layers: `spaces-pulse` (open-subset halo), `spaces-point` (the field of light), `spaces-glyph` (non-colour markers).
- `computeMarker()` / `computeAxisA/B/C` / `filteredSpaces()` preserved verbatim — they now feed paint expressions + `setData` instead of DOM construction.
- Two-surface ladder (`LADDER`/`LADDER_STROKE`) selected by the **theme toggle** (`tweaks.mapStyle`), not zoom. `shut` is dimmed green on both surfaces — the black-dot bug is retired in both the map paint and the legend swatch, and the dead `.map-marker.*` CSS was removed.
- Selection ported to GL `feature-state` (`{selected:true}` → red stroke). Map-background click guarded with `queryRenderedFeatures(['spaces-point'])` so clicking a dot no longer closes the detail drawer.
- World view unlocked (no `maxBounds`, `[10,20]`/z2 default) + viewport-first `?lat/?lon` init with no `flyTo` on cold load; share + preset/embed URLs now carry coords.
- `__driftProbe` repurposed: GL eliminates the DOM-marker-vs-projection drift class entirely, so it now just dumps rendered `spaces-point` features.

**⚠️ Manual verification — PENDING (gate owned by Nicolas, live on VPS).** Per this repo's pytest-vs-live DoD and prior map stories, `web/` front-end JS has no unit harness; verification is the manual matrix in Dev Notes → Testing standards: (a) world-view field of light on cold load; (b) one continuous radius ramp continental→street; (c) labels dissolve at altitude across light/dark/grayscale; (d) `?space=&lat=&lon=` opens local-first, drawer open, no flyTo; (e) legacy `?space=` still resolves (graceful fly); (f) filters/search repaint with **no marker DOM nodes** in DevTools; (g) embed popup fires; (h) `shut` dots dimmed-green not black.

**Tuning flagged for live review:** radius ramp stops (z2→z16) and `circle-opacity` glow are a first pass — tune against `screencap_0606_151757.png` / `screencap_0606_110737.png`. If a stronger additive-glow is wanted beyond what `circle-opacity` gives, that needs a heatmap layer or a custom shader (noted, not pulled into scope).

### File List

- `web/app.js` (modified) — GL substrate: source/layers, ladder paint expressions, rAF pulse, feature-state selection, viewport-first init, label dissolve, coord-bearing share/embed URLs; removed DOM-marker machinery.
- `web/maps-of-making.html` (modified) — removed retired `.map-marker.*` / `.marker-*` / `@keyframes pulse` CSS (incl. the black-dot `shut` bug); fixed `.pin-swatch.shut` legend to dimmed green.

### Change Log

- 2026-06-06 — Story 5.0 implemented: full-GL point-field substrate replaces DOM markers; world view unlocked; viewport-first deep links; label dissolve at altitude; black-dot `shut` bug retired. Status → review (live manual-verification matrix pending, owner Nicolas).
- 2026-06-07 — Visual tuning pass (live review with Nicolas): depth palette on both surfaces (no per-surface split); `saturate(0.45)` canvas filter dropped; seeded z-ordered below registered dots; stroke dissolves z9→z6; beacon rAF revived with `circle-*-transition:{duration:0}` fix; basemap auto-transitions dark→light z6→z9 via GL zoom expressions (theme toggle retired); initial viewport from 5/95 percentile bbox passed to map constructor (no post-load jump); `minZoom:1.5`; label layers split city/town; zoom indicator in legend; compact density as default.
