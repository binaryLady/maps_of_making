Budget Explanation

Requested Amount
€38,300

Rationale:

- 3-month intensive development + validation cycle
- 2 core team members half-time (~400 hours)
- Specialist support for critical technical decisions (~80 hours)
- Infrastructure & travel costs for in-person validation sessions
- 4 milestone-based deliverables with payment on completion

## Budget Structure

**Core Approach:**
Round 1 validates our architecture choices through rapid iteration with real users. We run two parallel tracks:

1. Technical Track: Build walking skeleton, test graph vs SQL, validate IPFS approach
2. Community Track: Interview operators, beta test onboarding, measure engagement

Both tracks inform each other through short 2-4 week cycles.

## Milestone Breakdown
**Milestone 1:** Solution Validation (2 weeks) — €6,400
Team Activities:

Compare graph database vs SQL for relationship queries
Prototype basic ingestion from real makerspace websites (3-5 sources)
Test onboarding flow concepts with 5 space operators
Validate core hypothesis: Would magic links + freshness signals actually drive sustained engagement?
Document architecture decisions and user feedback
Deliverable: Technical spike proving architecture choices + user research confirming solution addresses real needs
Hours: 80h
Rate: €80/h
Cost: €6,400

Milestone 2: Walking Skeleton + Decentralized Backup (3 weeks) — €9600
Team Activities:

Implement chosen architecture (graph database + ingestion pipeline)
Build basic map interface with freshness indicators
Add decentralized backup layer (IPFS or alternative)
Create magic link authentication flow
Design and prototype onboarding experience
Recruit 5 beta test spaces (mix: network-coordinated + permissionless)
Deliverable: Working end-to-end prototype with backup capability, ready for real user testing
Hours: 120h (includes specialist consultations)
Rate: €80/h
Cost: €9,600

Milestone 3: Beta Test + Iteration (3 weeks) — €9600
Team Activities:

Deploy beta version on production infrastructure
Support beta users through structured testing protocol
Add semantic query capability ("ask the map" feature)
Weekly check-ins with beta spaces: measure completion rates, identify friction
Performance monitoring and optimization
Document learnings and feature requests
Deliverable: Beta validation report proving engagement model works + refined prototype
Hours: 120h
Rate: €80/h
Infrastructure: Hosting + API costs (€1,500 for 3-month period, allocated across milestones)
Cost: €9600

Milestone 4: Extended Validation + Production Readiness (4 weeks) — €11200
Team Activities:

Implement critical improvements from beta feedback
Expand testing to all letter of intent supporters (7+ organizations)
In-person validation sessions with partners within 250km of Brussels
Build admin dashboard to measure freshness, usage patterns, performance
Document technical architecture and deployment procedures (Docker container guide)
Synthesize Round 1 learnings into Round 2 roadmap
Prepare case studies from successful early adopters
Deliverable: Production-ready MVP + comprehensive validation report proving the commons engagement model sustains participation
Hours: 140h (includes specialist consultations)
Rate: €80/h
Travel costs: In-person visits to validation partners
Cost: €11200

Infrastructure & Travel Costs (3 months)
Hosting:

Production server (may require higher performance for graph queries): €200
Options: Hetzner (Germany) or HuggingFace (France) for EU compliance
AI/LLM Computation:

Semantic query processing + synthetic testing for benchmarks: €500
Options: Mistral AI or HuggingFace inference API
Travel (~250km radius from Brussels):

In-person validation sessions with pilot partners: €500
Covers 2-3 site visits for deep user research
Communication & Miscellaneous:

Domain, SSL, collaboration tools: €300
Total Infrastructure & Travel: €1,500

(Integrated across milestones, primarily M3 and M4)

Budget Summary
Milestone	Duration	Hours	Cost
M1: Solution Validation	2 weeks	80h	€6,400
M2: Walking Skeleton + Backup	3 weeks	120h	€9,600
M3: Beta Test + Iteration	3 weeks	120h	€9,600
M4: Extended Validation	4 weeks	140h	€11,200
Infrastructure & Travel	12 weeks	-	€1,500
TOTAL	12 weeks	460h	€38,300
Rate Justification
€80/hour baseline (Brussels senior developer rate). Covers:

Core team time (half-time commitment each)
Specialist consultations (graph DB architecture, UX design, deployment infrastructure)
Project management and coordination overhead
Other Funding
Current: None for this project specifically.

In-kind contributions:

VULCA network access for pilot recruitment
OpenFab Brussels infrastructure for testing
Existing community relationships reducing cold-start risk
Future funding strategy:

Round 2: Scale to more networks (€40-50k, NLnet or NGI)
Phase 3: Skills + partnerships features (Erasmus+ KA220)
Phase 4: Ecosystem governance (Fediversity or similar)
Why This Budget Works
Short cycles = rapid validation (fail fast, adjust quickly)
Balanced approach - technical development AND community validation funded equally
Specialist support included - we bring in expertise where needed
Reasonable scope - walking skeleton with real user validation, not full product
Travel budget - in-person sessions with pilot partners build trust and deeper insights
Infrastructure flexibility - EU-based options (HuggingFace, Hetzner) for compliance