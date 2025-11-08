# Competitive Analysis: Maps of Making

**Project:** Maps of Making - Federated Makerspace Network Intelligence
**Version:** 1.0 (NLNet MVP Phase)
**Date:** 2025-11-05
**Purpose:** Competitive positioning for NLNet application and consortium recruitment

---

## Executive Summary

**The Question:** How does Maps of Making differentiate from existing makerspace mapping platforms?

**The Answer:** We're not building another directory. We're building **network intelligence infrastructure** that solves the root cause of why maps fail: **no ongoing maintenance incentive + no ecosystem visibility.**

**Competitive Position:**
- **Direct competitors** solve "where are spaces?" (coverage)
- **Maps of Making** solves "is this current? who works with whom? can I trust this?" (intelligence + trust)

---

## Competitive Landscape

### Primary Competitors

1. **fablabs.io** (Fab Lab Network official directory)
   - 1,750+ labs globally
   - SQL database, location + basic metadata
   - Community-maintained but suffers from stale data
   - No freshness tracking, no relationship intelligence

2. **Hackerspaces.org Wiki** (Hackerspace community directory)
   - 2,000+ spaces globally
   - Wiki-based, prone to abandonment
   - No automated updates, no data validation
   - Community edit model (often outdated)

3. **Internet of Production (Open-Know-Where)** (analyzed in detail below)
   - 14,172 facilities from 14 aggregated sources
   - Equipment tracking (7,488 machines)
   - Static aggregation, 48-month data expiration
   - **Closest competitor in scope**

4. **Map-all-spaces (mapall.space)** (Community aggregator)
   - Aggregates SpaceAPI + fablabs.io + wiki sources
   - SQL backend, exports GeoJSON
   - No freshness tracking, read-only
   - Static snapshot approach

5. **SpaceAPI Implementations** (Distributed status feeds)
   - Individual spaces self-host status APIs
   - Real-time "open/closed" status
   - No aggregation layer, no relationships
   - Only works if space implements API

---

## Deep Dive: Internet of Production (Primary Comparison)

### What They Do Well

**Internet of Production** is the most comprehensive existing solution:

| Feature | Details |
|---------|---------|
| **Coverage** | 14,172 facilities globally (dominates Africa: 8,391 entries) |
| **Equipment Tracking** | 7,488 machines (3D printers, CNC mills, etc.) |
| **Multi-Source Aggregation** | 14 sources (FabLab, Hackerspaces, Make Works, etc.) |
| **Offline Data Submission** | KoboToolBox surveys support offline collection |
| **Embeddable Map** | iframe widget for external sites |
| **Country/Type Filtering** | Basic query filters (country, organization, machine type) |
| **Data Validation** | 48-month re-validation or discard policy |

**Strengths:**
- ✅ Largest dataset in the ecosystem
- ✅ Africa-focused (underserved region)
- ✅ Production-ready platform

---

### Where They Fall Short (Our Opportunity)

#### **1. Freshness Problem: Batch Deletion vs. Real-Time Trust**

| Internet of Production | Maps of Making (Our Advantage) |
|----------------------|-------------------------------|
| **48-month expiration** → data deleted | **Continuous decay model** → Fresh ✅ → Aging ⚠️ → Zombie 🧟 → Dead 💀 |
| "Re-validate or discard after 48 months" | Activity signals + community reports prove livelyness |
| No visibility into data age | **Transparent freshness** shown on every space |
| Binary (exists or doesn't) | **Gradual trust signal** (pheromone decay) |

**Why This Matters:**
- Users can't trust 14,172 facilities if data is 0-48 months old with no indication
- Our real-time freshness **builds trust** through transparency
- Activity webhooks prove spaces are actually alive **right now**

---

#### **2. Update Mechanism: Manual Gatekeeping vs. Self-Serve**

| Internet of Production | Maps of Making (Our Advantage) |
|----------------------|-------------------------------|
| Email DevOps officer for updates/removals | **Magic-link self-serve** (no account, 2 minutes) |
| Centralized bottleneck | **Decentralized maintenance** (spaces own their data) |
| Slow, manual processing | **Instant updates** visible on map |
| No verification loop | **Proactive verification campaigns** + activity signals |

**User Experience:**

**IoP Flow:**
1. User finds outdated info
2. Emails DevOps: "Please remove Lab X at Location Y"
3. Waits for manual processing
4. No confirmation when done

**Maps of Making Flow:**
1. Space receives magic-link email
2. Clicks link → pre-filled form
3. Updates in 2 minutes
4. Map refreshes instantly, freshness resets to ✅

**Why This Matters:**
- IoP's model **doesn't scale** (single DevOps bottleneck)
- Our model **incentivizes maintenance** (spaces see their reputation live)
- Community can report closures (crowd-sourced trust)

---

#### **3. Data Model: Directory vs. Network Intelligence**

| Internet of Production | Maps of Making (Our Advantage) |
|----------------------|-------------------------------|
| **Relational DB** (facilities + machines) | **Graph DB** (spaces + relationships + skills + partners) |
| Query: "Where is space X?" | Query: "Who collaborates with space X? What schools partner with fablabs in Portugal?" |
| No relationship data | **COLLABORATES_WITH, PARTNERS_WITH, HAS_SKILL** relationships |
| Equipment inventory only | **Skill flows, partnership networks, ecosystem intelligence** |

**Example Queries They Can't Answer:**

❌ "Which makerspaces collaborate with schools in Berlin?"
❌ "Show me the partnership network around Fab Lab Barcelona"
❌ "What spaces offer laser cutting AND work with NGOs?"
❌ "Map skill flows between fablabs in Eastern Europe"

**We Can Answer These** → This is our **core differentiator**.

**Why This Matters:**
- IoP is a **directory** (addresses on a map)
- We are **network intelligence** (who works with whom, what connects communities)
- This reveals the **invisible ecosystem fabric** that funders/researchers need

---

#### **4. Data Governance: Deletion vs. Immutable Ledger**

| Internet of Production | Maps of Making (Our Advantage) |
|----------------------|-------------------------------|
| Data **deleted** after 48 months | Data **never deleted**, marked dead with full history |
| No audit trail | **Immutable ledger** (who verified when, why marked dead) |
| No provenance tracking | Blockchain-inspired governance (all events logged) |
| No dispute resolution mechanism | **Transparency** enables community accountability |

**Example Transparency:**

**IoP:** "Lab X was deleted" (no history, no reason)

**Maps of Making:**
- "Lab X marked dead 💀 on 2025-11-05"
- "Reason: 3 community closure reports (2025-10-01, 2025-10-15, 2025-10-28)"
- "Last verified: 2024-02-12 by alice@network.org"
- "Full verification history: [view ledger]"

**Why This Matters:**
- **Transparency = trust** (users see why data changed)
- **Accountability = quality** (bad actors visible)
- **History = research value** (ecosystem evolution trackable)
- **NLNet loves this** (commons governance maturity)

---

#### **5. Community Trust: Top-Down vs. Bottom-Up**

| Internet of Production | Maps of Making (Our Advantage) |
|----------------------|-------------------------------|
| No community reporting | **Users report closures** (3+ reports → auto-dead) |
| No trust signals | **Freshness icons** (✅ ⚠️ 🧟 💀) visible to all |
| DevOps officer as single authority | **Distributed trust** (community + network admins) |
| Stale data invisible | **Zombie state** signals "unclear if alive" |

**Trust Mechanisms We Add:**

1. **Community Closure Reporting:**
   - User: "I visited, it's closed"
   - System: Records report, shows "1 closure report pending"
   - After 3 reports: Auto-marks dead 💀
   - Space can reopen → admin verification required

2. **Activity Signal Validation:**
   - Space pings API: "We're open today"
   - Freshness instantly resets to ✅
   - Proves livelyness (not just claims)

3. **Public Freshness Display:**
   - "Last verified 8 days ago ✅"
   - "Last verified 187 days ago 🧟" (zombie, check before visiting)
   - "Confirmed closed 💀" (don't waste your time)

**Why This Matters:**
- **Distributed trust > single gatekeeper**
- **Transparency > hidden data quality**
- **Accountability > hope data is current**

---

#### **6. AI/Agent Accessibility: Filters vs. Natural Language**

| Internet of Production | Maps of Making (Our Advantage) |
|----------------------|-------------------------------|
| Basic filters (country, type, machine) | **Natural language console** powered by LLM |
| Manual query construction | "Find spaces in Germany with laser cutting that partner with schools" |
| Not agent-ready | **A2A protocol + OpenAPI** (agents can query autonomously) |
| Human-only interface | **Human + AI accessible** |

**Demo Scenario for Pitch:**

**IoP User:**
1. Selects "Germany" from dropdown
2. Selects "Laser Cutting" from machine filter
3. Gets list of facilities
4. Manually searches descriptions for school partnerships
5. No way to query relationship data (doesn't exist)

**Maps of Making User:**
1. Types: "Show me spaces in Germany with laser cutting that partner with schools"
2. LLM queries graph database
3. Returns spaces + partnership network visualization
4. Highlights relationships on map

**Why This Matters:**
- **Non-technical users** can ask complex questions
- **Researchers** can query ecosystem patterns
- **Agents** can assist trip planning with fresh data
- **Proves A2A compatibility** (NLNet priority)

---

#### **7. Architecture: Centralized vs. Federated**

| Internet of Production | Maps of Making (Our Advantage) |
|----------------------|-------------------------------|
| Centralized server (assumed) | **Federated IPFS** + validator node model |
| Single point of failure | **Hot-swap** if hub fails (replicas exist) |
| Proprietary control | **Data commons** (Apache 2.0, anyone can fork) |
| No network replication | **Each network can host a replica** |

**Federated Model Benefits:**

1. **Resilience:** If main hub fails, networks' replicas keep serving data
2. **Sovereignty:** Networks control their own infrastructure
3. **Alignment with Ethos:** Decentralization matches maker movement values
4. **NLNet Requirement:** "Digital commons" = decentralized architecture

**Why This Matters:**
- **Sustainability:** Not dependent on single org/funding
- **Trust:** No vendor lock-in, data lives in commons
- **Scalability:** Networks share infrastructure costs
- **NLNet Criterion:** 40% of score is "strategic impact" = this alignment

---

## Feature Comparison Matrix

| Feature | fablabs.io | Hackerspaces.org | IoP | mapall.space | SpaceAPI | **Maps of Making** |
|---------|-----------|------------------|-----|--------------|----------|-------------------|
| **Coverage** | 1,750 | 2,000 | 14,172 | ~3,000 | Varies | 100-500 (MVP) → Scales |
| **Multi-source aggregation** | No | No | ✅ 14 sources | ✅ 3 sources | No | ✅ Network APIs |
| **Real-time freshness tracking** | ❌ | ❌ | ❌ (48mo batch) | ❌ | ✅ (per space) | ✅ **Continuous decay** |
| **Activity signals (webhooks)** | ❌ | ❌ | ❌ | ❌ | ✅ (self-hosted) | ✅ **Centralized + optional** |
| **Community closure reporting** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Self-serve updates (magic links)** | ❌ (admin) | ❌ (wiki edit) | ❌ (email) | ❌ (read-only) | ✅ (if implemented) | ✅ |
| **Network intelligence (graph)** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **Core feature** |
| **Natural language queries** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **A2A protocol compatibility** | ❌ | ❌ | ❌ | ❌ | Partial | ✅ **OpenAPI + LLM** |
| **Immutable audit ledger** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ |
| **Decentralized (IPFS)** | ❌ | ❌ | ❌ | ❌ | ✅ (self-hosted) | ✅ **Federated replicas** |
| **Embeddable widget** | ❌ | ❌ | ✅ iframe | ✅ | Varies | ✅ **Script tag** |
| **Equipment/skills tracking** | Partial | ❌ | ✅ Machines | ❌ | Partial | ✅ **Skills as graph nodes** |
| **Partnership/collaboration data** | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ **Graph relationships** |

**Key Insight:** We compete on **1 dimension** (coverage) and **over-achieve on 10 dimensions** (trust, intelligence, governance).

---

## Strategic Positioning

### What We're NOT Competing On

**❌ Coverage** (number of spaces listed)
- IoP has 14,172 facilities
- fablabs.io has 1,750 labs
- We start with 100-500 (pilot networks)

**Why:** Coverage is a **solved problem**. Aggregation is easy. The hard problem is **keeping data current and revealing ecosystem intelligence.**

---

### What We ARE Competing On

**✅ Trust** (is this data current?)
- Real-time freshness signals
- Community closure reporting
- Activity webhooks prove livelyness
- Transparent audit trail

**✅ Intelligence** (who works with whom?)
- Graph database reveals collaborations
- Partnership networks visible
- Skill flows trackable
- Ecosystem patterns discoverable

**✅ Accessibility** (how do I query this?)
- Natural language console
- Agent-ready API
- Complex relationship queries
- Non-technical user friendly

**✅ Governance** (who controls this?)
- Decentralized IPFS replication
- Immutable ledger transparency
- Community-driven maintenance
- Apache 2.0 (true commons)

**✅ Sustainability** (will this last?)
- Incentive alignment (spaces see value)
- Federated infrastructure (networks share cost)
- Open source (anyone can fork/extend)
- No single point of failure

---

## Pitch Narrative: Competitive Framing

### For Consortium Partners

> "**Internet of Production** aggregated 14,172 facilities from 14 sources. That's impressive coverage.
>
> But coverage isn't the problem. **Trust is the problem.**
>
> Their data is 0-48 months old with no indication of freshness. When it expires, it's deleted—no history, no accountability.
>
> **Maps of Making** solves what they can't:
> - **Real-time trust signals** (you know what's current)
> - **Network intelligence** (you see who collaborates with whom)
> - **Community governance** (distributed trust, not single gatekeeper)
> - **Agent accessibility** (natural language + A2A protocol)
> - **Federated commons** (data lives in the network, not on one server)
>
> We're not competing on size. We're competing on **quality, trust, and intelligence.**"

---

### For NLNet Application (Differentiation)

**Question:** "How is this different from existing makerspace maps?"

**Answer:**

> "Existing maps solve *where spaces are located*.
>
> **Maps of Making** solves:
>
> 1. **Why maps go stale** → We align incentives (spaces maintain data because it's their reputation + single source of truth)
>
> 2. **How to trust the data** → Real-time freshness (✅ ⚠️ 🧟 💀) + community reporting + activity signals
>
> 3. **What's the invisible network** → Graph intelligence reveals collaborations, partnerships, skill flows
>
> 4. **How agents access it** → Natural language console + A2A protocol (not just basic filters)
>
> 5. **Who controls it** → Federated IPFS (true commons) + validator node model (networks host replicas)
>
> **This is network intelligence infrastructure for the maker ecosystem, not another directory.**
>
> **Competitors aggregate data. We reveal the social fabric.**"

---

### For Funding Justification

**Question:** "Why fund this when Internet of Production already has 14,000+ facilities?"

**Answer:**

> "Internet of Production proved **coverage is achievable**.
>
> **But coverage without trust is useless:**
> - Their 48-month data expiration policy admits the problem (data goes stale)
> - Email-to-DevOps update model doesn't scale
> - No way to know if data is 2 days old or 47 months old
> - No relationship intelligence (just addresses on a map)
>
> **We're solving the NEXT problem:**
> - **Trust through transparency** (freshness visible + community accountability)
> - **Intelligence through graphs** (who works with whom?)
> - **Sustainability through incentives** (spaces maintain data because they see value)
> - **Decentralization through federation** (data lives in commons, not single server)
>
> **This is why NLNet should fund us:**
> - IoP is Web 2.0 (centralized directory)
> - **We're Web 3.0** (federated network intelligence with transparent governance)
>
> **We're not competing. We're evolving the ecosystem.**"

---

## Collaboration Opportunities

### We're Not Enemies—We're Partners

**Potential Collaboration with Internet of Production:**

1. **Data Exchange:** We can ingest their 14,172 facilities as a seed dataset
2. **Freshness Layer:** We add real-time validation on top of their aggregation
3. **Network Intelligence:** We add graph layer revealing relationships they don't track
4. **Federated Architecture:** We offer IPFS replication they can adopt

**Win-Win:**
- They get: Freshness tracking, network intelligence, federated resilience
- We get: Initial coverage boost, credibility, larger ecosystem impact

**Pitch to them:**
> "You've built the largest aggregation. Let's add the trust and intelligence layer that keeps it alive."

---

## Appendix: Competitive Quotes

### What Existing Maps Say (Their Own Words)

**Internet of Production:**
> "Data would be re-validated or discarded after 48 months from the initial date of data publishing."

**Translation:** They admit data goes stale, solution is deletion (not real-time validation).

---

**IoP on Updates:**
> "For updates/removals, users email the DevOps officer with specific details..."

**Translation:** Centralized bottleneck, doesn't scale, slow manual processing.

---

**fablabs.io (observed behavior):**
- Many labs haven't updated in 2-3 years
- No freshness indicators
- Users report: "showed up, lab was closed/moved"

**Translation:** Coverage ≠ trust. Data quality degrades over time without ongoing validation.

---

## Conclusion: The Opportunity Gap

**The Market Reality:**
- ✅ Coverage is solved (14,000+ facilities mapped)
- ❌ Trust is broken (data goes stale, no transparency)
- ❌ Intelligence is missing (relationships invisible)
- ❌ Governance is centralized (single points of failure)

**Our Positioning:**
- ✅ We're the **trust and intelligence layer**
- ✅ We solve the **incentive misalignment** (why maps go stale)
- ✅ We enable the **next generation** (agent-accessible, federated)
- ✅ We align with **commons values** (decentralized, transparent, community-governed)

**This is not a map. This is digital commons infrastructure for the maker ecosystem.**

---

_Document prepared for NLNet Commons Fund application and consortium pitch at Vulca Seminar 2025-11-05_

**Strategic Recommendation:** Lead with "We solve what they can't"—not "We have more features." Position as **evolution, not competition.**
