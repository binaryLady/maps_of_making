# Architecture Document: Maps of Making

**Project:** Maps of Making - Federated Makerspace Data Commons
**Version:** 1.0 (NLNet MVP Phase)
**Date:** 2025-11-05
**Level:** 3 Greenfield Software (Digital Commons Infrastructure)

---

## Executive Summary

Maps of Making eliminates coordination costs for makerspace networks by creating **one single verification point that powers global discoverability**. Communities verify data once → visible everywhere across the entire ecosystem.

**The Problem We Solve:**
Spaces waste effort updating 5+ separate maps (Fablab.io, Hackerspaces.org, Google Maps, regional databases). Maps go stale. Networks lose critical coordination infrastructure.

**Why Graph Architecture Matters:**
Beyond solving the duplication problem, we use Neo4j graph database to reveal **relationships, collaborations, skill flows, and partnerships** that SQL-based maps cannot express. This transforms static location data into living ecosystem intelligence.

**Key Architectural Principles:**
- **Single source of truth:** One verification cascades everywhere (elimination of duplicate effort)
- **Graph intelligence:** Neo4j reveals network relationships and enables natural language queries
- **Effortless livelyness signals:** Magic links, webhooks, local device pings (<2 minutes per verification)
- **Decentralized commons:** IPFS storage + validator node model ensures data stays in commons, not proprietary platform
- **Agent-accessible:** Natural language API ("Ask the map") proves data is machine-readable and reveals intelligence

**Technology Stack:**
- Backend: Python + FastAPI + Neo4j (graph database)
- Frontend: Vanilla JavaScript + Leaflet.js (OpenStreetMap)
- Storage: Neo4j + IPFS snapshots (decentralized replication)
- Identity: Stateless JWT magic-links (no accounts for MVP)
- API: REST + OpenAPI (LLM agent-compatible)

---

## 1. System Architecture Overview

### Architecture Pattern: Hybrid Hub + Federated Replication

```
┌─────────────────────────────────────────────────────────────┐
│                    Maps of Making Platform                  │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐      ┌──────────────┐    ┌─────────────┐  │
│  │   Frontend   │◄────►│  API Layer   │◄──►│   Neo4j     │  │
│  │ (Leaflet +   │      │  (FastAPI)   │    │  Graph DB   │  │
│  │  NL Console) │      │              │    │             │  │
│  └──────────────┘      └──────────────┘    └─────┬───────┘  │
│                               │                  │          │
│                               ▼                  │          │
│                        ┌──────────────┐          │          │
│                        │ LLM Gateway  │          │          │
│                        │ (Mistral AI) │          │          │
│                        │              │          │          │
│                        └──────────────┘          │          │
│                                                  │          │
└──────────────────────────────────────────────────┼──────────┘
                                                   │
                                                   ▼
                                            ┌─────────────────┐
                                            │  IPFS Network   │
                                            │  (Snapshots)    │
                                            └─────────────────┘
                                                     │
                         ┌───────────────────────────┼────────────────┐
                         ▼                           ▼                ▼
                  ┌─────────────┐           ┌─────────────┐   ┌─────────────┐
                  │  Network A  │           │  Network B  │   │  Network C  │
                  │  Replica    │           │  Replica    │   │  Replica    │
                  │  (Validator)│           │  (Validator)│   │  (Validator)│
                  └─────────────┘           └─────────────┘   └─────────────┘
```

**Key Design Decisions:**

1. **Central Hub (MVP)** serves queries, but **data lives on IPFS** (decentralized)
2. **Networks can run replicas** (validation node model) → hot-swap if hub fails
3. **Graph DB enables network intelligence** (collaborations, skills, partnerships)
4. **Real-time freshness** builds trust ("this data is current")

---

## 2. Data Architecture: Graph Schema

### Core Node Types

**Space** (Makerspace/Fablab/Hackerspace)
```python
{
  "id": "fablab-barcelona",
  "name": "Fab Lab Barcelona",
  "address": "Carrer del Bailèn, 11",
  "lat": 41.3851,
  "lon": 2.1734,
  "hours": "Mon-Fri 9:00-18:00",
  "description": "Digital fabrication laboratory...",
  "contact_email": "info@fablabbcn.org",
  "last_verified": "2025-11-03T10:30:00Z",
  "last_activity": "2025-11-05T08:15:00Z"
}
```

**Network** (Regional/Global Organizations)
```python
{
  "id": "fablab-network",
  "name": "Fab Lab Network",
  "region": "global",
  "website": "https://fablabs.io",
  "contact_email": "hello@fablabs.io",
  "logo_url": "https://fablabs.io/logo.png",
  "description": "Global network of digital fabrication labs...",
  "type": "fablab_network",
  "created_at": "2014-01-01T00:00:00Z"
}
```

**Note**: Network metadata enables Phase 2+ features (network profiles, branded widgets) while avoiding tech debt. Initial population via CSV import or parallel backend API (Phase 1).

**Skill** (Competencies/Equipment)
```python
{
  "id": "laser-cutting",
  "name": "Laser Cutting",
  "category": "fabrication"
}
```

**Organization** (Partners: Schools, NGOs, Companies)
```python
{
  "id": "elisava-design-school",
  "name": "Elisava Design School",
  "type": "school",
  "contact": "info@elisava.net"
}
```

**ActivitySignal** (Sensor/Validation Events)
```python
{
  "id": "signal-12345",
  "timestamp": "2025-11-05T14:00:00Z",
  "signal_type": "manual_ping"
}
```

---

### Core Relationships

```cypher
// Network membership
(Space)-[:MEMBER_OF]->(Network)

// Skills and capabilities
(Space)-[:HAS_SKILL]->(Skill)

// Collaborations (the network intelligence layer)
(Space)-[:COLLABORATES_WITH {since: date, project: "name"}]->(Space)

// Partnerships (ecosystem connections)
(Space)-[:PARTNERS_WITH {since: date, description: "..."}]->(Organization)

// Trust signals
(Space)-[:VERIFIED_BY {timestamp: datetime, verifier: "email"}]->(Network)

// Activity tracking
(Space)-[:HAS_ACTIVITY {timestamp: datetime}]->(ActivitySignal)
```

**Why Graph > SQL:**
- SQL: "Where is Space X?"
- Graph: "Who collaborates with Space X? Through which skills? What's the local ecosystem?"

**This is the differentiator.**

---

### Pydantic Validation Layer

All data validated before Neo4j ingestion:

```python
from pydantic import BaseModel, Field
from datetime import datetime

class SpaceNode(BaseModel):
    id: str
    name: str
    address: str
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)
    hours: str | None = None
    contact_email: str
    last_verified: datetime
    last_activity: datetime | None = None

class CollaborationRelation(BaseModel):
    source_space_id: str
    target_space_id: str
    since: datetime
    project: str | None = None
    description: str | None = None
```

Ensures schema consistency across federation.

---

## 3. Technology Stack & Versions

| Component | Technology | Version | License | Rationale |
|-----------|-----------|---------|---------|-----------|
| **Backend Framework** | FastAPI | 0.104+ | MIT | Modern Python async framework, auto-generates OpenAPI spec for agent compatibility |
| **Graph Database** | Neo4j Community | 5.x | GPL3 | Graph-first architecture enables network intelligence queries |
| **Python Driver** | neo4j | 5.14+ | Apache 2.0 | Official Neo4j Python client |
| **Decentralized Storage** | IPFS | latest | MIT/Apache | Ensures data commons resilience, no single point of control |
| **Authentication** | PyJWT | 2.8+ | MIT | Stateless JWT for magic-link verification |
| **Frontend Map** | Leaflet.js | 1.9+ | BSD-2 | Battle-tested OSM rendering, lightweight, no tracking |
| **Frontend Base** | Vanilla JS | ES6+ | - | Zero dependencies, fast, easy embedding |
| **LLM Gateway** | Mistral AI SDK | 1.0+ | Apache 2.0 | Powers natural language console (EU-based, GDPR-native, supports embeddings + chat completions) |
| **Data Validation** | Pydantic | 2.5+ | MIT | Schema validation before Neo4j ingestion |
| **Knowledge Graph Construction** | Graphiti | latest | Apache 2.0 | Rich context extraction from unstructured data during ingestion phase (Phase 1) |
| **Deployment** | Docker + Docker Compose | latest | Apache 2.0 | Reproducible environment, easy network replica deployment |

**License Strategy:**
- Core platform: Apache 2.0 (enables derivative funding from NGI/Erasmus+)
- Neo4j Community: GPL3 (open source, compatible with commons philosophy)

---

## 4. Decentralization Strategy

### IPFS Snapshot Replication

**MVP Approach (NLNet Phase):**
1. Neo4j hub maintains live graph
2. Hourly/daily exports to IPFS (GraphML format)
3. IPFS content hash published (cryptographic integrity)
4. Networks can download snapshot → run local Neo4j replica

**Export Script:**
```python
from neo4j import GraphDatabase
import ipfshttpclient
import json

def export_to_ipfs():
    # Export Neo4j graph
    driver = GraphDatabase.driver("bolt://localhost:7687")
    with driver.session() as session:
        result = session.run("CALL apoc.export.graphml.all(null, {})")
        graph_data = result.single()["file"]

    # Push to IPFS
    ipfs = ipfshttpclient.connect('/ip4/127.0.0.1/tcp/5001')
    res = ipfs.add(graph_data)

    print(f"Graph snapshot: ipfs://{res['Hash']}")
    return res['Hash']
```

**Validation Node Model (Phase 4):**
- Each network runs Neo4j replica (like blockchain validators)
- If hub fails, replicas serve queries
- Requirement for advanced features: must host replica

---

## 5. Identity & Authentication

### Magic-Link Verification (No Accounts)

**Flow:**
1. After data ingestion, proactively send magic-links to all spaces
2. JWT token (24-hour expiry) embedded in email
3. User clicks → validates → sees pre-filled form → edits → submits
4. Updates Neo4j + resets freshness

**JWT Payload:**
```python
{
  "space_id": "fablab-barcelona",
  "email": "info@fablabbcn.org",
  "exp": 1699900000  # 24h expiry
}
```

**Security:**
- Email-to-space validation (token email must match Space node)
- HTTPS only
- 24h expiry (limits leak window)
- Secret key rotation policy (Phase 4)

**Email Template:**
```
Subject: Verify your listing on Maps of Making

Hi Fab Lab Barcelona,

You're now listed on Maps of Making, a federated network intelligence
platform for the global maker ecosystem.

Please verify your listing is accurate:
[Verify Your Listing - 24h link]

This helps maintain trust in the commons.
```

**Phase 4 Evolution:**
- SOLID protocol (decentralized identity)
- Blockchain wallet auth
- Keep magic-links as fallback

---

## 6. API Design & Agent Compatibility

### REST API Endpoints

**Core Endpoints:**
```
GET  /api/spaces                 # List all spaces (paginated)
GET  /api/spaces/{id}            # Single space details + freshness
GET  /api/spaces/search          # Spatial search (lat, lon, radius, skills)
GET  /api/spaces/{id}/skills     # Skills at space
GET  /api/spaces/{id}/partners   # Partnership network
GET  /api/networks               # List networks
GET  /api/graph/collaborations   # Collaboration graph data

POST /api/spaces/{id}/activity   # Record activity signal (webhook)
POST /api/agent/query            # Natural language query (LLM gateway)
POST /api/verify                 # Magic-link verification submission
```

**Response Format (Consistent):**
```json
{
  "data": {
    "id": "fablab-barcelona",
    "name": "Fab Lab Barcelona",
    "location": {"lat": 41.3851, "lon": 2.1734},
    "freshness": {
      "last_verified": "2025-11-03T10:30:00Z",
      "days_since": 2,
      "score": 0.994,
      "status": "fresh",
      "icon": "✅",
      "message": "Last verified 2 days ago"
    },
    "skills": ["laser_cutting", "3d_printing", "electronics"],
    "contact_email": "info@fablabbcn.org"
  },
  "meta": {
    "timestamp": "2025-11-05T14:22:00Z",
    "source": "ipfs://Qm..."
  }
}
```

---

### A2A Protocol Compatibility: Natural Language Console

**HERO FEATURE for NLNet Pitch:**

User types natural language query → LLM calls API → Results displayed on map.

**Example Queries:**
- "Show me makerspaces in Berlin"
- "Find fablabs with laser cutting in Portugal"
- "Which spaces collaborate with schools in Spain?" (graph query)

**Backend Implementation:**
```python
from mistralai import Mistral

@app.post("/api/agent/query")
async def natural_language_query(query: str):
    client = Mistral(api_key=MISTRAL_API_KEY)

    # FastAPI auto-generates OpenAPI spec → LLM tools
    tools = app.openapi()  # Your API as function tools

    response = client.chat.complete(
        model="mistral-large-latest",
        messages=[{"role": "user", "content": query}],
        tools=tools
    )

    # Execute tool calls (your API endpoints)
    results = execute_function_calls(response.choices[0].message.tool_calls)

    return {
        "query": query,
        "results": results,
        "map_highlight": [r["id"] for r in results]
    }
```

**Why This Matters:**
- Proves API is agent-compatible (not theoretical)
- Demonstrates graph intelligence (complex relationship queries)
- Makes data accessible to non-technical users
- Differentiates from SQL-based maps (can't do this)

---

## 7. Freshness & Activity Signals

### Real-Time Freshness Computation + Community Trust Signals

**Freshness States (Lifecycle):**

```python
def calculate_freshness(space: SpaceNode) -> dict:
    days_since = (datetime.now() - space.last_verified).days

    # Check if user-reported dead or permanently closed
    if space.status == "dead" or space.status == "permanently_closed":
        return {
            "score": 0,
            "status": "dead",
            "icon": "💀",
            "days_since": days_since,
            "message": "Confirmed closed or non-responsive",
            "reported_by": space.closure_report.user if space.closure_report else None
        }

    # Time-based decay
    score = max(0, 1 - (days_since / 365))  # 1-year decay window

    # Thresholds
    if days_since <= 90:
        status, icon = "fresh", "✅"
    elif days_since <= 180:
        status, icon = "aging", "⚠️"
    elif days_since <= 365:
        status, icon = "stale", "🧟"  # Zombie - might be alive, unclear
    else:
        status, icon = "dead", "💀"  # Auto-marked dead after 1 year no response

    return {
        "score": round(score, 2),
        "status": status,
        "icon": icon,
        "days_since": days_since,
        "message": f"Last verified {days_since} days ago"
    }
```

**Why Real-Time (Not Pre-Computed):**
- **Trust-building:** Activity webhook → instant freshness update
- **Simple:** No background jobs, no cron
- **Fast enough:** Microsecond calculation at MVP scale
- **Proof of livelyness:** Immediate feedback loop

---

### Activity Signal Webhook

**Endpoint:**
```python
@app.post("/api/spaces/{space_id}/activity")
async def record_activity(
    space_id: str,
    token: str,  # Space-specific auth token
    signal_type: str = "manual_ping"
):
    # Validate token
    space = validate_space_token(space_id, token)

    # Update Neo4j
    space.last_activity = datetime.now()
    neo4j.update_space(space)

    # Freshness recalculates automatically on next read
    return {"status": "recorded", "freshness": "updated"}
```

**Signal Types (MVP Phase 3):**
1. **Email verification (PRIMARY):** Magic-link verification resets freshness countdown
2. **Community reports:** Users can report space as "dead" or "permanently closed"

**Signal Types (Nice-to-have Phase 3 PoC):**
3. **Mock webhook:** Optional webhook_url registration + `POST /spaces/{space_id}/ping` endpoint for testing
   - Allows testing infrastructure without real sensors
   - Spaces can manually trigger freshness updates via webhook for demo purposes
   - Preparation for Phase 4 real integrations

**Signal Types (Phase 4+):**
4. **Real webhooks:** Space systems (door, booking, calendar) send POST to registered endpoint
5. **IoT sensors:** Light, motion, presence detectors via MQTT bridge
6. **Login logs:** Integration with space management systems

**Community Trust Endpoint:**
```python
@app.post("/api/spaces/{space_id}/report-closure")
async def report_closure(
    space_id: str,
    reporter_email: str,
    reason: str,  # "closed_permanently", "no_response", "moved"
    evidence: str | None = None  # Optional: URL, photo, etc.
):
    # Store closure report (doesn't auto-close, needs verification)
    report = ClosureReport(
        space_id=space_id,
        reporter_email=reporter_email,
        reason=reason,
        evidence=evidence,
        timestamp=datetime.now(),
        status="pending_verification"
    )

    # Create Neo4j relationship
    neo4j.create_relationship(
        (space_id, "HAS_CLOSURE_REPORT", report.id)
    )

    # If multiple reports (3+), auto-mark as "dead"
    if space.closure_reports.count() >= 3:
        space.status = "dead"

    return {"status": "recorded", "verification_pending": True}
```

**This proves community livelyness + community accountability** → core trust mechanism.

---

## 8. Data Governance: Versioning & Immutable Ledger

### Volatile vs. Permanent Data Classification

**Philosophy:** Like blockchain ledgers, critical events are never deleted—only appended. But operational data (opening hours, equipment) can be updated without full history.

**Data Classification:**

#### **Volatile Data** (Current State + Short History)
**Definition:** Operational information that changes frequently and doesn't need full audit trail.

**Examples:**
- Opening hours
- Equipment list
- Contact email/phone
- Description text
- Website URL

**Versioning Strategy:**
- Store current state in Neo4j node properties
- Keep last 3-5 versions (recent history for rollback)
- Older versions archived to IPFS snapshots

```python
# Volatile data structure
{
  "current": {
    "hours": "Mon-Fri 9:00-18:00",
    "updated_at": "2025-11-05T10:00:00Z"
  },
  "history": [
    {"hours": "Mon-Fri 10:00-17:00", "updated_at": "2025-09-01T..."},
    {"hours": "Mon-Thu 9:00-18:00", "updated_at": "2025-07-15T..."}
  ]
}
```

---

#### **Permanent Records** (Immutable Ledger)
**Definition:** Trust-critical events that form the audit trail. Never deleted, always versioned.

**Examples:**
- Verification events (when, by whom)
- Ownership transfers (space changes hands)
- Network membership changes (joined/left network)
- Partnership formations/dissolutions
- Closure reports (community trust signals)
- Activity signals (sensor pings, manual verifications)
- Status changes (active → zombie → dead)

**Versioning Strategy:**
- All events stored as Neo4j relationships with timestamps
- Immutable: create new relationship, never delete old
- Full history queryable

```cypher
// Example: Multiple verification events (ledger)
(Space)-[:VERIFIED_BY {timestamp: "2025-11-05", verifier: "alice@network.org"}]->(Network)
(Space)-[:VERIFIED_BY {timestamp: "2025-09-15", verifier: "bob@network.org"}]->(Network)
(Space)-[:VERIFIED_BY {timestamp: "2025-07-01", verifier: "carol@network.org"}]->(Network)

// Query full verification history
MATCH (s:Space {id: "fablab-bcn"})-[v:VERIFIED_BY]->(n:Network)
RETURN v.timestamp, v.verifier
ORDER BY v.timestamp DESC
```

---

### Ledger-Backed Trust Model

**Why This Matters for NLNet:**

1. **Transparency:** Full audit trail proves data integrity
2. **Accountability:** Who verified what, when?
3. **Dispute Resolution:** Can trace data provenance
4. **Community Governance:** Closure reports tracked, not hidden

**Example Query: "Show me closure reports for this space"**
```cypher
MATCH (s:Space {id: "some-space"})-[:HAS_CLOSURE_REPORT]->(r:ClosureReport)
RETURN r.reporter_email, r.reason, r.timestamp, r.evidence
ORDER BY r.timestamp DESC
```

**Example Query: "Who verified this space over time?"**
```cypher
MATCH (s:Space {id: "fablab-bcn"})-[v:VERIFIED_BY]->(n:Network)
RETURN v.verifier, v.timestamp, n.name
ORDER BY v.timestamp DESC
LIMIT 10
```

---

### Freshness Lifecycle with Community Trust

**State Machine:**

```
Active (✅ Fresh)
    ↓ (90 days no verification)
Aging (⚠️)
    ↓ (180 days no verification)
Zombie (🧟 Stale - unclear if alive)
    ↓ (365 days OR 3+ community reports)
Dead (💀 Confirmed closed)
```

**Reversibility:**
- Zombie → Fresh (if space verifies again)
- Dead → Active (if space reports "we reopened", requires admin verification)

**All state transitions logged as immutable events:**
```cypher
(Space)-[:STATE_CHANGE {
  from: "active",
  to: "zombie",
  reason: "365_days_no_verification",
  timestamp: "2025-11-05T14:00:00Z"
}]->(StateLog)
```

---

### Data Deletion Policy (GDPR-Compliant)

**Personal Data (can be deleted on request):**
- Contact emails (replaced with placeholder)
- Names of verifiers (anonymized)

**Structural Data (never deleted):**
- Space existence (marked "dead" instead of deleted)
- Verification events (anonymized if GDPR request)
- Partnerships (archived, not deleted)

**On GDPR "Right to be Forgotten" Request:**
1. Replace email with `anonymized-{hash}@deleted.local`
2. Remove name, keep verification timestamp
3. Space record remains (for historical network integrity)
4. Mark with `data_anonymized: true` flag

---

## 9. Frontend Architecture

### Map Display (Leaflet.js)

**Stack:** Pure HTML/CSS/JavaScript + Leaflet.js

**Why No Framework:**
- Simplest deployment (no build tools)
- Tiny bundle size
- Easy embedding (`<script>` tag)
- Fast development velocity (NLNet MVP priority)

**Embeddable Widget:**
```html
<!-- Network websites add this -->
<div id="maps-of-making" data-network="fablab-network"></div>
<script src="https://maps-of-making.org/embed.js"></script>
```

**Map Features:**
- OpenStreetMap tiles (free, open)
- Space markers color-coded by freshness (green/yellow/red)
- Click space → detail popup (skills, partners, freshness)
- Natural language console (query bar)

**Natural Language Console UI:**
```html
<div class="nl-console">
  <textarea placeholder="Ask about makerspaces... e.g., 'Find spaces in Germany with 3D printing'"></textarea>
  <button onclick="queryMap()">Ask</button>
</div>
<div id="map"></div>
```

User query → backend LLM gateway → results highlighted on map.

---

## 9. Project Structure

```
maps-of-making/
├── backend/
│   ├── main.py                 # FastAPI app entry
│   ├── api/
│   │   ├── spaces.py           # Space endpoints
│   │   ├── networks.py         # Network endpoints
│   │   ├── agent.py            # Natural language query
│   │   └── activity.py         # Activity webhook
│   ├── db/
│   │   ├── neo4j.py            # Neo4j connection
│   │   └── models.py           # Pydantic models
│   ├── auth/
│   │   └── magic_links.py      # JWT generation/validation
│   ├── ipfs/
│   │   └── export.py           # IPFS snapshot export
│   └── utils/
│       └── freshness.py        # Freshness calculation
├── frontend/
│   ├── index.html              # Main map page
│   ├── embed.html              # Embeddable widget
│   ├── js/
│   │   ├── map.js              # Leaflet initialization
│   │   └── console.js          # NL console logic
│   └── css/
│       └── styles.css
├── docker/
│   ├── docker-compose.yml      # Neo4j + Backend + IPFS
│   └── Dockerfile
├── docs/
│   ├── PRD.md
│   ├── epics.md
│   ├── architecture.md         # This document
│   └── bmm-workflow-status.md
└── README.md
```

---

## 10. Epic to Architecture Mapping

### Epic 1: Data Federation & Consolidation

**Architecture Components:**
- Pydantic validation models (`db/models.py`)
- Neo4j ingestion pipeline (`db/neo4j.py`)
- IPFS export script (`ipfs/export.py`)

**Stories:**
1. Pydantic schema design → `db/models.py`
2. CSV/JSON ingestion → `db/neo4j.py`
3. IPFS storage → `ipfs/export.py`
4. Source mapping & audit → Neo4j relationship tracking
5. Incremental updates → API for network data pushes

---

### Epic 2: Map Display & Public API

**Architecture Components:**
- FastAPI endpoints (`api/spaces.py`, `api/networks.py`)
- Leaflet frontend (`frontend/map.js`)
- Natural language console (`api/agent.py`, `frontend/console.js`)

**Stories:**
1. Leaflet map → `frontend/map.js` + `index.html`
2. Space detail view → Popup component
3. Embeddable widget → `embed.html`
4. REST API → `api/spaces.py`
5. Natural language console → `api/agent.py` + Mistral AI integration

---

### Epic 3: Verification & Community Maintenance

**Architecture Components:**
- Magic-link JWT auth (`auth/magic_links.py`)
- Verification form (`frontend/verify.html`)
- Activity webhook (`api/activity.py`)
- Freshness calculation (`utils/freshness.py`)

**Stories:**
1. Magic-link generation → `auth/magic_links.py`
2. Verification form → `frontend/verify.html`
3. Freshness tracking → Real-time calculation in API responses
4. Activity signals → `api/activity.py`
5. Verification campaigns → Email batch script

---

## 11. Deployment Architecture

### Docker Composition (MVP)

```yaml
# docker-compose.yml
version: '3.8'

services:
  neo4j:
    image: neo4j:5-community
    ports:
      - "7474:7474"  # Browser
      - "7687:7687"  # Bolt
    environment:
      NEO4J_AUTH: neo4j/password
    volumes:
      - neo4j_data:/data

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    environment:
      NEO4J_URI: bolt://neo4j:7687
      OPENAI_API_KEY: ${OPENAI_API_KEY}
      JWT_SECRET: ${JWT_SECRET}
    depends_on:
      - neo4j

  ipfs:
    image: ipfs/go-ipfs:latest
    ports:
      - "5001:5001"  # API
      - "8080:8080"  # Gateway
    volumes:
      - ipfs_data:/data/ipfs

  frontend:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./frontend:/usr/share/nginx/html

volumes:
  neo4j_data:
  ipfs_data:
```

**Deployment Options:**
- **MVP:** Single VPS (Hetzner, DigitalOcean)
- **Phase 4:** Each network runs replica (Docker Compose on their infrastructure)

---

## 12. Security Architecture

### Threat Model & Mitigations

| Threat | Mitigation |
|--------|-----------|
| Magic-link interception | HTTPS enforced, 24h expiry, email-to-space validation |
| Data tampering | IPFS content addressing (cryptographic integrity) |
| API abuse | Rate limiting (Phase 1), token auth for activity signals |
| Unauthorized edits | JWT validation, email must match Space node |
| DDoS | Cloudflare proxy (Phase 2) |
| Secret key leak | Rotation policy (Phase 4), monitoring |

**Privacy:**
- No tracking, no analytics on MVP
- Minimal personal data (contact emails only, encrypted at rest)
- GDPR-compliant: data export, deletion on request

---

## 13. Performance Considerations

### MVP Scale (NLNet Phase)

**Expected Load:**
- 3-5 pilot networks
- 100-500 spaces total
- ~1,000 API requests/day
- Hourly IPFS snapshots

**Performance Profile:**
- Neo4j query time: <10ms for spatial queries
- Freshness calculation: <1ms (real-time)
- API response time: <100ms (95th percentile)
- Map load time: <2s (Leaflet + GeoJSON)

**Bottleneck Mitigation (Phase 4):**
- CDN for static assets
- Redis caching for frequent queries
- Read replicas (federated Neo4j instances)

---

## 14. Integration Points

### External Systems Integration

**Data Ingestion (Phase 1):**
- CSV/JSON file upload (manual)
- API connectors for fablabs.io, hackerspaces.org (Phase 2)

**Activity Signal Sources (Phase 3-4):**
- Webhook from space management systems
- SpaceAPI status feeds
- IoT sensors (MQTT bridge)

**LLM Agent Integration (Phase 1):**
- Mistral AI function calling (natural language console)
- OpenAPI spec → auto-discovery by agents

**Embedding (Phase 2):**
- Network websites embed map widget
- iframe or `<script>` tag

---

## 15. Novel Architectural Patterns

### Pattern 1: Pheromone Decay Trust Model

**Problem:** How do we prove data is current without manual checking?

**Solution:** Time-based trust decay + activity signals

**Implementation:**
- Freshness score decays linearly over 365 days
- Activity signals (webhooks, pings) reset freshness
- Visual indicators (✅⚠️❌) shown to users
- Real-time calculation ensures immediate feedback

**Why Novel:**
- Traditional maps have binary "updated/not updated"
- We show **continuous trust gradient**
- Activity signals **prove livelyness** (not just claims)

---

### Pattern 2: Federated Graph Intelligence

**Problem:** How do we reveal network relationships without centralization?

**Solution:** Graph database + IPFS snapshots + validator nodes

**Implementation:**
- Neo4j stores relationships (collaborations, partnerships, skills)
- IPFS ensures data lives in commons (not proprietary server)
- Networks can run replicas (decentralized queries)

**Why Novel:**
- Existing maps: centralized SQL, location-only
- We: decentralized graph, relationship intelligence
- Enables queries like: "Who collaborates with whom?"

---

## 16. Architecture Decision Records (ADRs)

### ADR-001: Neo4j Graph-Only Database

**Status:** Accepted

**Context:** Need to reveal network relationships (collaborations, skills, partnerships) while handling spatial queries.

**Decision:** Use Neo4j Community Edition as single database, store lat/lon as node properties.

**Consequences:**
- ✅ Elegant graph traversal queries
- ✅ Network intelligence is differentiator
- ✅ Single database (simpler than SQL+Graph)
- ⚠️ Spatial queries not PostGIS-optimized, but fast enough at MVP scale

**Alternatives Considered:**
- Postgres + Neo4j (rejected: too complex for MVP)
- SQLite-only (rejected: graph queries painful)

---

### ADR-002: IPFS Snapshot Export (Not Primary Storage)

**Status:** Accepted

**Context:** Need decentralization story for NLNet, but IPFS-native graph DB is research-level complexity.

**Decision:** Neo4j primary, hourly exports to IPFS (GraphML format).

**Consequences:**
- ✅ Simple MVP implementation
- ✅ Decentralization narrative (data on IPFS)
- ✅ Networks can download snapshots
- ⚠️ Not real-time federation (hourly lag acceptable for MVP)

**Phase 4 Evolution:** Federated Neo4j instances with real-time sync.

---

### ADR-003: Stateless JWT Magic-Links

**Status:** Accepted

**Context:** No user accounts for MVP, need secure verification.

**Decision:** JWT tokens (24h expiry), email-to-space validation.

**Consequences:**
- ✅ Stateless (no token storage database)
- ✅ Standard practice (every framework has JWT)
- ⚠️ Can't revoke before expiry (acceptable: 24h window small)

**Security:** HTTPS + email validation + short expiry.

---

### ADR-004: Pure HTML/JS Frontend (No Framework)

**Status:** Accepted

**Context:** Need embeddable widget, fast MVP development.

**Decision:** Vanilla JavaScript + Leaflet.js, no React/Vue/Svelte.

**Consequences:**
- ✅ Zero build complexity
- ✅ Tiny bundle size
- ✅ Easy embedding
- ⚠️ Manual DOM manipulation (acceptable for simple UI)

**Phase 4:** Can migrate to Svelte if UI complexity grows.

---

### ADR-005: Natural Language Console (LLM Gateway)

**Status:** Accepted

**Context:** A2A protocol compatibility abstract; need demonstrable feature.

**Decision:** Build natural language query console powered by Mistral AI API.

**Consequences:**
- ✅ Proves API is agent-compatible (not theoretical)
- ✅ Demonstrates graph intelligence
- ✅ Accessible to non-technical users
- ✅ EU-based infrastructure (GDPR-native, aligns with NLNet values)
- ⚠️ Mistral AI API cost (acceptable for MVP; Phase 4: self-hosted LLM options)

**Why Hero Feature:** Differentiates from SQL maps, shows NLNet reviewers the value.

---

### ADR-006: Real-Time Freshness Computation

**Status:** Accepted

**Context:** Activity signals should update freshness immediately (trust-building).

**Decision:** Compute freshness on-read (not pre-computed daily).

**Consequences:**
- ✅ Real-time feedback (webhook → instant freshness update)
- ✅ Simple (no background jobs)
- ✅ Fast enough (<1ms calculation)
- ⚠️ Computed every API call (negligible overhead at MVP scale)

**Rationale:** "Fresh data" is the selling point; real-time proves livelyness.

---

## 17. Open Questions & Future Research

**For Phase 4 (NGI/Erasmus+ Funding):**

1. **Federated Consensus:** How do multiple Neo4j replicas resolve conflicts?
2. **Graph Visualization:** Best library for interactive network graph UI? (D3.js, Cytoscape, Graphistry)
3. **Self-Hosted LLM:** Can we run Mistral/Llama locally to replace Mistral AI API? (cost + privacy)
4. **Blockchain Identity:** SOLID vs. DID vs. wallet auth—which fits best?
5. **Governance:** How do networks vote on data quality disputes?

---

## 18. Success Metrics (Architecture Validation)

### Technical Metrics (MVP)

| Metric | Target | Validation Method |
|--------|--------|-------------------|
| API response time (p95) | <100ms | Load testing (Locust) |
| Neo4j query time | <10ms | EXPLAIN profiling |
| Map load time | <2s | Lighthouse audit |
| IPFS snapshot size | <50MB | Export script monitoring |
| Natural language console accuracy | >80% correct results | Manual testing (10 sample queries) |
| Freshness calculation time | <1ms | Python profiler |

### Functional Validation

- ✅ Natural language query: "Find spaces in Portugal" → returns correct results
- ✅ Activity webhook → freshness updates within 1 second
- ✅ Magic-link verification → updates Neo4j, visible on map
- ✅ Embeddable widget → renders on external site
- ✅ IPFS snapshot → downloadable, can restore to Neo4j

---

## 19. Consortium Pitch: Key Talking Points

**For today's pitch deck:**

1. **"One update, everywhere"** (PRIMARY VALUE)
   - Spaces update once → visible globally across ecosystem (Fablab.io, our map, regional networks, APIs)
   - Eliminates duplicate effort across 5+ separate map platforms
   - Single source of truth = communities want to maintain because they see immediate impact

2. **"Effortless verification signals"** (ADOPTION DRIVER)
   - Magic links, webhooks, local device pings—all under 2 minutes
   - Real-time feedback: Activity update → instant freshness change on map
   - Maintenance becomes self-reinforcing (communities rely on current data)

3. **"We reveal the invisible network"** (SECONDARY DIFFERENTIATOR)
   - Other maps show locations
   - We show collaborations, skills, partnerships, ecosystem relationships
   - Graph intelligence enables "Find spaces collaborating with schools in Spain" queries (impossible in SQL)

4. **"Decentralized commons designed to outlive funding"** (NGI ALIGNMENT)
   - Grounded in Elinor Ostrom's proven commons principles
   - Data lives on IPFS (not proprietary platform)
   - Networks can run validator nodes (decentralized governance layer)
   - Apache 2.0 license (enables derivative funding from other NGI calls)

5. **"Human + AI accessible"** (HERO FEATURE)
   - Natural language API: "Find active spaces in Portugal" (live demo)
   - Proves data is machine-readable and reveals intelligence
   - Demonstrates A2A protocol compatibility

6. **"Funding strategy aligned with ecosystem growth"**
   - NLNet: MVP (data federation + map + verification) = proof of concept
   - Phase 4: Erasmus+ KA220 (governance layer), Fediversity (decentralized scaling)
   - Replication revenue: Communities license implementation support

---

## 20. Implementation Roadmap

### Phase 1: Data Federation (Epic 1) - 3 days
- Pydantic schema
- Neo4j ingestion pipeline
- IPFS export script

### Phase 2: Map & API (Epic 2) - 3.25 days
- Leaflet map display
- REST API endpoints
- Natural language console
- Embeddable widget

### Phase 3: Verification (Epic 3) - 3.25 days
- Magic-link system
- Verification form
- Activity webhook
- Freshness tracking

**Total MVP: 9.5 dev days**

---

## Appendix A: Technology Justification for NLNet

**Why These Choices Maximize NLNet Impact:**

| Choice | NLNet Criterion | Justification |
|--------|----------------|---------------|
| Neo4j Community (GPL3) | Open Source Mandate | Fully open source, no proprietary lock-in |
| IPFS | Decentralization | Data lives in commons, resilient to single-point failure |
| Graph DB | Strategic Impact | Reveals network intelligence (not just directory) |
| Apache 2.0 License | Sustainability | Enables derivative funding (NGI, Erasmus+) |
| Natural Language Console | Innovation | Proves agent-ready infrastructure, accessible to all |
| Real-Time Freshness | Trust/Transparency | Builds community accountability, not extractive |

---

## Appendix B: Comparison to Existing Maps

| Feature | fablabs.io | mapall.space | **Maps of Making** |
|---------|------------|--------------|---------------------|
| Database | SQL (Postgres) | SQL (MySQL) | **Graph (Neo4j)** |
| Reveals relationships | ❌ | ❌ | **✅ (collaborations, skills)** |
| Freshness tracking | ❌ | ❌ | **✅ (pheromone decay)** |
| Activity signals | ❌ | ❌ | **✅ (webhooks, sensors)** |
| Decentralized storage | ❌ | ❌ | **✅ (IPFS)** |
| Agent-accessible | ❌ | ❌ | **✅ (natural language console)** |
| Federation | ❌ (centralized) | ❌ (centralized) | **✅ (validator nodes)** |

**Conclusion:** We're not building another map. We're building **network intelligence infrastructure.**

---

_Document prepared for NLNet Commons Fund application and consortium pitch at Vulca Seminar 2025-11-05_

**Next Steps:**
1. ✅ Architecture complete
2. ⏭️ Create pitch deck (one-pager + diagram)
3. ⏭️ Technical spec for NLNet application
4. ⏭️ Sprint planning (story breakdown → tasks)
