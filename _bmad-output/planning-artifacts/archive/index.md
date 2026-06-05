# Planning-Artifacts Archive

Consumed / superseded point-in-time documents, moved here on **2026-06-05** during the
artifact-alignment correct-course. They are **historical record** — their still-live decisions
have been folded into the active artifacts (see "Consumed into" column). They live here, **out of
the BMAD discovery glob path**, so `create-story` / `create-epic` / `correct-course` can never
auto-load them as if they were current.

> **Do not edit these to "update" them.** If a decision they describe is still relevant, it belongs
> in `architecture.md`, `prd.md`, or `epics.md` (the BMAD-native detail layer) — or in
> `docs/architecture/` (the onboarding abstraction layer). See [[project_doc_layer_model]].

## Why these were archived

Two were active **glob poisoners** — they matched BMAD's filename discovery and were being
FULL_LOADed as if authoritative:

| File | Matched glob | Loaded as |
|---|---|---|
| `mom-schema-architecture-handoff.md` | `*architecture*.md` | a second "Architecture" doc |
| `validation-report-epics-2026-05-29.md` | `*epic*.md` | a second "Epics" doc |

The rest are consumed handoffs / applied change-proposals kept for provenance.

## Contents

| File | Date | What it was | Status | Consumed into |
|---|---|---|---|---|
| `mom_handoff_2026-05-15.md` | 2026-05-15 | Story 3.3 narrowing + Epic 8 stub + Bernard lore | superseded by the 05-16 brief | `epics.md` Epic 8 stub; `bernard-bible.md` |
| `mom_handoff_2026-05-16.md` | 2026-05-16 | Story 3.3 Mother Sands three-axis canary (party-mode roundtable) | consumed — Story 3.3 done | `epics.md` Epic 3.5 / Story 3.3 (done); `architecture.md` ADR-004/006 |
| `mom-schema-architecture-handoff.md` | 2026-05-16 | Three/four-layer schema architecture + OMT community track | consumed; `w3id.org` IRIs were illustrative | `architecture.md` **ADR-016**; `ontology/` (`core.ttl`, `crosswalk.csv`); `schema-roleplay-personas.md` (companion, still live) |
| `sprint-change-proposal-2026-05-19.md` | 2026-05-19 | Epic 3.5 re-architecture (snapshot-as-unit) | approved + applied | `epics.md` Epic 3.5; `architecture.md` Epic 3.5 section |
| `sprint-change-proposal-2026-05-19b.md` | 2026-05-19 | Epic 3.5 three-token freshness model | approved + applied | three-token contract now live across `architecture.md` / `prd.md` / `epics.md` |
| `sprint-change-proposal-2026-05-29.md` | 2026-05-29 | Epic 9 "Bernard's Workshop" + pre-epic schema cleanup | applied — Epic 9 exists | `epics.md` Epic 9; `ux-bernard-wizard-spec.md` |
| `validation-report-epics-2026-05-29.md` | 2026-05-29 | Epic-breakdown validation report (fixes applied) | complete — point-in-time | fixes already in `epics.md` |
| `data-lifecycle.md` + `26.05.17_data-lifecycle.excalidraw` | 2026-05-17 | Story 3.4b data-lifecycle mermaid flow + source | superseded | `docs/architecture/01-walking-skeleton.md` + `09-seeding-model.md` (live replacement) |

## Note on inbound links

Some **done-story** annotations in `epics.md` still cite these by their old root path (e.g.
`mom_handoff_2026-05-16.md`). Those citations were intentionally left untouched (done-story bodies
are historical record); the files now resolve under `archive/`. This index is the lookup map.
