# Budget Breakdown - Maps of Making Round 1

**Requested Amount:** €39900

---

## Overview

3-month intensive development and validation cycle delivering a working prototype with validated engagement model. Budget covers 2 core team members working half-time, infrastructure costs, and in-person validation sessions with pilot partners.

**Key Principles:**
- Milestone-based payments tied to concrete deliverables
- Both technical AND community validation funded equally
- Short cycles enabling rapid iteration (fail fast, adjust)
- Reasonable scope: walking skeleton + validation, not full product

---

## Budget Structure

**Core Approach:**

Round 1 validates our architecture choices through rapid iteration with real users. We run two parallel tracks:

1. **Technical Track:** Build walking skeleton, test graph vs SQL, validate IPFS approach
2. **Community Track:** Interview operators, beta test onboarding, measure engagement

Both tracks inform each other through short 2-4 week cycles.

---

## Milestone Breakdown

### Milestone 1: Solution Validation (2 weeks) — €6400

**Team Activities:**
- Compare graph database vs SQL for relationship queries
- Prototype basic ingestion from real makerspace websites (3-5 sources)
- Test onboarding flow concepts with 5 space operators
- Validate core hypothesis: Would magic links + freshness signals actually drive sustained engagement?
- Document architecture decisions and user feedback

**Deliverable:** Technical spike proving architecture choices + user research confirming solution addresses real needs

**Hours:** 80h  
**Rate:** €80/h  
**Cost:** €6400

**Acceptance Criteria & Artifacts**
- [ ] Mockups (Figma or PNG) provided
- [ ] Architecture decisions documented (Markdown)
- [ ] ≥5 interview notes submitted
- [ ] Decision recorded and signed off by project leads

---

### Milestone 2: Walking Skeleton + Decentralized Backup (3 weeks) — €9600

**Team Activities:**
- Implement chosen architecture (graph database + ingestion pipeline)
- Build basic map interface with freshness indicators
- Add decentralized backup layer (IPFS or alternative)
- Create magic link authentication flow
- Design and prototype onboarding experience
- Recruit 5 beta test spaces (mix: network-coordinated + permissionless)

**Deliverable:** Working end-to-end prototype with backup capability, ready for real user testing

**Hours:** 120h  
**Rate:** €80/h  
**Cost:** €9600

**Acceptance Criteria & Artifacts**
- [ ] Staging prototype URL or local run instructions (README)
- [ ] Ingestion sample + schema provided
- [ ] Backup retrieval proof (IPFS hash or alternative)
- [ ] End-to-end smoke test passes

---

### Milestone 3: Beta Test + Iteration (3 weeks) — €9600

**Team Activities:**
- Deploy beta version on production infrastructure
- Support beta users through structured testing protocol
- Add semantic query capability ("ask the map" feature)
- Weekly check-ins with beta spaces: measure completion rates, identify friction
- Performance monitoring and optimization
- Document learnings and feature requests

**Deliverable:** Beta validation report proving engagement model works + refined prototype

**Hours:** 120h  
**Rate:** €80/h  
**Cost:** €9600

**Acceptance Criteria & Artifacts**
- [ ] Beta validation report (metrics + learnings)
- [ ] Semantic-query prototype (API + sample queries)
- [ ] Test dataset and example queries included
- [ ] ≥5 structured beta sessions documented

---

### Milestone 4: Extended Validation + Production Readiness (4 weeks) — €12800

**Team Activities:**
- Implement critical improvements from beta feedback
- Expand testing to all letter of intent supporters (7+ organizations)
- In-person validation sessions with partners (Gent, Rotterdam, Cologne, Lille/Paris)
- Build admin dashboard to measure freshness, usage patterns, performance
- Document technical architecture and deployment procedures (Docker container guide)
- Synthesize Round 1 learnings into Round 2 roadmap
- Prepare case studies from successful early adopters

**Deliverable:** Production-ready MVP + comprehensive validation report proving the commons engagement model sustains participation

**Hours:** 160h  
**Rate:** €80/h  
**Cost:** €12800

**Acceptance Criteria & Artifacts**
- [ ] Production deploy (repo/Docker + deploy instructions)
- [ ] Admin dashboard snapshot or access
- [ ] Final validation report with case studies (7+ partners)
- [ ] Runbook and maintenance docs submitted
- [ ] Smoke tests pass and partner onboarding evidence provided

---

## Infrastructure & Travel Costs

**Total:** €1500 (allocated across milestones)

### Hosting (€400)
- Production server for graph database queries
- EU-based providers: Hetzner (Germany) or HuggingFace (France)
- 3-month period with scaling capacity for beta testing

### AI/LLM Computation (€450)
- Semantic query processing via EU-compliant LLM
- Synthetic testing and benchmark validation
- Options: Mistral AI or HuggingFace Inference API
- Estimated usage: moderate query volume during beta + performance testing

### Travel & Validation Sessions (€650)
In-person validation visits with pilot partners within day-trip range from Brussels:
- **Gent, Belgium** (existing partner): €70
- **Rotterdam, Netherlands** (Peter Troxler): €140
- **Cologne, Germany** (VoW - Verbund offener Werkstätten): €140
- **Lille or Paris, France** (RFF network representative): €150
- Local public transport at each location: €50
- Buffer for additional coordination meetings: €100

**Travel scope:** 2 persons, Day trips only (train + lunch, no accommodation)  
**Geographic coverage:** BE, NL, DE, FR

### Communication & Tools (€0 - absorbed in milestone costs)
- Domain registration, SSL certificates, collaboration tools included in team overhead

---

## Budget Summary

| Milestone | Duration | Hours | Cost |
|-----------|----------|-------|------|
| M1: Solution Validation | 2 weeks | 80h | €6400 |
| M2: Walking Skeleton + Backup | 3 weeks | 120h | €9600 |
| M3: Beta Test + Iteration | 3 weeks | 120h | €9600 |
| M4: Extended Validation | 4 weeks | 160h | €12700 |
| Infrastructure & Travel | 12 weeks | - | €1500 |
| **TOTAL** | **12 weeks** | **480h** | **€39900** |

---

## Team Composition & Rate Justification

**Rate:** €80/hour (480 hours total)

Brussels 2025 senior developer rate for 2 co-leads working half-time commitment (20h/week each over 12 weeks).

**Core Team:**
- Jason Pettiaux (Project & Community Lead): ~240h
- Nicolas de Barquin (Technical Lead & Commons Architect): ~240h

**Budget Flexibility:**

We may allocate up to 80 hours within our 480h envelope for specialist consultations at market rates (€90-120/h). When we bring in specialists, we reduce our own hours proportionally to stay within budget. This approach lets us access expertise where needed while maintaining cost discipline.

Potential specialist areas:
- Graph database architecture review and optimization
- UX/onboarding design validation
- Production deployment and Docker container optimization

Round 1 will validate both our technical approach and where specialist support adds most value, directly informing Round 2 budget planning.

**Rate Justification:**
€80/hour baseline reflects Brussels 2025 IT consultant rates.
- General IT consultants in Belgium: €65-85/h (sources: Jellow, Malt, FreelanceNetwork)
- Senior developers (Java/.NET): €70/h average
- Specialist consultants (architecture, security): €90-120/h
- Our blended rate (€80/h) accommodates both core team work and occasional specialist support

---

## Other Funding

**Current:** None for this project specifically.

**In-kind Contributions:**
- VULCA network access for pilot recruitment
- Existing community relationships reducing cold-start risk
- 10+ years of domain expertise from founding OpenFab

**Future Funding Strategy:**
- **Round 2:** Scale to more networks (€40-50k, NLnet NGI Zero or similar)
- **Phase 3:** Skills + partnerships features (Erasmus+ KA220)
- **Phase 4:** Ecosystem governance transition (Fediversity or similar commons-focused funding)

---

## Why This Budget Works

✅ **Short validation cycles** - 2-4 week sprints enable rapid learning (fail fast, adjust)  
✅ **Balanced approach** - Technical development AND community validation funded equally  
✅ **Specialist flexibility** - Bring in expertise where needed without budget overruns  
✅ **Reasonable scope** - Walking skeleton with real user validation, not attempting full product  
✅ **In-person validation** - Travel budget enables trust-building with pilot partners  
✅ **Milestone-based payment** - Reduces risk for both parties, ensures accountability  
✅ **Infrastructure realism** - EU-based hosting, proven tools, no experimental dependencies  
✅ **Clear sustainability path** - Designed to inform Round 2, not dependent on endless grants

---

## Risk Mitigation

**Technical Risks:**
- Graph vs SQL decision validated in M1 before commitment
- IPFS tested early with fallback to simpler alternatives (rsync, torrents)
- Semantic queries proven with small dataset before scaling

**Community Risks:**
- Beta testing with real spaces in M3 validates engagement model
- In-person sessions build trust and gather honest feedback
- Multiple pilot networks reduce single-point-of-failure risk

**Budget Risks:**
- Milestone payments tied to deliverables prevent runaway costs
- Specialist flexibility allows expertise access without fixed overhead
- Infrastructure costs based on proven providers with transparent pricing
