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
    served -->|python scripts/load_canary.py| ox_canary

    subgraph registration ["Coordinator registration (Story 2.1)"]
        reg_url["POST /api/register-url\nSpaceAPI or JSON-LD URL"]
        pydantic["SpaceAPISchema\npydantic gate\nlink_handler/main.py"]
        reg_url --> pydantic
    end

    subgraph heartbeat_loop ["Heartbeat loop (Epic 3)"]
        scheduler["APScheduler 10 min\nPOST /api/heartbeat/run"]
        fetch["fetch endpointUrl\nconditional GET ETag"]
        transformer["transformer.py\nSpaceAPI → RDF triples"]
        scheduler --> fetch --> transformer
    end

    fetch -.->|reads endpointUrl\nfrom urn:mak:space| ox_space

    subgraph oxigraph ["Oxigraph named graphs"]
        ox_onto["urn:mak:ontology/mom\nurn:mak:ontology/iop\nload_ontology.sh"]
        ox_canary["urn:mak:canary\nMother Sands diagnostic\nload_canary.py · DROP+INSERT"]
        ox_space["urn:mak:space/{slug}\nregistered spaces\nheartbeat · DROP+INSERT"]
        ox_ledger["urn:mak:public_ledger\nreserved · TBD IPFS-IPLD\nappend-only · never DROP"]
    end

    pydantic -->|INSERT| ox_space
    transformer -->|DROP+INSERT| ox_space

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

> **Note:** The heartbeat loop processes `urn:mak:space/*` only. The canary graph (`urn:mak:canary`) is updated exclusively via `load_canary.py`. This is intentional — the canary is a controlled diagnostic instrument, not a live-fetched endpoint.

---

## What is deferred

| Item | Target |
|---|---|
| Three-layer schema formalization (SpaceAPI core / mom: extended / community) | Story 3.5 |
| Heartbeat transformer rewrite on clean schema | Story 3.5 |
| EU-spaces reintroduction (20 filtered from SpaceAPI directory) | Story 3.5+ |
| `urn:mak:public_ledger` minting (IPFS-IPLD dag-json) | Epic 4+ |
| Full SpaceAPI directory (~244 spaces) | Post-pilot |
