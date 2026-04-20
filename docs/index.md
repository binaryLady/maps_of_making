# Documentation Index: Maps of Making

> **Snapshot:** April 2026 | **Status:** LOD Pivot — pre-implementation  
> **Context:** NLnet grant not awarded. Pivoting to W3C Linked Open Data stack (Oxigraph/SPARQL/JSON-LD + LLM harness).

---

## Start Here

| I am... | Read this |
|---------|-----------|
| New to the project | [project-overview.md](project-overview.md) (5 min) |
| Technical / architect | [architecture/architecture.md](architecture/architecture.md) (20 min) |
| Developer ready to code | [development-guide.md](development-guide.md) + [stories/](stories/) |
| Community partner / network | [project-overview.md](project-overview.md) + blog post below |

**Published vision:** [map-of-making-locker blog post](../ndb_hugo/content/posts/map-of-making-locker/index.md) — the public-facing explanation of the LOD approach.

---

## Generated Documentation (Current)

- [Project Overview](project-overview.md) — executive summary, pivot context, current status
- [Architecture v2.0](architecture/architecture.md) — Oxigraph/RDF/SPARQL/LLM harness design
- [Source Tree Analysis](source-tree-analysis.md) — annotated repo structure
- [Development Guide](development-guide.md) — how to run the scraping pipeline

---

## Planning Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [planning/PRD.md](planning/PRD.md) | Product requirements | ⚠️ Needs update (references Neo4j stack) |
| [planning/epics.md](planning/epics.md) | Epic breakdown | ⚠️ Needs update (IPFS-based stories) |
| [planning/competitive-analysis.md](planning/competitive-analysis.md) | Market positioning | ✅ Still valid |
| [planning/PERSONAS.md](planning/PERSONAS.md) | User personas | ✅ Still valid |
| [planning/CULTIVATE principles.md](planning/CULTIVATE%20principles.md) | Values framework | ✅ Still valid |

---

## Architecture Documents

| Document | Purpose | Status |
|----------|---------|--------|
| [architecture/architecture.md](architecture/architecture.md) | System design | ✅ Updated (LOD stack) |
| [architecture/data_capture_flow.excalidraw](architecture/data_capture_flow.excalidraw) | Data flow diagram | ⚠️ Needs update |
| [architecture/tech-stack-audit.md](architecture/tech-stack-audit.md) | Tech verification | ⚠️ Needs update (new stack) |
| [architecture/admin-dashboard-spec.md](architecture/admin-dashboard-spec.md) | Admin UI spec | 🔄 Reference |
| [architecture/implementation-readiness-report.md](architecture/implementation-readiness-report.md) | NLnet gate-check | 📦 Archive (pre-pivot) |

---

## Sprint Tracking

| Document | Purpose |
|----------|---------|
| [sprint-status.yaml](sprint-status.yaml) | Story status tracking |
| [stories/001-lifetech-member-extraction.md](stories/001-lifetech-member-extraction.md) | Pilot story (in review) |
| [tech-spec-epic-1.md](tech-spec-epic-1.md) | Epic 1 tech spec (IPFS-based — obsolete, reference only) |

**Current sprint state:** 1 pilot story in review. All Epic 1-3 stories in backlog. Epics need re-contexting for LOD stack.

---

## Funding / Reference

| Document | Purpose |
|----------|---------|
| [funding/NLnet-NGI-ZERO-Commons-Application.md](funding/NLnet-NGI-ZERO-Commons-Application.md) | NLnet application (not awarded — reference) |
| `funding/*.pdf` | 12 Letters of Intent from partner orgs |
| [funding/COST-SUSTAINABILITY.md](funding/COST-SUSTAINABILITY.md) | Cost model |

---

## Explorations

- [explorations/partnership-visualization-concept.md](explorations/partnership-visualization-concept.md)
- [explorations/personas-review-and-refinement.md](explorations/personas-review-and-refinement.md)
- [explorations/visual-mockups-and-extended-use-cases.md](explorations/visual-mockups-and-extended-use-cases.md)

---

## Immediate Next Steps

1. **Re-context epics** for LOD stack (Oxigraph/SPARQL/JSON-LD replacing IPFS/Neo4j)
2. **Define MOM ontology** — the JSON-LD context file is the foundation for everything else
3. **Prototype Oxigraph** — stand it up locally, ingest bootstrapped TOML data as JSON-LD
4. **Prototype nanoclaw/openclaw** — NL→SPARQL proof of concept with pilot data
5. **Close pilot story 001** — finish LifeTech extraction review, use output as bootstrap data

---

## Key Vocabulary (for AI context)

- **LOD** — Linked Open Data; RDF-based, W3C standard
- **Oxigraph** — W3C-compliant RDF triplestore with SPARQL 1.1 endpoint (Rust)
- **SPARQL** — W3C query language for RDF data (replaces Cypher/Neo4j)
- **JSON-LD** — JSON format that is valid RDF; space endpoint file format
- **MOM ontology** — the custom vocabulary (`mom:` prefix) for maker ecosystem concepts
- **Heartbeat** — periodic URL fetch + diff to detect space data changes
- **nanoclaw / openclaw** — lightweight LLM harness for NL→SPARQL and diff tasks
- **Freshness** — ⚪ unconfirmed → 🔵 fresh → ⚠️ aging → 🧟 zombie → 💀 dead
- **Space endpoint** — the one JSON-LD file a space publishes at their own URL
