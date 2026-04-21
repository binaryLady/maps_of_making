# Next Session — Maps of Making

**Snapshot date:** 2026-04-21 (drift investigation complete)
**PRD:** `_bmad-output/planning-artifacts/prd.md` — COMPLETE (all 12 steps)

---

## Phase 1 — Start immediately, no architecture needed

Three tasks on the existing prototype (`maps_of_making-handoff.zip`):

1. **Protomaps spike** — swap OSM/Carto raster tiles → PMTiles in `Maps-of-Making.html` + `app.js`. 3-line MapLibre protocol registration + extract FR+DE regional PMTiles file. Fixes 403 referer block.
2. **Pin drift fix** — comes for free with vector tile switch (raster tile anchoring issue disappears).
3. **UI polish** — clean up drawers, legend, filter panel against the PRD spec. Prototype is already close.

**How to start:** brief Amelia (dev agent) directly with the PRD + prototype as spec. No epics needed for Phase 1.

---

## Phase 2 — Architecture first, then epics

Sequence before writing Phase 2 code:

1. **`/bmad-agent-architect`** — Winston session: Docker Compose services, ingestion pipeline design, Oxigraph schema, SPARQL validation gateway, bot adapter interface, CID-based snapshot storage
2. **`/bmad-create-epics-and-stories`** — break PRD into epics + stories from the architecture
3. **`/bmad-sprint-planning`** — generates `sprint-status.yaml` once epics exist

---

## Key decisions to remember

- Map is pure reader — no editing records, append-only versioned snapshots
- JSON endpoints describe spaces, not people (no personal contacts in public data)
- All thresholds (fetch cadence, failure counts, retention) in config — set from real PoC telemetry
- Admin: shared password, Nicolas + Jason only (PoC-grade); harden at pilot
- IPFS/IPLD archival of anonymized snapshots: Phase 3 exploration

---

## Pin drift investigation log

**Status:** open. Protomaps/OpenFreeMap swap done — drift still present on zoom. Previous fixes (shadow, anchor) had zero measurable effect → we have been fixing the wrong thing. This time: **measure first, hypothesize second, fix third.**

### Observed signature (user-reported, not yet measured)

- Drift happens **only on zoom**, not on pan.
- Drift is **vertical only**.
- Paris (lat 48.84) appears fixed — but map center is `[4.8, 49.5]`, so Paris is ~0.66° from center lat. Low drift ≠ zero drift. This needs measurement, not eyeballing.
- Lille (50.6, |Δ|=1.1°) drifts. Hamburg (53.5, |Δ|=4.0°) drifts **more** than Lille. Toulouse/Marseille/Lyon (43–45, |Δ|=4–6°) reportedly drift **less** than Lille — asymmetric, **not** a symmetric function of |Δlat|.
- Same behavior occurred with OSM raster tiles → not a tile issue.

### Reproducible measurement — `__driftProbe()`

Paste in DevTools console once the page has loaded:

```js
window.__driftProbe = () => {
  const rect = map.getContainer().getBoundingClientRect();
  const rows = [];
  state.markers.forEach((m, id) => {
    const ll = m.getLngLat();
    const projected = map.project(ll);
    const el = m.getElement();
    const r = el.getBoundingClientRect();
    const domX = r.left + r.width / 2 - rect.left;
    const domY = r.top + r.height / 2 - rect.top;
    rows.push({ id, lat: ll.lat, lon: ll.lng,
                dx: +(domX - projected.x).toFixed(2),
                dy: +(domY - projected.y).toFixed(2) });
  });
  console.table(rows.sort((a, b) => a.lat - b.lat));
  return rows;
};
```

Call `__driftProbe()` at each zoom, record `dy` for the three reference cities.

### Measurement table (fill in as tests run)

| Hypothesis | Zoom 4.3 Toulouse dy | Zoom 4.3 Paris dy | Zoom 4.3 Lille dy | Zoom 4.3 Hamburg dy | Zoom 6 dy (P/L/H) | Zoom 8 dy (P/L/H) | Zoom 10 dy (P/L/H) | Verdict |
|---|---|---|---|---|---|---|---|---|
| Baseline (no change)      |  |  |  |  |  |  |  | — |
| A1: remove `.map-paper`   |  |  |  |  |  |  |  |   |
| A2: hide `.paper-overlay` |  |  |  |  |  |  |  |   |
| A3: force `map.resize()` before markers |  |  |  |  |  |  |  |   |
| A4: `state.tweaks.pulse='off'` before render |  |  |  |  |  |  |  |   |
| A5: MapLibre 5.x          |  |  |  |  |  |  |  |   |
| B1: inspect `map.getProjection()` |  |  |  |  |  |  |  |   |
| C1: spot-check seed coords for Hamburg/Lille/Toulouse |  |  |  |  |  |  |  |   |

### Hypothesis branches

Decision rule from Step 0 measurement:

- **`dy` ≈ 0 at all zooms** → drift is not in DOM marker positioning. Go to Group B (canvas projection or paper-overlay illusion).
- **`dy` non-zero and grows with zoom** → DOM position disagrees with `map.project()`. Go to Group A.
- **`dy` non-zero at init, stable across zoom** → stale container size. Go straight to A3.

**Group A — DOM ≠ project():**
- A1. CSS `filter` on `.maplibregl-canvas` (map-paper class) may affect compositing. Remove class, remeasure.
- A2. `mix-blend-mode: multiply` on sibling `.paper-overlay`. Hide it, remeasure.
- A3. Stale `#map` container size captured by MapLibre at init (fonts/scrollbar/overflow applied late). Add `map.resize()` on `requestAnimationFrame` before `renderMarkers()`. **Matches "vertical only, zoom only" perfectly** — top candidate.
- A4. Pulse `::after` bounding-box interaction with `anchor:'center'` math. Disable pulse, remeasure.
- A5. MapLibre 4.7.1 upstream bug (related: gh maplibre-gl-js #2190, #6925). Upgrade to 5.x.

**Group B — DOM = project() but still visible drift:**
- B1. Tile canvas rendered at different Mercator scale than MapLibre's transform (globe projection sneaking in, non-standard tile size from OpenFreeMap).
- B2. Paper-overlay horizontal stripes (`repeating-linear-gradient(0deg, ...)`) create a parallax illusion against zooming tiles. Uniform across pins though — inconsistent with latitude-varying report.
- B3. devicePixelRatio / Hi-DPI subpixel mismatch.

**Group C — coords wrong:**
- C1. `moms_seed.json` lat/lon swap for a subset. Paris/Lyon/Marseille already spot-checked correct. Still worth grep'ing Hamburg/Lille/Toulouse against an authoritative source (2 min).

### Measurement results (2026-04-21)

Full correlation analysis across 40 sites at zoom 8:
- **r = 0.656** (moderate-to-strong latitude correlation)
- **slope = 55.6 px/degree** (drift increases northward)
- **Overlay visible vs hidden**: no change (A2 ruled out)
- **Container size / map.resize()**: no change (A3 ruled out)
- **Anchor change (center→bottom)**: correlation unchanged (anchor not culprit)

### Ruled out (evidence-based)

- Marker **anchor** calculation — tried 'center' and 'bottom', no effect.
- Marker **box-shadow** — removed, no effect.
- **Paper overlay mix-blend-mode** — hidden, no effect.
- **Tile provider** (raster Carto → vector OpenFreeMap) — drift persists across both.
- **Container size captured at init** — `map.resize()` before renderMarkers, no effect.
- **MapLibre 4.7.1 projection bug** — upgraded to 5.x, drift persisted.
- **DOM element CSS interactions** — removed shadows, border issues, etc.

### Root cause identified

**Custom DOM marker positioning in MapLibre has a latitude-dependent bug.** Evidence:
- Default maplibregl.Marker() (no custom element) → **r = 0.312, slope ≈ 0** ✓ NO DRIFT
- Custom button element with anchor: 'center' → **r = 0.656, slope = 55.6** ✗ DRIFT RETURNS
- Same drift pattern in both MapLibre 4.7.1 and 5.x with custom elements
- Issue is NOT in CSS, container size, overlay, or projection itself

### Solution

**Use default maplibregl.Marker() instead of custom DOM elements.** The default markers render correctly across all latitudes. Customize appearance via CSS targeting `.maplibregl-marker` class if needed, but avoid passing custom `element` to Marker constructor.

### Devil's-advocate notes to carry forward

1. "Paris is fixed" has not been measured — only eyeballed. A small drift at Paris is indistinguishable from zero by eye. Confirm with `__driftProbe`.
2. Toulouse-drifts-less-than-Lille, if confirmed numerically, breaks any symmetric-in-|Δlat| hypothesis (pure Mercator math mismatch). If **not** confirmed numerically, Mercator-mismatch hypothesis re-enters candidate list.
3. Code review found **nothing** obviously broken in marker handling (app.js:133–161). The bug is almost certainly not in the visible lines of app.js — it's either a container/layout issue (A3), an upstream MapLibre bug (A5), or a CSS-level interaction (A1/A2).
4. The handoff zip at the repo root is stale. The live files are in `maps-of-making/project/`.

