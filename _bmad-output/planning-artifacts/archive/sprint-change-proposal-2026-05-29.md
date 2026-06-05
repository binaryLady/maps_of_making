# Sprint Change Proposal — Epic 9 "Bernard's Workshop" + Pre-Epic Schema Cleanup

**Date:** 2026-05-29
**From:** Nicolas + Claude (brainstorming session)
**Source:** `_bmad-output/brainstorming/brainstorming-session-2026-05-29-1500.md`
**Status:** Ready for `bmad-edit-prd` / `bmad-create-epics-and-stories` in a fresh context

---

## TL;DR

Insert a parallel track **Epic 9 — Bernard's Workshop** (assisted SpaceAPI JSON composer at `genjson.mapsofmaking.org`) alongside the already-replanned Epic 4. Prerequisite: a small shared **Cleanup Story C.X — Schema namespace pass** that benefits both tracks.

New track sequence: **`C.X → Epic 9 → Epic 4 re-review`**.

---

## What changes

### 1. New shared prerequisite — Cleanup Story C.X

**Scope:** Rename `ext_mom` → `ext_canary` (current contents are Mother-Sands-only). Introduce `mom:` namespace fields for cross-network horizontal data: `opening_hours`, `memberOf`, `mom:sdgs` (migrated from `ext_fab.sdgs`). Update baseline.json, ontology (`mom.ttl`), transformer, materializer. Wipe + reseed using existing Makefile.

**Blocks:** Both Epic 9 AND Epic 4 re-review.

**Pattern reference:** Same split-out shape as the 2026-05-16 pre-Story-3.3 drift-fix cleanup story.

**Estimated:** 1 story.

### 2. New Epic 9 — Bernard's Workshop

Assisted SpaceAPI JSON composer at `genjson.mapsofmaking.org`, with the Bernard voice as the UX anchor. **Goal:** convincing, inclusive, effortless onboarding for non-tech space coordinators, with sovereignty + self-hosting (GitLab Pages) as the end state. UX over features. Minimal cognitive load. **Bernard never appears on screen as character imagery** — he is the voice of the copy, not a face.

**M1 — Floor & Core (must-ship):**
- Story 9.1 — Subdomain & infra (`genjson.mapsofmaking.org` DNS + nginx + cert + static page scaffold)
- Story 9.2 — Drawer UX on MoM map (Bernard one-liner + inline "Your endpoint" URL input + "Tell me about your space" CTA)
- Story 9.3 — Wizard core: tiers 0 + 1 (name+address → Nominatim derivation → SpaceAPI v15 core; localStorage; export)
- Story 9.4 — Nominatim proxy endpoint in `link_handler` (server-side, geopy.Nominatim, 1 req/s)
- Story 9.5 — Bernard voice copy pass (intro line, tier gates, validation messages, sovereignty line — single curated artifact)

**M2 — MoM features & pedagogy:**
- Story 9.6 — Tier 2 (`mom:` fields: `opening_hours`, `memberOf`, `mom:sdgs`)
- Story 9.7 — state.open FSM (cascading questions + marker mapping green/black/blue + opt-out via field omission)
- Story 9.8 — GitLab tutorial surface (embedded guide, "see logo on card" success moment, refresh affordance)

**M3 — Modes & extensibility (deferrable):**
- Story 9.9 — Three-mode unification (URL fetch → pre-fill update; validator mode; cache resume reconciliation)
- Story 9.10 — Tier 3 (`ext_fab.space_type` fuzzy dropdown, `ext_fab.equipment`)
- Story 9.11 — Validator error UX (inline per-field + summary report)

### 3. Sequencing adjustment

| Before | After |
|---|---|
| Epic 4 re-review next | C.X → Epic 9 → Epic 4 re-review |

**Rationale for deferring Epic 4 re-review:** Epic 9's build work is expected to surface further small schema course-corrections. Re-reviewing Epic 4 against a not-yet-stable target wastes the review. Better to absorb Epic 9's discoveries first.

---

## Architectural framework — the four-tier schema (LOCKED)

| Tier | Namespace | Scope | Examples | Unlocks |
|---|---|---|---|---|
| **0** | core subset | Floor | `space` (name), `location.address` → derived | Maëlle exits with something valid |
| **1** | SpaceAPI v15 **core** | Common to all SpaceAPI apps | `logo`, `url`, `description`, `contact.*`, `state.*` | Bidirectional interop (mapall.space etc.) |
| **2** | `mom:` | **Horizontal** — most/all networks | `opening_hours`, `memberOf`, `mom:sdgs` | MoM features (membership, hours, SDG filter) |
| **3** | `ext_X` | **Vertical** — silo-specific | `ext_fab.equipment`, future `ext_*` | Niche services / future service surface |

**Renames:**
- `ext_mom` → `ext_canary` (Mother-Sands-only)
- `ext_fab.sdgs` → `mom:sdgs` (SDGs are transversal)
- Cross-network MoM fields like `memberOf` move into `mom:` namespace

**Strategic insight:** Tier 3 is the **open extensibility surface** where future niche/managed services plug in. Aligns with the schema-bundle monetization model.

---

## Key UX decisions (LOCKED — input to story ACs)

1. **No account, no signup.** Sovereignty of identity, key MoM feature.
2. **Drawer composition rule:** every element must justify itself against "does this help her decide in 4 seconds, or does it provoke a question?" If it provokes a question, it goes.
3. **Bernard never appears as a character on screen.** No silhouette, no crab, no fort. Bernard is the **voice of the copy**.
4. **Bernard names themselves (they/them) ONLY on the wizard path**, briefly. Politeness, not a reward. Never in the drawer. Never in the URL shortcut.
5. **Forbidden voice patterns:** "most spaces leave this blank," "keep it simple," any nudge that comforts mediocrity OR shames. Pyramid-of-Greatness register (frankness, sovereignty of choice) **with a grain of salt**.
6. **state.open FSM** — opt-out signal is field **omission**, not a sentinel value. Absence reads as "no live signal" (matches Story 3.3 Axis C).
7. **Logo as GitLab tutorial payload** — the chicken-and-egg ("Maëlle has no hosting") becomes the pedagogy. First commit cycle teaches the whole loop.
8. **Browser localStorage** auto-saves wizard progress; cross-device resume only via URL fetch.

---

## Bernard's calibrated lines (reference for Story 9.5)

| Moment | Line |
|---|---|
| Drawer one-liner | *"Two ways through. [Tell me about your space]. Or paste a URL if you already have one. Either is fine."* |
| Wizard intro | *"Hi, I'm Bernard (they/them) from 'Mother Sands'. Let's get your space on the map."* |
| Floor gate (Tier 0) | *"Name and address. That's the floor. Everything else, I'll derive."* |
| Tier 1 exit | *"Core's in. Other SpaceAPI apps can read this file as-is."* |
| Tier 2 exit | *"MoM fields filled. Network features unlocked: membership, opening hours, SDGs."* |
| Tier 3 exit | *"Silo fields in. Your space's vertical features active."* |
| Sovereignty disclosure | *"You publish, we make it legible. The rest is history."* |
| localStorage warning | *"Your progress is saved in this browser. Hard-refresh or clearing site data wipes it. Export at any point if you want a copy outside the browser."* |

Full register, voice rules, forbidden patterns: see `memory/project_bernard_character.md` and the brainstorming session doc.

---

## Cross-references

- Brainstorming session: `_bmad-output/brainstorming/brainstorming-session-2026-05-29-1500.md`
- Bernard character bible: `_bmad-output/planning-artifacts/mom_handoff_2026-05-15.md` §"Bernard — character bible"
- Story 3.3 three-axis model (Axis C absence semantics): `_bmad-output/planning-artifacts/mom_handoff_2026-05-16.md`
- Schema bundle model (tier 3 = future service surface): `memory/project_schema_bundle_model.md`
- Existing Nominatim pattern: `scripts/normalize_vow.py`
- Canary baseline (genjson reference output): `data/canary/baseline.json`

---

## Recommended next steps (in fresh context)

1. **Apply Cleanup C.X** — small story, write it via `bmad-create-story` or just direct edit. Run wipe/reseed via Makefile. Verify map renders unchanged with new schema.
2. **Update `epics.md`** to insert Epic 9 (via `bmad-edit-prd` on `epics.md`).
3. **Run `bmad-sprint-planning`** to regenerate sprint status including Epic 9.
4. **Create Story 9.1** via `bmad-create-story` — subdomain & infra first.
5. **Defer Epic 4 re-review** until Epic 9 M1+ is in flight.

---

*End of proposal.*
