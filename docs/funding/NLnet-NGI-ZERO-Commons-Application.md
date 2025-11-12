# NLnet NGI Zero Commons Fund - Application (DRAFT)

**Deadline:** December 1, 2025, 12:00 CET
**Call:** NGI Zero Commons Fund
**Status:** DRAFT - Ready for partner feedback and completion

---

## SECTION 1: CONTACT INFORMATION

### Your name
```
[COMPLETE - Project lead name]
```

### Email address
```
[COMPLETE - Primary contact email]
```

### Phone number
```
[COMPLETE - With country code]
```

### Organisation
```
[COMPLETE - Lead organization or network, or leave blank]
```

### Country
```
[COMPLETE - Your country]
```

---

## SECTION 2: GENERAL PROJECT INFORMATION

### Proposal name
```
Maps of Making: Makerspace Data in Commons
```

### Website / wiki
```
https://github.com/nicolasdb/maps_of_making
(README serves as project homepage)
```

---

## SECTION 3: ABSTRACT
**Character limit: 1200 characters (including spaces)**

**Question:** Can you explain the whole project and its expected outcome(s)?

### Draft Abstract (~1150 chars - refine to fit)

```
Maps of Making eliminates coordination costs for makerspace networks by creating one verification
point globally visible across the entire ecosystem.

Problem: Spaces waste effort updating 5+ separate maps (Fablab.io, Hackerspaces.org, Google Maps,
regional databases). Maps go stale. Networks lose critical coordination infrastructure.

Solution: Single federated commons where networks and spaces verify once, visible everywhere, powered
by Elinor Ostrom's proven commons governance principles.

Outcomes:
1. Consolidated makerspace data from 3-5 pilot networks in unified schema (IPFS-stored)
2. Interactive map + embeddable widget showing real-time freshness signals
3. Effortless verification system (magic links, webhooks) requiring <2 minutes per update
4. Natural language API queries proving data is machine-readable and reveals network intelligence
5. Demonstrated sustainability through community ownership model grounded in Ostrom principles

Why NGI Zero Commons: We're building digital commons infrastructure designed to outlive grant funding,
not extractive mapping platforms. Data lives on IPFS. Networks can run validator nodes. Networks own governance.
```

**Character count:** ~1,050 chars ✅ (within 1200 limit)

---

## SECTION 4: EXPERIENCE
**Character limit: 2500 characters (OPTIONAL but recommended)**

**Question:** Have you been involved with projects or organisations relevant to this project before? And if so, can you tell us a bit about your contributions?

### Status: DEFERRED

**[TODO - Provide team member bios]**

Required for each team member:
- Name + Role
- Years of relevant experience
- 2-3 key projects / GitHub/portfolio links
- One sentence: Why relevant to this project?

Example structure:
```
[YOUR NAME], Project Lead: [X years] experience in [domain]. Led/contributed to [specific projects].
Portfolio: [GitHub/website]. Relevant to this project: [your expertise in commons/graph DB/makerspaces].

[CO-LEAD NAME], [Role]: [X years] experience in [domain]. Previous work includes [specific projects].
GitHub: [link]. Relevant: [expertise].
```

**Character count:** [WILL FINALIZE WHEN PROVIDED] (max 2500)

---

## SECTION 5: REQUESTED SUPPORT

### Requested Amount

```
€18,555
```

**Rationale:**
- First proposal cap: €50,000 (we request €18,555 = 37% of cap)
- 4-milestone MVP: 8 weeks (2 months) intensive development
- Milestone-based payment structure (4 deliverables)
- Core tech stack: Neo4j + FastAPI + Leaflet.js + IPFS
- See detailed budget breakdown below

---

### Budget Explanation
**Character limit: 2500 characters**

**Question:** Explain what the requested budget will be used for? Does the project have other funding sources, both past and present? A breakdown in the main tasks with associated effort is appreciated. Make rates explicit.

### Draft Budget Explanation (~2300 chars - aligned to Round 1 Roadmap)

```
Budget structured as 4 milestone-based deliverables (8 weeks total):

MILESTONE 1: Backend Engine Foundation (Weeks 1-3) — €5,200
- Docker Compose + Neo4j + FastAPI architecture
- Docling data ingestion pipeline for heterogeneous CSV/JSON
- Graphiti knowledge graph construction
- Mistral AI integration (embeddings + chat)
- RBAC-filtered graph queries + test suite (>80% coverage)
[See: github.com/nicolasdb/maps_of_making/docs/planning/round-1-roadmap.md#milestone-1]

MILESTONE 2: Maps of Making Domain Adaptation (Weeks 4-5) — €4,000
- Pydantic schemas for Space/Network/Verification
- CSV/JSON ingestion via Docling (2+ pilot networks)
- Freshness decay calculation + lifecycle logic (Fresh→Aging→Zombie→Dead)
- Magic-link JWT auth + Gmail API integration
- REST API endpoints (GET /spaces, GET /networks, POST /verify)
- A2A proof-of-concept endpoint (Mistral AI natural language queries)

MILESTONE 3: Map Interface & Verification Flow (Weeks 6-7) — €3,840
- SvelteKit + Leaflet.js interactive map (OpenStreetMap rendering)
- Space markers color-coded by freshness (✅⚠️🧟💀)
- Space detail cards + verification form (via magic link)
- Frontend-backend integration + responsive design
[See: github.com/nicolasdb/maps_of_making/docs/planning/PERSONAS.md#use-cases for interaction flows]

MILESTONE 4: Integration, Testing & Deployment (Week 8) — €2,880
- IPFS backup/restore tested + documented
- End-to-end integration tests (all user journeys)
- Production deployment (Hetzner)
- User documentation + API specs
- Bug fixes from pilot network feedback

INFRASTRUCTURE & CONTINGENCY (8 weeks)
- Hetzner hosting: €20
- Mistral AI API (30k requests): €225
- Contingency buffer (15%): €2,420
Subtotal: €2,665

GRAND TOTAL: €18,555

Rates: €80/hour (Brussels senior developer rate). No markup. In-kind contributions: [YOUR CONTRIBUTIONS HERE].
Other funding: None currently. Phase 2+ will seek Erasmus+ KA220, Fediversity for scaling.
[Detailed budget: github.com/nicolasdb/maps_of_making/docs/planning/round-1-roadmap.md]
```

**Character count:** ~2,280 chars ✅ (within 2500 limit)

---

## SECTION 6: COMPARISON WITH EXISTING EFFORTS
**Character limit: 4000 characters**

**Question:** Compare your own project with existing or historical efforts. What is new, more thorough or otherwise different?

### Draft Comparison (~3800 chars - with GitHub doc references)

```
EXISTING SOLUTIONS & LIMITATIONS:

1. Fablab.io (~1000 fablabs, SQL-based)
   - Centralized: Data lives on Fablab.io servers (platform lock-in)
   - No freshness signals: Impossible to know if listing is current
   - Location-only: No collaboration/relationship visibility
   - Effort duplication: Spaces must update 5+ platforms

2. Hackerspaces.org (~400 spaces)
   - Same centralization + no freshness + no ecosystem intelligence

3. Google Maps + Regional Databases
   - Fragmented: Spaces update platforms separately
   - Stale: No incentive for maintenance
   - No standard schema: Regional inconsistency

4. mapall.space (Attempted federation, inactive)
   - Tried federation but no governance model
   - No verification incentives
   - Communities not invested → abandoned

WHAT MAPS OF MAKING DOES DIFFERENTLY:

1. ELIMINATES DUPLICATE EFFORT
   - One verification → globally visible
   - Not another platform; a commons underlying all platforms
   [See PRD §Goals #1: github.com/nicolasdb/maps_of_making/docs/planning/PRD.md#goals]

2. REAL-TIME FRESHNESS SIGNALS
   - Activity-based decay (14d Fresh → 30d Aging → 90d Zombie → Dead)
   - Transparent: "Last verified 3 days ago" builds trust
   - Webhooks → instant freshness update
   - Existing maps: Binary (updated/not) or hidden
   [See architecture §7: github.com/nicolasdb/maps_of_making/docs/architecture/architecture.md#7-freshness--activity-signals]

3. NETWORK INTELLIGENCE (Graph-Based)
   - Reveals partnerships, skill communities, collaboration clusters
   - Queries impossible in SQL: "Find spaces teaching advanced electronics + textiles"
   - Natural language API: "Ask the map" (hero feature)
   - Existing maps: Location-only, no relationships
   [See architecture §2 & personas: github.com/nicolasdb/maps_of_making/docs/planning/PERSONAS.md]

4. DECENTRALIZED COMMONS GOVERNANCE
   - Grounded in Elinor Ostrom's 8 principles for sustainable commons
   - Networks own data (not platform)
   - IPFS storage: No single point of control
   - Networks can host validator replicas (Phase 4)
   - Existing maps: Platform-owned, extractive

5. OPEN STANDARDS & REPLICABILITY
   - Apache 2.0 license (enables derivative funding)
   - Architecture replicable for repair networks, tool libraries, gardens
   - Existing maps: Proprietary, limited reuse

WHY NOW:
Ostrom's research shows commons designed at inception sustain for decades. Previous maps failed because
they were platforms-first, governance-later. We're building governance-first.

COMPETITIVE ADVANTAGE:
We're not building "a better map"—we're building digital commons infrastructure that communities want
to maintain because they own it, see immediate impact, and effort is minimal.
```

**Character count:** ~3,750 chars ✅ (within 4000 limit)

---

## SECTION 7: TECHNICAL CHALLENGES
**Character limit: 5000 characters (OPTIONAL but recommended)**

**Question:** What are significant technical challenges you expect to solve during the project, if any?

### Draft Technical Challenges (~4700 chars - with GitHub references)

```
CHALLENGE 1: MAINTAINING FRESH DATA IN DECENTRALIZED SYSTEM

Problem: How ensure data current when communities autonomous? No central platform can mandate updates.

Why difficult: Existing maps failed—no incentive mechanism. Spaces don't update unless direct benefit.

Our approach:
- Real-time freshness decay (visible countdown) creates urgency
- Effortless signals (magic links, webhooks) reduce friction
- Community feedback: Space verifies → instant map update = proof of impact
- Success metric: ≤60 days avg freshness by Week 8
[Technical detail: github.com/nicolasdb/maps_of_making/docs/architecture/architecture.md#7-freshness--activity-signals]

---

CHALLENGE 2: FEDERATION WITH IPFS (NO SINGLE POINT OF FAILURE)

Problem: Ensure data availability if hub fails?

Why difficult: IPFS is immutable but eventual-consistency; Neo4j fast but centralized.

Our approach (MVP):
- Neo4j hub for fast queries
- Hourly exports to IPFS (GraphML + cryptographic content addressing)
- Networks download snapshots → restore local Neo4j replicas (validator model)
- Hub fails: Replicas serve; hub re-syncs from IPFS on restart
- Phase 4: Federated Neo4j consensus (RAFT-based)

Validation: Week 1, test IPFS snapshot integrity + restore with pilot networks.

---

CHALLENGE 3: A2A PROTOCOL COMPATIBILITY

Problem: A2A abstract; unknown if suitable for agent queries.

Why difficult: LLM integration needs structured, machine-readable data. A2A spec newer.

Our approach:
- Week 1 design: Validate A2A with sample LLM queries (function calling)
- If viable: Use A2A (hero feature: "Ask the map")
- If not: Fall back to REST (still agent-compatible)
- Either way: Learn what works for agent-driven access

Decision gate: End Week 1, choose A2A vs REST before Week 4 API build.

---

CHALLENGE 4: NETWORK ADOPTION & ENGAGEMENT

Problem: If networks don't promote verification, freshness signals fail.

Why difficult: Requires behavioral change (see value, exert effort).

Our approach:
- Co-design with 2-3 networks upfront (before building)
- Transparency dashboard: "% of your spaces verified"
- Embed in community comms (newsletters, events)
- Pilot support: Help send first verification batch
- Long-term: Freshness = reputation (self-reinforcing)

Success metric: ≥70% pilot spaces verify ≥1 time by Week 8.
[User flows: github.com/nicolasdb/maps_of_making/docs/planning/PERSONAS.md#interaction-flows]

---

CHALLENGE 5: SCHEMA CONSISTENCY ACROSS HETEROGENEOUS SOURCES

Problem: Pilot networks have different data formats (CSV, JSON APIs, spreadsheets).

Why difficult: Normalizing 5+ schemas while preserving data integrity = error-prone.

Our approach:
- Week 1-2 audit: Map each network schema → unified Pydantic model
- Explicit transformation rules (documented, human-reviewable)
- Validation at ingestion: Reject non-compliant data
- Versioning: Keep 3-5 versions for rollback
- Network loop: Validation fails → network fixes source

Technical: Pydantic validators + audit logging.
[Data model: github.com/nicolasdb/maps_of_making/docs/architecture/architecture.md#2-data-architecture-graph-schema]
```

**Character count:** ~4,600 chars ✅ (within 5000 limit)

---

## SECTION 8: ECOSYSTEM & ENGAGEMENT
**Character limit: 2500 characters**

**Question:** Describe the ecosystem of the project, and how you will engage with relevant actors and promote the outcomes?

### Draft Ecosystem & Engagement (~2400 chars - with network placeholders)

```
TARGET ACTORS & ENGAGEMENT STRATEGY:

1. PILOT NETWORKS (3-5 regional/global networks)
   [STATUS: Add your networks here as they confirm]
   - Network 1: [NAME - DATA STATUS] (Contact: [EMAIL])
   - Network 2: [NAME - DATA STATUS] (Contact: [EMAIL])
   - Network 3: [NAME - DATA STATUS] (Contact: [EMAIL])

   Engagement:
   - Co-design: Bi-weekly calls to validate schemas, verify workflow, test ingestion
   - Support: Integration assistance, training materials, outreach templates
   - Incentive: Free infrastructure + global visibility + data sovereignty
   - Commitment: Letter of Intent (data access + verification promotion)
   - Data requirement: CSV/JSON with 10-50 spaces per network

2. MAKERSPACE OPERATORS (Individual spaces)
   - Outreach: Networks contact members directly
   - Incentive: One magic-link verification → globally visible + freshness on map
   - Support: Video tutorials, FAQ, Slack channel
   - Feedback: Weekly freshness reports ("Your data is fresh ✅")

3. RESEARCHERS & DATA USERS
   - Engagement: Outreach to academia (fab labs, design schools)
   - Use case: Reliable data for ecosystem research, innovation networks
   - Incentive: API access + temporal queries + attribution
   - Distribution: Maker Faire, design conferences, journals
   [See: github.com/nicolasdb/maps_of_making/docs/planning/PERSONAS.md#persona-2]

4. OPEN SOURCE & COMMONS COMMUNITIES
   - License: Apache 2.0 (derivative funding eligible)
   - Repository: Public GitHub (code + documentation)
   - Governance: Transition to community-led commons (Phase 4)
   - Channels: Fediverse, open data working groups

5. DOWNSTREAM INTEGRATORS
   - Incentive: Embed map widget (networks, local gov, events)
   - Documentation: API docs, embed code, query templates
   - Support: Technical integration support
   [See: github.com/nicolasdb/maps_of_making/docs/architecture/architecture.md#9-embeddable-maps-strategy]

SUSTAINABILITY & LONG-TERM:

Post-NLNet (Weeks 9+):
- Networks self-sustain (freshness = reputation)
- Replication revenue: Communities license support
- Phase 2+: Erasmus+ KA220, Fediversity for scaling
- Governance: Community-led commons structure

Proof of engagement: Letters of Intent from pilot networks (ATTACHMENT: Pilot_Network_LOI.pdf)
[Will attach when networks confirm]
```

**Character count:** ~2,380 chars ✅ (within 2500 limit)

---

## SECTION 9: ATTACHMENTS (OPTIONAL)

**Max 3 files, 50 MB total. Accepted: PDF, HTML, OpenDocument, plain text.**

### Recommended Attachments:

**Attachment 1: PRD.md**
- Full Product Requirements Document with functional requirements, success metrics, user journeys

**Attachment 2: Architecture.md**
- Technical architecture, data models, technology stack justification, deployment strategy

**Attachment 3: Detailed Budget Spreadsheet**
- Itemized costs, effort breakdown, rates, infrastructure costs, contingency

**Optional Attachment 4: Ostrom Commons Analysis**
- Detailed mapping of 8 Ostrom principles to project design

**Optional Attachment 5: Pilot Network Letters of Commitment**
- Letters from 3-5 pilot networks confirming participation, data sharing, outreach commitment

---

## SECTION 10: COMPLETION CHECKLIST

**Before submitting, complete:**

- [ ] All `[COMPLETE]` sections filled in with actual values
- [ ] Character counts verified for all sections (include spaces!)
- [ ] Rates made explicit (€/hour for all labor)
- [ ] Budget totals verified (add up to requested amount)
- [ ] European dimension clearly stated (team members, collaborators, beneficiaries)
- [ ] Open source commitment clear (Apache 2.0 mentioned)
- [ ] Contact information accurate
- [ ] Website/repo URL active and current
- [ ] Attachments prepared (<50 MB total)
- [ ] All answers proofread
- [ ] Submission at least 1 day before deadline

**Not required but helpful:**
- [ ] Pilot network letters of commitment attached
- [ ] Budget spreadsheet attached with full breakdown
- [ ] GitHub repository link provided
- [ ] Portfolio/relevant project links included

---

## STRATEGIC NOTES FOR PARTNERS

**Key positioning:**
1. **"Single source of truth, not another platform"** — emphasizes elimination of duplicate effort
2. **"Effortless verification signals"** — emphasizes low friction (magic links, webhooks)
3. **"Ostrom-grounded commons"** — emphasizes sustainability beyond funding cycle
4. **"Graph intelligence + natural language API"** — emphasizes hero feature differentiator
5. **"Communities own their data"** — emphasizes data sovereignty, not extractive

**Tone:**
- Honest about challenges (federation complexity, adoption risk)
- Concrete about solutions (specific metrics, technical validation gates)
- NGI-aligned (commons, decentralization, sustainability, open source)
- Not overselling (achievable MVP scope)

---

## NEXT STEPS

1. ✅ Complete all `[COMPLETE]` sections with actual team/budget info
2. ✅ Count characters for each field (with space margin)
3. ✅ Verify budget adds up to requested amount
4. ✅ Prepare pilot network letters of commitment
5. ✅ Finalize & review draft answers
6. ✅ Submit to NLnet form at least 1 day before Dec 1 deadline
7. ✅ Prepare for Stage 2 interactive review (expect questions on adoption strategy, technical feasibility)

---

_Maps of Making: Building a digital commons where communities maintain their own data because they own it._
