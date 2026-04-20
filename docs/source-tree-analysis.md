# Source Tree Analysis: Maps of Making

> **Scan date:** April 2026 | **Scan level:** Deep

---

## Repository Structure

```
maps_of_making/                         # Project root
│
├── scraped/                            # ✅ WORKING — Python data pipeline
│   ├── scripts/                        # Scraping & extraction scripts
│   │   ├── utils.py                    # Shared: logging, Mistral client, SQLite, retry
│   │   ├── extract_lifetech_members.py # Phase 2: fetch LifeTech member list (paginated)
│   │   ├── fetch_member_websites.py    # Phase 3: crawl member websites
│   │   ├── extract_company_data.py     # Phase 4: LLM extraction → TOML profiles
│   │   ├── export_for_map.py           # Phase 5: generate GeoJSON for map display
│   │   ├── run_full_pipeline.py        # Orchestrator: runs all phases end-to-end
│   │   ├── model_comparison_report.py  # Util: compare Mistral model outputs
│   │   └── test_extraction_pipeline.py # Tests
│   ├── lifetech.brussels/              # Output dir: extracted TOML profiles
│   ├── deviceMed.fr/                   # Output dir: DeviceMed member data
│   ├── whatsapp-vulca/                 # VULCA chat analysis data
│   ├── venv/                           # Python virtualenv (git-ignored)
│   ├── requirements.txt                # Python dependencies
│   ├── .env.template                   # Config template (API keys)
│   └── profile_template.toml           # Template for space profiles
│
├── docs/                               # Project knowledge base
│   ├── index.md                        # ← MASTER ENTRY POINT for AI context
│   ├── project-overview.md             # Executive summary + current status
│   ├── source-tree-analysis.md         # This file
│   ├── development-guide.md            # How to run the scraping pipeline
│   ├── project-scan-report.json        # Workflow state (BMAD)
│   │
│   ├── architecture/
│   │   ├── architecture.md             # ← UPDATED: LOD/Oxigraph/SPARQL design
│   │   ├── data_capture_flow.excalidraw # Data flow diagram
│   │   ├── tech-stack-audit.md         # Tech verification (needs update for LOD stack)
│   │   ├── implementation-readiness-report.md  # Pre-NLnet gate-check (archived)
│   │   └── admin-dashboard-spec.md     # Admin UI spec
│   │
│   ├── planning/
│   │   ├── PRD.md                      # Product requirements (needs LOD update)
│   │   ├── epics.md                    # Epic breakdown (needs LOD update)
│   │   ├── competitive-analysis.md     # Market positioning
│   │   ├── PERSONAS.md / PERSONAS_refined.md   # User personas
│   │   ├── CULTIVATE principles.md     # Values framework
│   │   ├── BRAINSTORM-SUMMARY-2025-11-11.md
│   │   ├── phase-1-sprint-plan.md
│   │   ├── phase-2-3-research-plan.md
│   │   └── round-1-roadmap.md
│   │
│   ├── stories/
│   │   └── 001-lifetech-member-extraction.md   # Pilot story (in review)
│   │
│   ├── explorations/
│   │   ├── partnership-visualization-concept.md
│   │   ├── personas-review-and-refinement.md
│   │   ├── visual-mockups-and-extended-use-cases.md
│   │   └── Test_scrapping_w_claudeChrome.md
│   │
│   ├── funding/                        # NLnet application + 12 LOIs (reference)
│   │   ├── NLnet-NGI-ZERO-Commons-Application.md  # Submitted (not awarded)
│   │   └── *.pdf                       # Letters of Intent from partner orgs
│   │
│   ├── epics.md                        # Duplicate of planning/epics.md (root-level)
│   ├── tech-spec-epic-1.md             # Tech spec: Epic 1 (IPFS-based, now obsolete)
│   ├── sprint-status.yaml              # Current sprint tracking
│   └── bmm-workflow-status.md          # BMAD workflow phase tracking
│
├── Moms_mockup_index.html              # UI mockup (map + chat interface concept)
├── Maps_of_Making.html                 # Earlier static map prototype
├── mapsOfmaking_logo.png / .svg        # Brand assets
├── IMPLEMENTATION-ROADMAP-2025.md      # Earlier roadmap (pre-pivot)
├── README.md                           # Project README (needs update)
└── lifetech.brussels/                  # Also in root (mirror of scraped output?)
    └── extraction_log.db               # SQLite extraction log
```

---

## Critical Paths

### For understanding the project
1. `docs/index.md` → start here
2. `docs/project-overview.md` → context and pivot
3. `docs/architecture/architecture.md` → technical design (updated)

### For running the scraping pipeline
1. `scraped/.env.template` → copy to `.env`, add API keys
2. `scraped/requirements.txt` → install deps in venv
3. `scraped/scripts/run_full_pipeline.py` → orchestrator entry point

### Documents needing update (post-pivot)
- `README.md` — still references Neo4j/IPFS/NLnet
- `docs/planning/PRD.md` — tech references pre-pivot
- `docs/planning/epics.md` — stories designed for Neo4j stack
- `docs/tech-spec-epic-1.md` — IPFS-based spec, now obsolete

### Documents to archive
- `docs/architecture/implementation-readiness-report.md` — NLnet gate-check, no longer relevant
- `docs/tech-spec-epic-1.md` — superseded by LOD architecture
