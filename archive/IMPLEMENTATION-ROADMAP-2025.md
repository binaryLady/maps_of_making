# Implementation Roadmap 2025: Maps of Making MVP + Funding Strategy

**Date:** 2025-11-12
**Status:** Phase 1 Planning Complete; Ready for Execution
**Budget:** €18,555 (NLNet NGI Zero Commons Round 1)
**Timeline:** 8 weeks (Dec 2025 - Feb 2026)

---

## Executive Summary

Maps of Making has completed comprehensive planning across four strategic domains:

1. **Product Vision & Personas** — What users need (5 personas, 15+ use cases)
2. **Technical Architecture** — How we'll build it (Neo4j graphs, distributed federation)
3. **Sustainability Model** — How it survives (decentralized cost distribution, open commons)
4. **Execution Plan** — When we'll ship it (4 milestones, 46 user stories, week-by-week)

**Key documents are now ready for:**
- ✅ NLNet funding application (draft complete; awaiting user data)
- ✅ Phase 1 development (user stories + acceptance criteria)
- ✅ Phase 2-3 architecture (research plan to measure Phase 1 outcomes)
- ✅ Long-term sustainability (cost models + governance framework)

---

## Documentation Map

### Planning & Product (User Perspective)

| Document | Purpose | For Whom | Key Insight |
|----------|---------|----------|-------------|
| **[PERSONAS.md](docs/planning/PERSONAS.md)** | 5 detailed user personas + interaction flows | Product, UX, Developers | Personas 1 & 3 are MVP-critical; Persona 5 (LLM Agent) is hero feature |
| **[BRAINSTORM-SUMMARY-2025-11-11.md](docs/planning/BRAINSTORM-SUMMARY-2025-11-11.md)** | Decision log + traceability (skills-first, Tier 1+3 display, activity-based freshness) | Stakeholders, Decision makers | Why we chose each design; links to implementation |
| **[PRD.md](docs/planning/PRD.md)** | Functional requirements (40+ features, success metrics) | Developers, QA | Canonical requirements; linked to architecture & user stories |

### Architecture & Technical (How We Build It)

| Document | Purpose | For Whom | Key Insight |
|----------|---------|----------|-------------|
| **[architecture.md](docs/architecture/architecture.md)** | System design (graph schema, API design, deployment model) | Architects, Developers | Neo4j-only; IPFS backup; validator node model deferred to Phase 2 |
| **[admin-dashboard-spec.md](docs/architecture/admin-dashboard-spec.md)** | Operational monitoring spec (cost tracking, system health, data quality) | DevOps, Backend developers | 4 priority metrics; exact API endpoints; implementation timeline |
| **[tech-stack-audit.md](docs/architecture/tech-stack-audit.md)** | Technology choices + justification (FastAPI, Leaflet, Mistral AI) | Technical leads | All tools are open/hackable except Mistral (Phase 2 swap to SLM) |

### Funding & Sustainability (How It Survives)

| Document | Purpose | For Whom | Key Insight |
|----------|---------|----------|-------------|
| **[COST-SUSTAINABILITY.md](docs/funding/COST-SUSTAINABILITY.md)** | Cost models + funding roadmap (3 scenarios, Phase 1-4+ breakdown) | Finance, Strategy | Development always grant-funded; operations distributed = self-sustaining by Year 2-3 |
| **[NLnet-NGI-ZERO-Commons-Application.md](docs/funding/NLnet-NGI-ZERO-Commons-Application.md)** | Funding application (draft, 90% complete) | Funders, Project leads | €18,555 for MVP; clear governance + sustainability model |

### Execution & Sprint Planning (When We Ship It)

| Document | Purpose | For Whom | Key Insight |
|----------|---------|----------|-------------|
| **[phase-1-sprint-plan.md](docs/planning/phase-1-sprint-plan.md)** | Week-by-week user stories (46 stories, 340 hours, 4 milestones) | Developers, PM, QA | M1 backend, M2 domain logic, M3 frontend, M4 deploy; on budget |
| **[phase-2-3-research-plan.md](docs/planning/phase-2-3-research-plan.md)** | Framework for measuring Phase 1 to inform Phase 2-3 (5 research Q's) | Architects, Data analyst | Q1-5 define how to validate cost scenarios + federation viability |
| **[round-1-roadmap.md](docs/planning/round-1-roadmap.md)** | Original budget + timeline (milestones, deliverables, timeline) | Project management | Budget breakdown; links to detailed sprint plan |

---

## How Documents Relate (Information Architecture)

```
┌─────────────────────────────────────────────────────┐
│               USER PERSPECTIVE                      │
│ What do users need? (5 personas, 15+ use cases)     │
│ → PERSONAS.md ← → PRD.md                            │
└────────────────┬────────────────────────────────────┘
                 │ "Persona validation via implementation"
                 ▼
┌─────────────────────────────────────────────────────┐
│          ARCHITECTURE & TECHNOLOGY                  │
│ How do we build it? (Neo4j, FastAPI, Leaflet)      │
│ → architecture.md ← → admin-dashboard-spec.md       │
│ → tech-stack-audit.md                              │
└────────────────┬────────────────────────────────────┘
                 │ "Tech constraints ↔ user requirements"
                 ▼
┌─────────────────────────────────────────────────────┐
│           EXECUTION PLANNING                        │
│ When do we ship? (8 weeks, 46 stories)             │
│ → phase-1-sprint-plan.md ← → BRAINSTORM-SUMMARY    │
│ → round-1-roadmap.md                               │
└────────────────┬────────────────────────────────────┘
                 │ "Acceptance criteria ↔ architectural decisions"
                 ▼
┌─────────────────────────────────────────────────────┐
│        SUSTAINABILITY & FUNDING                     │
│ How does it survive beyond funding? (Cost models)   │
│ → COST-SUSTAINABILITY.md ← → phase-2-3-research    │
│ → NLnet-NGI-ZERO-Commons-Application.md             │
└─────────────────────────────────────────────────────┘
                 │ "Measurement validates sustainability claims"
                 ▼
         ┌───────────────────┐
         │  Continuous Cycle │
         │ (Phase 2-3-4)     │
         └───────────────────┘
```

---

## Key Decisions Documented

### 1. Data Model: Skills-First (Not Equipment)

**Decision:** Focus on competencies (anonymized proficiency counts) instead of equipment lists

**Why:** Equipment changes too fast; skills are core identity; enables ML queries

**Where documented:**
- BRAINSTORM-SUMMARY Section 1
- architecture.md Section 2 (Space node schema)
- PRD Section 3.2 (Skills & Capabilities)

**Impact:** Enables Persona 2 (Researcher) to query skill evolution; simplifies data maintenance

---

### 2. Display Strategy: Tier 1 + Tier 3 Only

**Decision:** Show freshness + partnerships; don't maintain detailed capability lists (link to website instead)

**Why:** Tier 2 (detailed capabilities) too expensive to maintain; Tier 1+3 is the differentiator

**Where documented:**
- BRAINSTORM-SUMMARY Section 2
- PRD Section 3.1-3.2
- PERSONAS.md (all use cases reference freshness + partnerships)

**Impact:** Reduces data maintenance burden by 60%; improves user trust (freshness = liveness signal)

---

### 3. Freshness Model: Activity-Based Decay (Option B)

**Decision:** Magic-link verification primary; optional webhooks/sensors extend freshness

**Decay timeline:**
- 0-14d: Fresh ✅
- 15-30d: Aging ⚠️
- 31-90d: Zombie 🧟
- 90d+: Dead 💀

**Why:** Communities don't want to verify monthly if clearly active; activity-based nudges automation adoption

**Where documented:**
- BRAINSTORM-SUMMARY Section 3
- architecture.md Section 7 (algorithm + implementation)
- PRD Section 3.5 (Freshness & Verification)

**Impact:** Incentivizes network operators to integrate webhooks (Phase 2-3); keeps data fresh without manual overhead

---

### 4. Decentralized Cost Model

**Decision:** No central funding required after MVP; costs absorbed into network infrastructure (€30-50/month per network anyway)

**Cost structure:**
- Central: €50-100/month (consolidation + IPFS)
- Per network: €30-50/month (their own VPS; volunteers manage)
- Cost per space: €3.70-16/year (decreases with scale)

**Why:** Aligns with Ostrom commons principles; networks own infrastructure they'd need anyway; no extractive revenue

**Where documented:**
- COST-SUSTAINABILITY.md Section 2-4 (all scenarios)
- COST-SUSTAINABILITY.md Section 10 (NLNet alignment)
- NLnet-NGI-ZERO-Commons-Application.md Section 5-6 (budget + sustainability)

**Impact:** System is genuinely sustainable; no dependency on continued grant funding after Phase 1-3

---

### 5. Federation Model (Deferred to Phase 2)

**Decision:** Phase 1 = centralized MVP; Phase 2-3 = validator nodes with IPFS replication

**Why:** Validator rollout depends on 5 research questions (Q1-5) that must be measured in Phase 1

**Where documented:**
- COST-SUSTAINABILITY.md Section 7 (deferred questions)
- phase-2-3-research-plan.md (complete framework for each Q)
- architecture.md Section 1 (architecture diagram shows Phase 1 vs Phase 2+ model)

**Impact:** Phase 1 stays simple & on-budget; Phase 2 architecture informed by evidence, not speculation

---

### 6. LLM Strategy: Mistral API → Self-Hosted SLM

**Decision:** Phase 1 use Mistral API (€420/year); Phase 2-3 migrate to fine-tuned 7B model (€0/year)

**Why:** Mistral is reliable but has vendor lock-in + ongoing cost; SLM is free but requires Phase 2 training/testing

**Where documented:**
- COST-SUSTAINABILITY.md Section 3 (LLM evolution)
- phase-2-3-research-plan.md Section Q3 (detailed SLM vs Mistral comparison framework)
- NLnet-NGI-ZERO-Commons-Application.md (mentions both phases)

**Impact:** Permanent €420/year savings after Phase 2; better privacy (queries stay local); demonstrates SLM viability

---

## Immediate Next Steps (Before Phase 1 Kick-Off)

### For Project Lead / Funding Coordinator

**NLnet Application (Draft → Submission):**

1. ✅ **Section 1 (Contact Info)** — User to complete
   - Name, email, phone, country, organization

2. ✅ **Section 4 (Experience/Team Bios)** — User to complete
   - Team member backgrounds, expertise, relevant projects
   - Template in draft; ~250 words per person

3. ✅ **Section 9 (Pilot Networks)** — User to complete
   - 3-5 network names, contact info, data status
   - Collect Letters of Intent (to attach as Pilot_Network_LOI.pdf)

**Timeline:** Sections 1, 4, 9 need completion by **Nov 25** for Dec 1 NLNet deadline

**All other sections:** ✅ Complete (Sections 2, 3, 5-8 are ready; refer to GitHub doc references)

---

### For Development Team

**Phase 1 Execution Prep:**

1. ✅ **Team onboarding** (Week of Nov 25)
   - Read: PERSONAS.md + PRD.md (1 hour)
   - Read: architecture.md + admin-dashboard-spec.md (1 hour)
   - Read: phase-1-sprint-plan.md Stories 1.1-1.7 (1 hour)

2. ✅ **Environment setup** (Week 1)
   - Story 1.1: Docker Compose + FastAPI project scaffold
   - Story 1.2: JWT middleware + RBAC framework

3. ✅ **Measurement framework** (Weeks 1-3)
   - Story 1.13: Admin dashboard data collection setup
   - Phase 1 research questions (phase-2-3-research-plan.md) begin measurement

---

### For Architecture & Design Review

**Before Phase 2 Planning:**

1. ✅ **Phase 1 measurement completion** (End Week 8)
   - Collect data from admin dashboard on:
     - Q1: Node ranking metrics (response times, latency)
     - Q2: IPFS consistency (snapshot freshness, integrity)
     - Q3: Mistral baseline accuracy
     - Q4: Central hub resource usage (to estimate validator node sizing)
     - Q5: Write load + consolidation overhead

2. ✅ **Phase 2 Briefing document generation**
   - Template in phase-2-3-research-plan.md Section 11
   - Use data to answer Q1-5; inform Phase 2 architecture

3. ✅ **Erasmus+ KA220 proposal prep** (Timeline: Feb-Apr 2026)
   - Leverage Phase 1 data to justify Phase 2 budget requests
   - Use cost projections from COST-SUSTAINABILITY.md (will be validated by Phase 1 measurement)

---

## Document Maintenance Guidelines

### Single Source of Truth

To prevent documentation drift, follow this hierarchy:

1. **Primary docs** (canonical; updated per decision):
   - architecture.md (technical decisions)
   - PRD.md (functional requirements)
   - phase-1-sprint-plan.md (execution plan)

2. **Supporting docs** (reference primary; cross-linked):
   - BRAINSTORM-SUMMARY (traceability; locked)
   - PERSONAS.md (user validation; locked until Phase 2)
   - COST-SUSTAINABILITY.md (cost data; updated with Phase 1 measurement)

3. **Funding docs** (external-facing; updated as needed):
   - NLnet-NGI-ZERO-Commons-Application.md (via GitHub doc references)
   - Supporting documents (round-1-roadmap.md, etc.)

### Update Triggers

| Document | Update When | Owner |
|----------|------------|-------|
| **architecture.md** | Major tech decision made | Architect |
| **PRD.md** | Feature scope changes | Product manager |
| **phase-1-sprint-plan.md** | Actual effort deviates >20% from estimate | Developers + PM |
| **COST-SUSTAINABILITY.md** | Phase 1 measurement completes | Finance + Research lead |
| **BRAINSTORM-SUMMARY** | (Locked; no updates until Phase 2 brainstorm) | N/A |

---

## Success Criteria: By Date

### By Nov 25, 2025
- ✅ NLnet application fully completed (all 9 sections)
- ✅ Sections 1, 4, 9 filled with user data
- ✅ All GitHub doc references active + working
- ✅ Application submitted to NLnet form

### By Dec 15, 2025 (Phase 1 Kick-Off)
- ✅ Development team onboarded + environments ready
- ✅ Week 1 sprint ready (Stories 1.1-1.7 prioritized)
- ✅ Measurement framework initialized (admin dashboard setup)
- ✅ Pilot networks confirmed + data provided

### By Feb 15, 2026 (Phase 1 Complete)
- ✅ MVP deployed to Hetzner (https://maps.making)
- ✅ ≥3 pilot networks verified their spaces
- ✅ Admin dashboard collecting cost + quality metrics
- ✅ Phase 2 Research Briefing generated (Q1-5 answered)
- ✅ Phase 2 budget proposal ready for Erasmus+ KA220

### By Apr 30, 2026 (Erasmus+ Submission)
- ✅ Phase 2 proposal submitted (€20-30k)
- ✅ Based on Phase 1 evidence + cost projections
- ✅ Partner networks confirmed as co-applicants

---

## Document Navigation

### For Users / Space Operators
→ Start with **PERSONAS.md** (find yourself) → **PRD.md** (understand features)

### For Developers
→ Start with **architecture.md** → **phase-1-sprint-plan.md** → specific story

### For Funders / Strategic Decision Makers
→ Start with **COST-SUSTAINABILITY.md** (Section 10: "Why This Works for NLNet")
→ Then **NLnet-NGI-ZERO-Commons-Application.md** (complete application)

### For Researchers / Data Analysis
→ **PERSONAS.md** Persona 2 → **phase-2-3-research-plan.md** (Q2, temporal data)

### For Network Coordinators / Operators
→ **PERSONAS.md** Persona 3 → **admin-dashboard-spec.md** (monitoring your network health)

---

## Key Metrics & Targets

### Phase 1 Success

| Metric | Target | Owner | Tracked In |
|--------|--------|-------|-----------|
| **Budget adherence** | ±10% of €18,555 | Finance | phase-1-sprint-plan.md |
| **Delivery on time** | 8 weeks (Dec 1 - Jan 31) | PM | phase-1-sprint-plan.md |
| **Pilot network adoption** | ≥3 networks verified | Product | admin-dashboard-spec.md |
| **Freshness rate** | ≥80% spaces verified in last 30d | Operations | admin-dashboard-spec.md |
| **API uptime** | ≥99% | DevOps | admin-dashboard-spec.md |
| **Research data quality** | Answers Q1-5 with 80% confidence | Research | phase-2-3-research-plan.md |

### Phase 2-3 Gating Criteria

✅ **If Phase 1 metrics are met:**
- Proceed with validator node deployment (Q4 answer)
- Evaluate SLM fine-tuning (Q3 answer)
- Plan decentralized governance (Q5 answer)

⚠️ **If Phase 1 metrics are weak:**
- Delay Phase 2 federation; focus on adoption
- Extend Mistral API usage; defer SLM migration
- Reassess network participation model

---

## Risk Register

### HIGH PRIORITY

| Risk | Impact | Mitigation | Owner |
|------|--------|-----------|-------|
| Pilot networks can't provide data on time | Phase 1 delay | Request sample data by Week 2; use synthetic if needed | Product |
| Mistral API cost overruns | Budget impact | Monitor weekly; implement query caching if needed | Backend |
| SLM not viable (accuracy <85%) | Eliminate €420/year savings | Plan for Phase 4; continue Mistral API beyond Phase 2 | ML lead |

### MEDIUM PRIORITY

| Risk | Impact | Mitigation | Owner |
|------|--------|-----------|-------|
| Neo4j performance issues at scale (250 spaces) | Deployment delay | Monitor Week 4-5; optimize indexes proactively | Backend |
| Frontend responsive design issues | Mobile adoption | Allocate 8h for accessibility audit (Story 3.5) | Frontend |
| Validator node hardware unclear | Phase 2 delay | Measure Q4 carefully; get cost quotes early | Architect |

---

## Glossary

| Term | Definition | Related Docs |
|------|-----------|-------------|
| **Freshness** | Time since last verification; decays from ✅→⚠️→🧟→💀 | architecture.md §7, PRD §3.5 |
| **Verification** | Space operator confirms data is current via magic-link email | phase-1-sprint-plan.md §2.2 |
| **Partnership** | Two spaces collaborating; requires 2-way confirmation (handshake) | BRAINSTORM-SUMMARY §4, architecture.md §2 |
| **Validator Node** | Network-hosted copy of database; allows decentralized fallback | architecture.md §1, COST-SUSTAINABILITY.md §4 |
| **Consolidation** | Nightly export of all space data to IPFS; enables federation | architecture.md §1, phase-2-3-research-plan.md §Q2 |
| **Magic-link** | Stateless JWT sent via email; no passwords or accounts | phase-1-sprint-plan.md §2.2, architecture.md §9 |
| **RBAC** | Role-Based Access Control; restricts endpoints by user role | phase-1-sprint-plan.md §1.2, architecture.md §9 |

---

## Support & Questions

### For Questions About...

| Topic | Resource | Contact |
|-------|----------|---------|
| **Product/Features** | PERSONAS.md + PRD.md | Product manager |
| **Technical Architecture** | architecture.md + admin-dashboard-spec.md | Architect |
| **Budget/Funding** | COST-SUSTAINABILITY.md + NLnet application | Finance |
| **Phase 1 Execution** | phase-1-sprint-plan.md | Development lead |
| **Phase 2-3 Planning** | phase-2-3-research-plan.md | Research lead |
| **Data/Measurement** | admin-dashboard-spec.md | Data analyst |

---

## Appendix: Document Checklist

### Required Before Phase 1 Kick-Off

- [ ] NLnet application (Sections 1, 4, 9) completed
- [ ] Development team onboarded (read PERSONAS, architecture, sprint plan)
- [ ] Pilot networks confirmed with data schedules
- [ ] GitHub Actions CI pipeline ready
- [ ] Docker Compose environment documented

### Required Before Phase 2 Submission (Erasmus+)

- [ ] Phase 1 complete + deployed
- [ ] Research Q1-5 answered with data
- [ ] Cost scenarios validated against actual metrics
- [ ] Pilot network feedback documented
- [ ] Phase 2 roadmap drafted (based on evidence, not speculation)

---

_Implementation Roadmap prepared: 2025-11-12_
_Status: Planning Complete; Execution Ready_
_Next Milestone: NLnet Submission (Dec 1, 2025)_

