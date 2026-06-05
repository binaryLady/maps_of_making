# Sprint Change Proposal — Artifact Alignment & Staleness Containment

**Date:** 2026-06-05
**Author:** correct-course workflow (operator: Nicolas)
**Scope classification:** Moderate — documentation governance; no code, no epic scope change
**Status:** Executed slice-by-slice with review; pending final sign-off
**Mode:** Incremental

---

## 1. Issue Summary

The large tech-writing session (2026-06-03 → 06-05) produced a fresh, dead-code-pruned
architecture set in `docs/architecture/01–09`. That created a **staleness-reintroduction risk**:
the fresh truth lived where the BMAD workflows never read, while older artifacts in
`_bmad-output/planning-artifacts/` — matched by filename glob — were being auto-loaded as
authoritative by `create-story` / `create-epic` / `correct-course`.

**Evidence — what the discovery globs pulled before this change:**

| Glob | Files loaded | Problem |
|---|---|---|
| `*architecture*.md` | `architecture.md` (1066-line monolith) **+** `mom-schema-architecture-handoff.md` | stale monolith + a corrections-laden handoff, both as "Architecture" |
| `*epic*.md` | `epics.md` **+** `validation-report-epics-2026-05-29.md` | a point-in-time report loaded as "Epics" |
| `*prd*.md` | `prd.md` (05-16) | predates the Epic 3.5 pivot |
| (none) | `docs/architecture/01–09` | the fresh truth was **invisible** to every workflow |

## 2. Impact Analysis

- **Epic impact:** none. Epics 0–3.5 done; 9.8 done. No scope, sequencing, or AC changes to live backlog.
- **Artifact impact:** `architecture.md`, `prd.md`, `epics.md` carried superseded mechanics
  (snapshot-to-disk, `<urn:mak:status>`, 6h cron, `w3id.org` IRIs, `mak-scheduler`/`metrics.db`).
- **Doc-model clarification (foundational):** two intentional altitudes, **consistent not identical** —
  `docs/architecture/` = onboarding abstraction (teammate-facing, diagram-level); `planning-artifacts/`
  = BMAD-native detailed decisions (agent context). Not a "triple source of truth" violation.
- **Trim rule:** cut **superseded / abandoned** choices; **keep not-yet-built planned** work
  (Nanobot/NL-bot = Epic 6, magic link = Epic 4b, open-now = Epic 7).

## 3. Recommended Approach

**Direct Adjustment (executed):** reconcile the three BMAD-native artifacts in place and move all
consumed point-in-time docs out of the glob path. No rollback, no MVP change. Reviewed slice by slice.

## 4. Detailed Changes (applied)

**Slice 1 — `architecture.md`** (−57 lines net): ADR-004/006 → three-token, browser-computed;
ADR-015 disk stages → SQLite snapshot store (mapping table kept); ADR-008 marked **superseded by
ADR-013** (Nanobot); ADR-012 metrics flagged → Epic 4; named-graph table → three-graph model;
`w3id.org` → canonical `nicolasdb.github.io`; project-structure tree + requirements map + compose
topology + Data Flow diagram rewritten to the real runtime (`infra/link_handler/`,
`scripts/spaceapi_extract/`, `web/data/spaces.geojson`); Epic 3.5 migration marked complete; stale
superseding banners removed once their sections were corrected. Planned Epic 6/4b/7 retained.

**Slice 2 — `prd.md`** (−4 lines net): core principle + FR14b/FR24/FR27b/FR31 → SQLite receipt +
DROP/INSERT-on-change; FR25 marker **computed in browser** (dropped `transformer.effective_marker`);
FR25b Story-3.2c drift marked resolved; NFR-R3 cadence **6h → ~10min**; removed 2 stray BMAD
`**Select:**` workflow prompts. No requirement scope changed.

**Slice 3 — `epics.md`** (6 line-replacements): forward-reference sections only — FR14b
(Requirements Inventory + traceability), `AR-DATA4` (w3id → canonical), `AR-METR1`
(`metrics.db` → `snapshot_store.db`), `AR-AGT2` (heartbeat is `link_handler`, not Nanobot), Epic 6
NL-bot AC (`<urn:mak:status>` → `space`/`canary`). **Done-epic story bodies left intact** (historical
record, already annotated as superseded).

**Slice 4 — archive moves + glob hygiene:** `git mv` of 7 consumed docs →
`planning-artifacts/archive/` with an `index.md` lookup map. `*architecture*` and `*epic*` globs now
resolve to exactly one live file each.

| Archived | Reason |
|---|---|
| `mom-schema-architecture-handoff.md` | glob poisoner (`*architecture*`); folded into ADR-016 |
| `validation-report-epics-2026-05-29.md` | glob poisoner (`*epic*`); fixes already in epics.md |
| `mom_handoff_2026-05-15.md` · `mom_handoff_2026-05-16.md` | consumed handoffs |
| `sprint-change-proposal-2026-05-19.md` · `-19b.md` · `-29.md` | approved + applied |

## 5. Implementation Handoff

**Scope: Minor → Moderate.** Changes are already applied to the working tree (clean, reviewed).

- **No `sprint-status.yaml` change** — no epic added/removed/renumbered.
- **Open follow-ups (operator decision):**
  - `data-lifecycle.md` (05-17, Story 3.4b) appears superseded by `docs/architecture/01` + `09` —
    archive or keep? (No glob risk either way.)
  - `schema-roleplay-personas.md` cites the now-archived schema handoff as "companion" — update the
    link to `archive/`?
- **Commit:** awaiting explicit approval (commit timing rule).

## Success Criteria

- ✅ `create-story` can only load current architecture/epics/prd.
- ✅ Fresh `docs/architecture/` left intact as the onboarding abstraction.
- ✅ No planned (Epic 6/4b/7) work cut.
- ✅ Provenance preserved (archive + index, `git mv` history).
