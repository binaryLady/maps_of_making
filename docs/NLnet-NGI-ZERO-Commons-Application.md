# NLnet NGI ZERO Commons Application
## Maps of Making - Federated Makerspace Data Commons

**Application Status**: DRAFT - Ready for partner feedback
**Target Deadline**: December 1, 2025, 12:00 CET
**Call**: NGI Zero Commons Fund

---

## SECTION 1: CONTACT INFORMATION

**Project Lead Name**: [COMPLETE]
**Email**: [COMPLETE]
**Phone**: [COMPLETE]
**Organisation/Network**: [COMPLETE]
**Country**: [COMPLETE]

---

## SECTION 2: CALL SELECTION

**Selected Call**: NGI Zero Commons Fund

**Rationale for Selection**:
Maps of Making aligns with NGI Zero Commons priorities by:
- Creating **digital commons infrastructure** (federated makerspace data) governed by participating communities
- Demonstrating **decentralized data stewardship** where communities maintain authoritative listings of their own resources
- Enabling **ecosystem transparency** through open standards and freshness metrics
- Building **scalable, interoperable infrastructure** for distributed maker networks globally

---

## SECTION 3: GENERAL PROJECT INFORMATION

### 3.1 Proposal Name
**Maps of Making: Federated Makerspace Data Commons**

### 3.2 Website/Wiki URL
[COMPLETE - Link to project repo, wiki, or landing page]

### 3.3 Abstract (Overall Project & Expected Outcomes)

**Problem Statement**:
Existing makerspace maps fail because they create a structural incentive misalignment: spaces maintain data once (to be discovered), then have no reason to keep it current. Result: maps become stale, trust erodes, and the ecosystem loses transparent infrastructure.

**Our Solution**:
Maps of Making establishes a **decentralized digital commons** where participating networks maintain authoritative listings of their own makerspaces. Communities stay engaged through:
- **Visible freshness metrics** (decay-based countdown showing data age)
- **Reputation signals** (maintaining current data proves community vitality)
- **Community ownership** (spaces control their own data, not a platform)
- **Usefulness** (embedded everywhere—websites, APIs, agent queries—proving resource value)

**Expected Outcomes (NGI Phase)**:

1. **Federated Data Infrastructure**:
   - Consolidated makerspace data from 3-5 pilot networks normalized into unified Pydantic schema
   - Data stored in IPFS with cryptographic integrity
   - Decentralized, no single point of failure

2. **Public Interactive Map & APIs**:
   - Interactive OpenStreetMap showing all spaces with freshness metadata
   - Embeddable widget for external websites
   - A2A-compatible API for LLM agent integration
   - Demonstrates data as usable digital commons

3. **Verification & Community Maintenance System**:
   - Magic-link verification process (no account required)
   - Space operators update data in <2 minutes
   - Freshness decay resets on verification—accountability through transparency
   - Audit trail logged immutably

4. **Open Standards & Portability**:
   - All data released under Apache 2.0
   - JSON/Pydantic schemas for interoperability
   - Reusable for other distributed resource mapping (repair networks, tool libraries, etc.)

**Impact**: Proves that decentralized data governance works when communities have clear ownership, visibility, and accountability—foundational for NGI digital commons vision.

---

## SECTION 4: PREVIOUS EXPERIENCE

### 4.1 Applicant's Relevant Experience

[COMPLETE - Include:]
- Prior projects with distributed/decentralized systems
- Experience with maker/maker communities
- Open-source or commons governance experience
- Relevant network partnerships

### 4.2 Consortium & Network Partners

[COMPLETE - List pilot networks providing makerspace data, e.g.:]
- Partner Network 1 (# spaces, location, existing data sources)
- Partner Network 2
- Partner Network 3
- [Optional: NGI or other institutional supporters]

---

## SECTION 5: REQUESTED SUPPORT

### 5.1 Budget Request (EUR)

**Total Project Budget**: [COMPLETE - e.g., €XX,XXX]

**Budget Breakdown by Phase**:

#### Phase 1: Data Federation & Consolidation (Months 1-3)
- Data migration & normalization engineering: €X,XXX
- IPFS storage infrastructure setup: €X,XXX
- Pydantic schema design & validation: €X,XXX
- **Subtotal P1**: €X,XXX

#### Phase 2: Map Display & Public API (Months 4-6)
- Frontend development (React/interactive map): €X,XXX
- API development (REST + A2A protocol): €X,XXX
- Embeddable widget framework: €X,XXX
- Documentation & integration guides: €X,XXX
- **Subtotal P2**: €X,XXX

#### Phase 3: Verification & Community Maintenance (Months 7-9)
- Magic-link authentication system: €X,XXX
- Space update form UI/UX: €X,XXX
- Freshness decay & event ledger: €X,XXX
- Community outreach & pilot coordination: €X,XXX
- **Subtotal P3**: €X,XXX

#### Project Management & Operations (All phases)
- Project coordination: €X,XXX
- Sustainability planning & final documentation: €X,XXX
- **Subtotal PM**: €X,XXX

**Grand Total**: €[TOTAL]

### 5.2 Explanation of Budget Usage

**Human Resources** (40-50% of budget):
- Lead Developer (decentralized architecture, IPFS): [X hours @ €X/hr]
- Frontend Developer (map & widgets): [X hours @ €X/hr]
- Community Coordinator (network partnerships, outreach): [X hours @ €X/hr]
- Project Lead/Product Manager: [X hours @ €X/hr]

**Infrastructure & Operations** (20-30% of budget):
- IPFS node hosting (9-12 months): €X,XXX
- Server/API infrastructure: €X,XXX
- Domain & platform services: €X,XXX
- Data migration tools & services: €X,XXX

**Community & Ecosystem** (10-15% of budget):
- Pilot network coordination (Vulca events, workshops): €X,XXX
- User research & feedback sessions: €X,XXX
- Documentation & training materials: €X,XXX

**Contingency** (5-10% of budget):
- Technical challenges, unforeseen dependencies: €X,XXX

### 5.3 Other Funding Sources (Past & Present)

[COMPLETE - Include:]
- Any existing funding or in-kind contributions from consortium partners
- Prior grants (e.g., Prototype Fund, other NGI calls)
- Institutional support

---

## SECTION 6: PROJECT NARRATIVE & TECHNICAL APPROACH

### 6.1 Ecosystem & Strategic Context

**The Ecosystem Problem**:
The maker movement is fragmented. Regional networks maintain their own makerspace directories, but there's no trusted cross-network resource. Researchers, digital nomads, and community members waste time on outdated maps and broken contact info.

**Why Previous Attempts Failed**:
Earlier makerspace mapping projects (e.g., Makespace map, local initiatives) collapsed because they:
1. Centralized data on a platform communities didn't control
2. Had no feedback loop showing spaces why updating mattered
3. Provided no incentive for ongoing maintenance
4. Couldn't establish authority across autonomous regional networks

**Our Strategic Insight**:
Maintenance becomes rationally justified when:
- **Data is authoritative** (spaces recognize it as their official listing)
- **Maintenance is transparent** (freshness metrics prove they're active)
- **Data is embedded everywhere** (used by users, agents, researchers—proving value)

Maps of Making decentralizes authority: each network controls their data, but participates in a global commons.

### 6.2 NGI Digital Commons Alignment

**Why This Matters to NGI Zero**:
- **Decentralization**: No platform gatekeeping; communities own their data
- **Interoperability**: Open standards (JSON-LD, OpenStreetMap, A2A) enable reuse
- **Sustainability**: Communities maintain data because it's *their* reputation
- **Replicability**: Architecture can be adapted for other distributed resource maps (repair networks, tool libraries, community gardens)

### 6.3 Technical Architecture (Summary)

**Core Components**:

1. **Federated Data Layer** (IPFS):
   - Each participating network publishes their makerspace data to IPFS
   - Data normalized to unified Pydantic schema
   - Cryptographic integrity via IPFS content hashing
   - Local mirrors for fault tolerance

2. **Index & Query Layer**:
   - Central index of all federated data sources
   - RESTful API for spatial queries (radius search, filters by space type)
   - A2A-compatible endpoints for LLM agent integration

3. **Frontend & Public Interface**:
   - Interactive OpenStreetMap showing real-time freshness status
   - Embeddable widget for external websites
   - Detail view showing: address, services, hours, **last verified date**, activity signals

4. **Verification & Maintenance** (Community-Facing):
   - Magic-link email authentication (no account required)
   - Simple form: review current data, confirm/update changes
   - Freshness decay countdown (1-year lifecycle)
   - Immutable audit trail logged

5. **Governance & Trust**:
   - Freshness lifecycle: Fresh ✅ → Aging ⚠️ → Zombie 🧟 → Dead 💀
   - Transparent decay metrics visible to users
   - Immutable event ledger for verifications, closures, partnerships
   - GDPR-compliant data deletion (remove personal info, preserve structural integrity)

**Technology Stack**:
- **Storage**: IPFS (distributed, no platform dependency)
- **Data Format**: JSON with Pydantic validation schemas
- **Frontend**: React, OpenStreetMap/Leaflet
- **Backend**: Python/FastAPI or Node.js
- **Identity**: Magic links (MVP); prepared for SOLID/A2A/blockchain in Phase 4
- **License**: Apache 2.0 (enables NGI derivative funding)

### 6.4 Technical Challenges & Mitigation

**Challenge 1: IPFS Data Availability**
- *Risk*: IPFS nodes may go offline; data becomes unavailable
- *Mitigation*:
  - Deploy redundant IPFS nodes across pilot networks
  - Cache hot data (recent verifications) in managed API layer
  - Pinning service for critical data

**Challenge 2: Decentralized Data Synchronization**
- *Risk*: Network lag; conflicting updates from multiple sources
- *Mitigation*:
  - Append-only event ledger (immutable record of truth)
  - Deterministic conflict resolution (last verified timestamp wins)
  - Version control for volatile data (keep 3-5 prior versions)

**Challenge 3: Adoption & Network Engagement**
- *Risk*: Pilot networks don't prioritize verification outreach
- *Mitigation*:
  - Embed verification into network communication (newsletters, events)
  - Show network leaders transparency dashboard (% of spaces verified)
  - Co-design verification flow with pilot communities

**Challenge 4: A2A Protocol Feasibility**
- *Risk*: A2A may not suit agent queries (to be validated)
- *Mitigation*:
  - Phase 1: Validate A2A compatibility with sample LLM queries
  - Fallback: Standard RESTful API if A2A unsuitable
  - Keep API interface agent-friendly (structured, JSON, semantic clarity)

---

## SECTION 7: SUCCESS METRICS & VALIDATION

### 7.1 Primary Success Metric: Data Freshness

**Target**: Average makerspace data freshness of **≤60 days** across pilot networks by end of NGI phase (month 9)

**Measurement**:
- Track last verification date for each space
- Decay model: 1-year evaluation window (365 days)
- Freshness score = (365 - days_since_verification) / 365
- Calculate network average monthly

**Why This Matters**: Proves communities are *actively maintaining* data because it's their reputation—solving the core incentive problem.

### 7.2 Secondary Success Metrics

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Network Participation** | ≥70% of pilot network spaces with ≥1 verification | Count spaces that have submitted at least one verification via magic link |
| **Activity Signal Adoption** | ≥20% of spaces integrate optional sensors/signals | Count spaces with connected activity feeds (login logs, sensor data, etc.) |
| **External Embedding** | ≥10 websites/platforms using map widget | Track widget embed code deployments |
| **API Engagement** | ≥100 API queries/month (if A2A viable) | Monitor API request logs for agent/user access |
| **Data Portability** | ≥3 third-party systems import our data via JSON export | Track downstream integrations |
| **Open Source Sustainability** | ≥2 external contributors to codebase during NGI phase | Track GitHub contributors, pull requests |

### 7.3 Validation Plan

**Month 3 (End of Phase 1)**:
- ✅ All pilot network data consolidated into unified schema
- ✅ IPFS infrastructure operational with redundancy
- ✅ Mapping maintained between source networks and federation
- Validation: Data audit & network partner sign-off

**Month 6 (End of Phase 2)**:
- ✅ Public map live, showing all pilot spaces + freshness metadata
- ✅ API endpoints functional; embeddable widget deployed
- ✅ A2A protocol viability assessed (validate or pivot to REST)
- Validation: User testing with sample researchers/nomads

**Month 9 (End of Phase 3)**:
- ✅ Verification flow deployed; ≥50% of spaces verified at least once
- ✅ Freshness decay visible on map; audit trail immutable
- ✅ Community maintenance sustainable (networks committed to outreach)
- Validation: Freshness metrics reviewed; sustainability plan finalized

---

## SECTION 8: ECOSYSTEM & PARTNERSHIPS

### 8.1 Pilot Network Commitment

[COMPLETE - For each pilot network, document:]
- Network name & geographic scope
- Number of member makerspaces
- Existing data sources (CSV, API, database)
- Data sharing agreement
- Commitment to verification outreach
- Contact person for coordination

**Example**:
> **Vulca Network (Spain)**
> - 45 member makerspaces across 12 regions
> - Data source: CSV + API from Vulca database
> - Commitment: Promote verification to members via monthly newsletter + annual conference
> - Contact: [Name, Email]

### 8.2 Downstream Stakeholders

**Who Benefits from Maps of Making**:
- **Researchers**: Reliable data on maker ecosystem distribution & vitality
- **Digital nomads/travelers**: Current info on available workspaces
- **Local government**: Transparent view of maker infrastructure in their region
- **LLM agents**: Machine-readable data for trip planning, site selection
- **Future networks**: Replicable architecture for other distributed resource maps

### 8.3 Open Source & Sustainability

**License**: Apache 2.0 (enables derivative works, commercial use, community extensions)

**Contribution Model**:
- Code hosted on GitHub (public repository)
- Documentation for fork & local deployment
- API specification enables third-party integrations
- Community governance framework (in Phase 4)

**Post-NGI Sustainability**:
- Maps of Making core remains free & open
- Pilot networks self-sustain verification outreach
- Potential Phase 4 funding from Erasmus+, NGI Fediversity for governance layer
- Replication revenue model: communities can license implementation support

---

## SECTION 9: ASSUMPTIONS & CONSTRAINTS

### 9.1 Key Assumptions

1. **Pilot networks have existing makerspace databases** (CSV/JSON/APIs) to consolidate
2. **Network leaders commit to promotion** (verification requires outreach; we provide the tool, they drive adoption)
3. **Spaces have email contacts** for magic-link verification outreach
4. **A2A protocol is suitable for agent integration** (to be validated in Phase 1; fallback to REST)
5. **Participating communities prioritize data freshness** as a reputation signal

### 9.2 Constraints

- **MVP scope**: 3-5 pilot networks (managing federation complexity)
- **Phase 1 capacity**: Data migration can handle 500-1000 spaces in initial consolidation
- **No account management** (simplifies Phase 3, ensures low friction)
- **Activity signals optional** in MVP (reduces complexity; infrastructure prepared)
- **Budget constraint**: Must cover data migration + federation setup + map platform + verification flow within approved grant

---

## SECTION 10: TIMELINE & MILESTONES

### Phase 1: Data Federation & Consolidation (Months 1-3)

| Milestone | Deliverable | Success Criteria |
|-----------|-------------|-----------------|
| **M1.1** | Data audit & schema design | All pilot network data schemas documented & Pydantic model finalized |
| **M1.2** | IPFS infrastructure | Nodes deployed, redundancy verified, pinning service operational |
| **M1.3** | Data migration | All pilot network data consolidated, normalized, stored on IPFS |
| **M1.4** | Index layer | Central query index deployed & queryable |

### Phase 2: Map Display & Public API (Months 4-6)

| Milestone | Deliverable | Success Criteria |
|-----------|-------------|-----------------|
| **M2.1** | Frontend foundation | React app with OSM base, freshness indicators rendered |
| **M2.2** | API endpoints | REST endpoints functional; A2A compatibility assessed |
| **M2.3** | Embeddable widget | Widget code generated, deployable on external sites |
| **M2.4** | Public launch | Map live on dedicated domain; all networks can view their spaces |

### Phase 3: Verification & Community Maintenance (Months 7-9)

| Milestone | Deliverable | Success Criteria |
|-----------|-------------|-----------------|
| **M3.1** | Verification flow | Magic-link email, form rendering, data updates functional |
| **M3.2** | Freshness decay | Lifecycle model implemented, countdown visible on map |
| **M3.3** | Pilot outreach | Verification emails sent; ≥50% space participation in pilot networks |
| **M3.4** | Sustainability plan | Community commitment documents, Phase 4 roadmap finalized |

---

## SECTION 11: ATTACHMENTS & SUPPORTING DOCUMENTS

[TO PREPARE]:
- [ ] Detailed technical architecture diagram (PDF)
- [ ] Pydantic schema specification (JSON Schema)
- [ ] Pilot network data sharing agreements (PDF)
- [ ] Budget spreadsheet with itemized costs (Excel/ODS)
- [ ] Letters of commitment from pilot network partners (PDF)
- [ ] Competitive analysis (vs. existing makerspace maps)
- [ ] Market research (maker ecosystem size, pain points)
- [ ] Mockups or wireframes of verification form & map interface (PDF/PNG)

**Attachment Guidelines**:
- Accepted formats: HTML, PDF, OpenDocument Format (.odt/.ods), plain text
- Maximum total size: 50 MB

---

## SECTION 12: PRIVACY & DATA PROTECTION STATEMENT

☑ **I have read and understood NLnet's privacy statement** (https://nlnet.nl/privacy/)

☑ **I agree to NLnet's data handling practices**, including:
- Contact information used for grant administration
- Project outcomes shared in NLnet's public database
- Compliance with GDPR and relevant data protection regulations

☑ **Optional**: Send me a copy of this application (yes/no): [COMPLETE]

**Optional PGP Public Key**: [If desired, add PGP key for secure communication]

---

## DOCUMENT CONTROL

| Field | Value |
|-------|-------|
| **Document Version** | 1.0 DRAFT |
| **Last Updated** | 2025-11-05 |
| **Status** | Awaiting Partner Feedback & Completion |
| **Next Steps** | Address partner remarks → Complete [COMPLETE] sections → Final review → Submit |

---

## NEXT ACTIONS

**For Nicolas & Partners**:

1. ✅ **Complete contact & consortium sections** (Section 1, 4.2)
2. ✅ **Finalize budget breakdown** (Section 5.1) with detailed cost estimates
3. ✅ **Document pilot network commitments** (Section 8.1)
4. ✅ **Prepare supporting attachments** (Section 11)
5. ✅ **Address partner feedback** (iteratively update affected sections)
6. ✅ **Final narrative polish** (align language to NGI Zero Commons priorities)
7. ✅ **Submit by December 1, 2025, 12:00 CET**

**For Immediate Partner Review**:
- Send this draft to pilot networks & partners
- Request feedback on:
  - Budget assumptions (are effort estimates realistic?)
  - Timeline feasibility (are 3-month phases realistic for your teams?)
  - Technical approach (concerns about IPFS, A2A, magic links?)
  - Scope & impact expectations

---

_Maps of Making: Building a trustworthy digital commons for distributed maker networks_
