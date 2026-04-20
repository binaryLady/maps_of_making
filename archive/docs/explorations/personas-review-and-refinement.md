# Personas Review & Refinement

**Purpose:** Critical analysis of current personas and recommendations for refinement
**Date:** 2025-11-15
**Status:** Draft for discussion

---

## Current State Analysis

### Existing Personas (from `/docs/planning/PERSONAS.md`)

| # | Persona | MVP Tier | Primary Goal |
|---|---------|----------|--------------|
| 1 | Individual Maker / Digital Nomad | Tier 1 | Find trustworthy, currently-open makerspace |
| 2 | Researcher / Ecosystem Analyst | Tier 2 | Understand ecosystem evolution & patterns |
| 3 | Space Operator / Network Coordinator | Tier 1 | Keep network healthy, find partnerships |
| 4 | Potential Founder / New Space Planner | Tier 3 | Understand market gaps, differentiate |
| 5 | LLM / AI Agent | Tier 2 | Answer natural language queries with context |

---

## Critical Issues Identified

### Issue 1: Persona 1 Conflates Two Distinct User Types

**Current:** "Individual Maker / Digital Nomad"

**Problem:** These have fundamentally different needs:

| Aspect | Individual Maker (Local) | Digital Nomad (Traveler) |
|--------|--------------------------|--------------------------|
| **Time horizon** | Long-term (months/years) | Short-term (days/weeks) |
| **Relationship** | Wants community membership | Transactional access |
| **Key concern** | Community fit, skill progression | Immediate access, hours, freshness |
| **Frequency** | Regular (weekly) | One-time or occasional |
| **Location** | Single city | Multiple cities globally |
| **Decision factors** | Culture, long-term value, cost | Convenience, equipment, availability |

**Example Queries:**
- **Local Maker:** "Which space in Brussels has the best metalworking community for long-term learning?"
- **Digital Nomad:** "I'm in Brussels for 3 days. Which space is open tomorrow and has a laser cutter?"

**Recommendation:** Split into two personas

### Issue 2: Persona 3 Conflates Two Organizational Roles

**Current:** "Space Operator / Network Coordinator"

**Problem:** Different scope and responsibilities:

| Aspect | Space Operator | Network Coordinator |
|--------|----------------|---------------------|
| **Scope** | ONE space | MULTIPLE spaces (regional/global) |
| **Authority** | Manages operations | Strategic oversight |
| **Daily tasks** | Member management, equipment, events | Network health, policy, standards |
| **Data needs** | My space's visibility | Network-wide metrics |
| **Partnership focus** | Find partners for MY space | Facilitate partnerships across network |
| **Examples** | FabLab manager, makerspace director | Fab Foundation regional coordinator, OpenFab Network lead |

**Example Queries:**
- **Space Operator:** "How can I improve my space's visibility? Who should I partner with?"
- **Network Coordinator:** "Which of my 30 spaces are at-risk? Where should I focus resources?"

**Recommendation:** Split into two personas

### Issue 3: Missing Persona from MakerTour.fr Exploration

**Gap Identified:** Residency Seeker

**Who:** Makers seeking 1-week to 11-month residencies with accommodation/stipend support

**Different from Digital Nomad because:**
- Longer duration (weeks/months vs days)
- Requires accommodation, not just workspace
- Formal application process (deadlines, eligibility)
- Project-focused (not just using equipment)
- Often has specific support needs (visa, materials budget)

**Typical Query:**
"I'm a bioart maker looking for a 2-3 month residency in Europe with accommodation and lab access. What programs are open?"

**Data from MakerTour.fr:**
- 2,500+ spaces worldwide
- Residency programs ranging from 1 week to 11 months
- Support: accommodation, food, stipends (€50-360/month)
- Age/region restrictions common

**Recommendation:** Add as new persona OR merge into refined "Traveling Maker" persona

### Issue 4: Persona Priority May Need Adjustment

**Current MVP Tier 1 (Must serve):**
- Persona 1: Individual Maker / Digital Nomad
- Persona 3: Space Operator / Network Coordinator

**Question:** Should Network Coordinators be Tier 1?

**Arguments FOR Tier 1:**
- Network coordinators control MANY spaces (30-100+)
- If they adopt Maps of Making, their entire network joins
- High leverage: 1 coordinator = 50 spaces

**Arguments AGAINST Tier 1:**
- Fewer users (hundreds of coordinators vs thousands of operators)
- More complex needs (dashboard, analytics)
- Operators are gatekeepers (coordinators can suggest, but operators execute)

**Current thinking in docs seems right:** Operators are Tier 1, Coordinators could be Tier 2

### Issue 5: Potential Missing Personas

Based on ecosystem knowledge, consider:

#### 5a. Educator / Workshop Facilitator

**Who:** Traveling instructors who teach at multiple spaces

**Needs:**
- Skill gaps analysis ("Which spaces need electronics training?")
- Equipment inventory ("Do they have the tools I need?")
- Audience size ("Can they host 15 students?")
- Partnership discovery ("Which spaces could co-host a regional workshop?")

**Different from:**
- Researcher: Not analyzing, actively teaching
- Space Operator: Doesn't manage a space
- Digital Nomad: Not working on own projects, teaching others

**Typical Query:**
"I teach advanced PCB design workshops. Which spaces in Germany have reflow ovens but no one teaching SMD soldering?"

**Recommendation:** Consider for Phase 2+ (not MVP critical)

#### 5b. Equipment Seeker (Transactional User)

**Who:** Someone who just needs specific equipment, no community interest

**Needs:**
- Equipment search ("laser cutter with 600x400mm bed")
- Hourly availability
- Cost transparency
- Minimal friction (no membership required)

**Different from:**
- Local Maker: Not interested in community/learning
- Digital Nomad: Not traveling, just needs tool access

**Typical Query:**
"I need a laser cutter in Brussels for 2 hours this week. Where can I go?"

**Recommendation:** Consider for Phase 2+ OR merge into "Local Maker" as a sub-type

#### 5c. Corporate / Institutional Partner

**Who:** Companies, universities seeking space partnerships

**Needs:**
- Bulk access agreements
- Formal invoicing, insurance
- Student/employee training programs
- Innovation lab partnerships

**Different from all others:** B2B relationship, not individual

**Typical Query:**
"We want to partner with a Brussels makerspace for our engineering students. Need space for 50 students/year, formal partnership."

**Recommendation:** Phase 3+ (not MVP, but valuable for sustainability)

---

## Refinement Options

### Option A: Minimal Changes (Split Conflated Personas)

**6 Personas Total:**

1. **Local Maker** (Tier 1)
   - Community member seeking long-term space
   - Primary metric: Community fit, skill progression

2. **Traveling Maker** (Tier 1)
   - Digital nomads, short-term visitors
   - Primary metric: Freshness, immediate access

3. **Researcher / Ecosystem Analyst** (Tier 2)
   - Academic, policy research
   - Primary metric: Historical data, patterns

4. **Space Operator** (Tier 1)
   - Single-space manager
   - Primary metric: Visibility, local partnerships

5. **Network Coordinator** (Tier 2)
   - Multi-space oversight
   - Primary metric: Network health, strategic growth

6. **Potential Founder** (Tier 3)
   - Planning new space
   - Primary metric: Market gaps, differentiation

7. **LLM Agent** (Tier 2)
   - AI assistant
   - Primary metric: Query accuracy, reasoning transparency

**Pros:**
- Minimal disruption to existing docs
- Addresses main conflation issues
- Clear separation of concerns

**Cons:**
- Doesn't add MakerTour.fr residency use case
- 7 personas might be too many

### Option B: Add Residency Seeker (8 Personas)

**Same as Option A, plus:**

8. **Residency Seeker** (Tier 2)
   - Seeking 1-week to 11-month programs
   - Primary metric: Accommodation support, application deadlines

**Pros:**
- Addresses MakerTour.fr integration opportunity
- Distinct use case not covered by "Traveling Maker"

**Cons:**
- 8 personas is complex
- Residency feature not in Phase 1 (so why Tier 2?)

### Option C: Consolidate Around "Jobs to Be Done"

**Instead of personas, organize by core jobs:**

| Job | Who Does It | MVP Priority |
|-----|-------------|--------------|
| **Find a space to visit** | Local makers, travelers, nomads, equipment seekers | 🔴 P0 |
| **Maintain space visibility** | Operators, coordinators | 🔴 P0 |
| **Discover partnerships** | Operators, coordinators, founders | 🟡 P1 |
| **Understand ecosystem** | Researchers, founders, coordinators | 🟢 P2 |
| **Answer user questions** | LLM agents | 🟡 P1 |
| **Secure residency** | Residency seekers, nomads | 🟢 P2 |

**Pros:**
- Focuses on user NEEDS, not demographics
- Reduces persona proliferation
- Makes feature prioritization clearer

**Cons:**
- Loses empathy/narrative richness of personas
- Harder to visualize user journeys

### Option D: Hybrid - Core Personas + Jobs Matrix

**4 Core Personas:**

1. **Visitor** (finds spaces to use)
   - Sub-types: Local member, Short-term traveler, Residency seeker
   - Tier 1 (MVP critical)

2. **Operator** (maintains space data)
   - Sub-types: Single-space manager, Network coordinator
   - Tier 1 (MVP critical)

3. **Analyst** (studies ecosystem)
   - Sub-types: Researcher, Founder, Policy maker
   - Tier 2 (nice to have)

4. **Agent** (AI assistant)
   - Tier 2 (hero feature)

**Plus: Jobs-to-be-done matrix showing which personas care about which jobs**

**Pros:**
- Reduces from 7-8 to 4 manageable personas
- Acknowledges diversity via sub-types
- Keeps narrative power of personas
- Adds clarity of JTBD framework

**Cons:**
- Requires rewriting persona docs
- May lose some specificity

---

## Recommended Approach

### My Recommendation: **Option A (Split Conflated Personas)**

**Why:**

1. **Minimal disruption:** Builds on existing well-written personas
2. **Addresses real issues:** The conflations ARE problematic for feature design
3. **Maintains richness:** Each persona keeps its narrative depth
4. **Proven framework:** 6-7 personas is manageable (common in UX practice)
5. **Clear prioritization:** Tier 1 = Operators + Visitors, Tier 2 = Researchers + Coordinators + Agents

**Changes Required:**

**Persona 1a: Local Maker** (Tier 1)
- Someone building long-term relationship with local space
- Use case: "Find a makerspace community in my city for regular metalworking practice"
- Key features: Skill progression, community culture, partnership discovery
- Success metric: Becomes regular member (visits 2+ times/month for 6+ months)

**Persona 1b: Traveling Maker** (Tier 1)
- Digital nomad, conference attendee, short-term visitor
- Use case: "I'm in Berlin for 5 days, need laser cutter access tomorrow"
- Key features: Freshness, immediate availability, equipment search
- Success metric: Successful visit during stated hours, completes project

**Persona 3a: Space Operator** (Tier 1)
- Manager of single makerspace
- Use case: "Keep my space discoverable and find local partnerships"
- Key features: Magic-link verification, partnership suggestions, visibility metrics
- Success metric: Space stays fresh (<30 days), gains 1+ partnership

**Persona 3b: Network Coordinator** (Tier 2)
- Oversees 10-100+ spaces in a network
- Use case: "Monitor network health, identify at-risk spaces, facilitate collaborations"
- Key features: Dashboard, network metrics, strategic recommendations
- Success metric: Network freshness >80%, partnerships growing

**Keep as-is:**
- Persona 2: Researcher / Ecosystem Analyst (Tier 2)
- Persona 4: Potential Founder (Tier 3)
- Persona 5: LLM Agent (Tier 2)

**Handle MakerTour.fr:**
- Add "Residency Seeker" as **sub-type** of Persona 1b (Traveling Maker)
- Document residency use case in detail
- Mark residency features as Phase 2 (not MVP blocker)

---

## Specific Refinements Needed

### 1. Persona 1a: Local Maker (NEW - Split from P1)

**Profile:**
- **Who:** Local resident seeking regular makerspace access and community
- **Tech Level:** Beginner to advanced
- **Primary Goal:** Find a space where I can learn, grow skills, and belong
- **Time Commitment:** Long-term (6+ months), regular visits (weekly)
- **Geographic:** Single city/region

**Current Pain (Legacy Maps Fail):**
- Can't tell if space has active community or just equipment
- No signal of teaching quality or skill progression pathways
- Don't know if space culture fits (hobbyist vs professional, collaborative vs rental)
- Membership costs hidden, no transparency

**What Maps of Making Unlocks:**
✅ **Skill depth visible:** "8 professionals in metalworking teach here" = mentorship available
✅ **Community signals:** "5 active partnerships" = collaborative culture
✅ **Freshness:** Recent verification = space is active, not dormant
✅ **Progression pathways:** "Beginners start here, advance to PartnerSpace for CNC"
✅ **Trust via network:** "Member of Fab Lab Network" = quality standards

**Typical Query:**
"I want to learn metalworking in Brussels. Which space has the best teaching community for beginners?"

**Success Metric:**
- Visits space within 1 week of discovering on map
- Becomes regular member (2+ visits/month for 6+ months)
- Progresses skills (beginner → intermediate within 6 months)

### 2. Persona 1b: Traveling Maker (NEW - Split from P1)

**Profile:**
- **Who:** Digital nomad, conference attendee, traveling researcher
- **Tech Level:** Intermediate to advanced (self-sufficient)
- **Primary Goal:** Immediate access to equipment in unfamiliar city
- **Time Commitment:** Short-term (1 day - 4 weeks)
- **Geographic:** Multiple cities globally

**Current Pain (Legacy Maps Fail):**
- Outdated listings → wasted travel to closed spaces
- No freshness signal → can't trust information
- Hours unclear or wrong
- No idea if space allows drop-ins vs members-only

**What Maps of Making Unlocks:**
✅ **Freshness critical:** "Verified 2 days ago ✅" = safe to visit today
✅ **Real-time status:** If integrated with SpaceAPI, can see "open now"
✅ **Drop-in policy:** Metadata shows "visitors welcome" vs "members only"
✅ **Equipment confirmation:** "Laser cutter functional, verified yesterday"
✅ **Quick contact:** One-click message to confirm availability

**Typical Query:**
"I'm in Barcelona for 3 days. Which space is open Tuesday and has a functioning 3D printer?"

**Sub-type: Residency Seeker** (MakerTour.fr integration)
- Duration: 1 week - 11 months
- Needs: Accommodation, stipend info, application deadlines
- Formal application process
- **Example:** "I need a 2-month bioart residency in France with lab access and housing"

**Success Metric:**
- Finds verified space within 30 minutes
- Arrives during stated hours
- Completes project successfully
- (Residency sub-type: Secures accepted residency application)

### 3. Persona 2: Researcher / Ecosystem Analyst (KEEP, Minor Refinements)

**Refinement:** Add specific research questions

**Refined Typical Queries:**
1. "What conditions predict makerspace survival post-COVID?"
2. "Do partnerships correlate with space longevity?"
3. "Which skill communities emerge first in new maker ecosystems?"
4. "How does skill diversity correlate with space age?"
5. "What closure reasons are most common? (funding, lease, founder burnout)"

**Add Success Metrics:**
- Can export complete dataset for analysis
- Can answer causal questions (not just descriptive)
- Published research cites Maps of Making as data source

### 4. Persona 3a: Space Operator (NEW - Split from P3)

**Profile:**
- **Who:** Manager, director, or founder of single makerspace
- **Tech Level:** Low to moderate (comfortable with web forms, not code)
- **Primary Goal:** Keep my space visible, attract members, find collaborators
- **Time Commitment:** Ongoing (weekly updates ideal, monthly acceptable)
- **Scope:** ONE space

**Current Pain (Legacy Maps Fail):**
- Update 5+ directories separately (Fablab.io, Hackerspaces.org, regional maps)
- No feedback on whether updates help discoverability
- Don't know who else to partner with
- Can't see how my space compares to others

**What Maps of Making Unlocks:**
✅ **One update, global visibility:** Magic-link verification → all networks see it
✅ **Visibility feedback:** "You're in top 20% for freshness" = motivation
✅ **Partnership matchmaking:** "Space X wants to partner with you (87% skill match)"
✅ **Competitive context:** "3 other spaces in your city, but you're only one with biolab"
✅ **Incentive alignment:** Fresher data = higher search ranking = more visitors

**Typical Query:**
"How do I make my space more discoverable? Who should I partner with locally?"

**Success Metric:**
- Verifies space every 30 days (stays "fresh")
- Gains 1+ partnership in first 6 months
- Website traffic increases 20% from map referrals

### 5. Persona 3b: Network Coordinator (NEW - Split from P3)

**Profile:**
- **Who:** Regional coordinator, federation director overseeing 10-100+ spaces
- **Tech Level:** Moderate to high (uses dashboards, analytics, some API knowledge)
- **Primary Goal:** Ensure network health, strategic growth, cross-space collaboration
- **Time Commitment:** Weekly monitoring, monthly strategic planning
- **Scope:** MULTIPLE spaces (network-wide)

**Current Pain (Legacy Maps Fail):**
- No visibility into which spaces are at-risk
- Can't see network-wide partnership patterns
- Manual outreach to check if spaces still active
- No data-driven decision making for resource allocation

**What Maps of Making Unlocks:**
✅ **Health dashboard:** "28 fresh ✅, 3 aging ⚠️, 1 zombie 🧟" = prioritize outreach
✅ **Network metrics:** Partnership density, skill coverage, geographic gaps
✅ **At-risk alerts:** "Space Alpha hasn't verified in 60 days" = intervention needed
✅ **Strategic insights:** "Our network strong in digital fab, weak in textiles"
✅ **Partnership facilitation:** "Recommend Space A ↔ Space B collaboration"

**Typical Query:**
"Which of my 30 spaces need attention this month? Where are skill gaps in my network?"

**Success Metric:**
- Network freshness >80% (most spaces verified <30 days)
- Partnership count increases 15% year-over-year
- Zero zombie spaces (>90 days stale) after 6 months

### 6. Persona 4: Potential Founder (KEEP, Add Competitor Analysis)

**Refinement:** Add competitor analysis use case

**New Use Case:**
"If I open a makerspace in Vienna, how would I differentiate? What's the competitive landscape?"

**What Maps of Making Unlocks:**
✅ **Competitive density:** "12 existing spaces in Vienna"
✅ **Skill saturation:** "9 spaces have 3D printers (saturated), 0 have biolabs (gap!)"
✅ **Partnership readiness:** "3 spaces cluster together, could I join that network?"
✅ **Historical learning:** "2 spaces closed in 2020 due to high rent, be careful"
✅ **Differentiation clarity:** "Focus on biolab + textiles = zero local competition"

### 7. Persona 5: LLM Agent (KEEP, Add Transparency Requirements)

**Refinement:** Emphasize need for "reasoning transparency"

**Agent Response Format:**
```
User: "Find me a metalworking space in Brussels"

Agent (good response):
"I recommend **OpenFab** in Brussels:
- Advanced metalworking (3 professionals teach here)
- Verified 2 days ago ✅
- Partnership with BrusselsMakerspace for equipment sharing

I chose this because:
1. Recent verification = likely open
2. Professional instructors = quality teaching
3. Partnership = backup if OpenFab unavailable
"

Agent (bad response):
"Try OpenFab."  ← No reasoning, no trust
```

**Add Success Metric:**
- User accepts recommendation 80%+ of time (indicates trust)
- Agent response includes "reasoning transparency" (explains WHY)

---

## Use Case Refinements

### Make Use Cases More Specific and Testable

**Current Use Case (vague):**
"Find a trustworthy space in a new city"

**Refined Use Case (specific, testable):**
```
User Story:
"As a traveling maker visiting Brussels for 3 days,
I want to find a space with a laser cutter that's verified fresh
So that I don't waste time traveling to a closed or non-functional space"

Acceptance Criteria:
✅ Can filter by equipment type ("laser cutter")
✅ Can filter by freshness (verified <7 days)
✅ Can see hours and contact info
✅ Can navigate to space within 2 clicks from search
✅ Freshness indicator clearly visible (green badge)

Success Metric:
- User arrives at space during stated hours (95% success rate)
- Space has functional equipment (90% success rate)
```

**Apply this pattern to ALL use cases**

### Add Edge Cases

**Current:** Use cases assume "happy path"

**Add:**
- What if space is aging (30-60 days stale)? → Show warning, offer to contact space
- What if no spaces match query? → Suggest nearest alternatives, offer to expand radius
- What if partnership request declined? → Show alternative partnership suggestions
- What if user is in rural area? → Show "No spaces within 50km, nearest is..."

---

## Proposed Persona Priority Matrix (Revised)

| Persona | MVP Tier | Why | Phase 1 Features |
|---------|----------|-----|------------------|
| **1a. Local Maker** | **Tier 1** | Core user, long-term value | Search, skill filters, freshness, partnerships |
| **1b. Traveling Maker** | **Tier 1** | High urgency, freshness critical | Search, freshness, equipment, hours |
| **3a. Space Operator** | **Tier 1** | Data maintainers, incentive critical | Magic-link verify, partnership suggest |
| **2. Researcher** | Tier 2 | NLnet narrative, not daily user | Temporal queries, export |
| **3b. Network Coordinator** | Tier 2 | High leverage, but fewer users | Dashboard, network metrics |
| **5. LLM Agent** | Tier 2 | Hero feature, differentiator | Natural language console |
| **4. Potential Founder** | Tier 3 | Phase 2+, not urgent | Market gap analysis, trends |
| **1b-sub. Residency Seeker** | Tier 3 | Phase 2+, MakerTour.fr integration | Residency filter, accommodation |

**Tier 1 = Must work for MVP (Feb 2026)**
**Tier 2 = Should work for MVP, can be basic**
**Tier 3 = Phase 2+**

---

## Questions for Discussion

1. **Split Personas?**
   - Do you agree that "Individual Maker" and "Digital Nomad" should split?
   - Do you agree that "Space Operator" and "Network Coordinator" should split?

2. **Priority Ordering?**
   - Should Network Coordinators stay Tier 2 or move to Tier 1?
   - Is LLM Agent really Tier 2, or should it be Tier 3 (nice to have)?

3. **Missing Personas?**
   - Should we add "Residency Seeker" as standalone persona or keep as sub-type?
   - Should we add "Educator/Workshop Facilitator" now or later?
   - Any other personas we're missing?

4. **Use Case Specificity?**
   - Do current use cases need more acceptance criteria?
   - Should we add "edge case" scenarios?

5. **Framework?**
   - Stick with personas or switch to "Jobs to Be Done"?
   - Hybrid approach?

---

## Next Steps

Based on your feedback, I can:

1. ✅ **Rewrite PERSONAS.md** with split personas (Option A)
2. ⬜ **Create user story mapping** linking personas to Phase 1 features
3. ⬜ **Add acceptance criteria** to each use case
4. ⬜ **Update PRD** to reference refined personas
5. ⬜ **Create journey maps** for each Tier 1 persona

**Your turn:** What do you think? Which option resonates? Any personas we're missing?

---

_Document Status:_ Draft for discussion
_Estimated Review Time:_ 20-30 minutes
