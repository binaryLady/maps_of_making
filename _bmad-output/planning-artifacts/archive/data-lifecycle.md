# Data Lifecycle — Maps of Making

*Redrawn 2026-05-17 (Story 3.4b clean-slate pivot). Replaces the 2026-04-26 sequence diagram.*

---

## Flow Diagram

```mermaid
flowchart TD

    subgraph canary_path ["Canary path (Story 3.4b)"]
        baseline["data/canary/baseline.json\ncommitted, version-controlled"]
        served["web/canary/mother-sands.json\nsingle source of truth"]
        scenarios["make cb-* / cc-* / ca-*\ncanary_scenarios.py"]

        baseline -->|make c-reset| served
        scenarios -->|direct write| served
    end

    subgraph vps_static ["VPS static (nginx)"]
        vps_endpoint["mapsofmaking.org/canary/mother-sands.json"]
    end

    served -->|make endpoint · rsync| vps_endpoint
    served -->|python scripts/load_canary.py\nmanual bootstrap only| ox_canary

    subgraph registration ["Coordinator registration (Story 2.1)"]
        reg_url["POST /api/register-url\nSpaceAPI or JSON-LD URL"]
        pydantic["SpaceAPISchema\npydantic gate\nlink_handler/main.py"]
        reg_url --> pydantic
    end

    subgraph heartbeat_loop ["Heartbeat loop (Epic 3 · routing: Story 3.5)"]
        scheduler["APScheduler 10 min\nPOST /api/heartbeat/run"]
        fetch["fetch endpointUrl\nconditional GET ETag"]
        router{"ext_mom.canary\ntrue / false·missing"}
        scheduler --> fetch --> router
    end

    fetch -.->|reads endpointUrl\nfrom Oxigraph| ox_space
    fetch -.->|reads endpointUrl\nfrom Oxigraph - Story 3.5| ox_canary

    router -->|true → Story 3.5\nbuild_canary_sparql| ox_canary
    router -->|false · missing\ntransformer.py| ox_space

    subgraph oxigraph ["Oxigraph named graphs"]
        ox_onto["urn:mak:ontology/mom\nurn:mak:ontology/iop\nload_ontology.sh"]
        ox_canary["urn:mak:canary\nMother Sands diagnostic\nDROP+INSERT"]
        ox_space["urn:mak:space/{slug}\nregistered spaces\nheartbeat · DROP+INSERT"]
        ox_ledger["urn:mak:public_ledger\nreserved · TBD IPFS-IPLD\nappend-only · never DROP"]
    end

    pydantic -->|INSERT| ox_space

    subgraph materialization ["Materialization"]
        sparql_select["SPARQL SELECT\nUNION both branches\nmain.py · materialize_geojson.py"]
        geojson["web/data/spaces.geojson"]
        sparql_select --> geojson
    end

    ox_onto --> sparql_select
    ox_canary --> sparql_select
    ox_space --> sparql_select

    geojson -->|fetch /data/spaces.geojson| map["Browser map\napp.js · MapLibre"]
```

---

## Named graphs — mutation rules

| Graph | Writer | Rule |
|---|---|---|
| `urn:mak:ontology/*` | `scripts/load_ontology.sh` | Replace on schema change only |
| `urn:mak:canary` | `scripts/load_canary.py` | DROP + INSERT (mutable, controlled) |
| `urn:mak:space/{slug}` | heartbeat `transformer.py` | DROP + INSERT each cycle |
| `urn:mak:public_ledger` | TBD (Story 3.5+) | Append-only — **never DROP** |

---

## Canary scenario cycle

```
make cb-zombie          →  writes web/canary/mother-sands.json
                        →  make endpoint (rsync to VPS)
                        →  make heartbeat (space/* loop — does NOT update urn:mak:canary)

python scripts/load_canary.py   →  syncs urn:mak:canary from served file
make c-report           →  coherence check: endpoint · heartbeat_log · Oxigraph · GeoJSON
```

> **Current state (3.4b):** The heartbeat loop processes `urn:mak:space/*` only. `urn:mak:canary` is updated manually via `load_canary.py` (bootstrap / scenario sync). Axis B and C are exercised. Axis A (endpoint reachability) is not yet live.
>
> **Intended state (Story 3.5):** The heartbeat also holds `mom:endpointUrl` for `urn:mak:canary`. On fetch, if the returned JSON contains `ext_mom.canary: true`, the heartbeat routes to `build_canary_sparql()` → `urn:mak:canary`. If false or missing, it routes to `transformer.py` → `urn:mak:space/{slug}`. This makes Axis A live and closes the coherence loop. The same routing pattern is reserved for `urn:mak:public_ledger` (different write contract — append-only, never DROP).

---

## Epic 3.5 — clean snapshot pipeline (transition state)

*Added 2026-05-19 (`sprint-change-proposal-2026-05-19.md`).*

Epic 3.5 re-architects the freshness path around the **snapshot as the unit of truth**: a
successful fetch produces one snapshot — `{JSON payload + observed_at + space UID}` — from which
every lifecycle fact is derived, never independently stamped. `observed_at` (UTC instant of a
successful fetch) is minted once and carried byte-identical to the browser, which computes
`age = now − observed_at`.

During the transition **two pipelines run side by side**:

| | Legacy pipeline | Clean snapshot pipeline |
|---|---|---|
| Serves | Registered spaces (`urn:mak:space/*`) | Mother Sands canary (`urn:mak:canary`) |
| Fetch store | `heartbeat_log.db` (noisy — derived columns) | New clean snapshot store, keyed by UID |
| Transform | `transformer.py` `_build_sparql_update` (fat) | Clean transform — copies `observed_at`, no re-stamp |
| GeoJSON | Full-payload feature | Minimal feature — geoloc + UID + `observed_at` |
| Built / owned by | Epic 3 | Story 3.6 (built), 3.7–3.10 (migration) |

Story 3.6 builds the clean pipeline canary-only, leaving the legacy path untouched (zero
regression risk). Stories 3.7–3.10 migrate registered spaces onto the clean path seam by seam
and **delete** the legacy `heartbeat_log` noise columns and transform-time stamping wholesale.
End state: one pipeline, the clean one.

---

## What is deferred

| Item | Target |
|---|---|
| Heartbeat routing on `ext_mom.canary` → `urn:mak:canary` (Axis A live) | Story 3.5 |
| Three-layer schema formalization (SpaceAPI core / mom: extended / community) | Story 3.5 |
| Heartbeat transformer rewrite on clean schema | Story 3.5 |
| EU-spaces reintroduction (20 filtered from SpaceAPI directory) | Story 3.5+ |
| GeoJSON payload-slimming for registered spaces (render-critical fields only) | Story 3.9 |
| Heartbeat routing on `ext_mom.public_ledger` → append-only write | Post-3.5 |
| `urn:mak:public_ledger` minting (IPFS-IPLD dag-json) | Epic 4+ |
| Full SpaceAPI directory (~244 spaces) | Post-pilot |
