# Story 9.2: Drawer UX on MoM Map — Bernard One-Liner + URL Input + CTA

Status: done

## Story

As a space coordinator browsing the MoM map,
I want a low-friction entry point into the wizard that respects my time and doesn't assume I have a JSON endpoint already,
so that I can choose my path — paste a URL I already have, or start from scratch — in four seconds or less.

## Acceptance Criteria

### AC1 — Drawer is an RPG-style fork (redesigned 2026-05-30)

**Given** the "Add your space" drawer is open (triggered via `btn-addurl` → `setDrawer('addurl')`)

**When** Story 9.2 lands

**Then** the drawer is a **fork serving two publics**, not a primary/secondary stack. The body
(`#drawer-addurl .addurl-body`) contains one frank sentence carrying **two inline-link choices**:

> *"Two ways onto the map. [Tell me about your space], or [paste a URL] if you've already got one. Either's fine."*

where the bracketed phrases are real `<button class="inline-link">` elements inside the prose:
1. **"Tell me about your space"** (`id="btn-wizard-cta"`) → opens the wizard (`genjson.mapsofmaking.org`, `?resume=1` if a `genjson_draft` exists) in a new tab.
2. **"paste a URL"** (`id="btn-reveal-url"`) → reveals the hidden `#url-fork` (existing-url-input + Fetch & validate + result) inline and focuses the input.

**And** the URL fork (`#url-fork`) is `hidden` on open — progressive **only** for the URL field;
both choices are visible at all times.

**And** the drawer is **top-center docked** (drops from the top like `.search-drawer`) and
**content-sized** (auto-height), not a full-height panel.

**And** the phrase "Tell me about your space" appears **once** (as the inline link, not also as prose).

**Bernard voice (drawer = ~20% bleed):** dry, frank, short sentences, no exclamation marks, no
"No JSON", no shaming. **No name reveal** — "Bernard" first appears only on the wizard path
(Story 9.3/9.5), never in the drawer. Per `memory/project_bernard_character.md`.

### AC2 — URL input ID and attributes

**Given** the existing Story 2.1 fetch-and-validate path relies on `$('#url-input')`

**When** the drawer is rendered

**Then** the input element has `id="existing-url-input"` (new canonical id per spec) **AND** `id="url-input"` is kept as an alias via a hidden duplicate OR the JS references are updated to use `existing-url-input` throughout

> **Implementation note:** The safest path is to rename `url-input` → `existing-url-input` in HTML and update the two JS references in `app.js` (`$('#url-input')` at lines ~994 and ~1006). The `_addUrlOriginalHTML` snapshot mechanism will capture the new id automatically.

### AC3 — CTA button behaviour

**Given** the coordinator clicks "Tell me about your space →"

**When** `localStorage.getItem('genjson_draft')` is checked

**Then** if a draft exists: opens `https://genjson.mapsofmaking.org/?resume=1` in a new tab (`target="_blank" rel="noopener"`)

**And** if no draft: opens `https://genjson.mapsofmaking.org/` in a new tab

### AC4 — Mobile layout (< 768 px)

**Given** the drawer is open on a viewport narrower than 768 px

**When** both the URL input and CTA button are visible

**Then** the CTA button is full-width (`width: 100%`) and there is no horizontal overflow (existing `#drawer-addurl { max-height: 80vh }` mobile rule is preserved)

### AC5 — Accessibility gate

**Given** the updated drawer HTML is loaded

**When** axe-core (or equivalent) runs against it

**Then** zero WCAG 2.1 AA violations are reported

**And** operator confirms visually: drawer renders correctly on desktop and mobile with no layout overflow.

---

## Files to Modify

| File | Change |
|------|--------|
| `web/maps-of-making.html` | Replace `#drawer-addurl .addurl-body` inner HTML; rename `id="url-input"` → `id="existing-url-input"` |
| `web/app.js` | Update `$('#url-input')` references (lines ~994, ~1006) → `$('#existing-url-input')`; add CTA click handler with `localStorage` check |

**No other files touch.**

---

## Developer Context

### Current drawer state (pre-9.2)

`web/maps-of-making.html` lines 649–670:

```html
<!-- Add URL drawer (right, replaces detail when open) -->
<aside class="drawer right" id="drawer-addurl" ...>
  <div class="drawer-head">
    <h2>Add your URL</h2>
    <button class="close" ...>✕</button>
  </div>
  <div class="drawer-body">
    <div class="addurl-body">
      <p style="...">Run your space? Paste the public URL...</p>
      <label for="url-input">Endpoint URL</label>
      <input id="url-input" type="url" placeholder="https://your-space.example/maker.json" />
      <div class="btn-row">
        <button class="btn btn-primary" id="btn-fetch-url">Fetch & validate</button>
      </div>
      <div id="url-result" class="mono" ...></div>
    </div>
  </div>
</aside>
```

The `<p>` copy ("Run your space?…") is the only element being removed. The input, fetch button, and result div are preserved and re-wired.

### JS wiring to preserve (app.js)

- `_addUrlOriginalHTML` (line ~988): snapshot of `.addurl-body` innerHTML taken on first open — **must still work** after rename. Since the snapshot is taken at runtime, renaming the id in HTML is sufficient; the snapshot will capture the new id.
- `_resetAddUrlForm()` (line ~990): restores `.addurl-body` innerHTML from snapshot. No change needed.
- `_wireAddUrlHandlers()` (line ~1000): attaches click to `#btn-fetch-url`. No change needed.
- `_onFetchUrl()` (line ~1004): reads `$('#url-input').value`. **Update this reference to `#existing-url-input`.**
- `_resetAddUrlForm` result/input checks (line ~993–995): `$('#url-result')` and `$('#url-input')`. **Update `#url-input` ref to `#existing-url-input`.**
- `setDrawer('addurl')` (line ~1176): calls `_resetAddUrlForm()` then focuses `$('#url-input')`. **Update focus target to `#existing-url-input`.**

### Where to add the CTA handler

Add inside the existing `_wireAddUrlHandlers()` function, immediately after the `btn-fetch-url` listener:

```js
const ctaBtn = $('#btn-wizard-cta');
if (ctaBtn) {
  ctaBtn.addEventListener('click', () => {
    const draft = localStorage.getItem('genjson_draft');
    const url = draft
      ? 'https://genjson.mapsofmaking.org/?resume=1'
      : 'https://genjson.mapsofmaking.org/';
    window.open(url, '_blank', 'noopener');
  });
}
```

Give the CTA button `id="btn-wizard-cta"` in HTML.

### Mobile: CTA full-width

Add to the existing `@media (max-width: 767px)` block (around line 386):

```css
#btn-wizard-cta { width: 100%; }
```

### Bernard one-liner copy

Story 9.5 (voice pass) is not done yet — draft copy is acceptable here. Use exactly:

> *"Two ways through. [Tell me about your space]. Or paste a URL if you already have one. Either is fine."*

The bracketed `[Tell me about your space]` is intentional — it echoes the CTA label and is part of Bernard's voice register (register: Ron-Swanson-on-fort; they/them). Do not rephrase or add punctuation.

### Style: one-liner paragraph

The one-liner `<p>` should inherit existing `.addurl-body` font styles. No special styling required — plain text in a `<p>` with `margin: 0 0 12px` is sufficient.

### CTA button styling

Use the existing `.btn` class. Add `.btn-primary` only if the design calls for it — the spec does not require a filled button; consistency with "Fetch & validate" is acceptable. The CTA button goes **after** the URL input + fetch row (below `#url-result`), not above it.

---

## Isolation Notes

- This is a **pure front-end story** — no backend changes, no Docker restarts needed.
- Local dev: open `web/maps-of-making.html` directly in browser (or via `python3 -m http.server` from `web/`), click "Add your URL" to test the drawer.
- VPS deploy: `scp web/maps-of-making.html hetzner:/srv/mapsofmaking/web/maps-of-making.html` and `scp web/app.js hetzner:/srv/mapsofmaking/web/app.js`. No nginx reload needed (static files).
- Distrobox note: `distrobox-host-exec` not needed — no container interaction.

---

## Out of Scope

- Modal vs new-tab decision: 9.2 uses new tab only. If Story 9.3 adds a modal, 9.2 is updated then.
- Bernard voice refinement: that is Story 9.5. Draft copy is fine here.
- `localStorage` key `genjson_draft` is read-only here; it will be written by Stories 9.3+.

---

## Story Completion Checklist

- [x] `#drawer-addurl .addurl-body` HTML updated: one-liner `<p>` + renamed input + fetch button + result div + CTA button
- [x] `id="url-input"` renamed to `id="existing-url-input"` in HTML
- [x] All three `$('#url-input')` references in `app.js` updated to `$('#existing-url-input')`
- [x] CTA handler added in `_wireAddUrlHandlers()` with `localStorage` check
- [x] Mobile CSS rule `#btn-wizard-cta { width: 100%; }` added
- [x] Operator visual confirmation: desktop + mobile layout OK, no overflow
- [x] axe-core (or browser accessibility check): zero WCAG 2.1 AA violations on drawer
- [x] Sprint status → `done` (after code review)

---

## Dev Agent Record

### Files Modified
- `web/maps-of-making.html` — `.addurl-body` HTML replaced; drawer title/aria updated; `url-input` → `existing-url-input`; `#btn-wizard-cta` added; mobile CSS rule added
- `web/app.js` — 3 `#url-input` refs → `#existing-url-input`; CTA handler added in `_wireAddUrlHandlers()`

### Completion Notes
All code changes applied. Two checklist items require operator action: visual confirmation on desktop/mobile, and accessibility audit. No backend changes, no regressions possible in server-side code.

### Post-review redesign (operator feedback, 2026-05-30)
Initial build worked functionally but layout/voice needed rework. Operator chose:
- **"Two doors, wizard first" layout:** Reordered drawer to match Bernard's narrative — wizard CTA is now the primary (filled, full-width `.cta-primary`) button up top, followed by an "— or —" divider (`.or-divider`), then the URL path as the secondary option (plain `.btn`, not primary). Label changed from "Endpoint URL" to "Already have a JSON URL?".
- **"Warm but blunt" Bernard voice:** Replaced bracketed copy with *"No JSON? No problem. Tell me about your space and we'll make one together. Got a URL already? Even easier — paste it below."* (the literal `[brackets]` read as broken markup on screen).
- Removed auto-focus on the secondary URL input (drew the eye away from the primary CTA).
- Removed now-redundant mobile `#btn-wizard-cta { width: 100% }` rule — `.cta-primary` is full-width at all breakpoints.
- Added `.intro`, `.cta-primary`, `.or-divider` styles to the Add-URL drawer CSS block.

### Second redesign — RPG fork (operator feedback, 2026-05-30)
The "two doors" stack still read as primary/secondary and repeated the wizard phrase. Operator
reframed the drawer as a **fork serving two publics** with RPG text-adventure navigation:
- Copy is now one frank sentence with **two inline-link choices** (`.inline-link` buttons):
  *"Two ways onto the map. [Tell me about your space], or [paste a URL] if you've already got one. Either's fine."* — no "No JSON", no repetition, no exclamation, no Bernard name (drawer = ~20% bleed; name reveal is wizard-only).
- **URL field hidden** (`#url-fork[hidden]`) until "paste a URL" is clicked (`#btn-reveal-url` → unhide + focus). Both choices stay visible; only the input is progressive.
- Drawer **repositioned top-center** (drops from top like `.search-drawer`) and **auto-height** (`bottom:auto`) so it sizes to content instead of a tall empty panel. Mobile bottom-sheet rules (`!important`) still win < 768px.
- Removed `.cta-primary` / `.or-divider` styles (superseded); added `.inline-link` + `#drawer-addurl` top-center override.
- `#btn-wizard-cta` localStorage→wizard handler unchanged; Story 2.1 fetch path (`existing-url-input` / `btn-fetch-url` / `url-result`) untouched.

### Change Log
| Date | Change |
|------|--------|
| 2026-05-30 | Initial implementation (one-liner + URL input + CTA) |
| 2026-05-30 | Redesign 1: "two doors" stack, warm-but-blunt voice |
| 2026-05-30 | Redesign 2: RPG fork — inline-link choices, progressive URL reveal, top-center auto-height drawer |
| 2026-05-30 | Polish: grid-row reveal animation on URL fork; result padding fix; em-dash dialogue opener; copy → "paste your endpoint URL" (intentional jargon polarization + ownership); **Special Elite** typewriter font test on `.bernard-voice` (canon deferred to Story 9.5) |
| 2026-05-30 | URL reveal made a **toggle** (click to open, click to collapse with reverse animation; `aria-expanded`/`aria-controls`). Consolidated **Bernard bible** created at `planning-artifacts/bernard-bible.md`. |
