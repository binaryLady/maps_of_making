# Mother Sands Canary — Setup Guide

Mother Sands is MOM's diagnostic canary: a synthetic space we control to test our own data pipeline. This guide covers starting the endpoint and injecting scenarios.

## Quick Start

```bash
# Restore baseline (healthy + confirmed + open)
make canary-reset

# Start the endpoint server (port 9191)
python3 data/canary/mother-sands-endpoint.py &

# In another terminal: run a scenario
make canary-b-aging

# Run the coherence report
make canary-report
```

## How It Works

The endpoint (`data/canary/mother-sands-endpoint.py`) serves `data/canary/served.json`. Makefile targets mutate `served.json` via the **safe write protocol**:

1. Write new payload to a temp file
2. `fsync` to disk
3. Atomic `os.rename` over `served.json`
4. Invalidate the ETag/Last-Modified entry in `heartbeat_log.db` for this URL (prevents stale 304)

The baseline (`data/canary/baseline.json`) is committed to git and never mutated. `make canary-reset` restores `served.json` from baseline.

## HTTP Behaviour Injection (Axis A)

The `MODE` env var controls the HTTP response:

| MODE | Behaviour |
|------|-----------|
| `ok` (default) | 200 with JSON body + ETag |
| `timeout` | Accepts connection, never replies |
| `404` | 404 Not Found |
| `503` | 503 Service Unavailable |

```bash
MODE=timeout python3 data/canary/mother-sands-endpoint.py
```

## File Roles

| File | Role |
|------|------|
| `data/canary/baseline.json` | Committed canonical baseline — never mutated |
| `data/canary/served.json` | Runtime served file — gitignored, mutated by scenarios |
| `data/canary/mother-sands-endpoint.py` | Programmable HTTP server |
| `scripts/canary_scenarios.py` | Pure scenario functions |
| `scripts/canary_coherence_report.py` | Per-layer diagnostic report |

## Named Graph Isolation

Canary data lives in `<urn:mak:canary>` — never in production `<urn:mak:space/*>` graphs. The coherence report verifies this on every run.
