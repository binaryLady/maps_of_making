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

1. **Establish a trusted digital commons** for makerspace data that communities actively maintain because it's their authoritative listing and people rely on it
2. **Demonstrate that decentralized data governance works** when communities have clear ownership, visibility, and accountability
3. **Create infrastructure for ecosystem transparency** where freshness and activity signals restore trust in distributed maker networks
4. **Build a scalable federation model** that enables regional networks to control their data while contributing to a global resource

**Technical Goals (NLNet Feasibility)**

5. **Prove decentralized architecture viability** using IPFS/distributed storage + open identity standards (SOLID/A2A/blockchain)
6. **Enable agent-driven data stewardship** through A2A protocol compatibility, allowing LLM agents to assist in validation and updates
7. **Ensure data portability and interoperability** via open standards (JSON/Pydantic schemas) and Apache license

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

3. **Ecosystem Perspective (Death Spiral)**
   - Failed maps reduce trust in mapping solutions
   - Networks stop updating because other maps are already stale
   - Each abandoned map reinforces the cycle
   - The ecosystem loses transparent infrastructure

### The Insight: Incentive Misalignment

Previous map projects failed not due to technology, but because they **divorced data maintenance from data value.** Spaces maintained their data once (to be discovered), then had no reason to keep it current.

### Our Approach: Align Incentives Through Decentralization

- **Single source of truth**: One authoritative listing per space, not scattered across multiple maps
- **Visible freshness**: Decay-based metrics (countdown from last verification) show data age and trigger re-verification
- **Activity signals**: Optional integration with space sensors/systems shows communities are actually alive
- **Community ownership**: Spaces control their data (decentralized), building accountability
- **Usefulness**: Embedded everywhere (websites, APIs, agent queries), proving the resource is essential

**Result**: Maintaining current data becomes **rationally justified** because it's their reputation, their discoverability, and the communities rely on it.

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
- **FR009**: Support A2A protocol compatibility for LLM agent queries
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

---

## Non-Functional Requirements

- **NFR001**: Data must be queryable by LLM agents via standardized A2A-compatible interfaces
- **NFR002**: All data and code released under Apache 2.0 license (open source)
- **NFR003**: Decentralized architecture: no single point of failure for data availability
- **NFR004**: Data portability: export all space data in standard formats (JSON with Pydantic schema)
- **NFR005**: Interoperability: use open standards (OpenStreetMap, GeoJSON, JSON-LD) to enable third-party integrations
- **NFR006**: Privacy-preserving: no personal data collection for basic features

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

## Out of Scope (MVP)

- **Phase 4 Automation**: Scheduled updates, bot-assisted validation, webhook automation (future funding)
- **Governance & Consensus**: Formal commons governance structures, multi-signature decisions (Phase 4)
- **Identity Layer Details**: Full SOLID/A2A/blockchain implementation (V2)
- **Community Fund/Incentives**: Monetary incentives, token systems (separate strategic discussion)
- **Mobile Native Apps**: Web-first MVP; native apps considered for later phases
- **Advanced Analytics**: Usage dashboards, member loss correlation studies (research phase)
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
