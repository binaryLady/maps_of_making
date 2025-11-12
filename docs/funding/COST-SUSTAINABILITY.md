# Cost & Sustainability Model: Maps of Making

**Document:** Long-term cost analysis, operational sustainability strategy, funding roadmap
**Date:** 2025-11-11
**Version:** 1.0 (Phase 1 planning; Phase 2-3 research required)
**Status:** Framework + scenarios; detailed costs TBD after pilot network data

---

## Executive Summary

Maps of Making is **designed to be self-sustaining without extractive revenue models.**

**Key principle:** Development is always consortium-funded (work packages); operational costs are distributed across participating networks.

| Phase | Development | Operations | LLM Costs | Total/Year |
|-------|-------------|------------|-----------|-----------|
| **Phase 1 (MVP)** | €18,555 (NLNet) | Distributed | €420 (Mistral) | €18,975 |
| **Phase 2-3** | €15-25k (Consortium) | Distributed | €0-200 (SLM) | €15-25k |
| **Phase 4+** | Ongoing (Consortium) | Distributed | €0 (Self-hosted) | Varies |

**Sustainability mechanism:** No central funding required after MVP. Costs absorbed into network infrastructure budgets.

---

## 1. MVP Costs (Phase 1 - NLNet Round 1)

### Development (One-Time)

| Item | Cost | Duration | Rationale |
|------|------|----------|-----------|
| **M1: Backend Engine** | €5,200 | Weeks 1-3 | Neo4j + FastAPI + IPFS foundation |
| **M2: Domain Adaptation** | €4,000 | Weeks 4-5 | Pydantic schemas + data ingestion + magic-link auth |
| **M3: Map Interface** | €3,840 | Weeks 6-7 | Leaflet.js + verification form + freshness tracking |
| **M4: Integration & Deploy** | €2,880 | Week 8 | Testing + IPFS backup + production deployment |
| **Subtotal (Dev)** | **€15,920** | 8 weeks | Senior developer rate €80/hr |

### Infrastructure (One-Time Setup)

| Item | Cost | Purpose |
|------|------|---------|
| **Hetzner VPS (8 weeks)** | €20 | Main node consolidation server |
| **Mistral AI API** | €225 | ~30k requests (embeddings + LLM queries) |
| **Domain + SSL** | €0 | Already secured |
| **Subtotal (Infra)** | **€245** | 8-week deployment |

### Contingency

| Item | Cost | Purpose |
|------|------|---------|
| **Buffer (15%)** | €2,420 | Velocity variations, technical challenges |

### **GRAND TOTAL (Phase 1)**

```
€15,920 (dev) + €245 (infra) + €2,420 (contingency) = €18,585
Requested: €18,555 ✅
```

**Funding source:** NLNet NGI Zero Commons Fund

---

## 2. Operational Costs (Post-MVP)

### Model: Distributed Node Architecture

**Each network/space runs:**
- Docker image `:latest` (same codebase, distributed)
- Neo4j instance (locally or cloud-hosted)
- Nightly: publishes data → main node consolidates → IPFS backup
- Queries: Route to nearest/fastest node (via IPFS + local replicas)

**Cost distribution:**
```
Maps of Making (Central)
├─ Main node (minimal): €20-30/month
├─ IPFS pinning: €20-50/month
└─ Operational: €10-20/month
Total: €50-100/month

Per Network (Distributed)
├─ Docker instance (Hetzner/cloud): €30-50/month
├─ Neo4j resource: Included in hosting
├─ Bandwidth: €5-10/month
└─ Maintenance labor: TBD (Phase 2)
Total: €35-60/month per network
```

### Scenario A: 5 Networks, ~50 Spaces Each (250 Total)

**Maps of Making Infrastructure**
```
Central (nightly consolidation):
├─ Main node (€25/month)
├─ IPFS pinning (€30/month) [GraphML export ~50MB/night]
├─ Mistral AI (Phase 1 only): €35/month
└─ Operational overhead: €15/month
Total: €105/month = €1,260/year

Per Network (if they self-host)
├─ VPS instance: €40/month × 5 = €200/month
├─ Bandwidth: €7/month × 5 = €35/month
└─ Local maintenance: In-kind (volunteer/staff time)
Total: €235/month = €2,820/year

COMBINED ANNUAL COST: €4,080
Cost per space: €16.32/year = €1.36/month per space
```

### Scenario B: 10 Networks, ~100 Spaces Each (1,000 Total)

**Maps of Making Infrastructure**
```
Central:
├─ Main node (€30/month) [higher traffic]
├─ IPFS pinning (€50/month) [larger GraphML exports]
├─ Mistral AI (Phase 1): €35/month
└─ Operational: €20/month
Total: €135/month = €1,620/year

Per Network (10 networks)
├─ VPS instance: €45/month × 10 = €450/month
├─ Bandwidth: €10/month × 10 = €100/month
└─ Local maintenance: In-kind
Total: €550/month = €6,600/year

COMBINED ANNUAL COST: €8,220
Cost per space: €8.22/year = €0.68/month per space
```

### Scenario C: 20 Networks, ~150 Spaces Each (3,000 Total)

**Maps of Making Infrastructure**
```
Central:
├─ Main node (€40/month) [distributed traffic routing]
├─ IPFS pinning (€80/month) [large-scale snapshots]
├─ Mistral AI (Phase 1): €35/month
└─ Operational: €25/month
Total: €180/month = €2,160/year

Per Network (20 networks)
├─ VPS instance: €50/month × 20 = €1,000/month
├─ Bandwidth: €12/month × 20 = €240/month
└─ Local maintenance: In-kind
Total: €1,240/month = €14,880/year

COMBINED ANNUAL COST: €17,040
Cost per space: €5.68/year = €0.47/month per space
```

**Key insight:** Cost per space **decreases** as scale increases (economies of scale). Distributed model is **more efficient** than centralized hub.

---

## 3. LLM Cost Evolution

### Phase 1 (MVP - NLNet): Mistral API

**Cost:** ~€35/month = €420/year

**Usage model:**
```
Natural language queries: "Find spaces with advanced electronics"
  ├─ LLM generates Cypher query
  ├─ Executes on local Neo4j
  └─ Returns results

Token estimate:
├─ Query generation: ~500 tokens/query
├─ Typical usage: 2,500 queries/month
└─ Cost: ~€10-15/month (at Mistral pricing)
```

**Limitations:**
- Cost scales with query volume
- Potential for token abuse (users asking non-map questions)
- Vendor lock-in to Mistral

---

### Phase 2-3: Migrate to Self-Hosted SLM

**Cost:** €0/month (after Phase 2 development)

**Model:**
```
Second Docker image: Ollama + fine-tuned Cypher generation model

1. Download base model (e.g., Llama 3.1, ~7B parameters)
2. Fine-tune on Maps of Making Cypher queries
3. Deploy locally on each network's node

Hardware requirements:
├─ CPU-only: Intel i5 + 16GB RAM (€0, reuse existing hardware)
├─ GPU (optional): NVIDIA T4 (~€0.35/hour on cloud = €250/month)
└─ Recommended: CPU-only for cost-efficiency
```

**SLM advantages:**
- ✅ Zero token cost (runs locally)
- ✅ No vendor lock-in
- ✅ Privacy-preserving (no data sent to external API)
- ✅ Can be fine-tuned for Maps-specific tasks
- ⚠️ Slightly lower quality (7B vs 70B models)
- ⚠️ Requires local compute

**Usage pattern:**
```
User: "Find spaces with advanced electronics + textiles"
  ↓
Local SLM: Generates Cypher query
  ↓
Neo4j: Executes, returns JSON
  ↓
Map UI: Displays results
  ↓
(User can export + continue in their own LLM if needed)
```

**Cost impact:**
```
Phase 1: €420/year (Mistral API)
Phase 2: €0/year (SLM on existing hardware)
Savings: €420/year
```

---

### Phase 3-4: Advanced LLM Features (Out of Scope for Round 1)

**Deferred questions:**
- Can 7B SLM generate accurate Cypher for complex queries?
- What's the fine-tuning cost / development effort?
- Should GPU acceleration be recommended or optional?
- How to prevent SLM hallucination (confidence thresholds)?

**Action:** Phase 2 pilot will measure SLM quality vs Mistral, inform Phase 3 investment.

---

## 4. Decentralization Economics

### Central Hub Model (Traditional)

```
Infrastructure:
├─ Main server (Hetzner): €50/month
├─ CDN/failover: €30/month
├─ Support: €20/month
└─ LLM: €35/month
Total: €135/month = €1,620/year

Characteristics:
✅ Simple to operate
✅ Fast queries (single source)
❌ Single point of failure
❌ Extractive (platform owns data)
❌ Centralized cost on one party
❌ Doesn't scale with community participation
```

### Distributed Node Model (Maps of Making)

```
Infrastructure (shared):
├─ Main consolidation node: €30/month (light workload)
├─ IPFS pinning: €40/month (backup + distribution)
├─ Operational: €20/month
└─ LLM: €35/month (Phase 1 only)
Total Central: €125/month = €1,500/year

Infrastructure (distributed across networks):
├─ 5 networks × €40/month = €200/month = €2,400/year
├─ 10 networks × €40/month = €400/month = €4,800/year
├─ 20 networks × €40/month = €800/month = €9,600/year

Cost per space (distributed):
├─ 5 networks (250 spaces): (€1,500 + €2,400) / 250 = €15.60/year
├─ 10 networks (1,000 spaces): (€1,500 + €4,800) / 1,000 = €6.30/year
├─ 20 networks (3,000 spaces): (€1,500 + €9,600) / 3,000 = €3.70/year

Characteristics:
✅ No single point of failure (if main drops, replicas serve)
✅ Costs distributed across stakeholders
✅ Communities own infrastructure
✅ Scales efficiently (more networks = lower per-space cost)
✅ Aligns with Ostrom commons principles
❌ Higher total operational cost (redundancy)
❌ More complex to coordinate
❌ Requires network commitment
```

### Cost-Benefit Analysis

| Metric | Central | Distributed (5 networks) | Distributed (20 networks) |
|--------|---------|--------------------------|---------------------------|
| **Annual Cost** | €1,620 | €3,900 | €11,100 |
| **Cost per Space** | €6.48/year | €15.60/year | €3.70/year |
| **Resilience** | ❌ Single point | ✅ Highly resilient | ✅ Highly resilient |
| **Community Ownership** | ❌ Platform-owned | ✅ Networks own | ✅ Networks own |
| **Governance** | ❌ Top-down | ✅ Polycentric | ✅ Polycentric |
| **Data Sovereignty** | ❌ Proprietary | ✅ Open commons | ✅ Open commons |

**Key insight:** Distributed model costs **more in absolute terms** but costs **less per space** at scale AND provides resilience + community ownership.

**Justification for networks:** "You're paying €30-50/month anyway for your infrastructure. Adding a Maps of Making node costs €10 more, and you get global visibility + data sovereignty."

---

## 5. Sustainability Strategy

### Development Costs (Always Consortium-Funded)

**Principle:** Feature development is treated as work packages in larger consortium projects.

| Phase | Funding Source | Duration | Budget | Work Package |
|-------|----------------|----------|--------|--------------|
| **Phase 1 (MVP)** | NLNet NGI Zero Commons | 8 weeks | €18,555 | Data federation + map + verification |
| **Phase 2** | Erasmus+ KA220 (Consortium) | 12 weeks | €20-30k | Embeddable widgets + governance layer |
| **Phase 3** | Fediversity or similar | 12 weeks | €15-25k | Decentralized scaling + SLM migration |
| **Phase 4+** | Future NGI calls / Fediversity | Ongoing | €10-20k/year | Feature development + maintenance |

**Rationale:** Development is **public goods work**, suitable for public/grant funding. Not dependent on commercial revenue.

---

### Operational Costs (Network Dues / Self-Hosting)

**Post-NLNet sustainability model:**

**Option A: Voluntary Participation (Recommended)**
- Networks that benefit from visibility + data ownership contribute infrastructure costs
- Cost: €30-50/month per network (their own VPS)
- Maps of Making covers: central consolidation + IPFS + coordination
- Result: Self-sustaining at scale (3+ networks)

**Option B: Sponsorship Model (Backup)**
- If networks can't contribute, seek sponsorships from:
  - Makerfed (if interested in ecosystem health)
  - European Commission (NGI initiatives)
  - Community foundations (maker-friendly)
- Covers: Central infrastructure + IPFS
- Risk: Dependent on grant cycles

**Option C: Hybrid (Most Likely)**
- Networks contribute infrastructure (€30-50/month each)
- Foundation/sponsors cover central consolidation (€50-100/month)
- Result: Shared responsibility, aligned incentives

---

### Cost Reduction Over Time

**Phase 1 → Phase 4 cost trajectory:**

```
Phase 1 (MVP):
├─ Development: €18,555 (NLNet)
├─ Operations: €50/month central + network self-hosting
├─ LLM: €35/month (Mistral)
└─ Total: €18,555 + €1,020 = €19,575 first year

Phase 2:
├─ Development: €25k (Consortium grant)
├─ Operations: €70/month central + network self-hosting
├─ LLM: €35/month (still Mistral, but testing SLM)
└─ Total: €25k + €1,260 = €26,260 first year

Phase 3:
├─ Development: €20k (Consortium grant)
├─ Operations: €80/month central + network self-hosting
├─ LLM: €0/month (SLM deployed, Mistral phase-out)
└─ Total: €20k + €960 = €20,960 first year

Phase 4+ (Steady State):
├─ Development: €10-15k/year (maintenance + new features)
├─ Operations: €100/month central + network self-hosting
├─ LLM: €0/month
└─ Total: €10-15k + €1,200 = €11,200-16,200/year
```

**By Phase 4:** Development is optional (funded via consortium), operations are self-sustaining across network community.

---

## 6. Admin Dashboard Requirements

### Purpose
Track costs, performance, and usage to enable cost projections and inform Phase 2-3 planning.

### Priority 1: Cost Tracking (Weekly)

**Central infrastructure costs:**
```json
{
  "mistral_ai": {
    "weekly_tokens": 45000,
    "weekly_cost": €0.23,
    "monthly_projection": €35,
    "queries": 1250
  },
  "hetzner": {
    "monthly_cost": €25,
    "resource_usage": {
      "cpu": "45%",
      "memory": "62%",
      "storage": "38%"
    }
  },
  "ipfs_pinning": {
    "monthly_cost": €30,
    "snapshot_size_mb": 52,
    "snapshots_stored": 30
  }
}
```

**Network-reported infrastructure costs:**
```json
{
  "networks": [
    {
      "name": "Brussels Network",
      "reported_vps_cost": €40,
      "reported_maintenance_hours": 5,
      "spaces": 28
    },
    // ... more networks
  ],
  "aggregate": {
    "total_network_cost": €235,
    "total_network_hours": 25,
    "cost_per_space": €0.94
  }
}
```

### Priority 2: Usage & Performance (Weekly)

**Query volume + performance:**
```json
{
  "api_requests": {
    "spaces_queries": 1250,
    "partnerships_queries": 340,
    "skill_queries": 890,
    "nlm_queries": 120
  },
  "average_response_times": {
    "spaces_query": "45ms",
    "partnerships_query": "78ms",
    "nlm_query": "340ms"
  },
  "token_usage": {
    "embeddings": 25000,
    "chat_completions": 20000,
    "total_cost": €0.23
  }
}
```

### Priority 3: Data Quality (Daily)

**Freshness + engagement metrics:**
```json
{
  "spaces": 250,
  "freshness_distribution": {
    "fresh": "68%",
    "aging": "22%",
    "zombie": "8%",
    "dead": "2%"
  },
  "verification_rate": {
    "verified_last_30d": "89%",
    "trend": "↑ +3% from previous week"
  },
  "partnership_adoption": {
    "spaces_with_partnerships": "34%",
    "pending_suggestions": 23
  }
}
```

---

## 7. Phase 2-3 Research Questions

**Technical questions deferred; must be answered via pilot measurement:**

### Question 1: Node Ranking & Traffic Routing
- **Metric for ranking:** API response time? Uptime? Throughput?
- **Routing mechanism:** DNS round-robin? API gateway? Client-side?
- **Cost impact:** How much bandwidth does routing add?
- **Owner:** To be determined in Phase 2 spike

### Question 2: Main Node Selection
- **Is main different from other nodes?** Or just highest-ranked?
- **Who operates main?** Us initially, or rotates among networks?
- **Cost of main:** Minimal (just consolidation) or significant?
- **Owner:** Architecture decision in Phase 2

### Question 3: IPFS as Source of Truth
- **Role:** Immutable backup, or live data vault?
- **Consistency model:** Eventual consistency OK?
- **Alternatives:** P2P replication? CRDTs?
- **Cost impact:** How much pinning cost for 14k+ spaces?
- **Owner:** To validate in Phase 2 proof-of-concept

### Question 4: Local SLM Requirements
- **Hardware:** CPU-only or GPU recommended?
- **Model size:** 7B sufficient, or need larger?
- **Fine-tuning:** How many Cypher examples needed?
- **Quality:** Compared to Mistral, acceptable accuracy?
- **Owner:** ML spike in Phase 2

---

## 8. Scenario Summary & Breakeven

### Breakeven Analysis: When Is System Self-Sustaining?

**Assumptions:**
- Phase 1 (NLNet): €18,555 one-time dev cost
- Phase 2-3: €40k additional dev cost (consortium-funded)
- Operational cost: €100/month central + network self-hosting

**Scenarios:**

**Scenario: 5 Networks, 250 Spaces**
```
Year 1 costs:
├─ Phase 1 dev: €18,555 (NLNet) ✓ Funded
├─ Phase 2 dev: €20k (Consortium) ✓ Funded
├─ Operations: €1,260 (central) + €2,400 (network) = €3,660
└─ Total: €42,215 (funded via grants)

Year 2 costs:
├─ Phase 3 dev: €20k (Consortium) ✓ Funded
├─ Operations: €1,260 (central) + €2,400 (network) = €3,660
└─ Total: €23,660 (funded via grants)

Year 3+:
├─ Phase 4 dev: €12k/year (Consortium) ✓ Funded
├─ Operations: €1,260 (central) + €2,400 (network) = €3,660
└─ Breakeven: YES (operational costs covered by network budgets)
```

**Scenario: 10 Networks, 1,000 Spaces**
```
Year 1: €42,215 (dev + operations)
Year 2: €26,620 (dev + operations)
Year 3+: €15,620/year (dev + operations, all funded)

Breakeven by Year 2 for operational sustainability.
```

**Scenario: 20 Networks, 3,000 Spaces**
```
Year 1: €42,215
Year 2: €26,620
Year 3+: €16,260/year

Even faster payback. More networks = stronger financial health.
```

---

## 9. Funding Roadmap

### Phase 1: NLNet NGI Zero Commons (Dec 2025 - Feb 2026)

**Funding:** €18,555 (NLNet Round 1)
**Focus:** MVP proof-of-concept
**Deliverable:** Working map + verification system + 3-5 pilot networks

---

### Phase 2: Erasmus+ KA220 (Spring 2026 - Winter 2026)

**Objective:** Scale to 10+ networks + governance layer
**Budget:** €20-30k (estimate; to be refined)
**Work packages:**
- Embeddable widgets + network-branded views
- Admin dashboard + cost tracking
- Governance models + community coordination
- SLM pilot + fine-tuning infrastructure

**Funding strategy:**
- **Lead applicant:** Consortium coordination body (TBD)
- **Co-applicants:** 2-3 pilot networks
- **Alignment:** EU digital sovereignty + commons governance

---

### Phase 3: Fediversity or NGI Data Commons (2027)

**Objective:** Decentralized scaling + self-hosted infrastructure
**Budget:** €15-25k
**Work packages:**
- P2P replication / federation protocol
- Node ranking + traffic routing
- SLM production deployment
- Validator node support for networks

**Funding strategy:**
- **Fediversity:** EU decentralization fund
- **Alternative:** Second NGI round (NGI Zero Entrust or NGI Search)

---

### Phase 4+: Ongoing Maintenance (2027+)

**Objective:** Sustain + enhance system
**Budget:** €10-15k/year (consortium work packages)
**Funding sources:**
- Ongoing EU Digital Programme grants
- Fediversity follow-on
- Possible sponsorships (Makerfed, foundations)

**Operational sustainability:** Communities self-fund infrastructure.

---

## 10. Why This Model Works for NLNet

### Alignment with NLNet Commons Principles

✅ **Digital commons:** Data owned by communities, not platform
✅ **Decentralization:** No single point of failure; validator node model
✅ **Sustainability:** Designed to outlive grant funding via community participation
✅ **Open standards:** Apache 2.0, JSON/Pydantic schemas, replicable architecture
✅ **Governance-first:** Ostrom principles embedded from day 1

### Why Distributed Costs = Better Than Centralization

```
Centralized extraction model:
├─ Platform owns data
├─ Platform owns costs
├─ Communities depend on platform
└─ Sustainability = platform funding (extractive)

Distributed commons model:
├─ Communities own data
├─ Communities share costs (infrastructure they'd pay anyway)
├─ Platform is shared infrastructure
└─ Sustainability = community incentive (non-extractive)
```

**Result:** A system that communities want to maintain because they own it, see impact immediately, and effort is minimal.

---

## 11. Open Questions & Research Plan

| Question | Phase | Owner | Cost Impact |
|----------|-------|-------|-------------|
| Node ranking metric? | Phase 2 | Architecture | TBD |
| Traffic routing model? | Phase 2 | Architecture | Bandwidth costs TBD |
| Main node responsibility? | Phase 2 | Architecture | €10-30/month delta |
| IPFS consistency model? | Phase 2 | Storage | €20-50/month delta |
| SLM quality vs Mistral? | Phase 2 | ML | Phase-out decision |
| SLM hardware requirements? | Phase 2 | DevOps | €0-250/month delta |
| Network commitment model? | Phase 2 | Governance | Revenue model TBD |

**Action plan:**
1. Phase 2 pilot: Instrument system with admin dashboard
2. Measure: Cost, usage, performance metrics
3. Inform: Phase 3 architecture decisions
4. Document: Lessons learned for future commons projects

---

## Summary: Cost & Sustainability

| Aspect | Status | Notes |
|--------|--------|-------|
| **MVP Cost** | ✅ Defined | €18,555 (8 weeks, NLNet) |
| **Operational Cost** | ✅ Modeled | €1,200-2,400/year central + network self-hosting |
| **LLM Cost** | ✅ Roadmap | €420/year Phase 1 → €0/year Phase 3+ |
| **Decentralization** | ✅ Justified | Costs distributed, resilience gained, communities empowered |
| **Development Funding** | ✅ Strategy | Always consortium-funded (work packages) |
| **Breakeven Timeline** | ✅ Projected | Year 2-3 for operational sustainability |
| **Funding Roadmap** | ✅ Outlined | NLNet → Erasmus+ → Fediversity → Sustaining |
| **Governance Model** | ⏳ Phase 2 | To be co-designed with pilot networks |

**Conclusion:** Maps of Making is genuinely sustainable because development is publicly funded (digital commons is public goods work) and operations are distributed across participants (no extractive rent-seeking required).

---

_Document prepared for NLNet Commons Fund review and Phase 2 planning._
_Last updated: 2025-11-11_
