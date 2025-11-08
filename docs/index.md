# Documentation Index: Maps of Making

> Comprehensive guide to all project documentation organized by phase and audience.

**Last Updated:** Nov 8, 2025
**Project Status:** Phase 3 Complete ✅ | Phase 4 Ready 🚀

---

## 📍 Quick Navigation by Role

### 🎯 For Project Managers & Funders
**Goal:** Understand problem, solution, impact, and funding strategy

**Reading Path:**
1. [README.md](../README.md) ← Start here (2 min read)
2. [planning/PRD.md](planning/PRD.md) (10 min) — User requirements, journeys, success metrics
3. [planning/competitive-analysis.md](planning/competitive-analysis.md) (10 min) — Market positioning
4. [funding/NLnet-NGI-ZERO-Commons-Application.md](funding/NLnet-NGI-ZERO-Commons-Application.md) (15 min) — Funding proposal
5. [planning/CULTIVATE-principles.md](planning/CULTIVATE-principles.md) (5 min) — Values framework

**Time Commitment:** ~45 minutes

---

### 🏗️ For Architects & Tech Leadership
**Goal:** Understand system design, technology choices, and implementation approach

**Reading Path:**
1. [README.md](../README.md) ← Start here (2 min)
2. [architecture/architecture.md](architecture/architecture.md) (30 min) — Full technical design
3. [architecture/tech-stack-audit.md](architecture/tech-stack-audit.md) (15 min) — Technology verification
4. [architecture/implementation-readiness-report.md](architecture/implementation-readiness-report.md) (20 min) — Gate-check validation
5. [planning/PRD.md](planning/PRD.md) — Sections on NFR (non-functional requirements)

**Time Commitment:** ~60 minutes
**Key Sections:** Architecture sections 1-6 (overview), Section 15 (ADRs)

---

### 👨‍💻 For Developers (Phase 4 Team)
**Goal:** Understand stories, sequencing, technical tasks, and acceptance criteria

**Reading Path:**
1. [README.md](../README.md) ← Start here (2 min)
2. [planning/epics.md](planning/epics.md) (15 min) — User stories, estimates, sequencing
3. [architecture/architecture.md](architecture/architecture.md) — Sections 1-3 only (system overview, data model, tech stack)
4. [bmm-workflow-status.md](bmm-workflow-status.md) (5 min) — Current phase, blockers, next actions

**Time Commitment:** ~25 minutes
**Key Files for Development:**
- Stories: [planning/epics.md](planning/epics.md)
- Technical Design: [architecture/architecture.md](architecture/architecture.md)
- Status Tracking: [bmm-workflow-status.md](bmm-workflow-status.md)

---

### 🤝 For Consortium Partners & Network Leaders
**Goal:** Understand value proposition, community role, and sustainability model

**Reading Path:**
1. [README.md](../README.md) ← Start here (3 min)
2. [planning/PRD.md](planning/PRD.md) — Sections: "The Problem", "User Journeys" (10 min)
3. [architecture/architecture.md](architecture/architecture.md) — Sections 1, 14-15 (decentralization, patterns) (15 min)
4. [planning/CULTIVATE-principles.md](planning/CULTIVATE-principles.md) (5 min)

**Time Commitment:** ~35 minutes

---

## 📚 Document Inventory

### Planning Phase (Phase 2 - Complete ✅)

**Location:** `docs/planning/`

| Document | Purpose | Key Info | Updated |
|----------|---------|----------|---------|
| **PRD.md** | Product Requirements Document | 35 functional requirements, 5 epics, 3 user journeys, success metrics | Nov 5 |
| **epics.md** | User Stories & Implementation Roadmap | 21-27 stories, 76 hours estimated, full sequencing | Nov 5 |
| **competitive-analysis.md** | Market Research & Positioning | 6 competitor comparison, strategic differentiation, IoT facility analysis | Nov 5 |
| **CULTIVATE-principles.md** | Values & Philosophy | 9 principles for digital commons, sustainability framework | Earlier |

**Total Lines:** ~1,200 | **Status:** Complete, ready for reference

---

### Architecture Phase (Phase 3 - Complete ✅)

**Location:** `docs/architecture/`

| Document | Purpose | Key Info | Updated |
|----------|---------|----------|---------|
| **architecture.md** | System Design & Technical Decisions | 20 sections, 6 ADRs, graph schema, API design, deployment | Nov 5 |
| **tech-stack-audit.md** | Technology Verification | 9 technologies verified, latest versions, license chain validated | Nov 8 |
| **implementation-readiness-report.md** | Gate-Check Validation | 100% alignment verified, zero critical issues, risk assessment | Nov 8 |

**Total Lines:** ~2,300 | **Status:** Complete, ready for implementation

---

### Funding Phase (In Progress 🟡)

**Location:** `docs/funding/`

| Document | Purpose | Status | Deadline |
|----------|---------|--------|----------|
| **NLnet-NGI-ZERO-Commons-Application.md** | NLNet Zero Commons Fund proposal | DRAFT - needs finalization | Dec 1, 2025 |
| **NLnet-NGI-ZERO-Commons-Application.template.md** | Application template (reference) | Reference only | N/A |

**Total Lines:** ~750 | **Status:** In progress, critical path item

---

### Project Management (Living Document)

**Location:** `docs/`

| Document | Purpose | Last Updated |
|----------|---------|--------------|
| **bmm-workflow-status.md** | Phase tracking, next actions, blockers | Nov 8 |

---

## 🎯 Document Types & How to Use Them

### Reference Documents (Stable, archived)
These don't change frequently and provide foundational understanding:
- PRD.md
- competitive-analysis.md
- architecture.md
- tech-stack-audit.md

**Use:** Read once, reference later. Update only if requirements change.

### Working Documents (Active, evolving)
These change as the project progresses:
- epics.md (updated as stories are refined)
- implementation-readiness-report.md (archived after Phase 4 starts)
- bmm-workflow-status.md (updated weekly)
- NLnet application (active until Dec 1)

**Use:** Check regularly for updates. Questions? Refer to current status.

---

## 🔄 Phase Transitions & Documentation Lifecycle

### Phase 2 → Phase 3 (Complete)
- ✅ PRD created
- ✅ Competitive analysis completed
- ✅ Epics drafted
- **Output:** Planning foundation ready for architecture

### Phase 3 → Phase 4 (Ready)
- ✅ Architecture designed
- ✅ Tech stack verified
- ✅ Gate-check passed
- **Output:** Implementation ready; sprint planning next

### Archival Strategy (Post-Phase 4)
- implementation-readiness-report.md → archive/ (was validation gate, no longer needed)
- Each sprint phase generates new implementation/ docs
- Keep planning/ and architecture/ as permanent reference

---

## 📖 How to Read Architecture.md (Most Complex Document)

**architecture.md** is comprehensive (20 sections). Different sections matter for different readers:

**Sections 1-3 (System Overview)** [15 min]
- For all audiences
- Diagrams, pattern explanation, key decisions
- Read first

**Sections 4-8 (Technical Deep Dive)** [30 min]
- For architects and tech leads
- Data models, API design, security
- Read if implementing

**Sections 9-15 (Implementation & Operations)** [20 min]
- For developers and DevOps
- Project structure, deployment, performance
- Read if developing

**Sections 16-20 (Decision Records & Beyond)** [15 min]
- For future reference
- ADRs explain the "why" behind choices
- Read to understand trade-offs

---

## ❓ Common Questions & Where to Find Answers

| Question | Answer Location |
|----------|-----------------|
| **What problem does this solve?** | [README.md](../README.md) Problem section |
| **What's the user experience?** | [planning/PRD.md](planning/PRD.md) User Journeys section |
| **How does the system work?** | [architecture/architecture.md](architecture/architecture.md) Sections 1-3 |
| **What's the tech stack?** | [architecture/tech-stack-audit.md](architecture/tech-stack-audit.md) |
| **What stories need development?** | [planning/epics.md](planning/epics.md) |
| **What's the current status?** | [bmm-workflow-status.md](bmm-workflow-status.md) |
| **Why Neo4j instead of PostgreSQL?** | [architecture/architecture.md](architecture/architecture.md) ADR-001 |
| **Is this funded?** | [funding/NLnet-NGI-ZERO-Commons-Application.md](funding/NLnet-NGI-ZERO-Commons-Application.md) |
| **How is data stored?** | [architecture/architecture.md](architecture/architecture.md) Section 4 (Decentralization) |
| **What about privacy?** | [architecture/architecture.md](architecture/architecture.md) Section 12 (Security) |

---

## 🚀 For Phase 4 Implementation

### Stories Ready for Development
All stories are in: **[planning/epics.md](planning/epics.md)**

### Technical Reference for Development
Primary: **[architecture/architecture.md](architecture/architecture.md)**
Backup: **[architecture/tech-stack-audit.md](architecture/tech-stack-audit.md)**

### Current Progress
Check: **[bmm-workflow-status.md](bmm-workflow-status.md)**

### Creating New Stories During Sprint
- Follow template in [planning/epics.md](planning/epics.md) Section "Epic Structure"
- Use story template: [name], [acceptance criteria], [technical tasks], [complexity estimate]
- Save new stories to `/stories/` directory when Phase 4 begins

---

## 📝 Documentation Standards & Maintenance

### Versioning
- **Documents:** Dated (e.g., "Updated: Nov 8, 2025")
- **Content:** No formal version numbers; updated in-place

### Update Cadence
- **Planning docs:** Updated only if requirements change
- **Architecture:** Updated if design changes
- **Status:** Updated weekly or when phase changes
- **Funding:** Updated until submission (Dec 1)

### When to Update Documentation
1. ✅ Requirements change (→ update PRD + architecture + epics)
2. ✅ Technical decisions made (→ add ADR to architecture)
3. ✅ Phase transitions (→ update status, archive old docs)
4. ✅ Gate-checks completed (→ add report, validate alignment)
5. ❌ DO NOT: Update for minor corrections without noting "Updated: [date]"

---

## 🔗 Quick Links

**Start Here:** [README.md](../README.md)

**Strategic Decisions:** [architecture/architecture.md](architecture/architecture.md) Section 16 (ADRs)

**Implementation Plan:** [planning/epics.md](planning/epics.md)

**Project Status:** [bmm-workflow-status.md](bmm-workflow-status.md)

**Funding Proposal:** [funding/NLnet-NGI-ZERO-Commons-Application.md](funding/NLnet-NGI-ZERO-Commons-Application.md)

---

**Maps of Making Documentation** | Organized by BMAD Method | Phase 3 Complete, Phase 4 Ready
