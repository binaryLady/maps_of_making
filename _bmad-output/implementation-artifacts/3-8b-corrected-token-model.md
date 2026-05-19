# Story 3.8b: Correct the Transformer Seam — Three-Token Model

Status: ready-for-dev

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

- [ ] Task 1 — Remove wrong triples from `transform_to_sparql` (AC: 1)
  - [ ] Remove the `mom:observedAt` triple from the INSERT DATA block
  - [ ] Remove `mom:operationalState` triple (search for `classify_endpoint_health` / `endpoint_health` usage)
  - [ ] Remove `mom:endpointHealth` triple
  - [ ] Remove `classify_lifecycle()` and `classify_endpoint_health()` call sites inside
        `transform_to_sparql` (or `process_one_space` — wherever the derived bucket is computed
        to feed these triples)

- [ ] Task 2 — Add `mom:updatedAt` on content-changed path (AC: 2)
  - [ ] In `transform_to_sparql`, add `mom:updatedAt "{now}"^^xsd:dateTime` triple to the
        INSERT DATA block (xsd:dateTime is fine here — this is a GENERATE stamp, byte-identity
        not required unlike CARRY tokens)
  - [ ] Confirm `transform_to_sparql` is only called on the 200+changed path in
        `process_one_space` (304 and error paths should not call it after Task 3)

- [ ] Task 3 — Add `state` block to `_IGNORED` diff set (AC: 2)
  - [ ] In `transformer.py`, find `_IGNORED` set (around L239)
  - [ ] Add `"state"` to the set so state open/closed changes are excluded from the content diff

- [ ] Task 4 — Delete `build_state_only_update` and wire 304 path (AC: 3)
  - [ ] Delete the `build_state_only_update` function from `transformer.py`
  - [ ] In `process_one_space`, find the 304 path; remove the `build_state_only_update` call
  - [ ] Ensure `advance_observed_at` (SQLite) still runs on the 304 path (Story 3.7 — verify
        it does; do not remove it)
  - [ ] Remove the error/unreachable path's `build_state_only_update` call (if any)

- [ ] Task 5 — Clean up `_read_space_metadata` (AC: 5)
  - [ ] Remove `OPTIONAL { ?s mom:lastUpdated ?lastUpdated }` from its SPARQL query
  - [ ] Remove `last_updated` from the returned dict
  - [ ] Update caller in `process_one_space` to not reference `last_updated`

- [ ] Task 6 — Remove dead `content_changed` parameter (AC: 6)
  - [ ] Remove `content_changed: bool = True` from `transform_to_sparql` signature
  - [ ] Remove from call site in `process_one_space`
  - [ ] Remove from call site in `main.py` registration path (if present)

- [ ] Task 7 — Write gating test `tests/test_transformer_three_token.py` (AC: 7)
  - [ ] `@pytest.mark.live_integration`
  - [ ] `test_content_changed_writes_updated_at`
  - [ ] `test_unchanged_no_oxigraph_write`
  - [ ] `test_state_block_ignored`

- [ ] Task 8 — Verify no regressions (AC: 8)
  - [ ] `python -m pytest tests/ -v` — full suite green
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

<!-- to be filled by dev agent -->

### Completion Notes List

<!-- to be filled by dev agent -->

### File List

<!-- to be filled by dev agent -->
