# Quick-Dev TODO — First-Load Correctness Fixes

**Created:** 2026-06-05 · **Author:** Winston (architect session) · **Owner:** quick-dev / Amelia
**Status:** ✅ IMPLEMENTED 2026-06-06
**Scope:** `web/app.js` + nginx config for `/data/spaces.geojson`. Three small, low-risk fixes. No data-model or pipeline changes.
**Theme:** *The first load (and shared/embedded load) should behave the way a returning or linked visitor expects.*

These are independent of the in-flight map-visualization (DOM→GL) work. Safe to land in parallel.

---

## ⚠️ Follow-up: viewport-first sequencing for `?space=` links (not in original scope)

Fix 2 as implemented likely uses `selectSpace(id, {fly:true})` after map load — which works but is the *fly-then-render* pattern: map boots at EU overview, loads EU tiles, then flies to the space. Two tile fetches, visible animation the visitor didn't ask for.

**The better pattern (for the GL migration slice):** encode coords in the share URL — `/?space=openfab&lat=51.50&lon=-0.12` — so `initMap()` can start at the target viewport before any tile loads. First tile fetch is local area only; no `flyTo` needed on cold load. Share button already knows the space object at click time, so adding coords is trivial.

Tag: → Thread B GL migration slice.

---

## Fix 1 — Stale "all broken" on revisit  ⚠️ HIGHEST PRIORITY (embed-killer)

**Symptom:** On a non-hard-refresh revisit, the map opens with every endpoint marked `broken`. Hard-refresh fixes it. On an embedded page (visitor never hard-refreshes) the whole network looks dead → credibility bug.

**Root cause:** The load-time fetch has no cache discipline:
```js
// web/app.js:72
const res = await fetch('/data/spaces.geojson');   // no cache-bust, serves stale HTTP cache
```
Every *other* fetch of this file already cache-busts with `?t=${Date.now()}` (lines ~826, ~1100, ~1466). Because freshness is computed **client-side at view time** against `Date.now()` (three-token model: `_ageMinutes` → `computeAxisA`), a stale cached file carries old `observed_at` tokens whose age exceeds the broken threshold → everything paints `broken`.

**Fix (do both — band-aid + contract):**
- **Client:** cache-bust the load-time fetch in `loadData()` — `fetch('/data/spaces.geojson?t=' + Date.now())` or `{ cache: 'no-cache' }`. Matches existing pattern.
- **Server (correct fix):** set `Cache-Control: no-cache` (or short `max-age` + `must-revalidate`) on `/data/spaces.geojson` in nginx. The file is a freshness snapshot; it must revalidate. Protects embeds and any future consumer that doesn't know the `?t=` trick.
  - Touch the maps-nginx location block (see memory: infra_gateway_nginx).

**Done when:** A normal browser revisit (no hard refresh) shows correct, current statuses. Verify with DevTools that the geojson response is revalidated, not served `200 (from disk cache)`.

---

## Fix 2 — `?space=<id>` deep link does nothing on load

**Symptom:** Sharing a profile (e.g. `https://mapsofmaking.org/?space=openfab`) loads the default EU view and ignores the param. Auto-zoom only works in the post-registration path.

**Root cause:** The Share button *generates* `/?space=<id>` (`web/app.js:548`) but `parseParams()` (lines ~900–921) reads `networks`, `country`, `status`, `specialty`, `q`, `bbox`, `center` — **never `space`**. The auto-zoom `selectSpace(id, {fly:true})` only fires after registration (line ~1145), not from the URL.

**Fix:** In `parseParams()`, read `p.get('space')`. After map + data are both ready, call `selectSpace(id, { fly: true })` (reuse the existing path). 
**Ordering matters:** must fire *after* `loadData()` resolves (space must exist in `state.spaces`) AND after the map can `flyTo`. Align with the `map.once('load')` timing used by `bbox`/`center`. While here, **verify `bbox`/`center` actually fire** — they share this timing and may be affected by Fix 3's rework.

**Done when:** Loading `/?space=openfab` cold opens the map flown to OpenFab with its detail drawer/selection active.

---

## Fix 3 — Loader jank: dismiss races tile paint

**Symptom:** "Buggy feeling" on first load — markers appear over half-painted grey tiles, then tiles pop in.

**Root cause:** Two paths flip `mapInitialized` and whichever loses early-returns:
```js
// web/app.js:185-193
map.on('load', () => { if (mapInitialized) return; mapInitialized = true; ... });
setTimeout(() => { if (!mapInitialized) { mapInitialized = true; ... } }, 1500); // blind fallback
```
On slow tiles the 1500ms fallback fires first, dismisses the loader, renders markers onto an unpainted map; the real `load` then no-ops.

**Fix:** Replace the boolean-guard with a single **idempotent `ready()`** safe to call from either path, so a late `load` still does a clean `renderMarkers()` instead of no-op'ing. Consider dismissing the loader on `styledata` (style parsed) and letting tiles fade in underneath, rather than blocking the screen on first-tile fetch.
**Note:** We are staying on OpenFreeMap for now (no PMTiles) — this fix targets *perceived* slowness, not tile latency. Add `<link rel="preconnect">` to `tiles.openfreemap.org` in `web/maps-of-making.html` `<head>` for a free handshake win.

**Done when:** Map chrome/markers never render over unpainted tiles; a slow tile load degrades gracefully (tiles fade in) without the markers-over-grey flash.

---

## Suggested sequencing
1. **Fix 1** can ship standalone today (≈1-line client + 1 nginx header) — it's the active embed risk.
2. **Fix 2 + Fix 3** together — they share the map-ready / `map.once('load')` timing rework.

## Verify
- Manual: normal revisit (no hard-refresh) shows current statuses; `?space=openfab` cold-loads zoomed-in; throttle network (DevTools "Slow 3G") and confirm no markers-over-grey flash.
- Watch for regressions in existing `bbox`/`center` deep links and the post-registration auto-zoom (line ~1145).
