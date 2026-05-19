# Story 3.9: Materializer Propagates `observed_at` to GeoJSON

Status: ready-for-dev

## Story

As a pipeline maintainer,
I want the materializer to read `mom:observedAt` from Oxigraph and carry it byte-identical into each GeoJSON feature,
so that the freshness token minted at fetch time reaches the browser without re-stamping or silent omission.

## Acceptance Criteria

1. Given all spaces have `mom:observedAt` in their named graphs (written by Story 3.8),
   when `_rematerialize_geojson()` in `main.py` runs,
   then each feature in `spaces.geojson` carries `properties.observed_at` byte-equal to the Oxigraph triple value.

2. Given all spaces have `mom:observedAt` in their named graphs,
   when `scripts/materialize_geojson.py` runs,
   then each feature carries `properties.observed_at` byte-equal to the Oxigraph triple value.

3. The produced GeoJSON file carries a top-level `"generated_at"` field (ISO-8601 UTC string,
   materialization time — a new GENERATE stamp, not carried from fetch).

4. If any feature is missing `observed_at` after a successful SPARQL query:
   - `scripts/materialize_geojson.py` logs `OBSERVED_AT_MISSING: space=<uri>` and exits non-zero.
   - `_rematerialize_geojson()` in `main.py` logs the same warning but does NOT raise (non-fatal — existing heartbeat contract).

5. The canary UNION block in both SPARQL queries gains `OPTIONAL { ?spaceUri mom:observedAt ?observedAt }` —
   removing the now-stale `mom:lastFetched`/`mom:lastUpdated` reads from the `urn:mak:canary` block.

6. `_read_space_metadata` in `transformer.py` no longer queries `mom:lastUpdated` (triple no longer written after 3.8);
   the stale column is replaced with `mom:observedAt`, and the returned dict key is renamed accordingly.

7. The dead `content_changed` parameter in `transform_to_sparql` is removed from the signature;
   all call sites updated.

8. The `_run_clean_canary_pipeline()` patch step (`materialize_canary_geojson`) is no longer needed
   after `_rematerialize_geojson()` correctly emits `observed_at` for the canary graph.
   Remove `_run_clean_canary_pipeline()` from `_heartbeat_job` and `heartbeat_run`; keep `write_canary_to_oxigraph`
   (Oxigraph write is still needed).

9. Gating test `test_materializer_observed_at.py` passes:
   - Seed one space with `mom:observedAt` in Oxigraph; one space without.
   - Run `scripts/materialize_geojson.py` → assert exit non-zero.
   - Run with both spaces having `mom:observedAt` → assert each feature's `properties.observed_at` matches the triple.

10. Full pytest suite remains green. Operator visual confirmation: canary feature in `spaces.geojson`
    shows non-null `observed_at` immediately after `_rematerialize_geojson()` without needing the
    subsequent canary patch step.

## Tasks / Subtasks

- [ ] Task 1 — Update SPARQL query in `main.py` (AC: 1, 5)
  - [ ] Add `?observedAt` to SELECT clause (alongside existing columns)
  - [ ] Add `OPTIONAL { ?spaceUri mom:observedAt ?observedAt }` to each UNION block
    (space graph block L96-128, rff-health block L132-163, canary block L168-186)
  - [ ] Remove `mom:lastFetched` / `mom:lastUpdated` OPTIONAL lines from canary block only
    (lines 179-180); keep them in space/rff blocks — those triples may still exist for seeded
    spaces that predate Story 3.8
  - [ ] Add `?observedAt` to GROUP BY and ORDER BY clauses

- [ ] Task 2 — Update `_binding_to_feature` in `main.py` (AC: 1, 3, 4)
  - [ ] Extract `observed_at = b.get("observedAt", {}).get("value")` from binding
  - [ ] Add `"observed_at": observed_at` to the returned `properties` dict
  - [ ] Remove `"last_updated"` and `"last_fetched"` keys from properties (triples gone after 3.8;
    browser migration is Story 3.10 — keep fields present but empty string is fine if removal
    breaks existing UI; see Dev Notes on scope guard)

- [ ] Task 3 — Update `_rematerialize_geojson` in `main.py` (AC: 3, 4)
  - [ ] After building `features`, log `OBSERVED_AT_MISSING: space=<uri>` for any feature with
    null `observed_at`; do NOT raise
  - [ ] Add `"generated_at": datetime.now(timezone.utc).isoformat()` to the `geojson` dict
    (this is a GENERATE stamp — materialization time, not fetch time)

- [ ] Task 4 — Update SPARQL query in `scripts/materialize_geojson.py` (AC: 2, 5)
  - [ ] Mirror Task 1: add `?observedAt` to SELECT, add OPTIONAL in all three blocks,
    remove stale lastFetched/lastUpdated from canary block only, update GROUP BY

- [ ] Task 5 — Update `binding_to_space` in `scripts/materialize_geojson.py` (AC: 2, 3, 4)
  - [ ] Extract `observed_at` from binding; add to returned properties
  - [ ] Add `generated_at` to the top-level GeoJSON dict in `materialize_spaces()`
  - [ ] In `main()`: after building features, log `OBSERVED_AT_MISSING: space=<uri>` for any
    feature with null `observed_at`; call `sys.exit(1)` if any missing

- [ ] Task 6 — Clean up `_read_space_metadata` in `transformer.py` (AC: 6)
  - [ ] Replace `mom:lastUpdated ?lastUpdated` with `mom:observedAt ?observedAt` in the SPARQL query
  - [ ] Rename `last_updated` → `observed_at` in returned dict and in the caller
    (`process_one_space` at L844 preserves this value across the DROP SILENT GRAPH + re-INSERT)
  - [ ] Update docstring

- [ ] Task 7 — Remove dead `content_changed` parameter from `transform_to_sparql` (AC: 7)
  - [ ] Remove `content_changed: bool = True` from signature at `transformer.py:373`
  - [ ] Update both call sites: `process_one_space` L855 (remove kwarg) and
    `main.py` registration path (remove kwarg)
  - [ ] Verify no logic inside `transform_to_sparql` references `content_changed`
    (per Story 3.8 dev notes, the branching was removed — parameter became a no-op)

- [ ] Task 8 — Remove canary GeoJSON patch from heartbeat (AC: 8)
  - [ ] In `main.py`: remove `await _run_clean_canary_pipeline()` calls from
    `_heartbeat_job` (L53) and `heartbeat_run` (L683)
  - [ ] Remove the `_run_clean_canary_pipeline` function definition (L40-47)
  - [ ] Keep `run_canary_pipeline` import — `write_canary_to_oxigraph` is still used
    OR: inline `write_canary_to_oxigraph` call directly and drop the import if nothing else uses it
  - [ ] Verify `canary_pipeline.py`'s `materialize_canary_geojson` is no longer called from
    any production path (it can remain for reference / tests)

- [ ] Task 9 — Write gating test `tests/test_materializer_observed_at.py` (AC: 9)
  - [ ] `@pytest.mark.live_integration`
  - [ ] `test_materialize_fails_on_missing_observed_at`: seed one space with `mom:observedAt`,
    one without; invoke `materialize_spaces()` / `main()`; assert exit non-zero and warning logged
  - [ ] `test_materialize_all_observed_at_present`: seed multiple spaces all with `mom:observedAt`;
    run materializer; assert each feature's `properties.observed_at` equals the seeded value

- [ ] Task 10 — Verify no regressions (AC: 10)
  - [ ] `python -m pytest tests/ -v` — full suite green
  - [ ] Live stack: heartbeat cycle completes; `spaces.geojson` contains `observed_at` and
    `generated_at` at top level; canary feature has non-null `observed_at`
  - [ ] Confirm `_run_clean_canary_pipeline` no longer appears in heartbeat logs

## Dev Notes

### Scope guard: GeoJSON field slimming

The epics spec and sprint-change-proposal both mention slimming GeoJSON features to render-critical
fields only. **Do NOT slim in this story.** The browser (`web/app.js`) reads `last_updated`,
`last_fetched`, and many card-detail fields directly from GeoJSON feature properties. Removing them
here without updating `app.js` would break card rendering and filter chips. That browser migration
is Story 3.10's responsibility. Story 3.9 adds `observed_at` and `generated_at`; existing properties
remain untouched.

### Canary block SPARQL — which triples to remove

After Story 3.8, `mom:lastFetched` and `mom:lastUpdated` are no longer written to **any** graph by
`transform_to_sparql`. However, seeded spaces (SpaceAPI directory, RFF) that predate Story 3.8
may still have those triples in their named graphs. Keep the OPTIONAL reads in the `urn:mak:space/`
and `urn:mak:mock/rff-health` blocks for backward compatibility — they'll return empty for new spaces
and non-empty for old ones. The `urn:mak:canary` block is written exclusively by the clean pipeline
(Stories 3.6–3.8) so it never had those triples; their OPTIONAL clauses are dead weight.

### `_run_clean_canary_pipeline` vs `run_canary_pipeline`

The current heartbeat sequence in `main.py:50-54`:
```
await run_heartbeat_cycle(...)        # legacy: fetches spaces → Oxigraph → rematerialize
await _run_clean_canary_pipeline()    # patch: re-fetches canary → Oxigraph → patches GeoJSON
```
After this story, `_rematerialize_geojson()` (called inside `run_heartbeat_cycle`) will emit
`observed_at` for the canary feature directly from Oxigraph. The GeoJSON patch is redundant.
The canary fetch + Oxigraph write still needs to happen — that's `fetch_canary_snapshot` +
`write_canary_to_oxigraph` from `canary_pipeline.py`. Decide whether to keep them as a
post-rematerialize step or fold into the heartbeat cycle. Simplest: inline the two async calls
where `_run_clean_canary_pipeline` was.

### `content_changed` removal safety

`transform_to_sparql` signature has `content_changed: bool = True` (added pre-3.8 for lastUpdated
branching). Story 3.8 removed the `if content_changed:` block. The parameter is now truly dead —
no code path inside the function reads it. Safe to delete. Both call sites pass it explicitly today:
- `transformer.py:855`: `transform_to_sparql(..., content_changed=content_changed, observed_at=...)`
- `main.py` registration path: may or may not pass it (check)

### `_read_space_metadata` observed_at preservation

`transform_to_sparql` does `DROP SILENT GRAPH <space_uri>` + `INSERT DATA`. Any triple not in the
INSERT is lost. `_read_space_metadata` reads `source` and `memberOf` before the DROP so they can
be re-inserted. After 3.8, `mom:observedAt` is written by `transform_to_sparql` from the snapshot
— so it does NOT need to be preserved by read-before-drop. The `lastUpdated` field was being
preserved (read, then re-inserted); since that triple no longer exists, the field is stale.
The query should simply remove the `?lastUpdated` OPTIONAL clause and the returned dict entry.
The caller should be updated to not pass `last_updated` to `transform_to_sparql`.

### Two materializers must stay in sync

`scripts/materialize_geojson.py` is the standalone script (called via `make` or seed pipeline).
`_rematerialize_geojson()` in `main.py` is the in-process version (called after heartbeat and
registration). The dev notes in Story 3.8 note they are intentionally kept in sync with a comment.
Apply identical SPARQL changes to both. The `main.py` comment at L82 ("Same SELECT query as
scripts/materialize_geojson.py — kept in sync intentionally") should remain.

### Project Structure

- `infra/link_handler/main.py` — `_SPARQL_SELECT`, `_binding_to_feature`, `_rematerialize_geojson`,
  `_heartbeat_job`, `heartbeat_run`, `_run_clean_canary_pipeline` (removal)
- `scripts/materialize_geojson.py` — `SPARQL_QUERY`, `binding_to_space`, `materialize_spaces`, `main`
- `infra/link_handler/transformer.py` — `transform_to_sparql` (remove param),
  `_read_space_metadata` (replace lastUpdated→observedAt)
- `tests/test_materializer_observed_at.py` — new gating test

### Running the Stack

```bash
distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d
source venv/bin/activate
python -m pytest tests/ -v
python -m pytest tests/test_materializer_observed_at.py -v -m live_integration
# verify GeoJSON
python scripts/materialize_geojson.py
python -c "import json; d=json.load(open('web/data/spaces.geojson')); print(d.get('generated_at')); print(d['features'][0]['properties'].get('observed_at'))"
```

### References

- Story 3.8 file: `_bmad-output/implementation-artifacts/3-8-transformer-emits-mom-observedat.md`
- Deferred 3.8 handoff: `_bmad-output/implementation-artifacts/deferred-work.md` (top entry, 2026-05-19)
- Review patches (deferred items): `_bmad-output/implementation-artifacts/deferred-work.md`
  (`_read_space_metadata lastUpdated`, dead `content_changed` param)
- `canary_pipeline.py`: `infra/link_handler/canary_pipeline.py` — reference for
  `write_canary_to_oxigraph` pattern (keep) vs `materialize_canary_geojson` (now redundant)
- Epics: `_bmad-output/planning-artifacts/epics.md` — Story 3.9 section

## Design Decisions

### `generated_at` is GENERATE, not CARRY

`generated_at` at the GeoJSON file level is the materialization timestamp — when the file was
written, not when any space was fetched. It is a new `datetime.now()` GENERATE stamp in the
materializer. This is correct: it tells the browser "this file was built at T" which is useful for
cache-busting and admin tooling. It does not represent any space's freshness — that is
`observed_at` per feature.

### Fail-loud is asymmetric by caller

`scripts/materialize_geojson.py` exits non-zero on any missing `observed_at` — it is a batch
script where a bad output is worse than no output. `_rematerialize_geojson()` only logs and
continues — it is called from the heartbeat async path where raising would abort all subsequent
heartbeat bookkeeping. This asymmetry is intentional and matches the existing error-handling
contract of both functions.

### Canary redundancy: remove cleanly

After this story, `_rematerialize_geojson()` reads from `urn:mak:canary` GRAPH directly (UNION
block) and emits `observed_at` for the canary feature just like any other space. The canary
GeoJSON patch step was a transitional workaround for the period when `_rematerialize_geojson()`
didn't know about `mom:observedAt`. Remove it entirely rather than keeping dead code.

## Dev Agent Record

### Agent Model Used

<!-- to be filled by dev agent -->

### Completion Notes List

<!-- to be filled by dev agent -->

### File List

<!-- to be filled by dev agent -->
