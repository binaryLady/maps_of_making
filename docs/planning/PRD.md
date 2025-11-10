# Product Requirements Document: Maps of Making

**Project:** Maps of Making - Federated Makerspace Data Commons
**Version:** 1.0 (MVP - NLNet Phase)
**Date:** 2025-11-05
**Level:** 3 Greenfield Software (Federated Digital Commons)

---

## Executive Summary

Maps of Making solves a critical ecosystem failure: **existing makerspace maps are unreliable because they provide no ongoing incentive for communities to maintain them.**

Our solution: **Create a single, trustworthy source of truth so useful and fresh that maintaining it becomes rationally justified.**

The MVP establishes a decentralized federation where participating networks maintain authoritative listings of their spaces, with visible freshness metrics and optional activity signals that prove community livelyness. This removes the "one-shot" incentive problem and transforms maintenance from a burden into a valuable reputation signal.

---

## Goals

**Strategic Goals (NLNet Impact)**

1. **Eliminate duplicate data entry effort** by creating a single, shared source of truth—one verification powers discoverability across the entire ecosystem, not scattered across competing maps
2. **Design and pilot a sustainable commons** for makerspace infrastructure, grounded in Elinor Ostrom's principles for polycentric governance: clear boundaries, collective decision-making, community accountability, and graduated conflict resolution
3. **Enable effortless community engagement** through continuous, low-friction verification signals (magic links, webhooks, local device pings) that make maintaining current data the path of least resistance
4. **Build a decentralized federation model** where participating networks and spaces own their data while contributing to a shared, globally visible resource

**Technical Goals (NLNet Feasibility)**

5. **Prove MVP-first decentralized architecture** using IPFS snapshots + graph-based network intelligence, demonstrating that communities can coordinate without platform gatekeeping
6. **Demonstrate A2A-compatible agent integration** with natural language queries ("Ask the map") as a hero feature that proves data is machine-readable and reveals network intelligence beyond traditional location-based maps
7. **Ensure data portability and community sovereignty** via open standards (JSON/Pydantic schemas), Apache 2.0 license, and federation protocols that enable local replication

---

## Background Context

### The Problem: Why Maps Fail

1. **Makerspace Perspective (Lost Members)**
   - Spaces list themselves once, then have no incentive to maintain multiple map listings
   - No feedback loop showing usage or impact
   - Effort to update scattered maps outweighs unclear, indirect benefits
   - Result: Spaces stop updating, maps become stale

2. **User Perspective (Wasted Resources)**
   - Digital nomads, researchers, travelers depend on current makerspace info
   - Outdated maps lead to wasted travel, time, money
   - No way to know if information is current or abandoned

3. **Ecosystem Perspective (Lost Learning)**
   - Failed spaces close, but their data disappears—no record of why or what was learned
   - Networks can't share lessons from failures across regions (knowledge stays siloed)
   - Platforms like Fablab.io keep inactive spaces visible but provide no context (when? why? what happened?)
   - The ecosystem loses a critical learning resource: how do innovation spaces evolve, adapt, or fail?

### The Insight: Incentive Misalignment + Lost Knowledge

Previous map projects failed not due to technology, but because they:
1. **Divorced data maintenance from data value** (spaces maintained data once, then had no reason to keep it current)
2. **Prevented learning from failure** (when spaces closed, their history was erased or hidden, so networks couldn't learn from the experience)

### Our Approach: Eliminate Coordination Costs, Enable Community Livelyness

**The Problem We Solve:**
Spaces waste effort updating 5+ separate map platforms. Each update feels disconnected from impact. No feedback loop showing "yes, people are actually using this." Result: abandonment.

**Our Strategy:**

- **Single verification point**: Update once → visible everywhere across the ecosystem. Zero duplicate effort.
- **Effortless freshness signals**: Magic links (30 seconds), webhooks (automated), local device pings (fun, effortless). Maintenance becomes low-friction.
- **Real-time livelyness feedback**: Activity webhook → instant freshness update on map. Communities see their verification matters immediately.
- **Community ownership**: Networks and spaces control their data, decide their own participation rules (Ostrom principles).
- **Network intelligence**: Graph reveals collaborations, skills, partnerships—transforming static location data into living ecosystem maps.

**Why It Works:**
Communities stay engaged because:
1. **Effort is minimal** (one verification, optional webhooks)
2. **Impact is visible** (instant map updates, global discoverability)
3. **They're trusted** (they own their data, not a platform)
4. **It's self-reinforcing** (their community relies on current data, so they maintain it)

---

### Grounding in Ostrom Commons Theory

Maps of Making applies Elinor Ostrom's principles for sustainable commons management, proven across fisheries, forests, and community resources worldwide:

| Ostrom Principle | Implementation in Maps of Making |
|------------------|----------------------------------|
| **1. Clear boundaries** | Federated networks define membership; spaces opt-in to participate. Data ownership rules explicit. |
| **2. Collective decision-making** | Networks set verification standards, governance rules, conflict resolution (Phase 4). |
| **3. Monitoring & accountability** | Freshness signals, activity logs, immutable ledger prove participation. Community can report closures. |
| **4. Graduated sanctions** | Status lifecycle (Fresh → Aging → Zombie → Dead) incentivizes timely verification. |
| **5. Conflict resolution** | Closure reports, dispute mechanisms, community trust signals. |
| **6. Recognition** | Each network governs their own data (not top-down platform control). |
| **7. Polycentric governance** | Networks can host federation replicas, participate in governance, apply same rules to their scale. |
| **8. Nested enterprises** | Pilot networks → Regional federations → Global ecosystem (Phase 4+). |

**Why This Matters for NLNet:**
Commons designed to Ostrom principles are **proven to sustain** across decades without external funding or platform gatekeeping. This isn't just a map—it's infrastructure designed to outlive any grant funding.

---

## Functional Requirements

### Core Features (MVP - Phases 1-3)

#### Data Consolidation & Federation (Phase 1)

- **FR001**: Ingest and consolidate makerspace data from multiple network sources (CSV, JSON, API)
- **FR002**: Normalize heterogeneous data schemas into unified Pydantic data model
- **FR003**: Store federated data in decentralized storage (IPFS) with cryptographic integrity
- **FR004**: Maintain mappings between original network sources and unified federation
- **FR005**: Support incremental data updates without full re-ingestion

#### Map Display & Embedding (Phase 2)

- **FR006**: Render unified makerspace dataset on interactive OpenStreetMap interface
- **FR007**: Generate embeddable map widget for external websites/platforms
- **FR008**: Expose API endpoints for programmatic access to makerspace data
- **FR009**: Support A2A protocol compatibility for LLM agent queries (Mistral AI integration, EU-compliant)
- **FR010**: Display freshness metadata (last verified date, decay countdown)

#### Data Verification & Community Maintenance (Phase 3)

- **FR011**: Send magic-link verification requests to space contacts (no account required)
- **FR012**: Allow space representatives to verify/update their own data via simple forms
- **FR013**: Track verification timestamps and maintain audit history
- **FR014**: Support optional activity signal integration (sensor inputs, login logs)
- **FR015**: Update freshness countdown based on verification events
- **FR016**: Display space livelyness status based on activity signals
- **FR017**: Community closure reporting (users can report space as dead/closed)
- **FR018**: Immutable event ledger for verification history, partnerships, state changes

#### Authentication & Access (Minimal - MVP Phase)

- **FR019**: No account management for basic read access (map viewing)
- **FR020**: Magic-link one-time authentication for space data updates
- **FR021**: Prepare infrastructure for future identity layer (SOLID/A2A/blockchain) in Phase 4+

#### Data Governance & Trust (Ledger Architecture)

- **FR022**: Classify data as volatile (operational) vs permanent records (audit trail)
- **FR023**: Version volatile data (keep last 3-5 changes for rollback)
- **FR024**: Immutable ledger for trust-critical events (verifications, closures, partnerships)
- **FR025**: Freshness lifecycle: Fresh (✅) → Aging (⚠️) → Zombie (🧟) → Dead (💀)
- **FR026**: State transitions logged as permanent records
- **FR027**: GDPR-compliant anonymization (delete personal data, preserve structural integrity)
- **FR028**: Preserve temporal context for all spaces (created_at, first_verified, closed_at, closure_reason, reopen_date)
- **FR029**: Timestamp all events in immutable ledger (verifications, state changes, collaborations, partnerships) for ecosystem learning analysis
- **FR030**: Enable rich knowledge graph construction during data ingestion (using graph technology like Graphiti) to preserve context about space evolution, failures, and ecosystem patterns

#### Activity Signals & Webhooks (Phase 3 MVP + Nice-to-Have PoC)

- **FR031**: MVP Phase 3: Magic-link + email verification only (primary verification method)
- **FR031A** (Nice-to-have PoC): Optional webhook URL registration on space profile (Phase 3)
- **FR031B** (Nice-to-have PoC): Mock endpoint `POST /spaces/{space_id}/ping` for testing webhook freshness updates (Phase 3)
- **FR031C** (Future Phase 4+): Real webhook integrations (door sensors, booking systems, MQTT bridge)

#### Network Metadata (Avoids Tech Debt)

- **FR032**: Store network metadata in unified schema (name, website, contact_email, logo_url, region, description)
- **FR033**: Support network data ingestion from CSV/JSON or parallel backend project API
- **FR034**: Render network detail views (Phase 2+): network profile, member count, location map
- **FR035**: Network-branded embeddable widgets (Phase 3+): networks embed map showing only their spaces

---

## Non-Functional Requirements

- **NFR001**: Data must be queryable by LLM agents via standardized A2A-compatible interfaces (Mistral AI integration)
- **NFR002**: All data and code released under Apache 2.0 license (open source)
- **NFR003**: Decentralized architecture: no single point of failure for data availability
- **NFR004**: Data portability: export all space data in standard formats (JSON with Pydantic schema)
- **NFR005**: Interoperability: use open standards (OpenStreetMap, GeoJSON, JSON-LD) to enable third-party integrations
- **NFR006**: Privacy-preserving: no personal data collection for basic features
- **NFR007**: EU data sovereignty: use EU-based infrastructure (Hetzner hosting, Mistral AI) for GDPR-native compliance

---

## User Journeys

### Journey 1: Space Operator Verifies & Maintains Data

**Actor**: Space manager at a participating network

1. Receives email with magic link: "Verify your space's info on Maps of Making"
2. Clicks link → Simple form shows current data: name, address, hours, services
3. Reviews and updates any changed information (opening times, equipment list, contact)
4. Clicks "Verify" → Data timestamp updated, freshness countdown resets
5. Can optionally connect activity signal (light sensor, login system)
6. Space appears "fresh ✅" on the public map; older spaces show "update needed ⚠️"

**Value**: 2-minute process that maintains their reputation and ensures people can actually find them

---

### Journey 2: User/Researcher Finds & Embeds Map

**Actor**: Digital nomad, university researcher, or website manager

1. Discovers Maps of Making embedding on a network's website or research page
2. Views interactive map with freshness indicators showing which spaces are currently active
3. Clicks space → sees: address, services, hours, **when data was last verified**, activity signals
4. Trusts the data because freshness is visible
5. Uses data for trip planning or research

**Value**: Reliable, current information that's worth trusting

---

### Journey 3: LLM Agent Queries Map for Space Information

**Actor**: AI agent assisting user planning

1. User asks: "What makerspaces are active in Berlin right now?"
2. Agent queries Maps of Making API via A2A protocol
3. Agent filters by freshness and activity signals, returns only "live" spaces
4. Agent provides verified, current recommendations

**Value**: Agent-driven assistance becomes viable when data is trustworthy and machine-readable

---

## UX/UI Vision

### Core Principles

- **Simplicity over features**: Magic links, no accounts. Minimal friction.
- **Transparency**: Freshness timestamps and activity indicators always visible
- **Decentralized feel**: Clear that communities control their own data, not a proprietary platform
- **Agent-friendly**: Clear, structured data that LLMs can parse and use

### Key Interfaces

1. **Public Map View**: Interactive OSM-based map showing spaces, freshness status, activity signals
2. **Space Detail View**: Information card with verification date, decay countdown, activity signals
3. **Space Update Form**: Simple, mobile-friendly form for verification (no login required)
4. **Embed Widget**: Self-contained map widget for external websites
5. **API/Agent Interface**: RESTful API + A2A-compatible endpoints for programmatic access

### Design Constraints

- Mobile-first: operators update data from phones
- Accessibility: WCAG 2.1 AA minimum
- Offline-capable: map can be deployed locally if needed

---

## Epic List

### Epic 1: Data Federation & Consolidation

**Goal**: Establish the foundation—ingest and normalize makerspace data from multiple network sources into a unified, decentralized storage layer.

**Success Criteria**:
- Pilot networks' data consolidated into single Pydantic schema
- Data stored in IPFS with cryptographic integrity
- Mapping maintained between source networks and unified data

**Estimated Stories**: 8-10

---

### Epic 2: Map Display & Public API

**Goal**: Make the federated data accessible and useful—interactive map for humans, standardized APIs for machines.

**Success Criteria**:
- Public interactive map shows all spaces with freshness metadata
- Embeddable widget works on external websites
- A2A-compatible API endpoints allow agent queries
- Data freshness decay visible to users

**Estimated Stories**: 7-9

---

### Epic 3: Verification & Community Maintenance

**Goal**: Solve the maintenance problem—enable spaces to verify their data with minimal friction, establish accountability through freshness signals.

**Success Criteria**:
- Magic-link verification process deployed
- Space operators can update data in <2 minutes
- Verification timestamps and activity signals integrated
- Freshness decay resets on verification events

**Estimated Stories**: 6-8

---

### Epic 4: Activity Signals & Livelyness (Phase 4 - Post-NLNet)

**Goal**: Prove space communities are actually alive by integrating optional activity signals (sensors, logins, etc.).

**Note**: Deferred to NGI/Erasmus+ phases. Infrastructure prepared in Phase 3.

---

### Epic 5: Temporal Ecosystem Analysis & Time-Based Visualization (Phase 4+ - Advanced Learning)

**Goal**: Enable networks to learn from ecosystem evolution by analyzing and visualizing makerspace history across time ranges.

**Why It Matters**:
- Innovation spaces fail—this is normal and valuable learning. We don't erase failures; we preserve them.
- Networks need to understand: Why did spaces close? What patterns exist across regions? What conditions enable success?
- Temporal player enables research on maker ecosystem dynamics, failure patterns, and evolution strategies.

**Success Criteria**:
- Temporal player UI: Scrub through time to see ecosystem state at any date
- Historical queries: "Show me ecosystem in January 2025" or "Which spaces closed in 2024?"
- Pattern analysis: Identify regional trends, closure reasons, revival rates
- Research export: Query results exportable for academic analysis
- Animation: Watch ecosystem evolve over time (space openings, closures, collaborations forming)

**Estimated Stories**: 8-12

**Prerequisites (MVP Phase 1-3)**: Temporal data preservation (FR028-FR030), complete implementation ensures this epic is unblocked.

---

## Out of Scope (MVP)

- **Phase 4 Automation**: Scheduled updates, bot-assisted validation, webhook automation (future funding)
- **Governance & Consensus**: Formal commons governance structures, multi-signature decisions (Phase 4)
- **Identity Layer Details**: Full SOLID/A2A/blockchain implementation (V2)
- **Community Fund/Incentives**: Monetary incentives, token systems (separate strategic discussion)
- **Mobile Native Apps**: Web-first MVP; native apps considered for later phases
- **Temporal Player & Historical Analytics**: Time-based ecosystem visualization, pattern analysis, research exports (Phase 4+ - see Epic 5)
- **Horizontal Expansion**: Focus on pilot networks first; global scaling in NGI phase

---

## Success Metrics (NLNet Phase)

### Primary Metric: Data Freshness

- **Target**: Average space data freshness of ≤60 days across pilot networks by end of NLNet phase
- **Decay Model**: 1-year evaluation window; gradual freshness decay from 100% (verified) to 0% (stale)
- **Rationale**: Proves communities are maintaining data because it's their reputation

### Secondary Metrics

- **Network participation**: % of spaces in pilot networks with at least one verification
- **Activity signal adoption**: % of spaces with optional sensors/signals integrated
- **External embedding**: # of websites/platforms using the map widget
- **Agent queries**: # of API queries via A2A protocol (if applicable)

---

## Technical Approach (Summary)

- **Architecture**: Decentralized federation with IPFS storage, distributed across pilot networks
- **Data Format**: JSON with Pydantic schemas for validation and portability
- **Identity**: Magic links (MVP); SOLID/A2A/blockchain prepared for Phase 4
- **Infrastructure**: EU-based (Hetzner hosting, Mistral AI for LLM queries, GDPR-native)
- **License**: Apache 2.0 (enables NGI/Erasmus+ derivative funding)
- **Standards**: OpenStreetMap, GeoJSON, A2A protocol, open formats

---

## Assumptions & Constraints

### Assumptions
- Pilot networks have existing makerspace databases (CSV/JSON/APIs) to consolidate
- Network leaders commit to promoting verification to their member spaces
- Spaces have email contacts for magic-link outreach
- A2A protocol is suitable for agent integration (to be validated in Phase 1)

### Constraints
- MVP limited to 3-5 pilot networks (capacity for federation complexity)
- No account management in MVP (simplifies Phase 3)
- Activity signal integration is optional in MVP (reduces Phase 3 scope)
- Budget must cover data migration + federation setup + map platform + verification flow

---

## Next Steps

1. **Architect Phase** (Architect Agent): Technical architecture design, data model, storage strategy
2. **Sprint Planning** (Scrum Master): Break epics into detailed stories and task plan
3. **Development**: Begin Phase 1 (Data Federation)

---

_Document prepared for NLNet Commons Fund application and consortium recruitment (Vulca Seminar 2025)_
