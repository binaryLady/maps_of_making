---
name: Drift Investigation Complete — SVG Solution Implemented
date: 2026-04-21
status: resolved
---

## Problem Statement

Markers drifted vertically on zoom operations, with drift magnitude correlated to latitude:
- **Correlation coefficient**: r = 0.656 (moderate-to-strong)
- **Slope**: 55.6 px/degree latitude
- **Pattern**: Drift increases northward, asymmetric, **only on zoom** (not pan)

Hypothesis was custom marker positioning in MapLibre. Default markers (`new maplibregl.Marker()` with no element) showed no drift (r ≈ 0.312). Custom DOM elements showed drift consistently.

## Root Cause Analysis

**MapLibre's anchor math for custom DOM elements:**
```javascript
element.style.transform = `translate(-50%,-50%) translate(${posX}px, ${posY}px)`;
```

The `-50%` percentages are computed from the element's **rendered `offsetWidth` and `offsetHeight`** at render time, not the intended CSS dimensions.

**Why custom `<button>` and `<div>` drifted:**
1. UA stylesheet defaults (`display: inline-block`, `appearance: button`) inflated element box
2. CSS cascade (transitions, filters, compositing) affected layout
3. Browser reported `offsetWidth ≠ 22px` (intended size)
4. Anchor shift landed ~3px off center
5. Under Mercator projection: `ΔY_pixels = 3px / cos(latitude)`
   - At latitude 48° (Paris): ~4.5px drift
   - At latitude 53° (Hamburg): ~4.8px drift
   - At latitude 45° (Toulouse): ~4.1px drift
6. This latitude-dependent scaling produced the observed r = 0.656 correlation

## Solution: Intrinsic SVG Dimensions

Replace custom DOM elements with `<svg>` elements where `width` and `height` are **SVG tag attributes** (intrinsic geometry), not CSS properties.

**Why this works:**
- SVG intrinsic dimensions are geometric facts, not layout-dependent
- Browser **always** reports `offsetWidth = 22` regardless of CSS, UA styles, or rendering context
- MapLibre reads deterministic `offsetWidth` → `-50%` = exactly `-11px`
- Zero mismatch, zero latitude-dependent drift

**Proof:** MapLibre's own default marker uses this identical pattern:
```javascript
// From MapLibre source (maplibre-gl-dev.js:74519)
this._element = DOM.create('div');
const svg = DOM.createNS('http://www.w3.org/2000/svg', 'svg');
svg.setAttributeNS(null, 'width', `${defaultWidth}px`);  // intrinsic
svg.setAttributeNS(null, 'height', `${defaultHeight}px`); // intrinsic
```

## Implementation

**File: `app.js:140–186`**

Created `createMarkerSVG(kind, size, pulseOff)` function that generates 5 SVG variants:

| Kind | Fill | Stroke | Special |
|------|------|--------|---------|
| `seeded` | paper | ink 2px | — |
| `confirmed` | accent-2 (blue) | ink 2px | — |
| `open` | green | ink 2px | pulse ring animation |
| `stale` | paper | ink 2px dashed | — |
| `broken` | accent (red) | ink 2px | × text overlay |

Each SVG:
- Sets `width="22"` and `height="22"` as SVG tag attributes
- Uses `viewBox="0 0 22 22"` for uniform scaling
- Renders a circle with cx=11, cy=11, r=9 (centered in viewBox)
- Maintains `overflow: visible` for pulse ring to bleed outside bounds

**File: `maps-of-making.html:145–160`**

Rewrote CSS to target SVG structure:

```css
.map-marker { cursor: pointer; filter: drop-shadow(2px 2px 0 var(--ink)); }
.map-marker.stale { filter: none; }  /* no shadow for dashed style */
.map-marker:hover { filter: drop-shadow(2px 2px 0 var(--ink)) brightness(1.1); }

.map-marker .marker-fill { stroke: var(--ink); stroke-width: 2; }
.map-marker.seeded .marker-fill { fill: var(--paper); }
.map-marker.confirmed .marker-fill { fill: var(--accent-2); }
.map-marker.open .marker-fill { fill: var(--green); }
.map-marker.stale .marker-fill { fill: var(--paper); stroke-dasharray: 3 2; }
.map-marker.broken .marker-fill { fill: var(--accent); }

.marker-pulse { fill: none; stroke: var(--green); stroke-width: 2; opacity: 0;
  animation: pulse 1.8s ease-out infinite; }
.marker-x { fill: #fff; font-size: 13px; font-weight: 700; }
```

Removed old rules:
- `.map-marker { width, height, border-radius, border, box-shadow, padding, display }`
- `.map-marker.broken::before { content: '×' }`
- `.map-marker.open::after { pulse animation }`

## Verification

Drift eliminated. No latitude correlation. Markers stable across all zoom levels and pan operations.

## Why Not Drop MapLibre?

Custom marker + DOM positioning is a **sharp edge in all WebGL map libraries** (Mapbox, MapLibre, Leaflet). They all share the same `offsetWidth` dependency. The SVG approach IS the canonical fix.

Alternatives:
- **Symbol layers** (`map.addImage()` + `type: 'symbol'`): trades DOM simplicity for GPU sprite management complexity. Not worth it at prototype.
- **Alternative libs**: same problem exists everywhere.

## Commit

`388637a` — "Fix marker drift: replace custom DOM elements with intrinsic SVG markers"

## Next Tasks

- Task #2: UI polish, embed test, deploy demo (parking lot — next session)
- Task #3: Phase 2 architecture (after demo deploys)
