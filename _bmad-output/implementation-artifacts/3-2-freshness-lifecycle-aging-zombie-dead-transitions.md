# Story 3.2: Endpoint Health + Space Lifecycle + Open-Now (unified)

Status: ready-for-dev

## Story

As MOM,
I want the heartbeat to interpret each fetch into three independent truth signals — endpoint health, space lifecycle, and dynamic open/closed — and resolve them into a single honest pin on the map,
so that visitors see a marker that reflects what's actually happening at each space, and coordinators get the right freshness incentive (keep `state.open` truthful, not edit JSON monthly to game the clock).

As a maker browsing the map,
I want a green pulsing pin when a space is open right now and a red ✕ when its endpoint is unreachable,
so that I can act on the live information without inspecting raw JSON.

As a coordinator running an automation that toggles `state.open`,
I want my `state.open` flips to count as material updates that reset the lifecycle clock,
so that an automated, honest endpoint never goes "aging" / "zombie" / "dead".

## Context & Dependencies

**Depends on:** Story 3.1 (heartbeat scheduler + `run_heartbeat_cycle` + manual refresh + `consecutive_failures` in `heartbeat_log` + `detect_diff()` in transformer.py).

**Blocks:** Epic 4 operator dashboard (reads `mom:endpointHealth` ladder), Story 3.2b (PII strip on closed), Stories 3.3/3.4 (magic-link nudges triggered by lifecycle transitions).

**Resolves several deferred items in `_bmad-output/implementation-artifacts/deferred-work.md`** — see "Resolved deferrals" section below.

**Epic 7 reframe:** Originally scoped as push/webhook ingest. Heartbeat + honored `state.open` cover the demo's freshness needs. Epic 7 is parked indefinitely; do NOT create webhook stories. The deferred entry "`state` open/closed → green marker → Epic 7" was a stale read-side misclassification — it belongs here.

## The truth model (read this before coding)

Three independent signals, two clocks. The 3.1 UI conflated them; 3.2 separates them cleanly.

### 1. Endpoint health (resets on every 200/304)

Clock: minutes since last successful fetch. Drives whether the endpoint is reachable.

| Time since last good fetch | `mom:endpointHealth` | Public marker contribution |
|----------------------------|----------------------|----------------------------|
| < 10 min                   | `healthy`            | none (lifecycle/open-now decide) |
| 10–30 min                  | `unresponsive`       | none (Epic 4 only)          |
| 30–60 min                  | `warning`            | none (Epic 4 only)          |
| ≥ 60 min                   | `broken`             | red ✕ (only when lifecycle is `confirmed`) |

Thresholds in `config.yaml` under a new `endpoint_health` block. Read at every cycle; never hardcoded (NFR-R3).

### 2. Space lifecycle (resets only on real content diff)

Clock: days since `mom:lastUpdated`. Drives whether the space is alive.

| Time since `mom:lastUpdated` | `mom:operationalState` | Public marker |
|------------------------------|------------------------|---------------|
| < 30 d                       | `confirmed`            | blue / green  |
| 30–90 d                      | `aging`                | ⚠️ yellow      |
| 90–180 d                     | `zombie`               | 🧟 orange      |
| ≥ 180 d                      | `dead`                 | 🪦 grey        |

`dead` renders like any other marker. Hide-by-default is a future UI tweak preset, NOT a backend rule — do not filter `dead` out anywhere in this story.

**Critical invariant — MOM annotates, never fabricates:** when the heartbeat writes `aging` / `zombie` / `dead` to a space's named graph, it MUST NOT touch `mom:lastUpdated`. The lifecycle clock keeps ticking. Only a real content diff from the source flips the space back to `confirmed` and resets the clock.

### 3. Dynamic open/closed (no clock)

Per successful fetch:

- v15 object `state.open` (boolean) → `mom:openNow "true"|"false"^^xsd:boolean`
- v0.13 string `"open"` / `"closed"` → same boolean triple
- v15 `state.lastchange` (epoch sec) → `mom:lastOpenChange`^^xsd:dateTime
- missing/unrecognized → no `mom:openNow` triple emitted; downstream defaults to `false`

**`state.open` flipping IS a material content change.** Do NOT add `state` to `detect_diff()._IGNORED`. A coordinator whose automation toggles `state.open` daily thereby keeps their space `confirmed` forever — this is the designed freshness incentive. SpaceAPI sensor fields (`sensors.*`, `extensions.sensors.*`) DO go to `_IGNORED` — they flap for physical reasons. The split is: `state.*` counts, `sensors.*` doesn't.

### Conflict resolution: lifecycle supersedes endpoint

A dead space whose hosting silently disappears shouldn't masquerade as merely broken. Lifecycle wins.

```python
def effective_marker(endpoint_health: str, lifecycle_state: str, open_now: bool) -> str:
    if lifecycle_state == "dead":   return "dead"
    if lifecycle_state == "zombie": return "zombie"
    if lifecycle_state == "aging":  return "aging"
    if endpoint_health == "broken": return "broken"
    if open_now:                    return "open"
    return "confirmed"
```

Resolved server-side. Single `status` field in GeoJSON. Frontend `markerKind` is unchanged.

## Acceptance Criteria

### AC1 — Two classifier functions replace the current one

**Given** `transformer.py` currently exposes `classify_operational_state(http_status, age_days, consecutive_failures, prior_state)`

**When** the developer refactors

**Then** that function is split into:

- `classify_endpoint_health(http_status, minutes_since_last_good, consecutive_failures) -> tuple[str, str]` — returns one of `healthy | unresponsive | warning | broken` + reason
- `classify_lifecycle(days_since_last_update) -> tuple[str, str]` — returns one of `confirmed | aging | zombie | dead` + reason

**And** thresholds are read from `config.yaml`:

```yaml
endpoint_health:
  unresponsive_minutes_threshold: 10
  warning_minutes_threshold: 30
  broken_minutes_threshold: 60

operational_state:
  aging_days_threshold: 30
  zombie_days_threshold: 90
  dead_days_threshold: 180
```

**And** existing callers are updated; the old `classify_operational_state` function is removed.

**And** negative `age_days` (clock-skew) is clamped to 0 in `classify_lifecycle` with a `WARNING` log entry — resolves deferred item from 3.0 review (2026-05-01).

---

### AC2 — `state.open` extracted and persisted

**Given** a heartbeat fetch returns 200 with a valid SpaceAPI payload

**When** `transform_to_sparql()` builds the per-space SPARQL UPDATE

**Then** a helper `_extract_open_now(state) -> Optional[bool]` returns `True`/`False`/`None` for:

- v15 object: `{"open": true/false, ...}`
- v0.13 string: `"open"` / `"closed"` (case-insensitive, trimmed)
- anything else (missing, `"unknown"`, malformed) → `None`

**And** when non-`None`, the triple `<{space_uri}> mom:openNow "true"|"false"^^xsd:boolean` is appended

**And** when `state.lastchange` is a positive integer, `<{space_uri}> mom:lastOpenChange "{ISO datetime}"^^xsd:dateTime` is appended

**And** when `state` is absent or unrecognized, neither triple is emitted (downstream binding falls back to `false` as today).

---

### AC3 — `mom:endpointHealth` and `mom:operationalState` written every cycle

**Given** a heartbeat cycle runs (success OR failure path)

**When** `process_one_space` finishes per-space processing

**Then** the cycle emits exactly one `mom:endpointHealth` triple and one `mom:operationalState` triple per space, even on 304 / failure paths

**And** these writes are idempotent — `DROP SILENT GRAPH` (already in transformer.py:317) handles the success path; for failure paths use a separate SPARQL UPDATE that surgically replaces only those two triples (`DELETE { ... mom:endpointHealth ?h } INSERT { ... mom:endpointHealth "broken" } WHERE { ... }`) to avoid wiping the rest of the graph

**And** on a successful 304 (no content diff), `mom:lastUpdated` is NOT rewritten

**And** on a 200 with `detect_diff()` returning `None`, `mom:lastUpdated` is NOT rewritten

**And** on a 200 with `detect_diff()` returning a non-`None` diff, `mom:lastUpdated` IS rewritten — this is the only path that resets the lifecycle clock.

---

### AC4 — `detect_diff()` ignore-set updated

**Given** the existing `_IGNORED = {"mom:lastFetched", "mom:snapshotDate", "lastFetched", "snapshotDate"}` (transformer.py:142)

**When** the developer extends it

**Then** `_IGNORED` adds: `"sensors"`, `"extensions"` (covers `extensions.sensors.*`), AND a one-line comment in the code documenting that `state` is intentionally NOT ignored — `state.open` flips are the designed freshness signal.

**And** unit tests verify:

- changing only `sensors.temperature[0].value` → `detect_diff()` returns `None`
- flipping `state.open` true → false → `detect_diff()` returns non-`None` with `state` in the changed list
- changing `location.address` → non-`None`

---

### AC5 — Effective marker resolved server-side; single `status` field

**Given** the SPARQL SELECT in `main.py` (line 68) and `scripts/materialize_geojson.py` (line 33) materialize per-space rows

**When** the materializer builds the GeoJSON binding

**Then** both queries SELECT `?endpointHealth ?operationalState ?openNow` and bind them via `OPTIONAL { ?spaceUri mom:endpointHealth ?endpointHealth }` etc.

**And** a shared helper `effective_marker(endpoint_health, lifecycle_state, open_now)` resolves the public marker per the conflict-resolution rule above

**And** the GeoJSON `status` property is the resolved marker — frontend `markerKind` (web/app.js:243) keeps reading `s.status` and `s.open_now` exactly as today

**And** the raw signals (`endpoint_health`, `operational_state`, `open_now`, `last_open_change`) are also exposed in the GeoJSON binding for Epic 4's operator dashboard.

---

### AC6 — Skip rematerialize when nothing changed

**Given** a heartbeat cycle finishes

**When** neither (a) any state triple changed for any space, nor (b) any content diff was applied

**Then** `_rematerialize_geojson()` is NOT called — log at INFO `"heartbeat cycle: no changes; skipping rematerialize"`

**And** when at least one space had a state OR content change, `_rematerialize_geojson()` is called once for the cycle (not per-space)

**And** the manual refresh endpoint (`POST /api/heartbeat-space/{id}`) follows the same rule — resolves deferred 3.1 review item.

---

### AC7 — Detail-card copy reads the right clock

**Given** `web/app.js:755-764` currently reads `last_fetched` for aging/zombie messages (the 3.1 incoherence)

**When** the developer fixes the copy

**Then**:

- `aging` → `"Going quiet · last content update {timeAgo(last_updated)} ago."`
- `zombie` → `"Unreachable · last content update {timeAgo(last_updated)} ago."`
- `dead` → `"Long inactive · last content update {timeAgo(last_updated)} ago."`
- `broken` → `"Endpoint unreachable · last successful fetch {timeAgo(last_fetched)} ago."`
- `open` → `"Open right now · last content update {timeAgo(last_updated)} ago."`
- `confirmed` → `"Confirmed · last content update {timeAgo(last_updated)} ago."`

**And** `last_updated` in the GeoJSON binding is a full ISO-8601 datetime (not a date-only `YYYY-MM-DD`) — resolves deferred W1 from 2.7 review.

**And** `markerKind` (web/app.js:243) is NOT modified; resolution is server-side.

---

### AC8 — Live integration tests against real SpaceAPI endpoints

**Given** the project's testing-feedback memory: prefer real network calls over mocks

**When** the developer writes the integration test

**Then** `infra/link_handler/test_integration.py` adds three live-fetch cases (mark with the project's existing live-test marker if any, else `pytest.mark.network`):

- `https://mattermore.zeus.gent/spaceapi.json` → expect `mom:openNow` triple written; resolved status MAY be `open` or `confirmed` depending on real-time state — assert presence and validity of the triple, not a specific boolean
- `https://urlab.be/spaceapi.json` → same
- `https://techinc.nl/space/spacestate.json` → same

**And** unit tests in `test_transformer.py` cover:

- v15 object `{"open": true, "lastchange": 1715000000}` → both triples emitted
- v15 object `{"open": false}` → only `openNow false`
- legacy string `"open"` / `"closed"` → boolean triple
- legacy string `"unknown"` → no triple
- missing `state` → no triple
- conflict-resolution matrix (12 cells minimum: 4 endpoint × 4 lifecycle × open_now=true/false where lifecycle == confirmed)
- `detect_diff` ignores `sensors.*`, counts `state.*`

## Tasks

1. **Refactor classifier** (`infra/link_handler/transformer.py`)
   - Split into `classify_endpoint_health` and `classify_lifecycle`. Remove `classify_operational_state`. Update all callsites in `transformer.py` and `main.py`.
   - Clamp negative `age_days`.
2. **Add open-now extraction** (`transformer.py`)
   - `_extract_open_now`, `_extract_last_open_change` helpers. Emit triples in `transform_to_sparql`.
3. **Extend `detect_diff` ignore-set** (`transformer.py:142`)
   - Add `sensors`, `extensions`. One-line comment explaining `state` is intentionally NOT ignored.
4. **State-only graph writes** (`transformer.py` + `main.py`)
   - For 304 and failure paths: surgical SPARQL `DELETE/INSERT` for `mom:endpointHealth` + `mom:operationalState` only. Never touch `mom:lastUpdated` from these paths.
5. **Lifecycle-clock guard** (`transformer.py` `transform_to_sparql`)
   - Only include `mom:lastUpdated` when called from a `200 + detect_diff != None` path. Plumb a `content_changed: bool` flag from caller.
6. **Server-side `effective_marker` resolver** (`transformer.py` + `main.py` + `scripts/materialize_geojson.py`)
   - Shared helper. SELECT new fields. Resolve to single `status` in GeoJSON binding.
7. **Skip rematerialize on no-op cycle** (`main.py` `run_heartbeat_cycle`)
   - Track per-cycle `any_change` flag; only call `_rematerialize_geojson()` when set.
8. **Config block** (`infra/link_handler/config.yaml`)
   - New `endpoint_health` section with three thresholds.
9. **Frontend copy fix** (`web/app.js:755-764`)
   - Lifecycle messages → `last_updated`. Endpoint messages → `last_fetched`. No `markerKind` changes.
10. **Tests** (`test_transformer.py`, `test_integration.py`)
    - Unit + live cases per AC8.
11. **Plan-doc cleanup**
    - Update `_bmad-output/planning-artifacts/epics.md` Story 3.2 ACs (replace with this story's content). Annotate Epic 7 as "deferred indefinitely — heartbeat covers it; do not create stories".
    - Update `_bmad-output/implementation-artifacts/deferred-work.md` per the "Resolved deferrals" list below.
    - Update memory file `project_progress.md` to reflect Epic 7 deferral.

## Resolved deferrals (strike from `deferred-work.md` with resolution date `2026-05-06`)

- 3.1 review: `_rematerialize_geojson` called even on `not_modified` → AC6.
- 3.0-A UX session: `state` open/closed → green marker → Epic 7 → AC2/AC5 here.
- 3.0 review: negative `age_days` from future-dated `Last-Modified` silently returns `confirmed` → AC1 clamp.
- 2.7 review W1: `timeAgo()` receives `YYYY-MM-DD` → AC7 (`last_updated` is full ISO datetime).

## Out of scope (explicitly NOT this story)

- **Story 3.2b** — `mak:closed` + PII contact strip after N consecutive `state.open == false` cycles. Different blast radius (deletion of triples). Add `3-2-b-mak-closed-pii-strip` as a new backlog row in sprint-status.yaml.
- **Epic 4b** — magic-link recovery emails (Stories 3.3 / 3.4).
- **Epic 7** — push/webhooks/hardware ingest. Parked indefinitely.
- UI tweak preset to hide `dead` markers by default — future UI story.
- Epic 4 surfacing of `unresponsive` / `warning` rungs — Epic 4 dashboard story.

## Verification (run after dev complete)

1. `cd infra && distrobox-host-exec docker compose -f docker-compose.dev.yml up -d`
2. Manual heartbeat: `curl -X POST http://localhost:8080/api/heartbeat-space/openfab`
3. SPARQL spot-checks (`localhost:7878/query`):
   - `ASK { GRAPH <urn:mak:space/openfab> { ?s mom:openNow ?o } }` → true after a successful fetch
   - `SELECT ?h ?s WHERE { GRAPH <urn:mak:space/openfab> { ?x mom:endpointHealth ?h ; mom:operationalState ?s } }` → both bound
4. Endpoint-health regression: redirect a known endpoint to a closed port via `/etc/hosts` for 65 min; observe pin → red ✕ at 60-min mark, reverts on first 200.
5. Lifecycle regression: temporarily set `aging_days_threshold: 0`, restart handler, run heartbeat. Pin becomes ⚠️ AND `mom:lastUpdated` is unchanged in the graph.
6. `state.open` reset semantics: hand-craft a snapshot diff that flips only `state.open`; confirm `detect_diff` returns non-`None`, `mom:lastUpdated` is rewritten, lifecycle clock resets.
7. Sensor-no-reset semantics: hand-craft a snapshot diff that changes only `sensors.temperature[0].value`; confirm `detect_diff` returns `None`, `mom:lastUpdated` unchanged.
8. UI counter coherence: detail drawer's aging/zombie/dead lines read "last content update X ago"; broken line reads "last successful fetch X ago".
9. Live integration tests pass: `pytest infra/link_handler/test_integration.py -m network`.

## Developer notes

- **Single source of truth for the resolver.** Implement `effective_marker` once in `transformer.py`; import it in both `main.py` and `scripts/materialize_geojson.py`. If you find yourself copy-pasting the if-ladder, stop.
- **Idempotent state writes.** `DROP SILENT GRAPH` on the success path is fine. For 304 / failure paths, do NOT use `DROP SILENT` — that wipes `mom:lastUpdated`, `schema:openingHours`, etc. and resets the lifecycle clock by accident. Use surgical `DELETE { ... } INSERT { ... } WHERE { ... }` keyed on the two predicates.
- **Conditional GET interaction.** A 304 carries no body, so `state.open` cannot be re-read. Treat `mom:openNow` as last-known-value across 304s — i.e. the surgical state-only update for 304 must NOT touch `mom:openNow`. Only re-evaluate `state.open` on actual 200 bodies.
- **Why server-side resolve.** A future Epic 4 may want raw signals; the public map wants a single resolved status. Exposing both in GeoJSON keeps both consumers happy without duplicating the resolution rule.
- **Test markers.** If `pytest.mark.live` or similar is already declared in `infra/link_handler/conftest.py`, reuse it; otherwise use `pytest.mark.network` and document it in the story branch's commit message.
- **Memory references for context:**
  - `feedback_data_integrity_no_silent_drops.md` — every anomaly in this story (clock skew clamp, missing `state`, malformed lastchange) must increment a named WARNING counter, not silently fold into "skipped".
  - `feedback_integration_testing.md` — live tests against real endpoints, not mocks.
  - `reference_sparql_syntax.md` — ASK pattern for verification.

## Story completion checklist

- [ ] All ACs satisfied with passing tests
- [ ] No regressions on Story 3.1 manual refresh + cooldown UX
- [ ] `epics.md` Story 3.2 section rewritten to match this story
- [ ] `deferred-work.md` resolved entries struck through with date
- [ ] `sprint-status.yaml` flips this row to `done` and adds `3-2-b` backlog row
- [ ] Memory `project_progress.md` updated (Epic 3 progress + Epic 7 deferred)
- [ ] Manual verification steps 1–9 above all pass
