# Project Overview: Maps of Making

> **Snapshot date:** April 2026  
> **Status:** Pre-implementation — strategic pivot to Linked Open Data stack

---

## What It Is

Maps of Making is federated infrastructure that answers one question: *"Is that makerspace still open?"* — without relying on every space to log in to 15 different directories.

The core mechanism: each space publishes **one structured file** at a public URL they control. Maps of Making crawls those URLs, detects changes (heartbeat diff), stores the data as **RDF triples** in an Oxigraph triplestore, and lets users query it — in SPARQL directly, or through a natural-language interface powered by an LLM harness.

The group-chat bot use case (someone asks in Mattermost: *"know any open spaces in Berlin?"*) is the target demo: NL query → SPARQL → structured answer → posted back in the channel.

---

## Strategic Context (April 2026)

The NLnet Commons Fund grant was not received. The project is course-correcting with a sharper, more W3C-aligned architecture:

| Before (NLnet proposal) | After (current direction) |
|-------------------------|--------------------------|
| Neo4j graph database | **Oxigraph** (RDF/SPARQL, W3C standard) |
| Graphiti LLM layer | **nanoclaw / openclaw** LLM harness |
| Custom schema + Pydantic | **JSON-LD / Turtle** (W3C Linked Data) |
| IPFS for storage | Oxigraph triplestore (SPARQL endpoint) |
| Manual verification forms | **Heartbeat diffs** on space endpoint URLs |
| Web-only queries | Web app **+ channel bots** (Mattermost, Matrix) |

The problem statement and community need are unchanged. The architecture is now aligned with W3C standards throughout — making the data intrinsically interoperable with any LOD-consuming tool.

---

## Architecture in One Sentence

> Each space publishes one JSON-LD file → a heartbeat agent monitors those URLs for diffs → changes update Oxigraph → queries are answered via SPARQL or NL→SPARQL (LLM harness) from the webapp or channel bots.

---

## Repository Structure

```
maps_of_making/
├── scraped/              # Working: Python pipeline for bootstrapping space data
│   ├── scripts/          # Scraping + extraction scripts (BS4 + Mistral AI)
│   └── requirements.txt  # Python deps
├── docs/                 # Planning, architecture, stories
│   ├── planning/         # PRD, personas, competitive analysis (needs update)
│   ├── architecture/     # Architecture docs (updated for LOD pivot)
│   ├── stories/          # Sprint stories
│   └── funding/          # NLnet application + LOIs (reference)
├── Moms_mockup_index.html  # UI mockup
└── Maps_of_Making.html     # Earlier map prototype
```

---

## Current State of Work

| Area | Status |
|------|--------|
| Vision & blog post | ✅ Published (April 2026) |
| Python scraping pipeline (LifeTech pilot) | ✅ In review (story 001) |
| Oxigraph / RDF architecture design | 🔄 In progress (this document cycle) |
| Space endpoint schema (JSON-LD) | ⬜ Not started |
| Heartbeat agent (nanoclaw/openclaw) | ⬜ Not started |
| SPARQL query layer | ⬜ Not started |
| NL→SPARQL LLM bridge | ⬜ Not started |
| Web map frontend | ⬜ Not started |
| Channel bot integration | ⬜ Not started |

---

## Pilot Networks

First two networks confirmed for piloting:
- **RFF** — Réseau des Fablabs Français
- **VOW** — Verbund Offener Werkstätten (Germany)

These will provide the first batch of space endpoint URLs and co-design the workshop onboarding process.

---

## Key Design Principles

1. **Spaces own their data** — one URL they control, not a profile on our platform
2. **Pull, don't push** — the platform fetches from spaces, not the other way around
3. **W3C all the way** — RDF, SPARQL, JSON-LD; no proprietary graph schema
4. **Freshness is a first-class signal** — heartbeat diffs power the ⚪→🔵→⚠️→🧟→💀 status
5. **Bots as the interface** — the query layer works where communities already talk
6. **Small LLM, big precision** — NL→SPARQL doesn't need GPT-4; it needs a tightly scoped harness
