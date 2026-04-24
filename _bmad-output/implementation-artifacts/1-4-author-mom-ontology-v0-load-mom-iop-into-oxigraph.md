# Story 1.4: Author MOM Ontology v0 + Load MOM & IoP into Oxigraph

Status: ready-for-dev

## Story

As a backend developer,
I want the MOM vocabulary (Turtle) and the IoP ontology authored and loaded into dedicated Oxigraph named graphs,
so that Story 1.5 can query typed space data and the NL bot (Epic 6) has ontology context for SPARQL generation.

## Acceptance Criteria

1. `ontology/mom.ttl` exists and declares the MOM v0 vocabulary: classes `mom:Space`, `mom:Coordinator`; properties `mom:sourceUrl`, `mom:confirmedAt`, `mom:operationalState`, `mom:visibility`, `mom:geolocationFidelity`; uses `schema:name`, `schema:description`, `schema:geo` (Schema.org reuse, not redefinition); `owl:Ontology` header with `owl:versionInfo "0.1"`.
2. `ontology/iop/iop.ttl` exists — the IoP ontology file (can be a minimal stub or a downloaded copy); it declares at minimum `owl:Ontology` header identifying itself as the IoP ontology.
3. `scripts/load_ontology.sh` loads `mom.ttl` into `<urn:mak:ontology/mom>` and `iop/iop.ttl` into `<urn:mak:ontology/iop>` via Oxigraph's `/store?graph=` HTTP endpoint; script is idempotent (safe to re-run).
4. After running `load_ontology.sh` locally, `ASK { GRAPH <urn:mak:ontology/mom> { mom:Space a owl:Class } }` returns `true` against `localhost:7878`.
5. After running `load_ontology.sh` locally, `ASK { GRAPH <urn:mak:ontology/iop> { ?s a owl:Ontology } }` returns `true` against `localhost:7878`.
6. `ontology/context/space.jsonld` exists — a JSON-LD context mapping compact terms (`name`, `geo`, `sourceUrl`, etc.) to their full IRIs (used by ingestion and heartbeat tasks).
7. `make sync` includes the `ontology/` directory (Makefile rsync command covers it or ontology files land under `infra/` or are explicitly added).
8. A test `scripts/test_load_ontology.py` verifies AC #4 and AC #5 against live Oxigraph using `httpx` (not `requests`, not `SPARQLWrapper`); test is skipped gracefully if Oxigraph is unreachable (connection error → `pytest.skip`).

## Tasks / Subtasks

- [ ] Author `ontology/mom.ttl` (AC: #1)
  - [ ] `owl:Ontology` header (`owl:versionInfo "0.1"`, `rdfs:label`, base IRI `https://nicolasdb.github.io/mapsofmaking_ontology/ns#`)
  - [ ] Declare `mom:Space a owl:Class`, `mom:Coordinator a owl:Class`
  - [ ] Declare properties: `mom:sourceUrl`, `mom:confirmedAt`, `mom:operationalState`, `mom:visibility`, `mom:geolocationFidelity` — each with `rdfs:domain`, `rdfs:range`, `rdfs:comment`
  - [ ] Add `schema:` prefix declarations; annotate reused Schema.org terms with `rdfs:comment` (do NOT re-declare them as OWL properties)
  - [ ] Validate Turtle syntax locally (`rapper -i turtle` or Python `rdflib.Graph().parse`)

- [ ] Author/obtain `ontology/iop/iop.ttl` (AC: #2)
  - [ ] Create `ontology/iop/` directory
  - [ ] Minimal stub sufficient for AC #5: `owl:Ontology` triple + key IoP class/property stubs needed by Epic 6 NL bot context (see Dev Notes for IoP scope)

- [ ] Author `ontology/context/space.jsonld` (AC: #6)
  - [ ] Create `ontology/context/` directory
  - [ ] Map terms: `name` → `schema:name`, `description` → `schema:description`, `geo` → `schema:geo`, `latitude` → `schema:latitude`, `longitude` → `schema:longitude`, `sourceUrl` → `mom:sourceUrl`, `confirmedAt` → `mom:confirmedAt`, `operationalState` → `mom:operationalState`, `visibility` → `mom:visibility`, `geolocationFidelity` → `mom:geolocationFidelity`
  - [ ] Include all four MOM prefixes in `@context`

- [ ] Write `scripts/load_ontology.sh` (AC: #3)
  - [ ] Accept optional `OXIGRAPH_URL` env var (default `http://localhost:7878`)
  - [ ] Use `curl -X PUT` with `Content-Type: text/turtle` to `/store?graph=<named-graph-iri>` (Oxigraph store endpoint)
  - [ ] Load mom.ttl → `<urn:mak:ontology/mom>`, iop.ttl → `<urn:mak:ontology/iop>`
  - [ ] Exit non-zero on curl failure; echo success/failure per graph
  - [ ] Idempotent: PUT replaces graph content, safe to re-run

- [ ] Write `scripts/test_load_ontology.py` (AC: #8)
  - [ ] Use `httpx` (already in `scripts/requirements.txt` from Story 0.x — verify, add if missing)
  - [ ] Two test functions: one for AC #4 ASK, one for AC #5 ASK
  - [ ] Graceful skip on `httpx.ConnectError` with `pytest.skip("Oxigraph unreachable")`
  - [ ] Use SPARQL ASK via POST to `/query` with `Content-Type: application/sparql-query` and `Accept: application/sparql-results+json`
  - [ ] Include required SPARQL prefixes in every query (see Dev Notes — critical!)

- [ ] Verify Makefile sync covers `ontology/` (AC: #7)
  - [ ] Check current `rsync` command in Makefile; if `ontology/` not covered, add it to the sync target alongside `web infra data`

- [ ] Local integration verification (AC: #4, #5)
  - [ ] Start Oxigraph: `distrobox-host-exec podman compose -f infra/docker-compose.yml up -d oxigraph`
  - [ ] Run `bash scripts/load_ontology.sh`
  - [ ] Run `python -m pytest scripts/test_load_ontology.py -v`

## Dev Notes

### SPARQL Prefixes — CRITICAL (never omit)

Every SPARQL query must include these PREFIX declarations. Oxigraph returns HTTP 400 without them:

```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX mak: <https://nicolasdb.github.io/mapsofmaking_ontology/resource/>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
```

The test file's ASK queries must include `PREFIX owl:` and `PREFIX mom:`.

### Oxigraph HTTP API

- **Load graph**: `PUT /store?graph=<iri>` with body = Turtle content, `Content-Type: text/turtle`
  - PUT is idempotent — replaces entire graph
- **SPARQL query**: `POST /query`, `Content-Type: application/sparql-query`, `Accept: application/sparql-results+json`
- Local endpoint: `http://localhost:7878` (Oxigraph container, port exposed from compose)
- Live data: 567 named graphs already loaded (566 VOW + 1 RFF mock) — this story adds 2 ontology graphs

### HTTP Client

Use `httpx` only — never `requests`, never `SPARQLWrapper`. Pattern from existing `scripts/test_seed_import.py`:

```python
import httpx

def sparql_ask(query: str, endpoint: str = "http://localhost:7878") -> bool:
    r = httpx.post(f"{endpoint}/query", content=query,
                   headers={"Content-Type": "application/sparql-query",
                            "Accept": "application/sparql-results+json"})
    r.raise_for_status()
    return r.json()["boolean"]
```

### MOM Ontology v0 Scope

MOM (Maps of Making vocabulary) is a **minimal application vocabulary** — not a standalone ontology. It extends Schema.org rather than duplicating it:

- Reuse `schema:name`, `schema:description`, `schema:geo`, `schema:latitude`, `schema:longitude` directly — declare in `@prefix` only, no OWL class/property declarations for Schema.org terms
- MOM-specific additions only: `mom:Space`, `mom:Coordinator`, and properties not in Schema.org (`mom:sourceUrl`, `mom:confirmedAt`, `mom:operationalState`, `mom:visibility`, `mom:geolocationFidelity`)
- `mom:geolocationFidelity` values: `"exact"`, `"approximate"`, `"city"`, `"country"` (from Story 0.1 pattern — propagate this tag)
- `mom:operationalState` values (from ADR-006): `seeded`, `aging`, `zombie`, `dead` (freshness lifecycle)
- `mom:visibility` values: `public`, `hidden` (from ADR-006)

Named graph for MOM: `<urn:mak:ontology/mom>` (architecture spec — do not change)

### IoP Ontology Scope

IoP = "Internet of Places" — the broader ontology context for the NL bot (Epic 6). For this story:
- A **minimal stub** is sufficient for AC #5 (one `owl:Ontology` triple)
- Full IoP content is not needed until Story 6.1 (NL→SPARQL task)
- The stub should declare the base IRI and a placeholder comment noting it will be expanded in Epic 6
- Named graph: `<urn:mak:ontology/iop>` (architecture spec)

### File Locations

```
maps_of_making/
├── ontology/
│   ├── mom.ttl                    ← MOM vocabulary (AC #1)
│   ├── iop/
│   │   └── iop.ttl               ← IoP ontology stub (AC #2)
│   └── context/
│       └── space.jsonld          ← JSON-LD context (AC #6)
├── scripts/
│   ├── load_ontology.sh          ← Load script (AC #3)
│   └── test_load_ontology.py     ← Integration test (AC #8)
```

These paths match the architecture document's project structure spec exactly.

### Python venv

VENV is managed externally by the user — never create `scripts/venv` or `harness/venv`. Activate with `source venv/bin/activate` before running Python. The `scripts/requirements.txt` already includes `httpx` (verify before adding again).

### Local Dev — Start Oxigraph

```bash
distrobox-host-exec podman compose -f infra/docker-compose.yml up -d oxigraph
```

(from project root, within distrobox — `distrobox-host-exec` reaches the host Podman daemon)

### Naming Conventions (AR-CONV1–5)

- Named graphs: `urn:mak:{type}/{id}` pattern — already defined in architecture
- Python: `snake_case` functions, `async def verb_noun()` for async
- Turtle: follow standard prefix casing — `mom:camelCase` properties, `mom:PascalCase` classes
- Shell scripts: exit non-zero on error (`set -e` or explicit `|| exit 1`)

### Makefile rsync target (AC #7)

Current `sync-app` target syncs `web infra data`. Add `ontology` to the list:
```makefile
sync-app:
    rsync -avz --delete $(RSYNC_EXCLUDE) \
        web infra data ontology \
        $(REMOTE):$(REMOTE_APP)/
```
Verify the RSYNC_EXCLUDE list doesn't inadvertently exclude `.ttl` or `.jsonld` files.

### Story 1.3 Context

Previous story (1.3) delivered:
- `infra/docker-compose.yml` with `maps_of_making_internal` network
- Oxigraph runs as `maps-oxigraph` service, expose port 7878 internally
- Nginx routes `/sparql/query` → oxigraph (CORS headers set), `/sparql/update` → 403
- `.env.example` documents all env vars

No changes needed to compose or nginx for this story.

### What Story 1.5 Needs From This Story

1.5 (GeoJSON materialization) will SPARQL-query typed `mom:Space` instances. The MOM ontology in `<urn:mak:ontology/mom>` lets it construct typed queries and the `space.jsonld` context supports JSON-LD framing of results. Ensure AC #4 passes before marking this story done.

### References

- [Source: _bmad-output/planning-artifacts/architecture.md — Named Graph Topology]
- [Source: _bmad-output/planning-artifacts/architecture.md — Project Directory Structure]
- [Source: _bmad-output/planning-artifacts/architecture.md — ADR-006 (freshness), ADR-007 (presence graph)]
- [Source: _bmad-output/planning-artifacts/architecture.md — AR-CONV1–5 (naming conventions)]
- [Source: _bmad-output/planning-artifacts/epics.md — Epic 1, Story 1.4]
- [Source: _bmad-output/implementation-artifacts/sprint-status.yaml — cross_epic_handoffs]
- [Source: _bmad-output/implementation-artifacts/1-3-docker-compose-stack-nginx-security-routing.md — compose topology]

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
