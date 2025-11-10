# Round 1 Roadmap: Maps of Making
**NLNet Commons Fund Application - Round 1**

**Version:** 2.0
**Date:** 2025-11-10
**Budget:** €18,555
**Timeline:** 8 weeks (2-month NLNet cycle)
**Objective:** Functional walking skeleton with 2+ pilot networks

---

## Executive Summary

Maps of Making addresses a critical ecosystem failure: **existing makerspace maps are unreliable because communities have no incentive to maintain them.**

Round 1 delivers a **working proof of concept** demonstrating technical feasibility and user value: data federation → interactive map → magic-link verification → AI-queryable knowledge graph.

**Strategic Value:** Builds reusable backend infrastructure (Neo4j + Graphiti + Mistral AI) that serves Maps of Making AND future commons projects—maximizing NLNet investment impact.

**EU Alignment:** 100% EU infrastructure (Hetzner hosting, Mistral AI), GDPR-native, Apache 2.0 license, Ostrom principles for sustainable commons governance.

---

## Project Context & Documentation

**Full requirements and technical details in sister documents (single source of truth):**
- **Product Vision:** [PRD.md](./PRD.md) - Functional requirements, user journeys, Ostrom principles
- **Technical Design:** [architecture.md](../architecture/architecture.md) - System architecture, data schema, API design
- **Technology Stack:** [tech-stack-audit.md](../architecture/tech-stack-audit.md) - Verified dependencies, licenses, trust scores

**This document focuses on:** Milestones, budget, timeline, success criteria for Round 1 delivery.

---

## Milestone-Based Budget (NLNet Payment Structure)

**Payment upon milestone completion with verified deliverables.**

### Milestone 1: Backend Engine Foundation
**Timeline:** Week 1-3
**Budget:** €5,200 (65 hours × €80/hour estimation basis)

**Deliverables:**
- Docker Compose + Neo4j + FastAPI architecture operational
- Docling data ingestion pipeline (handles heterogeneous CSV/JSON sources)
- Graphiti knowledge graph construction working
- Mistral AI integration (embeddings + chat completions)
- RBAC-filtered graph queries functional
- Test suite passing (>80% coverage)

**Success Criteria (GO/NO-GO):**
- [ ] Docker Compose `up` launches full stack without errors
- [ ] Neo4j schema created, vector search capability enabled
- [ ] Graphiti successfully constructs knowledge graph from test data
- [ ] Mistral AI API calls return valid responses
- [ ] Test suite: ≥80% pass rate

**Why This Milestone:** Foundation enables all subsequent work. Demonstrates reusable infrastructure for commons projects.

---

### Milestone 2: Maps of Making Domain Adaptation
**Timeline:** Week 4-5
**Budget:** €4,000 (50 hours × €80/hour estimation basis)

**Deliverables:**
- Pydantic schemas for makerspace domain (Space, Network, Verification)
- CSV/JSON ingestion via Docling (adapt from Milestone 1 pipeline)
- Freshness calculation + lifecycle logic (Fresh → Aging → Zombie → Dead)
- Magic-link JWT authentication + Gmail API integration
- REST API endpoints: GET /spaces, GET /networks, POST /verify/{token}
- A2A proof-of-concept endpoint (Mistral AI for natural language queries)

**Success Criteria (GO/NO-GO):**
- [ ] Ingest CSV/JSON from ≥2 pilot networks successfully
- [ ] Freshness decay calculation accurate (test cases pass)
- [ ] Magic-link email sent and JWT verified correctly
- [ ] REST API endpoints return correct data (integration tests pass)
- [ ] A2A endpoint: "Show spaces in Berlin" returns valid results

**Why This Milestone:** Proves backend architecture adapts to makerspace domain without major refactoring.

---

### Milestone 3: Map Interface & Verification Flow
**Timeline:** Week 6-7
**Budget:** €3,840 (48 hours × €80/hour estimation basis)

**Deliverables:**
- SvelteKit + Leaflet.js interactive map deployed
- OpenStreetMap rendering with space markers
- Freshness indicators on map (color-coded: ✅⚠️🧟💀)
- Space detail cards (name, location, services, last verified date)
- Verification form (accessed via magic link, updates space data)
- Frontend-backend integration complete

**Success Criteria (GO/NO-GO):**
- [ ] Map loads in <2 seconds with all pilot network spaces visible
- [ ] Click space marker → detail card displays correct info
- [ ] Magic-link → form → submit → data updates in <30 seconds
- [ ] Map updates freshness indicator on verification
- [ ] Responsive design works on desktop (>1024px)

**Why This Milestone:** User-facing proof that system works end-to-end. Demonstrates value to pilot networks.

---

### Milestone 4: Integration, Testing & Deployment
**Timeline:** Week 8
**Budget:** €2,880 (36 hours × €80/hour estimation basis)

**Deliverables:**
- IPFS daily backup script operational (snapshot + restore tested)
- End-to-end integration tests for all user journeys
- Bug fixes from pilot network feedback
- Deployment on Hetzner (production environment)
- User documentation (space operators: how to verify data)
- Technical documentation (API specs, deployment guide)
- NLNet milestone report

**Success Criteria (GO/NO-GO):**
- [ ] IPFS backup/restore successful (documented procedure)
- [ ] All 3 user journeys testable end-to-end (see PRD.md)
- [ ] Zero critical bugs blocking pilot network usage
- [ ] Production deployment accessible via public URL
- [ ] ≥2 pilot networks confirm "ready to use"

**Why This Milestone:** Validates system is production-ready for pilot testing, not just a prototype.

---

### Infrastructure Costs (8 weeks)
**Budget:** €255

**Breakdown:**
- Hetzner hosting (Docker containers): €20 (€10/month × 2 months)
- Mistral AI API (embeddings + LLM queries): €225 (~30k requests estimated)
- Domain/SSL: €0 (already secured)
- Gmail API: €0 (free tier sufficient)

**Note:** These are expected project costs for Round 1 duration, not reimbursement of existing expenses.

---

### Contingency Buffer (15%)
**Budget:** €2,420

**Purpose:** Velocity variations, unexpected technical challenges, pilot network data complexities.

---

## Total Round 1 Budget: €18,555

| Milestone | Budget | Timeline |
|-----------|--------|----------|
| M1: Backend Engine Foundation | €5,200 | Week 1-3 |
| M2: Domain Adaptation | €4,000 | Week 4-5 |
| M3: Map Interface & Verification | €3,840 | Week 6-7 |
| M4: Integration & Deployment | €2,880 | Week 8 |
| Infrastructure (8 weeks) | €255 | Ongoing |
| Contingency (15%) | €2,420 | As needed |
| **TOTAL** | **€18,555** | **8 weeks** |

**Payment Structure:** Milestone-based (NLNet standard). Payment released upon verified deliverable completion.

---

## Pilot Networks (Growing Checklist)

**Commitment Status:**
- [ ] Network 1: [Name TBD] - [Status: in discussion / committed]
- [ ] Network 2: [Name TBD] - [Status: in discussion / committed]
- [ ] Network 3: [Name TBD] - [Optional: buffer network]

**Access Confirmed:** Via Vulca Seminar 2025, agreements with EU makerspace networks for data access.

**Data Requirements:** CSV/JSON format, 10-50 spaces per network, structured contact info.

**Updated:** As commitments finalize, this section will be updated with network names and data access confirmation.

---

## Success Metrics (Quantitative)

### Primary Metrics (GO/NO-GO Gates)
1. **Data Federation:** ≥2 pilot networks ingested, ≥20 total spaces in database
2. **Map Performance:** Map loads <2 seconds, API responses <500ms
3. **Verification Flow:** ≥80% magic-link emails delivered successfully
4. **A2A Endpoint:** Natural language query returns correct results (5/5 test queries pass)
5. **Test Coverage:** ≥80% pass rate across all integration tests
6. **IPFS Backup:** Snapshot + restore successful (documented)

### Secondary Metrics
- Pilot network satisfaction: "Ready to use" confirmation from ≥2 networks
- Zero critical security vulnerabilities (basic scan)
- Documentation completeness: User guide + API docs + deployment guide published

**GO Decision:** 6/6 primary metrics met → Proceed to Round 2
**NO-GO Decision:** <4/6 primary metrics met → Pivot or cancel

---

## Team & Roles

**Core Team (In-Kind Contributions):**
- **Nicolas:** System design, architecture, backend/frontend development, integration
- **Jason:** A2A/LLM integration, pilot network coordination, business strategy
- **Fara:** Communications, pilot network liaison, documentation

**Budget Basis:** €80/hour Brussels high-end developer rate (used for estimation/planning only)

**Actual Work:** Performed by core team. Budget structured as milestone payments, not hourly contracts.

**External Support:** Contingency buffer available for unexpected needs (e.g., specialized DevOps consultation if needed).

---

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Pilot network data incompatible | Docling handles heterogeneous schemas; 15% contingency for manual normalization |
| Mistral API rate limits | Caching for repeated queries; €225 budget covers ~30k requests |
| IPFS complexity | Simple CLI script (PoC-level); defer production scaling to Round 2 |
| Velocity lower than expected | 15% contingency buffer; reuse proven betterCallSaul patterns |
| Magic-link email deliverability | Gmail API (reliable); fallback to alternative SMTP if needed |

---

## Licensing & Open Source

**License:** Apache 2.0
**Repository:** Public GitHub (to be created upon approval)
**Standards:** OpenStreetMap, GeoJSON, A2A protocol
**Data Portability:** JSON export with Pydantic schemas

---

## Future Rounds (Preview)

**Round 2 (if Round 1 successful):** Embeddable widgets, network-branded views, 3-5 additional pilot networks (~€20k, 8 weeks)

**Round 3:** Activity signals (webhooks), immutable ledger, governance structures (~€25k, 8 weeks)

**Full roadmap available upon request. Round 1 focus: prove technical feasibility + user value.**

---

_This roadmap focuses on Round 1 delivery. Full technical details in sister documents (PRD.md, architecture.md, tech-stack-audit.md). Single source of truth maintained across all documentation._
