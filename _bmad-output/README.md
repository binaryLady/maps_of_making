# `_bmad-output/` — structure & index

The BMAD working record for Maps of Making. Two halves:

- **`planning-artifacts/`** — the *what & why*. Durable design intent: requirements, epics,
  architecture, UX, character. These are **living references** unless marked historical.
- **`implementation-artifacts/`** — the *how it went*. Per-story execution record: one file per
  story, plus retros, specs, code reviews, and the status ledger. These are **append-only
  history** — completed story files are not edited after they ship.

Two files outside both folders:

| File | Role |
|------|------|
| `feature-requests-whatsapp.md` | Raw user-need backlog (Nicolas × Jason); `[NEW]` = not yet in epics |
| `brainstorming/` | Pre-planning ideation sessions (dated) |

> **Source of truth for status is [`implementation-artifacts/sprint-status.yaml`](implementation-artifacts/sprint-status.yaml).**
> If this README and `sprint-status.yaml` disagree on what's done, the YAML wins.

---

## planning-artifacts — current authoritative set

Read these first when picking up the project.

| File | What it is |
|------|-----------|
| `prd.md` | Product requirements (FRs/NFRs) — root reference |
| `epics.md` | Epic + story breakdown — the planning backbone |
| `architecture.md` | System architecture (superset; the trail in `docs/architecture/` is the navigable cut) |
| `data-lifecycle.md` | Pipeline design narrative (rendered from `26.05.17_data-lifecycle.excalidraw`) |
| `ux-bernard-wizard-spec.md` | Epic 9 wizard UX spec — **9.12 frame is locked here** |
| `bernard-bible.md` | Bernard character/voice reference — living |
| `schema-roleplay-personas.md` | Bundle-model personas (Epic 10 schema work) |
| `mom-schema-architecture-handoff.md` | Schema-layer architecture (core/mom/concept-commons/community) |

## planning-artifacts — historical (point-in-time; kept for provenance)

Snapshots of a decision *as it was made*. Do not treat as current; they're superseded by the
authoritative set above. Dated in filename or content.

| File | Superseded by / status |
|------|------------------------|
| `mom_handoff_2026-05-15.md` | Story 3.3 narrowing era — folded into 05-16 handoff |
| `mom_handoff_2026-05-16.md` | Three-axis canary handoff — now lives in code + `docs/canary-*.md` |
| `sprint-change-proposal-2026-05-19.md` | snapshot-as-unit — **superseded same day** by `-19b` |
| `sprint-change-proposal-2026-05-19b.md` | three-token model — **this is the one that shipped** (Epic 3.5) |
| `sprint-change-proposal-2026-05-29.md` | Epic 9 "Bernard's Workshop" + pre-epic schema cleanup — enacted |
| `validation-report-epics-2026-05-29.md` | Epic validation snapshot for the 05-29 proposal |
| `26.05.17_data-lifecycle.excalidraw` | Diagram source for `data-lifecycle.md` |

---

## implementation-artifacts — the ledger

| File | Role |
|------|------|
| `sprint-status.yaml` | **Status source of truth** — epic/story state, cross-epic handoffs |
| `deferred-work.md` | Active carried-forward backlog — triage before each story creation |

### Story files

One `N-M-slug.md` per story. Status lives in each file's header **and** in `sprint-status.yaml`.
Epic 0–3.5 + 9 are largely `done`; Epic 4/4b/5/6/10 stories are mostly `backlog` and may not have
files yet (a backlog key with no file is normal).

### Retros, specs, reviews

| Pattern | Role |
|---------|------|
| `epic-N-retro-*.md` | Per-epic retrospective |
| `spec-*.md` | Standalone investigation specs (`spec-3-2-heartbeat-staleness`, `spec-infra-nginx-new-domains`) |
| `*-code-review.md` | Review records (`0-3-code-review`) |
| `cx-schema-namespace-pass.md` | Cross-cutting cleanup (the "C.X" prereq) |
| `drift-investigation-complete.md` | Epic-0-era SVG-marker drift investigation (resolved) |

---

## ⚠️ Triage findings (2026-06-05)

Flagged here rather than deleted — BMAD artifacts are provenance. Resolve when convenient.

1. **Superseded story duplicates (token-model rewrites).** Two stories were rewritten mid-flight;
   the old files remain alongside the new:
   - `3-8-transformer-emits-mom-observedat.md` (old model) → **superseded by** `3-8b-corrected-token-model.md`
   - `3-9-materializer-propagates-observed-at-to-geojson.md` (header says `Status: depreciated`)
     → **superseded by** `3-9-materializer-three-tokens-geojson.md`

   *Disposition:* keep both (history), but the `-propagates-` / non-`b` files are dead. Safe to
   delete if you want a clean stories list; the retro + sprint-status already record the pivot.

2. **Orphaned Story 4.0 draft + name mismatch.** `4-0-admin-foundation-subdomain-auth-space-comparison.md`
   (`Status: draft`) is an **earlier, abandoned conception** of Story 4.0. The current Story 4.0 in
   `epics.md` is *"Epic 4 Prep — Consolidate Materializers, Verify Seed Tokens, Add Stall Threshold"*,
   tracked in `sprint-status.yaml` as the key `4-0-epic-4-prep-…` — which **has no file on disk**.

   *Disposition:* either (a) rename/rewrite the draft to match the prep story before Epic 4 kickoff,
   or (b) archive the draft and let `create-story` mint the real `4-0-epic-4-prep-…` file fresh.
   Do **not** leave both conceptions ambiguous when Epic 4 starts.

3. **Sub-artifact, not a story:** `3-6-datetime-audit.md` is a supporting audit under Story 3.6
   (`3-6-walking-skeleton-observed-at-end-to-end.md`), not a separate story. Correctly classified —
   noted here so the two `3-6-*` files aren't mistaken for a duplicate.
