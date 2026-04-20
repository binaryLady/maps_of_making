# Brainstorm Summary: Maps of Making Data & UX Strategy
**Date:** 2025-11-11
**Participants:** Design team brainstorm session
**Status:** Documented & Integrated into Primary Docs
**Next Step:** Sprint planning (Phase 1 story breakdown)

---

## Executive Summary

This document locks down key brainstorm decisions made on 2025-11-11 regarding:
1. **What data to display** (Tier 1 + Tier 3, not equipment)
2. **How to display it** (parametrized embeds → web components by contribution tier)
3. **How to value it** (skills-first, partnerships as graph edges, temporal preservation)
4. **How to operate it** (internal admin dashboard for benchmarking)

**All decisions integrated into:**
- `docs/planning/PRD.md` (FRs updated)
- `docs/architecture/architecture.md` (technical implementation locked in)

---

## 1. Data Model Decision: Skills-First Instead of Equipment

### Decision
Focus on **competencies/skills** (with anonymized proficiency counts) instead of equipment lists.

### Rationale
- **Equipment changes too fast** — spaces update equipment lists rarely, outdated burden
- **Skills are identity** — "we teach advanced metalworking" is core to space reputation
- **Anonymized counts tell stories** — "3 professionals, 5 advanced, 2 intermediate in metalworking" reveals ecosystem strength without privacy burden
- **Scalable querying** — skill-based recommendations possible at scale

### Implementation (architecture.md Section 2)
```
Space -[:HAS_SKILL {level, professionals, advanced, intermediate, novice}]-> Skill
```

**Data stays anonymized:**
- ✅ No individual instructor names in database
- ✅ Counts are aggregated: "8 professionals teach ceramics"
- ✅ GDPR-friendly: space can be anonymized, skill relationships preserved

### Outcome
- Spaces present themselves as "skill communities" not "equipment inventories"
- Researchers can query: "Which regions have advanced textile instruction?"
- Map shows skill diversity: **Small icon + text: "5 advanced, 3 pro" on hover**

---

## 2. Data Display: Two-Tier Approach

### Decision
**Tier 1 (Essential):** Freshness + location + verification status
**Tier 2 (Optional):** Equipment/capabilities (link to website instead)
**Tier 3 (Network Intelligence):** Partnerships + skill clusters + ecosystem relationships

### Rationale
- **Tier 2 deprecated:** Too much to maintain. Link to their website for current details.
- **Tier 1 + 3 = differentiator:** Freshness proves they're alive. Partnerships reveal ecosystem.
- **Single source of truth:** Website = canonical source for capabilities. Map = canvas for relationships.

### What Map Shows
| Element | Why It Matters |
|---------|----------------|
| **Freshness status (✅⚠️🧟💀)** | Users know if space is actually open |
| **Skills taught (aggregated counts)** | Searchable by skill type + proficiency |
| **Confirmed partnerships (edges)** | Reveals collaboration opportunities |
| **Network affiliation** | Shows which federation governs this space |
| **Last verified date** | Transparency = trust building |

### What Map Does NOT Show
- ❌ Detailed equipment lists (link to website instead)
- ❌ Opening hours (captured but not prominent)
- ❌ Contact info (visible only on detail view)

---

## 3. Freshness Decay: Activity-Based Model (Option B)

### Decision
**Primary:** Magic-link verification (manual)
**Secondary:** Optional activity signals (webhooks, sensors) reset decay
**Fallback:** Time-based thresholds if neither happens

### Decay Timeline
```
Day 0-14:   Fresh ✅         (verified or active)
Day 14-30:  Aging ⚠️         (send reminder email)
Day 30-90:  Zombie 🧟        (red alert, escalate)
Day 90+:    Dead 💀           (remove unless activity resumes)
```

### Activity Signal Strategy
- **Phase 1 (MVP):** Magic-link verification only
- **Phase 3 (PoC):** Optional webhook endpoint for testing
- **Phase 4+:** Real integrations (door sensors, calendar, MQTT)

### Why Activity-Based?
- Spaces don't want to re-verify monthly if they're clearly active
- "Keep pinging to stay fresh" nudges automation adoption
- Webhook ping = lightweight proof of livelyness (no manual effort)

**Implementation:** `docs/architecture/architecture.md` Section 7

---

## 4. Partnerships: Bidirectional with Handshake Validation

### Decision
Partnerships require two-step confirmation:
1. **Space A suggests partnership** → Creates pending relationship
2. **Space B validates** → Activates edge visibility on map

### Why Handshake?
- ✅ Prevents spam (false partnerships)
- ✅ Both parties intentionally commit
- ✅ "First mover advantage" nudges behavior (be the first to suggest!)
- ✅ Simple trust signal without central authority

### Graph Implementation
```cypher
// Pending: A suggests, waiting for B confirmation
(Space A)-[:SUGGESTS_PARTNERSHIP {status: "pending"}]->(Space B)

// Active: Both validated
(Space A)-[:PARTNERSHIP {type: "skill_exchange"}]->(Space B)
```

### Partnership Types (Tracked)
- `skill_exchange` — complementary skills
- `mentorship` — one teaches the other
- `co_hosting` — share events/workshops
- `resource_sharing` — share equipment/space

### Value
- **For spaces:** Discover collaborators with complementary skills
- **For researchers:** See ecosystem clusters & partnership strength
- **For LLM agents:** "Find spaces collaborating on X" queries possible

---

## 5. Temporal Data: What to Preserve (Immutable History)

### Decision
Create immutable ledger for ecosystem learning. Do NOT delete when spaces close.

### Events to Preserve (Immutable)
- ✅ Space **birth** (created_at)
- ✅ Space **death** (closed_at, closure_reason)
- ✅ **Relocations** (moved from address A to address B with dates)
- ✅ **Ownership changes** (when hands changed)
- ✅ **Status transitions** (active → dormant → zombie → dead → reactivated)
- ✅ **Skill additions/removals** (when community lost/gained expertise)
- ✅ **Partnership formation/dissolution** (when collaborations started/ended)
- ✅ **Verification events** (each magic-link verification timestamped)

### Volatile Data (Keep Latest + 3-5 History)
- Opening hours (may change seasonal)
- Contact email (may rotate)
- Website URL
- Description text

### Why Preserve Everything?
- **Researchers can analyze:** "Which spaces closed in 2024? Why? Regional patterns?"
- **Networks learn from failure:** "What conditions led to closure? Can we replicate success?"
- **Ecosystem memory:** When a space closes, its story lives on (not erased)

**Implementation:** `docs/architecture/architecture.md` Section 2 (Space node)

---

## 6. Embedding Strategy: Tiered by Contribution Level

### Decision
Hybrid approach: start simple (iframe), evolve with contributors

### Phase 1 (MVP): Parametrized URL + Iframe
**For:** Non-technical space operators
**Effort:** Copy-paste one line
**Capability:** Basic filtering (network, skills, freshness)

```html
<iframe src="https://maps.making/embed?
  center=50.8503,4.3517&
  network=brussels&
  freshness=30d">
</iframe>
```

**Use Cases:**
- Notion page
- WordPress site
- Any website with iframe support
- Shareable URL

### Phase 2 (Advanced): Web Component Library
**For:** Developers, contributors who want customization
**Effort:** JavaScript + callbacks + styling
**Capability:** Dynamic filters, event handlers, React/Vue integration

```html
<script src="https://maps.making/embed.js"></script>
<div id="map" data-network="brussels"></div>
<script>
  MapsOfMaking.embed('#map', {
    onSpaceClick: (space) => customAction(space),
    theme: 'dark'
  });
</script>
```

### Tie to Contribution Tiers
- **Tier 1 (Basic):** Can use iframe embeds
- **Tier 2+ (Developers/Coordinators):** Access to web component + API docs + feature requests

### Dashboard Feature (Phase 1)
Space operators log in → "Get Embed Code" button → form to customize → copy-paste iframe

---

## 7. Admin Dashboard: Internal Operations Only

### Decision
**NOT user-facing.** Internal tool for team to monitor system health, costs, data quality.

### Monitoring Priorities (in order)

**Priority 1: System Health** (real-time)
- API response times (p50/p95/p99)
- Error rates & specific errors
- Uptime %
- Neo4j connection pool status
- IPFS snapshot health

**Priority 2: Traffic & Costs** (weekly)
- API request volume by endpoint
- Mistral AI token usage / cost per day
- Infrastructure costs (Hetzner, Mistral, bandwidth)
- Embed view counts (iframe load tracking)

**Priority 3: Data Quality** (daily)
- Freshness distribution (% Fresh/Aging/Zombie/Dead)
- Aging spaces requiring outreach
- Verification rate by network
- Partnership adoption %
- Unresolved closure reports

**Priority 4: Federation Health** (weekly)
- IPFS replication status
- Validator node sync (Phase 4+)
- Data integrity checks

### Implementation
Endpoint: `GET /admin/dashboard?api_key=...` returns JSON

**Phase 1:** JSON endpoint only
**Phase 2+:** Simple HTML dashboard + Slack alerting

---

## 8. LLM Agent Queries: Deferred (Deep Dive Required)

### Status
**Decision:** Not finalized. Requires roleplay & deeper dive.

### What We Know
- Agents must access graph relationships (partnerships, skills, collaborations)
- Response must include freshness metadata (only verified spaces)
- A2A protocol compatibility needed (Mistral AI function calling)

### What We Need to Design
- **Exact response format:** What does agent get back? Just spaces? Plus recommendations? Plus reasoning?
- **Query filtering:** How do agents express "advanced electronics teachers near Berlin"?
- **Reasoning chain:** Can agent explain why Space A + Space B are recommended together?

### Next Step
**Roleplay 3-5 agent interaction flows** (user question → agent query → API response → user answer)

---

## 9. Single Source of Truth Maintenance

### Documentation Strategy
To prevent drift, documents are **layered by audience:**

| Document | Purpose | Update Frequency |
|----------|---------|------------------|
| `PRD.md` | Requirements & user stories | Per sprint |
| `architecture.md` | Technical implementation | As decisions lock in |
| `BRAINSTORM-SUMMARY.md` | Decision log & traceability | Locked (this doc) |
| `round-1-roadmap.md` | Sprints & milestones | Per sprint |

### Cross-References
- PRD references architecture for technical details ("see architecture.md Section 7")
- Roadmap references both PRD & architecture
- Brainstorm summary documents decisions, references where implemented

### Never Duplicate
If decision made → update ONE source document → cross-ref from others

---

## 10. Open Questions (Deferred)

### Tier 3 Node Operators (Phase 4)
1. Should Tier 3 customize what appears on their replica? (region-only views?)
2. Do they get write privileges or read-only access?
3. "Notarization" model (network validates partnerships in their region)?

### Temporal Data Privacy
1. If space relocates, can researchers query "all addresses this space ever had"?
2. Or just "space X as of today"?

### OSM Embedding Limits
1. How to handle massive deployments? (caching, CDN, etc.)
2. Rate limiting strategy for embeds?

**→ Evaluate when required (Phase 2+)**

---

## 11. Integration Checklist

### Updated Documents
- ✅ `PRD.md` — FRs added for skills, partnerships, embedding, temporal data, admin dashboard
- ✅ `architecture.md` — Sections 2, 7, 9, 11 updated with decision implementations
- ✅ `tech-stack-audit.md` — No changes needed (verified, still good)
- ✅ `round-1-roadmap.md` — Unchanged (still valid, decisions fit within budget)

### Ready for Sprint Planning
All decisions documented & cross-referenced. Next step: **Break epics into user stories** with acceptance criteria.

---

## Appendix: Decision Traceability

| Decision | Rationale Doc | Implementation Doc | Status |
|----------|---------------|-------------------|--------|
| Skills-first model | Section 1 | PRD FR021A-D, arch §2 | ✅ Locked |
| Tier 1+3 display | Section 2 | PRD FR020-021, arch §9 | ✅ Locked |
| Activity-based decay | Section 3 | arch §7, PRD FR025 | ✅ Locked |
| Bidirectional partnerships | Section 4 | PRD FR021E-I, arch §2 | ✅ Locked |
| Temporal preservation | Section 5 | PRD FR028-030, arch §2, §8 | ✅ Locked |
| Embedded maps (tiered) | Section 6 | PRD FR036-037, arch §9 | ✅ Locked |
| Admin dashboard | Section 7 | arch §11 | ✅ Locked |
| LLM agent queries | Section 8 | TBD (Phase 1 design task) | ⏳ Deferred |

---

_Document prepared: 2025-11-11_
_Brainstorm participants: Design team_
_Status: Ready for Phase 1 Sprint Planning_
