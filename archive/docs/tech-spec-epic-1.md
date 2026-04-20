# Technical Specification: Epic 1 - Data Federation & Consolidation

**Project:** Maps of Making - Federated Makerspace Data Commons
**Epic:** 1 - Data Federation & Consolidation
**Version:** 1.0
**Date:** 2026-01-12
**Author:** BMAD Tech Spec Workflow

---

## 1. Overview & Objectives

### Executive Summary

Epic 1 establishes the **foundation for Maps of Making**: a unified, decentralized data federation that consolidates makerspace information from multiple network sources (pilot networks contributing via CSV/JSON) into a single source of truth.

**Core Problem Solved:**
- Spaces waste effort updating 5+ separate maps
- Each map becomes stale independently
- Networks lose critical coordination infrastructure

**Epic 1 Solution:**
- Create a unified **Pydantic schema** that normalizes heterogeneous network data
- Ingest and consolidate data from pilot networks
- Store federated dataset in **IPFS** with cryptographic integrity
- Maintain **audit trail and mappings** showing original source → unified federation
- Prepare infrastructure for **incremental updates** (API/webhook integration in Phase 2+)

**Success Outcome:**
By the end of Epic 1, the Maps of Making platform holds a single, trustworthy, decentralized dataset of 20-50 spaces from 2-3 pilot networks, ready for visualization in Epic 2.

### In-Scope & Out-of-Scope

**In Scope:**
- Pydantic schema design (handles space metadata, temporal tracking, audit needs)
- CSV/JSON ingestion pipeline with flexible column mapping
- IPFS storage integration with integrity verification
- Source network mapping and audit trail
- Incremental update mechanism architecture (not full API implementation)
- Data validation and error handling

**Out of Scope (Phase 2+):**
- REST API endpoints (Epic 2)
- Web-based verification forms (Epic 3)
- Activity signal webhooks (Phase 3 PoC, Phase 4 full)
- Multi-network governance rules (Phase 4)
- GraphDB relationship extraction (deferred; data stored in IPFS as JSON, ingestion to Neo4j happens in Phase 2)

### System Architecture Alignment

Epic 1 delivers the **data layer** that feeds the architecture:

```
Epic 1 Output (IPFS Dataset)
         ↓
Epic 2 (Neo4j graph ingestion, API endpoints, map display)
         ↓
Epic 3 (Verification forms, freshness tracking, activity signals)
```

**Key Architectural Decisions Referenced:**
- **IPFS Storage**: Decentralized, immutable snapshots (Section 4 of architecture.md)
- **Pydantic Validation**: Data validation before ingestion (architecture.md Section 2)
- **Neo4j Graph Schema**: Epic 1 data structured to feed into graph relationships (architecture.md Section 2)
- **Temporal Tracking**: Preserve space lifecycle (created_at, first_verified, closed_at, relocated_from) for ecosystem learning

---

## 2. Detailed Design

### 2.1 Services & Modules

| Module | Responsibility | Input | Output | Owner |
|--------|---|---|---|---|
| **PydanticSchemaDefiner** | Design & maintain unified data schema | PRD requirements, network sample data | `schemas.py` (Space, Network, Skill models) | Backend Lead |
| **CSVJSONIngestionPipeline** | Parse diverse network formats, apply mappings | CSV/JSON files, column mapping config | Validated space records | Backend Lead |
| **DataNormalizer** | Standardize heterogeneous data into unified schema | Raw network data (various formats) | Pydantic-validated Space objects | Backend Lead |
| **DuplicateDetector** | Identify same space from multiple sources | Normalized space objects | Duplicate clusters + resolution strategy | Backend Lead |
| **IPFSStorageManager** | Serialize and store dataset in IPFS | Consolidated space data (JSON) | IPFS content hash, local backup | DevOps/Backend |
| **IntegrityVerifier** | Verify IPFS content integrity on retrieval | IPFS hash | Verification result (pass/fail) | QA/Backend |
| **SourceMappingTracker** | Maintain audit trail of source → federation mappings | Ingestion events | Mapping table (CSV export) | Backend Lead |
| **ChangeLogManager** | Track what changed, when, from which source | Update operations | Change log (JSON) | Backend Lead |
| **IncrementalUpdateArchitect** | Design (not implement) update pipeline | Epic 1 discoveries, Phase 2 API plans | Update mechanism design doc | Backend Lead |

### 2.2 Data Models (Pydantic)

**Core Entities:**

#### Space Node
```python
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime
from typing import Optional, List

class SpaceNode(BaseModel):
    # Identity
    id: str = Field(..., description="Unique federation ID (slug-based, network-qualified)")
    name: str = Field(..., description="Official space name")

    # Location
    address: str = Field(..., description="Full street address")
    lat: float = Field(..., ge=-90, le=90, description="Latitude")
    lon: float = Field(..., ge=-180, le=180, description="Longitude")

    # Operational
    hours: Optional[str] = Field(None, description="Operating hours (e.g., 'Mon-Fri 9:00-18:00')")
    contact_email: str = Field(..., description="Primary contact email")
    contact_phone: Optional[str] = Field(None, description="Phone number")
    website: Optional[HttpUrl] = Field(None, description="Official website")
    description: str = Field(..., description="Space description / mission statement")

    # Freshness & Status
    last_verified: datetime = Field(..., description="Last verification timestamp")
    last_activity: Optional[datetime] = Field(None, description="Last activity signal timestamp")
    status: str = Field("active", description="active | dormant | closed | relocated")

    # Temporal Data (Immutable - for ecosystem learning)
    created_at: datetime = Field(..., description="When space was established (from network data)")
    first_verified: datetime = Field(..., description="First verification in federation")
    closed_at: Optional[datetime] = Field(None, description="Closure date (if closed)")
    closure_reason: Optional[str] = Field(None, description="Why space closed")
    reopen_date: Optional[datetime] = Field(None, description="Date reopened (if applicable)")
    relocated_from: Optional[str] = Field(None, description="Previous address (if relocated)")
    ownership_changed_at: Optional[datetime] = Field(None, description="Date ownership changed")

    # Network Provenance
    source_network_id: str = Field(..., description="Which network provided this data")
    source_id: Optional[str] = Field(None, description="Original ID in source network")

    # Metadata
    tags: List[str] = Field(default_factory=list, description="Categories (fablab, hackerspace, etc.)")

class NetworkNode(BaseModel):
    id: str = Field(..., description="Network unique ID")
    name: str = Field(..., description="Network name")
    region: str = Field(..., description="Geographic region")
    website: Optional[HttpUrl] = Field(None)
    contact_email: Optional[str] = Field(None)
    logo_url: Optional[HttpUrl] = Field(None)
    description: Optional[str] = Field(None)
    type: str = Field("regional_network", description="fablab_network | hacker_network | maker_network | other")
    created_at: datetime = Field(..., description="When network was established")

class SkillNode(BaseModel):
    id: str = Field(..., description="Skill slug (e.g., 'laser-cutting')")
    name: str = Field(..., description="Skill display name")
    category: str = Field(..., description="Skill category (fabrication, textile, digital, etc.)")

class SpaceHasSkillRelation(BaseModel):
    space_id: str
    skill_id: str
    level: str = Field(..., description="novice | intermediate | advanced | professional")
    professionals: int = Field(default=0, description="Count of professional-level instructors")
    advanced: int = Field(default=0)
    intermediate: int = Field(default=0)
    novice: int = Field(default=0)
    verified_at: datetime = Field(default_factory=datetime.utcnow)
```

**Rationale:**
- **Temporal fields** (created_at, closed_at, relocated_from) preserve ecosystem history for Phase 4 analysis
- **source_network_id + source_id** enable audit trail without exposing internal network IDs
- **Skills + proficiency levels** prepared for Phase 2 graph queries ("find advanced electronics instructors")
- **Pydantic validation** ensures consistency before IPFS storage

---

### 2.3 Data Workflows & Sequencing

#### Workflow 1: Initial Ingestion (CSV/JSON → IPFS)

```
1. Network provides CSV/JSON export
   └─ Admin specifies column mapping (e.g., "column_5" = "address", "column_7" = "website")

2. CSVJSONIngestionPipeline parses file
   └─ Log warnings for missing fields, malformed data

3. DataNormalizer applies mapping rules
   └─ Output: List[SpaceNode] validated against Pydantic schema

4. DuplicateDetector compares against existing dataset
   └─ Flag spaces with same name + address in different networks
   └─ Ask human (SM) for resolution (merge, keep separate, etc.)

5. SourceMappingTracker records:
   - Original network: source_network_id
   - Original ID: source_id
   - Federation ID (generated)
   - Ingestion timestamp
   └─ Export as CSV for network to review

6. IPFSStorageManager serializes consolidated dataset
   └─ Convert to JSON with Pydantic .model_dump()
   └─ Push to IPFS
   └─ Record content hash

7. Integrity verification (on retrieval)
   └─ Fetch from IPFS by hash
   └─ Validate all spaces still match Pydantic schema
   └─ Confirm hash matches recorded value

8. Output: /ipfs/{hash} → Snapshot ready for Phase 2 (Neo4j ingestion)
```

#### Workflow 2: Incremental Update (MVP: Manual)

```
// Phase 1 (MVP): Admin receives CSV of updates
// Phase 2+: API endpoint triggers this (FutureWork)

1. Admin uploads updated CSV (subset of spaces)
2. System identifies spaces by source_id
3. For each update:
   a. Load space from existing IPFS snapshot
   b. Merge update fields (only allow mutable fields: hours, contact, description)
   c. Validate against Pydantic schema
   d. Record change in ChangeLogManager
      └─ What changed (field name, old value, new value)
      └─ When (timestamp)
      └─ From which source
   e. Regenerate IPFS snapshot
   f. Publish new content hash
4. Notify network of update success
```

#### Workflow 3: Duplicate Resolution

```
DuplicateDetector logic:
  For each new space S:
    For each existing space E:
      IF normalized_name(S) == normalized_name(E)
         AND distance(S.address, E.address) < 100m
      THEN:
        Flag as potential duplicate
        Ask SM:
        - Keep separate (different spaces with similar names)
        - Merge (same space, update data)
        - Replace (old data obsolete)
```

---

### 2.4 API Interfaces & Data Contracts

**Note:** Epic 1 does NOT implement API endpoints (that's Phase 2). However, we design data structures ready for Phase 2 REST API and Phase 3 verification forms.

**Internal Python Interfaces (used within Epic 1):**

```python
# CSVJSONIngestionPipeline
def ingest_csv(
    file_path: str,
    column_mapping: Dict[str, str],  # "raw_col_name" -> "space_field_name"
    network_id: str
) -> Tuple[List[SpaceNode], List[IngestionWarning]]:
    """
    Parse CSV, apply mapping, validate, return validated spaces.
    Warnings include: missing required fields, invalid email format, etc.
    """

# IPFSStorageManager
def export_to_ipfs(spaces: List[SpaceNode], networks: List[NetworkNode]) -> str:
    """
    Serialize spaces + networks to JSON
    Push to IPFS
    Return content hash (ipfs://QmXxxx)
    """

def verify_ipfs_integrity(content_hash: str, expected_data: dict) -> bool:
    """
    Fetch data from IPFS
    Verify hash matches
    Validate all objects match Pydantic schema
    Return pass/fail
    """

# SourceMappingTracker
def record_mapping(source_network_id: str, source_id: str, federation_id: str) -> None:
    """Record in mapping table for audit trail"""

def export_mapping_csv(network_id: str) -> str:
    """Export mapping for network review"""
```

---

## 3. Non-Functional Requirements

### Performance

| Requirement | Target | Rationale |
|-------------|--------|-----------|
| CSV ingest rate | ≥1000 spaces/second | Pilot network exports typically <5000 spaces |
| IPFS upload | <30 seconds for 50 spaces | Initial MVP scope |
| Data validation | <100ms per space | Pydantic validation should be fast |
| Duplicate detection | <5 seconds for 50 new spaces | O(n²) acceptable for MVP scope |

### Reliability

- **Data integrity**: IPFS content hash verified on every retrieval (no silent corruption)
- **Ingestion failures**: Partial failures logged; operator can retry
- **Rollback capability**: Keep previous 3 IPFS snapshots so operator can revert bad import
- **Audit trail**: 100% of ingestion events logged with timestamp, source, operator

### Security

- **No authentication needed** for MVP (Epic 1 is backend-only)
- **IPFS hash immutability**: Prevents tampering with stored data
- **Column mapping validation**: Prevent injection attacks (operator specifies mapping, not user-controlled)
- **Email validation**: Pydantic enforces valid email format
- **PII handling**: Personal names NOT stored (only contact email, which is necessary). Skills use anonymized counts (not individual names).

### Observability

**Logging required:**
- Every ingestion event (network, file, row count, warnings)
- Every IPFS upload (content hash, timestamp)
- Every duplicate detected (space names, resolution action)
- Every change in incremental update

**Metrics:**
- Total spaces ingested
- Spaces per network
- Duplicate rate (%)
- Ingestion success rate (%)

---

## 4. Dependencies & Integrations

### External Dependencies

| Dependency | Version | Purpose | License |
|---|---|---|---|
| `pydantic` | 2.5+ | Data validation | MIT |
| `python-ipfshttpclient` | latest | IPFS integration | MIT |
| `python-dotenv` | latest | Environment config | BSD |
| `pandas` | 1.5+ | CSV/Excel parsing (optional for complex mappings) | BSD |
| `python-jose` | 3.3+ | JWT for future API (Phase 2) | MIT |

### Internal Dependencies

- **Phase 2**: Output (IPFS dataset) feeds Neo4j ingestion workflow
- **Phase 3**: IPFS dataset queried by verification form (fetch space data to pre-populate form)

### Configuration

```env
# .env (git-ignored)
IPFS_GATEWAY_URL=http://localhost:5001  # or pinning service URL
IPFS_ENABLE_LOCAL_NODE=true
IPFS_PINNING_SERVICE_API_KEY=...  # if using external pinning

DATABASE_BACKUP_PATH=/mnt/backups/ipfs_snapshots
NETWORK_TIMEZONE=UTC
```

---

## 5. Acceptance Criteria & Traceability

### Acceptance Criteria (from PRD + Epic breakdown)

1. **Data Schema Defined (Story 1.1)**
   - [ ] Pydantic SpaceNode covers: name, address, lat/lon, hours, equipment, contact, description
   - [ ] Schema supports optional fields (activity sensor prep)
   - [ ] Schema documented with examples in README
   - [ ] Exportable as JSON-LD (via Pydantic .model_dump_json())
   - [ ] Version control: schema versioning strategy defined in docs

2. **CSV/JSON Ingestion Works (Story 1.2)**
   - [ ] CLI tool accepts CSV/JSON files
   - [ ] Flexible column mapping supported (e.g., "col_2" → "address")
   - [ ] Data validated against Pydantic; errors reported clearly
   - [ ] Mappings saved for re-use (incremental imports)
   - [ ] Pilot network source maintained in metadata
   - [ ] Duplicate detection implemented

3. **IPFS Storage & Integrity (Story 1.3)**
   - [ ] IPFS integration configured (local node or pinning service)
   - [ ] Dataset serialized to IPFS with content hash
   - [ ] Hash verified on retrieval
   - [ ] Version history maintained (pointer to previous snapshots)
   - [ ] Documentation on IPFS setup

4. **Audit Trail & Mappings (Story 1.4)**
   - [ ] Mapping table: original source → unified ID → current value
   - [ ] Audit trail: what ingested, when, by whom, from which source
   - [ ] Conflict log if same space in multiple sources
   - [ ] Export mapping as CSV
   - [ ] Manual override documented (SM capability)

5. **Incremental Update Architecture (Story 1.5)**
   - [ ] Update pipeline designed (insert/update/delete operations)
   - [ ] Rollback capability (can revert to previous snapshot)
   - [ ] Change log maintained
   - [ ] Prepared for API integration (not implemented, just architecture)
   - [ ] Documentation on update workflow

### Traceability Mapping

| AC # | Spec Section | Component(s) | Test Idea |
|------|---|---|---|
| 1.1-1 | 2.2 Data Models | SpaceNode Pydantic class | Load sample space, validate all fields |
| 1.1-2 | 2.2, 2.3 | Pydantic optional fields | Pass space with/without activity_signal |
| 1.1-3 | README | Documentation | Team reviews; schema clear to 3rd party |
| 1.1-4 | 2.2 | .model_dump_json() | Generate JSON-LD, validate format |
| 1.1-5 | design doc | Schema versioning strategy | Document in /docs/SCHEMA_VERSIONING.md |
| 1.2-1 | 2.1, 2.3 | CSVJSONIngestionPipeline | Parse sample CSV; output validated SpaceNodes |
| 1.2-2 | 2.3 Workflow 1 | ColumnMappingEngine | Specify non-standard columns; verify mapping |
| 1.2-3 | 2.1 | DataNormalizer | Parse malformed CSV; capture errors clearly |
| 1.2-4 | 2.3 | SourceMappingTracker | Re-ingest same CSV; confirm no duplicates |
| 1.3-1 | 2.1, 2.4 | IPFSStorageManager, IPFS config | Configure IPFS; export dataset; note hash |
| 1.3-2 | 2.3 Workflow 1 | IPFSStorageManager | Serialize spaces to JSON; push to IPFS |
| 1.3-3 | 2.4 | IntegrityVerifier | Fetch by hash; validate against schema |
| 1.3-4 | 2.3 Workflow 1 step 7 | Version management | Save multiple IPFS hashes; retrieve old snapshot |
| 1.3-5 | /docs/IPFS_SETUP.md | Configuration | Provide step-by-step IPFS setup guide |
| 1.4-1 | 2.3 Workflow 1 step 5 | SourceMappingTracker | Verify mapping table structure |
| 1.4-2 | 2.1 | ChangeLogManager | Ingest space; verify audit log has timestamp/source |
| 1.4-3 | 2.3 Workflow 3 | DuplicateDetector | Ingest duplicate space; see conflict log |
| 1.4-4 | 2.4 | export_mapping_csv() | Export mapping; verify CSV format |
| 1.4-5 | design doc | Manual override process | Document SM workflow for conflicts |
| 1.5-1 | 2.3 Workflow 2 | IncrementalUpdateArchitect | Design doc describes insert/update/delete |
| 1.5-2 | 2.3 Workflow 2 step 3e | Rollback mechanism | Upload bad data; revert to previous hash |
| 1.5-3 | 2.1 | ChangeLogManager | Update space hours; verify change logged |
| 1.5-4 | 2.3 Workflow 2 | API architecture notes | Notes in design doc: "Phase 2 REST endpoint will call this" |
| 1.5-5 | /docs/UPDATE_WORKFLOW.md | Documentation | Team documents incremental update process |

---

## 6. Risks, Assumptions, Questions

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|---|---|---|
| **IPFS reliability** | Medium | High | Use pinning service (Pinata, Infura) as backup; test failover |
| **Large dataset scale** | Low (MVP is 50 spaces) | Medium | Design for <1MB dataset; optimize later if needed |
| **CSV mapping complexity** | Medium | Low | Provide UI (Phase 2+) to generate mapping; template library |
| **Duplicate detection false positives** | Medium | Low | Manual review by SM before merge; don't auto-merge |
| **Data privacy (email addresses)** | Low | High | Document PII handling; anonymize logs; GDPR compliance |

### Assumptions

1. Pilot networks provide data in CSV/JSON format (not proprietary APIs)
2. Pilot networks have <5000 spaces each (MVP assumption)
3. IPFS suitable for MVP (may revisit for larger federation)
4. Manual column mapping acceptable (UI automation in Phase 2)
5. No real-time sync needed (incremental batch updates sufficient for MVP)

### Open Questions

1. **Skill categorization**: Should spaces self-report skills, or ingest from network metadata?
   - **Decision needed by**: Story 1.2 implementation
   - **Impact**: Affects data validation rules

2. **Duplicate resolution**: How to handle "space moved to new address" vs "duplicate entry"?
   - **Decision needed by**: Story 1.4 implementation
   - **Options**:
     a) Track relocations separately (use relocated_from field)
     b) Create new space record + link to old via relationship
   - **Recommendation**: Option (a) simpler for MVP; relationship graph query (b) for Phase 2+

3. **IPFS pinning**: Self-hosted node vs pinning service?
   - **Decision needed by**: Story 1.3 implementation
   - **Cost trade-off**: Self-hosted = free but operational overhead; pinning service = $20-50/month
   - **Recommendation for MVP**: Pinning service (Pinata free tier)

4. **Network metadata**: How to populate network data if not provided?
   - **Decision needed by**: Story 1.1 implementation
   - **Options**:
     a) Manual entry by admin
     b) Scrape from network websites
     c) Ingest from parallel backend (betterCallSaul)
   - **Recommendation**: Option (a) for MVP; (c) for Phase 2 if betterCallSaul ready

---

## 7. Test Strategy

### Unit Tests
- **DataNormalizer**: Malformed CSV, missing fields, type validation
- **DuplicateDetector**: Similar names, different addresses, exact matches
- **IntegrityVerifier**: IPFS hash mismatch, schema validation errors

### Integration Tests
1. **End-to-end ingest**: CSV → Pydantic validation → IPFS → Retrieve + verify
2. **Mapping accuracy**: Map non-standard column names; verify output
3. **Duplicate workflow**: Ingest duplicate; verify conflict flagged; test resolution
4. **Rollback**: Ingest bad data; revert to previous IPFS snapshot; verify recovery

### Manual/QA Tests
- **Pilot network import**: 2-3 real networks provide actual CSV exports; test end-to-end
- **Data accuracy spot-check**: Verify 10 random spaces ingested correctly
- **Mapping audit**: Network reviews mapping CSV; confirms accuracy

### Coverage Goal
- Unit tests: ≥80% code coverage
- Integration tests: All major workflows tested
- E2E: At least 1 pilot network successfully imported

---

## 8. Success Metrics & Definition of Done

### Epic-Level Success

**Epic 1 is DONE when:**

1. ✅ Pydantic schema designed, documented, version-controlled
2. ✅ CSV/JSON ingestion pipeline working with ≥1 pilot network
3. ✅ IPFS integration tested and documented
4. ✅ Audit trail and mapping tables functional
5. ✅ Incremental update architecture designed (not necessarily implemented)
6. ✅ ≥50 spaces successfully ingested from ≥2 pilot networks
7. ✅ Zero duplicates in final IPFS snapshot (manually resolved)
8. ✅ All ACsVerified via tests or manual review
9. ✅ Technical documentation complete (IPFS setup, column mapping guide, update process)
10. ✅ Code reviewed, tested, merged to main

### Metrics

- **Ingestion success rate**: ≥95% (failed rows logged, not blocking)
- **Data validation errors**: <2% (missing optional fields OK; missing required fields = error)
- **Duplicate rate**: 0% in final snapshot (all conflicts manually resolved)
- **IPFS integrity**: 100% of snapshots verified on retrieval

---

## 9. Handoff to Phase 2

### Deliverables

- ✅ IPFS snapshot with final, verified dataset (content hash recorded)
- ✅ Technical documentation (setup guides, data model, workflows)
- ✅ Python ingestion code (reusable for future networks)
- ✅ Audit trail CSV (for network review)
- ✅ Pydantic schema (ready for Neo4j ingestion in Phase 2)

### Phase 2 Expectations

Phase 2 will:
1. **Ingest IPFS snapshot into Neo4j graph** (create space nodes, relationships)
2. **Build REST API** on top of Neo4j (query spaces, filter, paginate)
3. **Create map frontend** (Leaflet + APIs from Epic 1 data)
4. **Implement Space Detail View** (show freshness, metadata)

**Phase 2 does NOT need to re-do data ingestion**—the work of Epic 1 is complete and verified.

---

**Epic 1 Technical Specification Complete**
*Prepared for development phase (Stories 1.1 - 1.5)*
