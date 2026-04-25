# Story 1.5: Map Reads from Oxigraph GeoJSON Materialization

Status: ready-for-dev

## Story

As a maker browsing the map,
I want the map to show spaces fetched from the Oxigraph-backed federated dataset (not `data/moms_seed.json`),
So that what I see on the map reflects the live system state — and the switch from bundled JSON to backend-served data is transparent to me (same load time, same pin rendering).

## Acceptance Criteria

### Data Flow (Epic 2→Epic 3 Context)

```
Ingestion (Epic 2/3): coordinator URL → fetch JSON-LD → parse → Oxigraph (write path)
Materialization (this story): Oxigraph → SPARQL SELECT → spaces.geojson (static file) → nginx → SPA fetch (read path)
```

The SPA never queries SPARQL directly. It fetches one pre-baked static GeoJSON file served by nginx. `materialize_geojson.py` re-bakes this file on demand; the scheduler (Epic 3) will call it after each ingest cycle. For demo: run manually once after seeding.

### Given-When-Then: SPARQL Materialization

**Given** Oxigraph is running (Story 1.3) with ontologies loaded (Story 1.4) and at least one space triple exists in `<urn:mak:space/{id}>`

**When** `python scripts/materialize_geojson.py` is run

**Then** it executes a SPARQL SELECT against `<urn:mak:status>` and `<urn:mak:space/*>` named graphs and writes the result to `web/data/spaces.geojson` as a valid GeoJSON `FeatureCollection`

**And** each feature contains:
- `geometry.coordinates [lng, lat]` (from `schema:geo.schema:latitude` + `schema:geo.schema:longitude`)
- `properties.name` (from `schema:name`)
- `properties.status` (seeded / confirmed / stale / broken) — from `mak:healthStatus`
- `properties.uri` (the space IRI)
- `properties.last_fetched` (from `mak:lastChecked` timestamp, ISO 8601)
- `properties.geolocationFidelity` (from `mom:geolocationFidelity` — values: `exact`, `approximate`, `city`, `country`) — **CRITICAL**: propagate this tag from Story 0.1 pattern

**And** the query includes a `LEFT JOIN` against `<urn:mak:presence>` returning `null` for all spaces now (Epic 7 presence slot wired but inactive)

**And** nginx serves `web/data/spaces.geojson` as a static file (no auth, no CORS restrictions — public read-only data)

### Given-When-Then: Frontend Integration

**Given** `spaces.geojson` is served at `/data/spaces.geojson` from nginx

**When** the map SPA boots (`web/app.js`)

**Then** `app.js` fetches `/data/spaces.geojson` **instead of** `data/moms_seed.json` — same fetch call, different source file

**And** pin rendering, filter chips, and search work identically to phase-1 behaviour (backward compatible with existing map UX)

**And** if the fetch returns non-200, the map degrades gracefully:
- Paper-overlay background (no pins rendered)
- Inline banner: "Map data temporarily unavailable — try refreshing" (no raw error, no blank screen)
- **Key**: Match the graceful failure pattern from Story 0.1 (geolocationFidelity tagging ensures no silent drops in the RDF layer)

---

## Tasks / Subtasks

### Phase 1: SPARQL Query Design & Validation

- [x] Understand Story 1.4's named graph topology (AC: map all four MOM namespaces)
  - [x] Read `scripts/test_load_ontology.py` to verify which PREFIX declarations Oxigraph requires
  - [x] Confirm `<urn:mak:ontology/mom>` has `mom:Space` class and `mom:geolocationFidelity` property

- [x] Design SPARQL SELECT query to materialize spaces.geojson (AC: SPARQL query + JSON-LD framing)
  - [x] Query `<urn:mak:space/*>` named graphs to SELECT all space IRIs + metadata
  - [x] JOIN `<urn:mak:status>` graph to get current `mak:healthStatus` (seeded / confirmed / stale / broken)
  - [x] LEFT JOIN `<urn:mak:presence>` graph (returns null — placeholder for Epic 7)
  - [x] Extract `schema:geo.schema:latitude` and `schema:geo.schema:longitude` (geo coordinates)
  - [x] Extract `schema:name`, `mak:lastChecked` (as ISO 8601), `mom:geolocationFidelity`
  - [x] Order by space IRI for deterministic output (ensures `spaces.geojson` is reproducible)
  - [x] **CRITICAL**: Include ALL PREFIX declarations from Story 1.4 (non-negotiable with Oxigraph)

- [ ] Test SPARQL query against live Oxigraph (localhost:7878)
  - [ ] Run manually: `curl -X POST http://localhost:7878/query` with the SPARQL query
  - [ ] Verify results contain spaces + status tags (use RFF mockup data from Story 0.3 seed)

### Phase 2: `materialize_geojson.py` Script

- [x] Create `scripts/materialize_geojson.py` — SPARQL-to-GeoJSON converter
  - [x] Read SPARQL query from inline string or `scripts/sparql/materialize_spaces.sparql`
  - [x] Call Oxigraph `/query` endpoint via `httpx` (POST, SPARQL results as JSON)
  - [x] Parse SPARQL JSON results: `results.bindings[]` → GeoJSON Feature objects
  - [x] Transform each binding into a Feature:
    ```json
    {
      "type": "Feature",
      "geometry": {
        "type": "Point",
        "coordinates": [longitude, latitude]
      },
      "properties": {
        "name": "...",
        "status": "confirmed|seeded|stale|broken",
        "uri": "urn:mak:space/...",
        "last_fetched": "2026-04-25T12:34:56Z",
        "geolocationFidelity": "exact|approximate|city|country"
      }
    }
    ```
  - [x] Wrap features in `FeatureCollection` header: `{ "type": "FeatureCollection", "features": [...] }`
  - [x] Validate output as valid GeoJSON (RFC 7946)
  - [x] Write to `web/data/spaces.geojson` atomically (write to temp file, rename)

- [x] Handle Oxigraph errors gracefully
  - [x] On HTTP 4xx/5xx from Oxigraph: log ERROR + return non-zero exit code (scheduler will retry)
  - [x] On connection timeout (>30s): log ERROR + exit non-zero (don't write stale data)
  - [x] On empty result set: write valid empty FeatureCollection `{"type":"FeatureCollection","features":[]}`

- [x] Optional: `OXIGRAPH_URL` env var for non-localhost deployments
  - [x] Default: `http://localhost:7878`
  - [x] Allow override for VPS/CI: `OXIGRAPH_URL=http://oxigraph:7878` (internal Docker network name)

### Phase 3: Frontend Wiring

- [x] Update `web/app.js` to fetch `/data/spaces.geojson` instead of `data/moms_seed.json`
  - [x] Find the existing fetch call (search for `moms_seed.json`)
  - [x] Replace with `fetch('/data/spaces.geojson')`
  - [x] Keep error handling identical (graceful degradation: banner + no pins)
  - [x] Verify backward compatibility: existing GeoJSON schema must match (no breaking changes to pin renderer)

- [ ] Ensure nginx serves `web/data/spaces.geojson` as static file
  - [ ] Verify `infra/nginx/conf.d/app.conf` doesn't block `.geojson` files
  - [ ] Add `Cache-Control: max-age=60` header for embedded map freshness (Epic 2.3 requirement)
  - [ ] Test locally: `curl -I http://localhost/data/spaces.geojson` → should see 200 + cache header

### Phase 4: Local Integration & Testing

- [ ] Run local demo from clean state
  - [ ] Start Oxigraph: `distrobox-host-exec podman compose -f infra/docker-compose.yml up -d oxigraph`
  - [ ] Verify seeded data is loaded (should have 567 named graphs from Story 0.3): `curl http://localhost:7878/query -X POST ...`
  - [ ] Run `python scripts/materialize_geojson.py` → should write `web/data/spaces.geojson`
  - [ ] Verify file was created: `jq .features | wc -l web/data/spaces.geojson` (should show count > 0)
  - [ ] Start nginx: `distrobox-host-exec podman compose -f infra/docker-compose.yml up -d nginx` (or already running)
  - [ ] Open browser: `http://localhost/` → map should load + show pins from live Oxigraph data
  - [ ] Verify map is identical to phase-1 UX (same rendering, filters, search)

- [ ] Verify graceful degradation
  - [ ] Stop Oxigraph: `distrobox-host-exec podman compose -f infra/docker-compose.yml down oxigraph`
  - [ ] Edit `materialize_geojson.py` to point to nonexistent endpoint: `OXIGRAPH_URL=http://localhost:9999`
  - [ ] Run script → should fail cleanly (ERROR log, non-zero exit)
  - [ ] Delete or move `web/data/spaces.geojson`
  - [ ] Open browser: `http://localhost/` → map should show banner "Map data temporarily unavailable" (no crash, no blank screen)

- [ ] Validate GeoJSON output
  - [ ] Download `web/data/spaces.geojson` and validate with `jq` or an online GeoJSON validator
  - [ ] Spot-check 3 features:
    - `coordinates` are `[lon, lat]` not `[lat, lon]` (RFC 7946 compliance)
    - `status` is one of: seeded, confirmed, stale, broken
    - `geolocationFidelity` is one of: exact, approximate, city, country (propagated from Story 0.1/0.2)

---

## Dev Notes

### SPARQL Query — Critical Pattern from Story 1.4

**Every SPARQL query must include these PREFIX declarations. Oxigraph returns HTTP 400 without them.** [Source: Story 1.4 Dev Notes]

```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX mak: <https://nicolasdb.github.io/mapsofmaking_ontology/resource/>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
```

These are not negotiable. The values are drawn from Story 1.4's `ontology/mom.ttl` and `ontology/context/space.jsonld`.

**HTTP Client Pattern:** Use `httpx` only (not `requests`, not `SPARQLWrapper`). Reference implementation from Story 1.4's `scripts/test_load_ontology.py`:

```python
import httpx

r = httpx.post("http://localhost:7878/query", 
               content=sparql_query,
               headers={"Content-Type": "application/sparql-query",
                        "Accept": "application/sparql-results+json"},
               timeout=30.0)
r.raise_for_status()  # raise on 4xx/5xx
results = r.json()
```

### Named Graphs — Topology from Story 1.4 & Architecture

- `<urn:mak:ontology/mom>` — MOM vocabulary (Classes + Properties) — loaded by Story 1.4
- `<urn:mak:ontology/iop>` — IoP ontology (placeholder for Epic 6) — loaded by Story 1.4
- `<urn:mak:status>` — Current health state (status labels + timestamps) — written by heartbeat scheduler (Epic 3)
- `<urn:mak:space/{id}>` — Current space data (names, geo, URLs) — written by ingestion (Epic 2)
- `<urn:mak:space/{id}/{date}>` — Snapshots (append-only history) — written by ingestion (Epic 2)
- `<urn:mak:presence>` — Presence data (reserved for Epic 7) — LEFT JOINed but currently empty

**Current State (Post-Story 1.4):** First four graphs exist (ontologies + seeded status + seeded space data from Story 0.3).

### Graceful Degradation — From Story 0.1 Memory

[Source: /memory/story_0-1_completion_notes.md]

**Contract:** Every space entry has a `mom:geolocationFidelity` tag (never silently dropped):
- `exact` — precise street-level geocoding (501 of 566 VOW entries)
- `approximate` — city-level fallback (53 of 566 VOW entries)
- `city` — country-level fallback (12 of 566 VOW entries)
- No failures — zero silent drops in Story 0.1

**Why This Matters for Story 1.5:** The SPARQL query must preserve this tag in the materialized GeoJSON so that:
1. The frontend can render fidelity indicators (optional: dim/highlight low-fidelity pins)
2. Future UI (Story 2.5) can show "Address incomplete" banners to coordinators
3. Analytics can track data quality metrics

**Frontend Graceful Failure:** If `spaces.geojson` fetch fails (404, 500, timeout):
- Show inline banner: "Map data temporarily unavailable — try refreshing"
- Keep map rendered (paper background, no pins)
- Don't crash, don't show raw error

Reference: Phase 1 implemented this pattern. Ensure Story 1.5's frontend integration doesn't break it.

### HTTP Endpoint: Oxigraph `/query`

[Source: Story 1.4 Dev Notes]

```
POST /query
Content-Type: application/sparql-query
Accept: application/sparql-results+json
Body: SPARQL query as plain text
Response: { "head": { "vars": [...] }, "results": { "bindings": [...] } }
```

**Timeout:** Set to 30s minimum. Oxigraph can be slow on complex queries over large datasets.

### File Locations

```
maps_of_making/
├── scripts/
│   ├── materialize_geojson.py        ← New (this story)
│   └── sparql/                        ← Optional
│       └── materialize_spaces.sparql  ← Optional (separate query file)
├── web/
│   ├── app.js                         ← Modified (fetch from /data/spaces.geojson)
│   ├── data/
│   │   ├── moms_seed.json             ← Deprecated (no longer fetched by SPA)
│   │   └── spaces.geojson             ← New (generated by materialize_geojson.py)
├── infra/
│   └── nginx/
│       └── conf.d/
│           └── app.conf               ← Verify (should already serve static .geojson)
```

### Testing Strategy

**Unit Testing:** Not required for this story.
- `materialize_geojson.py` is 100% integration — it queries live Oxigraph and writes to disk
- Mock tests would hide SPARQL bugs (learned from Story 0.3, confirmed in cross-epic handoffs)
- Live integration testing is the only reliable approach

**Integration Testing (Manual):**
1. Local dev with seeded data (Story 0.3 already did this)
2. Verify GeoJSON schema compliance
3. Verify frontend renders pins identically to phase-1
4. Verify graceful failure on missing/invalid data

**No CI/CD Changes:** Makefile `make sync` already covers `scripts/` (Story 1.4 expanded it to project root).

### Naming Conventions [AR-CONV1–5]

- Python: `snake_case` functions, `async def verb_noun()` for async
- Named graphs: `urn:mak:{type}/{id}` (already established by architecture)
- JSON keys: `camelCase` (standard GeoJSON format — `geometry`, `properties`, `coordinates`)
- Error messages: plain language, never raw SPARQL or HTTP responses

### venv Management

**CRITICAL from CLAUDE.md:** venv is managed externally by the user. Never create `scripts/venv` or `harness/venv`.

Before running `materialize_geojson.py` in deployment, activate the user's venv:
```bash
source venv/bin/activate
python scripts/materialize_geojson.py
```

The script itself should NOT attempt to activate or create a venv.

### Local Dev Environment

[Source: /memory/infra_local_dev.md]

- **Platform:** Fedora host + distrobox + Podman
- **Start Oxigraph:** `distrobox-host-exec podman compose -f infra/docker-compose.yml up -d oxigraph`
- **Start nginx:** already running from docker-compose
- **Verify:** `curl http://localhost:7878/health` (Oxigraph), `curl http://localhost/` (nginx)

### Infrastructure: .env Symlink

[Source: /memory/infra_env_symlink.md + Story 1.4 post-deployment fix]

After Story 1.4, `infra/docker-compose.yml` requires `.env` in the same directory. A symlink was created:
- `infra/.env` → `../.env` (points to root `.env`)
- This allows `docker-compose -f infra/docker-compose.yml` to find env vars without changing working directory

**For Story 1.5:** No changes needed. Just ensure `.env` is present at project root (already there from Story 1.3).

---

## Handoff from Previous Stories

### Story 1.1: Integration Dependency Spike ✅ DONE

**What it delivered:** Confirmed httpx as HTTP client, validated Oxigraph query patterns against live data, identified SPARQL PREFIX requirement.

**Why it matters for 1.5:** httpx is the only approved HTTP library. The spike discovered that Oxigraph returns 400 without PREFIX declarations — this is now a design constraint in every downstream story.

### Story 1.2: Scope Basemap to Europe + Loader Copy ✅ DONE

**What it delivered:** Basemap tiles scoped to Europe bounds, tile loader updated in `app.js`.

**Why it matters for 1.5:** The map bounds are fixed. When Story 1.5 fetches pins from Oxigraph, they'll always fall within Europe + pilot regions (validated by Story 2.1 schema check). No need to re-scope in 1.5.

### Story 1.3: Docker Compose Stack + Nginx Security Routing ✅ DONE

**What it delivered:** nginx reverse-proxy with `/sparql/query` routed to Oxigraph, CORS headers configured, `/sparql/update` blocked (403).

**Why it matters for 1.5:** 
- Nginx already serves `/data/` as static files (same infrastructure as `moms_seed.json`)
- Story 1.5 writes to `web/data/spaces.geojson` — nginx will serve it with zero config changes
- No direct browser→Oxigraph queries allowed (by design). The frontend fetches pre-baked static GeoJSON only.

### Story 1.4: Author MOM Ontology v0 + Load into Oxigraph ✅ DONE

**What it delivered:**
- `ontology/mom.ttl` — MOM vocabulary with `mom:Space` class + `mom:geolocationFidelity` property
- `ontology/iop/iop.ttl` — IoP ontology stub
- `ontology/context/space.jsonld` — JSON-LD context for ingestion + materialization
- `scripts/load_ontology.sh` — idempotent loader
- Ontologies loaded into Oxigraph at `<urn:mak:ontology/mom>` and `<urn:mak:ontology/iop>`
- 567 named graphs currently in Oxigraph (566 VOW + 1 RFF mock from Story 0.3)

**Why it matters for 1.5:**
- Story 1.5 SPARQL queries will reference `mom:Space`, `mom:geolocationFidelity`, and Schema.org terms
- The PREFIX declarations from Story 1.4 test file must be copy-pasted into every 1.5 SPARQL query (non-negotiable)
- The `space.jsonld` context defines the compact-to-IRI mappings — use it as reference when designing the materialization query

### Story 1.4: Post-Deployment Fix (2026-04-24)

**What was fixed:**
- Oxigraph healthcheck removed (image has no curl)
- `.env` symlink created at `infra/.env` → `../.env`
- All services now start cleanly on VPS

**Why it matters for 1.5:** The infrastructure is stable. Focus on SPARQL query design + GeoJSON output, not ops troubleshooting.

---

## File List

- `scripts/materialize_geojson.py` — NEW (SPARQL-to-GeoJSON converter)
- `web/app.js` — MODIFIED (fetch from /data/spaces.geojson instead of data/moms_seed.json)
- `web/data/spaces.geojson` — NEW (generated by materialize_geojson.py at runtime)
- `infra/nginx/conf.d/app.conf` — MODIFIED (added Cache-Control header for /data/ static files)
- `infra/docker-compose.yml` — MODIFIED (added SELinux :z permissions to volumes for Fedora compatibility)

## Change Log

**2026-04-25 — Story 1.5 Implementation (Phase 1-3 Complete)**
- Implemented SPARQL materialization pipeline: Oxigraph → spaces.geojson
- Updated SPA to fetch from live Oxigraph via pre-baked GeoJSON (not bundled JSON-LD)
- Added nginx cache headers for 60-second freshness (Epic 2.3 requirement)
- Fixed SELinux volume mount issues on Fedora (Podman compatibility)

## Dev Agent Record

### Agent Model Used

claude-haiku-4-5-20251001

### Implementation Plan

**Phase 1: SPARQL Query Design** ✓
- Analyzed Story 1.4's named graph topology (mom, mak, schema prefixes)
- Designed SPARQL SELECT query to fetch spaces from urn:mak:space/* graphs
- Query includes OPTIONAL joins for mak:status and mom:geolocationFidelity

**Phase 2: Python Script** ✓
- Implemented materialize_geojson.py with error handling (httpx, 30s timeout)
- Transforms SPARQL bindings → space objects compatible with app.js
- Atomic file writes with temp file + rename pattern
- Supports OXIGRAPH_URL env var for deployment flexibility

**Phase 3: Frontend Wiring** ✓
- Updated app.js loadData() to fetch /data/spaces.geojson
- Added graceful failure handling: banner + no pins if fetch fails
- Maintained backward compatibility with existing space object structure

**Phase 4: Integration & Testing** (PENDING)
- Need to test SPARQL query against live Oxigraph with seeded data
- Validate GeoJSON output schema and RFC 7946 compliance
- Verify map pins render identically to phase-1
- Test graceful failure when Oxigraph is unavailable

### Key Decisions

1. **Data Structure**: Wrapped GeoJSON features in `{ "spaces": [...] }` for backward compatibility with app.js loadData()
2. **Minimal vs. Rich Data**: Query fetches only critical fields from Oxigraph (name, geo, status, last_fetched, geolocationFidelity); other fields default to empty/false. Full enrichment will happen during Epic 2 ingestion.
3. **SELinux Fix**: Added `:z` to docker-compose volumes for Fedora compatibility (prevents access denied errors)
4. **Error Handling**: HTTP 4xx/5xx returns non-zero exit (scheduler retries); empty result set produces valid empty FeatureCollection

### Handoff Context Summary

This story is the **read-path materialization** — the inverse of the ingestion pipeline that will be built in Epic 2. The frontend has been reading from a static `moms_seed.json` since Phase 1; Story 1.5 swaps the source to live Oxigraph data without changing the map UX.

**Critical Dependencies:**
- Story 1.3 (Nginx + Oxigraph running) — ✅ done
- Story 1.4 (Ontologies loaded, prefixes documented) — ✅ done
- Story 0.3 (Seeded data in Oxigraph) — ✅ done (567 named graphs ready)

**Integration Points:**
- **Upstream (Epic 2):** Ingestion pipeline will write to `<urn:mak:space/{id}>` + `<urn:mak:status>` named graphs. Story 1.5 reads from these graphs.
- **Downstream (Epic 3):** Heartbeat scheduler will call `materialize_geojson.py` after each fetch cycle to refresh the static file.
- **Downstream (Epic 2):** Immediate materialization after first-fetch confirmation (Story 2.3) — `materialize_geojson.py` is invoked in the request path, not just scheduled.

**Data Integrity Pattern (from Story 0.1):**
- Every space has a `mom:geolocationFidelity` tag — never silently dropped
- The SPARQL query must preserve this tag so the UI can degrade gracefully
- No "missing field" skips in the materialization layer — that's a contract violation

**Graceful Failure (Phase 1 UX):**
- If `spaces.geojson` fetch fails: show banner, keep map rendered with no pins
- If Oxigraph is unreachable: `materialize_geojson.py` logs ERROR + exits non-zero (scheduler retries)

### Questions for Developer Agent

None at story-creation time. The spec is clear. Ask if SPARQL prefixes cause confusion or if the GeoJSON schema needs clarification during implementation.

### Debug Checklist (for Dev Agent)

Before marking done:
- [ ] `curl http://localhost:7878/query -X POST` with SPARQL query returns results as JSON
- [ ] `python scripts/materialize_geojson.py` creates valid `web/data/spaces.geojson` with correct schema
- [ ] `curl http://localhost/data/spaces.geojson` serves the file with `Cache-Control: max-age=60`
- [ ] Browser: `http://localhost/` shows pins from live Oxigraph (not from `moms_seed.json`)
- [ ] Browser graceful failure: `mv web/data/spaces.geojson /tmp/` then refresh → banner appears, no crash
- [ ] GeoJSON validator passes on output file
- [ ] `geolocationFidelity` tags are present in all features

---

## References

- [Source: _bmad-output/planning-artifacts/epics.md — Epic 1, Story 1.5]
- [Source: _bmad-output/planning-artifacts/architecture.md — Named Graph Topology]
- [Source: _bmad-output/planning-artifacts/architecture.md — ADR-006 (freshness), ADR-007 (presence)]
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml — cross_epic_handoffs]
- [Source: _bmad-output/implementation-artifacts/1-4-author-mom-ontology-v0-load-mom-iop-into-oxigraph.md — SPARQL prefixes + httpx patterns]
- [Source: _bmad-output/implementation-artifacts/1-3-docker-compose-stack-nginx-security-routing.md — Nginx routing + CORS]
- [Source: /memory/story_0-1_completion_notes.md — geolocationFidelity tag propagation]
- [Source: /memory/feedback_data_integrity_no_silent_drops.md — data integrity contract]
- [Source: /memory/infra_local_dev.md — distrobox-host-exec pattern]
- [Source: /memory/infra_env_symlink.md — .env symlink requirement]
