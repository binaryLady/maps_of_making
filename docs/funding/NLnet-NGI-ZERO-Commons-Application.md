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
Maps of Making: Federated Makerspace Data Commons
```

### Website / wiki
```
[COMPLETE - Link to project repo, website, or wiki]
```

---

## SECTION 3: ABSTRACT
**Character limit: 1200 characters (including spaces)**

**Question:** Can you explain the whole project and its expected outcome(s)?

### Draft Abstract (~1150 chars - refine to fit)

```
Maps of Making eliminates coordination costs for makerspace networks by creating one verification point → globally visible across the entire ecosystem.

Problem: Spaces waste effort updating 5+ separate maps (Fablab.io, Hackerspaces.org, Google Maps, regional databases). Maps go stale. Networks lose critical coordination infrastructure.

Solution: Single federated commons where networks and spaces verify once, visible everywhere, powered by Elinor Ostrom's proven commons governance principles.

Outcomes:
1. Consolidated makerspace data from 3-5 pilot networks in unified schema (IPFS-stored)
2. Interactive map + embeddable widget showing real-time freshness signals
3. Effortless verification system (magic links, webhooks, local device pings) requiring <2 minutes per update
4. Hero feature: Natural language API queries ("Find active spaces in Portugal") proving data is machine-readable and reveals network intelligence
5. Demonstrated sustainability through community ownership model grounded in Ostrom principles

Why NGI Zero Commons: We're building digital commons infrastructure designed to outlive grant funding, not extractive mapping platforms. Data lives on IPFS. Networks can run validator nodes. Networks own governance.
```

**Character count:** [COUNT WHEN FINALIZING]

---

## SECTION 4: EXPERIENCE
**Character limit: 2500 characters (OPTIONAL but recommended)**

**Question:** Have you been involved with projects or organisations relevant to this project before? And if so, can you tell us a bit about your contributions?

### Draft Experience (~2400 chars - refine to fit)

```
[COMPLETE - Lead team experience including:]
- Relevant open source projects or communities
- Distributed systems / decentralization work
- Maker ecosystem involvement
- Commons governance or participatory design experience
- Technical expertise areas
- Links to portfolio/GitHub/previous work

Example structure:
- [Name], [Role]: [X years] experience in [domain]. Led/contributed to [specific projects]. Github: [link]
- [Name], [Role]: [X years] experience in [domain]. Previous work includes [specific projects]. Links: [links]
```

**Character count:** [COUNT WHEN FINALIZING]

---

## SECTION 5: REQUESTED SUPPORT

### Requested Amount

```
€[COMPLETE - recommendation: €35,000-45,000 for 9-month MVP]
```

**Rationale:**
- First proposal cap: €50,000
- 3-phase MVP: Data Federation (3mo) + Map & API (3mo) + Verification (3mo)
- 2-3 core team members
- IPFS infrastructure
- See budget breakdown below

---

### Budget Explanation
**Character limit: 2500 characters**

**Question:** Explain what the requested budget will be used for? Does the project have other funding sources, both past and present? A breakdown in the main tasks with associated effort is appreciated. Make rates explicit.

### Draft Budget Explanation (~2400 chars - refine to fit)

```
PHASE 1: DATA FEDERATION & CONSOLIDATION (3 months)
- Data schema design & Pydantic validation: 40 hours @ €75/hr = €3,000
- CSV/JSON ingestion pipeline: 60 hours @ €75/hr = €4,500
- IPFS infrastructure setup & snapshots: 40 hours @ €75/hr = €3,000
Subtotal P1: €10,500

PHASE 2: MAP & PUBLIC API (3 months)
- Frontend (Leaflet map + UI): 80 hours @ €75/hr = €6,000
- Backend API (REST + natural language gateway): 100 hours @ €75/hr = €7,500
- Embeddable widget framework: 40 hours @ €75/hr = €3,000
- Documentation & integration guides: 30 hours @ €75/hr = €2,250
Subtotal P2: €18,750

PHASE 3: VERIFICATION & MAINTENANCE (3 months)
- Magic-link auth system: 50 hours @ €75/hr = €3,750
- Verification form UI & freshness tracking: 60 hours @ €75/hr = €4,500
- Activity webhook integration: 40 hours @ €75/hr = €3,000
- Community outreach & pilot coordination: 60 hours @ €50/hr = €3,000
Subtotal P3: €14,250

INFRASTRUCTURE & OTHER
- IPFS node hosting (9 months): €1,500
- Domain + services: €300
Subtotal: €1,800

PROJECT MANAGEMENT (All phases)
- Project coordination (10%): €4,500

GRAND TOTAL: €50,000

Rates: €75/hr for senior dev, €50/hr for community coordinator. No markup.

Other funding: None currently. Seeking complementary Erasmus+ funding for Phase 4 (governance layer).
```

**Character count:** [COUNT WHEN FINALIZING]

---

## SECTION 6: COMPARISON WITH EXISTING EFFORTS
**Character limit: 4000 characters**

**Question:** Compare your own project with existing or historical efforts. What is new, more thorough or otherwise different?

### Draft Comparison (~3900 chars - refine to fit)

```
EXISTING SOLUTIONS & LIMITATIONS:

1. Fablab.io (~1000 fablabs, SQL-based)
   - Centralized: Data lives on Fablab.io servers (platform lock-in risk)
   - No freshness signals: No way to know if listing is current
   - Location-only: No relationship/collaboration visibility
   - Effort duplication: Spaces must also update regional maps

2. Hackerspaces.org (~400 spaces, custom database)
   - Same centralization problem
   - No activity signals
   - No ecosystem intelligence

3. Google Maps + Regional Databases
   - Fragmented: Spaces update 5+ platforms separately
   - Stale: No incentive for communities to maintain
   - No standard schema: Data inconsistency across regions

4. mapall.space (Attempted federated map, inactive)
   - Tried federation but no governance model
   - No freshness/activity incentives
   - Abandoned—communities not invested

WHAT MAPS OF MAKING DOES DIFFERENTLY:

1. ELIMINATES DUPLICATE EFFORT
   - One verification → visible everywhere (Fablab.io, our map, regional networks, APIs)
   - Not another platform to update; a commons underlying all platforms

2. REAL-TIME FRESHNESS SIGNALS
   - Decay-based score (365-day window) visible on map
   - Activity webhooks → instant freshness update
   - Transparent: "Last verified 5 days ago" builds trust
   - Existing maps: Binary (updated/not updated) or hidden

3. NETWORK INTELLIGENCE
   - Graph reveals collaborations, skills, partnerships
   - Queries: "Find spaces collaborating with schools in Spain?" (impossible in SQL maps)
   - Natural language API access ("Ask the map")
   - Existing maps: Location-only, no relationships

4. DECENTRALIZED COMMONS GOVERNANCE
   - Grounded in Elinor Ostrom's 8 principles for sustainable commons
   - Networks own their data (not platform)
   - IPFS storage: No single point of control
   - Networks can run validator nodes (Phase 4)
   - Existing maps: Platform-owned, extractive model

5. OPEN STANDARDS & REPLICABILITY
   - Apache 2.0 license (enables derivative funding)
   - Architecture replicable for repair networks, tool libraries, community gardens
   - Existing maps: Proprietary, limited reuse

WHY NOW:
Ostrom's research shows commons designed at inception sustain for decades. Previous maps failed because they were platforms-first, governance-later. We're building governance-first.

COMPETITIVE ADVANTAGE:
We're not building "a better map"—we're building digital commons infrastructure that communities want to maintain because they own it, see impact immediately, and effort is minimal.
```

**Character count:** [COUNT WHEN FINALIZING]

---

## SECTION 7: TECHNICAL CHALLENGES
**Character limit: 5000 characters (OPTIONAL but recommended)**

**Question:** What are significant technical challenges you expect to solve during the project, if any?

### Draft Technical Challenges (~4900 chars - refine to fit)

```
CHALLENGE 1: MAINTAINING FRESH DATA IN A DECENTRALIZED SYSTEM

Problem: How do we ensure data stays current when communities are autonomous and no central platform can mandate updates?

Why difficult: Existing maps failed because they had no incentive mechanism. Spaces don't update Fablab.io unless they have direct benefit.

Our approach:
- Real-time freshness decay (visible countdown) creates natural urgency
- Effortless verification signals (magic links, webhooks) reduce friction below "worth updating"
- Community feedback loop: When a space verifies, they see instant map update—proof of impact
- Success metric: ≤60 days average freshness across pilot networks by month 9

Technical implementation: On-read freshness calculation (<1ms overhead). Activity webhooks trigger immediate Neo4j updates.

---

CHALLENGE 2: FEDERATION WITH IPFS (NO SINGLE POINT OF FAILURE)

Problem: How do we ensure data availability if the central hub fails?

Why difficult: IPFS is immutable but eventual-consistency; Neo4j is fast but centralized. Merging both worlds requires careful architecture.

Our approach (MVP):
- Neo4j central hub for fast queries
- Hourly exports to IPFS (GraphML format) with cryptographic content addressing
- Networks can download IPFS snapshot → restore local Neo4j replica (validator node model)
- If hub fails, replicas serve queries; hub re-syncs from IPFS on restart

Phase 4: Federated Neo4j consensus (RAFT-based replication)

Technical validation: In Phase 1, we'll test IPFS snapshot integrity + restore process with pilot networks.

---

CHALLENGE 3: A2A PROTOCOL COMPATIBILITY VALIDATION

Problem: A2A protocol is abstract; we don't know if it's suitable for agent queries until we try.

Why difficult: LLM agent integration requires structured, machine-readable data. A2A spec is newer; may not align perfectly with our use case.

Our approach:
- Phase 1 design: Validate A2A compatibility with sample LLM queries (GPT-4 function calling)
- If viable: Use A2A protocol for agent integration (hero feature: "Ask the map")
- If not viable: Fall back to standard RESTful API (still agent-compatible via function calling)
- Either way, we've learned what works for agent-driven data access

Technical decision gate: End of Phase 1, decide A2A vs REST before building Phase 2 API.

---

CHALLENGE 4: ADOPTION & NETWORK ENGAGEMENT

Problem: If networks don't promote verification to their spaces, freshness signals fail.

Why difficult: Requires behavioral change (communities must see value, exert effort).

Our approach:
- Co-design verification flow with 2-3 pilot networks upfront (before building)
- Show transparency dashboard to network leaders: "% of your spaces verified"
- Embed verification into community communication (monthly newsletters, events)
- Pilot support: We'll help networks send first batch of verification emails
- Long-term: Communities maintain outreach because data freshness = their reputation

Success metric: ≥70% of pilot network spaces verify at least once by month 9.

---

CHALLENGE 5: SCHEMA CONSISTENCY ACROSS HETEROGENEOUS SOURCES

Problem: Pilot networks have different data formats (CSV, JSON APIs, spreadsheets with different columns).

Why difficult: Normalizing 5+ different schemas while preserving data integrity is error-prone.

Our approach:
- Phase 1 audit: Map each network's schema to unified Pydantic model
- Explicit transformation rules (documented, human-reviewable)
- Validation at ingestion: Reject data that doesn't fit schema
- Versioning: Keep last 3-5 versions for rollback if ingestion fails
- Network feedback loop: If validation fails, network fixes source data

Technical: Pydantic + custom validators + audit trail logging.
```

**Character count:** [COUNT WHEN FINALIZING]

---

## SECTION 8: ECOSYSTEM & ENGAGEMENT
**Character limit: 2500 characters**

**Question:** Describe the ecosystem of the project, and how you will engage with relevant actors and promote the outcomes?

### Draft Ecosystem & Engagement (~2400 chars - refine to fit)

```
TARGET ACTORS & ENGAGEMENT STRATEGY:

1. PILOT NETWORKS (3-5 regional/global networks)
   - Recruitment: Vulca Seminar attendees + direct outreach to Fab Lab Network, Hackerspaces.org
   - Co-design: Monthly calls during Phase 1 to validate data schemas, verification flow
   - Support: We provide integration support, training materials, outreach templates
   - Incentive: Free infrastructure + global visibility + data ownership
   - Commitment: Letter of intent to participate, designate data steward

2. MAKERSPACE OPERATORS (Individual spaces)
   - Outreach: Via pilot networks (they contact their members)
   - Incentive: One update → visible everywhere; effortless verification signals
   - Support: Video tutorials, FAQ, community Slack channel
   - Feedback: Monthly verification reports showing impact

3. RESEARCHERS & DATA USERS
   - Engagement: Outreach to academia (university maker labs, design schools)
   - Use case: Reliable data for research on maker ecosystems, innovation networks
   - Incentive: API access to data, attribution for research
   - Distribution: Present at academic conferences (Maker Faires, design conferences)

4. OPEN SOURCE & COMMONS COMMUNITIES
   - License: Apache 2.0 (derivative funding eligible)
   - Repository: Public GitHub (documentation, contribution guidelines)
   - Community: Join open commons governance initiatives (Phase 4)
   - Engagement: Relevant Fediverse communities, open data working groups

5. DOWNSTREAM INTEGRATORS
   - Incentive: Embed map widget on their websites (networks, local government, event sites)
   - Documentation: API docs, embed code, example queries
   - Support: Technical support for integrations

SUSTAINABILITY & LONG-TERM ENGAGEMENT:

Post-NLNet (Months 10+):
- Networks self-sustain verification outreach (governance model in place)
- Replication revenue model: Communities license implementation support
- Phase 4 funding: Erasmus+ KA220 for expanded governance, Fediversity for decentralized scaling
- Open governance: Transition to community-led commons governance structure

Proof of engagement: Letters of commitment from 3-5 pilot networks (attached).
```

**Character count:** [COUNT WHEN FINALIZING]

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
