# Handoff Brief: Story 3.3 — Mother Sands Diagnostic Canary (Three-Axis Model)

**Date:** 2026-05-16
**From:** Nicolas + planning roundtable (party-mode: PM, Architect, Dev, UX, Analyst)
**To:** Claude Code (story-creation workflow + developer)
**Status:** Ready for story creation — supersedes the 2026-05-15 brief

---

## ⚠️ This brief SUPERSEDES `mom_handoff_2026-05-15.md`

A four-round team roundtable refined and in places **corrected** the 05-15 brief. Where the
two disagree, **this brief wins**. Nothing from the old brief is silently dropped — the table
below states exactly what changed and what carries forward.

### What changed vs. 05-15

| Topic | 05-15 brief said | This brief says (corrected) |
|---|---|---|
| Story 3.3 acceptance | "Canary must reproduce the production bug; `c-revive` resolves it" | The bug is the **motivation, not an AC**. An AC that depends on a bug existing cannot be completed once the bug is fixed. Bug is pinned by a separate regression test / root-cause story. |
| Lifecycle model | Flat list (`seeded → confirmed → aging → zombie → dead`) | **Three orthogonal signal axes** (Reachability / Lifecycle freshness / Open-Close). The marker is resolved by `effective_marker()` from all three. |
| Mother Sands serving | Static JSON file edited per scenario | **Programmable HTTP endpoint** with controllable serving modes. Axis-A faults (404/503/timeout) cannot be produced by editing JSON. |
| Canary output | Implied pass/fail | **Per-layer coherence-diff report**, never a boolean. |
| Makefile targets | Flat `c-*` list | **Axis-prefixed** targets (`canary-a-*`, `canary-b-*`, `canary-c-*`) + group runners. |
| Third Oxigraph graph name | `tombstone` | Renamed `public_ledger` (append-only event ledger). `tombstone` survives only as a UI marker style. |
| Terminal states | Single `dead` | **Two** terminal states: `closed` (declared) and `dead` (inferred). |

### What carries forward UNCHANGED from 05-15 (do not re-derive)

- **Bernard — character bible** (pronouns, personality vector, voice guide, reference
  inspirations). Still valid. See 05-15 brief §"Bernard — character bible".
- **Mother Sands lore** (8th never-built Maunsell fort, squatted-gap framing, U2–U7 fort
  rotation array with coordinates, salvage/dredge JSON content frame). See 05-15 §"Mother
  Sands — space concept".
- **Hermit-crab biology** (zoea → megalopa → juvenile → adult, molt/shell-change cadence,
  species notes). See 05-15 §"Hermit crab lifecycle → MOM mechanics map".
- **`mom_lore.md` skeleton** — the structure proposed in 05-15 §"`mom_lore.md` skeleton" is
  still the target scaffold. Epic 8 owns it.
- **Epic 8** — MOM as Living Space (website, profile card, lore, time-bubble demo mode,
  Bernard activation). Still a parallel, non-critical-path epic.
- **Domain `.org` canonical** + `.com` redirect janitorial pass. Still valid.

> The carry-forward sections above are storytelling/persona/website work. **They are Epic 8.**
> The corrections in this brief are about **Story 3.3's technical model only.**

---

## TL;DR

Story 3.3 builds the **Mother Sands diagnostic canary**: a programmable synthetic endpoint
plus an operator harness that drives it through controlled state changes, **one signal axis
at a time**, so that when the map shows something incoherent the operator can attribute the
fault to a specific layer — MOM's pipeline vs. the space's own endpoint.

Three things to internalise:

1. **Three orthogonal axes** resolve a marker: Reachability (A), Lifecycle freshness (B),
   Open/Close (C). The canary perturbs exactly one at a time.
2. **The output is a per-layer coherence-diff report**, not a green/red boolean. It shows,
   per layer, what *should* be true vs. what each layer *reports*, and flags the divergent
   layer.
3. Story 3.3 is a **diagnostic instrument**, not lore work and not a bug-fix. The bug is the
   motivation; the storytelling is Epic 8.

---

## Story 3.3 — Definition

### Single job

> Give the MOM operator a programmatic way to drive the MOM-owned "Mother Sands" synthetic
> endpoint through controlled state changes, so that an incoherent map can be attributed to a
> specific layer/axis.

It is a **diagnostic instrument**. It is **not** a side epic. It is **not** "reproduce a
production bug".

### AC framing — read this carefully

The production bug — *directory-imported spaces stuck on `seeded` despite a successful
fetch* — is the **MOTIVATION** for Story 3.3. It is **not** an acceptance criterion.

> An AC that depends on a bug existing cannot be completed once the bug is fixed.

- The bug is pinned **separately** by a failing regression test under `tests/test_*` that
  survives whoever fixes it.
- That root-cause + regression test is its own story — **Story 3.4**, sequenced after 3.3
  (3.3's diagnostic tools pin down the root cause). See "Decisions Resolved" below.

Acceptable AC shapes for 3.3 are about the *instrument*: "the canary can inject a known
triple on axis B and the resulting marker equals `effective_marker(...)`", "an Axis-A 503
mode produces `broken` health", "the coherence report flags the divergent layer", etc.

---

## The Three-Axis Model (core — replaces the 05-15 flat lifecycle)

A space's public map marker is resolved by `effective_marker()` from **three independent
axes**. The canary must perturb **one axis at a time**.

| Axis | Name | Classifier → values | Driven by | Fault ownership | Card line |
|---|---|---|---|---|---|
| **A** | Reachability | `classify_endpoint_health` → `healthy / unresponsive / warning / broken` | HTTP behavior of the served endpoint (200/304/404/503, timeouts, consecutive failures) | **ENDPOINT-fault** → MOM emits a CTA/nudge to the coordinator; not MOM's to fix | "fetched {n} ago" |
| **B** | Lifecycle freshness | `classify_lifecycle` → `seeded / confirmed / aging / zombie` + terminal `closed / dead` | Days since last *meaningful content* update | **SYSTEM-fault** → MOM's own responsibility to fix | "updated {m} ago" |
| **C** | Open/Close | `open_now` (SpaceAPI `state.open`) | The boolean itself | Presentational only — changes the pill | the open/closed pill |

`broken` (Axis A) means the **endpoint is unreachable/erroring** — **not** bad JSON content.

### Axis A — KEY INSIGHT (new): time-since-fetch is itself a health signal

A healthy endpoint polled every ~10 min must **never** show `n` greater than the heartbeat
period. `n > period` = elevated warning. The current code wrongly classifies "fetched 5h ago"
as `healthy`.

- Threshold = `heartbeat_period × multiplier`, configured in `config.yaml` under
  `endpoint_health` (e.g. `warning` at `>1.5×`, `broken` at `>3×`).
- **Not a magic number** — the multipliers live in config. (Exact values: open decision.)

### Axis B — KEY INSIGHT (new, load-bearing): the freshness clock must be FIELD-SCOPED

The content-diff that resets the freshness clock must be **field-scoped**:

- **Resets the clock** (meaningful change): identity/descriptive fields, contact, location,
  the open/close boolean *flip*, network membership.
- **Does NOT reset the clock**: a `sensors`-block value change, numeric telemetry.

If sensor noise reset the clock, every polled space would stay permanently `confirmed` and
the whole freshness axis becomes decorative.

> **Implement as a sensor-excluded projection / content-hash.** This projection function is
> **shared** by the transformer and by the canary assertion — one definition, two callers.

Axis B's "updated {m} ago" must match the Oxigraph last-update timestamp on the record.

### Axis C — scope is deliberately narrow for 3.3

Story 3.3 only does two things on Axis C:

1. Prove the boolean **propagates end-to-end** when `state.open` is present.
2. Prove **graceful handling of ABSENCE** — a space with no `open` field must not break the
   pipeline and must not get a false "open"/"closed". Absence reads as **"no live signal"**
   and is a first-class canary scenario.

Everything else on Axis C — the opt-out UX (CTA suggesting `openingHours`, a "no live status"
tag, deriving liveness from an events feed) — is **Epic 5**.

> Add a tracked **Epic 5 backlog placeholder**: *"Axis C: liveliness sovereignty & opt-out UX"*.
>
> **Sovereignty principle:** MOM measures and nudges, **never overrides** a space's choice.

---

## Naming Decisions: `closed` vs `close` (operator-confirmed, final)

This is intentional and **final**:

| Token | Axis | Meaning |
|---|---|---|
| `closed` | **B** (lifecycle) | A past **voluntary event** — the space retired. |
| `close` / `open` | **C** (boolean) | A current **present state**. |

The one-letter difference is a **deliberate guard**: a find-and-replace targeting Axis C must
not be able to break Axis B.

### Anti-collision scheme

- The string token `closed` is **RESERVED to Axis B only**.
- Code identifiers / Makefile targets / function names are **axis-prefixed**.
- Axis C **never emits a bare `close` token** — its false branch identifier is **`shut`**.
  - e.g. scenario `scn_c_openclose_shut`, Makefile target `canary-c-openclose-shut`.
- The operator and UI still read **"open" / "closed"**. The collision is removed **from code
  only**.

---

## Terminal States & Tombstone UI

Axis B has **two terminal states** (Reading B):

| State | Meaning | Provenance | Renders as |
|---|---|---|---|
| `closed` | Operator/coordinator **explicitly declared** retirement | Authoritative, intentional | `tombstone` marker — **solid, full opacity** |
| `dead` | MOM **auto-detected** end-of-life after N consecutive failed heartbeat cycles | Inferred, uncertain | `tombstone` marker — **same shape, dimmed / dashed outline** |

Both render in the `tombstone` marker **family**, but provenance differs and **must be
preserved** — declared vs. inferred is quality data.

The honest truth lives in the **drawer copy**:

- `closed` → *"Closed by operator — March 2026"*
- `dead` → *"No signal since January 2026 — presumed inactive. Automated inference, not a
  confirmation."*

> **Inference must confess it is inference.**

---

## Code ↔ Ontology Drift Fix

**The drift:** `effective_marker()` in `infra/link_handler/transformer.py` has a branch
`if lifecycle_state == "closed"`, but `mom:operationalState` in `ontology/mom.ttl` never
defined `closed` as a lifecycle value.

**The fix:**

1. In `mom.ttl`, update the `rdfs:comment` on `mom:operationalState` to enumerate **exactly**:
   `seeded, confirmed, aging, zombie, closed, dead` (`closed` + `dead` both terminal), plus
   out-of-lifecycle `error, unlinked`.
2. Add an explicit note that the open/close **boolean** belongs to `mom:dynamicState`, **NOT**
   to `operationalState`.
3. Remove / remap the stale `effective_marker()` branch so code and ontology agree.

> **Decided:** this is a small **pre-3.3 cleanup story** — split out, done before Story 3.3.

---

## Relocation & the `public_ledger` Graph

### Relocation is an EVENT, not a terminal state

A space can **relocate**. Relocation is **not** a terminal lifecycle state — the space stays
alive. It is an **append-only event**, decomposing into a linked pair of immutable records:

```
superseded@old-location  ──mom:relocatedTo──▶  seeded@new-location
        ◀──────────────── mom:relocatedFrom ──────────────────
```

- Space identity is **stable** across relocation: one `urn:mak:space/{slug}` IRI persists.
- `location` is a **current pointer**; per-location history lives in the event records.
- **The slug must NOT encode coordinates.**

### The renamed third graph: `public_ledger`

The third Oxigraph named graph (was `tombstone` in the 05-15 brief) is **renamed
`public_ledger`** — confirmed by Nicolas.

- It is an **append-only, immutable, IPFS/IPLD-anchored event ledger** for space life-events:
  registration/birth, relocation, schema upgrade, `closed`, `dead`, and future events (e.g.
  skill/certification records).
- `tombstone` survives **only** as a UI marker style name. `timeline` is a possible rendered
  projection. **Decoupled: graph name ≠ marker name.**

### Lock now / defer

| LOCK NOW (this session) | DEFER to a dedicated future Epic |
|---|---|
| The graph name `public_ledger` | The event schema |
| The append-only principle (write-once, never edited/deleted) | IPFS pinning mechanics |
| | Minting authority |
| | Relocation UX flow |

> **Relocation modeling is NOT Story 3.3.**
>
> A **false `dead`** (mistaking a relocation for a death) is the **worst error MOM can make**.
> Preventing it is the strategic rationale for the ledger: MOM gains verifiable **memory**,
> not just freshness.

---

## Story 3.3 — Build Shape (technical)

### Components

| Component | Detail |
|---|---|
| **Mother Sands endpoint** | A **programmable HTTP endpoint**, not a static JSON file. Needs a controllable serving mode, e.g. `MODE=ok\|404\|503\|timeout`. Axis-A faults cannot be produced by editing JSON. |
| **True canary path** | The **real MOM heartbeat** fetches the live Mother Sands endpoint — tests the real pipeline path. **Not** a direct store write. |
| **`effective_marker()` as oracle** | Inject a known `(health, lifecycle, open)` triple; assert the resolved public marker `== effective_marker(health, lifecycle, open)`. |
| **`c-reset` baseline** | A single canonical `data/canary/baseline.json` checked into git (healthy + confirmed + open Mother Sands). `c-reset` copies it over the live served file. Every scenario = baseline + one mutation. |
| **`heartbeat_log.db`** | Already persists `last_endpoint_health` and `last_lifecycle_state`. **ADD** `last_open_now` and `last_effective_marker` so the coherence report is a clean 3-column diff (injected / stored / rendered). |
| **Named graph isolation** | Canary data lives in its own graph `<urn:mak:canary>`, isolated from real-space graphs. Include a SPARQL `ASK` isolation test proving no canary triples leak into production queries. |
| **`simulatedAge` seam** | The lifecycle injection seam must **override the classifier INPUT** (inject a synthetic last-update), **never** add an `if canary:` branch inside the classifier. |

### Mother Sands has a dual identity

- **(a) Synthetic diagnostic canary** — **Story 3.3 scope.**
- **(b) MOM's own "broadcast" rig / comms platform** — conveys real info about MOM state, new
  features, changelog, recent real-space activity — **Epic 8 scope.**

Story 3.3 ships **one** truthfulness requirement here: an honest **"synthetic reference
space"** label in the drawer (one line). The broadcast *content* is Epic 8. ("Broadcast" +
the pirate-radio vibe matches the Mother Sands sea-fort lore.)

### Scenario library — Option A (code-defined pure functions)

- Each scenario is a **pure function** returning the served-file payload + optional
  HTTP-behavior overrides. **Not** a persisted data library.
- Each scenario function carries a **4-section docstring contract**, with the **axis named on
  line 1**:

  ```
  INJECT       — what gets mutated relative to baseline
  STATE        — the resulting (health, lifecycle, open) triple
  EXPECT MARKER — the marker effective_marker() should resolve to
  EXPECT CARD  — what the rendered card lines should say
  ```

  Reading the function **is** reading the test intent — this directly addresses the operator's
  distrust of opaque pass/fail scripts.
- **Option B** (persisted/replayable scenario library) is a possible **Epic 4+** concern,
  only if needed.

### Canary OUTPUT — a per-layer coherence-diff report, NOT a boolean

The canary compares, **per layer**, what *should* be true vs. what each layer *reports*:

```
endpoint file → heartbeat record → Oxigraph → rendered card
```

It flags the layer where reality diverges. **"All green" is legitimate only when every layer
agrees with every other AND with the injected intent.** This is the answer to "I don't trust
pass/fail scripts."

### Two test surfaces — split clean

| Surface | What it is | Proves |
|---|---|---|
| **(1) Hermetic pytest** | Fetch mocked, deterministic, CI-runnable. One parametrized test per scenario. Includes the regression-pin test for the stuck-`seeded` bug. | Classifier logic |
| **(2) Live operator-poke loop** | Real heartbeat, real ETag/304 path, real UI. Documented in `docs/canary-operator-runbook.md`. | The fetch / ETag / timer pipeline |

> Both are **mandatory**. The recurring Epic 3 bug lived in the **gap between them** — pytest
> never exercises the real fetch path, the poke loop never runs in CI.

### Safe injection write protocol

1. Write to a **temp file**, `fsync`.
2. **Atomic `os.rename`** over the served file — no torn reads.
3. Then **explicitly invalidate/refresh** the cached ETag/Last-Modified for that URL in
   `heartbeat_log.db`, so the next fetch is not served a stale `304`.

> The project has been bitten by **stale-ETag bugs** before — do not re-import that into the
> harness.

### Makefile targets — axis-prefixed (supersedes the 05-15 `c-*` flat list)

```makefile
# Axis A — Reachability
make canary-a-reachable          # endpoint healthy
make canary-a-timeout            # endpoint times out
make canary-a-dns-fail           # DNS failure
make canary-a-http-error         # endpoint returns 503 / error

# Axis B — Lifecycle freshness
make canary-b-seeded
make canary-b-confirmed
make canary-b-aging
make canary-b-zombie
make canary-b-closed

# Axis C — Open/Close   (note: false branch is 'shut', never bare 'close')
make canary-c-openclose-open
make canary-c-openclose-shut

# Group runners
make canary-axis-a
make canary-axis-b
make canary-axis-c
make canary-all

# Lifecycle utilities
make canary-reset                # restore Mother Sands to baseline.json
make canary-demo-cycle           # thin recipe chaining scenarios across a lifecycle
```

- **`canary-demo-cycle`** = a **thin recipe** chaining scenario targets across a lifecycle
  (seed → … → closed/dead) for the federated PoC demo. Confirmed as a thin wrapper — **no
  scripted-presentation logic.**

---

## Scope Boundaries

| Item | Owner |
|---|---|
| Three-axis canary instrument, programmable endpoint, scenario library, coherence report, two test surfaces, axis-prefixed Makefile | **Story 3.3** |
| Stuck-`seeded` root cause + regression test | **Story 3.4** — 3.3 builds the tools that pin (and likely solve) the root cause first |
| `mom.ttl` / `effective_marker` drift fix | **Pre-3.3 cleanup story** (decided — split out, done before 3.3) |
| Persisted/replayable scenario library (Option B) | **Epic 4+**, only if needed |
| Axis C opt-out UX — `openingHours` CTA, "no live status" tag, events-feed liveness derivation | **Epic 5** (add backlog placeholder: "Axis C: liveliness sovereignty & opt-out UX") |
| Mother Sands as broadcast rig — changelog, feature comms, lore content, website, Bernard activation, time-bubble ambient demo | **Epic 8** (parallel, non-critical-path) |
| Event schema, IPFS pinning mechanics, minting authority, relocation UX flow | **Dedicated future "public ledger / relocation" Epic** |

---

## Decisions Resolved (2026-05-16)

1. **Drift fix placement** — RESOLVED: split out as a small **pre-3.3 cleanup story**, done
   before Story 3.3.
2. **Root-cause story** — RESOLVED: the stuck-`seeded` root cause + regression test becomes
   **Story 3.4**, sequenced *after* 3.3. Rationale: 3.3 builds the diagnostic tools that pin
   down — and probably solve, or at minimum locate — the root cause.
3. **Config thresholds** — RESOLVED: confirmed. `config.yaml` `endpoint_health` multipliers
   for the stale-fetch warning are accepted (`warning` at `>1.5×` heartbeat period,
   `broken` at `>3×`).

---

## Carried-Forward Sections (from the 05-15 brief — still valid)

These are **not re-derived here**. They remain authoritative as written in
`mom_handoff_2026-05-15.md`. Cross-reference:

| Section | Where (05-15 brief) | Status |
|---|---|---|
| Bernard — character bible (pronouns, personality vector, voice guide, references) | §"Bernard — character bible" | Valid — Epic 8 input |
| Mother Sands lore (8th never-built fort, squatted gap, U2–U7 rotation array, salvage frame) | §"Mother Sands — space concept" | Valid — Epic 8 input |
| Hermit-crab biology (zoea → megalopa → juvenile → adult, molt/shell cadence) | §"Hermit crab lifecycle → MOM mechanics map" | Valid — Epic 8 input |
| `mom_lore.md` skeleton | §"`mom_lore.md` skeleton" | Valid — Epic 8 scaffold target |
| Epic 8 — MOM as Living Space | §"Epic 8 — MOM as Living Space" | Valid — parallel, non-critical-path |
| Domain `.org` canonical + `.com` redirect janitorial | §"Domain + DNS" | Valid |

> The 05-15 "production bug" section is **superseded** in framing only: the bug is real, but
> it is no longer a Story 3.3 acceptance criterion (see "AC framing" above).

---

*End of handoff brief. Supersedes `mom_handoff_2026-05-15.md`.*
