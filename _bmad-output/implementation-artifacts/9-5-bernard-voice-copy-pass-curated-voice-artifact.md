# Story 9.5: Bernard Voice Copy Pass — Curated Voice Artifact

Status: ready-for-dev

## Story

As the MoM product,
I want all wizard copy (intro, tier gates, field hints, validation messages, sovereignty disclosure) authored in a single curated artifact before any downstream UI story lands its final text,
so that Bernard's voice is consistent across Stories 9.2–9.8 and individual story ACs reference the artifact rather than each containing their own ad-hoc copy.

## Acceptance Criteria

### AC1 — `bernard_copy.yaml` exists as the canonical voice artifact

**Given** the calibrated lines in `bernard-bible.md §9` and the voice rules in §2–3
**When** Story 9.5 lands
**Then** `web/genjson/bernard_copy.yaml` exists as a YAML map keyed by moment, containing **exactly** these top-level keys and nested structure:

```yaml
drawer_one_liner: "Two ways onto the map. Tell me about your space, or paste your endpoint URL if you've got one. Either's fine."
wizard_intro: "Hi, I'm Bernard (they/them) from 'Mother Sands'. Let's get your space on the map."
floor_gate: "Name and address. That's the floor. Everything else, I'll derive."
tier_1_exit: "Core's in. Other SpaceAPI apps can read this file as-is."
tier_2_exit: "MoM fields filled. Network features unlocked: membership, opening hours, SDGs."
tier_3_exit: "Silo fields in. Your space's vertical features active."
sovereignty_disclosure: "You publish, we make it legible. The rest is history."
localstorage_warning: "Your progress is saved in this browser. Hard-refresh or clearing site data wipes it. Export at any point if you want a copy outside the browser."
localstorage_resume: "Continuing from where you left off."
field_hints:
  space: "The name your community knows you by."
  address: "Street address — the part before city."
  city: "City or municipality."
  postcode: "Postal code."
  country_code: "Two-letter ISO country code. e.g. DE, FR, BE."
  logo: "A direct URL to a square image. Shows on your map card."
  url: "Your space's main web page."
  description: "One or two sentences. What kind of space is this?"
  contact_email: "A contact address for the space — not a personal inbox."
  contact_mastodon: "e.g. @space@chaos.social"
  opening_hours: "When are you open? We use OSM opening_hours format."
  memberOf: "Which network(s) is this space part of? URL preferred."
  sdgs: "Which UN Sustainable Development Goals does your space contribute to? Numbers only."
validation_messages:
  schema_invalid: "Something's off. Check the fields marked in red — the file isn't valid yet."
  nominatim_unavailable: "Geocoding temporarily unavailable — enter coordinates manually."
  nominatim_no_result: "No result — enter coordinates manually."
  nominatim_rate_limit: "Too many requests — wait a moment and try again."
  clear_confirm: "This will erase your saved progress. Continue?"
  url_scheme_added: "Added https:// — update if wrong."
fork_stub:
  tier2_teaser: "Tier 2 is on the way. Network features land in a later step."
  tutorial_teaser: "Self-hosting walkthrough is on the way. Export your file and keep it warm for now."
```

**And** all string values follow the Bernard voice rules (§3 bible): short sentences, no exclamation marks, observation over explanation, dry register
**And** no forbidden patterns appear: "most spaces leave this blank", "keep it simple", "you can do better than them", any nudge that comforts mediocrity OR shames, any ranking of user choices
**And** em-dash (`—`) convention is **not** included in the YAML values — the JS prepends it to Bernard's spoken lines (not to field hints or validation messages)

### AC2 — `genjson.js` loads the artifact and replaces hardcoded strings

**Given** `web/genjson/bernard_copy.yaml` exists and `web/genjson/bernard_copy.json` is generated from it
**When** the wizard page loads
**Then** `genjson.js` fetches `/bernard_copy.json` (same-origin, CSP-safe) once at startup and caches the result in a module-level `COPY` object
**And** every string currently hardcoded in `genjson.js` that corresponds to a YAML key is replaced with a lookup into `COPY` (e.g. `COPY.wizard_intro`, `COPY.field_hints.space`)
**And** if the fetch fails (network error / 404), the wizard falls back to a **minimal inline fallback object** containing only the strings required for Tier 0 to function (`wizard_intro`, `floor_gate`, `localstorage_warning`, `localstorage_resume`, `clear_confirm`) — the wizard must remain usable if `bernard_copy.json` is unreachable
**And** the fallback inline object contains only the Tier 0/core strings — it is not a full duplicate of the YAML

### AC3 — Canonical font locked: self-hosted Special Elite

**Given** Story 9.3 uses a system-mono stack because Special Elite cannot load from Google Fonts CDN under the `'self'` CSP
**When** Story 9.5 lands
**Then** **Special Elite is the canonical Bernard font** (decision locked by operator 2026-05-31), self-hosted to satisfy the genjson CSP, applied consistently across **both** surfaces: the wizard (`web/genjson/`) and the map drawer (`web/maps-of-making.html`)
**And** `SpecialElite-Regular.woff2` is downloaded into `web/genjson/fonts/` and `web/fonts/` (Apache 2.0 license — vendored, not CDN)
**And** an `@font-face` rule is added in both surfaces pointing to the self-hosted file (served from `'self'`, CSP-safe)
**And** the canonical `.bernard-voice` declaration in both surfaces is:

```css
.bernard-voice {
  font-family: 'Special Elite', var(--font-mono), monospace;
  font-size: 17px;
  line-height: 1.55;
}
```

**And** the `maps-of-making.html:321` comment is updated from "test ahead of Story 9.5 font canon" to "canonical" and the Google Fonts `<link>` is replaced by the self-hosted `@font-face` (no CDN dependency remains on either surface)
**And** `var(--font-mono)` resolves to the existing system-mono stack (`'Courier New', 'Lucida Console', monospace`) as the loading/fallback face — define the CSS variable if not already present

> **Hierarchy constraint (operator note, 2026-05-31):** Special Elite ships **a single weight only** — `font-weight: bold` does nothing. Bernard's visual hierarchy must come from **font-size and color contrast** (the muted-tombstone pattern already in use), never from boldness. Do not add `font-weight` rules to `.bernard-voice` expecting an effect; reviewers should reject any such rule.

### AC4 — YAML → JSON build step documented

**Given** `genjson.js` loads `bernard_copy.json` at runtime
**When** `bernard_copy.yaml` is edited
**Then** running `make bernard-copy` (new Makefile target) regenerates `web/genjson/bernard_copy.json` from `web/genjson/bernard_copy.yaml`
**And** the target uses: `python3 -c "import yaml, json, sys; json.dump(yaml.safe_load(open('web/genjson/bernard_copy.yaml')), open('web/genjson/bernard_copy.json','w'), ensure_ascii=False, indent=2)"`
**And** `web/genjson/bernard_copy.json` is committed alongside `bernard_copy.yaml` — the JSON is the runtime artifact, the YAML is the source of truth for edits
**And** `deploy-genjson` Makefile target is updated to run `make bernard-copy` before rsync so deploys always ship an up-to-date JSON

### AC5 — `test_bernard_voice_completeness` passes

**Given** `web/genjson/bernard_copy.yaml` and `web/genjson/genjson.js`
**When** `pytest tests/test_bernard_voice_completeness.py` runs (venv activated)
**Then** the test:
  1. Loads the YAML and extracts all leaf key paths (e.g. `field_hints.space`, `validation_messages.schema_invalid`)
  2. Reads `genjson.js` source
  3. Asserts that every leaf key path appears as a lookup reference in `genjson.js` (e.g. `COPY.field_hints.space` or `COPY['field_hints']['space']`)
  4. Reports any YAML keys that are never referenced in the JS (warnings — not failures; future stories may introduce them)
  5. Asserts that **no** forbidden phrases appear in any YAML string value: checks for "most spaces leave this blank", "keep it simple", "you can do better", "well done", "great job"
**And** the test passes with exit 0

### AC6 — Operator tone approval

**Given** the full YAML artifact
**When** Nicolas reads it
**Then** Nicolas confirms:
  - No forbidden patterns (§3 bible)
  - Consistent register across all keys (not a mix of Bernard voice and generic SaaS copy)
  - Em-dash convention is correctly handled by the JS (not embedded in YAML values)
**And** tone approval is documented in the Story 9.5 completion notes (no automated tone test — operator judgement)

## Tasks / Subtasks

- [ ] **Font: self-host Special Elite** (AC3 — decision locked by operator)
  - [ ] Download `SpecialElite-Regular.woff2` (Apache 2.0) into `web/genjson/fonts/` and `web/fonts/`
  - [ ] Add `@font-face` in both `web/genjson/genjson.js` CSS block and `web/maps-of-making.html`, pointing to the self-hosted woff2 (served from `'self'`)
  - [ ] Set canonical `.bernard-voice` declaration in both surfaces (size 17px, line-height 1.55, `'Special Elite', var(--font-mono), monospace`); define `--font-mono` if absent
  - [ ] Replace the Google Fonts `<link>` in `maps-of-making.html` with the self-hosted face; update the `:321` comment from "test" to "canonical"
  - [ ] Confirm **no `font-weight`** rule on `.bernard-voice` (single-weight font — hierarchy via size/color only)

- [ ] **Author `bernard_copy.yaml`** (AC1) — curate all copy per bernard-bible; verify no forbidden patterns
  - [ ] Cross-check every string against bernard-bible §3 (voice guide) and §9 (calibrated lines)

- [ ] **Generate `bernard_copy.json`** (AC4) — YAML → JSON via Makefile target
  - [ ] Add `bernard-copy` target to Makefile
  - [ ] Update `deploy-genjson` to run `make bernard-copy` before rsync
  - [ ] Commit both `bernard_copy.yaml` and `bernard_copy.json`

- [ ] **Wire `genjson.js` to use the artifact** (AC2)
  - [ ] Add `fetchCopy()` at top of init — `fetch('/bernard_copy.json')`, cache in `COPY`
  - [ ] Add minimal inline fallback object (Tier 0 strings only)
  - [ ] Replace each hardcoded string with `COPY.<key>` lookup (use `grep` on the strings identified in Dev Notes below)
  - [ ] Confirm em-dash is prepended by JS, not in YAML values

- [ ] **Write `test_bernard_voice_completeness`** (AC5)
  - [ ] Add `tests/test_bernard_voice_completeness.py`
  - [ ] YAML leaf-key extraction + JS reference scan + forbidden-phrase check
  - [ ] `pytest tests/test_bernard_voice_completeness.py` passes

- [ ] **Operator tone review** (AC6)
  - [ ] Nicolas reads full `bernard_copy.yaml` and approves or requests edits
  - [ ] Document approval in Completion Notes

## Dev Notes

### Font — LOCKED: self-hosted Special Elite (operator decision, 2026-05-31)

`Special Elite` is canon. The drawer (`maps-of-making.html`) currently loads it from the Google Fonts CDN; the wizard CSP (`'self'`) blocks CDN, so the font must be **self-hosted** and both surfaces switched to the local copy:

- Download `SpecialElite-Regular.woff2` (Apache 2.0) → `web/genjson/fonts/` and `web/fonts/`.
- `@font-face { font-family: 'Special Elite'; src: url('fonts/SpecialElite-Regular.woff2') format('woff2'); font-display: swap; }` in both surfaces.
- Canonical declaration (operator-supplied):
  ```css
  .bernard-voice {
    font-family: 'Special Elite', var(--font-mono), monospace;
    font-size: 17px;
    line-height: 1.55;
  }
  ```
- Replace the Google Fonts `<link>` in `maps-of-making.html` so no CDN dependency remains.

**Single-weight gotcha:** Special Elite has **no weight variants** — `font-weight: bold` is a no-op. Hierarchy comes from **size + color contrast** (the muted-tombstone pattern), never boldness. Don't write `font-weight` rules on `.bernard-voice`; they silently do nothing and mislead future maintainers.

### Hardcoded strings to migrate in `genjson.js` (current locations)

The following strings in `genjson.js` map to `bernard_copy.yaml` keys and must be replaced with `COPY.*` lookups:

| Current JS string (approximate) | YAML key |
|---|---|
| `"— Hi, I'm Bernard (they/them) from 'Mother Sands'..."` | `wizard_intro` (em-dash prepended by JS) |
| `"— Your progress is saved in this browser..."` | `localstorage_warning` |
| `"— Name and address. That's the floor..."` | `floor_gate` |
| `"— Core's in. Other SpaceAPI apps can read this file as-is."` | `tier_1_exit` |
| `"Geocoding temporarily unavailable — enter coordinates manually"` | `validation_messages.nominatim_unavailable` |
| `"No result — enter coordinates manually"` | `validation_messages.nominatim_no_result` |
| `"This will erase your saved progress. Continue?"` | `validation_messages.clear_confirm` |
| `"— Tier 2 is on the way. Network features land in a later step."` | `fork_stub.tier2_teaser` |
| `"— Self-hosting walkthrough is on the way..."` | `fork_stub.tutorial_teaser` |
| `"Added https:// — update if wrong."` | `validation_messages.url_scheme_added` |
| Field hint divs (logo, url, description, email, mastodon) | `field_hints.*` |

Run `grep -n "// placeholder\|this will\|geocod\|your progress\|floor\|core's in\|hint\|Two ways" web/genjson/genjson.js` to locate each instance.

### `fetchCopy()` pattern — vanilla JS, no build step

```javascript
// Module-level COPY object — populated by fetchCopy() at init
let COPY = null;

// Minimal fallback — Tier 0 essentials only; avoids blank UI if fetch fails
const COPY_FALLBACK = {
  wizard_intro: "Hi, I'm Bernard (they/them) from 'Mother Sands'. Let's get your space on the map.",
  floor_gate: "Name and address. That's the floor. Everything else, I'll derive.",
  localstorage_warning: "Your progress is saved in this browser. Hard-refresh or clearing site data wipes it. Export at any point if you want a copy outside the browser.",
  localstorage_resume: "Continuing from where you left off.",
  validation_messages: { clear_confirm: "This will erase your saved progress. Continue?" }
};

async function fetchCopy() {
  try {
    const resp = await fetch('/bernard_copy.json');
    if (!resp.ok) throw new Error('copy fetch failed');
    COPY = await resp.json();
  } catch {
    COPY = COPY_FALLBACK;
  }
}
```

The existing `init()` function should `await fetchCopy()` before calling `render()`.

### Em-dash convention — JS responsibility, not YAML

Bernard's spoken lines open with `—` (em-dash, literary convention, bible §4). This is applied by JS when rendering `.bernard-voice` elements:

```javascript
// When setting bernard-voice textContent:
intro.textContent = `— ${COPY.wizard_intro}`;
// NOT stored in YAML — avoids double-dash if convention changes
```

Field hints and validation messages do NOT get em-dash — only the direct "Bernard speaks" lines (`wizard_intro`, `floor_gate`, `tier_*_exit`, `localstorage_warning`).

### `test_bernard_voice_completeness.py` approach

```python
import yaml, re, pytest
from pathlib import Path

ROOT = Path(__file__).parent.parent
COPY_YAML = ROOT / 'web/genjson/bernard_copy.yaml'
GENJSON_JS = ROOT / 'web/genjson/genjson.js'

FORBIDDEN = ['most spaces leave this blank', 'keep it simple',
             'you can do better', 'well done', 'great job']

def leaf_paths(d, prefix=''):
    for k, v in d.items():
        path = f"{prefix}.{k}" if prefix else k
        if isinstance(v, dict):
            yield from leaf_paths(v, path)
        else:
            yield path, v

def test_no_forbidden_patterns():
    copy = yaml.safe_load(COPY_YAML.read_text())
    for path, val in leaf_paths(copy):
        for forbidden in FORBIDDEN:
            assert forbidden.lower() not in val.lower(), \
                f"Forbidden pattern '{forbidden}' found at {path}"

def test_keys_referenced_in_js():
    js = GENJSON_JS.read_text()
    copy = yaml.safe_load(COPY_YAML.read_text())
    unreferenced = []
    for path, _ in leaf_paths(copy):
        # check COPY.field_hints.space style OR COPY['field_hints']['space'] style
        parts = path.split('.')
        dotted = 'COPY.' + path
        bracketed = 'COPY' + ''.join(f"['{p}']" for p in parts)
        if dotted not in js and bracketed not in js:
            unreferenced.append(path)
    # warn but don't fail — future stories add keys before JS uses them
    if unreferenced:
        pytest.warns(UserWarning, match='unreferenced')  # or just print
        print(f"WARN: YAML keys not yet referenced in genjson.js: {unreferenced}")
```

Adjust as needed for the actual lookup pattern used in `genjson.js`.

### `drawer_one_liner` key — informational, not injected

The `drawer_one_liner` key in the YAML documents the canonical drawer copy for reference (9.2 is done and hardcoded in `web/maps-of-making.html:676`). The drawer does **not** load `bernard_copy.json` — it is a static HTML file without a JS loader for copy. This key exists so future maintainers have a single place to read all Bernard copy. **Do not add a JS fetch to `maps-of-making.html`** — that would be out of scope and risky.

### Source tree

- `web/genjson/bernard_copy.yaml` — NEW (voice artifact SSOT)
- `web/genjson/bernard_copy.json` — NEW (generated; committed; runtime artifact)
- `web/genjson/genjson.js` — UPDATE (add fetchCopy, replace hardcoded strings)
- `web/maps-of-making.html:321` — UPDATE (`.bernard-voice` font declaration, remove "test" qualifier)
- `Makefile` — UPDATE (add `bernard-copy` target; update `deploy-genjson`)
- `tests/test_bernard_voice_completeness.py` — NEW
- `web/genjson/fonts/SpecialElite-Regular.woff2` — NEW (self-hosted, Apache 2.0)
- `web/fonts/SpecialElite-Regular.woff2` — NEW (self-hosted, shared with drawer)

### Isolation Notes

- **Frontend only** — no container changes. Serve `web/genjson/` with `python3 -m http.server 8080` from the `web/genjson/` dir for local iteration (or via the maps-nginx container). Activate venv (`source venv/bin/activate`) for Python scripts and pytest.
- `make bernard-copy` requires `pyyaml` — add to `requirements.txt` if not present, or use `pip install pyyaml` in venv.
- The `fetch('/bernard_copy.json')` call requires the file to be served from the same origin as `genjson.js`. Local `http.server` satisfies this.
- No nginx changes, no container restart needed for this story.

### Previous story intelligence (9.3 — done)

From 9.3 completion notes (operator-review iterations, 2026-05-31):
- **Contrast pass** and "fine styling + tone deferred to Story 9.5" — the CSS contrast tweaks from 9.3 are in place; this story completes the tone side of that deferral.
- `genjson.js` uses `'Courier New', 'Lucida Console', monospace` as the system-mono `.bernard-voice` stack (no Google Fonts). Story 9.5 locks or upgrades this (AC3).
- 9.3 review finding: "429 from nginx surfaces as 'Geocoding temporarily unavailable' (no retry hint) — UX improvement, deferred to Story 9.5 copy pass." → AC1 adds `validation_messages.nominatim_rate_limit` key for this.
- `fork_stub` text currently hardcoded inline in the `deeperBtn`/`tutorialBtn` click handlers — also migrated to `COPY.fork_stub.*`.

### References

- [Source: `_bmad-output/planning-artifacts/bernard-bible.md` §2–5, §9] — voice rules, typography, calibrated lines
- [Source: `_bmad-output/planning-artifacts/epics.md` §Story 9.5] — full AC including YAML structure
- [Source: `_bmad-output/implementation-artifacts/9-3-wizard-core-*.md` §Completion Notes] — 9.3 review deferrals
- [Source: `web/genjson/genjson.js` lines ~424–531] — all current hardcoded Bernard strings
- [Source: `web/maps-of-making.html:321`] — `.bernard-voice` font declaration (currently "test")
- [Source: `infra/gateway-nginx/08-genjson-mapsofmaking.conf:46`] — CSP `default-src 'self' 'unsafe-inline'`; same-origin fetch OK

## Out of Scope

- Updating the drawer HTML (`maps-of-making.html`) to dynamically load copy — the drawer is static; `drawer_one_liner` in the YAML is documentation only.
- Tier 2 / Tier 3 field copy (opening_hours, sdgs, ext_fab) — Story 9.6+; YAML includes placeholder keys for forward compatibility.
- `state.open` FSM labels — Story 9.7.
- GitLab tutorial copy — Story 9.8.
- Error UX / inline per-field error messages — Story 9.11.
- **Wizard visual design** (color scheme, layout, spacing, contrast, mobile) — **Story 9.12**. This story owns only the font (AC3) and the copy; all other styling is 9.12's. The Story 9.3 deferral *"fine styling + tone deferred to Story 9.5"* is split: tone+font here, visual design in 9.12.

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
