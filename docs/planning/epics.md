# Implementation Roadmap: Maps of Making

**Project:** Maps of Making - Federated Makerspace Data Commons
**Level:** 3 Greenfield (MVP - NLNet Phase)
**Status:** Story breakdown for development planning
**Date:** 2025-11-05

---

## Epic 1: Data Federation & Consolidation

**Goal**: Ingest and consolidate makerspace data from pilot networks into a unified, decentralized storage system with cryptographic integrity. This establishes the foundation for all downstream features.

**MVP Scope**: 3-5 pilot networks, existing data sources (CSV/JSON/API)

---

### Story 1.1: Data Schema Design & Pydantic Model

**As a** data engineer,
**I want** to define a unified Pydantic schema for makerspace data,
**So that** heterogeneous data from different networks can be normalized and validated.

**Acceptance Criteria:**
1. Pydantic model defined covering: space name, address, coordinates, hours, equipment, contact, description
2. Schema supports optional fields (activity sensor integration prepared for Phase 4)
3. Schema documented with examples in project README
4. Schema exportable as JSON-LD for interoperability
5. Version control established (schema versioning strategy defined)

**Prerequisites:** None

**Effort:** 4 hours

---

### Story 1.2: Data Ingestion Pipeline - CSV/JSON

**As a** federation admin,
**I want** to import makerspace data from CSV and JSON files,
**So that** pilot networks can contribute their existing databases.

**Acceptance Criteria:**
1. CLI tool accepts CSV/JSON files with flexible column mapping
2. Data validated against Pydantic schema; errors reported clearly
3. Mappings saved for incremental updates (don't re-ingest entire files)
4. Pilot network source maintained in metadata (traceability)
5. Duplicate detection logic implemented (same space from multiple sources)

**Prerequisites:** Story 1.1

**Effort:** 6 hours

---

### Story 1.3: IPFS Storage & Cryptographic Integrity

**As a** federation maintainer,
**I want** to store consolidated data in IPFS,
**So that** the dataset is decentralized, immutable, and verifiable.

**Acceptance Criteria:**
1. IPFS integration configured (local node or pinning service)
2. Consolidated dataset serialized to IPFS with content hash
3. Hash verified on retrieval (integrity checking)
4. Version history maintained (IPFS pointers to previous snapshots)
5. Documentation on how to run IPFS locally or use pinning service

**Prerequisites:** Story 1.1, 1.2

**Effort:** 5 hours

---

### Story 1.4: Source Network Mapping & Audit Trail

**As a** network lead,
**I want** to see how my network's data maps to the unified federation,
**So that** I can trust the consolidation and verify accuracy.

**Acceptance Criteria:**
1. Mapping table shows: original source → unified ID → current value
2. Audit trail tracks: when data ingested, by whom, from which source
3. Conflict resolution log if same space appears in multiple sources
4. Export mapping as CSV for network review
5. Manual override capability for network leads (prepare for Phase 3)

**Prerequisites:** Story 1.2

**Effort:** 4 hours

---

### Story 1.5: Incremental Update Mechanism

**As a** federation admin,
**I want** to update the dataset incrementally (not re-ingest entire sources),
**So that** pilot networks can push changes via API/webhook in later phases.

**Acceptance Criteria:**
1. Incremental update pipeline designed (insert/update/delete operations)
2. Rollback capability if update fails validation
3. Change log maintained (what changed, when, from which source)
4. Prepared for API integration in Phase 3 (not implemented yet, just architecture)
5. Documentation on update workflow

**Prerequisites:** Story 1.1, 1.3

**Effort:** 5 hours

---

## Epic 2: Map Display & Public API

**Goal**: Make the federated dataset accessible and useful—interactive map for humans, APIs for machines. Establish the "usefulness" that incentivizes maintenance.

**MVP Scope**: Public OSM-based map, read-only API, A2A protocol compatibility

---

### Story 2.1: Interactive OpenStreetMap Display

**As a** user,
**I want** to see all makerspace locations on an interactive map,
**So that** I can discover spaces and plan visits.

**Acceptance Criteria:**
1. Map interface displays all spaces as markers on OpenStreetMap
2. Markers color-coded by freshness status (fresh/stale/unknown)
3. Markers include basic info on hover (name, location, freshness)
4. Map supports zoom, pan, search by location or name
5. Mobile-responsive design
6. No tracking or analytics collection (privacy-first)

**Prerequisites:** Story 1.3 (data available in IPFS)

**Effort:** 6 hours

---

### Story 2.2: Space Detail View

**As a** user,
**I want** to click a space and see full information including verification timestamp and freshness decay,
**So that** I can assess current accuracy before visiting.

**Acceptance Criteria:**
1. Detail view shows: name, address, hours, equipment, contact, description
2. Freshness metadata displayed: last verified date, days since verification, decay countdown
3. Activity signal status shown if integrated (e.g., "Last activity: 2 days ago")
4. Link to verification update (prepared for Phase 3)
5. Mobile-friendly layout
6. Shareable link to space detail view

**Prerequisites:** Story 2.1

**Effort:** 4 hours

---

### Story 2.3: Embeddable Map Widget

**As a** network website admin,
**I want** to embed Maps of Making on my website,
**So that** my members see the federated map with no technical setup.

**Acceptance Criteria:**
1. Self-contained widget code (HTML embed snippet)
2. Widget displays map with spaces from specific network (configurable)
3. Widget respects external site styling/branding (customizable colors, sizes)
4. Widget loads map data independently (doesn't break if main site down)
5. Documentation and examples for embedding

**Prerequisites:** Story 2.1

**Effort:** 5 hours

---

### Story 2.4: RESTful API for Makerspace Data

**As a** developer,
**I want** to query makerspace data via a simple REST API,
**So that** I can build third-party applications using the federated dataset.

**Acceptance Criteria:**
1. API endpoints: GET /spaces (all), GET /spaces/{id} (single space), GET /spaces?filter=... (by name, location, equipment)
2. Response format: JSON with consistent schema
3. API returns freshness metadata for each space
4. Pagination support for large result sets
5. Rate limiting configured (prevent abuse)
6. API documentation (OpenAPI/Swagger)
7. CORS enabled for browser-based clients

**Prerequisites:** Story 1.3 (data available)

**Effort:** 6 hours

---

### Story 2.5: A2A Protocol Compatibility for Agents

**As a** LLM agent,
**I want** to query Maps of Making using A2A protocol,
**So that** I can provide accurate makerspace recommendations to users.

**Acceptance Criteria:**
1. A2A-compatible endpoint defined (or HTTP API documented for agent interpretation)
2. Agent can query by: location (lat/lon + radius), keyword (equipment), freshness filter (only recent data)
3. Response format suitable for agent interpretation (clear, structured JSON)
4. Example agent prompts documented
5. Test integration with at least one LLM API (e.g., OpenAI function calling)
6. Agent can filter by freshness (e.g., "spaces verified in last 30 days")

**Prerequisites:** Story 2.4

**Effort:** 5 hours

---

## Epic 3: Verification & Community Maintenance

**Goal**: Solve the core maintenance problem—enable spaces to verify/update their data with minimal friction. Establish accountability through freshness signals.

**MVP Scope**: Magic-link verification, simple update form, freshness tracking

---

### Story 3.1: Magic-Link Generation & Email System

**As a** federation admin,
**I want** to send magic-link verification requests to space contacts,
**So that** spaces can verify their data without creating accounts.

**Acceptance Criteria:**
1. Magic-link token generation (one-time, time-limited, cryptographically secure)
2. Email templates designed (friendly, clear calls-to-action)
3. Email system integrated (SMTP or email service provider)
4. Token expiry enforced (e.g., 7 days, then require new link)
5. Link tracking (when sent, to whom, if clicked) for monitoring
6. Logging for debugging (no personal data in logs)
7. Handling for bounced/invalid emails (retry logic, admin alerts)

**Prerequisites:** Story 1.1 (have contact data), Story 2.2 (space detail view exists)

**Effort:** 5 hours

---

### Story 3.2: Space Data Verification Form

**As a** space operator,
**I want** to click a magic link and verify/update my space information,
**So that** my data stays current and my space remains visible on the map.

**Acceptance Criteria:**
1. Form pre-populated with current data from federation
2. Operator can edit: name, address, hours, equipment, contact, description
3. Form validates against Pydantic schema before submission
4. Simple UX: 3-5 fields to edit, obvious "Verify" button
5. Mobile-friendly (operators likely on phones)
6. Confirmation page after submission with next steps
7. No account creation required (token-based authentication only)
8. Error messages clear and actionable

**Prerequisites:** Story 3.1, Story 2.2

**Effort:** 5 hours

---

### Story 3.3: Verification Timestamp & Freshness Tracking

**As a** federation system,
**I want** to record verification timestamps and update freshness decay,
**So that** the map can show which data is current and trustworthy.

**Acceptance Criteria:**
1. Verification event logged: timestamp, space ID, operator, data changed (yes/no)
2. Freshness timestamp updated in IPFS dataset
3. Freshness decay recalculated (resets to "fresh" on verification)
4. Historical verification data maintained (for research/analytics)
5. Decay model: 1-year window with configurable thresholds (e.g., 90 days = stale)
6. API returns freshness metadata (last_verified, days_since_verification, freshness_percentage)
7. Map UI updates in real-time to show refreshed status

**Prerequisites:** Story 1.3, 3.2

**Effort:** 4 hours

---

### Story 3.4: Activity Signal Integration - Optional Layer

**As a** space operator,
**I want** to optionally connect an activity signal (sensor, login system, etc.),
**So that** the map can show that my community is actually alive.

**Acceptance Criteria:**
1. Activity signal interface designed (abstraction layer for different signal types)
2. Support for: webhook ingestion, polling APIs, sensor data feeds (prepared for Phase 4)
3. Activity signal optional (doesn't block basic verification flow)
4. When activity detected, freshness countdown resets (proof of livelyness)
5. Activity status displayed on space detail view (e.g., "Last activity: 2 hours ago")
6. Documentation for space operators on connecting signals
7. Example integrations provided (light sensor, login system webhooks)

**Prerequisites:** Story 3.3

**Effort:** 6 hours

---

### Story 3.5: Verification Campaign Management

**As a** federation/network admin,
**I want** to manage verification campaigns (send links in batches, track response rates),
**So that** I can keep the dataset fresh and monitor participation.

**Acceptance Criteria:**
1. Admin interface to: view all spaces, filter by last verification date, select batch to verify
2. Bulk magic-link generation and email sending
3. Campaign dashboard: spaces contacted, % verified, average response time
4. Follow-up logic (send reminders to unverified spaces after N days)
5. Reporting: which spaces haven't been verified in 90+ days (stale)
6. Network-specific campaigns (network lead can campaign only their spaces)
7. Audit trail of all campaigns and sends

**Prerequisites:** Story 3.1, 3.2

**Effort:** 6 hours

---

## Phase 4: Activity Signals & Automation (Post-NLNet - Deferred)

**Note**: Phase 4 (automation, advanced activity signals, governance) is deferred to NGI/Erasmus+ funding. MVP infrastructure prepares for Phase 4 but does not implement it.

**Deferred stories include:**
- Webhook automation for scheduled updates
- Bot-assisted data validation
- Advanced sensor integrations
- Governance structures (consensus, multi-sig)
- Community incentive models

---

## Epic Sequencing Logic

**Why this order?**

1. **Epic 1 first**: Foundation—data must be consolidated and stored before anything else
2. **Epic 2 second**: Builds on Epic 1; establishes "usefulness" that makes verification worthwhile
3. **Epic 3 third**: Leverages Epic 2; closes the loop—enable communities to maintain their data now that they see it's useful

**No forward dependencies**: Epic 2 doesn't depend on Epic 3 (read-only map works without verification). Epic 3 uses Epic 2 (spaces see their updated data on map after verification).

---

## Development Notes

### Assumptions
- Pilot networks provide data in accessible formats (CSV/JSON)
- IPFS suitable for MVP (may revisit for scaling in Phase 4)
- Magic-link email authentication sufficient for MVP (full identity layer in Phase 4)
- A2A protocol compatible with REST API (to be validated in Story 2.5)

### Open Questions
- Activity signal types: prioritize light sensor or login webhooks first?
- Freshness decay thresholds: 90 days "stale," 365 days "very stale"?
- Follow-up email frequency: when to remind operators to re-verify?
- Network-specific permissions: should networks only see/manage their own spaces, or all?

### Risk Mitigation
- **Email deliverability**: Test with multiple providers; have fallback contact mechanisms (SMS, manual contact)
- **Data privacy**: Keep minimal personal data; use GDPR-compliant practices
- **IPFS reliability**: Consider pinning service if self-hosted IPFS unreliable
- **API adoption**: If agents don't adopt A2A protocol, REST API alone sufficient; can iterate

---

## Story Count & Effort Estimation

| Epic | Stories | Estimated Hours | Dev Days (8h/day) |
|------|---------|-----------------|-------------------|
| Epic 1 | 5 | 24 | 3 |
| Epic 2 | 5 | 26 | 3.25 |
| Epic 3 | 5 | 26 | 3.25 |
| **Total** | **15** | **76** | **9.5** |

*Note: Estimates assume experienced full-stack developer. Adjust for team skill level.*

---

## Next Phase: Sprint Planning

This epic breakdown is ready for the **Scrum Master agent** to create a detailed sprint plan, assigning stories to sprints and creating tasks for each story.

---

_Epic breakdown prepared for NLNet Commons Fund application and development team handoff_
