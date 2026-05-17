# Story 3.4b: Clean Slate + Real Canary Endpoint

Status: ready-for-dev

**Story ID:** 3.4b  
**Epic:** 3 (Ingestion Pipeline + Endpoint Health)  
**Branch:** mom-demo  
**Dependencies:** Story 3.4 (bugs fixed, regression tests solid)  
**Sequenced after:** Story 3.4

---

## Story

As MOM (operator), I want a clean Oxigraph store with only the canary space and a real public canary endpoint URL, so the ingestion pipeline can be verified end-to-end from a known-good baseline without the accumulated complexity of bulk-seeded legacy data.

---

## Context

**Why this story exists:**

The 3.x bug hunt (Stories 3.2b, 3.2c, 3.3, 3.4) identified and fixed three real code defects in the heartbeat pipeline. However, the stuck-seeded symptom for bulk-seeded spaces (VOW, RFF, SpaceAPI directory ~600 spaces) did not fully resolve. Continued patching on top of layered complexity creates more knots.

**Root cause of the knot:** The pipeline was developed with 600 bulk-seeded spaces as the primary dataset. These spaces carry legacy state, inconsistent timestamps, and schema drift from multiple migration rounds. The combination of bulk data + evolving schema + successive bug fixes creates a state that is hard to reason about.

**Decision:** Strip Oxigraph to a clean state, archive bulk seed data for progressive future reimport, and verify the pipeline with a single known-good reference point (Mother Sands canary). Then build 3.5 schema artifacts on this clean foundation.

**Lessons learned from 3.x (guardrails for future stories):**
1. **SPARQL separator bug** — When prepending a revival `DELETE/WHERE` to a main `DROP+INSERT`, always join with ` ;\n`. Test: both blocks parse as valid combined SPARQL.
2. **DROP wipes all triples** — `DROP SILENT GRAPH` + `INSERT DATA` on no-diff cycles must re-insert preserved values (`mom:lastUpdated` via `preserved_last_updated` metadata). Test: no-diff cycle does not erase timestamps.
3. **304 path must update lastFetched** — HTTP 304 skips content write by design, but `mom:lastFetched` must still be written. Test: space returning 304 shows fresh "fetched N ago" caption.
4. **Canary endpoint must be reachable from heartbeat** — Container-local endpoints are not fetchable by the link-handler container. Real URL required. Test: `make canary-report` coherence check passes end-to-end.

**Mother Sands friction resolved here:** The canary endpoint was running as a local Python HTTP server inside the container at `localhost:9191` — unreachable for real heartbeat fetch validation. This story publishes the canary JSON to the VPS static nginx, giving it a real fetchable URL: `https://mapsofmaking.org/canary/mother-sands.json`.

---

## Acceptance Criteria

### AC 1: Oxigraph Clean State

**Given** the reset operation  
**When** `make reset` is run  
**Then** Oxigraph contains only:
- Ontology graphs (`urn:mak:ontology/*`)
- Canary graph (`urn:mak:canary`) with Mother Sands

**And** `SELECT * WHERE { GRAPH ?g { ?s ?p ?o } }` returns no `urn:mak:space/*` triples from bulk seeds

### AC 2: Seed Data Archived

**Given** the VOW, RFF, and SpaceAPI directory bulk seed files  
**When** this story is done  
**Then** they are moved to `data/archive/` (not deleted)  
**And** `infra/link_handler/seed_import.py` is marked deprecated with a header comment  
**And** the `make reset` target does NOT re-seed any bulk data

### AC 3: Real Canary Endpoint

**Given** `data/canary/served.json`  
**When** `make endpoint` is run  
**Then** the file is published to the VPS nginx static server  
**And** `https://mapsofmaking.org/canary/mother-sands.json` returns the served JSON with HTTP 200  
**And** `data/canary/baseline.json` `url` field points to `https://mapsofmaking.org/canary/mother-sands.json`

### AC 4: Pipeline Verified End-to-End

**Given** the clean Oxigraph and real canary endpoint  
**When** a heartbeat fetch is triggered for Mother Sands  
**Then** the space fetches from `https://mapsofmaking.org/canary/mother-sands.json`  
**And** `make canary-report` shows all layers coherent (endpoint ✅ → heartbeat_log ✅ → Oxigraph ✅ → GeoJSON ✅)  
**And** Mother Sands appears on the map with `confirmed/healthy` state

### AC 5: Tests Still Green

**Given** the clean-slate changes  
**When** `pytest tests/ -v` is run  
**Then** all tests pass (14 regression tests + 83 transformer tests + any others)

---

## Tasks / Subtasks

- [ ] **Task 1: Wipe Oxigraph and verify clean state**
  - [ ] Run `make reset`
  - [ ] Query Oxigraph: confirm only ontology + canary graphs remain
  - [ ] Re-load ontology if `make reset` wipes it (check what reset does)

- [ ] **Task 2: Archive bulk seed data**
  - [ ] Create `data/archive/` directory
  - [ ] Move `data/moms_seed.json`, `data/rff_mockup.json`, and any other bulk seed files
  - [ ] Add deprecation header to `infra/link_handler/seed_import.py`
  - [ ] Update `.gitignore` if needed

- [ ] **Task 3: Publish canary JSON to VPS (`make endpoint`)**
  - [ ] Add bind-mount in `docker-compose.dev.yml`: `web/canary/` → `/var/www/mapsofmaking/canary/`
  - [ ] Add `make endpoint` Makefile target that copies `data/canary/served.json` → `web/canary/mother-sands.json`
  - [ ] Deploy to VPS: copy `web/canary/` to VPS static root (rsync or scp)
  - [ ] Verify: `curl https://mapsofmaking.org/canary/mother-sands.json` returns valid JSON

- [ ] **Task 4: Update canary baseline URL**
  - [ ] Update `data/canary/baseline.json` `url` → `https://mapsofmaking.org/canary/mother-sands.json`
  - [ ] Update `data/canary/served.json` `url` → same
  - [ ] Update the Mother Sands seed record in Oxigraph `endpointUrl` → same
  - [ ] Run `make canary-reset` to sync served.json from updated baseline

- [ ] **Task 5: Verify pipeline end-to-end**
  - [ ] `make canary-b-confirmed` → inject confirmed scenario
  - [ ] `make endpoint` → push to VPS
  - [ ] Trigger heartbeat for Mother Sands
  - [ ] `make canary-report` → all layers green
  - [ ] Mother Sands visible on map with `confirmed/healthy`
  - [ ] `pytest tests/ -v` → all tests pass

---

## Dev Agent Record

### Lessons Learned (from Stories 3.2b–3.4)

| Bug | Root Cause | Guard |
|---|---|---|
| Revival SPARQL parse error | Missing `;` separator between revival DELETE block and main DROP+INSERT | Join with ` ;\n`; test combined SPARQL validates |
| `mom:lastUpdated` wiped on no-diff | `DROP SILENT GRAPH` erases prior value; INSERT omits it when `content_changed=False` | Pass `preserved_last_updated` via metadata; re-insert across DROP |
| `mom:lastFetched` frozen on 304 | 304 path called `build_state_only_update` only on state change; `lastFetched` never written | 304 path always writes `lastFetched` |
| Canary unreachable from heartbeat | `localhost:9191` not accessible from link-handler container | Publish to real URL; test via canary-report coherence check |

---

## Files List

| File | Change |
|---|---|
| `Makefile` | Add `endpoint` target |
| `docker-compose.dev.yml` | Add bind-mount `web/canary/` → `/var/www/mapsofmaking/canary/` |
| `web/canary/mother-sands.json` | New (gitignored, generated by `make endpoint`) |
| `data/canary/baseline.json` | Update `url` to real VPS URL |
| `data/canary/served.json` | Update `url` to real VPS URL |
| `data/archive/` | New dir; receives `moms_seed.json`, `rff_mockup.json` |
| `infra/link_handler/seed_import.py` | Add DEPRECATED header |

---

## Change Log

| Date | Change |
|---|---|
| 2026-05-17 | Story created — clean-slate pivot after 3.x bug hunt |
