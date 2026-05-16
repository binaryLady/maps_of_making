# Story 3.3: Mother Sands Diagnostic Canary

Status: ready-for-dev

## Story

As MOM (operator),
I want a programmatic way to drive a MOM-owned synthetic endpoint ("Mother Sands") through controlled states on each of the three signal axes,
so that when the public map shows something incoherent I can attribute the fault to a specific layer — MOM's pipeline vs the space's own endpoint — instead of guessing.

## Acceptance Criteria

### AC Framing — Critical

**The production bug (directory-imported spaces stuck on `seeded` despite successful fetch) is the MOTIVATION, NOT an AC.** An AC that depends on a bug existing cannot be completed once the bug is fixed. The bug is pinned separately by a regression test / root-cause story (Story 3.4), sequenced *after* 3.3. This story builds the diagnostic *instrument* — not a bug-fix story.

Acceptable ACs are about the *instrument*: inject a known state, assert the output matches the expected marker and card rendering, prove isolation.

---

### Three-Axis Truth Model

Every space's public marker is resolved by `effective_marker()` from **three independent signal axes**. The canary must perturb **exactly one axis at a time** to test each.

| Axis | Name | Classifier | Range | Drives | Fault Ownership |
|---|---|---|---|---|---|
| **A** | Reachability | `classify_endpoint_health()` | `healthy / unresponsive / warning / broken` | HTTP behavior (200/304/404/503, timeouts, consecutive failures) | **Endpoint-fault** → MOM emits coordinator CTA; not MOM's to fix |
| **B** | Lifecycle freshness | `classify_lifecycle()` | `seeded / confirmed / aging / zombie` + terminal `closed / dead` | Days since last **field-scoped meaningful content** update (identity, contact, location, network, open/close flip — NOT sensor noise) | **System-fault** → MOM's own responsibility |
| **C** | Open/Close boolean | Direct from SpaceAPI `state.open` | `open / closed / unknown` | The boolean presence and value | Presentational only |

**Key insight (new, Axis A):** A healthy endpoint polled every ~10min must never show `n > heartbeat_period`. Currently, "fetched 5h ago" wrongly classifies as `healthy`. Threshold = `heartbeat_period × multiplier` (configured in `config.yaml` under `endpoint_health`; e.g., `warning` at `>1.5×`, `broken` at `>3×`). **Not a magic number** — thresholds live in config.

**Key insight (new, Axis B):** The freshness clock must be **field-scoped**. Resets: identity, descriptive, contact, location, network, `open_now` flip. Does NOT reset: `sensors.*` block changes, telemetry. Implement as a **sensor-excluded projection / content-hash**, shared by the transformer and canary (one definition, two callers).

**Axis C scope is narrow:** Story 3.3 only proves (1) the boolean propagates end-to-end when `state.open` is present, and (2) graceful handling of ABSENCE — no `open` field → "no live signal", not a false closed. Epic 5 handles the opt-out UX (liveliness sovereignty).

---

### Axis A — Reachability

**Given** the operator runs `make canary-a-reachable`, `make canary-a-timeout`, `make canary-a-dns-fail`, or `make canary-a-http-error`
**When** the real heartbeat fetches Mother Sands
**Then** the endpoint serves the injected HTTP behavior and `classify_endpoint_health()` resolves to the expected rung

**And** a scenario where the last successful fetch was older than `heartbeat_period × warning_multiplier` (e.g., "fetched 15 min ago; period=10min; multiplier=1.5") resolves health to `warning` regardless of body validity

**And** a scenario where the last successful fetch was older than `heartbeat_period × broken_multiplier` (e.g., "fetched 30 min ago") resolves to `broken`

---

### Axis B — Lifecycle Freshness

**Given** the operator runs `make canary-b-seeded`, `make canary-b-confirmed`, `make canary-b-aging`, `make canary-b-zombie`, or `make canary-b-closed`
**When** the real heartbeat fetches Mother Sands and the transformer classifies lifecycle
**Then** the lifecycle state resolves to the expected value per the injected days-since-update (via `simulatedAge` seam, not an `if canary:` branch)

**And** a fetch whose only delta from the previous snapshot is a `sensors.*` field change does NOT advance the lifecycle last-update timestamp (field-scoped diff test)

**And** a fetch where the `openNow` boolean flips **does** reset the clock (material change test)

**And** `classify_lifecycle(days)` produces the expected state: `confirmed` < 30d, `aging` 30–90d, `zombie` 90–180d, `dead` ≥ 180d (thresholds from `config.yaml`)

**And** both terminal states exist: `closed` = operator-declared retirement (authoritative), `dead` = auto-inferred after N consecutive failed fetches (inferred). Terminal semantics are clear in the comment / output.

---

### Axis C — Open/Close Boolean

**Given** the operator runs `make canary-c-openclose-open` or `make canary-c-openclose-shut`
**When** the real heartbeat fetches the Mother Sands endpoint
**Then** the `openNow` boolean propagates end-to-end: injected → `heartbeat_log.db` → Oxigraph → rendered card open/closed pill

**And** a scenario with **no `open` field** in the SpaceAPI payload does not break the pipeline and does not produce a false "closed" — absence reads as "no live signal"

**And** the card rendering correctly distinguishes `unknown` (absent) from `closed` (explicit boolean false) — both visually and in the written text

---

### Coherence-Diff Report (Core AC)

**Given** the canary has injected a known `(endpoint_health, lifecycle_state, openNow)` triple
**When** the operator queries the canary output
**Then** the canary emits a **per-layer coherence-diff report** across four layers:

```
1. Baseline: expected state from injected triple
2. Endpoint file: what Mother Sands endpoint served
3. Heartbeat record: what heartbeat_log.db persisted (endpoint_health, lifecycle_state, open_now, last_effective_marker)
4. Oxigraph: what the SPARQL query returned (mom:operationalState, mom:dynamicState, resolved marker in GeoJSON)
5. Rendered card: what the frontend renders (status pill, "updated X ago", "fetched Y ago", open/closed pill)
```

Each row shows: injected value → stored value → rendered value. The report **flags the layer where reality diverges** — never a boolean pass/fail. "All green" is legitimate **only** when every layer agrees with every other AND with the injected intent.

---

### Isolation (Named Graph)

**Given** the canary has been run multiple times with various scenarios
**When** a SPARQL query against the production-space named graphs (`<urn:mak:space/*>`) is executed
**Then** no canary triples leak into production: `SELECT COUNT(?s) WHERE { ?s ?p ?o . FILTER(CONTAINS(STR(?s), "canary")) }` returns 0

**And** `SELECT COUNT(?s) WHERE { GRAPH <urn:mak:canary> { ?s ?p ?o } }` returns the canary data intact

**And** isolation is asserted in the hermetic test suite (`test_transformer.py`) with an `ASK` query

---

### Baseline & Reset

**Given** the repository is cloned and `make canary-reset` is run
**When** the operator queries Mother Sands
**Then** the endpoint serves the canonical baseline (`data/canary/baseline.json`): healthy + confirmed + open, matching SpaceAPI v15 schema with `space`, `logo`, `url`, `contact`, `location.lat/lon` populated

**And** every scenario is baseline + one mutation. Baseline is checked into git and never mutated directly.

**And** `make canary-reset` restores the live served file from the committed baseline, clearing all injected faults

---

### Makefile Targets & Demo Cycle

**Given** the Makefile is complete
**When** the operator runs axis-prefixed targets
**Then** the following targets exist and work:

```makefile
# Axis A — Reachability
make canary-a-reachable
make canary-a-timeout
make canary-a-dns-fail
make canary-a-http-error

# Axis B — Lifecycle freshness
make canary-b-seeded
make canary-b-confirmed
make canary-b-aging
make canary-b-zombie
make canary-b-closed

# Axis C — Open/Close (note: false branch is 'shut', NOT 'close')
make canary-c-openclose-open
make canary-c-openclose-shut

# Group runners
make canary-axis-a
make canary-axis-b
make canary-axis-c
make canary-all

# Utilities
make canary-reset
make canary-demo-cycle
```

**And** `make canary-demo-cycle` is a thin recipe that chains scenario targets across a lifecycle (seed → confirmed → aging → zombie → closed/dead) for the federated PoC demo. **No scripted-presentation logic** — just runs targets in sequence.

---

### Test Coverage — Two Surfaces

**Hermetic pytest** (`tests/test_transformer.py`):
- One parametrized test per scenario function, mocked fetch, deterministic, CI-runnable
- Includes the regression-pin test for the stuck-`seeded` bug (passes initially to demonstrate the bug exists, then pinned in Story 3.4 with a fix)
- Verifies `effective_marker()` logic
- Verifies field-scoped diff (sensors excluded, open-flip included)
- Verifies `<urn:mak:canary>` isolation

**Live operator-poke loop** (`docs/canary-operator-runbook.md`):
- Real heartbeat, real ETag/304 path, real frontend rendering
- Operator manually runs `make canary-X-Y`, then checks the live map
- Validates end-to-end pipeline: fetch → heartbeat_log → Oxigraph → GeoJSON → rendered card

**Both are mandatory.** The recurring Epic 3 bug lived in the gap between them — pytest never exercises the real fetch path, the poke loop never runs in CI.

---

### Truthfulness Requirement

**Given** Mother Sands appears on the public map
**Then** its drawer carries an honest **"Synthetic reference space"** label (one line) explaining it is a diagnostic instrument. The broadcast *content*, lore, persona, and website are Epic 8 — not this story.

**And** the drawer states the purpose: *"Mother Sands is MOM's diagnostic canary — a reference space we control to test our own data pipeline."*

---

### `public_ledger` Named Graph (Lock, Defer Schema)

**Given** this story is complete
**Then** a third Oxigraph named graph exists: `<urn:mak:public_ledger>` (renamed from `tombstone` in earlier brief)

**And** it is marked as **append-only, immutable, IPFS/IPLD-anchored event ledger** in documentation / code comments — the name and append-only principle are **locked** here

**And** the event schema, IPFS pinning mechanics, minting authority, and relocation UX are **deferred** to a dedicated future epic — **NOT this story**

---

## Tasks / Subtasks

- [ ] Task 1: Mother Sands endpoint — programmable HTTP server (AC: Axis A injections, safe write protocol)
  - [ ] Create `data/canary/baseline.json` — SpaceAPI v15 canonical baseline (healthy + confirmed + open) with space, logo, url, contact, location.lat/lon
  - [ ] Create `data/canary/mother-sands-endpoint.py` — a lightweight HTTP server (Flask or stdlib) that serves the file + supports controllable HTTP behavior (`MODE=ok|timeout|404|503`)
  - [ ] Implement safe write protocol: temp file → fsync → atomic os.rename → invalidate ETag/Last-Modified in `heartbeat_log.db` for that URL
  - [ ] Document the endpoint in `docs/canary-setup.md` (how to start it, what it serves, how injection works)

- [ ] Task 2: Scenario library — code-defined pure functions with 4-section docstrings (AC: all axis scenarios)
  - [ ] Create `scripts/canary_scenarios.py` — pure functions for each scenario (Axis A: reachable/timeout/dns-fail/http-error; Axis B: seeded/confirmed/aging/zombie/closed; Axis C: openclose-open/shut)
  - [ ] Each function: returns served-file payload + optional HTTP-behavior overrides; docstring sections: INJECT / STATE / EXPECT MARKER / EXPECT CARD
  - [ ] **Shared helper:** field-scoped diff function (sensors excluded, open-flip included) — used by transformer AND canary assertion
  - [ ] No persisted library (Option B) — code-defined only

- [ ] Task 3: Makefile targets — axis-prefixed group runners (AC: all Makefile targets exist and work)
  - [ ] Create Makefile `canary-*` targets: `canary-a-*` (4 targets), `canary-b-*` (5 targets), `canary-c-*` (2 targets)
  - [ ] Create group runners: `canary-axis-a`, `canary-axis-b`, `canary-axis-c`, `canary-all`
  - [ ] Create utilities: `canary-reset` (restore from baseline.json), `canary-demo-cycle` (thin recipe chaining targets)
  - [ ] Each target mutates the live served file via the safe write protocol, then triggers a manual or automatic heartbeat fetch

- [ ] Task 4: Heartbeat log schema — add two columns (AC: coherence report columns)
  - [ ] Add to `heartbeat_log.db` schema: `last_open_now` (boolean), `last_effective_marker` (string)
  - [ ] Heartbeat fetch writes: health, lifecycle_state, open_now, effective_marker
  - [ ] Ensure backward compatibility if the columns already exist (check before altering)

- [ ] Task 5: Coherence-diff report — query all four layers (AC: per-layer report, no boolean)
  - [ ] Create `scripts/canary_coherence_report.py` — query endpoint file, heartbeat_log, Oxigraph, rendered GeoJSON
  - [ ] Output format: each layer on one row; shows injected / stored / rendered values
  - [ ] Flags divergent layers; passes only if all four agree with injection intent
  - [ ] Integrates with Makefile: `make canary-report` after each scenario

- [ ] Task 6: Hermetic pytest — scenario parametrization + isolation test (AC: hermetic tests, CI-runnable)
  - [ ] Create `tests/test_canary_scenarios.py` — parametrized test, one per scenario function
  - [ ] Mock the fetch; inject scenario payload; assert `effective_marker()` result matches expected marker
  - [ ] Verify field-scoped diff: sensors-only delta does not reset lifecycle clock; open-flip does
  - [ ] Isolation test: `ASK { FILTER(CONTAINS(STR(?s), "canary")) }` on production graphs returns false
  - [ ] Regression-pin test: create a test case that currently fails (stuck-`seeded` reproduction) — will pass once Story 3.4 fixes the root cause

- [ ] Task 7: Live operator runbook — documented poke loop (AC: docs/canary-operator-runbook.md)
  - [ ] Create `docs/canary-operator-runbook.md` — step-by-step guide: start the endpoint, run a scenario, check the live map, verify the card rendering
  - [ ] Include screenshots / expected outcomes for each axis
  - [ ] Note: this is the manual test surface — run separately from CI, validates real pipeline

- [ ] Task 8: Named graphs — `<urn:mak:canary>` isolation + `<urn:mak:public_ledger>` stub (AC: isolation, ledger naming locked)
  - [ ] All canary data is written to named graph `<urn:mak:canary>`, never to production `<urn:mak:space/*>` graphs
  - [ ] Verify SPARQL queries filtering by graph URI correctly isolate canary
  - [ ] Create `<urn:mak:public_ledger>` stub in ontology / documentation (append-only principle locked; schema deferred)
  - [ ] No event schema implementation (deferred to future epic)

- [ ] Task 9: Truthfulness label + documentation (AC: drawer copy, documentation of diagnostic intent)
  - [ ] Mother Sands drawer: add "Synthetic reference space — MOM diagnostic canary" label + one-line purpose
  - [ ] Create `docs/mother-sands-concept.md` (Epic 8 will expand this to full broadcast/lore content) — this story documents the diagnostic intent only
  - [ ] Clarify in comments: Bernard activation, broadcast content, website, time-bubble demo = Epic 8 (not this story)

- [ ] Task 10: Regression suite — all transformer tests still pass (AC: no regression)
  - [ ] `source venv/bin/activate && pytest infra/link_handler/test_transformer.py` — all 71 tests pass
  - [ ] Transformer behavior unchanged; only new code (canary scenarios, coherence report) added

---

## Dev Notes

### What this story is — and is not

**This is a diagnostic instrument story.** The goal is to give the MOM operator a **programmable way to drive all three signal axes independently** so that when the map shows something incoherent, the operator can narrow down whether the fault is in the endpoint, MOM's pipeline, or the frontend. **It is not a bug-fix story.** The production bug (stuck-`seeded`) is the motivation; the actual root cause + fix lives in Story 3.4, which comes after 3.3 builds the diagnostic tools.

**Epic 8 owns the storytelling/broadcast/lore side.** Mother Sands is a true sea fort (Maunsell sea fort concept, never-built eighth fort, squatted-gap framing) with a persona (Bernard, pronouns they/them) and a broadcast rig (changelog, feature comms, website). **That is not this story.** This story builds the technical canary instrument; Epic 8 dresses it in lore.

**Story 3.2c (lifecycle vocabulary drift fix) must land before this story.** This story depends on the ontology/code alignment being correct.

---

### Three-Axis Model — Core Conceptual Framework

Every space's marker is resolved by `effective_marker(endpoint_health, lifecycle_state, open_now)` — three **independent** axes. The canary proves each axis works in isolation.

**Axis A (Reachability / HTTP behavior):**
- Classifier: `classify_endpoint_health()` → `healthy / unresponsive / warning / broken`
- NEW INSIGHT: `n > heartbeat_period × multiplier` = warning / broken. "Fetched 5h ago" is NOT healthy. Config thresholds: `warning_multiplier=1.5`, `broken_multiplier=3.0` (open to tuning).
- Fault = endpoint unreachable/erroring → MOM nudges the coordinator; not MOM's to fix.

**Axis B (Lifecycle Freshness / Content-update days):**
- Classifier: `classify_lifecycle(days)` → `confirmed` / `aging` / `zombie` / `dead` (+ terminals `closed`, `seeded`)
- NEW INSIGHT: Field-scoped diff. `sensors.*` churn does NOT reset the clock. `openNow` flip DOES. Implement as a sensor-excluded projection (one definition, shared by transformer + canary).
- Fault = stale content → MOM's responsibility to investigate/fix.
- **Two terminals:** `closed` (operator-declared, authoritative), `dead` (inferred, uncertain). Names matter for UX copy.

**Axis C (Open/Close Boolean / SpaceAPI `state.open`):**
- Classifier: direct from payload or `unknown` if absent.
- Story 3.3 scope: prove it propagates end-to-end AND gracefully handles absence (no `open` field → "no live signal", not false closed).
- Epic 5 handles opt-out UX (liveliness sovereignty).

---

### Files Being Modified & Their Current State

| File | Change | Current State |
|---|---|---|
| `ontology/mom.ttl` | No change — Story 3.2c already aligned | `mom:operationalState` enumerates `seeded/confirmed/aging/zombie/closed/dead` + out-of-lifecycle; `mom:dynamicState` is the open/close boolean |
| `infra/link_handler/transformer.py` | No change — existing `effective_marker()` is correct | Returns one resolved marker given three inputs; lifecycle supersedes endpoint health |
| `infra/link_handler/test_transformer.py` | ADD tests for canary scenarios | Existing 71 tests must stay green |
| `heartbeat_log.db` schema | ADD `last_open_now`, `last_effective_marker` columns | Currently tracks `endpoint_health`, `lifecycle_state`; add two more for coherence report |
| (NEW) `data/canary/baseline.json` | Create canonical baseline | Healthy + confirmed + open Mother Sands, SpaceAPI v15 shape |
| (NEW) `data/canary/mother-sands-endpoint.py` | Create HTTP server | Serves baseline.json or scenario payload; MODE env var controls HTTP behavior |
| (NEW) `scripts/canary_scenarios.py` | Create scenario functions | Pure functions: each returns payload + optional HTTP overrides; docstring contract (INJECT/STATE/EXPECT MARKER/EXPECT CARD) |
| (NEW) `scripts/canary_coherence_report.py` | Create report generator | Query four layers; flag divergences; integrate with Makefile |
| (NEW) `Makefile` | ADD canary targets | `canary-a-*`, `canary-b-*`, `canary-c-*`, group runners, utilities |
| (NEW) `tests/test_canary_scenarios.py` | Create hermetic test suite | Parametrized, mocked, CI-runnable; includes regression-pin test |
| (NEW) `docs/canary-setup.md` | Create endpoint setup docs | How to start the endpoint, what it serves, how injection works |
| (NEW) `docs/canary-operator-runbook.md` | Create manual poke-loop guide | Step-by-step: run scenario, check live map, verify card |
| (NEW) `docs/mother-sands-concept.md` | Create concept doc | Diagnostic intent; lore/broadcast/website deferred to Epic 8 |

---

### Safe Write Protocol (Non-Negotiable)

The canary mutates the Mother Sands JSON file in a way that is safe under concurrent heartbeat fetches. **Do this exactly:**

1. Write scenario payload to a **temp file** (e.g., `/tmp/mother-sands-new-XXXX.json`)
2. **`fsync`** the temp file to ensure it hits disk
3. **Atomic `os.rename`** the temp file over the live served file (`data/canary/served.json`)
4. **Immediately invalidate the ETag/Last-Modified for that URL in `heartbeat_log.db`** — delete the cached ETag row so the next fetch is not served a stale 304

**Why step 4?** The project has been bitten by stale-ETag bugs before. If you mutate the file but don't invalidate the cache, the next heartbeat fetch will see the ETag hasn't changed and return a 304 — the mutation is never seen.

---

### Field-Scoped Diff Function (Shared)

Create a helper function that compares two SpaceAPI payloads and returns whether there was a **meaningful change** (identity, contact, location, network, open/close flip) — **excluding** sensor-block changes.

This function is used in **two places:**
1. **Transformer** (`infra/link_handler/transformer.py`) — decides whether to reset the lifecycle clock
2. **Canary** (`scripts/canary_scenarios.py`) — asserts whether a scenario mutation should reset the clock

**One definition, two callers.** Do not duplicate logic.

---

### `simulatedAge` Seam (Not an `if canary:` Branch)

When testing Axis B (lifecycle freshness), the dev needs to inject a synthetic last-update timestamp so the test can verify classification thresholds (confirmed @ 0d, aging @ 30d, zombie @ 90d, dead @ 180d).

**Inject as a classifier input, not as a branch inside the classifier:**

**Wrong:**
```python
def classify_lifecycle(days):
    if os.environ.get('CANARY_MODE'):
        days = os.environ.get('SIMULATED_AGE')
    # ... rest of logic
```

**Right:**
```python
# In the heartbeat harness:
days_since_update = get_days_since_update(space_uri)
if os.environ.get('CANARY_MODE'):
    days_since_update = float(os.environ.get('SIMULATED_AGE', days_since_update))
state, reason = classify_lifecycle(days_since_update)
```

The classifier remains pure; the seam is in the caller.

---

### `effective_marker()` as Oracle

The canary's core assertion: given a known `(endpoint_health, lifecycle_state, openNow)` triple, the resolved marker from `effective_marker(...)` matches the expected marker. This is the "oracle" that proves the three-axis model works.

Current `effective_marker()` logic (from transformer.py:157):
- `lifecycle_state == "seeded"` → `seeded`
- `lifecycle_state == "closed"` → `closed`
- `lifecycle_state == "dead"` → `dead`
- `lifecycle_state == "zombie"` → `zombie`
- `lifecycle_state == "aging"` → `aging`
- `endpoint_health == "broken"` → `broken`
- `open_now == True` → `open`
- else → `confirmed`

**This logic is correct and must not change.** The canary tests it.

---

### Baseline & Scenarios

**Baseline** (`data/canary/baseline.json`):
- Canonical healthy + confirmed + open Mother Sands
- SpaceAPI v15 shape: `api_compatibility: ["14", "15"]`, `space`, `logo`, `url`, `contact`, `location: {lat, lon}`
- Checked into git; never mutated directly
- `make canary-reset` restores from it

**Scenarios** (in `scripts/canary_scenarios.py`):
- Pure functions; each returns (payload, http_behavior_override)
- Docstring contract: INJECT / STATE / EXPECT MARKER / EXPECT CARD
- No Option B (persisted library) — code-defined only. Option B is a possible Epic 4+ concern if needed.

---

### Coherence Report — The Core UX

The report answers: "I injected X on Axis Y; where is the fault if the map looks wrong?"

It compares four layers:

```
INJECTED: endpoint_health=broken, lifecycle=zombie, openNow=true
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Endpoint file:   {actual served JSON with injected mutation}
Heartbeat log:   endpoint_health=broken ✓  lifecycle_state=zombie ✓  open_now=true ✓  marker=zombie ✓
Oxigraph SPARQL: mom:operationalState="zombie" ✓  mom:dynamicState="open" ✓
GeoJSON:         status=zombie ✓  "fetched 5 min ago" ✓  open pill ✓
Card (UI):       zombie marker ✓  "updated N days ago" ✓  open/closed pill ✓

RESULT: All layers agree. Injection → resolution → rendering coherent. ✓
```

If one layer diverges, the report flags it: *"Heartbeat log shows broken health but GeoJSON shows confirmed — check heartbeat_log schema or materialization query."*

---

### Two Test Surfaces — Why Both Matter

**Hermetic pytest:** Fetch is mocked. Tests run offline, deterministic, in CI. Proves the **classifier logic**.

**Live operator poke loop:** Real heartbeat, real ETag/304 caching, real frontend. Proves the **fetch/timer/ETag/update pipeline**.

**The recurring Epic 3 bug lived in the gap between them.** Pytest passed but the real pipeline broke. Both are mandatory.

---

### Regression-Pin Test (For Story 3.4)

Create a test case that reproduces the stuck-`seeded` bug: directory-imported space, successful fetch, valid JSON, correct lat/lon — yet stays `seeded` instead of transitioning to `confirmed`.

**In Story 3.3, this test FAILS** (the bug exists). It proves the bug is reproducible.

**In Story 3.4, this test PASSES** (the bug is fixed). It is the regression guard.

---

### Naming Decisions (Locked by Roundtable)

**`closed` (Axis B — lifecycle):** operator-declared retirement, terminal state, authoritative.

**`open` / `shut` (Axis C — boolean):** present state. Note: Axis C's false branch is `shut` (not `close`), a one-letter guard. Find-and-replace targeting Axis C cannot accidentally break Axis B.

**`openclose` (Makefile target prefix):** `canary-c-openclose-open`, `canary-c-openclose-shut` (not `close`).

---

### Project Structure Notes

- `data/canary/baseline.json` — committed to git; canonical baseline
- `data/canary/served.json` — runtime; mutated by scenario injection; not in git
- Endpoint server runs locally during tests/manual poke; can be started by Makefile or manually
- All scenario mutations go through the safe write protocol (temp → fsync → atomic rename → ETag invalidation)
- Oxigraph `<urn:mak:canary>` graph is isolated from production `<urn:mak:space/*>` graphs

---

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.3: Mother Sands Diagnostic Canary]
- [Source: _bmad-output/planning-artifacts/mom_handoff_2026-05-16.md] — **Authoritative. Full design record. Read it in full before starting.**
- [Source: _bmad-output/planning-artifacts/mom_handoff_2026-05-15.md#Bernard — character bible] — Bernard persona (pronouns, voice, reference inspirations); Epic 8 owns activation
- [Source: _bmad-output/planning-artifacts/mom_handoff_2026-05-15.md#Mother Sands — space concept] — Maunsell sea fort lore; Epic 8 owns storytelling
- [Source: infra/link_handler/transformer.py#effective_marker (line 157), #classify_endpoint_health (line 103), #classify_lifecycle (line 130)]
- [Source: infra/link_handler/test_transformer.py] — 71 existing tests; canary tests are new parametrized additions

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
