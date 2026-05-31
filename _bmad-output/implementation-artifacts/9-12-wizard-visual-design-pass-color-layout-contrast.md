# Story 9.12: Wizard Visual Design Pass — Color, Layout & Contrast

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a space coordinator stepping from the MoM map into Bernard's Workshop (`genjson.mapsofmaking.org`),
I want the wizard to look finished, legible, and coherent — a settled visual + interaction frame, not a half-styled form,
so that the tool feels trustworthy and effortless, and every later tier (9.6/9.7/9.10) plugs into a frame that is already locked.

**Why this story comes first (operator intent, 2026-05-31):** Epic 9's UI will keep growing (9.6 Tier 2, 9.10 Tier 3, …). We lock the **frame the next stories inherit** now, so the pattern isn't re-litigated five more times. This story owns the *visual skin* **plus** the two structural frame elements from the UX spec that all future tiers depend on: the **transient intro** and the **ownership strip**. The deep conversational field-by-field reveal is explicitly **deferred** (see Out of Scope) — the frame ships clean and reviewable first.

## Acceptance Criteria

> **Authority:** `_bmad-output/planning-artifacts/ux-bernard-wizard-spec.md` (locked principles P1–P6) governs this story. `bernard-bible.md §4` governs typography. Copy is **out of scope** — it stays in `bernard_copy.yaml` via `COPY.*` lookups (Story 9.5 domain); this story changes **only** visual/layout/interaction-frame, never string values.

### AC1 — World: Direction B locked — the dusk workshop (threshold, not lair)

**Given** the map drawer is a **light riso/zine** world (`web/maps-of-making.html` `:root`: `--paper #f7f2e7`, riso-red `--accent oklch(62% 0.18 25)`, cobalt `--accent-2 oklch(55% 0.17 250)`, Inter Tight) and Bernard's hermit-crab **vision** sees blue/yellow/green/UV but **not red** (bernard-bible §1; UX spec §3b)
**When** the wizard palette is built
**Then** the wizard is **Direction B — a dark "workshop interior"** you cross into (full-voice Bernard), **grounded in Bernard's vision**:
- **Base = liminal dusk** (deep blue-green dark), **not** pitch fort-black — the workshop is the **border crossing** between the MoM map and Mother Sands (the lair, reserved for Epic 8 lore); it reads as a threshold/antechamber, not the inner sanctum
- it adopts the drawer's **semantic discipline** (AC2) and shared grammar: Special Elite, underline links, `2px` radius, shadow language (*Jakob's Law*)
**And** the exact hues are an **operator-visual call** during implementation (Task 0 renders the palette for sign-off, one change at a time) — but the **direction** (dark dusk threshold + spectrum mapping) is **locked**, not re-litigated
**And** AC2–AC9 apply within Direction B

### AC2 — Semantic color discipline (mirrors the drawer fix)

**Given** the map's semantic convention (drawer `.inline-link` uses cobalt `--accent-2`; red/`--accent` is reserved for errors/broken/danger only — fix 2026-05-31)
**When** the wizard palette is reworked
**Then** color is mapped to **Bernard's spectrum** (AC1; bernard-bible §1; UX spec §3b):
- **Amber/brass** (yellow band — Lagavulin, lamplight): Bernard's voice (`.bernard-voice`), warmth, **primary CTA**
- **Blue** (in-spectrum; rhymes with drawer cobalt): **links / navigation**
- **Green** (in-spectrum): **valid / confirmed / derived-success** (e.g. successful geocode `coords-preview`, bedrock passed)
- **Red: errors/danger ONLY** (validation gaps, geocode-failure `.coords-preview.error`, `clear-link:hover`, `.warn-banner`) — the one color *outside* Bernard's vision, hence maximally salient as "something's wrong"
- **UV** (the band only Bernard sees): a faint cool shimmer for curiosity hooks / hover-focus glow — **optional, sparingly**; defer if it muddies the pass
**And** **no** neutral, positive, link, or CTA control ever renders in the error (red) color
**And** the focus-visible treatment matches the drawer pattern (visible outline, `outline-offset`)

### AC3 — Tier hierarchy via size + color, never weight

**Given** Special Elite is single-weight — `font-weight: bold` is a no-op (bernard-bible §4, locked Story 9.5)
**When** Tier 0 / Tier 1 (and the locked-state of higher tiers) are made visually distinct
**Then** hierarchy is achieved through **font-size + color contrast + spacing** (the muted-tombstone pattern), **never** `font-weight`
**And** no `font-weight` rule is added to `.bernard-voice` (reviewers reject any such rule)
**And** the canonical `.bernard-voice` triplet stays intact: `font-family: 'Special Elite', var(--font-mono), monospace; font-size: 17px; line-height: 1.55;` (color/border/padding/margin may be styled around it; the triplet is locked)
**And** the `.tier-label` / `.tier-block` / locked-tier (`.tier-locked`) states read as a clear progression

### AC4 — Spacing, layout & rhythm

**Given** the current `field-row` / `tier-block` / `btn-row` / fork layout in `genjson.js`
**When** the layout pass lands
**Then** field-row vertical rhythm, tier-block separation, and the fork-doors have consistent, comfortable spacing (breathing room; a single spacing scale, not ad-hoc px)
**And** inline `style="…"` attributes scattered in the `render()` template strings are consolidated into the `CSS` block where practical (so styling is maintainable in one place), without changing behavior
**And** the `680px` `.wiz-container` max-width and centered column are preserved

### AC5 — Transient intro (UX spec §3, P2)

**Given** the wizard currently renders the Bernard intro as permanent chrome at the top (`render()` appends `.bernard-voice` intro that never recedes — screenshot 2026-05-31 "too much")
**When** the page loads
**Then** the intro (`COPY.wizard_intro`) **launches like a loading beat, then recedes / gives way** to the Tier 0 bedrock step (it does not permanently occupy the top of the viewport)
**And** the recede is cheap and tasteful (CSS transition or a one-shot reveal — no heavy animation, no library; respects `prefers-reduced-motion`)
**And** the intro copy itself is **unchanged** (`COPY.wizard_intro`, em-dash prepended by JS) — only its **presentation/persistence** changes
**And** the resume warning (`COPY.localstorage_warning`) and `clear-btn` behavior are preserved

### AC6 — Ownership strip (UX spec §4, P1)

**Given** UX spec §4 defines a persistent bottom line as the literal home of "you can always walk with your file"
**When** the wizard renders
**Then** a single, quiet, **persistent bottom strip** carries three elements:
1. **Live preliminary filename** — computed as `<space-slug>-<city-slug>-<YYYY-MM-DD>.json` (e.g. `noisebridge-san-francisco-2026-05-31.json`), updating live as `draft.space` / `draft.city` change; falls back to `space-…` when name is empty (reuse/extend existing `slugify()` in `genjson.js`; **today's date** from `new Date()`)
2. **Shy progress indicator** — marks **bedrock** as its one threshold (goal-gradient); past bedrock it grows softly toward a faint full-state horizon. It **never** shows a percentage, never turns red, never signals "incomplete" or demands completion (P4: Bernard isn't needy). Minimal by design.
3. **Always-present Export** — export is available from the strip **at all times**, quiet and subordinate to the primary CTA, **including before bedrock passes** (the file is yours even half-built)
**And** the export filename produced by `exportJSON()` matches the strip's displayed filename convention (currently `slugify(name)`-only — **update** to `<space>-<city>-<date>.json`)
**And** the existing per-tier `Export JSON` buttons are **reconciled** with the strip (either removed in favor of the strip's always-on export, or kept but no longer the only path) — no duplicate/conflicting export affordances
**And** the strip enforces ownership wording already present in copy; **no new copy strings are invented here** (if a label is needed, add the key to `bernard_copy.yaml` per the 9.5 SSOT process — do not hardcode)

### AC7 — Contrast / accessibility (WCAG AA)

**Given** the 9.3 "contrast pass" (lighter surface/border/text + explicit placeholder color) is in place but unfinished
**When** the visual pass completes
**Then** text/background, placeholder, border, and every accent meet **WCAG AA** (≥ 4.5:1 for body text, ≥ 3:1 for large text / UI affordances) on the **dusk base** (Direction B)
**And** "dusk" is a **hue shift, not a lightness drop** — the base is a deep blue-green-tinted dark at roughly the current `#1a1a1a` lightness (the sea at dusk), **not** darker; near-white body text keeps its high contrast
**And** the drawer's accents are tuned for a **light** background — on the dark dusk base they are **re-derived lighter** (amber/blue/green lifted in lightness) so links/CTAs/confirmations stay legible *over* the dark; do **not** copy the drawer hex values unchanged (the blue link especially will fail contrast on dark)
**And** the disabled-button state (`.btn:disabled { opacity: 0.35 }`) and `.tier-locked { opacity: 0.4 }` remain perceivable (not invisible) — verify they still read as "present but inactive"
**And** focus states are visible for keyboard navigation on every interactive element

### AC8 — Mobile usable

**Given** the map is already mobile-responsive (Story 2.6) but the wizard is not verified on small screens
**When** the wizard is viewed at ≤ 480px width
**Then** the container, field rows, fork-doors (`flex-wrap` already present), button rows, and the ownership strip reflow without horizontal scroll or clipped controls
**And** tap targets meet a reasonable minimum (~44px height for primary controls)
**And** the transient intro and strip behave correctly at small width

### AC9 — No regressions; tests green

**Given** the wizard's behavior (geocode debounce, manual-coords fallback, localStorage save/resume, tier-0 gate, blur normalizers, validation warnings, export) is established and working (Stories 9.3, 9.5)
**When** the visual pass lands
**Then** **all existing behavior is preserved** — this is a styling + frame story, not a logic story
**And** `COPY.*` lookups are untouched, so `pytest tests/test_bernard_voice_completeness.py` still passes
**And** `bernard_copy.json` is regenerated only if the YAML changed (AC6 strip label, if any) via `make bernard-copy`; `test_json_matches_yaml` stays green
**And** operator visually confirms the result (no automated visual testing — per `memory/feedback_ui_iteration.md`, one change at a time)

## Tasks / Subtasks

- [ ] **Task 0 — Render the dusk-workshop palette (AC1, Direction B locked).** Build the liminal-dusk base + amber/blue/green/red(+optional UV) spectrum mapping; present the **hues** to the operator for visual sign-off (one change at a time) before the rest of the pass. The *direction* is locked — only exact hues are reviewed, not A-vs-B.
- [ ] **Task 1 — Palette + semantic discipline (AC2).** Define CSS variables for the chosen world; map links/positive/CTA → non-error accent, error/danger → reserved error color only. Audit every color use in the `CSS` block and inline styles.
  - [ ] Match drawer focus-visible + link (underline, `text-underline-offset`) treatment.
- [ ] **Task 2 — Tier hierarchy via size+color (AC3).** No `font-weight`; verify `.bernard-voice` triplet intact; make tier states a clear progression.
- [ ] **Task 3 — Spacing/layout pass (AC4).** Establish one spacing scale; consolidate scattered inline `style=""` into the `CSS` block where practical; preserve container width.
- [ ] **Task 4 — Transient intro (AC5).** Intro loads then recedes/gives way to Tier 0; honor `prefers-reduced-motion`; copy unchanged.
- [ ] **Task 5 — Ownership strip (AC6).** Persistent bottom strip: live `<space>-<city>-<date>.json` filename; shy threshold-not-quota progress indicator; always-on subordinate export. Update `exportJSON()` filename convention. Reconcile the per-tier export buttons. Any new label → `bernard_copy.yaml` (not hardcoded).
- [ ] **Task 6 — Contrast/accessibility (AC7).** Verify WCAG AA; disabled/locked states perceivable; focus visible.
- [ ] **Task 7 — Mobile (AC8).** Verify/reflow at ≤480px; tap-target sizes.
- [ ] **Task 8 — Regression + tests (AC9).** Manually exercise geocode/resume/export/tier-gate/normalizers; run `pytest tests/test_bernard_voice_completeness.py tests/test_json_matches_yaml*` (venv); `make bernard-copy` if YAML changed; operator visual sign-off.

## Dev Notes

### Where the code lives — read before touching

- **All wizard CSS is a single template literal** — the `CSS` const in `web/genjson/genjson.js` (~lines 67–285), injected into `#wizard-root` via a `<style>` element in `render()`. **There is no separate stylesheet and no build step.** Edit the `CSS` const for styling.
- **Inline `style="…"` attributes** are also scattered through the `render()` `innerHTML` template strings (e.g. country-code field `style="text-transform:uppercase;width:6rem"`, `#manual-coords` `display:none`, the resume-warn margin block, fork-note `display:none`). AC4 asks to consolidate these into the `CSS` block where practical — **carefully**, preserving behavior (some are JS-toggled display states).
- **Page shell:** `web/genjson/index.html` (12 lines) — loads `genjson.js` with `defer` into `<div id="wizard-root">`. Add a `<meta name="theme-color">` if Direction B (dark) wants it; otherwise leave shell minimal.
- **Drawer reference** (the visual target to harmonize with): `web/maps-of-making.html` `:root` (lines 22–40), `.inline-link` (lines 330–333), `.bernard-voice` (line 328), `.url-fork` reveal easing (lines 335–337, a good model for the AC5 transient-intro / AC6 strip transitions: `grid-template-rows 0fr→1fr` + opacity, `cubic-bezier(.2,.8,.2,1)`).

### Hard constraints (do not violate)

- **Font canon (bernard-bible §4, locked 9.5):** Special Elite, self-hosted (`web/genjson/fonts/SpecialElite-Regular.woff2`, served from `'self'`), **single weight** → hierarchy via **size + color only**, never `font-weight`. `.bernard-voice` triplet is locked.
- **Copy is 9.5's domain, not this story's.** Do **not** edit string values; do **not** bypass `COPY.*` lookups. If a new visible label is unavoidable (AC6), add the key to `web/genjson/bernard_copy.yaml` and run `make bernard-copy` — never hardcode (would fail `test_bernard_voice_completeness` philosophy and break the SSOT, see Story 9.5 change log 2026-05-31).
- **CSP is `default-src 'self' 'unsafe-inline'`** (`infra/gateway-nginx/08-genjson-mapsofmaking.conf:49`). Inline `<style>`/`style=""` are allowed; **no CDN fonts/CSS/JS**, no external image hosts. Stay self-contained.
- **Behavior is frozen.** Geocode (`/api/geocode` debounce + manual fallback), localStorage draft/resume/clear, tier-0 gate (`updateContinueButton`/`updateExportButtons`), blur normalizers (`normalizeUrl`/`normalizeMatrix` + their hint feedback), validation warnings, and `exportJSON()` assembly all stay functionally identical. Only the **filename convention** in `exportJSON()` changes (AC6).

### UX spec mapping (what each principle demands here)

- **P1 ownership** → AC6 strip (live filename = your name on your file; always-export = you can walk).
- **P2 one-beat / kill-the-wall** → AC5 transient intro. (Full field-by-field reveal is **deferred** — see Out of Scope.)
- **P3 bedrock-only gate** → unchanged; the strip's progress marks bedrock as the one threshold (AC6).
- **P4 acknowledgment-not-congratulations / not-needy** → AC6 progress indicator never demands completion, never turns red.
- **P5 familiar bones** → AC1/AC2 keep inputs/buttons conventional; harmonize, don't reinvent.
- **P6 craft is the argument** → the whole story; sub-400ms feel, tasteful transitions, no gimmick.

### Filename derivation (AC6) — concrete

Reuse the existing `slugify()` (`genjson.js:378`). Strip filename + export name:
```
`${slugify(draft.space || 'space')}-${slugify(draft.city || 'somewhere')}-${new Date().toISOString().slice(0,10)}.json`
```
This **mirrors the seed-ID basis** (`scripts/seed_import.py:34` hashes `name|city`) but stays human-readable — a hash is wrong for a filename a person recognizes on disk. The date stamp is the Bernard maintenance-log touch (bernard-bible §3). Supersedes the current `slugify(name)`-only export name (`genjson.js:463`).

### Project Structure Notes

- Touch only: `web/genjson/genjson.js` (the `CSS` const + `render()` template strings + `exportJSON()` filename), and possibly `web/genjson/index.html` (theme-color) and `web/genjson/bernard_copy.yaml` (only if AC6 needs a new label → then `make bernard-copy`).
- **Do not** touch `web/maps-of-making.html` (drawer) — it's the reference, not in scope; its `.bernard-voice` and link treatment are already canonical (Story 9.5).
- Local iteration: serve `web/genjson/` (the `fetch('/bernard_copy.json')` and `fetch('/genjson/spaceapi-v15.schema.json')` need same-origin) — see Story 9.5 Isolation Notes; or via maps-nginx. Activate venv for pytest. Deploy via `make deploy-genjson` (runs `make bernard-copy` first).

### Previous Story Intelligence

- **9.3 (wizard core, done):** did the initial **contrast pass** (lighter surface/border/text + explicit placeholder color) — *this story finishes it* (AC7). 9.3 deferred "fine styling + tone" → tone went to 9.5, **visual is this story**. Operator-review was iterative, one change at a time. localStorage save/resume confirmed working — don't break it.
- **9.5 (voice/font, done):** locked Special Elite self-hosted + canonical `.bernard-voice` + the `COPY` lookup architecture + `bernard_copy.yaml` as the **only** SSOT (`bernard_copy.json` is gitignored, regenerated via `make bernard-copy`; `test_json_matches_yaml` guards drift). Operator tone-approved; two lines (`tier_2_exit`, `tier_3_exit`) flagged for later refinement when walked in the UX narrative — **not this story** (copy).
- **9.6 (Tier 2, ready-for-dev) — coordinate, do not collide:** 9.6 adds Tier 2 fields (`opening_hours`, `memberOf`, `mom:sdgs`) and likely wires the fork "Go deeper" door. This story owns the **frame** those fields will sit in. If 9.6 lands first, re-base the visual pass onto its DOM; if this lands first, 9.6 inherits the frame (the intent). Keep the `CSS` block additive and tier-agnostic so a new Tier 2 block styles itself.

### References

- [Source: `_bmad-output/planning-artifacts/ux-bernard-wizard-spec.md`] — locked principles P1–P6, §3 transient intro, §4 ownership strip (the authority for this story)
- [Source: `_bmad-output/planning-artifacts/epics.md#Story 9.12`] — scope sketch (palette/hierarchy/spacing/contrast/mobile/consistency)
- [Source: `_bmad-output/planning-artifacts/bernard-bible.md §4`] — typography canon (single-weight, hierarchy via size+color, em-dash)
- [Source: `web/genjson/genjson.js:67-285`] — the `CSS` const (all wizard styling)
- [Source: `web/genjson/genjson.js:378,463`] — `slugify()` and current export filename (AC6 target)
- [Source: `web/maps-of-making.html:22-40,328,330-337`] — drawer `:root` palette, `.bernard-voice`, `.inline-link`, `.url-fork` reveal easing (harmonization reference)
- [Source: `infra/gateway-nginx/08-genjson-mapsofmaking.conf:49`] — CSP `'self' 'unsafe-inline'` (no CDN)
- [Source: `memory/feedback_ui_iteration.md`] — operator reviews visually, one change at a time; dark tiles need `filter:none` not invert (relevant if Direction A inverts anything)

## Dev Agent Record

### Agent Model Used

_TBD by dev agent_

### World Aesthetic Decision (AC1)

**Direction B — locked by operator (Nicolas), 2026-05-31.** Dark "workshop interior" as a
**threshold** (border crossing between the MoM map and Mother Sands; the full lair is Epic 8 lore).
Base = **liminal dusk** (deep blue-green dark), not pitch fort-black. Palette grounded in Bernard's
hermit-crab vision (bernard-bible §1): amber/brass = voice + CTA, blue = links, green =
valid/confirmed, **red = errors only** (outside Bernard's spectrum), UV = sparing curiosity shimmer.
Exact hex values are an operator-visual call in Task 0 (direction is locked; hues are reviewed).

### Debug Log References

### Completion Notes List

### File List
