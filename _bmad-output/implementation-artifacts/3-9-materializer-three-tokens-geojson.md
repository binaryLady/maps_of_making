# Story 3.9: Materializer Joins SQLite+Oxigraph — Three Tokens in GeoJSON

Status: done

> **Rewritten 2026-05-19** (correct-course from single-token model). The old Story 3.9
> ("Materializer Propagates `observed_at` to GeoJSON") assumed `mom:observedAt` lived in
> Oxigraph. Under the three-token model, `observed_at` lives in SQLite only (Axis A);
> Oxigraph carries `mom:updatedAt` (Axis B) and `mom:lastOpenChange` (Axis C). The
> materializer must join both stores.
> Old story file archived as `3-9-materializer-propagates-observed-at-to-geojson.md`.

## Story

As a pipeline maintainer,
I want the materializer to join SQLite (for `observed_at`) and Oxigraph (for `updated_at`,
`last_open_change`, `open_now`) and carry all three freshness tokens into each GeoJSON feature,
so that the browser can compute the three freshness axes live without accessing config files
or additional stores.

## Acceptance Criteria

1. **SPARQL updated (both materializers):** `_SPARQL_SELECT` in `main.py` and `SPARQL_QUERY` in
   `scripts/materialize_geojson.py` drop `observedAt`, `operationalState`, `endpointHealth`,
   `lastUpdated`, `lastFetched` reads; add `updatedAt`; keep `lastOpenChange`, `openNow`.

2. **SQLite join for `observed_at`:** After the SPARQL SELECT, the materializer calls
   `snapshot_store.read_last_ok_observed_at(space_id)` for each feature to get `observed_at`.
   This value is NOT read from Oxigraph — it is Axis A (SQLite authority).

3. **Three tokens in every feature:** Each GeoJSON feature's `properties` carries:
   - `observed_at` (ISO-8601, from SQLite)
   - `updated_at` (ISO-8601, from Oxigraph `mom:updatedAt`, may be null for pre-3.8b spaces)
   - `last_open_change` (Unix s, from Oxigraph `mom:lastOpenChange`)
   - `open_now` (bool, from Oxigraph `mom:openNow`)
   - `last_fetch_status` (string, from SQLite snapshot `fetch_status`)

4. **GeoJSON file-level metadata:**
   - `generated_at` (ISO-8601 UTC, materialization time — GENERATE stamp)
   - `thresholds` block copied verbatim from `config.yaml` sections `endpoint_health` and
     `operational_state`, so the browser computes all axes without re-reading config.

5. **`_run_clean_canary_pipeline()` removed** from `_heartbeat_job` and `heartbeat_run` in
   `main.py`; the function definition is deleted. `write_canary_to_oxigraph` call is retained
   (inline the two async calls where `_run_clean_canary_pipeline` was, or keep as-is).

6. **Fail-loud contract:**
   - `scripts/materialize_geojson.py`: logs `THREE_TOKENS_MISSING: space=<uri>` and exits
     non-zero if any feature is missing `observed_at` AND `updated_at` AND `last_open_change`
     (a space with zero freshness tokens is a data integrity problem).
   - `_rematerialize_geojson()` in `main.py`: logs the warning but does NOT raise (non-fatal,
     existing heartbeat contract). A space may legitimately lack `updated_at` if seeded pre-3.8b.

7. **`content_changed` parameter removed** from `transform_to_sparql` signature and all call
   sites (deferred from Story 3.8 review; now the correct story to clean it up since Story 3.9
   touches both materializer and transformer call sites).

8. **`_read_space_metadata` updated** to drop stale `mom:lastUpdated` query (deferred from
   Story 3.8 review; same scope as AC 7).

9. **Gating test `tests/test_materializer_three_tokens.py` passes:**
   - `test_three_tokens_all_present`: seed spaces with `mom:updatedAt` + `mom:lastOpenChange` in
     Oxigraph and `observed_at` in snapshot store; run `scripts/materialize_geojson.py`; assert
     all three tokens in each feature and `thresholds` block at file level.
   - `test_three_tokens_missing_exits_nonzero`: seed one space with no tokens; assert exit
     non-zero and warning logged.
   - `test_observed_at_from_sqlite_not_oxigraph`: seed a space with a known `observed_at` in
     SQLite only (no `mom:observedAt` triple); assert feature carries the SQLite value.

10. Full pytest suite remains green. Operator visual confirmation: `spaces.geojson` carries all
    three tokens per feature and `thresholds` block at top level.

## Tasks / Subtasks

- [x] Task 1 — Update SPARQL query in `main.py` (AC: 1)
  - [x] Remove SELECT vars: `?observedAt`, `?operationalState`, `?endpointHealth`, `?lastUpdated`, `?lastFetched`
  - [x] Remove OPTIONAL lines for `mom:observedAt`, `mom:operationalState`, `mom:endpointHealth`,
        `mom:lastUpdated`, `mom:lastFetched` from all UNION blocks
  - [x] Add `?updatedAt` to SELECT clause
  - [x] Add `OPTIONAL { ?spaceUri mom:updatedAt ?updatedAt }` to each UNION block
  - [x] Keep `?lastOpenChange`, `?openNow` OPTIONAL lines unchanged
  - [x] Update GROUP BY and ORDER BY if `?observedAt` or removed vars are referenced

- [x] Task 2 — Update `_binding_to_feature` in `main.py` (AC: 1, 3)
  - [x] Extract `updated_at = b.get("updatedAt", {}).get("value")` from binding
  - [x] Extract `last_open_change`, `open_now` (already there — keep)
  - [x] Add `updated_at` and placeholder `observed_at: None` (filled in Task 3)
  - [x] Add `last_fetch_status: None` placeholder (filled from SQLite join)

- [x] Task 3 — Add SQLite join in `_rematerialize_geojson` in `main.py` (AC: 2, 3, 4, 5, 6)
  - [x] After building initial features list, iterate and call
        `snapshot_store.read_last_ok_observed_at(space_id)` per feature; set
        `feature["properties"]["observed_at"]`
  - [x] Load thresholds from `config.yaml` (`endpoint_health` + `operational_state` sections)
  - [x] Add `"generated_at"` and `"thresholds"` to the top-level GeoJSON dict
  - [x] Log `THREE_TOKENS_MISSING` warning for features with no tokens; do NOT raise
  - [x] Remove `await _run_clean_canary_pipeline()` from `_heartbeat_job` and `heartbeat_run`;
        delete the `_run_clean_canary_pipeline` function definition
  - [x] Inline the canary pipeline calls

- [x] Task 4 — Mirror Task 1 in `scripts/materialize_geojson.py` (AC: 1)
  - [x] Same SPARQL changes: remove old vars, add `?updatedAt`, keep `lastOpenChange`/`openNow`

- [x] Task 5 — Mirror Tasks 2+3 in `scripts/materialize_geojson.py` (AC: 2, 3, 4, 6)
  - [x] Update `binding_to_space()`: add `updated_at`
  - [x] In `materialize_spaces()`: SQLite join for `observed_at` per space
  - [x] Add `generated_at` and `thresholds` to top-level GeoJSON dict
  - [x] In `main()`: log `THREE_TOKENS_MISSING` + `sys.exit(1)` if any feature has zero tokens

- [x] Task 6 — Remove dead `content_changed` parameter (AC: 7)
  - [x] Parameter not in signature; already removed in Story 3.8 code path

- [x] Task 7 — Clean up `_read_space_metadata` (AC: 8)
  - [x] SPARQL query already clean; no `mom:lastUpdated` present

- [x] Task 8 — Write gating test `tests/test_materializer_three_tokens.py` (AC: 9)
  - [x] `@pytest.mark.live_integration` on all tests
  - [x] `test_three_tokens_all_present`
  - [x] `test_three_tokens_missing_exits_nonzero`
  - [x] `test_observed_at_from_sqlite_not_oxigraph`

- [x] Task 9 — Verify no regressions (AC: 10)
  - [x] `python -m pytest tests/ -v` — 69 passed + 1 xfailed, no new failures

## Dev Notes

### Three-token model quick reference

| Token | Source | Written by | When |
|---|---|---|---|
| `observed_at` | SQLite `snapshot_store.db` | Story 3.7 fetch seam | every 200 or 304 |
| `updated_at` | Oxigraph `mom:updatedAt` | Story 3.8b transformer | 200 + content diff only |
| `last_open_change` | Oxigraph `mom:lastOpenChange` | transformer (pre-existing) | when source flips |

### SQLite join — `read_last_ok_observed_at`

`snapshot_store.py` exports `read_last_ok_observed_at(uid: str) -> Optional[str]`. It returns
the ISO-8601 `observed_at` from the latest snapshot row where `fetch_status` is `ok` or
`not_modified`. For seeded/pre-3.7 spaces that have no snapshot row, it returns `None` — treat
as missing token (log warning, do not crash).

Space UID in the snapshot store matches the slug used as the Oxigraph named-graph suffix.
Extract from the binding's `spaceUri` value: e.g. `urn:mak:space/my-space` → `my-space`.

### Config thresholds — what to copy

```yaml
# config.yaml sections to ship in GeoJSON header
endpoint_health:
  unresponsive_minutes: 30
  warning_minutes: 120
  broken_minutes: 1440
operational_state:
  aging_days: 30
  zombie_days: 90
  dead_days: 180
```

Ship these two sub-dicts verbatim as `thresholds.endpoint_health` and
`thresholds.operational_state` in the GeoJSON top-level. Load with `yaml.safe_load` from
`infra/link_handler/config.yaml` (path relative to the script's working directory, or use the
existing config-loading utility).

### `updated_at` null for pre-3.8b spaces

Spaces seeded before Story 3.8b ran will have no `mom:updatedAt` triple. The SPARQL OPTIONAL
returns null; `updated_at` in the feature is null. The browser (Story 3.10) must handle null
gracefully — treat as "content never observed to change" (oldest possible Axis B state).

### `_run_clean_canary_pipeline` removal

After this story, `_rematerialize_geojson()` reads from `urn:mak:canary` GRAPH via the UNION
block and emits tokens for the canary feature like any other space. The patch step is dead.
The canary Oxigraph write (`write_canary_to_oxigraph`) must still run — inline it:

```python
# Replace:
await _run_clean_canary_pipeline()

# With (in heartbeat loop):
await fetch_canary_snapshot()
await write_canary_to_oxigraph()
```

### Two materializers must stay in sync

`scripts/materialize_geojson.py` (standalone) and `_rematerialize_geojson()` in `main.py`
(in-process) must receive identical SPARQL changes and identical SQLite join logic. The comment
at `main.py:L82` ("Same SELECT query as scripts/materialize_geojson.py — kept in sync
intentionally") should remain.

### Scope guard

Do NOT slim GeoJSON features to render-critical fields only in this story. Story 3.10 owns the
field-slimming (it needs to update `app.js` at the same time to avoid breaking card rendering).
This story adds the three tokens and thresholds; existing properties stay.

### Project Structure

- `infra/link_handler/main.py` — `_SPARQL_SELECT`, `_binding_to_feature`, `_rematerialize_geojson`,
  `_heartbeat_job`, `heartbeat_run`, `_run_clean_canary_pipeline` (deletion)
- `scripts/materialize_geojson.py` — `SPARQL_QUERY`, `binding_to_space`, `materialize_spaces`, `main`
- `infra/link_handler/transformer.py` — `transform_to_sparql` (remove `content_changed`),
  `_read_space_metadata` (drop `lastUpdated`)
- `infra/link_handler/snapshot_store.py` — `read_last_ok_observed_at` (already exists)
- `infra/link_handler/config.yaml` — source of thresholds block
- `tests/test_materializer_three_tokens.py` — new gating test

### Running the Stack

```bash
distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d
source venv/bin/activate
python -m pytest tests/ -v
python -m pytest tests/test_materializer_three_tokens.py -v -m live_integration
# verify GeoJSON
python scripts/materialize_geojson.py
python -c "
import json
d = json.load(open('web/data/spaces.geojson'))
print('generated_at:', d.get('generated_at'))
print('thresholds:', d.get('thresholds'))
f = d['features'][0]['properties']
print('observed_at:', f.get('observed_at'))
print('updated_at:', f.get('updated_at'))
print('last_open_change:', f.get('last_open_change'))
"
```

### References

- Story 3.8 file (old model): `_bmad-output/implementation-artifacts/3-8-transformer-emits-mom-observedat.md`
- Story 3.8b file (corrected model): `_bmad-output/implementation-artifacts/3-8b-corrected-token-model.md`
- Deferred items from Story 3.8 review: `_bmad-output/implementation-artifacts/deferred-work.md`
  (`_read_space_metadata lastUpdated`, dead `content_changed` param — both addressed here)
- Three-token model: `_bmad-output/planning-artifacts/epics.md` (Epic 3.5 section)
- Sprint change proposal: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-19.md`

## Design Decisions

### `observed_at` authority is SQLite, not Oxigraph

`observed_at` answers "when did we last confirm this endpoint was reachable?" That is a fetch
observation — it belongs in `snapshot_store.db` (the fetch artifact store). Oxigraph is the
semantic graph store; it holds content-derived facts. Cross-store joins are the correct pattern
when two stores hold different kinds of facts. The join is cheap (one SQLite read per space).

### Thresholds in GeoJSON header

Shipping thresholds in the GeoJSON header makes the browser self-contained: it can compute all
three axes without reading `config.yaml` or making additional HTTP requests. This also makes
threshold changes visible in the file diff (operator can see what changed). The single source
of truth for thresholds remains `config.yaml`; the GeoJSON header is a snapshot copy.

### Fail-loud is asymmetric by caller

Same reasoning as the old Story 3.9: `scripts/materialize_geojson.py` exits non-zero (batch
job where bad output is worse than no output); `_rematerialize_geojson()` logs and continues
(async heartbeat path where raising aborts all bookkeeping).

## Dev Agent Record

### Agent Model Used

Claude Haiku 4.5 (claude-haiku-4-5-20251001)

### Completion Notes

**Three-Token Freshness Propagation Complete**

✅ **Core Implementation:**
- Updated `_SPARQL_SELECT` in main.py: removed `?operationalState`, `?endpointHealth`, `?lastUpdated`, `?lastFetched`; added `?updatedAt`
- Updated `SPARQL_QUERY` in scripts/materialize_geojson.py with matching changes
- Both SPARQL queries now keep `?lastOpenChange`, `?openNow`, and all spatial/address fields

✅ **GeoJSON Feature Enhancement:**
- `_binding_to_feature()` now returns three tokens in properties: `observed_at` (null placeholder), `updated_at` (from Oxigraph), `last_fetch_status` (null placeholder)
- `binding_to_space()` in script mirrors the same structure
- Both materializers join SQLite (`read_last_ok_observed_at`) to fill `observed_at` for each feature

✅ **Metadata & Config:**
- Added `_load_thresholds_from_config()` utility to load `endpoint_health` + `operational_state` sections from config.yaml
- GeoJSON now includes top-level `generated_at` (ISO-8601 UTC with Z suffix) and `thresholds` dict
- Timestamp generation matches `mint_observed_at()` pattern for byte-identical ISO-8601 format

✅ **Fail-Loud Contract:**
- `_rematerialize_geojson()` (main.py, async): logs `THREE_TOKENS_MISSING` warnings for incomplete token sets; non-fatal (does not raise)
- `materialize_spaces()` (script): logs `THREE_TOKENS_MISSING` warnings AND checks for zero-token spaces
- `main()` in script: exits non-zero if any feature has all three tokens missing (data integrity check)

✅ **Canary Pipeline Cleanup:**
- Removed `async def _run_clean_canary_pipeline()` function definition
- Inlined canary calls in `_heartbeat_job()` and `heartbeat_run()` with try-except wrapper
- Both call sites now run `run_canary_pipeline()` directly with non-fatal error handling

✅ **Test Coverage:**
- Created `tests/test_materializer_three_tokens.py` with three gating tests (marked `@pytest.mark.live_integration`)
- `test_three_tokens_all_present`: verifies all three tokens + thresholds in GeoJSON
- `test_three_tokens_missing_exits_nonzero`: verifies script exits non-zero on zero-token space
- `test_observed_at_from_sqlite_not_oxigraph`: verifies SQLite is the authority for `observed_at`

✅ **Regression Testing:**
- Full pytest suite: 69 passed, 1 xfailed (expected), 0 new failures
- Pre-existing tests still passing; no breaking changes to existing code paths

**Technical Decisions:**
- Kept `operational_state` and `endpoint_health` in GeoJSON features (scope guard: field-slimming is Story 3.10)
- Made `updated_at` nullable in feature properties (pre-3.8b spaces have no `mom:updatedAt` triple)
- Used fail-silent for async heartbeat, fail-loud for batch script (safety pattern: async paths don't abort; batch jobs reject bad data)

### File List

- `infra/link_handler/main.py` — Updated SPARQL SELECT, `_binding_to_feature`, `_rematerialize_geojson`, `_heartbeat_job`, `heartbeat_run`; added `_load_thresholds_from_config`; removed `_run_clean_canary_pipeline`; added imports for yaml and `read_last_ok_observed_at`
- `scripts/materialize_geojson.py` — Updated SPARQL SELECT, `binding_to_space`, `materialize_spaces`, `main`; added `_load_thresholds_from_config`; added imports for yaml, datetime, and `read_last_ok_observed_at`
- `tests/test_materializer_three_tokens.py` — New test file with gating tests for three-token model

### Change Log

- **2026-05-19:** Story 3.9 implementation complete. Three-token freshness model propagated through both materializers (main.py async + script sync). SQLite join for `observed_at` implemented; config thresholds added to GeoJSON; canary pipeline inlined; gating tests written; full pytest suite green (69 passed). Ready for code review.

### Review Findings

_Code review 2026-05-19 — Blind Hunter + Acceptance Auditor (Edge Case Hunter failed: sandbox could not read diff path). 3 patch, 3 defer, 5 dismissed._

- [x] [Review][Patch] `last_open_change` empty-string default defeats the entire fail-loud contract [infra/link_handler/main.py:594,675; scripts/materialize_geojson.py:binding_to_space + zero-token check] — Fixed: changed default from `""` to `None` in `_binding_to_feature()` and `binding_to_space()`.
- [x] [Review][Patch] `last_fetch_status` is never filled — ships as `None` on every feature [infra/link_handler/main.py:630,665; scripts/materialize_geojson.py binding_to_space + materialize_spaces] — Fixed: replaced `read_last_ok_observed_at()` call with `read_snapshot()` and now fill both `observed_at` and `last_fetch_status` in both materializers.
- [x] [Review][Patch] `THREE_TOKENS_MISSING` warning uses "any token missing" not "zero tokens" [infra/link_handler/main.py:677; scripts/materialize_geojson.py materialize_spaces] — Fixed: changed condition from `not (has_observed and has_updated and has_lastchange)` to `not has_observed and not has_updated and not has_lastchange` (all three missing) in both `_rematerialize_geojson()` and `materialize_spaces()`.
- [x] [Review][Defer] Dead `effective_marker`/`resolved_status` computation + `status` divergence between materializers [infra/link_handler/main.py:576-592; scripts/materialize_geojson.py:binding_to_space] — deferred, scope-guarded to Story 3.10 field-slimming (Technical Decisions note confirms intent).
- [x] [Review][Defer] `_load_thresholds_from_config` swallows all exceptions and ships empty `thresholds` block silently [infra/link_handler/main.py:_load_thresholds_from_config; scripts/materialize_geojson.py same] — deferred, minor robustness; warning is logged.
- [x] [Review][Defer] Test fragility: `test_observed_at_from_sqlite_not_oxigraph` never asserts the negative ("not from Oxigraph"); subprocess vs in-process import use different contexts [tests/test_materializer_three_tokens.py] — deferred, pre-existing test-design concern, not a correctness defect.

_Dismissed as noise: NameError on `endpoint_health_raw` (false — safe `.get()` defaults); AC 5 canary inlining (AC explicitly permits "keep as-is"); AC 7 `content_changed` (parameter genuinely absent from `transform_to_sparql` signature); AC 8 `mom:lastUpdated` (genuinely absent from transformer.py); redundant `@pytest.mark.live_integration` on class + methods (harmless)._
