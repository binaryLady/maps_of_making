# User Personas & Use Cases: Maps of Making

**Document:** Primary reference for user research, design decisions, and feature prioritization
**Date:** 2025-11-11
**Version:** 1.0 (Brainstorm-locked)

---

## Overview

Maps of Making serves five distinct user personas, each with different needs and pain points. This document defines them to anchor design decisions and validate that features serve real users.

**Key Principle:** Personas are ordered by **MVP priority** (Tier 1 first).

---

## Persona 1: Individual Maker / Digital Nomad

### Profile
- **Who:** Freelance makers, researchers, travelers who need makerspace access in new cities
- **Technical Level:** Moderate (can navigate websites, use maps)
- **Primary Goal:** Find a trustworthy, currently-open makerspace to work on projects
- **Time Commitment:** 2-4 weeks per location typically

### Current Pain (Legacy Maps Fail)
- **Outdated listings:** Maps show spaces that closed 6 months ago
- **No freshness signal:** Can't tell if information is current or abandoned (except mainly hackerspaces on mapall.space trough API)
- **Wasted travel:** Arrives at address → space is gone/closed/moved
- **No context:** Equipment list says "3D printer" but doesn't know what are the requirements, nor if it's functional or blocked for weeks
- **No trust:** Can't determine why a space isn't responding to contact attempts

### What Maps of Making Unlocks
✅ **Freshness visible:** "This space verified 2 days ago ✅" = confidence to visit
✅ **Skill matching:** See what the community actually teaches: "8 professionals in metalworking, 5 advanced in electronics"
✅ **Partnership discovery:** "This space partners with 3 others nearby" → find collaborators
✅ **One click to verify:** Can message space directly from map detail view
✅ **Trust by ecosystem:** See which networks govern this space (reputable federation = safer choice)

### Typical Query
**"I'm in Brussels for 3 weeks. Where can I work on a metalworking project? I need advanced instruction."**

Maps of Making shows:
- Spaces in Brussels with advanced metalworking (filtered by skill + level)
- Verified within last 7 days ✅ (fresh)
- Partner spaces nearby (if stuck, can reach out to collaborators)
- Contact info + hours

---

## Persona 2: Researcher / Ecosystem Analyst

### Profile
- **Who:** Academics, policy researchers, journalists studying maker movements
- **Technical Level:** High (comfortable with APIs, data analysis)
- **Primary Goal:** Understand how maker ecosystems emerge, evolve, fail, and sustain
- **Time Commitment:** Multi-month or multi-year research projects

### Current Pain (Legacy Maps Fail)
- **No historical data:** When spaces close, they disappear → can't research failure patterns
- **No temporal analysis:** Can't answer "which regions lost spaces post-COVID?"
- **Location-only view:** No understanding of relationships, skill communities, collaboration patterns
- **Siloed data:** Each map has different spaces → no integrated ecosystem view
- **Dead ends:** Success stories don't tell failure stories → biased learning

### What Maps of Making Unlocks
✅ **Temporal data preserved:** Spaces marked "closed" with dates, reasons, relocation history
✅ **Time travel queries:** "Show me Belgian maker ecosystem in Jan 2020 vs today"
✅ **Failure pattern analysis:** "Which spaces closed? When? Owner changed hands?"
✅ **Skill evolution tracking:** "Did metalworking communities cluster before or after 'laserlab' opened?"
✅ **Growth trajectories:** "Which networks are expanding? Which consolidating?"
✅ **Graph-based insights:** Query partnerships, collaboration chains, ecosystem health metrics

### Typical Query
**"What conditions predict makerspace survival vs closure in EU cities? Which skill communities emerge first?"**

Maps of Making enables:
- Historical space data (births, deaths, transitions, relocations)
- Skill distribution analysis over time
- Partnership formation patterns
- Closure reasons anonymized + aggregated
- Export for academic analysis

**Neo4j advantage:** "Find all spaces that existed in 2024 but not 2025" = one graph query, not manual database work

---

## Persona 3: Space Operator / Network Coordinator

### Profile
- **Who:** Makerspace managers, network directors responsible for multiple spaces
- **Technical Level:** Low to moderate (comfortable with dashboards, not code)
- **Primary Goal:** Keep their network healthy, find growth opportunities, prevent closures
- **Time Commitment:** Ongoing (weekly coordination)

### Current Pain (Legacy Maps Fail)
- **No visibility into network:** Which spaces are aging/at-risk? Who's collaborating?
- **Scattered verification:** Update Fablab.io, then Hackerspaces.org, then regional map = 5+ copies
- **No feedback loop:** When I update data, I don't see impact or adoption
- **Collaboration invisible:** Don't know which spaces could partner with each other
- **Growth blindness:** Where should I recruit new spaces? What skills are missing?

### What Maps of Making Unlocks
✅ **One verification point:** Update once → visible everywhere globally
✅ **Health dashboard:** "3 spaces aging ⚠️, send outreach email this week"
✅ **Collaboration suggestions:** "Space A has advanced electronics + metalworking. Space B needs electronics mentoring. Suggest partnership?"
✅ **Skill gap analysis:** "Our network strong in woodworking, weak in textiles. Should recruit someone?"
✅ **Partnership incentives:** "Spaces with >5 partnerships have 40% higher retention"
✅ **Real-time reputation:** Fresh data = higher discoverability = more visitors
✅ **Network insights:** See which of my spaces are hubs vs isolated

### Typical Query
**"How healthy is my network? Where should I focus outreach? Who should partner with whom?"**

Maps of Making shows:
- Freshness distribution by space (aging alert system)
- Partnership recommendations (skill-based matching)
- Network-wide collaboration graph
- Verification history (who's engaged)
- Growth metrics (new spaces, trend data)

**Incentive alignment:** The more fresh your network's data, the more visible you are → natural motivation to maintain

---

## Persona 4: Potential Founder / New Space Planner

### Profile
- **Who:** Entrepreneurs, community organizers planning to launch a new makerspace
- **Technical Level:** Moderate (researches online, uses maps and dashboards)
- **Primary Goal:** Understand what works in my region; differentiate my space
- **Time Commitment:** Intensive 6-12 month planning phase

### Current Pain (Legacy Maps Fail)
- **Black box ecosystem:** Just lists existing spaces, no understanding of what's working
- **No collaboration potential:** Can't see if there are ready-made partner networks
- **Proven models hidden:** Which skill areas are saturated? Which are underserved?
- **Silence on failure:** Don't know why other spaces closed or moved
- **Regional isolation:** No way to see macro trends (is making growing or shrinking?)

### What Maps of Making Unlocks
✅ **Ecosystem gaps:** "Vienna strong in digital fab + wood, but weak in biolab + electronics"
✅ **Proven models:** "Spaces with strong partnerships in region X are more sustainable"
✅ **Temporal trends:** "Which skill areas are growing in Central Europe? 2023 vs 2025?"
✅ **Collaboration readiness:** "These 3 spaces collaborate. Could my space fit into that cluster?"
✅ **Failure learning:** Understand what happened to predecessor spaces, conditions for success
✅ **Differentiation clarity:** "I'll focus on textiles + biolab, which no one else in region does"

### Typical Query
**"I want to start a makerspace in Vienna. What's the landscape? How can I differentiate?"**

Maps of Making shows:
- Existing spaces + skill coverage
- Partnership clusters (natural alliances)
- Skill gaps (where to focus)
- Historical data (why did other spaces close/move?)
- Regional trends (is interest growing?)

---

## Persona 5: LLM / AI Agent

### Profile
- **Who:** Artificial intelligence agent assisting human users (via Mistral AI, Claude, etc.)
- **Technical Level:** N/A (but requires machine-readable API)
- **Primary Goal:** Answer natural language questions about makerspaces with context
- **Time Commitment:** Milliseconds per query

### Current Pain (Legacy Maps Fail)
- **Opaque data:** Can't reason about relationships, only retrieve locations
- **Stale information:** No freshness metadata → agent gives outdated advice
- **No semantics:** Equipment list string "laser cutting, 3D printer" is unstructured
- **Isolated spaces:** No way to recommend complementary partners
- **Unreliable:** Users get bad advice from stale data → trust erodes

### What Maps of Making Unlocks
✅ **Semantic queries:** "Find spaces where skill 'metalworking' is 'advanced' AND 'textiles' is taught"
✅ **Freshness filtering:** "Return only spaces verified within 7 days"
✅ **Reasoning capability:** "Space A + Space B together offer the full skill set needed"
✅ **Graph intelligence:** Recommend partnerships, collaborations, ecosystem clusters
✅ **Transparency:** Show user why this recommendation was made ("because they collaborate on...")
✅ **Structured data:** OpenAPI spec → auto-discovery of all capabilities

### Typical Query
**"What makerspaces in Germany combine advanced metalworking with textiles instruction?"**

Agent's internal reasoning:
```
1. Query API: spaces with skill "metalworking" @ "advanced" + skill "textiles"
2. Filter: freshness verified < 7 days
3. Check: are they connected via partnerships?
4. If not: recommend partnership opportunity
5. Return: recommended space + reasoning
```

**Result for user:** "ElektroLab in Berlin teaches advanced metalworking (verified 3 days ago). Nearby TextileWorks has strong textile instruction. They're not yet partnered—could be great match for you."

---

## Persona Priority Matrix

### MVP (Phase 1-2) Focus
**Tier 1 (Must serve):**
- Persona 1: Individual Maker (critical for discoverability)
- Persona 3: Space Operator (critical for data freshness incentive)

**Tier 2 (Should serve):**
- Persona 2: Researcher (builds NLNet case for ecosystem learning)
- Persona 5: LLM Agent (hero feature demonstrating graph intelligence)

**Tier 3 (Phase 2+):**
- Persona 4: Founder (nice-to-have; valuable for growth)

---

## Feature-to-Persona Mapping

| Feature | Individual Maker | Researcher | Space Operator | Founder | LLM Agent |
|---------|-----------|-----------|-----------|-----------|-----------|
| **Freshness indicators** | 🔴 Critical | 🟡 Important | 🔴 Critical | 🟡 Important | 🟡 Important |
| **Skills + levels (anonymized)** | 🔴 Critical | 🟡 Important | 🟡 Important | 🔴 Critical | 🟡 Important |
| **Partnerships graph** | 🟡 Important | 🔴 Critical | 🔴 Critical | 🟡 Important | 🔴 Critical |
| **Temporal data** | 🟢 Nice | 🔴 Critical | 🟡 Important | 🟡 Important | 🟢 Nice |
| **Natural language API** | 🟢 Nice | 🟡 Important | 🟢 Nice | 🟢 Nice | 🔴 Critical |
| **Embeddable maps** | 🟢 Nice | 🟢 Nice | 🔴 Critical | 🟡 Important | 🟢 Nice |
| **Admin dashboard** | 🟢 Nice | 🟢 Nice | 🟡 Important | 🟢 Nice | 🟢 Nice |

**Legend:** 🔴 Critical = must work for MVP | 🟡 Important = should work | 🟢 Nice = Phase 2+

---

## Interaction Flows by Persona

### Persona 1: "Find me a trustworthy space in a new city"

```
Flow: Individual Maker in Berlin
├─ Visit maps.making/embed or discover via network website
├─ Map shows: Berlin spaces, color-coded by freshness
├─ Click space "ElektroLab"
│  ├─ Detail card: address, skills (8 pro in electronics), hours
│  └─ Freshness: ✅ verified 2 days ago
├─ Click "View partners"
│  └─ See: TextileWorks (recommends collaboration)
├─ Decision: Trust this space → visit
└─ Result: Arrives to open, active, welcoming space
```

**Success metric:** Persona arrives at space during stated hours

---

### Persona 2: "Analyze EU makerspace failure patterns 2020-2025"

```
Flow: Researcher studying maker ecosystems
├─ Access: /api/spaces?temporal_date=2020-01-01 (timeline query)
├─ Query 1: "Which regions lost spaces post-COVID?"
│  ├─ Setup: Compare space counts 2020-01-01 vs 2025-11-01
│  ├─ Result: [Belgium -8%, Germany -3%, France -12%, Austria +5%]
│  └─ Insight: Southern/Western EU hit harder; Eastern growing
├─ Query 2: "What happened to Belgian spaces between 2020-2025?"
│  ├─ Closed: 8 spaces (dates, owners noted)
│  ├─ Survived: 34 spaces (how did they adapt?)
│  └─ Result: Closure spike March-June 2020, recovery slow
├─ Query 3: "Did partnerships help spaces survive COVID?"
│  ├─ Compare: Partnered spaces vs isolated spaces
│  └─ Result: Partnered spaces had 40% higher survival rate
├─ Query 4: "Which skill areas disappeared? Which emerged?"
│  ├─ Lost: Traditional workshops (high overhead)
│  └─ Gained: Home-scale digital fab, online mentoring
├─ Export: All results as JSON for analysis
└─ Publish: Academic paper on COVID's impact on maker resilience
```

**Success metric:** Researcher can answer temporal + causal questions without manual work

---

### Persona 3: "Keep my network healthy & growing"

```
Flow: Network coordinator weekly check
├─ Log in (magic link? or account? or local node?)
├─ Dashboard: "Network Health Overview"
│  ├─ Fresh ✅: 28 spaces (89% verified <30d) — great!
│  ├─ Aging ⚠️: 3 spaces (verified 31-60d) — send reminder
│  ├─ Zombie 🧟: 1 space (verified 90d+) — escalate call
│  └─ Dead 💀: 0 spaces
├─ Partnerships tab:
│  ├─ Active: 12 partnerships
│  ├─ Pending: 5 suggestions waiting for 2nd space to validate
│  └─ Recommendations: "Space A ↔ Space B could learn from each other (skill match)"
├─ Action: Send reminder email to aging space
├─ Action: Encourage pending partnership
└─ Result: Network becomes stronger, more visible globally
```

**Success metric:** Network freshness rate stays >80%, partnerships grow

---

### Persona 4: "Plan a new makerspace in Vienna"

```
Flow: Founder researching Vienna market
├─ Visit maps.making, center on Vienna
├─ View current ecosystem:
│  ├─ 12 existing spaces
│  ├─ Skills covered: strong in digital fab, weak in biolab
│  └─ Partnerships: 3 hubs with multiple partners
├─ Time travel: "Show me Vienna 2023 vs 2025"
│  ├─ 2023: 10 spaces, mainly digital fab focus
│  └─ 2025: 12 spaces, slight growth in woodworking
├─ Analysis: "Biolab underserved + growth interest"
├─ Decision: Differentiate as biolab + maker community
├─ Export: Ecosystem data for business plan
└─ Result: Informed strategy, lower risk launch
```

**Success metric:** Founder makes informed decision about differentiation

---

### Persona 5: "Agent answering user question"

```
Flow: User asks agent a question
├─ User: "What makerspaces near Berlin teach advanced electronics?"
├─ Agent: Calls Maps of Making API
│  ├─ Query: spaces near Berlin, skill:electronics, level:advanced
│  ├─ Filter: freshness < 7 days (recent verification)
│  ├─ Result: [ElektroLab, CircuitWorks]
├─ Agent reasons: "ElektroLab has 3 professionals, verified yesterday ✅"
├─ Agent checks partnerships:
│  ├─ ElektroLab partners with TextileWorks
│  └─ Could mention if user interested in textiles too
├─ Agent responds to user:
│  └─ "ElektroLab in Berlin teaches advanced electronics (verified yesterday).
│      They partner with TextileWorks if you're interested in both skills."
└─ Result: User gets trusted, current recommendation with context
```

**Success metric:** Agent query accuracy >95%, user satisfaction with recommendations

---

## Persona Validation Checklist

Before shipping Phase 1, validate each persona's primary use case works:

### Persona 1 (Individual Maker)
- [ ] Can find a space by city + skill
- [ ] Freshness status clearly visible
- [ ] Can contact space directly
- [ ] Partnership info helps discovery

### Persona 3 (Space Operator)
- [ ] One magic-link verification powers global discoverability
- [ ] Network dashboard shows health at a glance
- [ ] Partnership suggestions are useful
- [ ] Freshness decay nudges re-verification behavior

### Persona 2 (Researcher)
- [ ] Can query spaces by temporal date
- [ ] Closure reasons preserved (not deleted)
- [ ] Partnership history queryable
- [ ] Data exportable for analysis

### Persona 5 (LLM Agent)
- [ ] Natural language console works
- [ ] API returns fresh data filtered by skill
- [ ] Partnership recommendations available
- [ ] Response includes transparency/reasoning

### Persona 4 (Founder)
- [ ] Can see ecosystem gaps
- [ ] Partnership clusters visible
- [ ] Temporal trends apparent
- [ ] Export works for business planning

---

## Use Case References in Requirements

| Persona | Primary Use Case | PRD Reference | Architecture Section |
|---------|------------------|---------------|----------------------|
| Individual Maker | Find + trust makerspace | Journey 1, FR006-010, FR020-025 | Sections 2, 6, 7 |
| Researcher | Analyze ecosystem history | Epic 5, FR028-030, FR040 | Sections 2, 8 |
| Space Operator | Verify + coordinate network | Journey 1, FR011-017, FR031 | Sections 7, 11 |
| Founder | Understand market opportunity | Epic 2 (Market Intelligence) | Section 2 (Skills) |
| LLM Agent | Answer natural language Qs | Journey 3, FR009, FR034 | Sections 6, 9 |

---

## Next Steps

1. **Sprint Planning:** Link user stories to personas (ensures feature serves real users)
2. **UX Design:** Create wireframes for each persona's primary flow
3. **Validation:** Contact real users in each persona group (early feedback)
4. **Prioritization:** If trade-offs needed, prioritize Tier 1 personas

---

_Document prepared: 2025-11-11_
_Version: Locked for Phase 1 MVP planning_
