# Sprint Change Proposal — Epic 3.5 Re-Architecture (snapshot-as-unit)

**Date:** 2026-05-19
**Author:** correct-course workflow (operator: Nicolas)
**Scope classification:** Moderate — spec re-architecture, no code written yet
**Status:** Approved

---

## 1. Issue Summary

Story 3.6 (`dev-story`) was halted during planning. On reviewing the Epic 3.5 and Story 3.6
specs, the operator found them stale relative to intent.

The specs described "carry one `observed_at` token through the *existing* five-stage pipeline"
(endpoint JSON → `heartbeat_log.db` → Oxigraph → `spaces.geojson` → browser). The existing
pipeline is the problem: `heartbeat_log.db` accumulated independently-stamped derived columns
(`last_fetched`, `last_content_updated`, `last_endpoint_health`, `last_lifecycle_state`,
`is_closed`, …) and the transformer stamps "now" at transform time (`transformer.py:402`,
`:521`). That independent stamping IS the retro-3 "pytest passes / live pipeline breaks" bug
class. Grafting a clean token onto that noisy foundation builds clean code on noise.

**Issue type:** misunderstood / stale requirements — the spec did not reflect the intended
architecture.

**Evidence:** `heartbeat_log` schema noise; transform-time stamping at `transformer.py:402/521`;
Story 3.6's own internal tension (simultaneously "carry a token" and "do not change the
pipeline / do not slim GeoJSON").

## 2. Impact Analysis

- **Epic impact:** Epic 3.5 cannot proceed as written — its sequencing premise ("carry token
  through existing 5 stages") is replaced. Narrative + all 5 stories redefined.
- **Story impact:** Story 3.6 rewritten. Stories 3.7–3.10 reframed (descriptions only — no story
  files exist yet; all `backlog`).
- **Artifact conflicts:** `epics.md` (Epic 3.5 section), Story 3.6 file, `data-lifecycle.md`.
  PRD — no conflict (FR24/25/27 still hold; this is an implementation re-architecture, not a
  requirements change). UX — minor (card loads non-render fields on demand; lands Story 3.10).
- **Technical impact:** none yet — no Epic 3.5 code merged. No rollback required.

## 3. Recommended Approach

**Direct Adjustment** — modify Epic 3.5 + Story 3.6 specs in place; 3.7–3.10 reframed as
descriptions. No code rollback (nothing merged).

**The corrected model — the snapshot is the unit.** A successful fetch of a reachable endpoint
produces one snapshot: `{JSON payload + observed_at + space UID}`, the single source of truth.
Every lifecycle fact is derived from it. `observed_at` is minted once, at fetch, carried
byte-identical to the browser.

**Clean rebuild, not a patch.** Story 3.6 builds a new clean snapshot pipeline *alongside* the
existing one, canary-only. The legacy pipeline is untouched (zero regression risk during 3.6).
Stories 3.7–3.10 migrate registered spaces onto the clean path seam by seam and *delete* the
legacy code. Rationale: everything is on git, so a rebuild is reversible; a patched-on-noise
foundation is not. Walking-skeleton discipline is preserved — 3.6 is a thin end-to-end slice of
*new clean code*, not a graft.

Effort: Medium. Risk: Low (parallel path; old code untouched until deleted as a unit).

## 4. Detailed Change Proposals

All six applied 2026-05-19:

1. **`epics.md` — Epic 3.5 narrative block.** Reframed to snapshot-as-unit; added "Clean
   rebuild, not a patch", "Fetch triggers", "What the map carries vs. what the card loads";
   updated "Decisions owed" and scope guard.
2. **`epics.md` — Story 3.6 entry.** Retitled "Walking Skeleton — Clean Snapshot Pipeline on the
   Canary"; ACs rewritten around the snapshot store + minimal GeoJSON + untouched legacy path.
3. **`epics.md` — Stories 3.7–3.10.** Reframed "Harden the … Seam" → "Migrate the … Seam"
   (migrate registered spaces + delete legacy code). GeoJSON slimming moved into Story 3.9.
4. **Story file `3-6-walking-skeleton-observed-at-end-to-end.md`.** Full rewrite to the
   corrected spec — 8 tasks, 11 ACs, dual-pipeline Dev Notes, retained `datetime.now()` audit.
5. **`data-lifecycle.md`.** Added "Epic 3.5 — clean snapshot pipeline (transition state)"
   section with the legacy-vs-clean comparison table; added GeoJSON-slimming → Story 3.9 row to
   the deferred table.
6. **`sprint-status.yaml`.** Updated `last_updated` and the Epic 3.5 comment block. No status
   changes — Story 3.6 stays `ready-for-dev`; 3.7–3.10 stay `backlog`.

## 5. Implementation Handoff

**Scope: Moderate.** Route to Developer agent.

- Story 3.6 is `ready-for-dev` against the corrected spec — run `dev-story 3.6`.
- Stories 3.7–3.10 remain `backlog`; create their story files later via `create-story` (and
  update their `sprint-status.yaml` slug keys to match the new "Migrate …" titles at that time).

**Success criteria:** `epics.md` Epic 3.5 reads coherently end-to-end; Story 3.6 file ACs match
the `epics.md` entry; `data-lifecycle.md` reflects the dual-pipeline transition; no
`sprint-status.yaml` status regressions.
