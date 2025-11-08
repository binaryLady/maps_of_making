# Maps of Making: Federated Makerspace Data Commons

> Digital commons infrastructure that solves why makerspace maps fail: **no ongoing incentive to maintain them.**

---

## The Problem

Existing makerspace maps (Fablab.io, Hackerspaces.org, regional databases) go stale because:

- **Spaces waste effort** updating 5+ separate platforms with zero visible impact
- **No feedback loop** showing "your verification matters"
- **Maps become unreliable** → users waste travel time and resources
- **Ecosystem loses coordination** → networks can't share lessons from failures
- **Knowledge disappears** → when spaces close, their history is erased

**Root cause:** Incentive misalignment. One-shot data entry ≠ ongoing maintenance.

**Impact:** Digital nomads, researchers, and communities depend on current makerspace info. Outdated maps lead to wasted travel, wasted resources, lost ecosystem learning.

---

## Our Solution

### One Verification Point → Visible Everywhere

Maps of Making creates a **single source of truth** so useful and fresh that maintaining it becomes rationally justified:

**For Space Operators:**
- Verify once → visible globally across the entire ecosystem
- Effortless maintenance: Magic links, webhooks, local sensors (**<2 minutes per update**)
- Real-time feedback: Activity update → instant freshness change on map
- Community reputation: "Our data is current; people can actually find us"

**For Users & Researchers:**
- One reliable source replaces 5+ stale platforms
- Freshness signals (✅ Fresh → ⚠️ Aging → 🧟 Zombie → 💀 Dead) show current status
- Machine-readable API: Natural language queries ("Find active spaces in Berlin")
- Network intelligence: Who collaborates? What partnerships exist? (not just locations)

**For the Ecosystem:**
- Spaces close, but their history is preserved (not deleted)
- Networks can study failure patterns and evolution strategies
- Communities share lessons across regions
- **Infrastructure designed to outlive any grant funding**

---

## Commons Alignment: Built for Sustainability

Maps of Making is grounded in **Elinor Ostrom's principles** for sustainable commons governance—proven across fisheries, forests, and community resources worldwide:

| Principle | Implementation |
|-----------|-----------------|
| **Clear boundaries** | Federated networks define membership; spaces opt-in |
| **Collective decision-making** | Networks set verification standards, governance rules |
| **Monitoring & accountability** | Freshness signals, activity logs, immutable ledger |
| **Graduated sanctions** | Status lifecycle incentivizes timely verification |
| **Conflict resolution** | Closure reports, dispute mechanisms, community trust |
| **Recognition** | Networks govern their own data (not platform gatekeeping) |
| **Polycentric governance** | Networks can host federation replicas, apply rules at their scale |
| **Nested enterprises** | Pilot networks → Regional federations → Global ecosystem |

**Key Design Decisions:**
- ✅ Community ownership: Networks and spaces control their data
- ✅ Decentralized architecture: IPFS snapshots (data lives in commons, not proprietary servers)
- ✅ Transparent governance: Immutable ledger tracks all verification events
- ✅ Apache 2.0 license: Enables derivative funding (NGI, Erasmus+)
- ✅ Validator node model: Networks can run local replicas (no single point of failure)

**Why This Matters for NLNet:** Commons designed to Ostrom principles are proven to sustain across decades without external funding or platform gatekeeping. This isn't just a map—**it's infrastructure designed to outlive grants.**

---

## Impact Potential

### 1. Eliminate Duplicate Effort
**Problem:** Spaces update 5+ separate maps. Each update feels disconnected from impact.
**Solution:** Single verification cascades everywhere—one update powers discoverability across the entire ecosystem.

### 2. Enable Ecosystem Learning
**Problem:** Failed spaces close, data disappears, networks can't learn from experience.
**Solution:** Preserve history, not delete it. Time-based queries enable research: "Which spaces closed in 2024? Why? What patterns exist?"

### 3. Reveal Invisible Networks
**Problem:** Other maps show locations. We reveal relationships.
**Solution:** Graph database captures collaborations, partnerships, skill flows. Answer questions like: "Who collaborates with whom? What ecosystems are forming?"

### 4. Agent-Ready Infrastructure
**Problem:** Closed maps are opaque to AI. Agents can't understand ecosystem.
**Solution:** Natural language API + A2A protocol compatibility. "Ask the map" becomes possible—agents get current, verified data.

### 5. Replicable Pattern for Commons
**Problem:** Solutions built for makerspaces only.
**Solution:** Same model scales to repair networks, tool libraries, community gardens, knowledge commons. Open source + Apache 2.0 enables forks.

---

## Documentation Guide

### For Reviewers & Funders
Start here and read in order:
1. **[Product Requirements (PRD)](docs/PRD.md)** — Full requirements, user journeys, success metrics, Ostrom alignment
2. **[Competitive Analysis](docs/competitive-analysis.md)** — Market positioning, competitor comparison, strategic differentiation
3. **[NLNet Application](docs/NLnet-NGI-ZERO-Commons-Application.md)** — Funding proposal, budget, timeline

### For Technical Leadership
1. **[Architecture](docs/architecture.md)** — System design, 6 ADRs, graph schema, API design, deployment
2. **[Tech Stack Audit](docs/tech-stack-audit.md)** — Verified technologies, latest versions, license compatibility
3. **[Implementation Readiness Report](docs/implementation-readiness-report.md)** — Gate-check validation, gap analysis, risk assessment

### For Development Team
1. **[Epics & Stories](docs/epics.md)** — 21-27 user stories, sequencing, acceptance criteria, estimates
2. **[Architecture](docs/architecture.md)** — Sections 1-3 (system design, data models, tech stack)
3. **[Project Status](docs/bmm-workflow-status.md)** — Phase completion, next actions, blockers

### For Consortium Partners
1. **This README** ← You are here
2. **[PRD](docs/PRD.md)** — Problem statement, solution approach, success metrics
3. **[Architecture](docs/architecture.md)** — Overview of technical approach and governance model

---

## Funding Strategy

### NLNet Commons Fund (MVP: Phases 1-3)
- **Timeline:** 6 months
- **Scope:** Data federation + interactive map + verification system
- **Proof of concept:** Demonstrates that communities maintain data when incentives align

### Phase 4+ (Strategic Funding)
- **Erasmus+ KA220:** Governance layer, network coordinator training
- **Fediversity:** Decentralized scaling, validator node deployment
- **Replication revenue:** Communities license implementation support

**Why It Works:** Pilot networks → regional federations → global maker ecosystem. Each level self-sustains through community participation.

---

## Contributing

Maps of Making is built for **community participation from day one.**

### For Makerspace Networks
Interested in piloting? **[Start here](docs/PRD.md#Epic-3-Verification--Community-Maintenance)** to understand verification workflow.

### For Developers
Phase 4 sprint planning begins Nov 2025. **[See implementation roadmap](docs/epics.md)** for story breakdown and contribution opportunities.

### For Researchers
**[Temporal ecosystem analysis](docs/PRD.md#Epic-5-Temporal-Ecosystem-Analysis)** is deferred to Phase 4 but core infrastructure is designed to support it. Space history is preserved, not deleted.

---

## Team

**Maps of Making** is developed by a coalition of makerspace networks, digital commons researchers, and open-source contributors.

**Current Team:**
- [COMPLETE with team members and roles]

**Contact:** [COMPLETE with primary contact]

---

## License

- **Core Platform:** Apache 2.0 (enables derivative funding from NGI calls)
- **Database:** GPL3 (Neo4j Community)
- **Dependencies:** All MIT or Apache 2.0 compatible

All code, documentation, and data schemas are open source. **Data commons, not data extraction.**

---

## Citation

If you reference Maps of Making in research or funding applications:

```
Maps of Making: Federated Makerspace Data Commons.
Grounded in Elinor Ostrom's principles for sustainable commons governance.
https://github.com/maps-of-making
Apache 2.0 License, 2025
```

---

<div align="center">

**Building digital commons where communities maintain their own data because they own it, see immediate impact, and the effort is minimal.**

[📄 Full PRD](docs/PRD.md) • [🏗️ Architecture](docs/architecture.md) • [💰 NLNet Application](docs/NLnet-NGI-ZERO-Commons-Application.md) • [📊 Analysis](docs/competitive-analysis.md)

</div>
