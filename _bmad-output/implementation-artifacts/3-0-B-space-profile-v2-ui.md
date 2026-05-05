# Story 3.0-B: Space Profile — v2 UI

Status: done

## Story

As a space coordinator or visitor,
I want the Space Profile card to match the finalized v2 visual design,
So that the layout, typography, and component hierarchy feel polished and intentional rather than improvised.

**Design rationale:** Story 3.0-A wired the data model (logo, contact, last_updated, subset tiers). Story 3.0-B applies the visual design Nicolas finalized in the Claude Projects design canvas (`Space Profile v2.html`), introducing `sp-*` CSS classes, a structured layout with a status bar, quick-facts grid, stepped unlock section, and terminal-style source data block.

---

## Scope

UI-only. No backend changes, no new data fields, no API changes. All data bindings from 3.0-A are unchanged — this story only changes DOM structure and CSS class names inside `renderDetail()`.

---

## Acceptance Criteria

### AC1 — Hero layout matches v2 design

**Given** any space card renders

**When** the drawer opens

**Then** the hero uses `sp-hero`: Caveat 28px name left, 44×44 `sp-logo` box right (image or SVG placeholder), JetBrains Mono address below, `sp-badge` row with bordered rectangular badges

---

### AC2 — Status bar present for non-seeded spaces

**Given** a confirmed, broken, aging, zombie, or dead space

**When** the drawer opens

**Then** a `sp-status-bar` strip renders between the hero and Quick Facts, showing a coloured dot + status phrase left, "updated X ago" right

**And** seeded spaces show no status bar (data not yet registered)

---

### AC3 — Quick Facts grid with inline contact channels

**Given** a non-seeded space

**When** the drawer renders

**Then** a `sp-section` labelled "Quick Facts" contains a `sp-facts` grid (92px key / 1fr value) with: Description, Website, Hours, (Next event if present), (Contact if s.contact present)

**And** contact channels render as `sp-channel` icon buttons inline in the Contact value cell, not as a separate section below

**And** email / twitter / mastodon / facebook use inline SVG icons; other channels use text abbreviations (`[ph]`, `[#]`, `[mx]`, `[fs]`, `↗`, `[xx]`)

---

### AC4 — Specialties as sp-pills, embed as sp-embed-btn

**Given** a space with specialties

**When** the drawer renders

**Then** specialties use `sp-pill` (rounded pill style), not the filter `.chip` class

**And** the embed CTA uses `sp-embed-btn` (full-width dark button with SVG icon), hidden on mobile via `.sp-embed-wrap { display:none }` at `< 768px`

---

### AC5 — Stepped unlock section

**Given** a confirmed or broken-with-guidance space

**When** `s.next_unlock` is set or `s.subset === 'spaceapi:compatible'`

**Then** a "What your data unlocks" section renders with `sp-unlock-step` rows: green ✓ marker for "done" state, accent → marker for "next" step

**And** the step text uses inline `<strong>` and preserves `s.next_unlock` content

---

### AC6 — Terminal-style source data block

**Given** a desktop (≥ 768px), non-seeded space with a successful `/api/space/{id}/raw` response

**When** Zone 3 renders

**Then** the JSON block is wrapped in `sp-terminal-wrap` with a dark `sp-terminal-head` showing "JSON · Endpoint Response" label and precise fetch timestamp

**And** the `pre.json.sp-terminal-body` uses v2 terminal colours (keys: `#8fc4e8`, strings: `#b8d89a`, numbers: `#e8c87a`)

**And** a `sp-trust-line` ("The map only reads & enhances your data…") appears below the terminal

**And** the disabled `sp-refresh-btn` renders below with "Refresh from endpoint" + "last: X ago" metadata

---

### AC7 — No regression

**Given** Stories 3.0 and 3.0-A behaviour

**When** 3.0-B changes are applied

**Then** filter chips (`.chip`) are unaffected — `sp-pill` is used only inside `renderDetail()`

**And** mobile suppression: Zone 3 (`.zone-source`), share CTA (`.share-cta`), embed wrap (`.sp-embed-wrap`) all hidden at `< 768px`

**And** 56 tests pass, 1 skipped (no backend changes)

---

## Files Touched

```
web/
  maps-of-making.html   ← added --status-bg to :root; added full sp-* CSS block (~80 rules)
  app.js                ← added _logoPlaceholder() and _contactChannel() helpers;
                           rewrote renderDetail() body to use sp-* structure
_bmad-output/
  implementation-artifacts/deferred-work.md  ← SVG icon collection entry
```

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Completion Notes

- AC1: `sp-hero` + `sp-name-row` + `sp-logo` (44×44 height, free width, transparent for real logos; SVG placeholder box on error/absent) + `sp-address` with fallback + `sp-badges-row`/`sp-badge` with per-kind colour classes
- AC2: `sp-status-bar` injected for all non-seeded statuses; dot colour varies by state (green / yellow for aging+zombie / red for broken); phrase from `statusPhrases` map
- AC3: Quick Facts grid replaces old `kv` dl; Name row removed (shown in hero); contact row inline via `_contactChannel()` helper; `sp-fact-empty` em element for absent values; Next event & Contact rows always rendered (even when empty)
- AC4: Specialties use `sp-pill`; embed uses `sp-embed-btn` inside `sp-embed-wrap` (CSS-hidden on mobile); old `btn btn-primary` embed button removed from this section
- AC5: Stepped unlock uses `sp-unlock-step` with `.done`/`.next` markers; `innerHTML` used for `<strong>` + `<code>` formatting; `s.next_unlock` text escaped for `<`/`>` before injection
- AC6: `sp-terminal-wrap` + `sp-terminal-head` wraps `pre.json.sp-terminal-body`; `jsonHighlight()` unchanged — new CSS rules target `.sp-terminal-body .k/.s/.n/.c` for v2 terminal colours; `_makeRefreshBtn()` helper produces `sp-refresh-btn` with SVG icon + `sp-refresh-meta` timestamp
- AC7: Filter `.chip` class untouched; `.zone-source` and `.share-cta` mobile-hide rules preserved; `sp-embed-wrap` mobile hide added; syntax check passed; no backend changes; UI refinements post-review: share/close as SVG icons, section labels darker, top-nav buttons unified to `--btn-h: 36px` height, logo free-width transparent
- 56 tests pass, 1 skipped

### Handoff to Story 3.1

The Space Profile v2 UI is complete. The following features are now stubbed/disabled pending the heartbeat endpoint:
- **Manual refresh button** — `sp-refresh-btn` is rendered as disabled with `title="Manual refresh available soon"` in Zone 3. Story 3.1 wires the `POST /api/heartbeat-space/{space_id}` endpoint and implements the click handler, cooldown, and Zone 3 re-render.

### Deferred

- **SVG contact channel icon collection** — email/twitter/mastodon/facebook have SVGs; all others use text abbreviations. Full platform SVG set (≥15 channels) needed before public launch. → Epic 5 / UI polish (logged in deferred-work.md)
- **Backend tier extension: event / image / state fields** — `classify_subset()` in `infra/link_handler/main.py` needs to extend the tier chain beyond current `logo → contact` to add `event`, `image`, `state` as ordered next-fields, surfacing them in `s.next_unlock` strings. → Story 3.1 or Epic 5
- **True change detection for "last updated"** — `mom:lastUpdated` currently updated on every fetch (not just when content changes). Genuine change detection requires diffing snapshot content. → Epic 7

### Change Log

- 2026-05-05: Story 3.0-B implemented — Space Profile v2 UI applied; refactored logo to free-width transparent, share/close as SVG icons, section labels darker, nav buttons to unified --btn-h height; always render Next event + Contact rows with fallback placeholders
