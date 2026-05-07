# Data Lifecycle: Seed → Registration → Heartbeat → Storage → Display

*Design artifact — produced 2026-04-26. Last refreshed 2026-05-07 (added Heartbeat phase, Persistence & Reset section, Network-as-Directory pattern).*

---

## Sequence Diagram

```mermaid
sequenceDiagram
    participant VOW as VOW / RFF source
    participant seed as seed_import.py
    participant coord as Coordinator endpoint<br/>(JSON-LD URL)
    participant handler as link_handler<br/>POST /api/register-url
    participant ox as Oxigraph<br/>(named graphs)
    participant mat as materialize_geojson.py<br/>(make publish)
    participant geojson as spaces.geojson<br/>(static file)
    participant app as app.js<br/>(browser)
    participant api as link_handler<br/>GET /api/space/{id}/snapshots

    rect rgba(40, 60, 80, 0.2)
        Note over VOW,ox: Phase 1 — Seed (Epic 1, done)
        VOW->>seed: vow_workshops.json / rff mockup
        seed->>ox: INSERT to urn:mak:space/{slug}<br/>name, geo, address, url, profileUrl,<br/>knowsAbout, source="scraped-vow",<br/>operationalState="seeded"
    end

    rect rgba(50, 70, 50, 0.2)
        Note over coord,ox: Phase 2 — Registration (Story 2.1, done)
        coord-->>handler: GET {url} → JSON-LD payload
        handler->>handler: validate (name + geo required)<br/>PII check (foaf:mbox blocked)
        handler->>ox: DROP SILENT + INSERT to urn:mak:space/{slug}<br/>name, geo, endpointUrl, lastFetched,<br/>source="self-registered", operationalState="confirmed"<br/>+ optional: address*, url, description, openingHours
        handler->>ox: INSERT snapshot graph<br/>urn:mak:space/{slug}/{YYYY-MM-DD}<br/>snapshotDate, snapshotSummary, lastHttpStatus
        Note over handler,ox: * address written as mom:address string,<br/>not schema:streetAddress — gap, see table below
    end

    rect rgba(80, 70, 40, 0.2)
        Note over coord,ox: Phase 2.5 — Heartbeat (Epic 3, done — Stories 3.0/3.1/3.2/3.2b)
        loop every 10 min (APScheduler in link-handler) or on POST /api/heartbeat/run
            handler->>coord: GET endpointUrl (conditional: ETag / If-Modified-Since)
            coord-->>handler: 200 + JSON-LD / SpaceAPI  •or•  304 Not Modified  •or•  error
            handler->>handler: transform SpaceAPI→JSON-LD (Story 3.0), diff vs prior snapshot,<br/>compute endpoint_health (mins), lifecycle_state (days), open_now,<br/>resolve effective_marker, strip PII on closed (Story 3.2b)
            handler->>ox: SPARQL UPDATE — operationalState, lastFetched,<br/>endpoint_health, lifecycle_state, raw source JSON snapshot
            handler->>geojson: rematerialize spaces.geojson when state changed
        end
        Note over handler: heartbeat state (ETag, failure counter, last health/lifecycle)<br/>persisted in /app/tasks/heartbeat_log.db (SQLite, bind-mounted since 2026-05-07)
    end

    rect rgba(70, 50, 50, 0.2)
        Note over ox,geojson: Phase 3 — Materialization (heartbeat-driven; manual via make heartbeat)
        mat->>ox: SPARQL SELECT (both UNION branches)
        ox-->>mat: bindings (see gap table)
        mat->>geojson: binding_to_space() → GeoJSON features<br/>⚠ opening_hours, contact, description,<br/>endpointUrl, lastFetched hardcoded "" (Story 2.2 fixes some)
    end

    rect rgba(60, 50, 80, 0.2)
        Note over geojson,app: Phase 4 — Display (browser)
        app->>geojson: fetch /data/spaces.geojson
        geojson-->>app: features → state.spaces
        app->>app: renderDetail(s) → drawer card
        app->>api: GET /api/space/{s.id}/snapshots (async, Story 2.2)
        api->>ox: SPARQL SELECT snapshot graphs
        ox-->>api: [{date, summary, http_status}]
        api-->>app: JSON array → history section
    end
```

---

## Field Mapping Table

*Columns: what field, where it comes from in JSON-LD, what predicate lands in Oxigraph, whether materialize reads it, what GeoJSON property it becomes, what the card shows, and the gap.*

| Field | Coordinator JSON-LD key | mom/schema predicate in Oxigraph | materialize reads? | GeoJSON property | Card label | Gap / Story |
|---|---|---|---|---|---|---|
| **Name** | `schema:name` | `schema:name` | ✅ | `name` | Header | — |
| **Latitude / Longitude** | `schema:geo.schema:latitude` / `longitude` | `schema:geo [schema:latitude ; schema:longitude]` | ✅ | `coordinates` | Pin position | — |
| **Street address** | `schema:address.schema:streetAddress` | `schema:streetAddress` (seed only) | ✅ (seed) | `address` | Address line | ⚠ register-url writes `mom:address` string, materialize reads `schema:streetAddress` → **confirmed spaces lose address** |
| **City / Country** | `schema:address.schema:addressLocality/Country` | `schema:addressLocality` / `schema:addressCountry` | ✅ (seed) | `city`, `country` | Address / filter | Same gap as above |
| **Website** | `schema:url` | `schema:url` | ✅ | `website` | not shown directly | — |
| **VOW profile link** | *(from VOW scrape)* | `mom:profileUrl` | ✅ → used as `endpoint_url` fallback | `endpoint_url` | Provenance URL (2.2) | — |
| **Endpoint URL** | *(req.url, not JSON-LD field)* | `mom:endpointUrl` | ❌ not yet | `endpoint_url=""` | Provenance URL empty | **Story 2.2 Task 3** |
| **Last fetched** | *(generated at write time)* | `mom:lastFetched` | ❌ not yet | `last_fetched=""` | Freshness line blank | **Story 2.2 Task 3** |
| **Error type** | *(future: set by scheduler)* | `mom:errorType` | ❌ not yet | `error_type=""` | Error banner | **Story 2.2 Task 3** (field added; value populated by Epic 3 scheduler) |
| **Operational state** | *(set by handler)* | `mom:operationalState` | ✅ | `status` | Pin colour, freshness | — |
| **Source** | *(set by handler)* | `mom:source` | ✅ | `source` | Provenance label (2.2) | — |
| **Specialties (seed)** | *(from VOW tags)* | `schema:knowsAbout` | ✅ | `specialties` | Chips | — |
| **Specialties (coordinator)** | `schema:knowsAbout` | ❌ register-url does not write | — | `specialties=[]` | Chips empty | **Epic 3** (full ingestion) |
| **Description** | `schema:description` | `schema:description` | ❌ not read | — | (not shown) | **Story 2.2 deferred note → Epic 3** |
| **Opening hours** | `schema:openingHours` | `schema:openingHours` | ❌ not read | `opening_hours=""` | Hours row blank | **Epic 3** |
| **Founded** | *(not in current spec)* | ❌ not written | — | `founded=""` | Founded row blank | **Epic 3** |
| **Capacity** | *(not in current spec)* | ❌ not written | — | `capacity=0` | Capacity row blank | **Epic 3** |
| **Contact** | *(not in current spec)* | ❌ not written | — | `contact=""` | Contact row blank | **Epic 3** |
| **Network memberships** | *(not in current spec)* | ❌ not written | — | `network_memberships=[]` | Badges blank | **Epic 3** |
| **Open for hosting** | *(not in current spec)* | ❌ not written | — | `open_for_hosting=false` | Badge blank | **Epic 3** |
| **Snapshot history** | *(generated at write time)* | `mom:snapshotDate` / `snapshotSummary` / `lastHttpStatus` | via API not GeoJSON | — | History section (2.2 AC4) | **Story 2.2 Task 1+2** |
| **Geolocation fidelity** | *(geocoder output)* | `mom:geolocationFidelity` | ✅ | `geolocationFidelity` | (internal) | — |

---

## Summary: what Story 2.2 fixes vs what is Epic 3

**Story 2.2 fixes (read-back from Oxigraph):**
- `mom:endpointUrl` → `endpoint_url` (replaces profileUrl fallback for confirmed spaces)
- `mom:lastFetched` → `last_fetched` (enables freshness line for confirmed spaces)
- `mom:errorType` → `error_type` (field added; value populated by Epic 3 scheduler)
- Snapshot named graph: written by amended register-url, queried by new snapshots API

**Confirmed address gap (not in Story 2.2 scope):**
Register-url writes `mom:address` as a flat string; materialize reads `schema:streetAddress` etc. Confirmed spaces will inherit their seeded address (the DROP SILENT + INSERT overwrites the graph, discarding seeded address triples). This needs either: (a) register-url to write structured `schema:streetAddress` triples, or (b) materialize to also read `mom:address` as fallback. → Tag for **Story 2.3 or Epic 3**.

**Everything else (opening hours, specialties from coordinator, contact, etc.):**
Requires Epic 3's periodic fetch-and-update cycle, where the scheduler re-fetches the coordinator endpoint and writes a full set of triples — not just the registration minimum.

---

## Persistence & Reset

### Storage map — where each piece of data physically lives

| Data | Location | Container that writes it | Survives restart? | Wiped by |
|---|---|---|---|---|
| Triplestore (named graphs — all spaces, snapshots, ontology) | `data/oxigraph/` (host bind mount) | maps-oxigraph | ✅ yes (bind mount) | `rm -rf data/oxigraph/*`; SPARQL `CLEAR/DROP` |
| Heartbeat state (ETag, Last-Modified, consecutive_failures, last endpoint_health, last lifecycle_state, prior snapshot for diffing) | `data/tasks/heartbeat_log.db` (host bind mount, since 2026-05-07) | maps-link-handler | ✅ yes (bind mount) | `rm -f data/tasks/heartbeat_log.db` |
| Materialized GeoJSON (what the browser reads) | `web/data/spaces.geojson` (host bind mount) | maps-link-handler regenerates on heartbeat | ✅ yes; regenerated on every materialize | next heartbeat overwrites it |
| Static seed JSON (VOW + RFF) | `web/data/moms_seed.json`, `web/data/rff_mockup.json` | host-only, mounted read-only | ✅ yes | git operations only |
| Container images / build cache | podman/docker storage | n/a | ✅ yes | `make rebuild` rebuilds; `podman system prune` clears |

`podman compose down` / `up` stops and starts containers. **It does not touch any of the bind-mounted state above.** Only explicit `rm` (or SPARQL `DROP`) wipes data.

### `make seed --force` semantics

- Walks each VOW entry: writes `urn:mak:space/{slug}` only if the graph does not yet exist (idempotent — VOW data is never overwritten).
- For RFF: if the shared `urn:mak:mock/rff-health` graph already exists, `--force` does `CLEAR GRAPH` then re-inserts. Without `--force`, RFF is skipped.
- **Coordinator-registered spaces are never cleared by seed** — they live in `urn:mak:space/{slug}` graphs with `mom:source = "self-registered"`, and seed only writes graphs whose source is `scraped-vow` or `mock-rff`.
- The same protection applies to `seed_spaceapi.py`: it skips graphs whose `mom:source` is `self-registered`, even with `--force`.

### Reset procedure (local) — `make reset`

`make reset` is the only supported way to fully wipe local state. It:

1. Prompts for typed confirmation (`reset`).
2. Stops the compose stack.
3. `rm -rf data/oxigraph/*` and `rm -f data/tasks/heartbeat_log.db`.
4. Runs `make devdeploy` (rebuild + seed + heartbeat).

**This loses all coordinator-registered spaces.** Acceptable for demo prep. If you need to preserve them, manually `cp -r data/oxigraph data/oxigraph.bak` first.

### Reset procedure (VPS) — intentionally manual

There is **no `make reset` equivalent for the VPS**. Production safety: any wipe must be deliberate, on-host, and witnessed. Procedure:

```bash
ssh hetzner
cd ~/maps_of_making
docker compose -f infra/docker-compose.yml down
sudo rm -rf data/oxigraph/* data/tasks/heartbeat_log.db
docker compose -f infra/docker-compose.yml up -d --build
# from local:
make vps-seed         # reseed VOW+RFF + trigger heartbeat
```

Pilot-time: this needs a backup story before we onboard real coordinators.

---

## Network-as-Directory pattern

SpaceAPI exposes its membership via a single URL (`https://directory.spaceapi.io/`) listing all member endpoints. MoM ingests that URL once and gets ~244 verified spaces (`scripts/seed_spaceapi.py`, tagged `mom:memberOf <urn:mak:network/spaceapi>` → "SPACEAPI" filter chip).

This is a battle-tested federation pattern and fits the MoM model directly:

- **The network is the gatekeeper of its members.** They control add/remove. We get verified, maintained membership for free.
- **Open and reciprocal.** Any network can publish such a directory; any aggregator can consume it.
- **Acceleration vs single-URL onboarding.** One URL → N spaces, instead of N coordinator-by-coordinator registrations.

VOW, RFF, FabLabs.io, and other federations could each expose an equivalent directory. The current single-URL coordinator flow (Story 2.1) and the directory flow (`seed_spaceapi.py`) are both valid registration modes. **Pilot decision:** whether to formalize "network-directory coordinator" as a first-class registration mode in the link-handler (alongside the single-URL flow), or keep it as a seed-time-only pattern.

Status: demonstrated in the demo. Hardening (auth, signed directories, conflict resolution when two networks claim the same endpoint) deferred to Pilot.

---

## Admin Dashboard: what needs to be visible

The side-by-side view maps directly to the lifecycle columns above:

| Column | Source | What it shows |
|---|---|---|
| **Seed data** | Oxigraph seeded graph (`urn:mak:space/{slug}`) | Name, address, VOW profile URL, specialties, geo fidelity |
| **URL data** | Live fetch of `mom:endpointUrl` at query time (or last cached in snapshot) | Raw JSON-LD from coordinator endpoint |
| **Stored data** | Oxigraph confirmed graph (all predicates) | All triples for this space — what landed after ingestion |
| **Viewed data** | GeoJSON feature for this space | Exactly what the map card renders — the end result |

Gaps become visible as: field present in URL data but absent or stale in Stored / Viewed columns.

Snapshot history provides the "ingestion progress" timeline per space.
