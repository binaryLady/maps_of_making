# Mother Sands Canary — Operator Runbook

This runbook is the **manual test surface** for the Mother Sands diagnostic canary. Run it when the public map shows something incoherent and you need to attribute the fault to a specific layer.

See also: `docs/canary-setup.md` for first-time setup.

---

## The Three Axes

| Axis | What it tests | Fault owner |
|------|--------------|-------------|
| **A** — Reachability | HTTP behaviour of the endpoint | Endpoint/network — MOM nudges coordinator |
| **B** — Lifecycle freshness | Days since last meaningful content update | MOM's pipeline responsibility |
| **C** — Open/Close boolean | `state.open` boolean propagation end-to-end | Presentational |

---

## Prerequisites

```bash
# 1. Start the local stack
make startdev

# 2. Restore baseline (healthy + confirmed + open)
make canary-reset

# 3. Start the canary endpoint in a separate terminal
python3 data/canary/mother-sands-endpoint.py
# → listening on :9191

# 4. Register Mother Sands with the heartbeat (one-time setup)
#    The endpoint URL is http://localhost:9191/
#    Space URI: urn:mak:canary/mother-sands
#    Use the admin panel or seed script to add it.
```

---

## Axis A — Reachability

### Scenario: healthy endpoint

```bash
make canary-a-reachable
make heartbeat
make canary-report
```

**Expected card:** open pill; "fetched N min ago" (recent)

### Scenario: timeout

```bash
make canary-a-timeout
# Restart the endpoint with MODE=timeout:
# Ctrl-C the endpoint, then:
MODE=timeout python3 data/canary/mother-sands-endpoint.py &
make heartbeat
make canary-report
```

**Expected card:** endpoint issue; "fetched X ago" — timestamp stalls as heartbeat retries fail.

### Scenario: HTTP 503

```bash
make canary-a-http-error
MODE=503 python3 data/canary/mother-sands-endpoint.py &
make heartbeat
make canary-report
```

**Expected card:** broken marker after failures accumulate past threshold.

### Scenario: DNS fail {#axis-a-dns-fail}

The Makefile target can't automate DNS failure (requires changing the registered URL). Do it manually:

1. In `heartbeat_log.db`, update the space URL to `http://unresolvable.invalid/`
2. `make heartbeat`
3. `make canary-report`

**Expected:** `ConnectError` in logs; health degrades over time to `broken`.

---

## Axis B — Lifecycle Freshness

Each target injects a `simulatedAge` value via `ext_mom.simulatedAge` in the payload. The heartbeat reads this and passes it to `classify_lifecycle()`.

```bash
# Walk through the lifecycle in order:
make canary-b-seeded        # never updated → seeded marker
make heartbeat && make canary-report

make canary-b-confirmed     # 0 days → confirmed / open
make heartbeat && make canary-report

make canary-b-aging         # 45 days → aging
make heartbeat && make canary-report

make canary-b-zombie        # 120 days → zombie
make heartbeat && make canary-report

make canary-b-closed        # operator-declared retirement → closed
make heartbeat && make canary-report
```

Or run the full demo lifecycle chain:
```bash
make canary-demo-cycle
```

**Verify for each scenario:** The coherence report shows the same lifecycle state across heartbeat_log, Oxigraph, and the GeoJSON.

---

## Axis C — Open/Close Boolean

```bash
make canary-c-openclose-open
make heartbeat && make canary-report
# Expected: open pill visible in drawer
```

```bash
make canary-c-openclose-shut
make heartbeat && make canary-report
# Expected: no open pill; "Confirmed" status (not closed — that's Axis B)
```

**Note:** The false branch is `shut` (not `close`) to avoid collision with Axis B's `closed` lifecycle state.

**Absence test (manual):**
```bash
# Edit served.json to remove the state field entirely, then:
make heartbeat && make canary-report
# Expected: no open/closed pill; absence reads as "no live signal", not "closed"
```

---

## Coherence-Diff Report

```bash
make canary-report
```

The report queries all four layers and flags where they disagree:

```
━━ Mother Sands Canary Coherence Report ━━━━━━━━━━━━━━━━━━━━━━
[1] Endpoint file    data/canary/served.json
    state.open: True
    simulatedAge: 0

[2] Heartbeat log   data/tasks/heartbeat_log.db
    endpoint_health:  healthy
    lifecycle_state:  confirmed
    open_now:         True
    effective_marker: open
    last_fetched:     2026-05-16T...

[3] Oxigraph SPARQL  GRAPH <urn:mak:canary>
    mom:operationalState: confirmed
    mom:dynamicState:     open

[4] Rendered GeoJSON web/data/spaces.geojson
    status: open
    open_now: True

[isolation]
    ✓ No canary triples in production graphs

━━ Divergence analysis ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ✓ No layer divergences detected
```

If a layer diverges, the report tells you which layer is at fault. "All green" is only legitimate when every layer agrees with every other AND with the injected intent.

---

## Resetting

```bash
make canary-reset
# → restores data/canary/served.json from committed baseline.json
# → does NOT clear heartbeat_log.db (let the next heartbeat cycle overwrite it)
```

---

## Named Graph Isolation

Canary data must live only in `<urn:mak:canary>`. The coherence report runs an isolation SPARQL check on every run. You can also verify manually in Oxigraph:

```sparql
# Should return 0 (no canary subjects in production graphs)
SELECT (COUNT(?s) AS ?count) WHERE {
  GRAPH ?g { ?s ?p ?o . FILTER(CONTAINS(STR(?s), "canary")) }
  FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
}

# Should return the canary data intact
SELECT * WHERE { GRAPH <urn:mak:canary> { ?s ?p ?o } }
```

---

## When the Map Shows Something Incoherent

1. Run `make canary-report` to see where the divergence is.
2. If **Endpoint file ≠ Heartbeat log**: heartbeat didn't pick up the mutation (check ETag invalidation, check if endpoint is running).
3. If **Heartbeat log ≠ Oxigraph**: transformer write failed (check link-handler logs, check SPARQL update).
4. If **Oxigraph ≠ GeoJSON**: materializer didn't run or used stale data (trigger `make heartbeat` to rematerialize).
5. If **GeoJSON ≠ Card**: frontend rendering bug (check `effective_marker()` logic in app.js).
