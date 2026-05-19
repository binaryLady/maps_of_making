# Story 3.6: Walking Skeleton — Clean Snapshot Pipeline on the Canary

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->
<!-- Re-architected 2026-05-19 via correct-course (sprint-change-proposal-2026-05-19.md):
     snapshot-as-unit clean rebuild, replacing the earlier "carry one token through the
     existing five-stage pipeline" framing. -->

## Story

As the operator of the Maps of Making ingestion pipeline,
I want a new, clean snapshot pipeline built end-to-end on the Mother Sands canary — `{payload + observed_at + UID}` minted at fetch, carried byte-identical through Oxigraph and a minimal GeoJSON to a live age in the browser — running *alongside* the existing pipeline,
so that the propagation contract is proven on day one against clean code rather than grafted onto the noisy `heartbeat_log` / fat-transformer pipeline, and Stories 3.7–3.10 migrate registered spaces onto a working clean target.

## Context

This is the **first story of Epic 3.5 — Freshness Propagation Contract** (`epics.md` §"Epic 3.5"), and it is a **walking skeleton / thin vertical slice** — a clean rebuild, not a patch.

Epic 3 shipped a five-stage chain for one fact about a space — endpoint JSON → `heartbeat_log.db` (SQLite) → Oxigraph named graph → `web/data/spaces.geojson` → browser. Every retro bug lived at a *seam* where a stage stamped its own "now," and `heartbeat_log.db` accumulated independently-stamped derived columns (`last_fetched`, `last_content_updated`, `last_endpoint_health`, `last_lifecycle_state`, `is_closed`…). That is the retro-3 bug class.

**Corrected approach (operator decision 2026-05-19, `sprint-change-proposal-2026-05-19.md`).** Earlier the plan was to carry a clean `observed_at` token through that *existing* pipeline. Operator review rejected it: building a clean token on a noisy foundation builds on noise. Story 3.6 instead builds a **new, clean snapshot pipeline alongside the existing one**, exercised on the Mother Sands canary only. The old `heartbeat_log` / transformer path is **not touched** and keeps serving registered spaces — zero regression risk during 3.6. Stories 3.7–3.10 then migrate registered spaces onto the clean path and *delete* the old code wholesale.

**The model — the snapshot is the unit.** A successful fetch of a reachable endpoint produces one **snapshot**: the JSON payload + the UTC instant it was observed (`observed_at`) + the space UID. The snapshot is the single source of truth; every lifecycle fact is *derived* from it, never independently stamped.

**The discipline that makes a skeleton safe:** the skeleton may hardcode, shortcut, or single-case anything **except the token's identity**. `observed_at` is minted exactly once, at fetch, and must be byte-identical at every downstream stage. If you find yourself re-stamping it, stop — that is the bug class this epic exists to kill.

## Acceptance Criteria

1. **Snapshot minted once.** On a successful (HTTP 200) Mother Sands canary heartbeat fetch, one snapshot is created — JSON payload + `observed_at` (UTC ISO instant generated at fetch time) + space UID — and stored in the new clean snapshot store. `observed_at` is minted exactly once, here.
2. **Clean store, not `heartbeat_log`.** The snapshot store is a new, dedicated store keyed by space UID. It does **not** add columns to `heartbeat_log.db`. Minimal fields only: UID, `observed_at`, payload, `etag`/`last_modified`.
3. **Carried to Oxigraph.** The clean transform reads `observed_at` from the snapshot — never regenerates it — and writes a single `mom:observedAt` triple into the `urn:mak:canary` graph.
4. **Carried to GeoJSON, minimal.** The canary feature in `web/data/spaces.geojson` carries only render-critical fields — geolocation, UID, `properties.observed_at`. `observed_at` is copied, not regenerated.
5. **Read by the browser.** `web/app.js` reads `properties.observed_at` and renders a live `age = now − observed_at` value for the canary marker (raw age display is sufficient — lifecycle *bucketing* is Story 3.10).
6. **Byte-identical end-to-end.** The `observed_at` value is string-equal at all four downstream observation points (snapshot store, `mom:observedAt` triple, GeoJSON property, browser-read value).
7. **Old path untouched.** The existing `heartbeat_log` / transformer path for registered spaces is unchanged — no schema edits, no behavior change. Verified by the existing test suite still passing.
8. **`datetime.now()` audit doc exists.** A document (`3-6-datetime-audit.md`) inventories every `datetime.now()` / `utcnow()` call in `infra/link_handler/transformer.py`, `infra/link_handler/main.py`, and `scripts/materialize_geojson.py`, each with `file:line`, the payload it feeds, and a **carry vs. generate** verdict naming the Epic 3.5 story that will re-wire or delete it. This audit is the input that tells 3.7–3.9 which stamps to delete.
9. **Gating test green** — `test_observed_at_skeleton_e2e` (see below).
10. **Operator visual confirmation.** Nicolas loads the live map and confirms the canary marker shows a live, advancing age derived from the token. A green pytest exit alone is not "done."
11. **DoD gate.** `make canary-report` is all-green after this story.

## Gating Test — `test_observed_at_skeleton_e2e`

Full-stack, live canary, **real seams only — no mocked snapshot store, no mocked Oxigraph, no mocked HTTP**:
1. Run one clean fetch cycle against the live Mother Sands canary endpoint.
2. Read `observed_at` from the snapshot store row → call it `T`.
3. SPARQL-SELECT `mom:observedAt` from `urn:mak:canary` → assert `== T` exactly.
4. Read the canary feature's `properties.observed_at` from `spaces.geojson` → assert `== T` exactly.
5. Assert the value `web/app.js` reads/derives age from `== T` exactly.

Place the test in `infra/link_handler/` alongside the existing `test_*.py` suite.

## Tasks / Subtasks

- [ ] Task 1: `datetime.now()` carry/generate audit (AC: #8)
  - [ ] Walk `transformer.py`, `main.py`, `scripts/materialize_geojson.py` for `datetime.now` / `utcnow`
  - [ ] For each: record `file:line`, payload/variable fed, persisted-vs-transient, carry/generate verdict, and the owning later story (3.7/3.8/3.9) for anything to be migrated or deleted
  - [ ] Save to `_bmad-output/implementation-artifacts/3-6-datetime-audit.md`
- [ ] Task 2: Define and create the clean snapshot store (AC: #2)
  - [ ] Decide the storage mechanism — recommend a new dedicated SQLite table/file (e.g. `snapshot_store`) keyed by UID, holding `payload`, `observed_at`, `etag`, `last_modified`. SQLite TEXT/BLOB handles the payload (1GB limit; payloads are KB).
  - [ ] Do NOT add columns to `heartbeat_log.db`
- [ ] Task 3: Clean fetch path — mint the snapshot for the canary (AC: #1)
  - [ ] On a successful (HTTP 200) canary fetch, stamp `observed_at` once and write `{payload, observed_at, etag, last_modified}` to the snapshot store keyed by the canary UID
  - [ ] Happy path only — 304 / unreachable handling is Story 3.7
- [ ] Task 4: Clean transform — carry into Oxigraph as `mom:observedAt` (AC: #3)
  - [ ] Read `observed_at` from the snapshot store and write one `mom:observedAt` triple into `urn:mak:canary`
  - [ ] Do NOT call `datetime.now()` for this value — copy only
- [ ] Task 5: Minimal canary materialization into GeoJSON (AC: #4)
  - [ ] The canary feature carries geolocation, UID, and `properties.observed_at` — nothing else needed for the skeleton
  - [ ] Copy `observed_at`, never regenerate
- [ ] Task 6: Render live age in the browser (AC: #5)
  - [ ] `web/app.js` reads `properties.observed_at`, computes `age = now − observed_at`, shows it on the canary marker/card (reuse the existing `timeAgo()` helper)
- [ ] Task 7: Write and pass `test_observed_at_skeleton_e2e` (AC: #6, #9)
- [ ] Task 8: Verify (AC: #7, #10, #11)
  - [ ] Existing `heartbeat_log`/transformer test suite still green (old path untouched)
  - [ ] `make canary-report` all-green
  - [ ] Operator visual confirmation with Nicolas on the live map

## Dev Notes

### Skeleton discipline — what may and may not be shortcut

| May shortcut in 3.6 | May NOT shortcut |
|---|---|
| One space only (Mother Sands canary) | Re-minting `observed_at` at any stage |
| Happy path only — HTTP 200 (304/unreachable = Story 3.7) | Letting the value drift between stages |
| Raw age display, no buckets (buckets = Story 3.10) | Skipping any of the pipeline stages |
| Crude `mom:observedAt` write, full hardening later | Mocking a seam in the gating test |
| Canary-only clean path; old pipeline untouched | Touching / patching the old `heartbeat_log` schema |

### The two pipelines run side by side

Story 3.6 deliberately leaves the legacy pipeline alone:
- **Legacy path** (registered spaces): `heartbeat_log.db` + `transformer.py` `_build_sparql_update` + fat `materialize_geojson.py` → unchanged.
- **Clean path** (canary only, NEW): clean snapshot store → clean transform → minimal canary GeoJSON feature → browser age.

There is no shared mutable state between them beyond Oxigraph (different named graphs: `urn:mak:canary` vs `urn:mak:space/*`) and the `spaces.geojson` file (different features). Stories 3.7–3.9 collapse the legacy path into the clean one, space by space, and delete the legacy code.

### `datetime.now()` inventory (starting point — verify, do not trust blindly)

`grep` baseline at commit `e9fa797`:

**`infra/link_handler/transformer.py`**
- L68 — gap-log line timestamp → likely **generate** (diagnostics).
- L179 (`_build_pii_strip_sparql`) — lifecycle event time → likely **generate**; confirm it does not feed `observedAt`-adjacent fields.
- L317 — `datetime.fromtimestamp` parsing SpaceAPI `lastchange`; not a `now()` call, out of scope.
- L402 `now` / L403 `snapshot_date` — **hot zone (legacy path).** `now` feeds `mom:lastUpdated`/`lastFetched`-class triples on the legacy DROP+INSERT write path → classify **carry**, owner Story 3.8 (delete when registered spaces migrate). `snapshot_date` is a structural named-graph suffix → **generate**.
- L521 — `mom:snapshotDate` written to the snapshot graph as transform-time `now` → classify **carry**, owner Story 3.8 (this is a stale-stamp; the clean model derives it from `observed_at`).
- L624 — legacy heartbeat SQLite write path → **generate** in the legacy path; the clean path mints `observed_at` separately in Task 3.
- L670 — post-200 ETag/Last-Modified handling, fetch-time region.
- L747 / L759 (`_days_since` / `_minutes_since`) — transient server-side age math feeding `endpoint_health` / `lifecycle_state` triples. Classify **generate — TRANSITIONAL, remove in Story 3.10** (end state = age-math in the browser).
- L808 `_now_304` — 304-path `lastFetched` refresh → **carry**, owner Story 3.7.

**`infra/link_handler/main.py`** — L39/L668 (`_last_heartbeat_completed`, scheduler bookkeeping → generate), L478, L687, L795 (`snapshot_date` → generate). Verify L478/L687 payloads.

**`scripts/materialize_geojson.py`** — grep showed no `datetime.now`; the file-level `generated_at` field is introduced later (Story 3.9), not here.

### Architecture constraints

- Canonical namespace: `https://nicolasdb.github.io/mapsofmaking_ontology/ns#`.
- `observed_at` = wall-clock UTC instant of a *successful* fetch — NOT SpaceAPI's optional `lastchange`.
- Canary writes route to the `urn:mak:canary` graph; subject URI `urn:mak:canary/mother-sands`. The clean path uses this graph directly (existing `is_canary` branch is the reference; the clean transform may be a separate function — it need not reuse `_build_sparql_update`).
- The clean snapshot store is new — do not extend `heartbeat_log.db`. SQLite is a fine backing store (TEXT/BLOB ≤ 1GB; SpaceAPI payloads are a few KB).
- **Scope guard (epics.md):** do NOT pull in `fetch_status` / 304 rules (3.7), transform-stamp deletion / registered-space migration (3.8), multi-space materializer + GeoJSON slimming for registered spaces (3.9), lifecycle bucketing (3.10), retry logic, or ontology work. 3.6 builds ONE clean canary slice. Nothing else.

### Project Structure Notes

- Gating test in `infra/link_handler/` to join the existing `test_*.py` suite + `conftest.py`.
- Audit doc in `_bmad-output/implementation-artifacts/` next to this story.
- `make canary-report` is the live DoD gate (Epic 3 retro Actions 2/3).

### Previous Story Intelligence (Story 3.5)

Story 3.5 (`core.ttl` + `crosswalk.csv`) was static-artifact only — no transformer changes. The `ext_mom.canary: true` write-routing flag deferred from 3.4b → 3.5 was missed (3.5 was static-only) and remains unimplemented; do not build 3.6 on it — the clean path targets the canary by UID directly.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3.5 — Story 3.6]
- [Source: _bmad-output/planning-artifacts/sprint-change-proposal-2026-05-19.md]
- [Source: _bmad-output/implementation-artifacts/epic-3-retro-2026-05-18.md#Addendum — Party-Mode Roundtable Deep-Dive]
- [Source: infra/link_handler/transformer.py — lines 68, 179, 402-403, 521, 624, 670, 742-759, 808]
- [Source: infra/link_handler/main.py — lines 27, 39, 478, 668, 687, 795]
- [Source: CLAUDE.md — "Changes development sequence from horizontal layers to vertical slices"]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
