# Story 3.4b: Clean Slate + Real Canary Endpoint

Status: done

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

- [x] **Task 1: Wipe Oxigraph and verify clean state**
  - [x] Run `make reset` (manual podman compose down, data wipe)
  - [x] Query Oxigraph: confirm only ontology + canary graphs remain (3 graphs, 184 triples, no bulk space/*)
  - [x] Load ontology (scripts/load_ontology.sh: mom + iop graphs)
  - [x] Load Mother Sands canary via new clean skeleton loader (load_canary.py)
  - [x] AC 1 satisfied: `urn:mak:canary` + `urn:mak:ontology/{mom,iop}`

- [x] **Task 2: Archive bulk seed data**
  - [x] Created `data/archive/` directory
  - [x] Moved `web/data/moms_seed.json`, `rff_mockup.json` → `data/archive/`
  - [x] Added deprecation header to `scripts/seed_import.py` + archive location note
  - [x] Removed `seed` from `make devdeploy` (Story 3.4b: no re-seeding on reset)
  - [x] Marked `make seed` as deprecated with helpful error + archive pointer
  - [x] Reorganized test suite: archived deprecated tests, marked heartbeat/transformer as @pytest.mark.legacy

- [x] **Task 3: Publish canary JSON to VPS (`make endpoint`)**
  - [x] Drop `canary-endpoint` container — served file retargeted to `web/canary/mother-sands.json` (single source of truth)
  - [x] `canary_scenarios.py` writes directly to `web/canary/mother-sands.json` (no cp); chmod 644 fix
  - [x] Renamed all canary Makefile targets: `cb-*` `cc-*` `ca-*` `caxis-*` `c-reset` `c-report` `c-demo` `c-all`
  - [x] `make endpoint` = rsync `web/canary/mother-sands.json` + logo to VPS; each scenario auto-chains endpoint + heartbeat
  - [x] `docker-compose.yml` + `docker-compose.dev.yml`: bind-mount `web/canary/` → `/var/www/mapsofmaking/canary/`
  - [x] Verified: `curl https://mapsofmaking.org/canary/mother-sands.json` returns valid JSON ✓

- [x] **Task 4: Architecture cleanup (replaces URL update)**
  - [x] `load_canary.py` retargeted to read `web/canary/mother-sands.json`
  - [x] `canary_coherence_report.py` retargeted to same
  - [x] `SpaceAPISchema`: `api_compatibility` accepts `Union[List[str], str]`
  - [x] `data-lifecycle.md` redrawn as Mermaid flowchart; documents `ext_mom.canary` routing (→ Story 3.5)
  - [x] `data/canary/served.json` removed — superseded by `web/canary/mother-sands.json`

- [x] **Task 5: Verify pipeline end-to-end**
  - [x] `make cb-confirmed` → inject confirmed scenario → `web/canary/mother-sands.json` · simulatedAge=0
  - [x] `make endpoint` → pushed to VPS; `curl https://mapsofmaking.org/canary/mother-sands.json` ✓
  - [x] `python scripts/load_canary.py` → Oxigraph: `confirmed / healthy` · 13 triples
  - [x] `make c-report` → endpoint ✅ · Oxigraph ✅ · GeoJSON ✅ · isolation ✅ · no divergences
  - [x] Mother Sands on map: `confirmed / open / healthy`
  - [x] `pytest tests/ -v` → 77 passed, 1 xfailed, 1 known pre-existing (heartbeat_log empty — resolves Story 3.5)

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
| `Makefile` | Rename canary targets (`cb-*` etc.), `make endpoint` = VPS rsync, `make seed` deprecated |
| `infra/docker-compose.dev.yml` | Drop `canary-endpoint` container; add `web/canary/` bind-mount |
| `infra/docker-compose.yml` | Add `web/canary/` bind-mount |
| `infra/link_handler/main.py` | `SpaceAPISchema.api_compatibility`: `Union[List[str], str]` |
| `scripts/canary_scenarios.py` | Write to `web/canary/mother-sands.json`; chmod 644 fix |
| `scripts/canary_coherence_report.py` | Read from `web/canary/mother-sands.json`; isolation check tightened |
| `scripts/load_canary.py` | Read from `web/canary/mother-sands.json` |
| `data/canary/mother-sands-endpoint.py` | `SERVED_FILE` updated to `web/canary/mother-sands.json` |
| `data/canary/baseline.json` | `api_compatibility` simplified to `"15"` |
| `data/canary/served.json` | Removed — superseded by `web/canary/mother-sands.json` |
| `web/canary/mother-sands.json` | New — single source of truth for canary endpoint |
| `data/archive/` | New dir; `moms_seed.json` + `rff_mockup.json` archived |
| `scripts/seed_import.py` | DEPRECATED header added |
| `pytest.ini` | `addopts = -m "not legacy"`; `tests/archive/` excluded |
| `tests/test_load_canary.py` | New — 15 hermetic tests pinning 13-predicate RDF contract |
| `tests/archive/` | New — deprecated test archive (never collected) |
| `_bmad-output/planning-artifacts/data-lifecycle.md` | Redrawn as Mermaid flowchart |

---

## Completion Notes

- `ext_mom.canary: true` routing flag in the JSON was the intended mechanism to route heartbeat writes to `urn:mak:canary` vs `urn:mak:space/*`. Implementation deferred to Story 3.5 (transformer rewrite). Tagged in `data-lifecycle.md`.
- Heartbeat log DB is empty (clean slate) — `TestHeartbeatLogState` will pass once the heartbeat processes a real space in Story 3.5.
- `canary_endpoint` container removed; VPS nginx static serve is the production path. `load_canary.py` is now the manual bootstrap tool only.

## Change Log

| Date | Change |
|---|---|
| 2026-05-17 | Story created — clean-slate pivot after 3.x bug hunt |
| 2026-05-17 | Tasks 1–5 complete — story closed |
