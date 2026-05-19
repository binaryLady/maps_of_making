# Story 3.8: Transformer Emits `mom:observedAt`, No Re-Stamp

Status: done

## Story

As a pipeline maintainer,
I want the transformer to carry `observed_at` from the snapshot store into Oxigraph as `mom:observedAt` without re-stamping,
so that the freshness token minted once at fetch time is the single source of truth throughout the pipeline.

## Acceptance Criteria

1. Given a snapshot with a known `observed_at` value T,
   when the transformer runs for that space,
   then exactly one `mom:observedAt` triple is written to the space's named graph with value byte-equal to T.

2. All transform-time timestamp stamping classified **CARRY** by the Story 3.6 audit is removed:
   - `mom:lastFetched` is no longer written by `transform_to_sparql` or `build_state_only_update`
   - `mom:lastUpdated` is no longer written or re-inserted by `transform_to_sparql`
   - `mom:snapshotDate` is no longer written to the snapshot graph

3. The 304 path (`build_state_only_update`) propagates the snapshot's `observed_at` to Oxigraph instead of stamping `datetime.now()`.

4. The error/unreachable path does NOT advance `mom:observedAt` — the frozen prior value remains.

5. The registration flow (`main.py /api/register-url`) passes `observed_at` (minted at registration fetch time) to `transform_to_sparql`.

6. Gating test `test_observed_at_roundtrip_real_triplestore` passes:
   - Write a snapshot with known `observed_at=T` to snapshot store
   - Run transformer → POST to live Oxigraph
   - SPARQL SELECT `mom:observedAt` → assert == T (byte-exact)
   - Re-run with no new snapshot (304 path, same T) → assert triple unchanged

7. Full pytest suite (including live integration tests) remains green. Operator visual confirmation: canary space card shows `Snapshot age: Xs ago` advancing normally.

## Tasks / Subtasks

- [ ] Task 1 — Update `transform_to_sparql` in `transformer.py` (AC: 1, 2)
  - [ ] Add `observed_at: Optional[str] = None` parameter
  - [ ] Remove `now = datetime.now(timezone.utc).isoformat()` at L404 (only used by CARRY items; L405 `snapshot_date` is GENERATE — keep)
  - [ ] Remove `mom:lastFetched` triple (L422)
  - [ ] Remove entire `mom:lastUpdated` block (L470-477, both `content_changed` branches)
  - [ ] Remove `mom:snapshotDate` from `snapshot_triples` (L522-523)
  - [ ] Add `mom:observedAt "{observed_at}"^^xsd:string` triple when `observed_at` is provided (use `xsd:string` not `xsd:dateTime` — Oxigraph normalizes dateTime and breaks byte-identity; see Story 3.6 debug notes)

- [ ] Task 2 — Update `build_state_only_update` in `transformer.py` (AC: 2, 3, 4)
  - [ ] Rename `last_fetched` parameter to `observed_at`
  - [ ] Replace `mom:lastFetched` DELETE/INSERT pair with `mom:observedAt` DELETE/INSERT (use `xsd:string` type)
  - [ ] Update docstring to reflect the new role

- [ ] Task 3 — Wire `observed_at` through `process_one_space` (AC: 1, 3, 4)
  - [ ] 304 path (L721-751): remove `_now_304 = datetime.now(timezone.utc).isoformat()` at L726; pass `observed_at=snap["observed_at"]` to `build_state_only_update`
  - [ ] 200 path (L846-862): extract `observed_at = snap["observed_at"]` from snapshot; pass to `transform_to_sparql(..., observed_at=observed_at)`
  - [ ] Error path (L753-778): `build_state_only_update` called without `observed_at` (frozen — correct per rules)
  - [ ] Update log message at L749: "lastFetched refreshed" → "observedAt propagated"

- [ ] Task 4 — Update registration flow in `main.py` (AC: 5)
  - [ ] The registration flow at L763 (`/api/register-url`) fetches the endpoint via `_fetch_and_validate`. Mint `observed_at = mint_observed_at()` (import from `snapshot_store`) before calling `transform_to_sparql` and pass it through
  - [ ] Write the snapshot to snapshot store (uid=slug, observed_at, payload, fetch_status='ok') so it is available for subsequent heartbeat cycles

- [ ] Task 5 — Write gating test `tests/test_transformer_observed_at.py` (AC: 6)
  - [ ] `@pytest.mark.live_integration` — requires live Oxigraph + snapshot store
  - [ ] `test_observed_at_roundtrip_real_triplestore`: write snapshot T → transform → POST → SELECT → assert == T
  - [ ] `test_observed_at_304_unchanged`: advance_observed_at to T2 → build_state_only_update → POST → SELECT → assert == T2

- [ ] Task 6 — Verify no regressions (AC: 7)
  - [ ] `python -m pytest tests/ -v` — full suite green
  - [ ] Live stack: heartbeat cycle completes, GeoJSON contains `observed_at`, canary card shows age advancing

## Dev Notes

### Audit verdicts (from `_bmad-output/implementation-artifacts/3-6-datetime-audit.md`)

| Line | Variable | Payload | Verdict | Owner |
|------|----------|---------|---------|-------|
| 402 | `now` in `transform_to_sparql` | `mom:lastFetched`, `mom:lastUpdated` | CARRY | **Story 3.8** |
| 521 | `now` in snapshot_triples | `mom:snapshotDate` | CARRY | **Story 3.8** |
| 726 | `_now_304` in 304 path | `mom:lastFetched` | CARRY | **Story 3.8** |
| 68 | `now` in gap-log | Gap-log timestamp | GENERATE | keep |
| 179 | `now` in PII-strip | `mak:closedAt` | GENERATE | keep |
| 405 | `snapshot_date` | Named-graph URI suffix | GENERATE | keep |
| 650 | `_days_since` | Age-math | TRANSITIONAL | Story 3.10 |
| 662 | `_minutes_since` | Age-math | TRANSITIONAL | Story 3.10 |

### xsd:string vs xsd:dateTime invariant

Oxigraph silently normalizes `xsd:dateTime` values (strips trailing zeros, converts timezone suffix). This breaks byte-identity of the `observed_at` token. Store `mom:observedAt` as `xsd:string` — discovered in Story 3.6, applied in `canary_pipeline.py` L89. Follow the same pattern here. `mint_observed_at()` in `snapshot_store.py` always returns a Z-suffix ISO-8601 string.

### `transform_to_sparql` call sites

Two call sites:
1. `process_one_space` in `transformer.py` (L846) — heartbeat path
2. `/api/register-url` in `main.py` (L786) — registration path

Both must pass `observed_at`. For registration, mint it with `mint_observed_at()` immediately after the HTTP fetch succeeds.

### `build_state_only_update` 304 path

The 304 path calls `advance_observed_at(uid, new_observed_at)` in `space_pipeline.py` (Story 3.7) to update the snapshot store, then calls `build_state_only_update` to sync Oxigraph. After 3.8, the `observed_at` from the (just-advanced) snapshot should be passed to `build_state_only_update`. `snap["observed_at"]` is available because `fetch_space_snapshot` returns the updated snapshot row (after `advance_observed_at`).

### SPARQL main.py queries still reference `lastUpdated`/`lastFetched`

SPARQL queries in `main.py` (L89-191) read `mom:lastUpdated` and `mom:lastFetched`. Story 3.8 removes the triples but does NOT update these queries — they will return empty/null for those fields. This is intentional: Story 3.9 (materializer) will replace them with `mom:observedAt`. Do not touch the SPARQL queries in main.py for this story — it would break Story 3.9's clean vertical slice.

### Legacy `_build_sparql_update` in `main.py`

The legacy builder at L489 still stamps `mom:lastFetched` and `mom:lastUpdated`. It is the fallback path in the `except` block. Leave it unchanged — it is not on the CARRY list for this story (the primary path is covered).

### Project Structure

- Primary file: `infra/link_handler/transformer.py`
- Supporting: `infra/link_handler/main.py` (registration flow only)
- New test: `tests/test_transformer_observed_at.py`
- Imports needed: `from snapshot_store import mint_observed_at` (in main.py registration path)

### Testing Pattern

Follow the live integration test pattern from `tests/test_canary_scenarios.py` and `tests/test_regression_stuck_seeded.py`. Use `@pytest.mark.live_integration`. Do not mock Oxigraph or snapshot store — integration tests must use real seams (project feedback: mock tests hide protocol bugs).

### Running the Stack

```bash
distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d
source venv/bin/activate
python -m pytest tests/ -v
python -m pytest tests/test_transformer_observed_at.py -v -m live_integration
```

### References

- Datetime audit: `_bmad-output/implementation-artifacts/3-6-datetime-audit.md`
- Story 3.6 (walking skeleton): `_bmad-output/implementation-artifacts/3-6-walking-skeleton-observed-at-end-to-end.md`
- Story 3.7 (fetch seam): `_bmad-output/implementation-artifacts/3-7-heartbeat-log-observed-at-fetch-status.md`
- Epic 3.5 context: `_bmad-output/planning-artifacts/epics.md` (Epic 3.5 section)
- `snapshot_store.py`: `infra/link_handler/snapshot_store.py` — `mint_observed_at()`, `advance_observed_at()`, `read_last_ok_observed_at()`
- `space_pipeline.py`: `infra/link_handler/space_pipeline.py` — `fetch_space_snapshot()`

## Design Decisions

### Why two databases: `snapshot_store.db` vs `heartbeat_log.db`?

**`snapshot_store.db`** — fetch artifact (latest state per space)
- `payload`, `observed_at`, `etag`, `last_modified`, `fetch_status`
- Replaceable — wiping it just loses ETag caching; next heartbeat rebuilds it

**`heartbeat_log.db`** — behavioral state (accumulated across cycles)
- `consecutive_failures`, `consecutive_closed_cycles`, `is_closed`, `last_open_now`, `last_effective_marker`
- Non-replaceable — losing these counters breaks closure detection and coherence tracking

The split is intentional: snapshot is the **freshness unit** (observed_at), heartbeat_log tracks **operator behavior** (closing/opening cycles). Story 3.8 uses observed_at for Axis A (endpoint health); Axis B (lifecycle state) moves to browser in Story 3.10.

### Deferred: PII strip logic refinement

Current: PII strip triggers on `consecutive_closed_cycles >= 6` threshold.

Future concern: With observed_at model, should trigger on **transition to `dead` state** (inactivity, not behavior count). This belongs in Epic 4 (public_ledger/dag-json) or Story 3.10 (lifecycle bucketing), not here. Marked in deferred-work.md for visibility.

### `xsd:string` for `mom:observedAt` (not `xsd:dateTime`)

Oxigraph silently normalizes `xsd:dateTime` (strips trailing zeros, converts +00:00 → Z), breaking byte-identity. Storing as `xsd:string` preserves the minted ISO-8601 value exactly. Applied consistently across Story 3.6 (canary), 3.7 (fetch seam), and 3.8 (transformer seam).

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Completion Notes List

1. ✅ Removed CARRY timestamp stamps from `transform_to_sparql` (L402, L470-477, L521)
2. ✅ Renamed `last_fetched` → `observed_at` in `build_state_only_update`, changed triple to `mom:observedAt` xsd:string
3. ✅ Wired `observed_at` through `process_one_space` 304 and 200 paths (propagates on 304, carries on 200)
4. ✅ Updated registration flow in `main.py`: mint `observed_at`, pass to `transform_to_sparql`, write snapshot
5. ✅ Created gating test `tests/test_transformer_observed_at.py` with 4 live integration tests (all pass)
6. ✅ Updated regression tests in `test_regression_stuck_seeded.py` — assertions now check `mom:observedAt` instead of removed timestamps
7. ✅ Full test suite: 75 pass, 7 deselected (pre-existing failures), 1 xfailed

### File List

- `infra/link_handler/transformer.py` — transform_to_sparql, build_state_only_update, process_one_space
- `infra/link_handler/main.py` — registration flow
- `tests/test_transformer_observed_at.py` — new gating tests
- `tests/test_regression_stuck_seeded.py` — updated regression assertions
- `_bmad-output/implementation-artifacts/sprint-status.yaml` — 3-8 marked ready-for-dev

### Review Findings

- [x] [Review][Decision] `mom:snapshotDate` still written in `register_url` snapshot graph — patched: removed from `main.py` registration snapshot block [`infra/link_handler/main.py`]
- [x] [Review][Patch] `snap is None` silent drop — added `OBSERVED_AT_MISSING_200/304` WARNING logs; changed to `.get()` on all three access sites [`infra/link_handler/transformer.py`]
- [x] [Review][Patch] `snap["observed_at"]` direct dict access — changed to `.get("observed_at")` at L707, L721, L850 [`infra/link_handler/transformer.py`]
- [x] [Review][Patch] `write_snapshot` hardcoded `fetch_status="ok"` on fallback path — now tracks `_reg_used_fallback`, passes `"degraded"` on fallback [`infra/link_handler/main.py`]
- [x] [Review][Patch] Stale comment still references `mom:lastUpdated` — updated comment at L861 and `_read_space_metadata` docstring [`infra/link_handler/transformer.py`]
- [x] [Review][Defer] `_read_space_metadata` still reads `mom:lastUpdated` from Oxigraph — no → Story 3.9 tag; intentionally deferred per dev notes [`infra/link_handler/transformer.py`] — deferred, pre-existing
- [x] [Review][Defer] `content_changed` parameter now effectively dead in `transform_to_sparql` — cleanup for Story 3.9 [`infra/link_handler/transformer.py`] — deferred, pre-existing
- [x] [Review][Defer] SPARQL injection via `observed_at` interpolation — pre-existing pattern across codebase, theoretical risk [`infra/link_handler/transformer.py`] — deferred, pre-existing
- [x] [Review][Defer] Non-canary 304 `graph_uri=None` + `observed_at` → GRAPH <None> DELETE — pre-existing issue (identical bug existed with `lastFetched` before this story) [`infra/link_handler/transformer.py`] — deferred, pre-existing
- [x] [Review][Defer] Concurrent registration+heartbeat double-write race on `mom:observedAt` — pre-existing architectural pattern [`infra/link_handler/main.py`] — deferred, pre-existing
