# Story 3.2b: mak:closed + PII Strip on Persistent Closure

Status: done

## Story

As MOM,
I want the heartbeat to detect when a space self-reports closed for N consecutive cycles and automatically strip PII contact fields while marking the space as `mak:closed`,
so that the map stays honest about permanently-closed spaces without retaining personal data, and revives automatically if the coordinator updates their endpoint.

## Acceptance Criteria

### AC1 — Closed-cycle counter increment

**Given** a space's SpaceAPI fetch returns HTTP 200 with `state.open == false` (v15 object) or `state == "closed"` (v0.13 string)

**When** the heartbeat processes the response

**Then** `consecutive_closed_cycles` in `heartbeat_log` increments by 1

**And** if the fetch returns 200 with `state.open == true` or `state == "open"`, `consecutive_closed_cycles` resets to 0

**And** 304 responses do NOT change `consecutive_closed_cycles` (last-known value preserved)

**And** error / non-200 responses do NOT change `consecutive_closed_cycles` (last-known value preserved)

---

### AC2 — Closure threshold triggers PII strip + mak:closed mark

**Given** `consecutive_closed_cycles >= closed_cycles_threshold` (configurable, default 6 cycles ≈ 1 hour at 10-min heartbeat)

**When** the heartbeat processes the next 200 response for that space

**Then** a SPARQL update strips `schema:contactJson` from the space's named graph

**And** writes `mak:closedAt` with the current ISO datetime

**And** writes `mom:operationalState "closed"`

**And** logs `WARNING closed_pii_strip space_id=<id>` (named counter, never folded into generic "skipped")

**And** does NOT delete coordinates, name, description, logo, URL, or endpoint URL

---

### AC3 — Idempotency: repeated closed cycles do not re-strip

**Given** a space is already in `mom:operationalState "closed"` (PII already stripped)

**When** the heartbeat processes another closed-cycle response

**Then** no additional SPARQL delete is issued (SPARQL `DELETE` is safe to repeat but the logic skips it to avoid noise)

**And** `consecutive_closed_cycles` continues incrementing (or is clamped — implementation choice)

---

### AC4 — Revival on material content diff

**Given** a space is in `mom:operationalState "closed"` (was PII-stripped)

**When** the heartbeat receives a 200 response AND `detect_diff` returns non-None (material content changed)

**Then** `mom:operationalState` is reset to `"confirmed"` (lifecycle clock resets to 0 days)

**And** `mak:closedAt` triple is removed from the named graph

**And** `consecutive_closed_cycles` resets to 0 in `heartbeat_log`

**And** `mom:lastUpdated` is rewritten (same as standard content-changed path)

**Note:** PII contact fields are NOT restored (coordinator must re-supply them by updating their endpoint JSON — the new content diff will include the contact block if they add it back)

---

### AC5 — Config threshold is configurable

**Given** `config.yaml` has a `closure` section

**When** the heartbeat reads its config

**Then** `consecutive_closed_cycles >= closed_cycles_threshold` uses the configured value

**Default:** `closed_cycles_threshold: 6` (6 × 10-min cycles = ~1 hour of confirmed-closed before stripping)

---

### AC6 — DB schema migration

**Given** the existing `heartbeat_log` SQLite table lacks `consecutive_closed_cycles`

**When** `init_db()` runs (container start)

**Then** an `ALTER TABLE ... ADD COLUMN consecutive_closed_cycles INTEGER DEFAULT 0` migration runs if the column is absent (same pattern as `last_content_updated` migration in Story 3.0)

---

### AC7 — Unit tests

**Given** the test suite in `infra/link_handler/test_transformer.py`

**When** the developer adds tests for Story 3.2b

**Then** the following cases are covered:

- `state.open == false` (v15) → `consecutive_closed_cycles` increments
- `state == "closed"` (v0.13) → increments
- `state.open == true` → resets to 0
- 304 → no change
- error → no change
- threshold reached → PII strip SPARQL generated, `mak:closedAt` written
- idempotency: second strip call after already-closed → no-op
- revival: material diff on closed space → `mak:closedAt` removed, state → confirmed, counter reset

---

### AC8 — GeoJSON materialization: closed spaces visible as "closed" pin

**Given** a space in `mom:operationalState "closed"`

**When** `scripts/materialize_geojson.py` runs

**Then** `effective_marker` returns `"closed"` for that space

**And** the GeoJSON feature includes `"status": "closed"` in its properties

**Note:** The closed pin's visual treatment (e.g. greyed-out marker) is a UI concern deferred to a future story. This AC only ensures the signal is correctly propagated in the data layer.

---

## Tasks / Subtasks

- [x] **Task 1: DB migration** (`transformer.py` `init_db`)
  - [x] Add `consecutive_closed_cycles INTEGER DEFAULT 0` column migration (same pattern as `last_content_updated`)
  - [x] Add column to `_read_heartbeat_row` SELECT + default dict
  - [x] Add column to all `_write_heartbeat_row` INSERT/UPDATE statements

- [x] **Task 2: Config** (`config.yaml`)
  - [x] Add `closure:` section with `closed_cycles_threshold: 6`
  - [x] Read in `process_one_space` (or dedicated helper)

- [x] **Task 3: Closed-cycle signal extraction** (`transformer.py`)
  - [x] Add `_is_open_now(validated_data)` helper that returns `True`, `False`, or `None` (no signal)
  - [x] In `process_one_space`, after 200 body parse: if `_is_open_now` returns `False`, increment `consecutive_closed_cycles`; if `True`, reset to 0; if `None` or 304/error, leave unchanged
  - [x] Update `heartbeat_log` with new counter value after each 200 response

- [x] **Task 4: Closure trigger** (`transformer.py` `process_one_space`)
  - [x] After counter update: if `consecutive_closed_cycles >= threshold` AND `operationalState != "closed"` (check via DB or Oxigraph):
    - Build PII-strip SPARQL (DELETE `schema:contactJson`; INSERT `mak:closedAt`, `mom:operationalState "closed"`)
    - Execute against Oxigraph
    - Log named WARNING counter `closed_pii_strip`
  - [x] Guard: if already closed, skip (AC3)

- [x] **Task 5: Revival logic** (`transformer.py` `process_one_space`)
  - [x] On material diff (content_changed == True) for a space currently in `closed` state:
    - Include `DELETE { <space> mak:closedAt ?t }` in the content-changed SPARQL update
    - Set `mom:operationalState` back to `"confirmed"` (lifecycle clock reset to 0)
    - Reset `consecutive_closed_cycles = 0` in DB

- [x] **Task 6: effective_marker update** (`transformer.py`)
  - [x] Add `"closed"` as a valid lifecycle state in `effective_marker` (below `"dead"`, above everything else that could fight it)
  - [x] Update `classify_lifecycle` or add a separate path: if `operationalState == "closed"` → return `("closed", "Self-reported closed for N cycles")` — OR handle entirely in `process_one_space` and pass as metadata

- [x] **Task 7: Tests** (`test_transformer.py`)
  - [x] All AC7 cases (see above)
  - [x] Test that coordinates, name, description, logo, URL are NOT touched by PII strip SPARQL

- [x] **Task 8: Plan-doc update**
  - [x] Update `_bmad-output/implementation-artifacts/deferred-work.md`: strike FR25b as resolved with date
  - [x] Update `_bmad-output/planning-artifacts/epics.md`: add completion stamp to Story 3.2b section
  - [x] Update `_bmad-output/implementation-artifacts/sprint-status.yaml`: flip `3-2-b-mak-closed-pii-strip` to `review`

---

## Dev Notes

### Scope clarity — what this story is NOT

- Does NOT send coordinator emails (Epic 4b / Story 3.3)
- Does NOT show a UI closure confirmation or grey pin (future UI story)
- Does NOT handle magic-link YES/NO flow (Epic 4b)
- Does NOT hard-block PII at validation time (deferred to Epic 5 hardening)

### What counts as "closed signal"

`state.open == false` (v15 object) **OR** `state == "closed"` (v0.13 string). Reuse `_extract_open_now` from Story 3.2 — it already handles both forms and returns `False` for closed. A return value of `False` from `_extract_open_now` is the closed signal.

A missing or unparseable `state` field (`None` return) is treated as "no signal" — counter unchanged. This is intentional: many spaces don't report state at all, and we must not penalize them.

### SPARQL for PII strip (triple deletion)

This is the blast-radius concern that justified a separate story. The SPARQL must:
1. Delete `schema:contactJson` from the space's named graph
2. Insert `mak:closedAt` (one datetime)
3. Insert `mom:operationalState "closed"` (surgical — same DELETE/INSERT pattern as `build_state_only_update`)

Template (adapt from `build_state_only_update`):
```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
PREFIX mak: <urn:mak:>
DELETE {
  GRAPH <urn:mak:space/{slug}> {
    <urn:mak:space/{slug}> schema:contactJson ?contactJson .
    <urn:mak:space/{slug}> mom:operationalState ?oldState .
  }
}
INSERT {
  GRAPH <urn:mak:space/{slug}> {
    <urn:mak:space/{slug}> mom:operationalState "closed" .
    <urn:mak:space/{slug}> mak:closedAt "{now}"^^xsd:dateTime .
  }
}
WHERE {
  GRAPH <urn:mak:space/{slug}> {
    OPTIONAL { <urn:mak:space/{slug}> schema:contactJson ?contactJson }
    OPTIONAL { <urn:mak:space/{slug}> mom:operationalState ?oldState }
  }
}
```

### Revival SPARQL (delete mak:closedAt on revival)

When content_changed == True for a space currently in `closed` state, add to the standard `transform_to_sparql` output:
```sparql
DELETE {
  GRAPH <urn:mak:space/{slug}> {
    <urn:mak:space/{slug}> mak:closedAt ?t .
  }
}
WHERE {
  GRAPH <urn:mak:space/{slug}> {
    OPTIONAL { <urn:mak:space/{slug}> mak:closedAt ?t }
  }
}
```

### How to detect "already closed" (AC3 guard)

Two options — choose the simpler one:
- **SQLite flag** (preferred for speed): add `is_closed INTEGER DEFAULT 0` column to `heartbeat_log`, set on PII strip, clear on revival. Read from `_read_heartbeat_row`. Avoids an extra Oxigraph query per cycle.
- **Oxigraph ASK**: `ASK { GRAPH <urn:mak:space/{slug}> { ?s mak:closedAt ?t } }` — correct but adds latency.

The SQLite flag is consistent with the existing `consecutive_failures` pattern.

### Namespace reference

All namespaces from `transformer.py` top-of-file:
```python
MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"
SCHEMA = "https://schema.org/"
MAK = "urn:mak:"  # (add if not present)
XSD = "http://www.w3.org/2001/XMLSchema#"
```
Check if `MAK` is already defined; if not, add it alongside `MOM` and `SCHEMA`.

### Data integrity: named WARNING counter

Per `feedback_data_integrity_no_silent_drops.md`: every anomaly must increment a named counter, not fold into generic "skipped". Use:
```python
logger.warning("closed_pii_strip space_id=%s consecutive_closed=%d", space_id, consecutive_closed_cycles)
```
This is the same convention as Story 3.2's WARNING counters.

### Testing standards

Per `feedback_integration_testing.md`: live integration tests preferred over mocks for protocol behavior. However, the closed/PII-strip flow is primarily a DB-state + SPARQL-generation concern — unit tests covering the SPARQL output are sufficient here. No new live-network tests needed for 3.2b (Story 3.2 already covers the network path).

Use `pytest.mark.network` for any live tests if added. Existing conftest.py likely has this marker — verify before defining a new one.

### File list (expected changes)

| File | Change type |
|------|------------|
| `infra/link_handler/transformer.py` | UPDATE — `init_db`, `_read_heartbeat_row`, `process_one_space`, `effective_marker`, new `_build_pii_strip_sparql` helper |
| `infra/link_handler/config.yaml` | UPDATE — add `closure:` section |
| `infra/link_handler/test_transformer.py` | UPDATE — add AC7 test cases |
| `_bmad-output/planning-artifacts/epics.md` | UPDATE — completion stamp |
| `_bmad-output/implementation-artifacts/deferred-work.md` | UPDATE — strike FR25b |
| `_bmad-output/implementation-artifacts/sprint-status.yaml` | UPDATE — status → done |

### Project Structure Notes

- All heartbeat logic lives in `infra/link_handler/transformer.py` (imported by `main.py`). Do NOT split into a new file.
- DB path resolved via `HEARTBEAT_DB_PATH` env var or `config.yaml` `bandwidth.heartbeat_log_path`. Follow the same resolution pattern as `_read_heartbeat_row`.
- `build_state_only_update` is the reference for surgical SPARQL writes — the PII strip SPARQL follows the same DELETE/INSERT/WHERE pattern, never `DROP SILENT GRAPH`.
- `effective_marker` in `transformer.py` is the single source of truth for resolved status — update it, don't add a parallel resolver in `main.py` or `materialize_geojson.py`.

### References

- `infra/link_handler/transformer.py` — `init_db` (line ~444), `_read_heartbeat_row` (line ~461), `process_one_space` (line ~621), `build_state_only_update` (line ~252), `_extract_open_now` (line ~217), `effective_marker` (line ~154)
- `infra/link_handler/config.yaml` — existing `endpoint_health` section (reference for `closure` section format)
- `_bmad-output/planning-artifacts/epics.md` — FR25b (line ~60), Story 3.2b inline note (line ~1115)
- `_bmad-output/implementation-artifacts/3-2-freshness-lifecycle-aging-zombie-dead-transitions.md` — dev notes: `build_state_only_update` idempotency, `detect_diff` semantics, WARNING counter pattern
- Memory: `feedback_data_integrity_no_silent_drops.md`, `feedback_integration_testing.md`, `reference_sparql_syntax.md`

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

- Added `consecutive_closed_cycles` and `is_closed` columns to `heartbeat_log` via migration pattern matching `last_content_updated`.
- Used existing `_extract_open_now` (already handles v15 object and v0.13 string) to derive closed signal — no new helper needed.
- Chose SQLite `is_closed` flag (over Oxigraph ASK) for idempotency guard per Dev Notes recommendation.
- `_build_pii_strip_sparql` deletes only `schema:contactJson` and `mom:operationalState`; does NOT touch name, geo, url, logo (confirmed by test).
- Revival prepends `_build_revival_closedAt_delete` SPARQL before the content-update SPARQL (same transaction style as existing multi-statement updates).
- `effective_marker("closed")` added as highest-priority lifecycle state in both `transformer.py` and `materialize_geojson.py` (duplicate kept in sync per existing comment).
- 24 new tests added; all 79 tests pass with no regressions.

### File List

- `infra/link_handler/transformer.py`
- `infra/link_handler/config.yaml`
- `infra/link_handler/test_transformer.py`
- `scripts/materialize_geojson.py`
- `_bmad-output/planning-artifacts/epics.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/3-2-b-mak-closed-pii-strip.md`

### Change Log

- 2026-05-06: Implemented Story 3.2b — `mak:closed` + PII strip on persistent closure, closed-cycle counter, revival logic, `effective_marker` update, DB migration, config, 24 new tests.

## Review Findings

### Story 3.2 findings

- [x] [Review][Decision] AC6 — 304 path always returns `state_changed=True` → FIXED: 304 and failure paths now only set `state_changed=True` when health/lifecycle value actually changed; prior values tracked in `last_endpoint_health`/`last_lifecycle_state` DB columns

- [x] [Review][Patch] `_minutes_since(None)` returns 0.0 → first-ever fetch failure classified as `endpoint_health="healthy"` → FIXED: failure path now uses `float("inf")` when `last_fetched_ts` is None [`transformer.py`]
- [x] [Review][Patch] `effective_marker` duplicated verbatim in `materialize_geojson.py` instead of imported — AC5 violation → FIXED: now imported via `sys.path.insert` [`scripts/materialize_geojson.py`]
- [x] [Review][Patch] `endpoint_health` defaults to `"healthy"` for spaces with no stored triple → FIXED: default changed to `"unknown"` [`main.py`, `scripts/materialize_geojson.py`]

### Story 3.2b findings

- [x] [Review][Patch] Revival DB desync: `is_closed=0` in-memory before SPARQL post — FIXED: end-of-function DB write now wrapped in try/except with WARNING_DB_WRITE_FAILED named counter [`transformer.py`]
- [x] [Review][Patch] AC7: counter mechanics untested behaviorally → FIXED: 4 new behavioral tests added driving `process_one_space` with mocked I/O [`infra/link_handler/test_transformer.py`]

- [x] [Review][Defer] SPARQL injection: `space_uri` f-string interpolated into SPARQL strings without `_sparql_iri` sanitization [`transformer.py` — `_build_pii_strip_sparql`, `build_state_only_update`] — deferred, pre-existing pattern
- [x] [Review][Defer] SQLite read-modify-write on `consecutive_closed_cycles` is not atomic — concurrent manual refreshes could lose counter updates [`transformer.py`] — deferred, pre-existing pattern
- [x] [Review][Defer] `_fetch_last_snapshot` ORDER BY on string snapshot graph URIs relies on lexicographic sort of ISO datetimes — deferred, pre-existing
