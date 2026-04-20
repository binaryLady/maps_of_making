# BMM Workflow Status

## Project Configuration

PROJECT_NAME: maps_of_making
PROJECT_TYPE: software
PROJECT_LEVEL: 3
FIELD_TYPE: greenfield
START_DATE: 2025-11-05
WORKFLOW_PATH: greenfield-level-3.yaml

## Current State

CURRENT_PHASE: 3 (Solutioning) - NLNet Round 1 Roadmap Complete ✅
CURRENT_WORKFLOW: NLNet Application Preparation
CURRENT_AGENT: pm (Product Manager - John)
PHASE_1_COMPLETE: false (Phase 1 Analysis deferred - will do after consortium)
PHASE_2_COMPLETE: true (PRD.md + epics created ✅)
PHASE_3_COMPLETE: true (Architecture + tech-stack-audit + Round 1 roadmap ✅)
PHASE_4_COMPLETE: false (Awaiting NLNet Round 1 approval)

## Recent Session: Round 1 Roadmap & Mistral AI Migration (2025-11-10)

### Completed Work ✅

1. **Round 1 Roadmap Created**
   - File: `docs/planning/round-1-roadmap.md` (295 lines)
   - Budget: €18,555 (4 milestones + infrastructure + contingency)
   - Timeline: 8 weeks (aligned with NLNet 2-month cycles)
   - Structure: Milestone-based payments, quantitative success criteria
   - References sister docs (PRD, architecture, tech-stack-audit) - single source of truth

2. **Technology Stack Migration: OpenAI → Mistral AI**
   - **Rationale:** EU data sovereignty, GDPR-native, aligns with NLNet values
   - **License:** Apache 2.0 (was MIT for OpenAI)
   - **Trust Score:** 8.7/10 (Context7 verified)
   - **Cost:** Competitive with OpenAI pricing

3. **Documentation Updates**
   - `architecture.md`: All 7 OpenAI references → Mistral AI
   - `tech-stack-audit.md`: Section 6 rewritten for Mistral AI SDK
   - `PRD.md`: Added NFR007 (EU data sovereignty), updated FR009, NFR001

### Round 1 Budget Breakdown

| Milestone | Budget | Timeline |
|-----------|--------|----------|
| M1: Backend Engine Foundation | €5,200 | Week 1-3 |
| M2: Domain Adaptation | €4,000 | Week 4-5 |
| M3: Map Interface & Verification | €3,840 | Week 6-7 |
| M4: Integration & Deployment | €2,880 | Week 8 |
| Infrastructure (8 weeks) | €255 | Ongoing |
| Contingency (15%) | €2,420 | As needed |
| **TOTAL** | **€18,555** | **8 weeks** |

**Key Decision:** Milestone 1 (betterCallSaul backend) included as foundation work eligible for payment.

### Success Metrics (Quantitative)

**Primary GO/NO-GO Criteria:**
1. ≥2 pilot networks ingested, ≥20 total spaces
2. Map loads <2s, API <500ms
3. ≥80% magic-link email delivery
4. A2A endpoint: 5/5 test queries pass
5. ≥80% test suite pass rate
6. IPFS backup/restore successful

**GO Decision:** 6/6 metrics met → Proceed to Round 2

---

## NLNet Application Status

**Target Fund:** Commons Fund
**Application Deadline:** December 1, 2025
**Requested Amount:** €18,555 (Round 1)
**Timeline:** 8 weeks from approval

**Ready to Submit:**
- [x] Round 1 roadmap complete
- [x] PRD.md with 27 functional requirements
- [x] Architecture.md with technical design
- [x] Tech stack audit (Mistral AI verified)
- [ ] Pilot network commitments (2 minimum) - TBD
- [ ] NLNet application form filled

**Next Actions:**
1. Secure 2+ pilot network commitment letters
2. Complete NLNet application form
3. Submit before Dec 1, 2025

---

## Completed Deliverables

1. **PRD.md** - 27 functional requirements across 4 epics, Ostrom principles
2. **epics.md** - 21-27 stories, 76 hours estimated, fully sequenced
3. **architecture.md** - 6 ADRs + comprehensive system design (Mistral AI)
4. **competitive-analysis.md** - Market positioning vs 6 competitors
5. **tech-stack-audit.md** - 9 core technologies verified (Mistral AI 8.7/10)
6. **implementation-readiness-report.md** - Gate-check APPROVED ✅
7. **round-1-roadmap.md** - Milestone-based budget, 8-week timeline ✅

---

## Parallel Workflows

**PRIMARY TRACK (Immediate):**
- NEXT_ACTION: Secure pilot network commitments
- TARGET: 2+ networks with commitment letters
- BLOCKING: Yes - required for NLNet application

**SECONDARY TRACK (Post-Approval):**
- NEXT_ACTION: Sprint planning for Phase 4
- NEXT_COMMAND: /sprint-planning
- NEXT_AGENT: scrum-master
- BLOCKING: No - ready to start upon funding approval

---

## Gate-Check Results (2025-11-08)

**Solutioning Gate-Check: ✅ APPROVED**

- ✅ Zero critical issues found
- ✅ 100% alignment: PRD ↔ Architecture ↔ Stories
- ✅ All 35 requirements traced to implementation stories
- ✅ All architectural components have story coverage
- ✅ Tech stack verified + license chain validated
- ✅ Risk level: LOW (all risks have mitigations)
- ✅ MVP scope achievable: 9.5 dev days, well-bounded

**Status:** Ready for Phase 4 upon NLNet approval

---

## Technology Stack (Updated 2025-11-10)

**Backend:**
- FastAPI 0.104+ (MIT)
- Neo4j Community 5.x (GPL3)
- Neo4j Python Driver 5.14+ (Apache 2.0)
- **Mistral AI SDK 1.0+** (Apache 2.0) ← Updated from OpenAI
- Graphiti (Apache 2.0)
- Pydantic 2.5+ (MIT)
- PyJWT 2.8+ (MIT)

**Frontend:**
- Leaflet.js 1.9+ (BSD-2)
- SvelteKit (expected)
- Vanilla JS ES6+

**Infrastructure:**
- Docker + Docker Compose (Apache 2.0)
- IPFS (MIT/Apache)
- Hetzner hosting (EU-based)
- **Mistral AI API** (EU-based, GDPR-native)

**License Strategy:** Apache 2.0 (enables NGI/Erasmus+ derivative funding)

---

## Team & Roles

**Core Team:**
- **Nicolas:** System design, architecture, backend/frontend development, integration
- **Jason:** A2A/LLM integration, pilot network coordination, business strategy
- **Fara:** Communications, pilot network liaison, documentation

**Budget Basis:** €80/hour (Brussels high-end developer rate, estimation only)
**Actual Work:** Performed by core team, milestone-based payments

---

## Timeline

**Phase 2 Completion:** 2025-11-05 (PRD + epics)
**Phase 3 Completion:** 2025-11-08 (architecture + tech verification)
**Round 1 Roadmap:** 2025-11-10 (milestone-based budget + Mistral AI migration)
**NLNet Application:** Target Dec 1, 2025
**Round 1 Execution:** 8 weeks from approval
**MVP Target:** End of Round 1 (working skeleton with 2+ pilot networks)

---

## Funding Strategy

**Round 1 (NLNet Commons Fund):** €18,555 - Walking skeleton MVP (8 weeks)
**Round 2 (NLNet):** ~€20k - Embeddable widgets, 3-5 additional networks (8 weeks)
**Round 3 (NLNet):** ~€25k - Activity signals, governance structures (8 weeks)
**Future (NGI/Erasmus+):** Consortium scaling, temporal analysis, advanced features

**Total NLNet Potential:** ~€60-65k over 3 rounds (24 weeks)

---

## Notes

**Key Strategic Decisions:**
- Mistral AI chosen over OpenAI for EU compliance, GDPR-native infrastructure
- betterCallSaul backend included as Milestone 1 (foundation work eligible for payment)
- 8-week milestones align with NLNet 2-month funding cycles
- Single source of truth: roadmap references sister docs (no duplication)
- Milestone-based budget structure (NLNet payment model)

**Documentation Status:**
- Total: 2,741+ lines across planning, architecture, funding docs
- Single source of truth maintained (roadmap references, doesn't duplicate)
- All docs updated for Mistral AI migration

**Phase 4 Ready:**
- All solutioning complete
- NLNet roadmap ready for application
- Awaiting pilot network commitments
- Sprint planning ready to execute upon funding approval

---

_Last Updated: 2025-11-10 - Round 1 Roadmap Complete ✅ | Mistral AI Migration Complete ✅_
