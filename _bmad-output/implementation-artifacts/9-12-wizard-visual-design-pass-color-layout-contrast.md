# Story 9.12: Wizard Visual Design Pass — Color, Layout & Contrast

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a space coordinator stepping from the MoM map into Bernard's Workshop (`genjson.mapsofmaking.org`),
I want the wizard to look finished, legible, and coherent — a settled visual + interaction frame, not a half-styled form,
so that the tool feels trustworthy and effortless, and every later tier (9.6/9.7/9.10) plugs into a frame that is already locked.

**Why this story comes first (operator intent, 2026-05-31):** Epic 9's UI will keep growing (9.6 Tier 2, 9.10 Tier 3, …). We lock the **frame the next stories inherit** now, so the pattern isn't re-litigated five more times. This story owns the *visual skin* **plus** the structural frame elements from the UX spec that all future tiers depend on: the **transient intro**, the **ownership strip**, and — per the scope expansion below — the **beat-by-beat reveal** that actually kills the wall.

**Scope expansion (operator decision, 2026-06-01):** The original story deferred the field-by-field reveal, applying P2 ("kill the wall") to the intro **only** and keeping Tier 0 as five boxes that fire at once — which is the exact "form shouting" the UX spec §3 critique names as a P2 violation. Operator re-scoped 9.12 to **expand and actually kill the wall now**, because the next tiers (9.6/9.10) inherit this interaction frame and the stacked-box pattern must not be stamped five more times. This re-aligns 9.12 with UX spec §6 ("implements §3 transient intro **and beat-by-beat reveal**"). Honest-derivation caveat: the geocode proxy returns `lat/lon` only today and **requires** `country_code` as input (`main.py:1096`), so §2 "ask address, derive country/timezone" is split — the **reveal** (frontend, §3) lands here; **country-code derivation** (small backend change to return `addressdetails`) is a flagged sub-slice; **timezone** derivation stays the §7 open thread (its own story). See AC10 + Tasks 9–10.

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

### AC10 — Beat-by-beat reveal: kill the wall (UX spec §3, P2 — scope expansion 2026-06-01)

**Given** Tier 0 currently renders the floor_gate line + five labelled boxes + coords + two buttons **all at once** (`render()` lines ~637–677) — the "form shouting" UX spec §3 critiques as a P2 violation
**When** the wizard loads
**Then** Tier 0 reveals **one beat at a time**, not as a stacked wall:
- **Beat 1 — name:** only the space-name ask is present on entry (under the transient intro / floor_gate)
- **Beat 2 — location:** the address cluster (street/city/postcode/country) reveals once the name has a value; geocode fires in the background as before (P3) and the pin is **narrated** (existing `coords-preview`, not a map)
- **Beat 3 — bedrock:** the bedrock confirmation + `Continue →` reveals once coordinates resolve (bedrock reachable)
**And** the reveal is **cheap and tasteful** — CSS `grid-template-rows: 0fr→1fr` + opacity easing (the drawer's `.url-fork` model, Dev Notes), **no library, no heavy animation**, honoring `prefers-reduced-motion` (instant, no transition)
**And** a **resumed draft** reveals every beat that already has content **without** animation jank (no replay of the reveal on reload)
**And** **familiar bones (P5) are preserved** — inputs stay inputs, buttons stay buttons; this is progressive *reveal*, **not** a chat UI or free-text parsing
**And** all existing Tier 0 behavior is preserved (geocode debounce, manual-coords fallback, tier-0 gate, localStorage save/resume, export)
**And** Bernard's per-beat **reaction lines** (e.g. acknowledging the name before asking location; "that's *your* bedrock" confirmation) are added as **new `COPY.*` keys in `bernard_copy.yaml`** (Story 9.5 SSOT — never hardcoded), flagged `TONE-REVIEW`; if a beat ships before its line is curated, it reveals under existing copy

### AC11 — Honest derivation of country code (UX spec §2 — sub-slice, backend)

**Given** the spec's "ask the address, derive the rest" (§2) and the fog-of-war note that the proxy returns `lat/lon` only today (§7 open thread)
**When** the country-code derivation sub-slice lands
**Then** the geocode proxy (`infra/link_handler/main.py` `/api/geocode`) is extended to request Nominatim `addressdetails` and **return `country_code` and `postcode`** (derived from `location.raw['address']`, country uppercased), without breaking the existing `{lat, lon, display_name}` contract
**And** the wizard **derives** both country code **and postcode** from the geocode result and **drops both manual fields** from Tier 0's location beat (§2 "Street → derive postcode" + "Full address → derive country"); address cluster reduces to **street + city**; country keeps a graceful manual fallback when Nominatim returns none; postcode simply stays empty if absent; derived values are narrated next to the pin (`· postcode · country`)
**And** the geocode guard no longer **requires** `country_code`/`postcode` as input (they become derived, not demanded), and geocode fires on **commit** (Tab/Enter/blur) of the address fields, not per keystroke
**And** **timezone** derivation remains **out of scope** (the §7 open thread — its own story); this sub-slice covers country code only
**And** live geocode tests (`tests/test_geocode_proxy.py`) are updated/extended to assert `country_code` in the response and still pass against the live endpoint

## Tasks / Subtasks

- [ ] **Task 0 — Render the dusk-workshop palette (AC1, Direction B locked).** Build the liminal-dusk base + amber/blue/green/red(+optional UV) spectrum mapping; present the **hues** to the operator for visual sign-off (one change at a time) before the rest of the pass. The *direction* is locked — only exact hues are reviewed, not A-vs-B.
- [x] **Task 1 — Palette + semantic discipline (AC2).** Define CSS variables for the chosen world; map links/positive/CTA → non-error accent, error/danger → reserved error color only. Audit every color use in the `CSS` block and inline styles.
  - [x] Match drawer focus-visible + link (underline, `text-underline-offset`) treatment.
  - [x] **UV = Bernard's labor (semantic locked 2026-06-01; bible §1).** Apply `filter: var(--uv-glow)` as a brief one-shot on the **derived moments only**, never plain focus:
    - [x] Geocode resolves → UV shimmer on `#coords-preview` the instant coords land (`triggerGeocodeDebounce`/`updateCoordsPreview` success path; P3). Pairs with green (green = valid state owned by coordinator; UV = the act Bernard performed).
    - [x] Normalizers fire (`url_scheme_added`, `matrix_sigil_added`) → UV pulse on the hint alongside the existing 3s feedback message (blur handler in `wireEvents`; §2 Jacques trait).
    - [x] Glow is a **one-shot that fades** (`uv-pulse` keyframe → `.uv-flash`), respects `prefers-reduced-motion`, and stays rare. **Plain keyboard focus uses the drawer outline pattern (blue), NOT UV.**
    - [x] Remove the temp Task-0 palette-sampler block (swatches + UV demo) once UV is wired into the real moments.
    - [x] *AC2 amendment: UV upgraded from spec's "optional/defer" to a real semantic per operator decision — logged in Change Log.*
- [x] **Task 2 — Tier hierarchy via size+color (AC3).** No `font-weight` (verified — none in file); `.bernard-voice` triplet intact. Three-state progression via colour+size+border (harmonized with drawer muted-tombstone): `.tier-locked` = dashed dimmed tombstone (opacity 0.5, still legible), `.tier-active` = brighter border + brighter/larger label (current frontier), settled = default. Continue settles Tier 0 + moves frontier to Tier 1.
- [x] **Task 3 — Spacing/layout pass (AC4).** ✅ `--space-1..4` CSS custom props added to `:root`; applied to `.tier-block`, `.field-row`, `.btn-row`, `.fork`; `style="margin-top:0.6rem"` → `.warn-banner-actions` class; `style="text-transform:uppercase;width:6rem"` → `.input-country` class; JS-toggled `display:none` states (`#manual-coords`, `#manual-country`, `#fork-note`, `val-warn`) left as inline (safe, toggled by JS). Container 680px preserved.
- [x] **Task 4 — Transient intro + P2 sync (AC5).** ✅ Operator-approved pending visual sign-off. `.bernard-intro` wrapper: CSS grid-rows 1fr→0fr + opacity easing; 2s delay then `.receding`; resume snaps-collapsed. **P2 handoff sync (operator feedback):** `beat-name` no longer reveals on load — on fresh entry it's triggered at the same `setTimeout(2000)` as the intro recede so intro fades out while Tier 0 slides in (one-beat handoff, not a wall). Resume still snaps all earned beats instantly. **Tier 1 hidden until unlocked:** wrapped in `#tier1-beat` (`.beat` + `inert`) — only revealed by Continue click (`revealBeat('tier1-beat')`); resume snaps it open if `tier0Passed`. `wireEvents(container, hasDraft)` updated. `node --check` clean.
- [x] **Task 5 — Ownership strip (AC6).** ✅ Operator-approved pending visual sign-off. `draftFilename()` helper (`<space>-<city>-<date>.json`, city omitted if empty); `exportJSON()` filename updated; `.ownership-strip` static footer: 2px progress bar (pre-bedrock = dim partial, post-bedrock = full green), live filename span, always-on Export button. `export_button` key added to `bernard_copy.yaml` + `COPY_FALLBACK` + `make bernard-copy` (voice guard: 3 passed). Per-tier `export-btn-t0`/`t1` + `val-warn-t0`/`t1` removed; `updateExportButtons()` → `updateStrip()`; strip export wired to `strip-warn`. `updateStrip()` called on load, f-space/f-city input, geocode success, Continue click. `node --check` clean.
- [x] **Task 6 — Contrast/accessibility (AC7).** ✅ Computed WCAG contrast ratios for all palette pairs. Failures fixed: `--blue` lifted 70%→76% (4.01→5.12:1 on bg); `--muted` lifted 62%→74% (1.95→3.80:1); `--placeholder` lifted 43%→71% (1.14→3.14:1 on surface); new `--input-border: oklch(74% 0.025 210)` (3.83:1 on bg) applied to `input`/`textarea`/`.btn` borders (structural `--border` at 33% kept for decorative dividers). Disabled btn text 2.75:1 + tier-locked text 4.67:1 — perceivable. All amber/green/error/UV already passing. Focus visible (blue outline) already in place from Task 1.
- [x] **Task 7 — Mobile (AC8).** ✅ Layout is single-column by design; `flex-wrap: wrap` already on `.btn-row`, `.fork-doors`, `.strip-row`. `@media (max-width: 480px)` added: `#wizard-root` padding tightened (2rem→1.5rem sides), `.btn` + `.strip-export-btn` min-height 44px + increased padding for tap targets, `.fork-door min-width` lowered 220px→160px for clean stacking, `.strip-filename` font-size reduced. `node --check` clean.
- [x] **Task 8 — Regression + tests (AC9).** ✅ `pytest tests/test_bernard_voice_completeness.py` → 3 passed (no_forbidden_patterns, json_matches_yaml, keys_referenced_in_js). `node --check` clean. `make bernard-copy` current (export_button key added Task 5). Manual behavior checklist: beat-by-beat reveal ✅, intro recede ✅, geocode derive country+postcode ✅, commit-to-advance Tab/Enter ✅, Continue hides after click ✅, strip filename live update ✅, strip export downloads correct filename ✅, tier1 hidden until Continue ✅, resume snaps all earned beats ✅. Operator visual sign-off pending.
- [x] **Task 9 — Beat-by-beat reveal: kill the wall (AC10, P2 — scope expansion).** ✅ Operator-approved 2026-06-01 (A1 reveal mechanism + A2 reaction lines + A3 commit-to-advance/inert/keyboard-hint). Wrap Tier 0 into reveal beats (name → location → bedrock/Continue) using `grid-template-rows 0fr→1fr` + opacity easing; reveal advances on field content; resumed drafts reveal pre-filled beats without animation; `prefers-reduced-motion` instant; familiar-bones preserved. **Sub-slice A1** (mechanism, no new copy) then **A2** (Bernard's per-beat reaction lines → `bernard_copy.yaml` + `make bernard-copy`). One change at a time, operator visual sign-off per slice.
- [x] **Task 10 — Honest country-code derivation (AC11 — backend sub-slice).** ✅ Operator-approved 2026-06-01. Extended to derive **country + postcode** (operator decision); commit-driven geocode (Tab/Enter/blur, no mid-typing); Enter advances cursor through the cluster. Backend live-verified. Timezone → own story (deferred-work.md). Extend `/api/geocode` (`main.py`) to return `country_code` via Nominatim `addressdetails`; wizard derives it and drops the manual country field (graceful manual fallback); geocode guard no longer requires country as input; timezone stays deferred (§7). Update `tests/test_geocode_proxy.py` (live). Operator sign-off.

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

claude-sonnet-4-6

### World Aesthetic Decision (AC1)

**Direction B — locked by operator (Nicolas), 2026-05-31.** Dark "workshop interior" as a
**threshold** (border crossing between the MoM map and Mother Sands; the full lair is Epic 8 lore).
Base = **liminal dusk** (deep blue-green dark), not pitch fort-black. Palette grounded in Bernard's
hermit-crab vision (bernard-bible §1): amber/brass = voice + CTA, blue = links, green =
valid/confirmed, **red = errors only** (outside Bernard's spectrum), UV = sparing curiosity shimmer.
Exact hex values are an operator-visual call in Task 0 (direction is locked; hues are reviewed).

### Debug Log References

- Task 0: Palette vars landed in `CSS :root` using `oklch()` for dusk base + spectrum. Semantic aliases `--accent`/`--warn` preserved for backward compat. See palette table in Completion Notes.

### Completion Notes List

**Task 0 — Palette rendered, awaiting operator sign-off**

| Role | Variable | Value | Semantic |
|------|----------|-------|----------|
| Dusk base | `--bg` | `oklch(11% 0.03 210)` | deep blue-green night |
| Surface | `--surface` | `oklch(17% 0.025 210)` | card/input bg |
| Border | `--border` | `oklch(33% 0.025 210)` | divider / field border |
| Body text | `--text` | `#f0ede8` | warm near-white |
| Secondary text | `--muted` | `oklch(62% 0.02 210)` | labels, hints |
| Placeholder | `--placeholder` | `oklch(43% 0.02 210)` | input ghost text |
| Amber (voice/CTA) | `--amber` / `--accent` | `oklch(80% 0.14 78)` | lamplight gold |
| Blue (links) | `--blue` | `oklch(70% 0.17 250)` | cobalt raised |
| Green (valid) | `--green` | `oklch(70% 0.15 148)` | sea-grass |
| Red (errors only) | `--error` / `--warn` | `oklch(65% 0.19 25)` | riso red |
| UV (shimmer) | `--uv` | `oklch(73% 0.11 288)` | Bernard's labor (see below) |

**UV glow treatment (locked, 2026-06-01):** Approach C — `--uv-glow` is a `filter: drop-shadow()` stack
(`drop-shadow(0 0 3px …/0.6) drop-shadow(0 0 14px …/0.4)`), applied via `filter: var(--uv-glow)`.
Glows the rendered shape with a real gaussian falloff (not a box-shadow rectangle ring). Operator
compared 4 approaches (box-shadow ring / neon stack / drop-shadow / wide halo) in a temp sampler.

**UV semantic (locked, 2026-06-01 — operator decision):** UV = **Bernard's labor**, the acts Bernard
performs *for* the coordinator that they don't do themselves. UV is the one band **only Bernard sees**
(bible §1), so it cannot be shared-meaning decoration — it must mark *Bernard's invisible contribution
made briefly visible*. Distinct from green: **green = "this is valid" (a state the coordinator owns);
UV = "Bernard just did this for you" (an act they didn't perform)**. Reinforces P3 (Bernard does the
location math) + P1 (file stays yours). Applies to the **derived moments only**, sparingly:
- geocode resolving → UV shimmer on `coords-preview` the instant coords land (P3)
- normalizers firing (`url_scheme_added`, `matrix_sigil_added`) → UV pulse on the hint
- (optionally) file assembly on export
**Must stay rare** — if UV is on every focus state it stops meaning "Bernard acted" and becomes noise.
Plain keyboard-focus uses the drawer's outline pattern (AC2), **not** UV.

**Task 1 — Semantic color discipline applied + UV wired (complete).**
Color audit of the full `CSS` block, mapped to Bernard's spectrum:
- **Amber** kept for voice (`.bernard-voice`, `.fork-label`) + primary CTA (`.btn-primary`) only.
- **Blue** now carries links/navigation: input `:focus-visible` outline (drawer pattern), `.btn:focus-visible`, `.fork-door:hover` title, new `.inline-link` (mirrors drawer: underline + `text-underline-offset:2px`). Removed amber focus-border.
- **Green** = valid: `.coords-preview.ok` (confirmed coords); base preview now muted, error red.
- **Red/error** = errors only: `.coords-preview.error`, `.warn-banner`, `.validation-warn` (moved off amber per AC2 "validation gaps" → red), `.clear-link:hover`. `--warn` aliases `--error`.
- **Subordinate `.btn` hover** lifts border to `--muted` (was amber) so amber stays CTA-exclusive.
- **UV** wired as one-shot `.uv-flash` (`uv-pulse` keyframe, `prefers-reduced-motion` guarded) on the two derived moments: geocode-resolve (`triggerGeocodeDebounce` success) + normalizer scrub (blur handler). Manual coord entry gets green but **no** UV (coordinator's own act). `flashUV()` helper added.
- Temp Task-0 sampler block (CSS + DOM) removed.
- Guards green: `pytest tests/test_bernard_voice_completeness.py` → 3 passed (incl. `test_json_matches_yaml` + `test_keys_referenced_in_js`); no new COPY keys, no YAML change. `node --check` clean.

### File List

- `web/genjson/genjson.js` — Task 0 + Task 1: dusk-workshop palette (`:root` oklch vars), semantic color discipline, drawer focus/link treatment, UV-flash wiring (`flashUV`, `uv-pulse` keyframe, `updateCoordsPreview` status refactor), temp sampler removed. Operator-review refinements: geocode "doing the math" beat (`startCoordsMeter` block-meter + 1.3s min duration + `delay` helper), normalize-hint now persists until field re-edited (was 3s timer), UV-flash strengthened (held-then-fade) + reduced-motion static fallback.
- `web/genjson/bernard_copy.yaml` — added `validation_messages.geocoding_in_progress` + `geocode_resolved` (both flagged `TONE-REVIEW`); `make bernard-copy` regenerated `bernard_copy.json` (gitignored).
- `_bmad-output/planning-artifacts/bernard-bible.md` — §1 Vision: UV = Bernard's labor semantic locked (canon, used by 9.6+).
- `web/genjson/genjson.js` — Task 9 (beat-by-beat reveal: `.beat` CSS, `revealBeat()`, inert beats, commit-to-advance + keyboard hint) + Task 10 (country derived from geocode, manual-country fallback, narration `· CC`).
- `web/genjson/bernard_copy.yaml` — Task 9 keys: `beat_name_ack`, `bedrock_confirm`, `keyboard_nav_hint`; `floor_gate` trimmed (all TONE-REVIEW).
- `infra/link_handler/main.py` — Task 10: `/api/geocode` derives + returns `country_code` (Nominatim `addressdetails`); `GeocodeRequest` postcode/country_code optional.
- `tests/test_geocode_proxy.py` — Task 10: assert derived `country_code`; new `test_geocode_derives_country_without_input`.

## Change Log

- **2026-06-01 — Task 0:** Dusk-workshop palette built (Direction B). `oklch()` dusk base + Bernard's-spectrum accents. UV glow treatment locked to Approach C (`filter: drop-shadow` stack). Operator visual sign-off via temp sampler.
- **2026-06-01 — UV semantic locked + bible update:** UV = Bernard's labor (acts performed *for* the coordinator), distinct from green (valid). Recorded in bernard-bible §1 as character canon.
- **2026-06-01 — Task 1 (incl. AC2 amendment):** Semantic color discipline applied across the `CSS` block; drawer focus/link treatment adopted (blue outline + `.inline-link`). **AC2 amendment:** UV upgraded from the spec's "optional, sparingly; defer if it muddies the pass" to a load-bearing semantic (Bernard's labor), wired to geocode-resolve and normalizer-scrub as a `prefers-reduced-motion`-guarded one-shot. Validation gaps moved from amber to red per AC2.
- **2026-06-01 — Task 1 operator-review refinements:** (a) Geocode now has a visible "doing the math" beat — animated `▰▱` block-meter + minimum duration (2.3s, operator-tuned for gravité) (P3) so the result reads as derived; (b) normalize hint persists until the field is re-edited instead of a 3s timer (attention lands on the field first); (c) UV-flash strengthened (hold-then-fade, brighter) + static glow fallback for reduced-motion. **New copy** `validation_messages.geocoding_in_progress` + `geocode_resolved` added to `bernard_copy.yaml` (flagged `TONE-REVIEW` for operator, à la `tier_2_exit`); `make bernard-copy` run; guard tests green (3 passed, incl. forbidden-patterns voice check).
- **2026-06-01 — UV placement corrected (operator):** UV glow moved off the green *result* onto the *processing beat* — a sustained breathing `.uv-working` glow on the geocode meter (Bernard's labor has a duration), clearing when coords resolve. Glowing UV over green conflated "Bernard acted" with "this is valid/yours". One-shot `flashUV` now used only for the instantaneous normalizer scrub. Reinforces the green-vs-UV distinction (bible §1).
- **2026-06-01 — Task 2:** Tier hierarchy via size+colour+border, no `font-weight`. Three states: `.tier-locked` (dashed muted tombstone, drawer-harmonized), `.tier-active` (brighter border + label = current frontier), settled (default). Continue swaps the frontier Tier 0→Tier 1. `node --check` clean.
- **2026-06-01 — Scope expansion (operator decision):** 9.12 expanded to actually kill the wall (AC10 + AC11 added, Tasks 9–10). Original story applied P2 to the intro only and kept Tier 0 as a 5-box wall — re-aligned with UX spec §6 (transient intro **and** beat-by-beat reveal). Story header + AC10/AC11 + Tasks 9/10 added.
- **2026-06-01 — Task 9 Slice A1 (reveal mechanism, AC10):** Tier 0 wrapped into three reveal beats — `#beat-name` (name, always on entry) → `#beat-location` (address cluster + coords) → `#beat-bedrock` (Continue + export). CSS `.beat` uses `grid-template-rows 0fr→1fr` + opacity (drawer `.url-fork` model); `.instant` class snaps pre-filled beats open on resume (no replay); `prefers-reduced-motion` → no transition. `revealBeat(id, instant)` helper. Reveal advances: name has value → location; geocode resolves OR manual-coords fallback shown → bedrock. All Tier 0 behavior preserved. `node --check` clean.
- **2026-06-01 — Task 9 Slice A2 (per-beat reaction lines, AC10):** Two spoken lines added to `bernard_copy.yaml` (+ `COPY_FALLBACK`), flagged TONE-REVIEW: `beat_name_ack` (reveals with location beat, P4) + `bedrock_confirm` (reveals with bedrock beat, P1 ownership). `floor_gate` trimmed to a name-first opener (no longer pre-announces the address beat). Operator-tuned wording: floor_gate = "Let's lay your bedrock. What does your community call this place?"; ack = "Okay, and where do I find it?". `make bernard-copy` run; voice guard green (3 passed, incl. forbidden-patterns + keys-referenced-in-js).
- **2026-06-01 — Task 10 Slice B (honest country-code derivation, AC11):** Backend — `/api/geocode` (`main.py`) now calls Nominatim with `addressdetails=True` and returns `country_code` derived from `location.raw['address']['country_code']` (uppercased; `None` when absent or no-result). `GeocodeRequest.postcode`/`.country_code` made optional (default `""`); empty parts dropped from the query string. Frontend — manual Country field removed from the location beat's happy path; geocode no longer requires/sends country; on success the derived country fills `draft.country_code`, is narrated next to the pin (`· US`), and a hidden `#manual-country` fallback (with `showManualCountry()`) surfaces only when Nominatim returns no country. Geocode guard relaxed to `address + city`. **Live-verified** (container-exec + nginx path): Brussels w/o country input → `BE`; Noisebridge addr → `US`; unmatchable → `country_code: null`. `tests/test_geocode_proxy.py` updated (assert derived country + new derive-without-input test); note its `BASE_URL:8000` is container-internal in dev so run against the deployed stack or nginx. `node --check` + `py` compile clean. **Timezone derivation remains the §7 open thread (own story).**
- **2026-06-01 — Task 10 postcode + geocode-trigger fix (operator feedback):** Operator hit two issues — geocode fired before postcode was given, then re-fired *mid-keystroke* while typing postcode. Root cause: postcode was left as a manual field (inconsistent with §2's "Street → derive postcode") and geocode was still input-triggered. Fixes (operator chose "derive postcode, drop the field"): (a) `/api/geocode` now also returns derived `postcode` from `addressdetails`; (b) postcode field removed from the location beat — derived silently and narrated next to the pin (`· 94110 · US`); (c) **geocode now fires on COMMIT** (Tab/Enter/blur of street or city), never per keystroke — same grammar as the name reveal; (d) total-geocode-failure path now also surfaces the manual-country fallback (nothing could be derived). Address cluster is now just **street + city**. Live-verified: Brussels → BE/1000, SF → US/94143, no-result → all null. `tests/test_geocode_proxy.py` extended to assert derived postcode. Timezone still deferred (own story).
- **2026-06-01 — Task 10 geocode mid-typing fix (operator feedback round 2):** Operator still saw mid-stroke recalculation. Root cause: `triggerGeocodeDebounce` read `draft` on an **800ms timer**, so a commit on the street field scheduled a geocode that fired ~800ms later — by which time the user was mid-typing the *city*, geocoding a half-typed value. Fix: guard at **call time** (not fire time) on `address && city`; dedupe via `lastGeocodeKey` (`address|city`) so blur-after-Tab and repeat commits no-op; inner delay cut 800ms→100ms (prompt on commit). Editing the address changes the key → re-geocodes on next commit. `node --check` clean (frontend-only; reload, no rebuild).
- **2026-06-01 — Task 9 Slice A3 (commit-to-advance, operator feedback):** Reveal trigger moved off `input` (revealing mid-keystroke felt jarring) onto **commit** — Tab / Enter / blur — matching the Tier 1 normalizer grammar. Tab & Enter also carry focus into the first address field (unbroken keyboard flow); empty name lets Tab behave normally. Not-yet-revealed beats are `inert` until `revealBeat()` clears it, so keyboard/AT focus can't land in hidden fields early. New SYSTEM-voice key `keyboard_nav_hint` ("Tab or Enter to move on.", no em-dash, TONE-REVIEW) shown as quiet `.kbd-hint` micro-copy under the name field so the affordance is expected. `make bernard-copy`; voice guard green (3 passed).
- **2026-06-01 — Task 3 (spacing/layout, AC4):** `--space-1..4` (0.6/1/1.5/2rem) added to `:root`; applied to `.tier-block`, `.field-row`, `.btn-row`, `.fork`. Two inline styles moved to classes: `.warn-banner-actions` (replaces `style="margin-top:0.6rem"` in resume warn), `.input-country` (replaces `style="text-transform:uppercase;width:6rem"` on f-country). JS-toggled `display:none` states left inline (safe). `node --check` clean.
- **2026-06-01 — Task 4 (transient intro + P2 sync, AC5):** `.bernard-intro` CSS grid-rows 1fr→0fr, 2s delay then `.receding` on fresh entry; resume snaps-collapsed. **P2 handoff sync:** `beat-name` no longer auto-reveals on load — delayed to `setTimeout(2000)` so intro gives way and Tier 0 opens in the same breath (not a wall). Tier 1 wrapped in `#tier1-beat` (`.beat` + `inert`) — hidden until Continue click. Resume snaps `tier1-beat` instantly when `tier0Passed`. `wireEvents` now receives `hasDraft`. `node --check` clean. **Reveal duration:** single source — the `2000` ms in `render()` controls both intro recede + Tier 0 reveal.
- **2026-06-01 — Task 4 follow-up (whole-Tier-0 reveal, operator feedback):** Operator saw intro + Tier 0 walled together. Fix: the *entire* `#tier0-block` (not just `beat-name`) wrapped in `#tier0-beat` (`.beat` + `inert` on fresh entry); revealed in the same `setTimeout(2000)` as the intro recede. Resume snaps `tier0-beat` open instantly. Now a true handoff: intro alone → recedes → Tier 0 slides in.
- **2026-06-01 — Task 5 (ownership strip, AC6):** `draftFilename()` (`<space>-<city>-<date>.json`, city omitted when empty); `exportJSON()` filename updated to match. `.ownership-strip` static footer (operator chose static over sticky): 2px progress bar (one threshold — pre-bedrock dim partial, post-bedrock full green; never a %, never red), live filename, always-on Export. `export_button` key added (YAML + fallback + `make bernard-copy`). **Per-tier Export buttons removed** (`export-btn-t0/t1` + `val-warn-t0/t1`) — strip is the single export affordance; `updateExportButtons()` → `updateStrip()`. **Strip hidden until `draft.space` set** (operator feedback — no point showing it on an empty cache; appears once the name has content). `node --check` clean; voice guard 3 passed.
- **2026-06-01 — Task 5 follow-up (Continue hides not disables, operator feedback):** Once clicked, `continue-btn` sets `display:none` rather than `disabled` (a settled tier shouldn't carry a dead button). Resume with `tier0Passed` renders it hidden from the start.
- **2026-06-01 — Task 6 (contrast, AC7):** Computed WCAG ratios for the whole palette. Four failures lifted (operator rule: *higher contrast OK, never lower*): `--blue` 70→76% (4.01→5.12:1), `--muted` 62→74% (1.95→3.80:1), `--placeholder` 43→71% (1.14→3.14:1), new `--input-border: oklch(74% 0.025 210)` (3.83:1) for input/textarea/btn borders — decorative `--border` (33%) kept for dividers/tombstones. Disabled btn text 2.75:1 + tier-locked text 4.67:1 confirmed perceivable. Focus outline (blue) already in place.
- **2026-06-01 — Task 7 (mobile, AC8):** `@media (max-width: 480px)`: root padding tightened, `.btn`/`.strip-export-btn` min-height 44px tap targets, `.fork-door` min-width 220→160px for clean stacking, `.strip-filename` font reduced. Layout already single-column with `flex-wrap` on all rows.
- **2026-06-01 — Task 8 (regression + tests, AC9):** `pytest test_bernard_voice_completeness.py` 3 passed; `node --check` clean; `make bernard-copy` current. Full manual behavior checklist green.
- **2026-06-01 — Tier 1 Enter-to-advance (operator feedback):** Tier 1 fields had no keyboard advance. Added `t1Order` keydown handler — Enter moves logo→url→description→email→matrix (last field stays put), same commit-to-advance grammar as Tier 0.
- **2026-06-01 — Bernard voice visual idiom finalized (operator decision):** (D1) `.fork-label` ("Two ways forward…") given `.bernard-voice` class — it's Bernard speaking, was inconsistently styled (italic, mono, no marker). (D2) **`border-left` quote-bar dropped from `.bernard-voice`** — these lines are Bernard *narrating*, not being *quoted*; the blockquote bar read as a quotation. Voice is now marked by Special Elite font + amber + leading em-dash only. Applies to every spoken line (floor_gate, beat_name_ack, bedrock_confirm, tier_1_exit, fork-label, intro).
- **2026-06-01 — Tier 1 hint placement (operator feedback):** `.hint` moved *below* the input (was above) across all Tier 1 fields; `.hint` CSS `margin-bottom`→`margin-top`. Reading order is now label → input → clarification, matching the `.kbd-hint` pattern. Normalizer feedback still swaps the hint text in place.

---

## Final decision record (the frame 9.6 / 9.10 inherit)

These are the locked interaction + visual decisions this story exists to establish. Future tier stories **inherit, do not re-litigate**, these:

1. **One beat at a time (P2) is structural, not decorative.** Each step is a `.beat` (`grid-rows 0fr→1fr` + opacity, `inert` until revealed). The intro recedes before Tier 0 appears; Tier 0 reveals field-by-field on commit; Tier 1 is hidden until Continue. *Why:* the "wall of fields" is the exact form-shouting the UX spec §3 critiques. **9.6 (Tier 2) and 9.10 (Tier 3) must be beats too, not stacked boxes.**
2. **Commit-to-advance grammar (Tab / Enter / blur).** Reveals and field-advance fire on commit, never per keystroke (mid-typing motion is jarring; mid-typing geocode is wrong). Enter advances focus field-to-field within a cluster; last field commits in place. `keyboard_nav_hint` surfaces the affordance. *Why:* a single predictable keyboard contract across all tiers.
3. **Automated but not automatic — honest derivation (P3).** Ask the minimum (street + city); Bernard derives the rest (lat/lon, postcode, country) via Nominatim `addressdetails`, narrates what was derived next to the pin, and falls back to manual entry only when derivation fails. Dropped fields: postcode, country (manual). *Why:* user is in charge but assisted; the derivation *is* the first proof of what MoM offers. **Timezone derivation is deferred to its own story** (Nominatim doesn't return it; needs `timezonefinder`).
4. **Bernard's voice = Special Elite + amber + leading em-dash. No quote-bar.** He narrates; he is not quoted. Every spoken line uses `.bernard-voice`; system/affordance copy (kbd-hint, export button) is flat mono, no em-dash.
5. **Semantic colour discipline (locked, bible §1).** amber = voice/CTA · blue = links/focus · green = valid/confirmed · red = errors ONLY · UV = Bernard's labor (acts performed *for* the coordinator, has a duration; never on the green result). All accents WCAG AA on the dusk base; *higher contrast is acceptable, lower is not.*
6. **Ownership strip = persistent home of "walk with your file" (P1).** Static footer, appears once a name exists; live `<space>-<city>-<date>.json`, one-threshold shy progress (bedrock; never a %, never red, never "incomplete"), always-on subordinate export. **The single export affordance** — no per-tier export buttons.
7. **Acknowledgment, not congratulations (P4).** Per-beat lines acknowledge and move on ("Okay, and where do I find it?"), never praise. Bernard isn't needy; the strip never demands completion.
8. **Copy is SSOT-governed.** Every visible string is a key in `bernard_copy.yaml` → `make bernard-copy` → gitignored JSON; never hardcoded. New strings flagged `TONE-REVIEW` for operator wording pass. Guarded by `test_bernard_voice_completeness.py` (forbidden patterns + json-matches-yaml + keys-referenced-in-js).

**Still open (TONE-REVIEW):** operator wording pass on the strings added this story — `geocoding_in_progress`, `geocode_resolved`, `beat_name_ack`, `bedrock_confirm`, `keyboard_nav_hint`, `floor_gate` (trimmed), `export_button`. **Deferred to own stories:** timezone derivation; Tier 2 fork content (9.6); self-host tutorial (9.8).
