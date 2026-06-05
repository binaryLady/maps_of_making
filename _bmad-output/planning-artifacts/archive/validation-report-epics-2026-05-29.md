---
validationTarget: '_bmad-output/planning-artifacts/epics.md'
validationDate: '2026-05-29'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - web/maps-of-making.html
validationStepsCompleted: ['format-detection', 'density', 'consistency', 'prd-drift', 'story-quality', 'coverage']
validationStatus: COMPLETE — fixes applied 2026-05-29 (C1, H2, M1, M2, L1; H1 waived; M3 deferred to separate PRD update)
---

# Epic Breakdown Validation Report

**Document Validated:** `_bmad-output/planning-artifacts/epics.md`
**Validation Date:** 2026-05-29
**PRD Cross-Reference:** `_bmad-output/planning-artifacts/prd.md` (lastEdited: 2026-04-29)

## Input Documents

- `_bmad-output/planning-artifacts/prd.md` ✓
- `_bmad-output/planning-artifacts/architecture.md` ✓
- `web/maps-of-making.html` ✓

---

## Format Detection

**Document type:** Epic breakdown (non-standard BMAD PRD format — expected and correct)
**BMAD core sections (PRD-format check):** 0/6 — N/A for this document type
**Validation approach:** Story quality, PRD traceability, internal consistency, PRD drift

**Information Density:** PASS — zero anti-pattern violations found (`grep` returned no results for filler phrases, wordy patterns, or redundant phrases). Dense, technically precise throughout.

---

## Findings

### 🔴 CRITICAL

#### C1 — Epic 9 has no FR backing in the FR Coverage Map

**Location:** FR Coverage Map (lines 249–308), AR Coverage Summary (lines 301–308)

**Issue:** The FR coverage map lists FR1–FR44 mapped to Epics 0–8. Epic 9 (Bernard's Workshop, Stories 9.1–9.11) introduces new capabilities — a JSON composer wizard at `genjson.mapsofmaking.org`, Nominatim proxy endpoint, `state.open` FSM, GitLab tutorial — that have **no corresponding FRs**. The PRD mentions a "LLM-assisted JSON generator" only in the Vision (Post-PoC) section, not as a numbered FR. A downstream dev or story-creator reading the FR coverage map cannot trace Epic 9 stories back to any PRD requirement.

**Impact:** Creates a traceability gap: Epic 9 looks like scope creep unless a reader knows to look at the sprint change proposal. Risks scope challenges from stakeholders.

**Recommended fix:** Add a note after the FR coverage map:

```
**Epic 9 scope note:** Stories 9.1–9.11 implement the "LLM-assisted JSON generator" referenced
in PRD §Vision (Post-PoC). No numbered FRs exist for this capability — it was approved via the
2026-05-29 sprint change proposal. The PRD requires a targeted update to add FRs for Epic 9 when
it moves to active development (pre-Story 9.1 recommended).
```

And add to the AR coverage summary:
```
- AR-INF1 (subdomain/nginx pattern) → Epic 9 (Story 9.1)
- Story C.X → schema prerequisite for Epic 9 + Epic 4 re-review
```

---

### 🟠 HIGH

#### H1 — FR24 cadence contradiction: FR inventory says 6h, Story 3.1 + implementation say 10 min

**Location:**
- FR inventory line 58: `"6-hour cadence, configurable"`
- FR coverage map line 275: `"Periodic endpoint fetch (6h cadence, configurable)"`
- Story 3.1 user story (line 818): `"fetches all registered endpoint URLs every 10 minutes"`
- Story 3.1 AC (line 828): `"Nanobot CronService every 6h, configurable via config.yaml"`
- `infra/link_handler/config.yaml` line 12: `heartbeat_interval_seconds: 600` (= 10 min)
- PRD FR24: `"10-minute cadence, configurable"` ← PRD has the correct value

**Issue:** Three-way inconsistency: the FR inventory says 6h, Story 3.1's user story says 10 min, Story 3.1's AC says 6h. The implementation is 600s (10 min). The PRD (correct source) says 10 min. The FR inventory and Story 3.1 AC are both stale — they predate the heartbeat cadence change.

**Recommended fix:**
1. Update FR24 inventory (line 58): `6-hour cadence` → `10-minute cadence`
2. Update FR coverage map row (line 275): same
3. Update Story 3.1 AC (line 828): `"Nanobot CronService every 6h"` → `"Nanobot CronService every 10 min (600s)"`
4. Update Epic 3 description (line 376, historical but still confusing): note the 6h is superseded

#### H2 — Story 3.0 snapshot path still pinned as canonical, contradicts Epic 3.5 contract

**Location:** Story 3.0 ACs, lines 774, 775, 788

**Issue:** Story 3.0 ACs include:
> `"this path is pinned here and referenced in Epic 4 stories"` for `/data/snapshots/{space_id}/latest.json`

This was true at the time Story 3.0 was written, but the Epic 3 warning block (line 753) explicitly states these disk paths were never built and are superseded by `snapshot_store.db`. The "pinned here" language is now actively misleading — Epic 4 stories reference `snapshot_store.db`, not disk paths. A developer reading Story 3.0 without reading the warning block first gets a false anchor.

**Recommended fix:** Add a strikethrough or inline supersession note to Story 3.0's snapshot path ACs, e.g.:

> ~~`this path is pinned here and referenced in Epic 4 stories`~~ **Superseded by Epic 3.5: snapshots live in `snapshot_store.db` (see Epic 4 Story 4.3). Disk path never built.**

---

### 🟡 MEDIUM

#### M1 — Story 9.3 specifies Playwright; no Playwright in project test infra

**Location:** Story 9.3 gating test (line 1895)

**Issue:** `test_wizard_tier0_tier1_export (Playwright or equivalent, against genjson.mapsofmaking.org staging)` — Playwright is not present in the project (`grep` finds zero Playwright references; `infra/link_handler/conftest.py` uses pytest + httpx pattern). "Or equivalent" provides an out, but the spec-level mention of Playwright sets a false expectation. Genjson is a browser-side JS wizard — it does need browser-level testing, so the need is real, but "pytest + httpx" cannot validate localStorage, file download, or live wizard flow.

**Recommended fix:** Replace `(Playwright or equivalent)` with `(browser E2E test — Playwright or Cypress; new test infra dependency, must be set up as part of Story 9.1 or 9.3)` to make the infra requirement explicit rather than implicit.

#### M2 — Story 9.2 and Story 9.3 have a split ownership gap on `?resume=1` handling

**Location:** Story 9.2 line 1849, Story 9.3 lines 1891–1894

**Issue:** Story 9.2 defines the CTA behaviour: "if `localStorage.getItem('genjson_draft')` exists, open `?resume=1`". Story 9.3 defines localStorage auto-save and draft restoration on page load, but does not mention handling the `?resume=1` URL param. The two stories are consistent in intent but Story 9.3's ACs don't include: "And if `?resume=1` is present in the URL and no localStorage draft exists, the wizard loads at the floor gate (draft was cleared or is cross-device)." This edge case is unspecified.

**Recommended fix:** Add one AC to Story 9.3: `**And** if `?resume=1` is in the URL but `localStorage.getItem('genjson_draft')` is null (draft cleared or cross-device), the wizard loads at Tier 0 with no pre-fill and no error — `?resume=1` is a hint, not a requirement.`

#### M3 — PRD lastEdited 2026-04-29 predates three significant course corrections

**Location:** `_bmad-output/planning-artifacts/prd.md` frontmatter

**Issue:** The PRD has not been updated since 2026-04-29. Three significant course corrections since then are reflected in epics.md but not in the PRD:

| Course correction | PRD text (stale) | epics.md (current) |
|---|---|---|
| Snapshot storage | FR24: "Raw payload stored to disk with timestamp" | `snapshot_store.db` (Epic 3.5) |
| Three-token freshness model | FR25: describes old lifecycle without three-axis model | Epic 3.5 + Story 3.8b |
| FR30/31 inspection panel source | "raw source JSON from last disk snapshot" | `snapshot_store.db.payload` blob via `read_snapshot()` |

The PRD is the upstream document — if a new contributor reads the PRD, they get the old model. The epics.md already has extensive supersession notes, but the PRD is the authoritative requirement source.

**Recommended fix:** Run `bmad-edit-prd` on `prd.md` targeting FR24, FR25, FR30/31 specifically to reflect the three-token model and `snapshot_store.db`. This is a separate action from this validation — flagged here as a tracked follow-up.

---

### 🔵 LOW / INFORMATIONAL

#### L1 — AR coverage summary missing C.X and Epic 9

**Location:** Lines 301–308

**Issue:** The AR coverage summary maps Architecture Requirements (AR-SEED1, AR-INF1, etc.) to epics. It doesn't mention Story C.X or Epic 9. Not a functional gap (both sections self-document their dependencies) but creates an incomplete index.

**Recommended fix:** Add two lines:
```
- AR-INF1 (nginx subdomain pattern) → Epic 9 Story 9.1
- Story C.X (schema namespace pass) → prerequisite for Epic 9 + Epic 4 re-review (no AR number — architectural cleanup)
```

#### L2 — Epic 3 description (historical) still says "6h cycle" and "disk write"

**Location:** Lines 376, 760

**Issue:** The Epic 3 preamble text (marked as pre-3.5 historical with the warning block) still says "Heartbeat scheduler runs the full 6h cycle" and "raw snapshot written to disk before any transformation". These are covered by the warning block but the preamble text itself isn't annotated. A skim-reader may miss the warning block.

**No fix required** — the warning block is clear and prominent. Informational only.

#### L3 — Story 0.3 references `<urn:mak:status>` graph (pre-3.5 historical)

**Location:** Line 487

**Issue:** Story 0.3 AC: `"the status scheduler job (<urn:mak:status>) is updated with materialized status triples for all imported spaces"`. This graph was never built (superseded by Epic 3.5). However, Story 0.3 is in the pre-3.5 historical section and the Epic 3 warning block covers this.

**No fix required** — informational trail only.

---

## Story Quality Summary — New Sections

### Story C.X: Schema Namespace Pass ✅
- User story: well-formed
- BDD ACs: complete Given/When/Then throughout
- Gating test: named (`test_namespace_pass`), live integration, operator visual confirmation required
- Dependencies: correctly stated (blocks Epic 9 + Epic 4 re-review)
- Measurable: `grep` zero-result check + `ASK {}` SPARQL verification
- **Quality: High**

### Epic 9 — Stories 9.1–9.8 (M1 + M2) ✅
| Story | User Story | BDD | Gating Test | Quality |
|---|---|---|---|---|
| 9.1 Subdomain | ✅ | ✅ | ✅ (curl + browser) | High |
| 9.2 Drawer UX | ✅ | ✅ | ✅ (axe-core + visual) | High |
| 9.3 Wizard core | ✅ | ✅ | ✅ (Playwright — see M1) | High* |
| 9.4 Nominatim proxy | ✅ | ✅ | ✅ (live + rate-limit) | High |
| 9.5 Bernard voice | ✅ | ✅ | ✅ (completeness test + human gate) | High |
| 9.6 Tier 2 fields | ✅ | ✅ | ✅ (Oxigraph triple check) | High |
| 9.7 state.open FSM | ✅ | ✅ | ✅ (three-path E2E) | High |
| 9.8 GitLab tutorial | ✅ | ✅ | ✅ (manual M2 acceptance test) | High |

*Story 9.3 flagged under M1 (medium finding).

### Epic 9 — Stories 9.9–9.11 (M3, deferrable) ℹ️
M3 stories are intentionally less detailed — they are deferred until M2 is validated with real coordinators. Story 9.9 (URL pre-fill + validator mode) is the most complete of the three; 9.10 and 9.11 are appropriately stub-level for deferred scope. No quality issues for M3 given the deferral intent.

---

## PRD Drift Summary

| PRD section | Status | Action needed |
|---|---|---|
| FR24 cadence (10 min) | Stale in epics.md FR inventory | Fix in epics.md (H1 above) |
| FR25 three-axis model | Partially stale in PRD | PRD update (M3 above) |
| FR30/31 disk snapshot source | Stale in PRD | PRD update (M3 above) |
| Vision: JSON generator | ✅ Delivered as Epic 9 | Add PRD note (C1 above) |
| All user journeys | ✅ Covered | No action |
| All FR1–FR44 except FR24 | ✅ Covered | FR24 fix only |

---

## Recommended Actions — Priority Order

| # | Severity | Action | Effort |
|---|---|---|---|
| 1 | 🔴 Critical | Add Epic 9 FR scope note to FR Coverage Map + AR Coverage Summary | 5 min |
| 2 | 🟠 High | Fix FR24 cadence: `6h` → `10 min` in FR inventory (line 58), coverage map (line 275), Story 3.1 AC (line 828) | 5 min |
| 3 | 🟠 High | Annotate Story 3.0 snapshot path ACs as superseded (not just the epic-level warning) | 5 min |
| 4 | 🟡 Medium | Add browser E2E test infra note to Story 9.3 (Playwright as explicit new dependency) | 2 min |
| 5 | 🟡 Medium | Add `?resume=1` edge-case AC to Story 9.3 | 2 min |
| 6 | 🟡 Medium | Schedule PRD update for FR24/FR25/FR30/FR31 (separate `bmad-edit-prd` on prd.md) | 30 min |
| 7 | 🔵 Low | Add C.X and Epic 9 to AR Coverage Summary | 2 min |

**Total quick fixes (1–5, 7):** ~20 minutes in epics.md
**Deferred:** PRD update (action 6) — separate workflow

---

## Validation Verdict

**`epics.md` (post-2026-05-29 edits): PASS WITH FINDINGS**

The document is structurally sound, internally consistent at the story level, and the new sections (C.X + Epic 9 M1/M2) are at full BDD-spec quality. Seven findings identified: one critical (traceability gap for Epic 9), two high (FR24 cadence stale, Story 3.0 path annotation), two medium (test infra + edge case AC), one medium deferred (PRD update), one low (AR coverage index).

The critical and high findings are fast edits (< 15 min combined). The PRD update is a separate tracked action.
