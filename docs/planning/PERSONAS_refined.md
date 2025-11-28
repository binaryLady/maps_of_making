# User Personas: Maps of Making

**Version:** 3.1 (Mission-Based Consortia)
**Date:** 2025-11-16
**Status:** Production

**Strategic Focus:** Operators/Coordinators build Erasmus+ consortia through **mission alignment** (SDGs, topics, values), not skill matching. Skills = community impact evidence (Erasmus+ Phase 2 scope).

---

## 1. QUICK REFERENCE

### 9 Personas, 3 Tiers

| # | Persona | Tier | Job | Octalysis Drives |
|---|---------|------|-----|------------------|
| **1a** | Local Maker | 1 | Find community aligned with values | #5 Social, #1 Epic Meaning, #4 Ownership |
| **1b** | Traveling Maker | 1 | Find equipment now | #8 Avoidance, #6 Scarcity |
| **2a** | Space Operator | 1 | Keep space visible, define mission | #4 Ownership, #8 Avoidance, #1 Epic Meaning |
| **2b** | Network Coordinator | 1 | Build consortia, monitor health | #1 Epic Meaning, #4 Ownership, #8 Avoidance |
| **3** | Researcher | 2 | Study ecosystem patterns | #1 Epic Meaning, #3 Empowerment |
| **4** | LLM Agent | 2 | Answer NL queries | #3 Empowerment, #8 Avoidance |
| **5** | Potential Founder | 3 | Plan new space | #2 Accomplishment, #8 Avoidance |
| **6** | Educator | 3 | Find teaching opportunities | #1 Epic Meaning, #2 Accomplishment |
| **7** | Equipment Seeker | 3 | Find tools fast | #8 Avoidance |

**Tier 1 = Must work (MVP)** | **Tier 2 = Should work** | **Tier 3 = Phase 2+**

---

### Who Needs What (Feature Matrix)

| Feature | 2a | 2b | 1a | 1b | 3 | 4 | Priority |
|---------|----|----|----|----|---|---|----------|
| Freshness indicators | 🔴 | 🔴 | 🔴 | 🔴 | 🟡 | 🟡 | **P0** |
| Magic-link verification | 🔴 | - | - | - | - | - | **P0** |
| Network dashboard | - | 🔴 | - | - | - | - | **P0** |
| Basic map display | 🔴 | 🔴 | 🔴 | 🔴 | - | - | **P0** |
| Mission/SDG/Topics metadata | 🔴 | 🔴 | 🟡 | - | 🟡 | - | **P0** |
| Partnerships (mission-aligned) | 🔴 | 🔴 | 🟡 | - | 🔴 | 🔴 | **P1** |
| Search by mission/SDG | - | 🔴 | 🟡 | - | 🟡 | - | **P1** |
| Temporal queries | - | - | - | - | 🔴 | - | **P1** |
| Natural language API | - | - | 🟢 | 🟢 | 🟡 | 🔴 | **P1** |
| Skills (community growth) | 🟡 | 🟡 | 🟡 | - | 🔴 | - | **P2 (Erasmus+)** |
| Equipment filters | - | - | 🟡 | 🟡 | - | 🟡 | **P3+** |

🔴 Critical | 🟡 Important | 🟢 Nice-to-have

**Strategy:** 
- **P0:** Operators/coordinators build consortia (mission alignment, not skills)
- **P1:** Network partnerships documented
- **P2:** Skills = community impact evidence (Erasmus+ grant scope)
- **P3+:** Visitor optimization (organic once map fresh)

---

## 2. SPRINT PLANNING (10 Sprints)

### Sprint 1: Foundation (No user-facing)
- Data model (spaces, skills, partnerships)
- Freshness lifecycle algorithm
- Immutable ledger
- **Validates:** Technical feasibility

---

### Sprint 2: Basic Map + Mission Metadata
**Serves:** 2a Space Operator, 2b Network Coordinator

**Features:**
- [ ] Map display (OSM)
- [ ] List all spaces
- [ ] Freshness indicators
- [ ] Space detail view: name, address, hours, freshness
- [ ] **Mission statement field**
- [ ] **SDG tags (1-17)**
- [ ] **Topics/themes** (circular economy, digital inclusion, etc.)
- [ ] **Values/principles tags**

**Rationale:**
Consortia need to find partners by **mission alignment**, not skills. 
"Show me spaces working on SDG 12 (responsible consumption)" > "Show me spaces with metalworking"

**Octalysis Check:**
- ✅ Drive #4 (Ownership): Operators define their mission
- ✅ Drive #1 (Epic Meaning): Mission visible = purpose clear

**Acceptance Criteria:**
- [ ] All spaces render on map
- [ ] Freshness badge clearly visible
- [ ] Detail view shows mission + SDGs + topics
- [ ] Mission/SDG fields editable via verification form

**Test with:** 3 operators (define their mission), 1 coordinator (search by mission)

---

### Sprint 3: Verification (Core Incentive Loop)
**Serves:** 2a Space Operator

**Features:**
- [ ] Magic-link email system
- [ ] Verification form (<2 min workflow)
- [ ] Freshness countdown dashboard
- [ ] Status lifecycle (Fresh → Aging → Zombie → Dead)

**Octalysis Check:**
- ✅ Drive #8 (Avoidance): Countdown creates urgency
- ✅ Drive #4 (Ownership): "My space" dashboard
- ✅ Drive #2 (Accomplishment): Stay fresh = visible

**Acceptance Criteria:**
- [ ] Magic link arrives in <1 min
- [ ] Can update data in <2 min
- [ ] Dashboard shows countdown
- [ ] Edge case: 90 days stale → zombie recovery email

**Test with:** 5 space operators

---

### Sprint 4: Network Dashboard (Coordinator Tools)
**Serves:** 2b Network Coordinator

**Features:**
- [ ] Health overview (Fresh/Aging/Zombie/Dead counts)
- [ ] Freshness distribution
- [ ] Filter by freshness/region
- [ ] At-risk alerts

**Octalysis Check:**
- ✅ Drive #1 (Epic Meaning): "Stewarding 30 spaces"
- ✅ Drive #8 (Avoidance): Prevent network decay

**Test with:** 2 coordinators

---

### Sprint 5: Partnerships (Mission-Aligned Consortia)
**Serves:** 2a Space Operator, 2b Network Coordinator

**Features:**
- [ ] Partnership data model
- [ ] Bidirectional handshake
- [ ] Partnership suggestions by **mission/SDG alignment** (not skills)
- [ ] Display on map
- [ ] Search/filter: "Show spaces working on SDG 12"

**Rationale:**
Consortia form around **shared purpose**, not skill overlap. 
Erasmus+ KA220 needs partners with aligned missions, complementary approaches.

**Partnership Matching Logic:**
- Same SDGs = aligned purpose
- Complementary topics = diverse approaches
- Shared values = compatible culture

**Example:**
Space A: Mission = "waste reduction", SDG 12, circular economy
Space B: Mission = "upcycling textiles", SDG 12, circular economy
→ Consortium opportunity for circular maker education

**Octalysis Check:**
- ✅ Drive #1 (Epic Meaning): Shared mission = bigger purpose
- ✅ Drive #5 (Social): Collaborative culture visible

**Acceptance Criteria:**
- [ ] Can search "SDG 12 + circular economy"
- [ ] Partnership requires both spaces to accept
- [ ] Suggestions based on mission, not skills
- [ ] Partnerships visible on map

**Test with:** 3 operators, 1 coordinator building consortium

---

### Sprint 6: Embedding (Distribution)
**Serves:** 2a Space Operator, 2b Network Coordinator

**Features:**
- [ ] Embeddable widget (iframe)
- [ ] Parametrized URLs
- [ ] Embed code generator

**Octalysis Check:**
- ✅ Drive #4 (Ownership): Networks control view

**Test with:** 2 operators

---

### Sprint 7: API (Tier 2 Agent)
**Serves:** 4 LLM Agent

**Features:**
- [ ] RESTful API
- [ ] Natural language endpoint
- [ ] Semantic queries
- [ ] OpenAPI spec

**Test with:** Integration tests

---

### Sprint 8: Temporal (Tier 2 Researcher)
**Serves:** 3 Researcher

**Features:**
- [ ] Temporal queries
- [ ] Closure tracking
- [ ] Export (JSON, CSV)

**Test with:** 1-2 researchers

---

### Sprint 9: Visitor Optimization (1a/1b)
**Serves:** 1a Local Maker, 1b Traveling Maker

**Features:**
- [ ] Search by city + proximity
- [ ] Filter by mission/values (primary)
- [ ] Filter by freshness
- [ ] Contact forms
- [ ] Edge case handling (no results, stale data)
- [ ] (Optional) Skills as indirect equipment signal

**Rationale:**
Map is now fresh (operators engaged), visitors can trust it.
Visitors discover by **mission/values alignment** first, validate via skills/equipment.

**Why now:** 
Operators have defined missions (Sprint 2), partnerships visible (Sprint 5).
Visitors can find **communities they align with**, not just equipment.

**Acceptance Criteria:**
- [ ] Can search: "Circular economy + repair in Brussels"
- [ ] Mission/values visible on space detail
- [ ] Freshness <7 days prioritized
- [ ] Contact works
- [ ] Edge case: No matches → "Expand to [city]?"

**Test with:** 2 local makers, 1 traveling maker

---

### Sprint 10: Polish
**Serves:** All personas

- [ ] Performance optimization
- [ ] Edge cases
- [ ] Final validation

---

## Phase 2: Erasmus+ Scope

### Skills & Community Engagement
**Grant objective:** "How to engage community to measure skills and document growth"

**What Skills Are For:**

1. **Community representation (local stakeholders)**
   - "Our community grew 40% in biolab skills"
   - Show growth to commune, funders
   - Justify support/resources

2. **Research data (Tier 2 persona)**
   - Ecosystem learning: which skills cluster?
   - Temporal: how do communities evolve?
   - Failure patterns: skill diversity = resilience?

3. **Indirect equipment signal (Tier 1 visitors)**
   - "8 professionals in electronics" → probably has good equipment
   - Not explicit inventory, just inference

4. **Member journey documentation (internal)**
   - Level 1 game = members document own progression
   - Fablab tracks community learning
   - Erasmus+ reports need this data

**What Skills Are NOT For:**
- ❌ Partnership matching (use mission/SDG instead)
- ❌ Equipment inventory (websites have this)

**Features:**
- [ ] Skill taxonomy (collaboratively defined)
- [ ] Level 1 game integration (maker journey methodology)
- [ ] Community engagement strategy
- [ ] Proficiency measurement methodology
- [ ] Temporal skill tracking (growth over time)
- [ ] Dashboard for local stakeholders

**Why Erasmus+:** Requires community engagement research + methodology, not just tech

**Integration with Maker Journey:**
- Level 1 game teaches project planning
- Members document skills gained through projects
- Community growth visible for local representation
- Temporal data available for research

---

## Phase 3+: Advanced Features

- Equipment filters (websites already list this)
- Cost transparency
- Real-time status (webhooks)
- Temporal player UI

---

## 3. OCTALYSIS VALIDATION PER SPRINT

### Key Drives Strategy

**White Hat (Sustainable):**
- #1 Epic Meaning → Coordinators, Researchers
- #2 Accomplishment → Operators, Local Makers (real progress only)
- #3 Empowerment → Researchers, Agents

**Neutral:**
- #4 Ownership → **CRITICAL** for operators (data sovereignty)
- #5 Social → Collaborative signals (not competitive)

**Black Hat (Use Carefully):**
- #6 Scarcity → Only real scarcity (freshness urgency)
- #8 Avoidance → **KEY TO MVP** (honest warnings, not punishment)

### Red Flags (Don't Build)

**❌ Competitive leaderboards** (zero-sum thinking)
**❌ Paid boosts** (breaks commons model)
**❌ Gamification points** (fake accomplishment)
**❌ Public shaming** (toxic)
**❌ Artificial scarcity** (dishonest)

---

## 4. PERSONA DETAILS

### Tier 1: MVP Critical

#### 1a: Local Maker
**Who:** Local resident seeking regular makerspace access, long-term learning
**Job:** Find community where I can learn, grow skills, belong
**Time:** 6+ months, weekly visits

**Pain Points:**
- Can't tell if space has active community or just equipment
- Don't know if space mission/values align with mine
- No signal of teaching quality or community culture

**What We Unlock:**
- **Mission visible:** "Circular economy, waste reduction, repair"
- **Values clear:** "Community-driven, inclusive, open-source"
- **Community signals:** "5 active partnerships" = collaborative culture
- Freshness = space is active, not dormant
- **Indirect skill signal:** "8 professionals in electronics" → probably has good equipment

**Typical Query:**
"I want to learn electronics in Brussels. Which space has a community focused on repair and sustainability?"

**Success Metrics:**
- Visits space within 1 week
- Becomes regular member (2+ visits/month for 6+ months)
- Progresses skills (beginner → intermediate)

**Edge Cases:**
- No spaces match mission → Show "No exact matches. Expand to [city]?"
- Space aging (30-60 days) → Warning: "Data may be outdated. Confirm before visiting."
- All local spaces closed → "No active spaces in [city]. Nearest: [3 within 50km]"

---

#### 1b: Traveling Maker (Digital Nomad)
**Who:** Digital nomad, conference attendee, short-term visitor
**Job:** Immediate access to specific equipment in unfamiliar city
**Time:** 1 day - 4 weeks

**Pain Points:**
- Outdated listings → wasted travel to closed spaces
- No freshness signal → can't trust information
- Hours unclear or wrong
- Equipment listed but broken

**What We Unlock:**
- Freshness critical: "Verified 2 days ago ✅"
- Drop-in policy visible: "visitors welcome"
- Equipment confirmation: "Laser cutter functional"

**Typical Query:**
"I'm in Barcelona for 3 days. Which space is open Tuesday and has a functioning 3D printer?"

**Success Metrics:**
- Finds verified space within 30 minutes
- Arrives during stated hours (95% success rate)
- Equipment functional (90% success rate)

**Edge Cases:**
- Space open but equipment broken → "3D printer: under repair"
- No fresh spaces in city → "Recent verification not available. Contact these spaces to confirm"
- Rural area → "No spaces within 25km. Expand to 50km?"

**Sub-type: Residency Seeker** (Tier 3, Phase 2+)
- Duration: 1 week - 11 months
- Needs: Accommodation, stipend, application deadlines
- Query: "2-month bioart residency in France with housing"

---

#### 2a: Space Operator (Single-Space Manager)
**Who:** Manager/director of ONE makerspace
**Job:** Keep my space visible, attract members, find collaborators
**Time:** Ongoing (weekly updates ideal, monthly acceptable)

**Pain Points:**
- Must update 5+ directories separately
- No feedback on whether updates help
- Don't know who else to partner with
- Can't see how space compares

**What We Unlock:**
- One update, global visibility → all networks see it
- Visibility feedback: "You're in top 20% for freshness"
- Partnership matchmaking: "Space X wants to partner (87% skill match)"
- Incentive alignment: Fresher data = higher ranking = more visitors

**Typical Query:**
"How do I make my space more discoverable? Who should I partner with locally?"

**Success Metrics:**
- Verifies every 30 days (stays "fresh")
- Gains 1+ partnership in first 6 months
- Website traffic from map increases 20%

**Edge Cases:**
- Forgot to verify 90 days → Zombie status, recovery email
- Partnership request from incompatible space → Can decline with reason
- Space temporarily closed → Can set "temporarily closed" + reopen date
- Space relocated → Update includes "We moved to [address]" + date

---

#### 2b: Network Coordinator
**Who:** Regional coordinator overseeing 10-100+ spaces
**Job:** Ensure network health, build consortia, facilitate cross-space collaboration
**Time:** Weekly monitoring, monthly planning

**Pain Points:**
- No visibility into which spaces at-risk
- Can't find partners by mission alignment for Erasmus+ consortia
- Manual outreach to check if spaces active
- No data-driven decision making

**What We Unlock:**
- Health dashboard: "28 fresh ✅, 3 aging ⚠️, 1 zombie 🧟"
- Network metrics: Partnership density, mission alignment clusters
- At-risk alerts: "Space Alpha hasn't verified in 60 days"
- **Consortium builder:** "Show spaces working on SDG 12 in Belgium, France, Spain"
- Strategic insights: "Our network strong in circular economy, weak in digital inclusion"

**Typical Queries:**
- "Which of my 30 spaces need attention this month?"
- "Show spaces aligned on SDG 12 (responsible consumption) for KA220 consortium"
- "Which spaces have complementary missions to Space A?"
- "Where are mission gaps in our network?"

**Success Metrics:**
- Network freshness >80%
- Partnership count increases 15% year-over-year
- Zero zombie spaces after 6 months
- 2+ successful Erasmus+ consortia built per year

**Edge Cases:**
- Entire network declining → Dashboard highlights: "Freshness dropped 15% this quarter"
- Coordinator manages 100+ spaces → Pagination, bulk actions
- Space closes but coordinator unaware → Community report triggers alert
- Mission alignment unclear → Space prompted to clarify mission during verification

---

### Tier 2: Should Work for MVP

#### 3: Researcher / Ecosystem Analyst
**Who:** Academic, policy researcher studying maker movements
**Job:** Understand how ecosystems emerge, evolve, fail, sustain
**Time:** Multi-month or multi-year projects

**Pain Points:**
- No historical data → when spaces close, they disappear
- No temporal analysis → can't answer "which regions lost spaces post-COVID?"
- Siloed data → no integrated view
- Dead ends → success stories visible, failures erased

**What We Unlock:**
- Temporal data preserved: Spaces marked "closed" with dates, reasons
- Time travel queries: "Show Belgian ecosystem Jan 2020 vs Nov 2025"
- Failure pattern analysis: "Which spaces closed? When? Why?"
- Graph-based insights: Partnerships, collaboration chains

**Typical Queries:**
1. "What conditions predict makerspace survival post-COVID?"
2. "Do partnerships correlate with space longevity?"
3. "Which skill communities emerge first in new ecosystems?"

**Success Metrics:**
- Can export complete dataset
- Can answer causal questions (not just descriptive)
- Published research cites Maps of Making

---

#### 4: LLM / AI Agent
**Who:** AI assistant serving human users
**Job:** Answer natural language questions with accurate, current context
**Time:** Milliseconds per query

**Pain Points:**
- Opaque data → can't reason about relationships
- Stale information → no freshness metadata
- No semantics → equipment list is unstructured string
- Isolated spaces → can't recommend complementary partners

**What We Unlock:**
- Semantic queries: "Find spaces where skill 'metalworking' is 'advanced' AND 'textiles' is taught"
- Freshness filtering: "Return only spaces verified within 7 days"
- Reasoning capability: "Space A + Space B together offer full skill set"
- Graph intelligence: Recommend partnerships, collaborations

**Typical Query:**
"What makerspaces in Germany combine advanced metalworking with textiles instruction?"

**Success Metrics:**
- Query accuracy >95%
- User accepts recommendation 80%+ of time
- Agent responses include reasoning transparency
- Zero hallucinations about space status

---

### Tier 3: Phase 2+

#### 5: Potential Founder / New Space Planner
**Job:** Understand market opportunity, differentiate from competitors
**Phase:** Planning 6-12 months before launch

**What We Unlock:**
- Ecosystem gaps: "Vienna strong in digital fab, weak in biolab"
- Proven models: "Spaces with partnerships more sustainable"
- Temporal trends: "Which skill areas growing 2023-2025?"
- Failure learning: Understand what happened to predecessors

---

#### 6: Educator / Workshop Facilitator
**Job:** Find spaces needing teaching expertise, plan workshop tours
**Phase:** Ongoing (monthly workshops, regional tours)

**What We Unlock:**
- Skill gap analysis: "Which spaces have reflow ovens but no SMD training?"
- Equipment confirmation
- Partnership opportunities: "These 3 spaces could co-host regional workshop"

---

#### 7: Equipment Seeker (Transactional User)
**Job:** Find specific equipment, no community interest
**Phase:** One-time or occasional use (hours, not weeks)

**What We Unlock:**
- Equipment search: "Laser cutter with 600x400mm bed"
- Cost transparency: "Drop-in €15/hour, no membership required"
- Minimal friction: Contact space directly

---

## 5. APPENDIX

### A. Jobs-to-be-Done Summary

**7 Core Job Categories:**

1. **Discovery & Access** - Find and use spaces
   - 1.1 Find trustworthy space in new city
   - 1.2 Find local community by mission/values alignment
   - 1.3 Find specific equipment
   - 1.4 Secure residency program

2. **Visibility & Reputation** - Maintain discoverability
   - 2.1 Maintain space discoverability
   - 2.2 Demonstrate community liveness
   - 2.3 Communicate mission and values clearly

3. **Network Coordination** - Keep network healthy
   - 3.1 Monitor network health
   - 3.2 Build Erasmus+ consortia (mission-aligned)
   - 3.3 Identify strategic growth opportunities
   - 3.4 Allocate resources effectively

4. **Ecosystem Learning** - Understand patterns
   - 4.1 Understand what makes spaces succeed/fail
   - 4.2 Compare regional ecosystems
   - 4.3 Track ecosystem evolution over time
   - 4.4 Export data for academic analysis

5. **Agent-Assisted Discovery** - Answer NL queries
   - 5.1 Answer "where can I..." queries
   - 5.2 Recommend mission-aligned spaces
   - 5.3 Provide reasoning transparency
   - 5.4 Stay current with ecosystem changes

6. **Partnership Building** - Find collaborations
   - 6.1 Discover partnership opportunities by mission/SDG
   - 6.2 Formalize partnership (bidirectional)
   - 6.3 Showcase collaborations
   - 6.4 Dissolve partnerships gracefully

7. **Community Impact** - Document growth
   - 7.1 Measure community skill development
   - 7.2 Report to local stakeholders
   - 7.3 Track member journey (Erasmus+ documentation)

**Key Shift:** Partnerships form around **mission alignment** (SDGs, values, topics), not skill overlap. 
Skills = evidence of community growth, not matching criteria.

---

### B. Why Current Maps Fail (Octalysis Lens)

**Legacy Maps Activate:**
- Nothing. Zero game mechanics.
- No feedback loop
- No social proof
- No urgency

**Result:**
- Operators have no motivation to maintain
- Visitors have no trust signals
- Death spiral

---

### C. Why Maps of Making Works

**For Space Operators:**
- Drive #4 (Ownership): "My space, my reputation, my mission"
- Drive #8 (Avoidance): Freshness countdown = urgency
- Drive #2 (Accomplishment): Stay fresh, gain partnerships
- Drive #5 (Social): Reputation among peers
- **NEW:** Drive #1 (Epic Meaning): Mission visible = part of bigger purpose

**Result:** Operators WANT to verify (intrinsic motivation)

**For Network Coordinators:**
- Drive #1 (Epic Meaning): Stewarding commons, building consortia
- Drive #4 (Ownership): "My network"
- Drive #8 (Avoidance): Don't let network decay
- **NEW:** Mission-based search enables Erasmus+ consortium building
- **NEW:** Partnership facilitation by purpose, not just proximity

**Result:** Coordinators actively build consortia (strategic value)

**For Visitors:**
- Drive #8 (Avoidance): Don't waste travel
- Drive #5 (Social): Find right community fit
- **NEW:** Mission alignment = cultural compatibility
- **Secondary:** Skills = indirect equipment signal

**Result:** Visitors TRUST the data + find aligned communities

**For Researchers:**
- Drive #1 (Epic Meaning): Advance ecosystem understanding
- Drive #3 (Empowerment): Creative data exploration
- **NEW:** Skills data reveals community evolution patterns

**Result:** Research proves ecosystem learning possible

**Key Differentiator from Legacy Maps:**

**Legacy maps:**
- No mission/purpose metadata
- No incentive for operators
- No partnership facilitation
- Skills = not tracked
- Death spiral

**Maps of Making:**
- Mission/SDG-based search (consortia)
- Freshness incentive (visibility = motivation)
- Partnership documentation (network effect)
- Skills = community impact evidence (Erasmus+ scope)
- **Virtuous loop:** Fresh data → consortia → mobility → partnerships → fresh data

---

### D. Validation Checklist (Before MVP Launch)

**Tier 1 Personas:**

**Persona 1a (Local Maker):**
- [ ] Can find space by city + skill + proficiency
- [ ] Freshness clearly visible
- [ ] Partnership info accessible
- [ ] Edge case: No matches → alternatives shown

**Persona 1b (Traveling Maker):**
- [ ] Can filter by equipment + freshness
- [ ] Hours + drop-in policy visible
- [ ] Can contact space directly
- [ ] Edge case: Stale data → warning shown

**Persona 2a (Space Operator):**
- [ ] Magic-link verification <2 minutes
- [ ] Partnership suggestions appear
- [ ] Dashboard shows freshness countdown
- [ ] Edge case: 90 days stale → recovery email

**Persona 2b (Network Coordinator):**
- [ ] Dashboard shows all spaces + health
- [ ] Can filter by freshness, partnerships, region
- [ ] At-risk alerts work
- [ ] Edge case: 100+ spaces → pagination works

**Tier 2 Personas:**

**Persona 3 (Researcher):**
- [ ] Temporal queries work
- [ ] Closure data preserved
- [ ] Data exportable

**Persona 4 (LLM Agent):**
- [ ] API returns structured JSON
- [ ] Freshness in every response
- [ ] Partnership graph queryable

---

### E. Feature Gaps & Future Work

**Gap 1: Real-Time Status** (Phase 4)
- Needed by: Traveling Maker, Equipment Seeker
- Current: Freshness = "probably open"
- Future: Activity webhooks = "open now"

**Gap 2: Cost Transparency** (Phase 2)
- Needed by: Equipment Seeker, Traveling Maker
- Current: Must contact space
- Future: Cost fields (hourly rate, day pass, membership)

**Gap 3: Equipment Specs** (Phase 2)
- Needed by: Educator, Equipment Seeker
- Current: Generic list
- Future: Detailed specs (e.g., "laser: 600x400mm, 80W CO2")

**Gap 4: Tour Planning** (Phase 2)
- Needed by: Educator
- Current: Contact spaces individually
- Future: Multi-space contact, tour wizard

**Gap 5: Temporal Player UI** (Phase 4)
- Needed by: Researcher
- Current: API queries only
- Future: Interactive time scrubber, animation

---

### F. Two-Way Value: Maps of Making ↔ Maker Journey

**The fablab is a microcosm:**
"A fablab is a strange kind of nation. On any given day, you might have a retired engineer from Poland, a 19-year-old Belgo-British student learning 3D printing, a Belgian artist rethinking her practice, a middle-aged woman who just discovered soldering. Different backgrounds, cultures, ages, genders, past experiences and aspirations. We are literally Europe in miniature—with all the complexity that entails."

**Vision:**
"Transform the fablab into a European learning hub where members acquire, share, and transmit skills in Erasmus+ project management through practice, in a logic of pooling, inclusion, and open innovation. The fablab becomes a factory for Erasmus+ projects, supporting members to become actors in their own mobility and cooperation journey."

#### Maps of Making → Maker Journey

**Consortium building:**
- Network coordinators search partners by mission/SDG alignment
- "Show spaces working on SDG 12 (responsible consumption) in Belgium, France, Spain"
- Complementary missions, not skill overlap
- Partnership documentation for Erasmus+ applications

**Validation loop:**
- Erasmus+ projects = natural partnerships to document
- Members traveling = use cases for freshness validation
- Multi-space collaborations = prove partnership model works

**Example flow:**
1. Coordinator searches: "SDG 12 + circular economy"
2. Finds 3 aligned spaces (Belgium, France, Spain)
3. Proposes consortium for KA220
4. Partnership documented on map
5. Project validated → freshness maintained

#### Maker Journey → Maps of Making

**Solves the skills problem:**
- Erasmus+ game (Level 1) = methodology for skill documentation
- Members measure their own skills through project planning
- "How to engage community to measure skills" = Erasmus+ grant scope
- Game provides engagement strategy

**Active data generation:**
- Fablab projects create partnerships to document
- Member mobility validates freshness
- Community engagement = natural skill measurement
- Local representation: "Our community grew 40% in biolab skills"

**The loop:**
1. Member plays Level 1 (learns project planning)
2. Uses Maps of Making to find partner space
3. Goes on Erasmus+ mobility
4. Documents skills gained (feeds back to map)
5. Returns, creates partnership (documented on map)
6. Teaches next member (cycle repeats)

**Result:** Fablab becomes both **data generator** AND **consumer**. Self-reinforcing.

#### Skills Serve Multiple Jobs (Not Partnership Matching)

**1. Community representation (local stakeholders)**
- Dashboard: "Our community grew 40% in biolab skills 2024-2025"
- Show growth to commune, funders
- Justify continued support/resources

**2. Research data (Tier 2 persona)**
- Ecosystem learning: which skills cluster?
- Temporal: how do communities evolve?
- Failure patterns: skill diversity = resilience indicator?

**3. Indirect equipment signal (Tier 1 visitors)**
- "8 professionals in electronics" → probably has good electronics equipment
- Not explicit inventory, just inference
- Visitor discovers via mission first, validates via skills

**4. Member journey documentation (internal)**
- Level 1 game = members document own progression
- Fablab tracks community learning
- Erasmus+ reports need this data

**Skills are NOT for:**
- ❌ Consortium building (use mission/SDG instead)
- ❌ Equipment inventory (websites already list this)

#### Grant Strategy Integration

**NLnet (Phase 1 - Infrastructure):**
- Build for 2a/2b personas (operators, coordinators)
- Mission/SDG search for consortia
- Partnership documentation
- Freshness incentive model

**Erasmus+ (Phase 2 - Community Engagement):**
- "How to engage community to measure skills"
- Level 1 game = methodology (learning by doing)
- Skills data feeds:
  - Research (ecosystem patterns)
  - Local stakeholders (community growth)
  - Indirect equipment signals (visitor inference)

**Integration:**
- Consortia use mission/SDG search (NLnet infrastructure)
- Members use Level 1 game for skill documentation (Erasmus+ methodology)
- Skills data proves community impact (local representation)
- Partnerships validated through Erasmus+ projects (freshness loop)

#### Example: Complete Journey

**Fablab member Maria:**
1. Plays Level 1 game → learns project planning
2. Plans Erasmus+ mobility on "circular maker education"
3. Uses Maps of Making: searches "SDG 12 + circular economy in France"
4. Finds partner space with aligned mission
5. Goes on 2-week mobility, learns upcycling textiles
6. Documents skills gained (textiles: novice → intermediate)
7. Returns, creates partnership between spaces
8. Partnership documented on map
9. Both spaces verify (freshness maintained)
10. Maria teaches textile upcycling to 5 members
11. Community skills dashboard shows: "Textiles: 0 → 6 members"
12. Fablab shows commune: "New competency, growing community"
13. Next member sees Maria's journey, repeats cycle

**Virtuous loop:** Maps infrastructure enables mobility → Mobility creates data → Data proves impact → Impact justifies support → Support enables more mobility

---

### F. Personas NOT in Scope

**Corporate Partner** (Phase 3+)
- B2B relationship, different incentives
- Not critical for MVP

**Policy Maker / Government** (Phase 4+)
- High-level strategic view
- Not daily user

**Equipment Vendor** (Future)
- Commercial relationship
- Not part of commons model

---

_Document prepared: 2025-11-16_
_Version: 3.0 (Consolidated)_
_Status: Production_
