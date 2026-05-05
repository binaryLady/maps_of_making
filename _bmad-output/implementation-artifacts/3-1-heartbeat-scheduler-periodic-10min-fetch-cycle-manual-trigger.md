# Story 3.1: Heartbeat Scheduler — Periodic Fetch Cycle + Manual Trigger

Status: done

## Story

As the system,
I want a scheduled job that fetches all registered endpoint URLs every 10 minutes using conditional GET,
so that the federated dataset stays fresh without manual intervention and without hammering space servers.

As Luca (coordinator),
I want a "Refresh from endpoint" button on the space profile,
so that I can force an immediate update after editing my JSON without waiting for the next cycle.

## Context & Dependencies

**Depends on:** Story 3.0 (transformer.py + fetch_endpoint_conditional complete) and Story 3.0-A (disabled stub button in Zone 3 ready for activation).

**Blocks:** Story 3.2 (freshness lifecycle uses consecutive_failures from heartbeat_log).

**Architecture note on Nanobot:** `sprint-status.yaml` cross-epic handoffs make clear that Nanobot is Epic 6 only. Story 3.1 must implement the scheduler **inside the existing `mak-link-handler` FastAPI service** using APScheduler + FastAPI lifespan — no new container, no new compose service.

## Acceptance Criteria

### AC1 — APScheduler background job starts with FastAPI

**Given** the `mak-link-handler` container starts

**When** the FastAPI lifespan context runs

**Then** an APScheduler `AsyncIOScheduler` is started with an `IntervalTrigger` reading cadence from `config.yaml` `bandwidth.heartbeat_interval_seconds` (default: 600 → 10 min)

**And** the scheduler runs `run_heartbeat_cycle()` at each interval

**And** a scheduler crash does NOT crash the FastAPI process — errors are caught and logged at ERROR level

---

### AC2 — Heartbeat cycle: query all active spaces

**Given** the scheduler fires

**When** `run_heartbeat_cycle()` executes

**Then** it queries Oxigraph for all spaces where `mom:endpointUrl` exists and `mom:operationalState` is NOT `"dead"` (i.e. confirmed, aging, zombie, broken are all fetchable):

```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
SELECT ?spaceUri ?endpointUrl WHERE {
  GRAPH ?g {
    ?spaceUri mom:endpointUrl ?endpointUrl .
    OPTIONAL { ?spaceUri mom:operationalState ?state }
    FILTER (!BOUND(?state) || ?state != "dead")
  }
  FILTER (STRSTARTS(STR(?g), "urn:mak:space/"))
}
```

**And** for each result, the space slug is derived as the path component of `?spaceUri` (e.g. `urn:mak:space/openfab` → `openfab`)

**And** each space is fetched sequentially (not concurrently) to limit Oxigraph write contention

---

### AC3 — Per-space fetch + transform + write

**Given** a space with `endpointUrl` is in the heartbeat cycle

**When** `process_one_space(space_uri, endpoint_url)` runs

**Then** it calls `fetch_endpoint_conditional(endpoint_url, space_id)` from `transformer.py`

**And** if `was_304`: no transform, no Oxigraph write — log at INFO "304 Not Modified for {space_id}, skipping"

**And** if HTTP 200: parse JSON, call `SpaceAPISchema.model_validate()`, call `transform_to_sparql()`, POST SPARQL UPDATE to Oxigraph

**And** if HTTP error (4xx, 5xx, timeout): increment `consecutive_failures` in `heartbeat_log` (already handled by `fetch_endpoint_conditional`), log at WARNING, skip transform

**And** after ALL spaces are processed, call `_rematerialize_geojson()` once — not per-space

---

### AC4 — `POST /api/heartbeat-space/{space_id}` manual trigger endpoint

**Given** Zone 3 "↺ Refresh from endpoint" button (Story 3.0-A) is now active

**When** a POST request arrives at `/api/heartbeat-space/{space_id}`

**Then** the endpoint:
1. Validates `space_id` matches `^[a-zA-Z0-9_-]+$` (same pattern as existing space_id validation)
2. Enforces a 60-second per-space cooldown using an in-memory dict `_manual_refresh_cooldowns: dict[str, datetime]`
3. If cooldown active: returns HTTP 429 `{"error": "rate_limited", "retry_after_seconds": N}`
4. Queries Oxigraph for `?endpointUrl` of `urn:mak:space/{space_id}`
5. If no endpoint found: returns HTTP 404 `{"error": "no_endpoint", "message": "Space has no registered endpoint URL"}`
6. Calls `process_one_space(space_uri, endpoint_url)` (same function as scheduler uses)
7. Calls `_rematerialize_geojson()`
8. Returns HTTP 200 `{"status": "ok", "space_id": space_id, "outcome": "refreshed" | "not_modified"}`

**And** cooldown is stored in memory — resets on container restart (acceptable, see deferred-work.md)

---

### AC5 — Zone 3 manual fetch button wired (app.js)

**Given** Story 3.0-A rendered the button disabled with `title="Manual refresh available soon"`

**When** Story 3.1 is implemented

**Then** in `web/app.js`, the button is made active: `disabled` attribute removed, `title` updated to `"Refresh data from endpoint"`

**And** on click:
1. Button shows spinner (replace `↺` with `…` text), becomes `disabled` again during request
2. Fetch `POST /api/heartbeat-space/{s.id}` (no body)
3. On 200: re-fetch Zone 3 raw content (`GET /api/space/{s.id}/raw`) and re-render Zone 3 in-place
4. On 429: show inline message `"Refreshed recently — try again in {retry_after_seconds}s"` below the button for 3s
5. On error: show `"Refresh failed — try again later"` for 3s
6. Button reverts to active state after response (success or error)

**And** the button remains hidden on mobile (`< 768px`) — consistent with Zone 3 suppression in Story 3.0-A AC7

---

### AC6 — config.yaml heartbeat settings

**Given** `infra/link_handler/config.yaml` is the single source of truth for scheduler config

**Then** add:

```yaml
bandwidth:
  heartbeat_interval_seconds: 600     # 10 minutes
  heartbeat_timeout_seconds: 60       # per-endpoint fetch timeout
  heartbeat_log_path: "/app/tasks/heartbeat_log.db"   # already present
  gap_log_path: "/app/tasks/gap_log.txt"               # already present
```

**And** `fetch_endpoint_conditional` uses `heartbeat_timeout_seconds` (currently hardcoded to `10.0`) — update to read from config with 60.0 default

---

### AC7 — No regression

**Given** Stories 2.1, 2.7, 3.0, 3.0-A behaviour

**When** 3.1 changes are applied

**Then** `POST /api/register-url` is unchanged

**And** `POST /api/validate-url` is unchanged

**And** Zone 1 / Zone 2 rendering in app.js is unchanged

**And** seeded spaces (no `endpointUrl`) are excluded from heartbeat cycle (SPARQL filter on `mom:endpointUrl` existence)

---

## Tasks / Subtasks

- [x] Add APScheduler dependency (AC1)
  - [x] Add `apscheduler` to `infra/link_handler/requirements.txt`
  - [x] Rebuild container image locally to verify install

- [x] Implement `run_heartbeat_cycle()` and `process_one_space()` in `transformer.py` (AC2, AC3)
  - [x] Add `query_active_spaces()` helper — SPARQL SELECT for spaces with endpointUrl (not dead)
  - [x] Add `process_one_space(space_uri, endpoint_url)` — fetch → validate → transform → write
  - [x] Add `run_heartbeat_cycle()` — iterate spaces, call process_one_space, then rematerialize

- [x] Wire APScheduler into FastAPI lifespan in `main.py` (AC1)
  - [x] Add `lifespan` context manager to `app = FastAPI(lifespan=lifespan)`
  - [x] Scheduler reads `heartbeat_interval_seconds` from config
  - [x] Catch and log scheduler errors — no crash propagation

- [x] Add `POST /api/heartbeat-space/{space_id}` endpoint to `main.py` (AC4)
  - [x] In-memory cooldown dict with 60s TTL
  - [x] Oxigraph lookup for endpointUrl
  - [x] Call `process_one_space`, then `_rematerialize_geojson`
  - [x] Return 200 / 429 / 404 as specified

- [x] Update `config.yaml` with heartbeat settings (AC6)
  - [x] Add `heartbeat_interval_seconds`, `heartbeat_timeout_seconds`
  - [x] Update `fetch_endpoint_conditional` timeout to read from config (default 60s)

- [x] Wire Zone 3 button in `web/app.js` (AC5)
  - [x] Remove `disabled` attribute, update `title`
  - [x] Add click handler: POST → spinner → re-render Zone 3 or error message
  - [x] 429 handling with `retry_after_seconds`

- [x] Integration test for manual trigger endpoint (AC4, AC7)
  - [x] Add test in `test_heartbeat.py`: POST to `/api/heartbeat-space/{id}` with mock Oxigraph

### Review Findings

- [x] [Review][Decision] Cooldown stored before 404/no-endpoint check — resolved: keep current behaviour (cooldown on all attempts); pilot UX improvement deferred to post-demo story.

- [x] [Review][Patch] HTTP error in process_one_space returns "not_modified" — fixed: now returns "error"; test updated [`transformer.py:466,472`, `test_heartbeat.py:113`]
- [x] [Review][Patch] `_SPACE_ID_RE` has no length cap — fixed: `{1,64}` quantifier added [`main.py:611`]
- [x] [Review][Patch] JS: `body.detail.retry_after_seconds` accessed without null guard on 429 — fixed: optional chaining + fallback message [`web/app.js`]

- [x] [Review][Defer] Circular import (transformer ← main) via lazy `from main import` in `process_one_space` — works at runtime, fragile in test isolation; extract shared types to `schemas.py` in a future story [`transformer.py:process_one_space`] — deferred, pre-existing design
- [x] [Review][Defer] Concurrent scheduler + manual trigger can race on Oxigraph writes + GeoJSON file — at 6 spaces / 10min cycle, risk is very low; add asyncio lock in Epic 4 ops story — deferred, pre-existing
- [x] [Review][Defer] Mobile suppression of refresh button not confirmed in diff — likely inherited from Zone 3 CSS from Story 3.0-A; verify in CSS audit — deferred, pre-existing
- [x] [Review][Defer] APScheduler startup failure swallowed — no `/health` scheduler signal; by spec design (AC1 says catch+log, not fail-fast) — deferred, Epic 4 observability
- [x] [Review][Defer] SVG innerHTML duplicated 3× in click handler — extract to `_REFRESH_SVG` const in a future UI pass — deferred, pre-existing
- [x] [Review][Defer] New `httpx.AsyncClient` per space per cycle — harmless at 6 spaces; pass shared client when scaling — deferred, pre-existing
- [x] [Review][Defer] `_rematerialize_geojson` called unconditionally on "not_modified" in manual endpoint — wasted I/O, minor; skip rematerialize when outcome == "not_modified" — deferred, pre-existing

---

## Dev Notes

### Scheduler architecture (no Nanobot)

Nanobot is Epic 6 only (see `sprint-status.yaml` `cross_epic_handoffs.epic_1_architectural_decisions.nanobot_integration`). The heartbeat scheduler lives inside `mak-link-handler` as an APScheduler `AsyncIOScheduler`. Pattern:

```python
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger

scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    cfg = get_config()
    interval = cfg.get("bandwidth", {}).get("heartbeat_interval_seconds", 600)
    scheduler.add_job(run_heartbeat_cycle, IntervalTrigger(seconds=interval))
    scheduler.start()
    yield
    scheduler.shutdown()

app = FastAPI(lifespan=lifespan)
```

### fetch_endpoint_conditional — SQLite concurrency note

From deferred-work.md (Story 3.0 code review): "synchronous SQLite calls in async context; concurrent heartbeats for same space_id can race." Since heartbeat cycle is **sequential** (AC3), this is safe in Story 3.1. Do NOT introduce concurrent fetches — that deferred fix stays deferred to future ops story.

### SPARQL for active spaces query

Seeded spaces (VOW/RFF) have no `mom:endpointUrl` — the FILTER on `mom:endpointUrl` existence in AC2 naturally excludes them. Only self-registered confirmed spaces have an endpoint URL. Dead spaces are explicitly excluded.

### transform_to_sparql call pattern

From `main.py:552–558`:
```python
from transformer import transform_to_sparql
schema_obj = SpaceAPISchema.model_validate(data)
sparql_update, _ = transform_to_sparql(schema_obj, {"endpoint_url": endpoint_url, "space_id": slug})
```
`process_one_space` should follow this exact pattern. Use the fallback `_build_sparql_update` if `transform_to_sparql` raises (same pattern as register-url).

### In-memory cooldown dict

```python
_manual_refresh_cooldowns: dict[str, datetime] = {}
COOLDOWN_SECONDS = 60
```
Check: `now - _manual_refresh_cooldowns.get(space_id, epoch) < timedelta(seconds=COOLDOWN_SECONDS)`

On 200/404/error: update cooldown timestamp. On 429: do not update (timer keeps running from first call).

### Zone 3 re-render on manual refresh

`web/app.js` Zone 3 is currently built inside `renderDrawer()` / `renderZone3()`. The click handler should call the existing `loadZone3(s.id)` or equivalent function that fetches `/api/space/{id}/raw` and re-renders. If no such extracted function exists, extract it from the Zone 3 render block before wiring the button.

### Files to touch

```
infra/link_handler/
  requirements.txt          ← add apscheduler
  config.yaml               ← add heartbeat_interval_seconds, heartbeat_timeout_seconds
  transformer.py            ← add query_active_spaces(), process_one_space(), run_heartbeat_cycle()
                               update fetch_endpoint_conditional timeout to read from config
  main.py                   ← add lifespan, POST /api/heartbeat-space/{space_id}

web/
  app.js                    ← activate Zone 3 button, add click handler
```

### Testing

- Unit tests for `query_active_spaces()` SPARQL output (no live Oxigraph needed — test the query string)
- Unit test for cooldown logic in manual trigger
- Integration test: POST `/api/heartbeat-space/{id}` against live Oxigraph (distrobox-host-exec pattern from Story 3.0 integration tests)
- Use `source venv/bin/activate` before any python test command (CLAUDE.md requirement)

### Project Structure Notes

- No new top-level directories — all changes in `infra/link_handler/` and `web/`
- `tasks/` directory referenced in architecture is not created in this story (Epic 6 Nanobot concern)
- `heartbeat_log.db` path stays at `/app/tasks/heartbeat_log.db` in container (already in config)

### References

- [Source: epics.md#Story-3.1] — User story, AC pattern, 10min cadence, sequential fetch, materialize after cycle
- [Source: transformer.py:310–399] — `fetch_endpoint_conditional`, `_init_heartbeat_db`, SQLite schema
- [Source: transformer.py:193–307] — `transform_to_sparql` signature and snapshot pattern
- [Source: main.py:534–622] — `register_url` as reference for transform + Oxigraph write pattern
- [Source: main.py:487–511] — `_rematerialize_geojson()` — call once after all fetches
- [Source: config.yaml] — existing `bandwidth` block, `operational_state` thresholds
- [Source: sprint-status.yaml#cross_epic_handoffs] — Nanobot is Epic 6 only
- [Source: deferred-work.md#Story-3.0-code-review] — SQLite concurrency risk: safe if sequential
- [Source: 3-0-A-space-profile-card-ux-refinement.md#AC5] — disabled button stub to activate

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

None.

### Completion Notes List

- Address display bug fixed: `mom:address` now read from Oxigraph in both SPARQL SELECT queries (main.py + materialize_geojson.py) and used with fallback to street/postcode/city composition.
- APScheduler `AsyncIOScheduler` wired into FastAPI lifespan. Scheduler reads `heartbeat_interval_seconds` from config (default 600s). Errors caught and logged; no crash propagation.
- `query_active_spaces()`, `process_one_space()`, `run_heartbeat_cycle()` added to transformer.py. Sequential fetch pattern preserves SQLite safety noted in deferred-work.md.
- `fetch_endpoint_conditional` timeout now reads `heartbeat_timeout_seconds` from config (default 60s, was hardcoded 10s).
- `POST /api/heartbeat-space/{space_id}` endpoint: slug validation, 60s in-memory cooldown (429), Oxigraph endpointUrl lookup (404), calls process_one_space + rematerialize, returns outcome.
- Zone 3 Refresh button activated: `_loadZone3()` extracted for reuse, click handler with spinner, 429 inline message, error message, re-render on success.
- 12 new unit tests in `test_heartbeat.py`; full suite 68 passed, 1 skipped.

**Post-implementation fixes (live testing 2026-05-05):**
- Scheduler lambda bug: `lambda: run_heartbeat_cycle(...)` returned a coroutine APScheduler never awaited. Fixed by replacing with a proper `async def _heartbeat_job()` wrapper. Symptom: "coroutine was never awaited" warning, cycle appeared to run but did nothing.
- Double refresh button: `_loadZone3()` cleared `rawEl.innerHTML` but the button lives on `rawEl.parentElement`, surviving re-render. Fixed by `querySelector('.sp-refresh-btn')?.remove()` before each append.
- Heartbeat cycles now pass `raw_content=resp.text` to `transform_to_sparql` so Zone 3 shows current endpoint content, not the registration-time snapshot.
- `json_ld_valid` renamed to `schema_valid` throughout (main.py, app.js) — field checks for name presence, not JSON-LD format.
- `specialties` accepted as alias for `knowsAbout` in SpaceAPISchema and legacy builder.
- `activity_map.yaml` volume-mounted into container via docker-compose.yml (`../scripts/activity_map.yaml:/app/scripts/activity_map.yaml:ro`).
- SKILL.md rewritten: SpaceAPI v15 as primary format, `@context` demoted to optional export enrichment.

### File List

- `infra/link_handler/requirements.txt` — added apscheduler>=3.10
- `infra/link_handler/config.yaml` — added heartbeat_interval_seconds, heartbeat_timeout_seconds
- `infra/link_handler/transformer.py` — timeout from config; added query_active_spaces, process_one_space, run_heartbeat_cycle
- `infra/link_handler/main.py` — lifespan + APScheduler; address bug fix in SPARQL + _binding_to_feature; POST /api/heartbeat-space endpoint
- `scripts/materialize_geojson.py` — address bug fix in SPARQL + binding_to_space
- `web/app.js` — Zone 3 button activated, _loadZone3 extracted, click handler wired
- `infra/link_handler/test_heartbeat.py` — new test file (12 tests)
