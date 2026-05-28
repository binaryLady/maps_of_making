# Retrospective — Epic 3.5: Freshness Propagation Contract

**Date:** 2026-05-28
**Participants:** Nicolas (Project Lead), Amelia (Developer)
**Previous retro:** `epic-3-retro-2026-05-18.md`

---

## Epic Summary

**Completed:** 7/7 stories (Story 3.8 archived as superseded by 3.8b; counted with it).
**Scope note:** Planned as 3.6→3.10 strictly linear (correct-course from Epic 3 roundtable, 2026-05-18). Shipped as 3.6, 3.7, 3.8 (superseded), 3.8b, 3.9, 3.10, plus 3.11 (unify SpaceAPI extractor) and 3.12 (seeding model + VPS ops pass) added mid-flight. Story 3.8 was redone as 3.8b on day one when the architectural review showed `mom:observedAt` was on the wrong axis — Axis A is SQLite-only, Oxigraph carries `mom:updatedAt` (Axis B) and `mom:lastOpenChange` (Axis C).

| Story | Title | Status |
|---|---|---|
| 3.6 | Walking Skeleton — Clean Snapshot Pipeline on the Canary | done |
| 3.7 | Migrate the Fetch Seam — Snapshot Store + 304 / Unreachable | done |
| 3.8 | Transformer Emits `mom:observedAt` *(superseded)* | done (archived) |
| 3.8b | Correct the Transformer Seam — Three-Token Model | done |
| 3.9 | Materializer Joins SQLite + Oxigraph — Three Tokens in GeoJSON | done |
| 3.10 | Browser Computes Three Axes Live — Canary E2E | done |
| 3.11 | Unify SpaceAPI Payload Extractor (core / mom / fab bundle) | done |
| 3.12 | Seeding Model + VPS Ops Pass (Paths A & B, claim-merge) | done |

**Epic done-condition (acceptance test):** _“An operator loads the map; a space whose endpoint has stopped updating past the staleness threshold visibly renders as stale, and a space still fetching fresh renders confirmed — demonstrated live against the operator-controlled Mother Sands canary, not a mock.”_ ✅ Met (Story 3.10 operator confirmation).

---

## Epic 3 Action Item Follow-Through

| # | Epic 3 commitment | Status | Notes |
|---|---|---|---|
| 1 | Epic 4 planning review against real data sources | ⏳ Partially overtaken | Epic 3.5 rewired the data sources themselves; Epic 4 ACs need re-review against the three-token output, not the old `urn:mak:status` model |
| 2 | DoD gate: canary coherence check on every pipeline story | ✅ Applied | Every 3.x story closed with `make c-report` and visual canary confirmation |
| 3 | DoD gate: live integration test on transformer/heartbeat | ✅ Applied | Real-seam gating tests on 3.6, 3.7, 3.8b, 3.9, 3.10; `@pytest.mark.live_integration` is now load-bearing |
| 4 | Fold stale-propagation bug-sweep into Epic 4 | ➡️ Pre-empted | Epic 3.5 closed the root cause (no propagation contract) before Epic 4 — sweep no longer needed; symptom debt is gone |
| 5 | `ext_mom.canary: true` write-routing | ✅ Resolved | Canary writes go to `urn:mak:canary` via the clean `canary_pipeline.py` (3.6); old routing-flag debt is moot |
| 6 | Close story 2.2 file | ❌ Still open | Sprint-status still shows it `done` but worth confirming in Epic 4 prep |
| 7 | Sync `mom.ttl` + `core.ttl` to ontology repo | ⏳ Story 3.11 added `countryCode` + `timeZone` to local `mom.ttl`; manual push to `mapsofmaking_ontology` repo + GitHub Pages publish still pending |
| 8 | Fix `_rematerialize_geojson()` temp filename race | ⏳ Untouched | Snapshot-unit pivot reduced the blast radius; still in `deferred-work.md` |

---

## What Went Well

1. **The clean-skeleton-first sequencing was the right call.** Story 3.6 built the new snapshot pipeline alongside the old one and proved the propagation contract on day one against new code, not grafted onto noise. Stories 3.7→3.10 then migrated and deleted in lock-step. Zero regression risk during 3.6, and `heartbeat_log.db`’s derived noise columns (`last_fetched`, `last_content_updated`, `last_endpoint_health`, `last_lifecycle_state`, `is_closed`) were deleted wholesale rather than refactored.

2. **The three-token model survived contact with reality.** `observed_at` (SQLite, Axis A) / `updated_at` (Oxigraph, Axis B) / `state.lastchange` (Oxigraph `mom:lastOpenChange`, Axis C) held together byte-identically across five stages. The mid-epic correction from one-token to three-token (3.8 → 3.8b) was caught at the Story 3.9 architectural review, before the bad shape calcified.

3. **Storage holds facts, never derived buckets.** `operationalState` and `endpointHealth` are now `f(token, now, thresholds)` computed in the browser from the `thresholds` block shipped in the GeoJSON header. The class of bug where “a stale payload looks fresh whenever the last stage that touched it ran recently” is structurally impossible now.

4. **Real-seam gating tests delivered what mocks could not.** `test_observed_at_skeleton_e2e`, `test_heartbeat_two_cycle_temporal`, `test_transformer_three_token`, `test_materializer_three_tokens`, `test_canary_three_axis_e2e` — each one of these would have failed under the old mocked test design but caught real seam bugs (e.g. `read_last_ok_observed_at` returning `None` after 304s — Story 3.7 patch).

5. **Code reviews caught the load-bearing bugs in flight.** Three of Story 3.9’s patches were fail-loud contract violations (`last_open_change` empty-string default, `last_fetch_status` never filled, `THREE_TOKENS_MISSING` using wrong condition). Story 3.8b caught an AC2 violation (`transform_to_sparql` called on no-diff). Reviews are now load-bearing infrastructure, not ceremony.

6. **Story 3.11 found and fixed a class of drift.** The unify-extractor pass surfaced that `main.py::_SPARQL_SELECT` and `scripts/materialize_geojson.py::SPARQL_QUERY` were two hand-maintained copies of the same query — drift between them was the root cause of an empty-card bug on `make reset`. The drift is patched and `docs/field-lifecycle.md` written, but the structural fix (one shared query module) is still owed.

7. **Story 3.12 closed the VPS deploy story.** Paths A (`vps-seed LIST=…`) and B (`vps-seed-bundle BUNDLE=…`) are now the canonical seed routes; `make publish` no longer carries hidden seed logic; gateway reload prevents 502s; `_find_seeded_graph_by_name` + claim-merge is wired for the future self-registration flow. Documentation (`docs/host-your-space.md`, `docs/vps-operations.md`) shipped with it.

---

## What Was Hard / Challenges

1. **Story 3.8 → 3.8b: the token shape was wrong on the first attempt.** Story 3.8 wrote `mom:observedAt` to Oxigraph; Story 3.9’s architectural review caught that `observed_at` belongs in SQLite only (Axis A), and Oxigraph’s job is `mom:updatedAt` (Axis B) — the rewrite cost a story-shaped patch. Catching it at the review boundary is the right outcome, but the model was not fully derived before code started.

2. **Two materializers, one schema — and they drifted.** `infra/link_handler/main.py::_SPARQL_SELECT` and `scripts/materialize_geojson.py::SPARQL_QUERY` are still two copies. Story 3.11 patched the drift but did not consolidate them. The same class of bug **will** recur until they’re behind one module.

3. **Scope grew mid-epic — twice.** The original Epic 3.5 was 3.6–3.10 (linear, single-purpose). Stories 3.11 (unify extractor) and 3.12 (seeding + VPS ops) were added during execution. Both were genuinely necessary and well-scoped, but as in Epic 3, “linear, strictly bounded” turned out to be a hypothesis.

4. **Pre-existing fallback path still violates the contract.** Story 3.8b’s deferred review entry: `_build_sparql_update()` legacy fallback in `main.py:787` still writes `mom:operationalState` and `mom:lastFetched` on transform exceptions. The three-token contract holds on the happy path but breaks on the error path. Carried to deferred work.

5. **Operator visual confirmation is the only test the bots can’t run.** Story 3.10 sat in `review` until Nicolas drove the canary through unreachable / stale-content / closed states by hand. The DoD gate is good policy; it’s also the slowest gate. No fix — this is the cost of the “green pytest is not done” discipline.

6. **Several Story 3.8b / 3.9 review items deferred rather than fixed.** Patterns: no WAL mode / busy timeout on SQLite; broad `httpx.RequestError` catch including `InvalidURL`; `consecutive_failures` not persisted on error path; 304 streak leaving `last_open_now` stale. None block Epic 4, but they’re drag.

---

## Key Insights

- **Snapshot-as-unit is the right axiom; once it’s the rule, the bug class disappears.** The Epic 3 retro named the root cause as “five-stage cache chain with no propagation contract.” Epic 3.5 made the snapshot the unit, minted `observed_at` once at fetch, and carried it byte-identical to the browser. Every retro bug from Epic 3 (scheduler lambda, `mom:lastUpdated` wipe, stuck-`seeded`, 304 freezing `lastFetched`) lived at a seam that no longer stamps its own “now.”

- **Architectural review at the materializer seam saved the model.** Story 3.9 surfaced that Story 3.8 had the wrong axis. Story 3.11 surfaced the dual-materializer drift. The seam *between* stories is where the model is interrogated; in-story review catches code, between-story review catches design.

- **The “correct-course inside an epic” discipline is now load-bearing.** Story 3.8 → 3.8b happened cleanly because Epic 3.5 was framed as “clean rebuild, not patch” from the start. There was no sunk-cost pressure to keep Story 3.8’s shape — the rebuild was already the strategy.

- **Epic 4’s plan needs re-review against Epic 3.5’s output.** Epic 4’s story ACs in `epics.md` were rewritten in the Epic 3 retro against the Epic 3 output (heartbeat_log.db columns, `urn:mak:status` graph, `mak:probeResult`). Epic 3.5 deleted those exact columns and replaced them with `snapshot_store.db` + `mom:updatedAt`/`mom:lastOpenChange` + browser-side axis computation. Epic 4’s inspection panel now reads against the three-token output, not the old shape.

- **The “browser computes from raw tokens + thresholds header” pattern is reusable.** Story 3.10’s `computeAxisA/B/C/Marker` pattern + `FALLBACK_THRESHOLDS` is the template for any future axis (e.g. coordinator-network membership freshness, ontology bundle version). Stored derived state is the anti-pattern; raw tokens + consumption-time computation is the pattern.

---

## Technical Debt Entering Epic 4

**High priority (Epic 4-adjacent):**
- Epic 4 plan re-review against Epic 3.5 output (snapshot store, three-token GeoJSON, browser-computed axes) — **blocks story 4.1 creation**.
- Two-materializer drift (`main.py::_SPARQL_SELECT` vs `scripts/materialize_geojson.py::SPARQL_QUERY`) — patched by 3.11, not structurally fixed. One shared query module is the real fix.
- Legacy `_build_sparql_update()` error-path fallback in `main.py` still writes `mom:operationalState` / `mom:lastFetched` — violates three-token contract on transform exceptions.

**Medium priority:**
- Story 3.7 SQLite robustness gaps deferred: no WAL mode / busy-timeout (concurrent-writer deadlock risk); broad `httpx.RequestError` catch includes `InvalidURL` (config errors treated as transient); `consecutive_failures` not persisted on error path.
- `_load_thresholds_from_config` swallow-all behavior was partially fixed in 3.10 (fail-loud `THRESHOLDS_MISSING`); audit that all call sites are aligned.
- `_rematerialize_geojson()` fixed temp filename race — still untouched from Epic 3 retro; pertinent under concurrent heartbeats.
- 304 streak leaves `last_open_now` from SQLite stale if a space closes during the streak — `effective_marker` can report `open` indefinitely.

**Low / monitor:**
- Ontology repo manual sync — Story 3.11 added `mom:countryCode` and `mom:timeZone` to local `mom.ttl`; the `mapsofmaking_ontology` GitHub repo + Pages publish is still operator-manual.
- Story 2.2 file confirmation (carried from Epic 3 retro).
- Network-membership handshake (Story 3.12 deferred) — `memberOf` honored on trust; cross-check against declared network directory is owed.
- SDG ontology + processing (`ext_fab.sdgs` stored verbatim, predicate/namespace/UI TBD).

---

## Next Epic Preview — Epic 4: Operator Observability Dashboard

**Stories:** 4.1 system health strip · 4.2 space registry table · 4.3 per-space inspection panel (raw / ingested / displayed) · 4.4 export + operator action log.

### 🚨 SIGNIFICANT DISCOVERY — Epic 4 ACs are out of sync (again, but differently)

The Epic 3 retro already flagged Epic 4 as out-of-sync with Epic 3’s shape. Epic 3.5 then **rewrote** that shape. A reverse-engineering pass from the Epic 4 done-condition (operator opens `/admin`, reads system state, finds and diagnoses a broken space — _operator tool for Nicolas, not network coordinator dashboard_, per `[[project_epic4_reframe]]`) confirms the four-story decomposition holds but redlines the ACs in three load-bearing ways.

---

#### Epic 4 Re-planning Brief — work-backwards from operator time horizons

**Horizon 1 — “Is anything on fire?” (<5 s) → Story 4.1: System Health Strip**

| Pill | Post-3.5 signal | Source |
|---|---|---|
| Oxigraph live | `ASK {}` | `sparql_client.run_select()` (already exists) |
| Ingestion cycling | `MAX(observed_at)` across snapshots vs `now − threshold` | `snapshot_store.db` SQL — **no marker file**; the snapshots _are_ the heartbeat trace |
| Spaces reachable | `COUNT(fetch_status='ok') / COUNT(*)` over latest snapshot per space | `snapshot_store.db` SQL — **not `mak:probeResult` in `urn:mak:status`** (that graph was never built) |

**Horizon 2 — “Which space is broken?” (~30 s) → Story 4.2: Space Registry Table**

One join: `snapshot_store.db` (Axes A + reachability) ⋈ per-space Oxigraph graphs (Axes B + C + metadata). Columns: name, endpoint URL, `observed_at` (Axis A), `fetch_status`, `updated_at` (Axis B), `open_now` / `last_open_change` (Axis C), **browser-computed worst-of-three axis badge** matching Story 3.10’s pattern. Default sort: stalest `observed_at` first. Re-probe button triggers `space_pipeline.run_space_pipeline()` (Story 3.11 unified path), not the old `tasks/heartbeat.py`.

**Horizon 3 — “Where did this break?” (~2–3 min) → Story 4.3: Per-Space Inspection Panel + Axis Trace**

The RAW / INGESTED / DISPLAYED triptych maps cleanly onto the three-token model — this is the load-bearing insight:

| Column | Post-3.5 implementation | What it proves |
|---|---|---|
| RAW | `snapshot_store.db.payload` blob for `(space_id, latest_ok)` | Zone 3 trust receipt (per `[[project_zone3_trust_receipt]]`) — proof we didn’t mutate source |
| INGESTED | `SPARQL DESCRIBE <urn:mak:space/{id}>` | Proves Story 3.11 extractor extracted what the bundle says it should |
| DISPLAYED | `_binding_to_feature()` output + browser `computeAxisA/B/C/Marker` | Proves materializer + browser axis logic agree with INGESTED |

Mismatch detection is the panel’s primary job — RAW→INGESTED gaps surface `spaceapi_extract` bugs; INGESTED→DISPLAYED gaps surface materializer drift (critical-path #2 dependency) or browser axis bugs. `mom:deathReason` callout still belongs here; the panel _recomputes_ death classification rather than reading a stored bucket — self-validating.

**Horizon 4 — “Prove what shipped” → Story 4.4: Export + Operator Action Log**

Shape carries forward intact; only AC redline is that the export schema now includes the three tokens explicitly so a downstream consumer can replay axis computation.

---

#### Three load-bearing AC changes

1. **Snapshot store is the universal data source for reachability/freshness.** Drop every reference to `urn:mak:status`, `mak:probeResult`, the heartbeat marker file, and `/data/snapshots/{id}/latest.json` on disk. All four stories pull Axis A from `snapshot_store.db`.
2. **Story 4.2 needs two independent staleness columns (Axes A and B), plus a browser-computed worst-of-three badge.** The old single-column “probe result” framing silently re-couples them.
3. **Story 4.3’s RAW column reads the snapshot store’s payload blob, not disk.** Eliminates a phantom disk-artifact dependency that doesn’t exist after 3.5.

#### Two architectural choices that need explicit ADRs before story creation

- **A. Ingestion-health signal:** snapshot-store `MAX(observed_at)` vs marker file vs APScheduler health endpoint. Real failure modes (e.g. APScheduler running but every fetch erroring — does `observed_at` advance on errors? Story 3.7 says “unreachable → unchanged”, so yes, this signal degrades correctly — but the choice deserves explicit capture).
- **B. Story 4.3 inspection-panel backend:** per-space generalization of the canary coherence report vs a new SPARQL-DESCRIBE flow vs reading the snapshot-store payload directly. Three viable shapes with real trade-offs in latency, code reuse, and consistency with Story 3.10’s axis computation.

**Decision:** Resolve ADRs A and B + consolidate the two materializers (critical-path #2) before Story 4.1 is created. The PM agent can write Story 4.1–4.4 cleanly once those land.

---

#### ADRs (Epic 4 prep)

##### ADR-A — Ingestion-health signal for Story 4.1 Pill 2

**Context.** Operator needs to know in <5 s whether the heartbeat scheduler is still cycling. Old AC referenced a “heartbeat marker file” written after each scheduler cycle. That file doesn’t exist; APScheduler runs in-process inside `mak-link-handler`. Verified `mark_unreachable()` in `infra/link_handler/snapshot_store.py:121` does **not** touch `observed_at` — only `fetch_status` / `fetch_error`.

**Options.**

| Option | Source | Failure modes detected | Failure modes missed |
|---|---|---|---|
| **A1. `MAX(observed_at)` over snapshot store** | 1 SQLite query | Scheduler dead; scheduler running but every fetch unreachable (MAX freezes since `mark_unreachable` doesn’t touch `observed_at`) | Scheduler running, one space succeeding, all others erroring — MAX advances. Operator sees “healthy ingestion” despite 99% failure. **Pill 3 catches this.** |
| **A2. Heartbeat-marker file written by APScheduler job wrapper** | 1 `stat` call on `/var/lib/mom/heartbeat.stamp` | Scheduler-process dead | Scheduler ticking but doing zero work; introduces new on-disk artifact + SELinux/volume gotcha (per `[[infra_selinux_and_platform_notes]]`) for one bit |
| **A3. APScheduler `get_jobs()` introspection via API** | In-process Python | Scheduler-object dead; misconfigured | Scheduler ticking but every job raising — `next_run_time` still advances; leaks in-process state into a SPARQL-shaped API |

**Decision: A1 — `MAX(observed_at)` over `snapshot_store.db`, with Pill 3 (reachable count) as the safety net.**

**Rationale.**
- The snapshot store is the *thing the scheduler exists to produce*. Reading the artifact is more truthful than a side-channel marker. Same axiom as the rest of Epic 3.5: storage holds facts, derived state is computed.
- The “scheduler ticks but every fetch unreachable” failure mode A1 misses is exactly what Pill 3 is for. The two pills together cover the matrix; neither alone does.
- A2 would re-introduce the “stage stamps its own now” anti-pattern that Epic 3.5 just deleted.
- A3 reports liveness of the scheduler object, not of the work it does.

**Consequences.**
- Threshold for STALLED is `now − MAX(observed_at) > heartbeat_interval × N` (N=3 reasonable). Add `pill_2_stalled_after_seconds` to `config.yaml.thresholds` so the canary demo can compress it.
- Diagnostic logic for the operator: Pill 3 = 0/N AND Pill 2 stalled → “scheduler dead.” Pill 3 = 0/N AND Pill 2 fresh → “scheduler alive, network/upstream broken.” Distinguishable without log-diving.
- One SQL query serves both Pill 2 and Pill 3 (group by latest snapshot per space). Keep them in one `/admin/api/status` endpoint.

**Tradeoff accepted.** Cannot distinguish “scheduler dead” from “every space unreachable simultaneously” using Pill 2 alone. Pill 3 disambiguates; the cure (A2 or A3) is worse than the disease.

---

##### ADR-B — Story 4.3 inspection-panel backend shape

**Context.** Story 4.3 shows RAW / INGESTED / DISPLAYED side-by-side for one space. Three viable backend shapes.

**Options.**

| Option | RAW | INGESTED | DISPLAYED | Code reuse | Consistency with Story 3.10 |
|---|---|---|---|---|---|
| **B1. Per-space generalization of canary coherence report** | `snapshot_store.db.payload` | Hand-written per-predicate SPARQL SELECTs (same as `make c-report`) | Re-run `_binding_to_feature()` + browser axes | High | Medium — coherence report predates 3.10; needs an axis-trace addendum |
| **B2. SPARQL DESCRIBE for INGESTED, snapshot blob for RAW, production materializer + browser axes for DISPLAYED** | `snapshot_store.db.payload` | `DESCRIBE <urn:mak:space/{id}>` → key/value list | `_binding_to_feature()` + browser `computeAxisA/B/C/Marker` | Lower — DESCRIBE rendering is new | **High** — DISPLAYED uses exactly the production rendering path |
| **B3. Recompute INGESTED from payload via `spaceapi_extract`** | `snapshot_store.db.payload` | Run `spaceapi_extract.extract_core/mom` at request time | Same as B2 | Medium | Low — INGESTED shows what the extractor *would* produce, not what is actually in Oxigraph; **hides ingestion bugs** |

**Decision: B2 — DESCRIBE for INGESTED, snapshot-payload blob for RAW, production materializer + browser axes for DISPLAYED.**

**Rationale.**
- The inspection panel exists to expose *gaps* between layers. B3 reads ingestion-time data through a current-code lens and erases the very gap the panel is supposed to surface. Disqualifying.
- B1 ships faster (canary coherence report already exists) but its per-predicate SPARQL hand-list is brittle — every new predicate in core/mom/ext_fab requires editing the coherence report. `DESCRIBE` is schema-agnostic; the panel renders whatever is in the graph. Matches the bundle-loadable direction in `[[project_schema_bundle_model]]`.
- B2 makes DISPLAYED use the exact production rendering path — the only way the panel can prove the rendering pipeline isn’t lying. B1’s parallel re-run can itself drift.
- B2 makes mismatch detection structural:
  - **RAW → INGESTED gap**: payload field present, no triple in DESCRIBE → `spaceapi_extract` bug.
  - **INGESTED → DISPLAYED gap**: triple in DESCRIBE, not in `_binding_to_feature()` output → materializer drift (critical-path #2 dependency).
  - **Token-axis mismatch**: `observed_at` from snapshot row ≠ Axis A computed in DISPLAYED → SQLite/browser disagreement.

**Consequences.**
- **Hard dependency on critical-path #2 (consolidate the two materializers)** — B2’s DISPLAYED column calls production `_binding_to_feature()`; if the script-side materializer drifts again, the panel will under-report drift on batch-materialized spaces. Consolidation must land before Story 4.3.
- `read_snapshot(uid)` accessor already exists (`snapshot_store.py:78–95`); no new schema work.
- DESCRIBE-to-key/value-list rendering is new client-side code but small — one Turtle-to-rows transform.
- `mom:deathReason` callout becomes a derived render off DESCRIBE plus browser axis classification. No special storage path needed.

**Tradeoff accepted.** Higher up-front cost than B1 in exchange for (1) production-rendering equivalence in DISPLAYED, (2) schema-agnostic INGESTED that grows with the bundle, and (3) structural mismatch surfacing rather than hand-listed predicate diffs.

---

##### ADR-B Hardenings — surfaced by red-team pass

Five attacks against B2; decision survives, consequences list grows.

**1. Partial materializer consolidation under-reports drift.** If critical-path #2 lands at 80% (variable names unified, canary block / OPTIONAL / GROUP BY still divergent), B2's DISPLAYED column calls in-process `_binding_to_feature()` and misses drift on batch-materialized spaces — the exact bug the panel exists to surface.
- **Add to critical-path #2 DoD:** `grep -rn "_SPARQL_SELECT\|SPARQL_QUERY" infra/ scripts/` returns exactly one definition site. One module exports `build_select_sparql()`, `binding_to_feature()`, `bundle_field_set()`; both `main.py` and `scripts/materialize_geojson.py` import them with no shadow copies.
- **Story 4.3 fallback AC:** DISPLAYED column has two sub-columns — “as `main.py` renders” and “as `scripts/materialize_geojson.py` renders.” Byte-identical after consolidation (hide one); divergence becomes a third inline mismatch class.

**2. The inspection panel must render endpoint payloads verbatim — MoM does not filter content.** Per `[[feedback_no_pii_filtering]]` (locked principle, reaffirmed Epic 3.5): MoM is IPO over public coordinator endpoints; we never edit, censor, scan, or strip what coordinators choose to publish. This is the foundation of Zone 3 trust — the evaluator's audit is meaningful *because* we're provably non-altering. Also deprecated: the Story 3.2-b `mak:closed` PII-strip on persistent closure — same principle.
- **Story 4.3 AC:** RAW column shows the snapshot payload byte-identical. No redaction, no PII flags, no "sensitive" warnings. INGESTED renders DESCRIBE verbatim. The panel is a window onto what the coordinator publishes — coordinator authority is absolute.
- **Story 4.3 AC:** No "download as JSON" affordance on the panel. Read-only diagnostic surface. Operators screenshot if needed.
- **Story 4.4 AC:** Export excludes raw payloads — per NFR-S6, on *aggregation* grounds (mass export across the registry enables surveillance the individual public endpoints don't), not on PII grounds. Different defense, different rationale.
- **Future-tool note (not in scope, but record so it isn't confused with deprecated filtering):** a coordinator-side advisory pre-publish scan during registration / JSON-document generation could warn the coordinator about fields they might not realize are public (`"your contact.email will be world-readable"`). Coordinator-side only, advisory only, coordinator chooses, MoM never acts. Filed for Epic 4-b / Epic 9 host-your-space tooling. **Do not confuse with the deprecated pipeline-side filtering.**

**3. Token-axis mismatch detection: drop the misleading "SQLite/browser disagreement" framing.** ADR-B oversold this. The browser's Axis A in DISPLAYED is computed from the GeoJSON feature's `observed_at`, which came from a SQLite read via the materializer. Comparing it to the snapshot row is a *serialization audit* between two reads of the same DB, not a cross-source consistency check.
- **Reframe mismatch classes in the panel:**
  - **(a) Serialization audit (Axis A):** DB `observed_at` == GeoJSON feature `observed_at`. Catches materializer dropping/mangling the token.
  - **(b) Config audit:** GeoJSON header `thresholds` == `config.yaml`. Catches stale-config-in-shipped-file.
  - **(c) Browser liveness check:** displayed age tracks DB age within tolerance. The only real liveness check.
  - **(d) Cross-source temporal invariant:** `mom:updatedAt` ≤ `observed_at` (Story 3.8b guarantees `updated_at` only writes on 200-with-diff; the gap is the content-stale window). Catches transformer bugs that stamp `updated_at` outside the contract.
  - **(e) RAW → INGESTED gap:** payload field present, no triple in DESCRIBE → `spaceapi_extract` extractor bug.
  - **(f) INGESTED → DISPLAYED gap:** triple in DESCRIBE, not in `_binding_to_feature()` output → materializer drift (depends on #1).

**4. DESCRIBE on rich bundles can be slow rendering, not slow querying.** Bundle-realistic triple count is 30–60 (mom) + 20–50 (ext_fab once landed). Oxigraph DESCRIBE is sub-ms at that scale; client-side Turtle-to-rows transform can drag if naive.
- **Story 4.3 AC:** inspection-panel open-latency budget = 500ms for INGESTED + DISPLAYED combined; RAW (snapshot blob) is what it is.
- **Story 4.3 AC:** group DESCRIBE rows by predicate prefix (`mom:` / `schema:` / `mak:` / `ext_fab:`); collapse non-mom by default with a `<details>` toggle. Operator scans the mom bundle, expands the rest only when diagnosing a bundle-layer bug.

**5. Seeded-only spaces are first-class, not edge case.** Per Story 3.12, 566 VOW + future bulk seeds enter the registry without snapshot rows. Many may never have endpoints. If the operator clicks one, B2's RAW column with naive `read_snapshot(uid)` returns None and the panel shows three empty columns — the operator can't tell "bug in panel" from "no endpoint to fetch." This is the class of space *most* likely to need operator attention (orphan seeds awaiting claim).
- **Story 4.3 AC:** "seeded-only" is a first-class RAW state alongside "responded" and "unreachable (last known…)". RAW shows the seed source (bundle name: `vow`, `rff`, `coordinator-registered`) and `mom:seededAt` timestamp. INGESTED shows DESCRIBE — for seeded-only, that's bundle metadata, no `mom:updatedAt`. DISPLAYED shows the seeded grey pin.
- **Verify in Story 3.12 output:** does the seed pipeline write `mom:seededAt`? If not, that AC is added to the materializer consolidation or done as a small precursor.
- **Cross-epic link:** the seeded-only state is the diagnostic surface for the seeded→confirmed gap (per `[[story_3_4_open_seeded_gap]]`) and for Epic 4-b self-registration claim affordances. Out of scope for Story 4.3 backend (B2 still applies); record as a deferred-work link from Story 4.3 → Epic 4-b.

---

#### Epic 4 AC Redline — line-by-line, ingestible by PM agent

Comparative-analysis matrix scoring existing `epics.md` Stories 4.1–4.4 ACs against the re-planning brief + ADRs + hardenings. Legend: **KEEP** / **REWRITE** / **DROP** / **ADD-NEW**.

##### Story 4.1 — System Health Strip

| # | Existing AC | Score | Post-3.5 replacement / rationale |
|---|---|---|---|
| 4.1.1 | `GET /admin/api/status` endpoint | KEEP | Endpoint shape carries forward |
| 4.1.2a | Oxigraph: `ASK {}` → LIVE/DOWN | KEEP | Verbatim |
| 4.1.2b | Ingestion: heartbeat-marker-file timestamp → RUNNING/IDLE/STALLED | REWRITE | Per ADR-A: `MAX(observed_at)` over `snapshot_store.db` vs `now − heartbeat_interval × N`. No marker file. Threshold from `config.yaml.thresholds.pill_2_stalled_after_seconds`. |
| 4.1.2c | Spaces reachable: `mak:probeResult "ok"` count in `<urn:mak:status>` | REWRITE | `COUNT(fetch_status='ok') / COUNT(*)` over latest snapshot per space in `snapshot_store.db`. No `urn:mak:status`, no `mak:probeResult` — neither was ever built. One SQL query serves 4.1.2b + 4.1.2c. |
| 4.1.3 | Three pills rendered top of page | KEEP | Visual unchanged |
| 4.1.4 | "Last checked: N min ago" + 60s auto-refresh | KEEP | Unchanged |
| 4.1.5 | Oxigraph DOWN → red pill + "— unavailable" elsewhere | KEEP | Graceful-degrade pattern stands |
| 4.1.6 | Operational metrics only — no raw payloads, NFR-S6 | KEEP | Aggregation-grounds defense (Attack 2 hardening) |
| 4.1.+1 | Diagnostic-logic AC: Pill 3 = 0/N AND Pill 2 stalled → "scheduler dead"; Pill 3 = 0/N AND Pill 2 fresh → "scheduler alive, network broken" | ADD-NEW | Per ADR-A consequence — failure-mode disambiguation explicit in AC |

##### Story 4.2 — Space Registry Table

| # | Existing AC | Score | Post-3.5 replacement / rationale |
|---|---|---|---|
| 4.2.1 | Given health strip + `<urn:mak:status>` populated | REWRITE | Drop `urn:mak:status` clause. Given: health strip loaded AND `snapshot_store.db` has snapshots AND `urn:mak:space/{id}` graphs exist |
| 4.2.2 | SPARQL over `<urn:mak:status>`: name, endpoint, last probe, probe result | REWRITE | Join: `snapshot_store.db` ⋈ per-space Oxigraph graphs. Columns: name, endpoint URL, `observed_at`, `fetch_status` (ok/not_modified/unreachable), `updated_at`, `open_now` / `last_open_change` |
| 4.2.+1 | Browser-computed worst-of-three axis badge per row (matches Story 3.10 `computeMarker()`) | ADD-NEW | Single visual signal collapsing three axes; old "probe result" coupled them |
| 4.2.3 | Non-200 rows muted-red bg | REWRITE | Rows where worst-of-three axis is aging/zombie/dead get muted-red |
| 4.2.4 | Sortable by last probe / probe result; default most-recently-failed | REWRITE | Default: stalest `observed_at` first. Sortable by `observed_at`, `updated_at`, `fetch_status`, axis badge |
| 4.2.5 | Client-side text filter | KEEP | Unchanged |
| 4.2.6 | Row click opens inspection panel (4.3) | KEEP | Unchanged |
| 4.2.7 | "Re-probe now" triggers `tasks/heartbeat.py` | REWRITE | Triggers `space_pipeline.run_space_pipeline()` (Story 3.11 unified path); `tasks/heartbeat.py` deleted |
| 4.2.8 | Re-probe written to action log | KEEP | Unchanged |
| 4.2.+2 | Seeded-only spaces show axis badge "seeded" (grey), not "unreachable" | ADD-NEW | Per Attack 5 — 566+ spaces; cannot read as failures |

##### Story 4.3 — Per-Space Inspection Panel (RAW / INGESTED / DISPLAYED)

| # | Existing AC | Score | Post-3.5 replacement / rationale |
|---|---|---|---|
| 4.3.1 | Row click → panel opens with three columns | KEEP | Unchanged |
| 4.3.2 | RAW reads `/data/snapshots/{id}/latest.json` from disk | REWRITE | RAW reads `snapshot_store.db.payload` blob via `read_snapshot(uid)` (`infra/link_handler/snapshot_store.py:78`). No disk artifact. |
| 4.3.3 | RAW: raw JSON monospaced + fetch timestamp + endpoint URL | KEEP | Verbatim render — MoM does not edit endpoint content (`[[feedback_no_pii_filtering]]`) |
| 4.3.4 | RAW status: "responded" or "unreachable (last known …)" | REWRITE | Three first-class states: `responded` / `unreachable (last known …)` / **`seeded-only (bundle: {name}, seeded at: {mom:seededAt})`** |
| 4.3.5 | RAW = Zone 3 source of truth, verbatim, unmodified | KEEP | Locked principle |
| 4.3.6 | INGESTED: `SPARQL DESCRIBE <urn:mak:space/{id}>` via `/sparql/query` | KEEP | Per ADR-B — schema-agnostic, grows with bundle |
| 4.3.7 | INGESTED as key→value list, not Turtle | REWRITE | Group by predicate prefix (`mom:` / `schema:` / `mak:` / `ext_fab:`); collapse non-mom by default via `<details>` (Attack 4) |
| 4.3.8 | INGESTED: triple count + last-ingested timestamp | KEEP | Triple count diagnoses bundle-shape; last-ingested = `mom:updatedAt` |
| 4.3.9 | DISPLAYED: SELECT for exact card fields | REWRITE | DISPLAYED calls production `_binding_to_feature()` (from consolidated materializer module, critical-path #2) + browser `computeAxisA/B/C/Marker`. Production-rendering equivalence per ADR-B. |
| 4.3.10 | DISPLAYED as mini card preview: name, address, status, hours, specialties | KEEP | Visual unchanged |
| 4.3.11 | Field in RAW absent in card → ⚠ "not displayed" | KEEP | RAW → DISPLAYED gap |
| 4.3.+1 | Structural mismatch detection — six classes, inline ⚠ flags: | ADD-NEW | Replaces looser AC text; per ADR-B Hardening 3 |
|  | (a) Serialization audit: snapshot row `observed_at` == GeoJSON feature `observed_at` |  |  |
|  | (b) Config audit: GeoJSON header `thresholds` == `config.yaml` |  |  |
|  | (c) Browser liveness: displayed age tracks DB age within tolerance |  |  |
|  | (d) Cross-source invariant: `mom:updatedAt` ≤ `observed_at` |  |  |
|  | (e) RAW → INGESTED gap: payload field present, no triple → `spaceapi_extract` bug |  |  |
|  | (f) INGESTED → DISPLAYED gap: triple present, not in `_binding_to_feature()` → materializer drift |  |  |
| 4.3.12 | Col 1 ↔ col 2 ⚠ → gaps in `tasks/ingest.py` | REWRITE | Subsumed by 4.3.+1e; rename target to `scripts/spaceapi_extract/` (Story 3.11 unified library) |
| 4.3.13 | Col 2 ↔ col 3 ⚠ → gaps in `app.js` | REWRITE | Subsumed by 4.3.+1f; target is consolidated materializer + browser `computeAxis*` |
| 4.3.14 | Panel is primary diagnostic tool — no SSH, no log access needed | KEEP | Unchanged |
| 4.3.15 | Terminal-state (`closed`/`dead`) shows `mom:deathReason`; ledger writer dependency note | REWRITE | Death classification *recomputed* by browser axes (self-validating). Panel shows both derived classification and triggering tokens (`mom:lastOpenChange`, threshold breach) so operator audits the derivation. `mom:deathReason` rendered from DESCRIBE if present. Ledger writer dependency unchanged. |
| 4.3.+2 | No "download as JSON" affordance on panel — read-only diagnostic surface | ADD-NEW | Per Attack 2 (aggregation-defense + IPO principle) |
| 4.3.+3 | Latency budget: INGESTED + DISPLAYED ≤ 500ms; RAW bounded by payload size | ADD-NEW | Per Attack 4 |
| 4.3.+4 | (Conditional until consolidation lands) DISPLAYED has two sub-columns "as `main.py` renders" / "as `scripts/materialize_geojson.py` renders"; byte-identical post-consolidation (hide one); divergence becomes seventh mismatch class | ADD-NEW | Per Attack 1 fallback |
| 4.3.+5 | Seeded-only state cross-links to Epic 4-b registration flow ("awaiting claim") when RAW state is `seeded-only` | ADD-NEW | Per Attack 5; backend stays B2; record as deferred-work link to Epic 4-b |

##### Story 4.4 — Export Registry + Operator Action Log

| # | Existing AC | Score | Post-3.5 replacement / rationale |
|---|---|---|---|
| 4.4.1 | Export: name, URI, endpoint, status, last probe, probe result → CSV + JSON | REWRITE | Export schema against three-token shape: name, URI, endpoint URL, `observed_at`, `fetch_status`, `updated_at`, `last_open_change`, `open_now`, browser-computable axis-A/B/C states. Downstream can replay axis computation deterministically. |
| 4.4.2 | Excludes raw payloads + coordinator contact details not on public map (NFR-S6) | REWRITE | Excludes raw payloads on **aggregation grounds** (mass export enables surveillance the individual public endpoints don't). **Drop** the "coordinator contact details" clause — conflates with deprecated PII-strip. Coordinators publish what they publish; MoM does not edit. |
| 4.4.3 | Action log: reverse-chronological list with timestamp, action, space URI, result | KEEP | Unchanged |
| 4.4.4 | Append-only — no delete, no edit | KEEP | Matches `[[project_three_graph_model]]` ledger pattern |
| 4.4.5 | Export action recorded itself | KEEP | Unchanged |

##### Net counts

| Story | KEEP | REWRITE | DROP | ADD-NEW | Net AC change |
|---|---|---|---|---|---|
| 4.1 | 5 | 2 | 0 | 1 | +1 |
| 4.2 | 3 | 5 | 0 | 2 | +2 |
| 4.3 | 6 | 5 | 0 | 5 (+ 6 mismatch sub-clauses) | +5 |
| 4.4 | 3 | 2 | 0 | 0 | 0 |
| **Total** | **17** | **14** | **0** | **8** | **+8** |

**Zero DROP rows.** Every existing AC's intent survives — Epic 4's *shape* was right; its *sources* were stale. The work-backwards + red-team passes didn't break the design; they re-grounded it.

Net new ACs concentrate in Story 4.3, where post-3.5 reality is richest — three-token model gives six structural mismatch classes the old plan had no concept of.

##### Three blocking dependencies before redline becomes story files

1. **Critical-path #2 (materializer consolidation)** — gates Story 4.3 ACs 4.3.9, 4.3.+1f. Without consolidation, AC 4.3.+4 dual-sub-column fallback is load-bearing rather than optional.
2. **`mom:seededAt` verification in Story 3.12 output** — gates ACs 4.3.4 (seeded-only RAW state) and 4.2.+2 (seeded badge). Quick precursor; small seed-pipeline fix if missing.
3. **ADR-A `pill_2_stalled_after_seconds` added to `config.yaml.thresholds`** — gates AC 4.1.2b. Trivial config addition before Story 4.1 dev.

---

## Readiness Assessment

| Dimension | Status |
|---|---|
| Three-token propagation contract (fetch → SQLite → Oxigraph → GeoJSON → browser) | ✅ Live and byte-identical |
| Canary three-axis E2E demo | ✅ Operator-confirmed (Story 3.10) |
| Snapshot store as Axis A authority | ✅ Live; `heartbeat_log.db` noise columns deleted |
| Browser-side axis computation + thresholds header | ✅ Live, fail-loud on missing thresholds |
| Unified SpaceAPI payload extractor + canary baseline coverage | ✅ Story 3.11 |
| VPS seeding (Paths A & B) + claim-merge | ✅ Story 3.12 |
| Two-materializer drift | ⚠️ Patched, not structurally fixed |
| Legacy `_build_sparql_update` error-path fallback | ⚠️ Still violates three-token contract on exceptions |
| Ontology repo sync (`mom.ttl` additions from 3.11) | ❌ Manual push pending |
| Epic 4 plan vs Epic 3.5 reality | ❌ Out of sync — planning review required (2nd pass) |

**Verdict:** Epic 3.5 is complete and the propagation contract is live. The “pytest passes but the live pipeline breaks” bug class named in the Epic 3 retro is structurally resolved. Remaining debt is well-routed and Epic-4-adjacent. The single blocker before Epic 4 is the planning re-review against the post-3.5 data sources.

---

## Action Items

| # | Action | Owner | When |
|---|---|---|---|
| 1 | **Epic 4 planning re-review** — rewrite Story 4.1–4.4 ACs against the post-3.5 sources: `snapshot_store.db` (Axis A + last payload), `urn:mak:space/*` + `urn:mak:canary` graphs (Axes B & C), browser-side `computeAxis*` for derived state. Reuse canary coherence logic for Story 4.3. | Nicolas + PM agent | Before Story 4.1 creation |
| 2 | **Consolidate the two materializers** — extract `_SPARQL_SELECT` / `SPARQL_QUERY` and the `binding → feature` mapping into one shared module imported by both `main.py` and `scripts/materialize_geojson.py`. | Developer agent | Epic 4 prep (before any inspection-panel SPARQL work) |
| 3 | **Replace `_build_sparql_update` legacy fallback** — the error-path code in `main.py:787` still writes `mom:operationalState` / `mom:lastFetched`; either delete (fail-loud on exception) or rewrite to the three-token contract. | Developer agent | Epic 4 prep |
| 4 | **Push ontology additions to `mapsofmaking_ontology` repo** — `mom:countryCode` + `mom:timeZone` from Story 3.11; verify GitHub Pages publish. | Nicolas | Before Epic 4 |
| 5 | **SQLite hardening** — WAL mode + busy timeout on `snapshot_store.db`; narrow `httpx.RequestError` to exclude `InvalidURL`; persist `consecutive_failures` on error path. | Developer agent | Epic 4 prep or early Epic 4 (low-risk batch) |
| 6 | **DoD gate — “browser visual confirmation” added to story template** — codify what Story 3.10 made explicit: operator visually confirms any pipeline-touching change, not just `pytest` exit. | Developer agent | Add to story template now |
| 7 | **DoD gate — “derived state forbidden in storage”** — codify the three-token rule: storage holds facts (tokens), consumption layers compute derived buckets. Any PR adding a stored derived column trips the gate. | Developer agent | Add to story template now |
| 8 | Confirm Story 2.2 file status (Epic 3 carryover). | Nicolas | Before Epic 4 |

---

## Critical Path — Before Epic 4 Kickoff

1. Epic 4 planning re-review (Action 1) — **blocks Story 4.1 creation**.
2. Two-materializer consolidation (Action 2) — blocks Story 4.3’s INGESTED column SPARQL.
3. DoD gates 6, 7 added to story template.
4. `_build_sparql_update` legacy fallback (Action 3) — non-blocking but should land in Epic 4 prep so Epic 4’s inspection panel sees a clean error path.
5. Ontology repo sync, Story 2.2 confirmation — housekeeping, non-blocking.

---

*Retrospective conducted by Nicolas + Amelia (Developer). Focus on systems and processes — no blame.*
