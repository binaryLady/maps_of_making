# Story 3.6: Walking Skeleton — `observed_at` End-to-End on the Canary

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As the operator of the Maps of Making ingestion pipeline,
I want a single `observed_at` freshness token minted once at the canary heartbeat fetch and carried — byte-identical — through all five pipeline stages to a live age shown in the browser,
so that the propagation contract is proven working end-to-end on day one, before any seam is hardened, and Stories 3.7–3.10 each refactor against a working target instead of a guess.

## Context

This is the **first story of Epic 3.5 — Freshness Propagation Contract** (`epics.md` §"Epic 3.5"), and it is deliberately a **walking skeleton / thin vertical slice**, not a horizontal layer.

Epic 3 shipped a five-stage chain for one fact about a space — endpoint JSON → `heartbeat_log.db` (SQLite) → Oxigraph named graph → `web/data/spaces.geojson` → browser — and every retro bug lived at a *seam* where a stage stamped its own "now." The fix is one token, `observed_at`, minted once at a successful heartbeat fetch and carried unchanged.

The original Epic 3.5 plan built that token up stage-by-stage (audit → SQLite → Oxigraph → GeoJSON → browser) and only proved end-to-end behavior at story five — horizontal layering, which contradicts the project's vertical-slice principle (CLAUDE.md). **Restructured 2026-05-18:** 3.6 is now a thin slice that gets the token from canary fetch to browser age *immediately*; 3.7–3.10 then harden each seam against that working slice.

**The discipline that makes a skeleton safe:** the skeleton may hardcode, shortcut, or single-case anything **except the token's identity**. `observed_at` is minted exactly once and must be byte-identical at every stage. If you find yourself re-stamping it "just to make the slice work," stop — that is the bug class this epic exists to kill.

## Acceptance Criteria

1. **Minted once.** On a successful Mother Sands canary heartbeat fetch, an `observed_at` UTC ISO instant is generated at fetch time and written to `heartbeat_log.db`. It is the *only* mint point.
2. **Carried to Oxigraph.** The transformer copies that `observed_at` — never regenerates it — into the canary named graph as a single `mom:observedAt` triple.
3. **Carried to GeoJSON.** The materialization step copies `observed_at` into the canary feature's `properties.observed_at` in `web/data/spaces.geojson`.
4. **Read by the browser.** `web/app.js` reads `properties.observed_at` and renders a live `age = now − observed_at` value for the canary marker (raw age display is sufficient for the skeleton — lifecycle *bucketing* is Story 3.10).
5. **Byte-identical end-to-end.** The `observed_at` value is string-equal at all four downstream observation points (SQLite row, `mom:observedAt` triple, GeoJSON property, browser-read value).
6. **`datetime.now()` audit doc exists.** A document (`3-6-datetime-audit.md`) inventories every `datetime.now()` / `utcnow()` call in `infra/link_handler/transformer.py`, `infra/link_handler/main.py`, and `scripts/materialize_geojson.py`, each with `file:line`, the payload it feeds, and a **carry vs. generate** verdict naming the Epic 3.5 story that will re-wire it. This audit is the input that tells 3.7–3.9 which stamps to delete.
7. **Gating test green** — `test_observed_at_skeleton_e2e` (see below).
8. **Operator visual confirmation.** Nicolas loads the live map and confirms the canary marker shows a live, advancing age derived from the token. A green pytest exit alone is not "done."
9. **DoD gate.** `make canary-report` is all-green after this story.

## Gating Test — `test_observed_at_skeleton_e2e`

Full-stack, live canary, **real seams only — no mocked SQLite, no mocked Oxigraph, no mocked HTTP**:
1. Inject a canary state and run one heartbeat cycle against the live canary endpoint.
2. Read `observed_at` from the `heartbeat_log.db` row → call it `T`.
3. SPARQL-SELECT `mom:observedAt` from the canary graph → assert `== T` exactly.
4. Read the canary feature's `properties.observed_at` from `spaces.geojson` → assert `== T` exactly.
5. Assert the value `web/app.js` reads/derives age from `== T` exactly.

Place the test in `infra/link_handler/` alongside the existing `test_*.py` suite.

## Tasks / Subtasks

- [ ] Task 1: `datetime.now()` carry/generate audit (AC: #6)
  - [ ] Walk `transformer.py`, `main.py`, `scripts/materialize_geojson.py` for `datetime.now` / `utcnow`
  - [ ] For each: record `file:line`, the payload/variable fed, persisted-vs-transient, carry/generate verdict, and (if carry) the owning later story
  - [ ] Save to `_bmad-output/implementation-artifacts/3-6-datetime-audit.md`
- [ ] Task 2: Mint `observed_at` at the canary heartbeat fetch (AC: #1)
  - [ ] In the heartbeat fetch path, stamp `observed_at` once on a successful (HTTP 200) canary fetch
  - [ ] Write it to `heartbeat_log.db` (add a column if needed — minimal; `fetch_status` rules are Story 3.7)
- [ ] Task 3: Carry into Oxigraph as `mom:observedAt` (AC: #2)
  - [ ] Transformer reads `observed_at` from the SQLite row and writes one `mom:observedAt` triple into the canary graph
  - [ ] Do NOT call `datetime.now()` for this value — copy only
- [ ] Task 4: Carry into GeoJSON (AC: #3)
  - [ ] Materialization SPARQL select includes `observed_at`; copy into `feature.properties.observed_at`
  - [ ] Keep `_SPARQL_SELECT` (main.py) and `materialize_geojson.py` query in sync
- [ ] Task 5: Render live age in the browser (AC: #4)
  - [ ] `web/app.js` reads `properties.observed_at`, computes `age = now − observed_at`, shows it on the canary marker/card
- [ ] Task 6: Write and pass `test_observed_at_skeleton_e2e` (AC: #5, #7)
- [ ] Task 7: Verify (AC: #8, #9)
  - [ ] `make canary-report` all-green
  - [ ] Operator visual confirmation with Nicolas on the live map

## Dev Notes

### Skeleton discipline — what may and may not be shortcut

| May shortcut in 3.6 | May NOT shortcut |
|---|---|
| One space only (Mother Sands canary) | Re-minting `observed_at` at any stage |
| Happy path only — HTTP 200 (304/unreachable = Story 3.7) | Letting the value drift between stages |
| Raw age display, no buckets (buckets = Story 3.10) | Skipping any of the 5 stages |
| Minimal SQLite column, no `fetch_status` yet (3.7) | Mocking a seam in the gating test |
| Crude `mom:observedAt` write, full hardening later | — |

### `datetime.now()` inventory (starting point — verify, do not trust blindly)

`grep` baseline at commit `e9fa797`:

**`infra/link_handler/transformer.py`**
- L68 — gap-log line timestamp → likely **generate** (diagnostics).
- L179 (`_build_pii_strip_sparql`) — lifecycle event time → likely **generate**; confirm it does not feed `observedAt`-adjacent fields.
- L317 — `datetime.fromtimestamp` parsing SpaceAPI `lastchange`; not a `now()` call, out of scope.
- L402 `now` / L403 `snapshot_date` — **hot zone.** `now` feeds `mom:lastUpdated`/`lastFetched`-class triples on the main DROP+INSERT write path → classify **carry**, owner Story 3.8. `snapshot_date` is a structural named-graph suffix → **generate**.
- L624 — heartbeat SQLite write path → this is the **`observed_at` mint point** for Task 2.
- L670 — post-200 ETag/Last-Modified handling, fetch-time region.
- L747 / L759 (`_days_since` / `_minutes_since`) — transient server-side age math feeding `endpoint_health` / `lifecycle_state` *triples*. **Per the roundtable decision (see below), classify these `generate` — transitional, scheduled for removal in Story 3.10.**
- L808 `_now_304` — 304-path `lastFetched` refresh → **carry**, owner Story 3.7.

**`infra/link_handler/main.py`** — L39/L668 (`_last_heartbeat_completed`, scheduler bookkeeping → generate), L478, L687, L795 (`snapshot_date` → generate). Verify L478/L687 payloads.

**`scripts/materialize_geojson.py`** — grep showed no `datetime.now`; the file-level `generated_at` field is introduced later (Story 3.9), not here.

### Decided: server-side age-math is transitional, removed by 3.10

The audit must NOT bless `_days_since` / `_minutes_since` (L747/L759) as permanently acceptable. They compute age server-side and that age drives `endpoint_health` / `lifecycle_state` triples written into Oxigraph — a *derived value stamped at transform time*, which is the same stale-stamping class the epic kills, one level removed. Decision (Nicolas, 2026-05-18): the end state is **one timestamp at fetch, age-math in the browser** (Story 3.10's pure bucketing function). 3.6 cannot delete them yet (the browser does not bucket until 3.10), so the audit classifies them `generate — TRANSITIONAL, remove in Story 3.10`. Story 3.10's ACs already own that deletion.

### Architecture constraints

- Canonical namespace: `https://nicolasdb.github.io/mapsofmaking_ontology/ns#`.
- `observed_at` = wall-clock UTC instant of a *successful* fetch — NOT SpaceAPI's optional `lastchange`.
- Canary writes route through the `is_canary` branch → `urn:mak:canary` graph (transformer.py:402). The `ext_mom.canary: true` write-routing flag remains unimplemented (Epic 3 retro open item) — 3.6 must not depend on it; use the existing `is_canary` branch.
- `mom:lastUpdated` rewrite rule unchanged: only on 200 + non-`None` `detect_diff()`; state-only writes must not touch it.
- `_SPARQL_SELECT` (main.py:27) and the `materialize_geojson.py` SPARQL query must stay in sync.
- **Scope guard (epics.md):** do NOT pull in `fetch_status` / 304 rules (3.7), transform-stamp deletion (3.8), multi-space materializer hardening (3.9), lifecycle bucketing (3.10), retry logic, ontology work, or GeoJSON payload-slimming (deferred). 3.6 carries ONE token on the happy path. Nothing else.

### Project Structure Notes

- Gating test in `infra/link_handler/` to join the existing `test_*.py` suite + `conftest.py`.
- Audit doc in `_bmad-output/implementation-artifacts/` next to this story.
- `make canary-report` is the live DoD gate (Epic 3 retro Actions 2/3).

### Previous Story Intelligence (Story 3.5)

Story 3.5 (`core.ttl` + `crosswalk.csv`) was static-artifact only — no transformer changes. The `ext_mom.canary: true` write-routing flag deferred from 3.4b → 3.5 was missed (3.5 was static-only) and remains unimplemented; do not build 3.6 on it.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Epic 3.5 — Story 3.6]
- [Source: _bmad-output/implementation-artifacts/epic-3-retro-2026-05-18.md#Addendum — Party-Mode Roundtable Deep-Dive]
- [Source: infra/link_handler/transformer.py — lines 68, 179, 402-403, 624, 670, 742-759, 808]
- [Source: infra/link_handler/main.py — lines 27, 39, 478, 668, 687, 795]
- [Source: CLAUDE.md — "Changes development sequence from horizontal layers to vertical slices"]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
