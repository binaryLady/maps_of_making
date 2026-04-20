# Architecture: Maps of Making — Linked Open Data Stack

> **Version:** 2.0 (LOD Pivot)  
> **Date:** April 2026  
> **Status:** Design — pre-implementation  
> **Supersedes:** v1.0 (Neo4j/IPFS stack, Nov 2025)

---

## 1. Executive Summary

Maps of Making is federated infrastructure for the global maker ecosystem. The architecture is built on W3C Linked Open Data standards throughout — making the data natively interoperable rather than requiring a proprietary adapter layer.

**The core data flow:**

```
Spaces publish one JSON-LD file at a URL they control
         ↓
Heartbeat agent (nanoclaw/openclaw) monitors those URLs for diffs
         ↓
Changes are ingested into Oxigraph (RDF triplestore, SPARQL endpoint)
         ↓
Queries arrive from web app or channel bots
         ↓
LLM harness translates natural language → SPARQL → structured answer
```

**Why this stack:**
- **Oxigraph** is a pure W3C-compliant RDF store with a built-in SPARQL 1.1 endpoint. No proprietary query language — SPARQL is the standard.
- **JSON-LD** gives spaces a familiar JSON format that is simultaneously valid RDF. Zero friction for space operators.
- **nanoclaw / openclaw** is a lightweight LLM harness designed for constrained agentic tasks — ideal for NL→SPARQL translation and heartbeat diff logic without requiring large models.
- **Channel bots** bring queries where communities already talk, eliminating the "new tab" problem.

---

## 2. System Architecture

### 2.1 Components

```
┌─────────────────────────────────────────────────────────────┐
│                      SPACE LAYER                            │
│  Each space controls one file at a public URL               │
│  Format: JSON-LD (or Turtle) — W3C Linked Data              │
│  Hosted anywhere: website, GitHub, Nextcloud, VPS           │
└─────────────────────┬───────────────────────────────────────┘
                      │  HTTP GET (periodic)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   HEARTBEAT AGENT                           │
│  nanoclaw/openclaw LLM harness                              │
│  - Fetches registered URLs on schedule                      │
│  - Diffs content against stored version                     │
│  - Extracts changed fields                                  │
│  - Writes diff events to Oxigraph                          │
│  - Updates freshness status (⚪🔵⚠️🧟💀)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │  RDF triples (SPARQL UPDATE)
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     OXIGRAPH                                │
│  W3C RDF triplestore                                        │
│  - SPARQL 1.1 endpoint (query + update)                     │
│  - Named graphs per space (provenance)                      │
│  - Freshness metadata as RDF properties                     │
│  - Full history via named graph versioning                  │
└────────────┬──────────────────┬──────────────────────────────┘
             │                  │
             ▼                  ▼
┌────────────────────┐  ┌────────────────────────────────────┐
│    WEB MAP APP     │  │         CHANNEL BOTS               │
│  Leaflet/OpenLayers│  │  Mattermost, Matrix, Telegram      │
│  SPARQL → GeoJSON  │  │  NL query → LLM harness → SPARQL  │
│  Embed widget      │  │  → structured answer → post back   │
└────────────────────┘  └────────────────────────────────────┘
```

### 2.2 Data Model

**Space endpoint file (JSON-LD minimum viable)**

```json
{
  "@context": "https://mapsofmaking.org/context/space.jsonld",
  "@type": "MakerSpace",
  "@id": "https://fablab-example.org/space.jsonld",
  "name": "FabLab Ooo",
  "address": "12 Sugar Plum Street, Land of Ooo",
  "geo": {"@type": "GeoCoordinates", "latitude": 50.85, "longitude": 4.35},
  "url": "https://fablab-example.org",
  "email": "hello@fablab-example.org",
  "status": "open",
  "openingHours": "Mo-Fr 14:00-20:00",
  "amenityFeature": ["woodworking", "electronics", "laser-cutting"],
  "memberOf": ["https://rff.fr/network.jsonld", "https://vulca.eu/network.jsonld"],
  "dateModified": "2026-04-15"
}
```

**RDF Graph schema in Oxigraph**

Core classes and properties align with Schema.org + custom MOM vocabulary:

| Subject | Predicate | Object |
|---------|-----------|--------|
| `mom:space/fablab-ooo` | `rdf:type` | `schema:LocalBusiness` |
| `mom:space/fablab-ooo` | `schema:name` | `"FabLab Ooo"` |
| `mom:space/fablab-ooo` | `schema:geo` | `[lat, lon]` |
| `mom:space/fablab-ooo` | `mom:status` | `mom:StatusOpen` |
| `mom:space/fablab-ooo` | `mom:freshness` | `mom:FreshnessConfirmed` |
| `mom:space/fablab-ooo` | `mom:endpointUrl` | `"https://fablab-example.org/space.jsonld"` |
| `mom:space/fablab-ooo` | `mom:lastHeartbeat` | `"2026-04-20T08:00:00Z"` |
| `mom:space/fablab-ooo` | `mom:memberOf` | `mom:network/rff` |

Named graphs: `mom:graph/space/fablab-ooo/2026-04-20` — enables temporal queries.

---

## 3. Technology Stack

| Layer | Technology | Rationale |
|-------|-----------|-----------|
| **Triplestore** | [Oxigraph](https://oxigraph.org) | Pure Rust, W3C SPARQL 1.1, embedded or server mode, no JVM overhead |
| **Data format** | JSON-LD / Turtle | W3C standard; JSON-LD readable by spaces without RDF knowledge |
| **LLM harness** | nanoclaw / openclaw | Lightweight agent framework for constrained NL→SPARQL tasks |
| **Scraping (bootstrap)** | Python + BeautifulSoup4 + Mistral | Already working (scraped/ pipeline) |
| **Map frontend** | Leaflet + OpenLayers | Open source, embeddable widget support |
| **Bot integration** | Mattermost / Matrix webhooks | Where pilot communities already talk |
| **Schema vocabulary** | Schema.org + custom MOM ontology | Maximum interoperability |
| **Query language** | SPARQL 1.1 | W3C standard, works natively with Oxigraph |

### ADR-001: Oxigraph replaces Neo4j

**Decision:** Use Oxigraph (RDF/SPARQL) instead of Neo4j (graph/Cypher).

**Rationale:**
- Neo4j uses Cypher (proprietary). Oxigraph uses SPARQL (W3C standard).
- RDF triples are natively interoperable with any LOD tool — no adapter needed.
- Oxigraph is embeddable (Rust library) or runs as standalone HTTP server with SPARQL endpoint.
- Named graphs give provenance and temporal versioning natively.
- No GPL license constraint (Oxigraph is MIT/Apache 2.0).

**Trade-off:** SPARQL is more verbose than Cypher for deep graph traversals. Mitigated by the NL→SPARQL layer which generates queries automatically.

### ADR-002: nanoclaw / openclaw as LLM harness

**Decision:** Use nanoclaw or openclaw as the LLM harness for agent tasks.

**Rationale:**
- Heartbeat diff and NL→SPARQL are **constrained, repeatable tasks** — not open-ended reasoning.
- A lightweight harness keeps the LLM surface minimal and auditable.
- Avoids LangChain/LlamaIndex complexity for what amounts to: prompt → structured output → SPARQL string.
- Can run locally (no API cost for heartbeat monitoring).

**Tasks handled by LLM harness:**
1. **Heartbeat diff interpretation**: "These two versions of a space file changed — what fields changed, are they significant?"
2. **NL→SPARQL translation**: "Convert this natural language question to a valid SPARQL query against our ontology."
3. **Answer formatting**: "Here is the SPARQL result — format it for a chat message."

### ADR-003: JSON-LD as the space endpoint format

**Decision:** Space endpoint files use JSON-LD as the primary format (Turtle as alternative).

**Rationale:**
- JSON-LD looks like regular JSON to space operators who have never heard of RDF.
- It is valid RDF and can be ingested directly into Oxigraph.
- A published `@context` file (mapsofmaking.org) provides the shared vocabulary.
- Compatible with SpaceAPI spirit — one file, one URL, you control it.

---

## 4. Heartbeat System

The heartbeat agent is the core innovation. It operationalises the "freshness" concept:

```
Registered URLs (stored in Oxigraph)
    ↓ (cron, e.g. daily)
Fetch current file content
    ↓
Hash compare with stored version
    ↓ (if changed)
LLM diff: extract changed fields, classify significance
    ↓
SPARQL UPDATE: write new triples, update mom:lastHeartbeat
    ↓
Update freshness status:
  - Endpoint responds + content changed < 30 days:  🔵 Fresh (Confirmed)
  - No content change 30-90 days:                   ⚠️  Aging
  - No response or timeout 90-180 days:             🧟 Zombie
  - HTTP 404 / DNS failure:                         💀 Dead
```

**Freshness as RDF:**
```turtle
mom:space/fablab-ooo
    mom:lastHeartbeat "2026-04-20T08:00:00Z"^^xsd:dateTime ;
    mom:freshnessStatus mom:StatusFresh ;
    mom:endpointHealthy true .
```

---

## 5. NL→SPARQL Bridge

The LLM harness receives a natural language query and returns a SPARQL query string.

**Example:**

Input (from Mattermost): `"J'ai envie de visiter des spaces ouverts à Berlin ce weekend"`

System prompt includes: MOM ontology summary + SPARQL template library + bounding box lookup table.

Output SPARQL:
```sparql
PREFIX schema: <https://schema.org/>
PREFIX mom: <https://mapsofmaking.org/vocab#>

SELECT ?name ?address ?email ?hours
WHERE {
  ?space rdf:type schema:LocalBusiness ;
         schema:name ?name ;
         schema:address ?address ;
         schema:email ?email ;
         schema:openingHours ?hours ;
         mom:freshnessStatus mom:StatusFresh ;
         schema:geo ?geo .
  ?geo schema:latitude ?lat ;
       schema:longitude ?lon .
  FILTER(?lat > 52.3 && ?lat < 52.7 && ?lon > 13.1 && ?lon < 13.7)
}
```

Result is formatted back into a chat message by the harness: names, contacts, a map link.

**Key constraint:** The LLM only generates the SPARQL string — it never interprets or fabricates data. All answers come from the triplestore.

---

## 6. Bootstrap Path (Scraping Pipeline → LOD)

The existing `scraped/` Python pipeline provides **bootstrap data** before space operators publish their own files:

```
scraped/scripts/run_full_pipeline.py
    → Fetches member lists from network websites (BS4)
    → Extracts company data via Mistral AI
    → Outputs TOML profiles
    → export_for_map.py → GeoJSON

New step to add (post-pivot):
    → Convert TOML profiles to JSON-LD
    → Ingest to Oxigraph as "unconfirmed" spaces (mom:StatusUnconfirmed)
    → Flag for outreach: "can you publish your own endpoint URL?"
```

Unconfirmed spaces (scraped) show as ⚪ on the map.
Confirmed (space-owned endpoint) → 🔵.

---

## 7. Federation Model

Multiple networks can run their own Oxigraph instances. The shared vocabulary (MOM ontology + Schema.org) ensures queries work across federated stores via SPARQL federation (`SERVICE` keyword).

```
Network A (RFF)     Network B (VOW)
   Oxigraph            Oxigraph
       \                  /
        \                /
    Federated SPARQL query
    (maps-of-making.org hub or P2P)
```

For MVP: single Oxigraph instance (hub model). Federation via `SERVICE` is Phase 5.

---

## 8. Implementation Phases

| Phase | What | Key Deliverable |
|-------|------|-----------------|
| **0** | Define MOM ontology (JSON-LD context file) | `mapsofmaking.org/context/space.jsonld` |
| **1** | Oxigraph setup + SPARQL endpoint + ingest bootstrapped TOML data | Working SPARQL endpoint with pilot data |
| **2** | Heartbeat agent (nanoclaw/openclaw) — URL polling + diff | Freshness signals live on map |
| **3** | Web map frontend (Leaflet) + embeddable widget | Public map at mapsofmaking.org |
| **4** | NL→SPARQL LLM bridge + Mattermost/Matrix bot | Bot answering channel queries |
| **5** | SPARQL federation across network instances | Multi-network queries |

---

## 9. Open Questions

1. **Oxigraph deployment**: Embedded (Rust lib) vs standalone server mode? Standalone simplifies SPARQL endpoint exposure for the web app.
2. **nanoclaw vs openclaw**: Which is more production-ready for NL→SPARQL? Prototype both.
3. **JSON-LD context versioning**: `mapsofmaking.org/context/space.jsonld` must be stable — needs a versioning strategy before publishing.
4. **Bot framework**: Mattermost webhooks vs full bot user? Matrix via maubot?
5. **Ontology scope**: Start minimal (Schema.org only) or define MOM vocabulary from the start?
