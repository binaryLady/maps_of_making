# Story 9.8: GitLab Tutorial Surface — Embedded Guide + Raw URL Handoff to Register Flow

Status: review

## Story

As a space coordinator who has exported their JSON file but has no hosting,
I want a compact 4-step tutorial showing me how to put my file on GitLab and get a raw URL,
So that I can register as an advanced user and appear on the MoM map without needing to ask anyone for help.

## Acceptance Criteria

### AC1 — "Go live →" fork door wires to an expanded tutorial section

**Given** the coordinator has passed Tier 0 and Tier 1 is visible (fork rendered per existing `render()`)
**When** the coordinator clicks `#fork-live` ("Go live →")
**Then** the `#fork-note` stub behaviour is replaced: instead of showing the `tutorial_teaser` line, the click **reveals the `#golive` section** (the tutorial wrapper, already in the DOM, hidden by default) via `revealBeat('golive')` — the same reveal grammar used throughout the wizard
**And** the `#fork-live` button becomes visually settled (non-active state, no hover highlight) once the section is open — it acts as a toggle-open, not a repeated trigger
**And** on second click (section already open) nothing changes — it is open-only, no collapse needed

### AC2 — Tutorial is beat-by-beat narration, not a static wall (UX spec §P2)

**Given** UX spec §P2 ("one beat at a time; kill the wall") governs every wizard surface, and the tutorial narrates an **external** process (GitLab actions the coordinator performs in another tab)
**When** `#golive` is revealed
**Then** the four steps reveal **one beat at a time**, never all at once — each step is a `.beat` using the same `grid-template-rows 0fr→1fr` + opacity + `inert`-until-revealed pattern as Tier 0 (9.12 BUILT grammar)
**And** only the first beat (`#golive-beat-account`) is visible when the section first opens; later beats are present-but-`inert` until advanced to
**And** because there is no field to commit (the action happens in GitLab, not the wizard), each beat carries a manual **advance affordance** — a `<button class="btn beat-next">` rendered with `COPY.tutorial.next` ("Done →") — clicking it settles the current beat and reveals the next (P5 familiar bones: a button stays a button)
**And** between beats Bernard **reacts** before the next reveals (P2: "Bernard reacts to the prior answer before the next reveals") — the reaction is the opening of the next beat's line, in Bernard's register, acknowledging the step just completed without congratulating (P4)

The five beats inside `#golive`, each a `.beat` (IDs per the `<section>-beat-<leaf>` taxonomy) with a `.bernard-voice` line (em-dash prepended by JS), a screencap, and a "Done →" advance button (except the terminal step):

**`#golive-beat-account` — Create a GitLab account**
- Line: `COPY.tutorial.step1`
- Screencap: `<img src="tuto/step1-account.png" alt="GitLab sign-up screen" loading="lazy">`
- Advance: `COPY.tutorial.next` button → `revealBeat('golive-beat-project')`

**`#golive-beat-project` — Create a public project**
- Line: `COPY.tutorial.step2`
- Screencap: `<img src="tuto/step2-project.png" alt="GitLab create blank project with Public visibility" loading="lazy">`
- Advance: `COPY.tutorial.next` button → `revealBeat('golive-beat-upload')`

**`#golive-beat-upload` — Upload your JSON file**
- Line: `COPY.tutorial.step3`
- Screencap: `<img src="tuto/step3-upload.png" alt="GitLab upload file dialog with Commit changes" loading="lazy">`
- Advance: `COPY.tutorial.next` button → `revealBeat('golive-beat-rawurl')`

**`#golive-beat-rawurl` — Copy the raw URL**
- Line: `COPY.tutorial.step4`
- Screencap: `<img src="tuto/step4-raw.png" alt="GitLab file view with Open raw button highlighted" loading="lazy">`
- Advance: `COPY.tutorial.next` button → `revealBeat('golive-beat-endpoint')` (the close)

**`#golive-beat-endpoint` — The hero's return** (see AC3)
- Two `.bernard-voice` lines: `COPY.tutorial.endpoint_bridge` then `COPY.tutorial.closing`
- No screencap, no advance button — this is terminal

**And** the system-voice intro line `COPY.tutorial.trigger` (no em-dash, no `.bernard-voice`) renders once inside `#golive` above `#golive-beat-account` — it sets context before the first beat
**And** only `#golive-beat-account` is visible when `#golive` first reveals; the rest are present-but-`inert` until advanced to
**And** each `<img>` has `max-width: 100%` (no overflow on mobile)
**And** `prefers-reduced-motion` is honored — reveals are instant when set (same as 9.12)

### AC3 — Closing beat: the hero returns knowing what an endpoint is (UX spec §P6 Peak-End)

**Given** UX spec §P6 marks the 9.8 go-live as "the payoff the whole flow points at" (Peak-End), and the coordinator entered the workshop via the drawer's "tell me about your space" path
**When** `#golive-beat-rawurl` settles (the coordinator has copied their raw URL and clicked "Done →")
**Then** `#golive-beat-endpoint` reveals as the terminal beat with two `.bernard-voice` lines (em-dash prepended by JS):
  1. `COPY.tutorial.endpoint_bridge` — names what they now hold: "That URL is your endpoint…"
  2. `COPY.tutorial.closing` — points them back to the map's second path by its literal drawer text: *"That 'paste your endpoint URL' line back on the map? It's for you now."*
**And** there is no input field, no URL collection, and no JS navigation — the coordinator returns to the map themselves
**And** this is the engineered end (Peak-End): they arrived via "tell me about your space" and leave as an advanced user who knows what a JSON file and an endpoint are, and how to self-host — the closing **witnesses** that crossing without congratulating (P4), trusting they know the way back (no map-of-doors, no escape-game cryptics — reduce cognitive load)

### AC4 — New `bernard_copy.yaml` keys (SSOT — never hardcode)

**Given** Story 9.5 SSOT rule: all visible strings are keyed in `bernard_copy.yaml`, not hardcoded in JS
**When** Story 9.8 lands
**Then** these keys are added to `bernard_copy.yaml` under a top-level `tutorial:` namespace:

```yaml
tutorial:
  # trigger = system voice (no em-dash), sets context above #golive-beat-account
  trigger: "You've got the file. Now it needs an address. GitLab will give you one, free, permanently, in about five minutes. No credit card. No server. No command line."
  # step1..4 = Bernard spoken (em-dash prepended). Beats 2-4 OPEN with a terse
  # reaction to the step just completed (P4 acknowledgment, never congratulation),
  # then state the next action — this is the "Bernard reacts before the next reveals" beat seam.
  step1: "Create a free account at gitlab.com. Email or SSO — your call. Verify your address when they ask."
  step2: "Account's yours. Now a place to put the file: New project → Create blank project. Set it Public — the map has to read it without a login. Any name will do."
  step3: "Project's up. The + button → Upload file. Drop in the JSON you exported. Commit changes."
  step4: "It's hosted. Open the file, top-right: Open raw. Copy that URL from your browser."
  endpoint_bridge: "That URL is your endpoint. It's the address where the map finds your file. When anything asks for your endpoint URL, that's the one."
  closing: "That 'paste your endpoint URL' line back on the map? It's for you now."
  next: "Done →"   # advance affordance — system voice, no em-dash
```

**Beat-seam rationale:** Each of `step2`/`step3`/`step4` opens by naming the completed state ("Account's yours.", "Project's up.", "It's hosted.") — this is Bernard *reacting* to the prior beat before stating the next action, satisfying §P2's "reacts before the next reveals" and §P4 acknowledgment-not-congratulation. `step1` has no opener (nothing precedes it).

**And** `COPY_FALLBACK` in `genjson.js` is updated to include a matching `tutorial` object with the same keys (minimal inline fallback — same AC2 pattern as Story 9.5)
**And** `make bernard-copy` is run to regenerate `bernard_copy.json`
**And** `pytest tests/test_bernard_voice_completeness.py` passes (3 tests: no_forbidden_patterns, json_matches_yaml, keys_referenced_in_js)

### AC5 — Screencap assets: source from `docs/gitlab_tuto/`, commit to `web/genjson/tuto/`

**Given** Nicolas has captured screencaps and produced `docs/gitlab_tuto/V2_Hosting_Your_Space.png` as a 6-panel reference guide plus individual screencaps
**When** Story 9.8 assets are placed
**Then** four named PNG files are committed to `web/genjson/tuto/`:

| Asset file | Source screencap | Content |
|---|---|---|
| `step1-account.png` | `screencap_0601_165023.png` | GitLab sign-in/register screen |
| `step2-project.png` | `screencap_0601_165341.png` or `165500.png` | Create blank project with Public visibility selected |
| `step3-upload.png` | `screencap_0601_170836.png` | Commit changes dialog with JSON file |
| `step4-raw.png` | `screencap_0601_171102.png` | File view with Open raw highlighted |

**And** each image is scaled/cropped to show only the relevant UI action (not the full viewport) — max width ~600px, PNG
**And** `web/genjson/tuto/` is served statically by the existing nginx config (no config change needed — it falls under the genjson location block's `try_files` → nginx already serves all files under the root)

### AC6 — Tutorial styling inherits the 9.12 dusk-workshop frame

**Given** the 9.12 locked frame (Direction B dusk palette, semantic colour discipline, `.bernard-voice` triplet, spacing scale `--space-1..4`, AC2 colour rules)
**When** the tutorial section is styled
**Then** each `.beat` uses `--space-3` top spacing and a left border in `--border` color as a subtle step separator
**And** optional step numbers (if shown) render in `--muted` color, Special Elite, `font-size: 14px` (subordinate to Bernard's spoken lines)
**And** screencap `<img>` elements have `border-radius: 2px; border: 1px solid var(--border); max-width: 100%; margin-top: var(--space-2)`
**And** the "Done →" advance button (`.beat-next`) uses the existing `.btn` class — but in a **subordinate** style (not the amber primary CTA): it is an in-flow stepper, not the page's main action; blue (`--blue`, navigation) or a quiet outline is appropriate, never error-red
**And** the closing beat (`#golive-beat-endpoint`) renders its two Bernard lines (`endpoint_bridge`, `closing`) in `.bernard-voice` with `--space-3` top spacing separating it from `#golive-beat-rawurl`
**And** the tutorial collects no data — only "Done →" steppers; no input field, no submit/CTA button
**And** no `font-weight` rules are added (Special Elite is single-weight — hierarchy via size + color only, per bernard-bible §4)

### AC7 — Mobile: tutorial usable at ≤ 480px

**Given** the wizard is already mobile-responsive (Story 2.6, AC8 of 9.12)
**When** `#golive` is viewed at ≤ 480px
**Then** beats stack vertically, screencaps fill the container width (`max-width: 100%`), and each "Done →" advance button has a min-height 44px tap target (reuses the existing `@media (max-width: 480px)` block from Task 7 of 9.12)

### AC8 — Regression: existing wizard behavior untouched

**Given** Stories 9.3, 9.5, 9.12 established: geocode debounce, localStorage draft/resume/clear, tier-0 gate, blur normalizers, export, beat-by-beat reveal, ownership strip, COPY lookups
**When** Story 9.8 lands
**Then** all existing behavior is preserved — this story adds one new beat-by-beat section under the "Go live →" fork door and the `tutorial.*` COPY keys; it does not touch any existing logic
**And** `node --check web/genjson/genjson.js` passes (no syntax errors)
**And** `pytest tests/test_bernard_voice_completeness.py` passes (3 tests: forbidden patterns, JSON/YAML match, key references)

### AC9 — Gating test (M2 acceptance test — manual)

**Given** Story 9.8 is deployed to `genjson.mapsofmaking.org`
**When** Nicolas follows the tutorial with a real GitLab account
**Then**:
1. Nicolas completes Tier 0 + Tier 1, exports the JSON, and clicks "Go live →" (the fork door at the end of Tier 1)
2. `#golive` reveals `#golive-beat-account`; Nicolas creates a GitLab account, clicks "Done →"
3. `#golive-beat-project` reveals (Bernard reacts "Account's yours…"); creates a public project, "Done →"
4. `#golive-beat-upload` reveals; uploads the JSON, "Done →"
5. `#golive-beat-rawurl` reveals; opens raw, copies the URL, "Done →"; `#golive-beat-endpoint` reveals (`endpoint_bridge` + `closing`)
6. Nicolas returns to the MoM map, opens "Add your space", takes the "paste your endpoint URL" path, pastes the raw URL, submits → space pin appears on the map

**This is the M2 acceptance test.** The story is not done until this manual path succeeds end-to-end. The beat seam (Bernard reacting between steps) must read naturally — operator confirms voice.

---

## Tasks / Subtasks

- [x] **Task 0 — Add `tutorial:` keys to `bernard_copy.yaml` and regenerate** (AC4). Add the `tutorial:` namespace (trigger, step1–4, endpoint_bridge, closing, next). Run `make bernard-copy`. Update `COPY_FALLBACK` in `genjson.js` with a matching `tutorial` object. Run `pytest tests/test_bernard_voice_completeness.py` → 3 passed. Watch the voice guard: the beat-seam openers ("Account's yours.", "Project's up.", "It's hosted.") must not trip forbidden patterns.

- [x] **Task 0b — Rename legacy beat IDs to the `<section>-beat-<leaf>` taxonomy** (Dev Notes "Beat ID taxonomy"; ux-spec §P2 lock). Mechanical, behavior-preserving rename of the 9.12-shipped IDs in `genjson.js`: `tier0-beat`→`tier0`, `beat-name`→`tier0-beat-name`, `beat-location`→`tier0-beat-location`, `beat-bedrock`→`tier0-beat-bedrock`, `tier1-beat`→`tier1`. Update every reference: `id=` attributes (render template) **and** all `revealBeat()` / `getElementById()` call sites (~lines 757–758, 1016, 1118, 1167–1171, 1236, 1304). Do this **first**, before building the `golive` section, so the new beats land on a clean convention. Verify: `node --check` clean; manual smoke — fresh load reveals name→location→bedrock→Continue→tier1, resume snaps earned beats, geocode/strip/export all unchanged. **No copy, no behavior change** — IDs only.

- [x] **Task 1 — Crop and commit screencap assets** (AC5). Crop `docs/gitlab_tuto/` screencaps to step-relevant UI. Commit as `web/genjson/tuto/step1-account.png`, `step2-project.png`, `step3-upload.png`, `step4-raw.png`. Max ~600px wide.

- [x] **Task 2 — Add `#golive` as beat-by-beat DOM in `render()`** (AC2, AC3, AC6). After the existing `fork` `<div>`, append the `#golive` section wrapper (class `.beat`) hidden. Inside it: the system-voice `trigger` line, then the five `.beat` blocks per the taxonomy — `#golive-beat-account`, `-project`, `-upload`, `-rawurl` (each: `.bernard-voice` line + screencap `<img>` + a "Done →" `.beat-next` button), then `#golive-beat-endpoint` (two Bernard lines, no screencap, no button). Each beat uses the `grid-template-rows 0fr→1fr` + opacity + `inert` pattern; only `#golive-beat-account` visible on open. Reference `COPY.tutorial.*` keys only. Add CSS for `#golive .beat-next` + screencap `<img>` in the `CSS` const (no new stylesheet; `.beat` already exists). `node --check` clean.

- [x] **Task 3 — Wire `#fork-live` to expand `#golive` + the beat steppers** (AC1, AC2). Replace the existing `fork-live` click handler (currently shows `COPY.fork_stub.tutorial_teaser`) with logic that `revealBeat('golive')` then `revealBeat('golive-beat-account')`, and settles `#fork-live`. Wire each `.beat-next` button to settle its beat and `revealBeat()` the next in the chain (account→project→upload→rawurl→endpoint). `revealBeat()` already exists (~line 934) — reuse it. Honor `prefers-reduced-motion`.

- [x] **Task 4 — Terminal close beat** (AC3). The "Done →" on `#golive-beat-rawurl` reveals `#golive-beat-endpoint` (`endpoint_bridge` + `closing`). That beat has no screencap and no advance button — it is terminal. No input, no CTA, no navigation — the coordinator returns to the map themselves. Confirm there is no URL collection anywhere in `#golive`.

- [x] **Task 5 — Mobile pass** (AC7). Add `.beat-next` to the `@media (max-width: 480px)` block (min-height 44px). Confirm beats stack and screencaps reflow without horizontal scroll.

- [x] **Task 6 — Regression check** (AC8). `node --check`, `pytest tests/test_bernard_voice_completeness.py`. Manual smoke: load wizard fresh + resume, confirm all existing beats, geocode, strip, export still work. Confirm `#fork-deeper` still shows `COPY.fork_stub.tier2_teaser` (untouched).

- [ ] **Task 7 — Deploy + M2 acceptance test** *(manual — Nicolas)* (AC9). `make deploy-genjson`. Walk the beat-by-beat tutorial with a real GitLab account, then return to the map and register via "paste your endpoint URL". Confirm end-to-end: raw URL → map pin. Operator (Nicolas) confirms the beat seam reads naturally.

---

## Dev Notes

### Where the code lives — read before touching

- **All wizard code is `web/genjson/genjson.js`** — single file, no build step. CSS is the `CSS` const (~lines 67–285). DOM is built in `render()`. Events are wired in `wireEvents()`.
- **`index.html`** is 12 lines — loads `genjson.js` with `defer`. Do not touch.
- **`bernard_copy.yaml`** is the copy SSOT. Edit here → `make bernard-copy` → `bernard_copy.json` generated. Never edit the JSON by hand.
- **The fork is at `render()` lines ~896–911** — `#fork-live` click handler is in `wireEvents()` lines ~1135–1138. That handler is Task 3's target.
- **`revealBeat(id, instant)`** (~line 934) drives all beat reveals via `grid-template-rows 0fr→1fr` + opacity. It is **ID-agnostic** — pass any beat ID. **Reuse it directly; never fork a parallel reveal mechanism.**

### Beat ID taxonomy — `<section>-beat-<leaf>` (LOCKED in ux-bernard-wizard-spec.md §P2)

`.beat` and `revealBeat()` are **shared grammar**, not tier-specific. Every step in the workshop is a `.beat` by design (§P2). The tutorial beats are **real `.beat`s reusing `revealBeat()`** — inventing a separate reveal path is the violation, not the reuse.

Differentiation is by **section-first ID namespace**: the section owns its beats (reads like nested JSON `golive.beat.account`). Sections are the namespace root; beats hang under them.

| Section (wrapper, a `.beat`) | Its beats — `<section>-beat-<leaf>`, semantic, never numbered |
|---|---|
| `tier0` | `tier0-beat-name`, `tier0-beat-location`, `tier0-beat-bedrock` |
| `tier1` | *(no content beats today)* |
| `golive` (this story) | `golive-beat-account`, `golive-beat-project`, `golive-beat-upload`, `golive-beat-rawurl`, `golive-beat-endpoint` |

Rules:
- **Section wrapper = bare section name** (`golive`), itself carrying class `.beat`, revealed via `revealBeat('golive')`.
- **Each beat = `<section>-beat-<leaf>`**, semantic leaf, prefixed by its owning section. No bare `beat-*` IDs.
- **Reuse the `.beat` class** — inherits transition, `inert`, `prefers-reduced-motion` for free.
- The "Done →" advance button is tutorial-specific: scope it `#golive .beat-next` (or a `golive-`prefixed class).
- Grep test: `grep tier0` isolates all of Tier 0; `grep golive` isolates the whole tutorial. No overlap.

**Legacy rename (Task 0b below):** this story renames the 9.12-shipped IDs to align: `tier0-beat`→`tier0`, `beat-name`→`tier0-beat-name`, `beat-location`→`tier0-beat-location`, `beat-bedrock`→`tier0-beat-bedrock`, `tier1-beat`→`tier1`. Behavior identical; `node --check` + manual smoke confirms equivalence.

### No handoff machinery — the loop is manual by design

There is **no** localStorage handoff, no URL pre-fill, no `window.location` navigation. The closing beat (`endpoint_bridge` + `closing`) tells the coordinator to return to the MoM map themselves and use the drawer's existing **"paste your endpoint URL"** path (Fork B, second door) with the raw URL they copied. This is deliberate (hero's-journey return — they now know what an endpoint is): we do not automate the crossing, we witness it. **Do not** build a cross-page handoff; `web/maps-of-making.html` is out of scope.

### `fork_stub.tutorial_teaser` after Story 9.8

Once `#fork-live` is wired to expand `#golive`, the `COPY.fork_stub.tutorial_teaser` key is no longer used by `#fork-live`. **Do not delete the COPY key** — `test_bernard_voice_completeness.py` checks that all YAML keys are referenced in JS. Either keep a dormant reference in a JS comment or add a note explaining the key is reserved. Simplest: leave the `fork-live` handler referencing it in a comment. Alternatively, remove the key from the YAML and update the test — but that risks churn. Leave it for now; clean up in a future story.

### Screencap assets path and nginx

`web/genjson/tuto/` is served by nginx via the genjson location block:

```nginx
location /genjson/ {
    root /var/www/maps;
    try_files $uri $uri/ =404;
}
```

No nginx config change needed — any file under `web/genjson/` is served as-is. The `<img src="tuto/step1-account.png">` path is relative to the wizard page at `/genjson/` → resolves to `/genjson/tuto/step1-account.png`.

### Copy em-dash convention (Story 9.5)

- **Bernard spoken lines** (`tutorial.step1`, `step2`, `step3`, `step4`, `endpoint_bridge`, `closing`): the JS prepends `— ` before rendering inside `.bernard-voice` elements.
- **System voice** (`tutorial.trigger`, `tutorial.next`): rendered flat, no `.bernard-voice` class, no em-dash. `trigger` is the orientation line above `#golive-beat-account`; `next` is the "Done →" advance button label.

### `tutorial.trigger` placement

`COPY.tutorial.trigger` is the first thing shown when `#golive` opens — it is **system voice** (not `.bernard-voice`), no em-dash, rendered above `#golive-beat-account`. It reads as an orientation statement before Bernard's first beat. (It folds the old `no_friction` "no credit card / no server / no command line" fact into one line.)

### Hard constraints (do not violate)

- **No `font-weight` rules** (Special Elite is single-weight — bernard-bible §4).
- **No CDN resources** (CSP `default-src 'self' 'unsafe-inline'`). All images from `tuto/` served self-origin.
- **No hardcoded strings** — every visible label uses `COPY.tutorial.*`. Any string not in the YAML will fail `test_bernard_voice_completeness`.
- **`#fork-deeper` is untouched** — it still shows `COPY.fork_stub.tier2_teaser` (wired in Story 9.6, still a stub for now).
- **`exportJSON()` filename convention is locked** (Story 9.12 AC6) — do not change it.
- **Do not touch `web/maps-of-making.html`** — the drawer is out of scope.

### Isolation note

Local dev: serve `web/genjson/` from maps-nginx (same-origin needed for `fetch('/bernard_copy.json')`). Use `distrobox-host-exec` for Podman access if running in distrobox:

```bash
distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up
```

`source venv/bin/activate` before any pytest run.

Deploy: `make deploy-genjson` (runs `make bernard-copy` first, then rsync to VPS).

### 9.12 frame lock reminder

All new UI elements in this story **inherit the locked 9.12 frame**:
- Direction B dusk palette (CSS variables already defined — use them, don't invent new colors)
- Semantic color discipline: amber = CTA, blue = links, green = valid, red = errors only
- `.bernard-voice` triplet is locked (`font-family: 'Special Elite'; font-size: 17px; line-height: 1.55;`)
- Spacing via `--space-1..4` custom props
- `2px` border-radius, shadow language consistent with rest of wizard

---

## Reference Assets

```
docs/gitlab_tuto/
├── V2_Hosting_Your_Space.png          ← 6-panel visual summary of the full flow (reference)
├── screencap_0601_164821.png          ← (not used — login screen, registration is elsewhere)
├── screencap_0601_165023.png          ← Step 1 source: GitLab sign-in page (register link visible)
├── screencap_0601_165341.png          ← Step 2 source: project creation form
├── screencap_0601_165500.png          ← Step 2 alt: visibility selector
├── screencap_0601_170836.png          ← Step 3 source: "Commit changes" dialog with JSON file
├── screencap_0601_171102.png          ← Step 4 source: file view + "Open raw" highlighted
└── ...
```

Target assets (to be created in Task 1):
```
web/genjson/tuto/
├── step1-account.png
├── step2-project.png
├── step3-upload.png
└── step4-raw.png
```

---

## Dev Agent Record

### Completion Notes (2026-06-02)

**COPY_FALLBACK removed** — replaced with `emptyProxy()` (JS Proxy returning `''` for any nested access). Fetch failure now logs `console.error('[wizard] copy fetch failed…')` and degrades gracefully. Single source of truth: YAML → JSON → wizard. No string in two places.

**Beat ID taxonomy landed** — `tier0-beat`→`tier0`, `beat-name/location/bedrock`→`tier0-beat-*`, `tier1-beat`→`tier1`. All call sites updated. Behavior unchanged, `node --check` clean.

**Screencaps** — cropped from `docs/gitlab_tuto/` via ImageMagick, committed to `web/genjson/tuto/` at ≤600px wide.

**`#golive` section** — 5 beats wired beat-by-beat. Trigger line (system voice), then `account→project→upload→rawurl→endpoint`. Each step uses `data-next=` attribute; event delegation on `#golive` handles all `.beat-next` clicks. Terminal beat has no button.

**`#fork-live`** — settles visually on first click (disabled + muted), open-only (second click no-ops). Reveals `golive` + `golive-beat-account` together.

### File List

- `web/genjson/genjson.js` — COPY_FALLBACK removed; emptyProxy added; beat ID rename; #golive DOM + CSS + wiring
- `web/genjson/bernard_copy.yaml` — `tutorial:` namespace added
- `web/genjson/bernard_copy.json` — regenerated via `make bernard-copy`
- `web/genjson/tuto/panel-account.png`, `panel-project.png`, `panel-upload.png`, `panel-rawurl.png` — new (cropped from V2 composite, per beat)
- `web/genjson/tuto/panel-register.png` — new (real "Add your space" drawer screenshot — Step 5 finishes on the familiar view)
- `web/genjson/tuto/hosting-guide-hd.png` — new (1200px V2 composite, offered as downloadable cheat sheet)

### Post-review revisions (operator feedback 2026-06-02)

- COPY_FALLBACK removed → `emptyProxy()` + `console.error` logging (single source of truth)
- trigger line → Bernard voice (em-dash), was system voice
- fork "Two ways forward. Your call." label removed (rhythm fix)
- Tab/Enter advances golive beats (commit-to-advance parity with Tier 0)
- "← close" affordance collapses #golive, re-enables "Go live →"
- 4 individual screencaps → 5 per-beat panels derived from V2; added Step 5 (register); video link + downloadable cheat sheet
- merged `endpoint_bridge` into step4 (removed key) — one Bernard utterance per beat

### Change Log

- 2026-06-02: Story 9.8 implemented — golive tutorial section, beat ID taxonomy, screencap assets, emptyProxy replaces COPY_FALLBACK
