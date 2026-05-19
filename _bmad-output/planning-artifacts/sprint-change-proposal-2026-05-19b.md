# Sprint Change Proposal — Epic 3.5 Three-Token Freshness Model

**Date:** 2026-05-19
**Author:** correct-course workflow (operator: Nicolas)
**Scope classification:** Moderate — spec re-architecture, Story 3.8 superseded by 3.8b
**Status:** Approved

---

## 1. Issue Summary

Story 3.9 planning surfaced that Story 3.8 (`done`) implemented the **wrong token model**:
a single `observed_at` token was written to Oxigraph to answer two unrelated questions —
"is the endpoint reachable?" (Axis A) and "is the content maintained?" (Axis B). These have
different update triggers and cannot be the same token.

The Retro 3 "multi-cache authority" bug has a deeper form: derived buckets (`operationalState`,
`endpointHealth`) were frozen into Oxigraph at transform time and go stale the instant they're
written. These are `f(timestamp, now, thresholds)` — they must be computed at consumption time
(browser), not stored.

**Trigger:** Story 3.9 (as written) reads `mom:observedAt` back *out of Oxigraph* — a value
Story 3.8 wrote into Oxigraph at fetch time. That round-trip is the bug: Oxigraph is not the
authority for fetch-time reachability observations. SQLite (`snapshot_store.db`) is.

**Approved plan:** `/home/nicolas/.claude/plans/wondrous-tickling-marble.md`

## 2. Impact Analysis

| Area | Impact |
|---|---|
| Story 3.8 | `done` under old model — superseded by 3.8b; code is the starting point for 3.8b |
| Story 3.8b | New story (ready-for-dev) — corrects transformer to three-token model |
| Story 3.9 | `ready-for-dev` — fully rewritten; old file archived |
| Story 3.10 | `backlog` — description updated for three-axis browser computation |
| Epic 3.5 narrative | "freshness token" section replaced with three-token model |
| PRD | No change — FR24/25/27 still hold |

## 3. The Corrected Model

**Three tokens, three axes:**

| Token | Minted by | Advances when | Home | Axis |
|---|---|---|---|---|
| `observed_at` (ISO-8601) | us | every responsive fetch (200 or 304) | SQLite `snapshot_store.db` | A — endpoint health |
| `updated_at` (ISO-8601) | us, on content diff | content JSON meaningfully differs | Oxigraph `mom:updatedAt` | B — content maintenance |
| `state.lastchange` (Unix s) | the space (source claim) | they flip open/closed | Oxigraph `mom:lastOpenChange` (already exists) | C — operational liveness |

**Ingestion truth table:**

| Fetch | `observed_at` (SQLite) | Oxigraph write | `updated_at` |
|---|---|---|---|
| 304 | advance | **none** | unchanged |
| 200 content identical | advance | **none** | unchanged |
| 200 content changed | advance | DROP+INSERT | set to now |

**Principle:** storage holds facts; `operationalState`/`endpointHealth` computed at consumption
time from tokens + `config.yaml` thresholds (shipped in GeoJSON header).

## 4. Applied Changes

All applied 2026-05-19:

1. **`epics.md` — Epic 3.5 narrative.** "Freshness token" section replaced with three-token
   table, ingestion truth table, and "storage holds facts" principle.

2. **`epics.md` — Story 3.8 entry.** Annotated `(done — old model)` with note it is superseded
   by Story 3.8b.

3. **`epics.md` — Story 3.8b entry.** New story added: "Correct the Transformer Seam —
   Three-Token Model". ACs: stop writing `mom:observedAt`/`operationalState`/`endpointHealth`;
   add `mom:updatedAt` on content-changed path only; delete `build_state_only_update`; add
   `state` block to `_IGNORED`; clean up `_read_space_metadata` and `content_changed` param.

4. **`epics.md` — Story 3.9 entry.** Retitled "Materializer Joins SQLite+Oxigraph — Three
   Tokens in GeoJSON". ACs: SPARQL drops old tokens; materializer joins SQLite for `observed_at`;
   three tokens + `thresholds` block in GeoJSON; `_run_clean_canary_pipeline` deleted.

5. **`epics.md` — Story 3.10 entry.** Updated ACs for three-axis live computation: Axis A from
   `observed_at` + fetch status, Axis B from `updated_at`, Axis C from `last_open_change`/`open_now`;
   thresholds from GeoJSON header; coordinator notifications on bucket transitions.

6. **Story file `3-8b-corrected-token-model.md`.** New story file — 8 tasks, 8 ACs, full dev
   notes including `_IGNORED` set, `build_state_only_update` deletion, backward compatibility
   for pre-3.8b Oxigraph data.

7. **Story file `3-9-materializer-three-tokens-geojson.md`.** Complete rewrite — 9 tasks, 10
   ACs, dev notes for SQLite join pattern, config thresholds shipping, canary pipeline removal.
   Old file (`3-9-materializer-propagates-observed-at-to-geojson.md`) archived in place.

8. **`sprint-status.yaml`.** Story 3.8 annotated `# old model — superseded by 3-8b`;
   `3-8b-corrected-token-model: ready-for-dev` added; `3-9-materializer-three-tokens-geojson:
   ready-for-dev` added (old key remains as a historic record, status: done is NOT set for it).

## 5. Implementation Handoff

**Scope: Moderate.** Route to Developer agent.

Sequence (mandatory order — each story's Oxigraph state is the next story's input):
1. **`dev-story 3.8b`** — correct transformer; zero Oxigraph writes on 304/unchanged
2. **`dev-story 3.9`** — materializer joins SQLite+Oxigraph; three tokens in GeoJSON
3. **`dev-story 3.10`** — browser computes three axes live

**Success criteria:**
- `mom:observedAt`, `mom:operationalState`, `mom:endpointHealth` absent from Oxigraph
- `mom:updatedAt` present in Oxigraph only for spaces with real content diffs
- `spaces.geojson` features carry `observed_at` (from SQLite), `updated_at` (from Oxigraph),
  `last_open_change`, `open_now`
- File-level `thresholds` block present in `spaces.geojson`
- Browser computes all three axes live; no stored bucket fields in GeoJSON
- Full pytest suite green; operator visual confirmation on live canary for each story
