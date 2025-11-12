# Phase 1 Sprint Plan: 4 Milestones, 8 Weeks

**Document:** Week-by-week user stories, tasks, and acceptance criteria for MVP execution
**Date:** 2025-11-12
**Milestones:** M1-M4 (8 weeks total)
**Budget:** €18,555 (NLNet NGI Zero Commons)
**Team:** 1 senior developer (€80/hour) + part-time support (architecture, PM)

---

## Overview: Milestone Structure

```
Week 1-3:  MILESTONE 1 - Backend Engine Foundation
           ├─ Docker Compose + Neo4j setup
           ├─ FastAPI core + RBAC framework
           ├─ Data ingestion pipeline (Docling)
           ├─ Knowledge graph construction (Graphiti)
           └─ Mistral AI integration (embeddings)

Week 4-5:  MILESTONE 2 - Domain Adaptation
           ├─ Pydantic schemas (Space, Network, Verification)
           ├─ CSV/JSON ingestion (pilot network data)
           ├─ Freshness decay + lifecycle logic
           ├─ Magic-link JWT auth + Gmail API
           └─ REST API endpoints (spaces, networks, verify)

Week 6-7:  MILESTONE 3 - Map Interface & Verification
           ├─ SvelteKit frontend scaffold
           ├─ Leaflet.js map integration (OSM rendering)
           ├─ Space detail cards + verification form
           ├─ Freshness status UI (✅⚠️🧟💀)
           └─ Frontend-backend integration

Week 8:    MILESTONE 4 - Integration, Testing & Deploy
           ├─ E2E tests (all user journeys)
           ├─ IPFS backup/restore (tested)
           ├─ Production deployment (Hetzner)
           ├─ User documentation + API specs
           └─ Pilot network feedback loop
```

---

## MILESTONE 1: Backend Engine Foundation (Weeks 1-3)

### Goal
"A working FastAPI backend can ingest, transform, and query space + network data in Neo4j, with embeddings powered by Mistral AI."

### Week 1: Project Setup & Architecture Validation

#### Story 1.1: Development Environment & Deployment Pipeline

**User:** Developer
**Goal:** Have a local development environment that mirrors production

**Tasks:**
1. Create Docker Compose file with services:
   - Neo4j instance (latest)
   - FastAPI container (Python 3.11)
   - Redis (for caching, optional but recommended)
2. Initialize GitHub Actions CI pipeline:
   - Lint (black, ruff)
   - Unit tests (pytest)
   - Docker image build
3. Create `.env.example` template with all required variables:
   - Neo4j URI, credentials
   - Mistral API key
   - IPFS node (optional for MVP)
   - Email service credentials (Gmail API)

**Acceptance Criteria:**
- ✅ `docker-compose up` starts all services within 30 seconds
- ✅ FastAPI `/health` endpoint returns `{"status": "ok"}` after startup
- ✅ Neo4j is accessible at localhost:7687
- ✅ CI pipeline runs on every commit (auto-lint, test)
- ✅ README has 5-minute setup instructions

**Estimated effort:** 8 hours

---

#### Story 1.2: FastAPI Core Structure & RBAC Framework

**User:** Developer
**Goal:** Have a foundation for all API endpoints with built-in role-based access control

**Tasks:**
1. Create FastAPI app structure:
   - `main.py` (app initialization)
   - `routers/` directory (endpoints)
   - `models/` directory (Pydantic schemas)
   - `services/` directory (business logic)
   - `middleware/` directory (auth, logging)
2. Implement JWT magic-link authentication:
   - `POST /auth/magic-link` — Send JWT to email
   - JWT validation middleware
   - Stateless verification (no session DB)
3. Implement RBAC:
   - Role enum: `admin`, `network_coordinator`, `space_operator`, `researcher`, `public`
   - `@require_role` decorator
   - Sample protected endpoint: `GET /admin/dashboard`

**Acceptance Criteria:**
- ✅ `POST /auth/magic-link` with email generates signed JWT
- ✅ JWT can be decoded + verified via middleware
- ✅ Protected endpoints reject requests without valid JWT
- ✅ Admin endpoints require `admin` role
- ✅ OpenAPI docs auto-generated at `/docs`

**Estimated effort:** 12 hours

---

#### Story 1.3: Neo4j Connection + Graph Schema

**User:** Developer
**Goal:** Define the core graph schema and test CRUD operations

**Tasks:**
1. Define Neo4j node types:
   - `Space` (properties: id, name, address, lat, lon, created_at, closed_at, etc.)
   - `Network` (properties: id, name, country, founded_date, etc.)
   - `Skill` (properties: id, name, category)
2. Define relationships:
   - `Space -[:PART_OF]-> Network`
   - `Space -[:HAS_SKILL]-> Skill` (with level, professionals, advanced, intermediate, novice)
   - `Space -[:PARTNERSHIP]-> Space` (bidirectional, with type + status)
   - `Space -[:VERIFICATION_EVENT]-> Event`
3. Write Neo4j driver wrapper class:
   - Connection pooling
   - Health check endpoint
   - Query timeout handling

**Acceptance Criteria:**
- ✅ Can create/read/update spaces in Neo4j
- ✅ Relationships are created correctly (test: create Space + Network, check PART_OF edge)
- ✅ Indexes created on: Space.id, Network.id, Skill.id (performance)
- ✅ Health check endpoint responds in <100ms
- ✅ Cleanup script drops all data (for testing)

**Estimated effort:** 10 hours

---

#### Story 1.4: Docling Data Ingestion Pipeline

**User:** Developer
**Goal:** Ingest heterogeneous CSV/JSON data, transform to unified schema, load into Neo4j

**Tasks:**
1. Integrate Docling library:
   - Support CSV, JSON, Excel inputs
   - Parse arbitrary column names → standard schema mapping
   - Handle missing/null values gracefully
2. Create data transformation service:
   - Map pilot network schema → canonical Space schema
   - Example: Fablab.io CSV format → internal Space model
   - Validation: Reject non-compliant data with clear errors
3. Implement bulk loader:
   - `POST /admin/ingest` endpoint
   - Accept file upload (CSV/JSON)
   - Return: # spaces created, # relationships created, # errors

**Acceptance Criteria:**
- ✅ Can ingest Fablab.io CSV sample (>100 spaces)
- ✅ Column mapping configurable (Phase 2 UI; Phase 1 hardcoded)
- ✅ Validation rejects invalid data (missing name, invalid lat/lon)
- ✅ Bulk insert is fast (100 spaces in <5 seconds)
- ✅ Duplicate detection: Don't create space twice if imported again

**Estimated effort:** 12 hours

---

#### Story 1.5: Graphiti Knowledge Graph Construction

**User:** Developer
**Goal:** Automatically infer relationships from data (e.g., spaces in same city might partner)

**Tasks:**
1. Define inference rules:
   - If Space A and Space B in same city + both teach metalworking → suggest partnership
   - If Space closes → mark as zombie/dead lifecycle
   - If space verified in last 14 days → mark as "fresh"
2. Implement inference service:
   - `POST /admin/infer-relationships` endpoint
   - Run after data ingestion
   - Log: # suggestions created, confidence scores

**Note:** For MVP, keep inference simple. Phase 2-3 can add ML-based suggestions.

**Acceptance Criteria:**
- ✅ Partnership suggestions created correctly (test: 2 spaces same city teaching same skill)
- ✅ Lifecycle inference assigns freshness states
- ✅ Inference is idempotent (running twice doesn't duplicate suggestions)
- ✅ Results visible in Neo4j browser

**Estimated effort:** 8 hours

---

#### Story 1.6: Mistral AI Integration (Embeddings + Chat)

**User:** Developer
**Goal:** Call Mistral API for embeddings (space descriptions) and LLM queries

**Tasks:**
1. Create Mistral client wrapper:
   - Initialize with API key
   - Retry logic (3x with exponential backoff)
   - Cost tracking (log tokens used)
2. Implement embedding endpoint:
   - `POST /ai/embed` — given text, return embedding vector (1536 dimensions)
   - Store embeddings in Neo4j (optional for MVP)
3. Implement LLM query endpoint:
   - `POST /ai/query` — given natural language question, return Cypher + results
   - Example: "Find spaces with advanced metalworking" → generates Cypher, executes, returns JSON

**Acceptance Criteria:**
- ✅ Can call Mistral API without errors (test with sample prompt)
- ✅ Embeddings returned consistently (same input = same output)
- ✅ LLM query generates valid Cypher (test on sample queries from PERSONAS.md)
- ✅ Token usage tracked (logged to admin dashboard)
- ✅ Costs stay under €35/week budget projection

**Estimated effort:** 10 hours

---

#### Story 1.7: Unit Test Suite + Code Coverage

**User:** QA
**Goal:** Ensure backend is reliable; >80% code coverage

**Tasks:**
1. Write tests for all story 1.1-1.6 components:
   - Neo4j CRUD operations
   - JWT middleware
   - Docling ingestion
   - Mistral API wrapper
2. Use pytest fixtures for:
   - Fresh Neo4j instance per test
   - Mock Mistral API (don't call real endpoint)
3. CI pipeline runs tests on every commit

**Acceptance Criteria:**
- ✅ Code coverage: >80% for all modules
- ✅ All tests pass locally (`pytest`)
- ✅ CI pipeline enforces test pass before merge
- ✅ README has testing instructions

**Estimated effort:** 12 hours

---

### Week 1 Summary

| Story | Effort | Status |
|-------|--------|--------|
| 1.1 | 8h | ⬜ |
| 1.2 | 12h | ⬜ |
| 1.3 | 10h | ⬜ |
| 1.4 | 12h | ⬜ |
| 1.5 | 8h | ⬜ |
| 1.6 | 10h | ⬜ |
| 1.7 | 12h | ⬜ |
| **Week 1 Total** | **82h** | |

**Target:** ~80h available; Week 1 is full but achievable

---

### Week 2-3: Milestone 1 Completion

**Stories 1.8-1.15** (documented in similar format):

| Week | Story | Title | Effort |
|------|-------|-------|--------|
| **2** | 1.8 | API Versioning & Documentation | 6h |
| | 1.9 | GraphQL vs REST Decision | 4h |
| | 1.10 | Caching Strategy (Redis) | 8h |
| | 1.11 | Error Handling & Logging | 8h |
| | 1.12 | Performance Optimization (indexes) | 6h |
| **2 Total** | | | **32h** |
| **3** | 1.13 | Admin Dashboard Data Collection | 12h |
| | 1.14 | Pilot Network Data Load Testing | 8h |
| | 1.15 | M1 Code Review + Refactoring | 8h |
| **3 Total** | | | **28h** |

**M1 Total:** 82 + 32 + 28 = **142 hours available** (3 weeks × 46 hours/week minus holidays)
**Budget allocated to M1:** €5,200 (65 hours @80/h) ✅ Achievable

---

## MILESTONE 2: Domain Adaptation (Weeks 4-5)

### Goal
"Maps of Making domain logic is live: spaces verify, partnerships form, freshness decays, API serves real pilot network data."

### Week 4: Schema + Auth + Core API

#### Story 2.1: Pydantic Schemas (Space, Network, Verification)

**Tasks:**
1. Define Pydantic models:
   ```python
   class Space(BaseModel):
       id: str
       name: str
       address: str
       lat: float
       lon: float
       network_id: str
       created_at: datetime
       first_verified_at: datetime
       last_verified_at: datetime
       closed_at: Optional[datetime] = None
       closure_reason: Optional[str] = None
       # ... 20+ fields

   class Network(BaseModel):
       id: str
       name: str
       country: str
       founded_date: date
       # ...

   class VerificationEvent(BaseModel):
       space_id: str
       verified_at: datetime
       verified_by: str (email)
       freshness_status: str  # ✅⚠️🧟💀
   ```

2. Add validation:
   - Email must be valid
   - lat/lon must be valid coordinates
   - Dates must be reasonable (not future)

**Acceptance Criteria:**
- ✅ All models have field docstrings
- ✅ Validation catches invalid data (test with bad inputs)
- ✅ OpenAPI schema is auto-generated

**Estimated effort:** 8h

---

#### Story 2.2: Magic-Link Verification (Email + JWT)

**Tasks:**
1. Implement verification flow:
   - `POST /verify/magic-link?space_id=X&email=user@space.org`
   - Generate JWT token (valid 7 days)
   - Send email via Gmail API: "Click here to verify: https://maps.making/verify?token=JWT"
   - `POST /verify` with JWT → Record verification event
2. Store verification events:
   - Create `VerificationEvent` node in Neo4j
   - Link to Space via `:VERIFICATION_EVENT` relationship
   - Update Space.last_verified_at

**Acceptance Criteria:**
- ✅ Email sent successfully (test with real email)
- ✅ JWT generated + valid
- ✅ Verification endpoint updates Space node
- ✅ Token expires after 7 days (test: try expired token)

**Estimated effort:** 10h

---

#### Story 2.3: Freshness Decay Algorithm

**Tasks:**
1. Implement decay logic (Activity-Based, Option B):
   ```
   days_since_verification = (now - space.last_verified_at).days
   if days_since_verification <= 14:
       freshness = "✅ fresh"
   elif days_since_verification <= 30:
       freshness = "⚠️ aging"
   elif days_since_verification <= 90:
       freshness = "🧟 zombie"
   else:
       freshness = "💀 dead"
   ```
2. Calculate freshness for all spaces:
   - `GET /spaces?freshness=fresh` — returns ✅ only
   - `GET /spaces?freshness=zombie` — returns 🧟
3. Cron job (daily):
   - Recalculate freshness for all spaces
   - Alert admin if >10 spaces entering zombie state

**Acceptance Criteria:**
- ✅ Freshness states calculated correctly
- ✅ Filtering by freshness works (`?freshness=aging`)
- ✅ Cron job runs daily, logs results
- ✅ Admin dashboard shows freshness distribution

**Estimated effort:** 8h

---

#### Story 2.4: CSV/JSON Ingestion (Pilot Network Data)

**Tasks:**
1. Load 2+ pilot networks' data:
   - Brussels Network (28 spaces, CSV)
   - Vienna Network (35 spaces, API JSON)
2. Map external schema → internal Space schema
3. Bulk create spaces + relationships
4. Validate no duplicates

**Note:** This is a data task, not code. Phase 1 should ingest real data ASAP to begin measurement.

**Acceptance Criteria:**
- ✅ Brussels 28 spaces in Neo4j
- ✅ Vienna 35 spaces in Neo4j
- ✅ All spaces have correct network affiliation
- ✅ Freshness calculated for all

**Estimated effort:** 6h

---

#### Story 2.5: REST API Endpoints (GET /spaces, GET /networks, POST /verify)

**Tasks:**
1. Implement endpoints:
   - `GET /spaces` — returns all spaces (paginated, filterable)
   - `GET /spaces/{id}` — detailed space view
   - `GET /networks` — all networks
   - `GET /networks/{id}/spaces` — spaces in network
   - `POST /verify` — submit verification (via magic-link JWT)
2. Filtering support:
   - `?freshness=fresh`
   - `?skill=metalworking`
   - `?network=brussels-network`
3. Pagination:
   - `?limit=50&offset=0`

**Acceptance Criteria:**
- ✅ All endpoints return valid JSON (test with curl)
- ✅ Filters work correctly
- ✅ Pagination works (test: 100 spaces, limit=50, get two pages)
- ✅ OpenAPI docs show all endpoints + examples

**Estimated effort:** 10h

---

#### Story 2.6: Skills + Partnerships Model

**Tasks:**
1. Implement skill relationships:
   - Create Skill nodes (metalworking, electronics, etc.)
   - Add Space -[:HAS_SKILL {level, professionals, advanced}]-> Skill
   - `GET /spaces/{id}/skills` endpoint
2. Implement partnerships:
   - Create Space A -[:SUGGESTS_PARTNERSHIP]-> Space B (pending)
   - Space B validates → upgrade to -[:PARTNERSHIP {type}]->
   - `GET /spaces/{id}/partnerships` endpoint
3. Partnership types: skill_exchange, mentorship, co_hosting, resource_sharing

**Acceptance Criteria:**
- ✅ Skills attached to spaces correctly
- ✅ Partnership suggestions create pending edge
- ✅ Validation upgrades to confirmed edge
- ✅ API endpoints return partnerships + status

**Estimated effort:** 10h

---

### Week 4 Summary

| Story | Effort | Status |
|-------|--------|--------|
| 2.1 | 8h | ⬜ |
| 2.2 | 10h | ⬜ |
| 2.3 | 8h | ⬜ |
| 2.4 | 6h | ⬜ |
| 2.5 | 10h | ⬜ |
| 2.6 | 10h | ⬜ |
| **Week 4 Total** | **52h** | |

**Target:** ~46h available; Week 4 overruns by 6h (OK; acceptable)

---

### Week 5: Integration + Testing

**Stories 2.7-2.10:**

| Story | Title | Effort |
|-------|-------|--------|
| 2.7 | A2A Protocol Exploration (or fallback to REST) | 6h |
| 2.8 | E2E Test: Verification Flow | 8h |
| 2.9 | Pilot Network Integration Testing | 6h |
| 2.10 | M2 Refinement + Performance Tuning | 6h |

**Week 5 Total:** 26h ✅ (under budget; leaves 20h buffer)

**M2 Total:** 52 + 26 = **78 hours** (matches €4,000 budget ✅)

---

## MILESTONE 3: Map Interface & Verification Flow (Weeks 6-7)

### Goal
"Users can see interactive map of spaces, color-coded by freshness, and verify their space in <2 minutes via magic link."

### Week 6: Frontend Setup + Map

#### Story 3.1: SvelteKit Project Scaffold

**Tasks:**
1. Create SvelteKit project:
   - Router setup
   - Layout/page structure
   - Environment variables (.env)
2. Install & configure:
   - Leaflet.js (map library)
   - Tailwind CSS (styling)
   - TypeScript support
3. Create basic pages:
   - `/` — Map page
   - `/space/[id]` — Space detail
   - `/verify` — Verification form

**Acceptance Criteria:**
- ✅ Project builds without errors
- ✅ Dev server runs at localhost:5173
- ✅ Routes work (navigate between pages)

**Estimated effort:** 6h

---

#### Story 3.2: Leaflet.js Map Integration + OSM Rendering

**Tasks:**
1. Initialize Leaflet map:
   - Center on Europe (default view)
   - Zoom levels 2-16
   - OpenStreetMap basemap
2. Render space markers:
   - Load spaces via `/api/spaces`
   - Create marker for each space
   - Color by freshness: green (✅), yellow (⚠️), gray (🧟), black (💀)
3. Click marker → open space detail popup

**Acceptance Criteria:**
- ✅ Map renders without errors
- ✅ Spaces appear as color-coded markers
- ✅ Map is responsive (works on mobile)
- ✅ Zoom/pan works smoothly

**Estimated effort:** 8h

---

#### Story 3.3: Space Detail Card + Verification Form

**Tasks:**
1. Create detail card component:
   - Space name, address, contact
   - Freshness status + last verified date
   - Skills taught (anonymized counts)
   - Partnerships
2. Verification form:
   - Email input: `user@space.org`
   - Submit → calls `POST /verify/magic-link`
   - Success message: "Check your email!"
3. Verification confirmation page:
   - Token in URL
   - Displays space name
   - Confirm button → calls `POST /verify`
   - Success: "Thank you! Space verified ✅"

**Acceptance Criteria:**
- ✅ Detail card displays all info
- ✅ Email form submits successfully
- ✅ Verification token works (7-day expiry)
- ✅ Confirmation page accessible via token link

**Estimated effort:** 10h

---

#### Story 3.4: Frontend-Backend Integration

**Tasks:**
1. Connect frontend to backend API:
   - Fetch spaces on page load
   - Handle loading + error states
   - Refresh button to re-fetch
2. Environment variables:
   - `.env.local` for development (`http://localhost:8000`)
   - `.env.production` for production (`https://maps.making`)
3. CORS handling:
   - Backend allows frontend origin

**Acceptance Criteria:**
- ✅ Frontend loads spaces from API
- ✅ Maps update when spaces change
- ✅ No CORS errors
- ✅ Works in both dev + production modes

**Estimated effort:** 6h

---

#### Story 3.5: Responsive Design + Mobile Support

**Tasks:**
1. Test responsiveness:
   - Desktop (1920px)
   - Tablet (768px)
   - Mobile (375px)
2. Mobile-specific UI:
   - Tap markers (not hover)
   - Detail card fills viewport width
   - Verification form optimized for small screens
3. Accessibility:
   - ARIA labels for map markers
   - Keyboard navigation support
   - Color-blind friendly (not just color for status)

**Acceptance Criteria:**
- ✅ Map usable on all screen sizes
- ✅ No horizontal scrolling on mobile
- ✅ Touch gestures work (pinch-zoom)
- ✅ WCAG AA accessibility standard

**Estimated effort:** 8h

---

### Week 6 Summary

| Story | Effort | Status |
|-------|--------|--------|
| 3.1 | 6h | ⬜ |
| 3.2 | 8h | ⬜ |
| 3.3 | 10h | ⬜ |
| 3.4 | 6h | ⬜ |
| 3.5 | 8h | ⬜ |
| **Week 6 Total** | **38h** | ✅ Under budget |

---

### Week 7: Polish + Testing

**Stories 3.6-3.10:**

| Story | Title | Effort |
|-------|-------|--------|
| 3.6 | Search + Filter UI (skills, freshness, location) | 8h |
| 3.7 | Embeddable Map Widget (iframe version) | 8h |
| 3.8 | E2E Tests (Playwright) | 8h |
| 3.9 | Performance Optimization (bundle size, load time) | 6h |
| 3.10 | M3 Polish + Accessibility Review | 6h |

**Week 7 Total:** 36h ✅

**M3 Total:** 38 + 36 = **74 hours** (€3,840 budget ✅)

---

## MILESTONE 4: Integration, Testing & Deployment (Week 8)

### Goal
"System is production-ready, tested end-to-end, deployed to Hetzner, documented, and receiving pilot network feedback."

#### Story 4.1: End-to-End Test Suite

**Tasks:**
1. Write E2E scenarios (Playwright):
   - **Journey 1:** User searches for space in Berlin → Finds ElektroLab → Verifies it
   - **Journey 2:** Network coordinator views network health dashboard
   - **Journey 3:** Researcher queries temporal data ("Show spaces from Jan 2025")
2. Test all critical paths:
   - Map loads → Click space → See details ✅
   - Email verification flow ✅
   - Admin dashboard metrics collection ✅

**Acceptance Criteria:**
- ✅ 100% of critical journeys pass
- ✅ Tests run in CI pipeline on every commit
- ✅ Test reports visible in GitHub Actions

**Estimated effort:** 8h

---

#### Story 4.2: IPFS Backup + Restore

**Tasks:**
1. Implement nightly snapshot:
   - Export Neo4j to GraphML
   - Upload to IPFS
   - Log IPFS hash
2. Implement restore:
   - `POST /admin/restore?ipfs_hash=QmXxxx`
   - Download snapshot
   - Restore Neo4j from backup
3. Test failover:
   - Simulate data loss
   - Restore from IPFS
   - Verify data integrity

**Acceptance Criteria:**
- ✅ Nightly export completes in <5 minutes
- ✅ IPFS upload successful (hash logged)
- ✅ Restore works; data matches original
- ✅ Failover tested (data loss scenario)

**Estimated effort:** 8h

---

#### Story 4.3: Production Deployment (Hetzner)

**Tasks:**
1. Configure Hetzner VPS:
   - OS: Ubuntu 22.04
   - Instance: CX21 (2 vCPU, 4GB RAM, 40GB SSD)
   - Firewall rules: SSH, HTTP, HTTPS only
2. Deploy application:
   - Docker Compose on VPS
   - NGINX reverse proxy
   - SSL certificate (Let's Encrypt)
3. Setup monitoring:
   - Uptime checks
   - Error logs to stdout
   - Admin dashboard accessible at `/admin/dashboard`

**Acceptance Criteria:**
- ✅ Application accessible at https://maps.making
- ✅ HTTPS working (valid cert)
- ✅ API endpoints responding
- ✅ Monitoring + alerts configured

**Estimated effort:** 8h

---

#### Story 4.4: Documentation + API Specs

**Tasks:**
1. Write user documentation:
   - "How to verify your space" (5 min guide)
   - "How to embed the map on your site" (iframe snippet)
   - "FAQ" (common questions)
2. Write API documentation:
   - OpenAPI spec (auto-generated from FastAPI)
   - Example curl commands
   - Postman collection
3. Write operational runbook:
   - How to deploy updates
   - How to monitor system health
   - Troubleshooting guide

**Acceptance Criteria:**
- ✅ User docs are clear enough for non-technical space operators
- ✅ API docs are complete + examples work
- ✅ Team can deploy from runbook without asking questions

**Estimated effort:** 8h

---

#### Story 4.5: Pilot Network Feedback Loop

**Tasks:**
1. Onboard pilot networks:
   - Provide credentials + access
   - Training call (30 min each, 3-5 networks)
   - Feedback survey
2. Collect feedback:
   - "Was the verification process easy?" (target: <2 min)
   - "Did the map show accurate data?"
   - "What's missing for your network?"
3. Triage feedback:
   - Quick fixes (Phase 1)
   - Phase 2 items (backlog)
   - Won't-fix items (out of scope)

**Acceptance Criteria:**
- ✅ All pilot networks have access
- ✅ Feedback collected from ≥3 networks
- ✅ Quick fixes implemented
- ✅ Backlog items documented for Phase 2

**Estimated effort:** 6h

---

#### Story 4.6: Admin Dashboard + Cost Tracking

**Tasks:**
1. Implement admin dashboard endpoints (from admin-dashboard-spec.md):
   - `GET /admin/costs/central` (Mistral, Hetzner, IPFS)
   - `GET /admin/health/performance` (response times, errors, uptime)
   - `GET /admin/quality/freshness` (freshness distribution, at-risk spaces)
2. Manual cost tracking:
   - Set up weekly cost report collection from networks
   - Aggregate into JSON (stored in repo or small DB)
3. Weekly markdown report generation:
   - Script that pulls metrics + generates summary
   - Email to team

**Acceptance Criteria:**
- ✅ Dashboard endpoints return valid JSON
- ✅ Metrics are collected daily/weekly
- ✅ Weekly report generated automatically
- ✅ Reports tie back to COST-SUSTAINABILITY.md projections

**Estimated effort:** 8h

---

### Week 8 Summary

| Story | Effort | Status |
|-------|--------|--------|
| 4.1 | 8h | ⬜ |
| 4.2 | 8h | ⬜ |
| 4.3 | 8h | ⬜ |
| 4.4 | 8h | ⬜ |
| 4.5 | 6h | ⬜ |
| 4.6 | 8h | ⬜ |
| **Week 8 Total** | **46h** | ✅ On budget |

**M4 Total:** 46 hours (€2,880 budget ✅)

---

## Phase 1 Summary: Budget vs Actual

| Milestone | Budget (€) | Hours | Status |
|-----------|-----------|-------|--------|
| **M1: Backend Foundation** | €5,200 | 142 | ✅ Planned |
| **M2: Domain Adaptation** | €4,000 | 78 | ✅ Planned |
| **M3: Map Interface** | €3,840 | 74 | ✅ Planned |
| **M4: Integration & Deploy** | €2,880 | 46 | ✅ Planned |
| **Subtotal (Development)** | **€15,920** | **340** | ✅ On budget |
| **Infrastructure** | €245 | - | ✅ |
| **Contingency (15%)** | €2,420 | - | ✅ Buffer |
| **TOTAL** | **€18,585** | **~346h** | ✅ Matches NLNet request |

**Available development time:** 8 weeks × 46h = 368 hours
**Estimated effort:** 346 hours
**Buffer:** 22 hours (can handle 1 sprint worth of overrun)

---

## Execution Guidelines

### Daily Stand-Up (Async)

**Format:** 2-3 sentences in team channel

```
Today: Working on Story 2.3 (Freshness decay algorithm)
Blockers: None
Tomorrow: Unit tests for Story 2.3
```

### Weekly Retrospective (Friday)

**Topics:**
1. Stories completed this week
2. Blockers + solutions
3. Actual vs estimated effort
4. Adjustments for next week

### Risk Management

| Risk | Mitigation | Owner |
|------|-----------|-------|
| Mistral API downtime | Test with mock; implement fallback | DevOps |
| Neo4j scaling issues | Start with CX21; monitor growth | Backend |
| Pilot network data delays | Get data in Week 2, use synthetic if needed | PM |
| Scope creep | Track all requests as Phase 2 backlog | PM |
| Team member unavailability | Have backup for critical path items | PM |

---

## Related Documents

- **round-1-roadmap.md** — Original budget + timeline (this plan operationalizes it)
- **admin-dashboard-spec.md** — Detailed spec for Story 4.6
- **phase-2-3-research-plan.md** — Research questions to measure during Phase 1
- **PERSONAS.md** — User journeys that drive acceptance criteria
- **COST-SUSTAINABILITY.md** — Budget + cost assumptions
- **architecture.md** — Technical decisions that inform story breakdown

---

## Success Criteria: End of Phase 1

✅ **MVP is live** on Hetzner with real pilot network data
✅ **All 4 milestones completed** (no critical items pushed to Phase 2)
✅ **≥3 pilot networks verified** their spaces
✅ **Freshness decay working** (at least 80% of spaces verified in last 30 days)
✅ **Admin dashboard** collects cost + quality metrics
✅ **Budget on-target** (actual vs estimated effort within 10%)
✅ **Documentation complete** (users can navigate without asking questions)
✅ **Research framework ready** for Phase 2 decision-making

---

## Next: Phase 2 Planning

Once Phase 1 is complete (Week 8), the team will:

1. **Review Phase 1 metrics** (admin dashboard data)
2. **Answer research questions** (Q1-5 from phase-2-3-research-plan.md)
3. **Plan Phase 2** based on evidence, not speculation
4. **Apply for Erasmus+ KA220** funding (€20-30k)

---

_Phase 1 Sprint Plan prepared for 8-week MVP execution_
_Next: Developer onboarding + Week 1 kick-off_

