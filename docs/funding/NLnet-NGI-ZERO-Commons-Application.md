# NLnet NGI Zero Commons Fund - Application (DRAFT)

**Deadline:** December 1, 2025, 12:00 CET
**Call:** NGI Zero Commons Fund
**Status:** DRAFT - Ready for partner feedback and completion

---

## SECTION 1: CONTACT INFORMATION

### Your name
```
Jason Pettiaux
```

### Email address
```
jason.pettiaux@gmail.com
```

### Phone number
```
+32 493 53 11 24
```

### Organisation
```
[COMPLETE - Lead organization or network, or leave blank]
Vulca
```

### Country
```
Belgium
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
or pre-website on notion
https://plucky-beef-541.notion.site/Maps-of-Making-2b9bbd21f4c18078b0b6dc1e64c9daf0
```

---

## SECTION 3: ABSTRACT
**Character limit: 1200 characters (including spaces)**

**Question:** Can you explain the whole project and its expected outcome(s)?

### Draft

```
Makerspaces reinvent manufacturing from invention, prototyping to production, repair and recycling, they must work together. 

Maps of Making solves a critical failure in makerspace coordination: existing maps die because spaces update once and receive no sustained value in return. This misalignment wastes community effort and reduces overall ecosystem impact.

We're building a digital commons where fresh data unlocks ecosystem intelligence. The more communities contribute, the more useful the map becomes — creating a self-reinforcing value loop grounded in Elinor Ostrom's proven commons governance principles.

Round 1 validates this with diverse stakeholders who've confirmed their support. 8+ organizations have already committed letters of intent.

Key deliverables:

- Federated data commons with decentralized backup
- Freshness signals validating spaces maintain data because it delivers value
- Graph database enabling relationship queries SQL can't handle
- Semantic "ask the map" queries via EU-compliant LLM 

Success metric:

Provide a community database behaving like a true commons — useful, shared, and self-reinforcing.
```

**Character count:** 1,142 (max 1200) ✅

---

## SECTION 4: EXPERIENCE
**Character limit: 2500 characters (OPTIONAL but recommended)**

**Question:** Have you been involved with projects or organisations relevant to this project before? And if so, can you tell us a bit about your contributions?

### Status: WIP

**[TODO - Provide team member bios]**

Required for each team member:
- Name + Role
- Years of relevant experience
- 2-3 key projects / GitHub/portfolio links
- One sentence: Why relevant to this project?

```
Jason Pettiaux, Project & Community Lead: 5 years in healthcare product development, a complex stakeholder ecosystem; 5 years as Scout leader animating communities through flat governance, 2 years as Vulca Explorer building fablab networks across Europe and the world.

Nicolas de Barquin, ??? : 
10+ years founding and leading OpenFab Brussels. I experienced the classic commons tragedy: as the single maintainer, I burned out. Members relied on me to fix, teach, organize—and when I couldn't anymore, the space nearly closed. That failure sent me on a journey to understand why commons collapse, studying Ostrom's principles, game theory, and behavioral economics. "Maps of Making" is the system I wish had existed: designed so no single person becomes the bottleneck.
Built OpenFab on a €14k/year participation model—members contributed labor instead of high fees. The space survived 13 years including COVID, but still relied on key maintainers.
9 years participating in VULCA (European maker mobility network). This peer connections kept me functional — meeting fabmanagers facing the same struggles was like fresh air. We'd share solutions, learn from each other's experiments across cultures. It's why I lasted 10 years at OpenFab instead of burning out sooner.
5 years as Lead CAD Developer at EATOPS SA, designing telemetry systems for spacecraft and offshore platforms. Built predictive monitoring to catch silent failures before they became critical. That systems thinking—using historical data to anticipate problems—directly informs Maps of Making's temporal analysis layer.

Maps of Making sits at the intersection: I know why commons fail, what keeps maker communities alive, and how to build systems that prevent silent failures. This project is the convergence.
https://github.com/nicolasdb
```

**Character count:** 1807 (max 2500) ✅

---

## SECTION 5: REQUESTED SUPPORT

### Requested Amount

```
38300€
```
### Explain Cost
**Character limit: 2500 characters**

```
Budget covers 3-month intensive development and validation cycle with 4 milestone-based deliverables.

APPROACH:
Round 1 validates architecture choices through rapid iteration with real users. We run parallel technical and community tracks, testing both our technology decisions (graph vs SQL, decentralized backup) and engagement model (do spaces actually maintain data when it's useful?).

MILESTONE STRUCTURE (12 weeks):

M1: Solution Validation (2 weeks) — €6,400
Deliverable: Architecture decisions + user research confirming solution fit.

M2: Walking Skeleton + Backup (3 weeks) — €9,600
Deliverable: Working prototype ready for real user testing.

M3: Beta Test + Iteration (3 weeks) — €9,600
Deliverable: Beta validation proving engagement model works.

M4: Extended Validation (4 weeks) — €11,200
Deliverable: Production-ready MVP + validation report for Round 2.

Infrastructure & Travel: €1,500
Hosting (graph database performance), AI computation (semantic queries + benchmarks), travel for in-person validation sessions, communication tools.

RATE: €80/hour (460 hours total)
Brussels senior rate covering core team half-time commitment plus specialist consultations (graph architecture, UX design, deployment). Project management overhead included.

OTHER FUNDING:
None currently for this project. In-kind: VULCA network access, OpenFab infrastructure for testing, community relationships reducing cold-start risk.

Future strategy: Round 2 scaling (€40-50k NLnet/NGI), Phase 3 skills features (Erasmus+ KA220), Phase 4 governance (Fediversity).

WHY IT WORKS:

- Milestone payments reduce risk for both parties
- Short cycles enable rapid validation (fail fast, adjust)
- Both technical and community validation funded equally
- Specialist support when needed (we're not experts in everything)
- Reasonable scope: walking skeleton + validation, not full product
- Travel enables trust-building with pilot partners
- Clear sustainability path beyond grant funding
```

**Character count:** 1978 chars ✅ (max 2500)

---

## SECTION 6: COMPARISON WITH EXISTING EFFORTS
**Character limit: 4000 characters**

**Question:** Compare your own project with existing or historical efforts. What is new, more thorough or otherwise different?

### Draft

```
EXISTING LANDSCAPE:

Several platforms map maker ecosystems with varying approaches:
1. INTERNET OF PRODUCTION (IoP)
   - Largest coverage: 14,172 facilities
   - Equipment tracking: 7,488 machines
   - Strength: Comprehensive aggregation, production-ready
   - Limitations:
     * 48-month data expiration
     * No real-time freshness indicators
     * Manual updates via email to DevOps officer
     * Relational database: location-only queries, no relationship intelligence
     * Deleted data = lost history

2. FABLAB.IO & HACKERSPACES.ORG
   - 1,750+ fablabs, 2,000+ hackerspaces
   - Community-maintained but chronically stale

3. MAPALL.SPACE
   - Aggregates SpaceAPI + existing directories
   - Live data but read-only
   - Static snapshot approach

4. SPACEAPI (Distributed Status Protocol)
   - Individual spaces self-host real-time status APIs
   - Brilliant for "is space open now?"
   - Limited adoption

WHAT MAPS OF MAKING DOES DIFFERENTLY:

1. TRUST THROUGH TRANSPARENCY
   - Continuous freshness decay: Fresh ✅ → Aging ⚠️ → Zombie 🧟 → Dead 💀
   - IoP deletes after 48 months; we mark status changes with full history
   - Users see "verified 8 days ago" vs "unverified for 187 days"
   - Community closure reporting (3 reports → auto-dead, reversible with proof)
   - Activity webhooks prove liveness (not just claims)
   
   Why: Trust requires transparency. Batch deletion hides problems.

1. INCENTIVE ALIGNMENT
   - Magic links: 2-minute self-serve updates
   - Single source of truth → globally visible
   - Instant map refresh = proof of impact
   - Networks can't scale via email-to-DevOps model; we enable federated self-service
   
   Why: Existing maps fail because spaces have no reason to maintain data. We make maintenance effortless AND valuable.

1. NETWORK INTELLIGENCE
   - Graph database reveals ecosystem fabric (partnerships, collaborations, skill flows)
   - Queries impractical in SQL:
     * "Show partnership network around Fab Lab Barcelona"
     * "Find spaces with advanced electronics + textile instruction + NGO partnerships"
     * "Map skill flows between Eastern European fablabs"
   - Natural language console ("ask the map"): semantic queries via EU-compliant LLM
   - Agent-accessible via OpenAPI (A2A protocol compatible)
   
   Why: Directories show WHERE. We show WHO WORKS WITH WHOM and WHY. This is the invisible coordination layer funders and researchers need.

1. ECOSYSTEM LEARNING
   - Immutable ledger: spaces never disappear, marked dead with full audit trail
   - Closure reports preserved: "Lab X closed 2025-11-05, 3 community reports, reason: [view]"
   - Temporal queries: "Show ecosystem state in January 2024" or "Which spaces closed after pandemic?"
   - Research value: networks learn from failures, not just successes
   
   Why: Deleted data = lost knowledge. We preserve ecosystem history so communities learn from what worked and what didn't.

1. FEDERATED COMMONS GOVERNANCE
   - Decentralized backup : data survives individual failures
   - Networks can host validator replicas (no single point of control)
   - Apache 2.0 license: truly replicable for repair networks, tool libraries, any commons
   - Grounded in Ostrom principles: designed to sustain beyond grant funding
   
   Why: Platforms die when the operator loses interest. Commons governed by communities endure.

STRATEGIC POSITIONING:

We're not competing on coverage, we're competing on what coverage can't solve:
- Trust (is this data current?)
- Intelligence (who collaborates with whom?)  
- Accessibility (can agents query this?)
- Sustainability (will this outlive its creators?)

Internet of Production proved aggregation is achievable. We're solving the NEXT problem: keeping data alive, revealing invisible networks, enabling the federated coordination layer.

This isn't another map. It's network intelligence infrastructure for maker ecosystems—designed as digital commons.
```

**Character count:** 3928 chars ✅ (4000 max)

---

## SECTION 7: TECHNICAL CHALLENGES
**Character limit: 5000 characters (OPTIONAL but recommended)**

**Question:** What are significant technical challenges you expect to solve during the project, if any?

### Draft Technical Challenges (~4700 chars - with GitHub references)
/// TO REVIEW JASON
```
CHALLENGE 1: GETTING SPACES TO ACTUALLY MAINTAIN DATA

The hard part isn't a tech problem. It's human behavior. Every map platform dies because people update once and never come back. They don't get recurring benefits, so why bother? No amount of polish fixes that.

Our approach: 
- Make it stupidly easy to start and show immediate impact (map refreshes instantly, freshness resets to ✅). 
- Single source of truth made visible everywhere. They keep up-to-date their website, we automate ingestion into a persistant "common" easy to consult. 
- The system creates its own gravity.

The risk: 
If this doesn't work, nothing else matters. We validate with 5 beta spaces first, then expand to all pilot networks. 


CHALLENGE 2: MAKING IT A REAL COMMONS, NOT ANOTHER PLATFORM

We need the data to survive even if we disappear tomorrow. But blockchain is overkill, Git has merge conflicts, and Conflict-free replicated data type (CRDTs) are too complex. How do we get persistence without drowning in coordination protocols?

Our approach: 
One main database for fast queries. Periodic snapshot it to IPFS. Anyone can dockerize the snapshots. If the main hub dies, restore from IPFS. No consensus algorithms, no mining, no distributed writes. It's simpler than Git and way lighter than blockchain. If IPFS doesn't work, we fall back to rsync or torrents. The principle stays the same.

The risk: 
If we don't deliver decentralized backup, we're lying about the commons part. This gets tested in Milestone 2 with pilot networks running their own container.


CHALLENGE 3: CHOOSING STANDARDS WITHOUT OVER-ENGINEERING

GraphRAG with LLMs is straightforward to build. The challenge is picking standards that let us federate later without painting ourselves into a corner. But we can't spend Round 1 debating protocols.

Our approach: 
Build OpenAPI REST first. Test A2A protocol in week 2—if it works easily, use it. 
If not, stick with REST. Either way, prove that "ask the map" queries actually work. Natural language like "find spaces teaching electronics in Berlin partnered with NGOs" should just work.

The risk: 
Over-invest in standards = wasted time. Under-invest = proprietary mess later. We validate what works in Milestone 1, commit in Milestone 2.


CHALLENGE 4: EXTRACTING DATA FROM MESSY SOURCES

Some spaces will share clean CSV files. Others have barely-maintained websites with just "name + address" buried in text. We need to extract useful data from both without building a PhD thesis in NLP.

Our approach: 
Use LLMs to parse unstructured text. Pydantic schemas enforce baseline consistency (location and name are required, everything else is optional). Show extracted data to operators for confirmation—they know if it's right. Keep confidence scores so we know what's reliable.

The risk: 
If extraction quality is poor, manual curation becomes the bottleneck and we're back to the old problem. We test with 5-10 real sources in Milestone 1 to catch this early.

CHALLENGE 5: GETTING NETWORKS TO ACTUALLY PROMOTE IT 

Individual spaces are one thing. Convincing network coordinators to actively push our solution to 20-50 member spaces is different. That's organizational behavior change, and organizations are slow. 

Our approach: 
Co-design with coordinators before we build anything. Give them a dashboard showing "72% verified" as a network health metric. Provide newsletter templates and social assets so they don't have to write from scratch. Help them send the first batch. Make it obvious that fresh data = their network looks professional. 

The risk: 
This is existential. If networks don't promote it, the freshness model collapses and we've built nothing. Milestone 4 tests this by expanding to all 7+ pilot organizations.


THE REAL QUESTION:

These 5 challenges all ask the same thing: 
> Can we design a digital common that people actually maintain because it serves them, not because we're brute forcing it?

The tech serves the behavior. 
If spaces don't engage (Challenge 1), decentralized backup (Challenge 2) doesn't matter. 
If networks don't promote (Challenge 5), the standards we chose (Challenge 3) are irrelevant.
If data extraction is broken (Challenge 4), nobody gets value.

Round 1 validates the thesis:
"Well-designed commons outlive their creators."

As Ostrom’s work reminds us, systems endure when the people using them help shape the rules.  
As Bauwens shows, value grows when communities co-produce and steward shared resources.  
And as Rifkin argues, the digital era favors collaborative infrastructures over centralized ones.

If our database behaves like a true commons — useful, shared, and self-reinforcing —  
it won’t need to be forced.  
People will maintain it because it gives them power,  
not because it gives them work.
```

**Character count:** 4787 chars ✅ (5000 max)

---

## SECTION 8: ECOSYSTEM & ENGAGEMENT
**Character limit: 2500 characters**

**Question:** Describe the ecosystem of the project, and how you will engage with relevant actors and promote the outcomes?

### Draft Ecosystem & Engagement

```
WHO WE'RE WORKING WITH:

We've secured letters of intent from 7+ organizations spanning maker networks, individual spaces, and researchers—from European networks coordinating dozens of spaces to project-based initiatives. 
What they share: frustration with unreliable maps and excitement about network intelligence. They've committed to sharing data, promoting verification, and giving honest feedback.

HOW WE'LL ENGAGE:

Pilot Networks: Co-design in Milestone 1-2 through bi-weekly calls validating needs. More importantly: their spaces become discoverable across the entire ecosystem, not just one platform.

Individual Spaces: Progressive onboarding in three waves.

1.  Magic link asks "are you still open?" Verify location and status. 
This proves freshness with minimal effort.
No response? 
Space marked "zombie", then "dead".

2.  If alive, we ask consent to scrape their website. Scraping extracts deeper data (focus 
areas, partnerships, capabilities). Results shown to operator for validation—they curate what's accurate, building trust in the process.

3.  Test it yourself. "Ask questions about your space"—they know the answers, so they validate quality. Then: "Want to embed these results on your website?" Generate custom iframe. Now their data feeds back to them, visible to their visitors.

Researchers: We're reaching academia studying maker ecosystems. Plan interviews for deeper understanding of their needs and interests.

PROMOTING OUTCOMES:

Round 1 outcomes documented publicly: 
validation report with engagement metrics, case studies, technical architecture. We'll share through maker networks, academic channels, NGI events.

The best promotion is working infrastructure. If spaces verify because it serves them, networks will notice.

SUSTAINABILITY:

Networks self-sustain because single verification = ecosystem-wide visibility. Strength in numbers, not scattered effort across platforms. We're designing for community maintenance: Docker containers, clear docs, no proprietary dependencies.

Future funding: Erasmus+ for skills (Phase 2), Fediversity for scaling (Phase 3). But the 
core—spaces verifying data—runs on aligned incentives, not grant money.

The letters prove the need. Round 1 proves the model.
```

**Character count:** 2242 chars ✅ (2500 max)

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

_Maps of Making: Building a digital commons where communities maintain their own data because they own it._
