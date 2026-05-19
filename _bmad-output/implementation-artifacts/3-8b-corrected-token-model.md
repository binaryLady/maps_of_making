# Story 3.8b: Correct the Transformer Seam — Three-Token Model

Status: done

> **Added 2026-05-19** (correct-course). Story 3.8 wrote `mom:observedAt` to Oxigraph — wrong
> axis. `observed_at` belongs in SQLite only (Axis A — endpoint health). Oxigraph must carry
> `mom:updatedAt` (Axis B — content maintenance, written only on genuine content diff) and
> `mom:lastOpenChange` (Axis C — source's own claim, already exists). Derived buckets
> `mom:operationalState` and `mom:endpointHealth` are removed from Oxigraph; they are computed
> at consumption time (browser) from the three tokens + config thresholds.
>
> Starting point: `infra/link_handler/transformer.py` as left by Story 3.8.

## Story

As a pipeline maintainer,
I want the transformer to write `mom:updatedAt` to Oxigraph only when content genuinely changes,
and to never write `mom:observedAt`, `mom:operationalState`, or `mom:endpointHealth` to Oxigraph,
so that the semantic store holds only source-derived facts and our content-observation, not
derived buckets or fetch-time observations that belong in SQLite.

## Acceptance Criteria

1. **`transform_to_sparql` stop writing wrong tokens:**
   - `mom:observedAt` triple is NOT written (belongs in SQLite, not Oxigraph)
   - `mom:operationalState` triple is NOT written (derived bucket — computed at consumption time)
   - `mom:endpointHealth` triple is NOT written (derived bucket — computed at consumption time)

2. **`transform_to_sparql` writes `mom:updatedAt`:**
   - On a 200+content-changed call: writes `mom:updatedAt` with current UTC ISO-8601 timestamp
     (GENERATE stamp — this is OUR observation of the diff, so `datetime.now()` is correct here)
   - The `state` block is added to the `_IGNORED` diff set so state open/closed flips do NOT
     advance `updated_at` (state flips count toward Axis C via `mom:lastOpenChange`)

3. **304 path produces zero Oxigraph writes:**
   - `build_state_only_update` is deleted
   - The 304 path in `process_one_space` writes nothing to Oxigraph
   - `observed_at` in SQLite still advances (Story 3.7 handles this — no change needed)

4. **Error/unreachable path produces zero Oxigraph writes** (same as 304 — no content, no write).

5. **`_read_space_metadata` updated:**
   - Drops the stale `mom:lastUpdated` OPTIONAL from its SPARQL query
   - Removes `last_updated` from returned dict and caller references

6. **Dead `content_changed` parameter removed** from `transform_to_sparql` signature and all
   call sites (`process_one_space` in transformer.py, registration path in main.py).

7. **Gating test `tests/test_transformer_three_token.py` passes:**
   - `test_content_changed_writes_updated_at`: run transformer on content-changed path; SPARQL
     SELECT `mom:updatedAt` → assert exists; assert `mom:observedAt` absent; assert
     `mom:operationalState` absent; assert `mom:endpointHealth` absent.
   - `test_unchanged_no_oxigraph_write`: run transformer on 304/unchanged path; assert Oxigraph
     triple count for the space is unchanged.
   - `test_state_block_ignored`: run transformer with only state field changed; assert `updated_at`
     does NOT advance (state diff excluded from Axis B).

8. Full pytest suite remains green. Operator visual confirmation: canary heartbeat cycle completes;
   Oxigraph has `mom:updatedAt` but no `mom:observedAt` for the canary space.

## Tasks / Subtasks

- [x] Task 1 — Remove wrong triples from `transform_to_sparql` (AC: 1)
  - [x] Remove the `mom:observedAt` triple from the INSERT DATA block
  - [x] Remove `mom:operationalState` triple (search for `classify_endpoint_health` / `endpoint_health` usage)
  - [x] Remove `mom:endpointHealth` triple
  - [x] Remove `classify_lifecycle()` and `classify_endpoint_health()` call sites inside
        `transform_to_sparql` (or `process_one_space` — wherever the derived bucket is computed
        to feed these triples)

- [x] Task 2 — Add `mom:updatedAt` on content-changed path (AC: 2)
  - [x] In `transform_to_sparql`, add `mom:updatedAt "{now}"^^xsd:dateTime` triple to the
        INSERT DATA block (xsd:dateTime is fine here — this is a GENERATE stamp, byte-identity
        not required unlike CARRY tokens)
  - [x] Confirm `transform_to_sparql` is only called on the 200+changed path in
        `process_one_space` (304 and error paths should not call it after Task 3)

- [x] Task 3 — Add `state` block to `_IGNORED` diff set (AC: 2)
  - [x] In `transformer.py`, find `_IGNORED` set (around L239)
  - [x] Add `"state"` to the set so state open/closed changes are excluded from the content diff

- [x] Task 4 — Delete `build_state_only_update` and wire 304 path (AC: 3)
  - [x] Delete the `build_state_only_update` function from `transformer.py`
  - [x] In `process_one_space`, find the 304 path; remove the `build_state_only_update` call
  - [x] Ensure `advance_observed_at` (SQLite) still runs on the 304 path (Story 3.7 — verify
        it does; do not remove it)
  - [x] Remove the error/unreachable path's `build_state_only_update` call (if any)

- [x] Task 5 — Clean up `_read_space_metadata` (AC: 5)
  - [x] Remove `OPTIONAL { ?s mom:lastUpdated ?lastUpdated }` from its SPARQL query
  - [x] Remove `last_updated` from the returned dict
  - [x] Update caller in `process_one_space` to not reference `last_updated`

- [x] Task 6 — Remove dead `content_changed` parameter (AC: 6)
  - [x] Remove `content_changed: bool = True` from `transform_to_sparql` signature
  - [x] Remove from call site in `process_one_space`
  - [x] Remove from call site in `main.py` registration path (if present)

- [x] Task 7 — Write gating test `tests/test_transformer_three_token.py` (AC: 7)
  - [x] `@pytest.mark.live_integration`
  - [x] `test_content_changed_writes_updated_at`
  - [x] `test_unchanged_no_oxigraph_write`
  - [x] `test_state_block_ignored`

- [x] Task 8 — Verify no regressions (AC: 8)
  - [x] `python -m pytest tests/ -v` — full hermetic suite green (69 passed, 1 xfailed)
  - [ ] Live heartbeat cycle; check Oxigraph via SPARQL for `mom:updatedAt` and absence of
        `mom:observedAt` / `mom:operationalState` / `mom:endpointHealth`

## Dev Notes

### `classify_lifecycle` and `classify_endpoint_health` — what happens to them

These functions (`transformer.py:133` and `transformer.py:106`) compute the derived buckets.
After this story they have no callers in the transform path. **Do not delete them yet** —
Story 3.10 may reference their logic when implementing browser-side axis computation. Mark
them with a comment `# Axis computation moved to browser — Story 3.10` and leave in place.

### `mom:updatedAt` — xsd:dateTime is correct here

Unlike `mom:observedAt` (Story 3.8's CARRY token requiring byte-identity via `xsd:string`),
`mom:updatedAt` is a GENERATE stamp minted by us at the moment we detect a diff. Oxigraph
may normalize `xsd:dateTime` (strip trailing zeros etc.) but that doesn't break anything —
we don't round-trip this value for byte comparison. Using `xsd:dateTime` is semantically
correct and lets SPARQL do temporal comparisons.

### 304 path after this story

Before 3.8b:
```
304 → advance_observed_at (SQLite) → build_state_only_update (Oxigraph)
```
After 3.8b:
```
304 → advance_observed_at (SQLite)   [Oxigraph: nothing]
```

Verify `advance_observed_at` call is NOT removed. It was added by Story 3.7 and is the
correct behavior for Axis A — it is NOT part of `build_state_only_update`.

### `_IGNORED` set context

The `_IGNORED` set controls which JSON keys are excluded from the content diff. Currently
excludes `mom:lastFetched`, `mom:snapshotDate`. Adding `"state"` means a space that only
changes `state.open` (open/closed flip) will not produce an `updated_at` advance. The flip
is captured by `_extract_last_open_change` → `mom:lastOpenChange` (Axis C). This is correct:
Axis B tracks content maintenance; Axis C tracks operational liveness.

### Registration path in `main.py`

The `/api/register-url` path calls `transform_to_sparql`. After removing `content_changed`,
verify the registration call still works. Registration always has a fresh content fetch, so
it is always a "content changed" call — `mom:updatedAt` should be written.

### Backward compatibility for pre-3.8b Oxigraph data

Spaces already in Oxigraph from Story 3.8 will have `mom:observedAt` triples. These will
persist until their next heartbeat cycle runs `transform_to_sparql` (which does DROP SILENT
GRAPH + re-INSERT, erasing them). No explicit cleanup needed — they self-clear on next ingest.

### Project Structure

- `infra/link_handler/transformer.py` — primary file
  - `transform_to_sparql`: remove wrong triples, add `mom:updatedAt`
  - `_IGNORED`: add `"state"`
  - `build_state_only_update`: delete
  - `process_one_space`: remove 304/error Oxigraph calls; keep SQLite advance
  - `_read_space_metadata`: drop `lastUpdated`
  - `classify_lifecycle`, `classify_endpoint_health`: keep, add comment
- `infra/link_handler/main.py` — registration path cleanup only
- `tests/test_transformer_three_token.py` — new gating test

### Running the Stack

```bash
distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d
source venv/bin/activate
python -m pytest tests/ -v
python -m pytest tests/test_transformer_three_token.py -v -m live_integration
# verify Oxigraph
python -c "
from infra.link_handler.snapshot_store import get_connection
# or use SPARQL directly:
import requests
q = '''SELECT ?p ?o WHERE { GRAPH <urn:mak:canary> { ?s ?p ?o } }'''
r = requests.get('http://localhost:7878/query', params={'query': q})
for row in r.json()['results']['bindings']:
    print(row['p']['value'].split('/')[-1], '→', row['o']['value'][:40])
"
```

### References

- Story 3.8 (old model): `_bmad-output/implementation-artifacts/3-8-transformer-emits-mom-observedat.md`
- `_IGNORED` set: `infra/link_handler/transformer.py:~239`
- `classify_lifecycle`: `infra/link_handler/transformer.py:133`
- `classify_endpoint_health`: `infra/link_handler/transformer.py:106`
- `build_state_only_update`: `infra/link_handler/transformer.py` (search by name)
- Sprint change proposal: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-19.md`

## Design Decisions

### Why remove `mom:observedAt` from Oxigraph

`observed_at` answers "when did we last see this endpoint respond?" That is a fetch-time
observation — it advances on every 200 or 304, regardless of content. Writing it to Oxigraph
on the content-changed path (as Story 3.8 did) conflates Axis A (reachability) with Axis B
(content maintenance). If a 304 also wrote to Oxigraph, you'd have Oxigraph written on every
fetch — defeating the "write only on content change" principle. SQLite is the correct home:
`snapshot_store.db` is the fetch artifact store; Oxigraph is the semantic content store.

### Why `build_state_only_update` is deleted (not modified)

`build_state_only_update` exists solely to push `observed_at` to Oxigraph on the 304 path.
Under the three-token model, the 304 path writes nothing to Oxigraph. The function has no
remaining purpose and deleting it is cleaner than making it a no-op.

### Derived buckets at consumption time

`operationalState` and `endpointHealth` are `f(timestamp, now, thresholds)`. They go stale
the moment they're written. Story 3.10 will compute them in the browser from the three tokens
and the thresholds block shipped in the GeoJSON header. No data is lost — the inputs are all
preserved in the three tokens.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Completion Notes List

- Removed `mom:observedAt`, `mom:operationalState`, `mom:endpointHealth` from `transform_to_sparql` INSERT block
- Added `mom:updatedAt` (xsd:dateTime GENERATE stamp) to `transform_to_sparql`
- Added `"state"` to `_IGNORED` diff set — state flips are Axis C, not Axis B
- Deleted `build_state_only_update`; 304 and error paths now write nothing to Oxigraph
- Removed `content_changed` and `observed_at` params from `transform_to_sparql` signature and all call sites
- Cleaned `_read_space_metadata`: dropped `lastUpdated` OPTIONAL and return key
- Marked `classify_lifecycle` and `classify_endpoint_health` with "Axis computation moved to browser — Story 3.10" comment
- Archived obsolete Story 3.8 test files to `tests/archive/`
- Wrote `tests/test_transformer_three_token.py` with hermetic + live_integration tests
- Fixed pre-existing `test_canary_scenarios.py` failures caused by baseline `state.open:false`
- Updated `test_open_flip_is_meaningful` → `test_open_flip_is_not_meaningful` to reflect 3.8b model

### File List

- `infra/link_handler/transformer.py`
- `infra/link_handler/main.py`
- `tests/test_transformer_three_token.py` (new)
- `tests/test_canary_scenarios.py`
- `tests/archive/test_transformer_observed_at_story38.py` (archived from tests/)
- `tests/archive/test_regression_stuck_seeded_story38.py` (archived from tests/)
- `pytest.ini`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Review Findings

- [x] [Review][Decision] `state` block fully excluded from Axis B diff — Intentional by design; all state changes route to Axis C via `_extract_last_open_change`. Accepted.
- [x] [Review][Patch] AC2 violation — `transform_to_sparql` called unconditionally on all 200 responses — Fixed: wrapped `transform_to_sparql` + Oxigraph POST in `if content_changed:` guard [transformer.py:762-791]
- [x] [Review][Patch] AC7 violation — `test_unchanged_no_oxigraph_write` was vacuous — Fixed: added `detect_diff` call to explicitly test no-diff scenario [tests/test_transformer_three_token.py:145-171]
- [x] [Review][Patch] Comments `# Axis computation moved to browser — Story 3.10` placed inside docstrings — Fixed: moved outside docstring bodies [transformer.py:117, 144]
- [x] [Review][Defer] `content_changed=True` default when `_fetch_last_snapshot` raises — every 200 after Oxigraph fetch error advances `mom:updatedAt` silently [transformer.py:741-747] — deferred, pre-existing
- [x] [Review][Defer] `_fetch_last_snapshot` SPARQL prefix doesn't match canary graphs — canary always treated as content_changed=True [transformer.py] — deferred, pre-existing
- [x] [Review][Defer] Error path does not persist incremented `consecutive_failures` to SQLite — health never advances beyond first degradation level [transformer.py:681-698] — deferred, pre-existing
- [x] [Review][Defer] Legacy fallback `_build_sparql_update` still writes `mom:operationalState` and `mom:lastFetched` — violates three-token contract on transform exception [main.py:787] — deferred, pre-existing
- [x] [Review][Defer] 304 path `last_open_now` from SQLite goes stale if space closes during a 304 streak — `effective_marker` reports `open` indefinitely [transformer.py:667] — deferred, pre-existing
