---
stepsCompleted: ['step-01-init', 'step-02-discovery', 'step-02b-vision', 'step-02c-executive-summary', 'step-03-success', 'step-04-journeys', 'step-05-domain', 'step-06-innovation', 'step-07-project-type', 'step-08-scoping', 'step-09-functional', 'step-10-nonfunctional', 'step-11-polish', 'step-12-complete']
inputDocuments: ['maps_of_making-handoff.zip/Maps of Making.html', 'maps_of_making-handoff.zip/app.js', 'ndb_hugo/content/posts/map-of-making-locker/index.md']
workflowType: 'prd'
briefCount: 0
researchCount: 0
brainstormingCount: 0
projectDocsCount: 3
classification:
  projectType: web_app
  domain: civic/open-data-commons
  complexity: high
  projectContext: brownfield
  phases: 2
---

# Product Requirements Document - maps_of_making

**Author:** nicolas
**Date:** 2026-04-20

## Executive Summary

Maps of Making is a federated open-data platform for the European maker ecosystem, piloting with RFF (France) and VOW (Germany). It inverts the broken directory model: instead of spaces registering on platforms they never update, each space publishes one structured JSON endpoint they control — and the map reads from it live. Freshness is automatic. No logins, no forms, no middlemen.

The immediate deliverable is a production-ready SPA built on the existing hi-fi prototype: a fullscreen MapLibre map with Protomaps vector tiles (replacing blocked OSM/Carto raster tiles), filter/search/detail drawers, and embeddable iframe + web component output. Phase 1 ships a convincing, working map with federation UI placeholders clearly labelled as phase 2.

Phase 2 wires the federated backend: URL ingestion, Oxigraph SPARQL triplestore, and a Nanobot agent (OpenRouter-compatible, Discord + Telegram built-in) enabling natural language queries over live endpoints. Space coordinators add their URL once and see their pin flip ⚪→🔵. Network admins get a dashboard with endpoint health monitoring, diff detection, and Oxigraph sync status.

**Primary users:** Space coordinators (claim your pin, publish once, forget it); network admins (confidence dashboard — who's live, stale, or broken at a glance). Makers browsing the map are secondary users.

### What Makes This Special

Every existing maker directory asks spaces to come to them — register, fill a profile, never update it. Maps of Making flips the contract: the space owns the data, publishes it once, and every map that cares reads from them. The ⚪→🔵 pin flip is not a UI flourish — it's proof the federated model works. When enough spaces have live endpoints, natural language queries become possible ("open wood workshops in Hamburg this weekend") without hallucination: structured data, spatial query, LLM as translation layer only.

The group chat question "is the Venice fab lab still open?" is the metric. This product makes it answerable without asking 200 people.

### Project Classification

- **Type:** Web application (SPA + federated backend)
- **Domain:** Civic / open-data commons
- **Complexity:** High (SPA layer: medium; federated PoC with Oxigraph + LLM agents: high)
- **Context:** Brownfield — hi-fi prototype exists, production implementation with Protomaps + federation layer
- **Phases:** 2 (Phase 1: map SPA; Phase 2: federated PoC)

## Success Criteria

### User Success

- **Coordinator:** Adds URL via "Add your URL" drawer, sees pin flip ⚪→🔵 within minutes, requires no follow-up support after initial workshop onboarding
- **Network admin:** Opens dashboard, identifies live/stale/broken spaces at a glance, can triage and contact a broken space in under 2 minutes
- **Maker (secondary):** Finds a confirmed open space near their destination without posting in a group chat

### Business Success

- **Phase 1:** Map loads cleanly — tiles render, pins stable at all zoom levels, embed snippet functional — sufficient to demo to RFF/VOW coordinators and generate genuine interest
- **Phase 2:** 5–10 spaces from RFF/VOW pilot with confirmed live JSON endpoints on the map (proves the federated model works end-to-end); at least 1 functional bot query in a real Mattermost or Matrix channel; output credible enough to anchor workshop curriculum and support grant applications
- **Validation signal:** A real question that previously went to a group chat gets answered by the map

### Technical Success

- Protomaps tiles load reliably — no referer blocks, no pin drift at any zoom level
- Oxigraph ingests and syncs endpoints; diff detection flags stale/broken URLs automatically
- Nanobot agent translates natural language to SPARQL via OpenRouter (LiteLLMProvider), with a validation gate against the IoP ontology before queries reach the triplestore
- System degrades gracefully — map remains functional if up to 50% of endpoints are unreachable

### Measurable Outcomes

| Metric | Phase 1 | Phase 2 |
|---|---|---|
| Tiles loading without error | 100% | 100% |
| Confirmed live endpoints | n/a | 5–10 spaces |
| Working bot queries | n/a | ≥1 in real channel |
| Admin dashboard uptime | n/a | visible to network admin |
| Demo viability | Yes | Workshop + grant ready |

## Product Scope

### MVP — Phase 1 (Demo-ready map SPA)

Production-ready implementation of existing prototype: Protomaps vector tiles, MapLibre, filters, search, detail drawer, embed (iframe + web component). Federation UI elements ("Add your URL", "Ask the map") present but clearly labelled as phase 2 placeholders. No backend wiring.

### Growth — Phase 2 (Federated PoC, workshop + grant ready)

URL ingestion pipeline, Oxigraph SPARQL triplestore, ⚪→🔵 pin confirmation, Nanobot agent (Discord + Telegram built-in, Mattermost custom adapter at pilot), admin dashboard (health monitoring, diff detection, sync status). Coordinator onboarding via facilitated workshops + JSON schema guide.

## User Journeys

### Journey 1 — The Coordinator: "Just tell me it's working"

**Meet Sophie**, coordinator at Atelier Commun, a woodworking collective in Lyon. She manages 40 members, maintains 12 machines, runs the newsletter, and answers the same three questions on Mattermost every week. Someone from RFF just sent her a message: "We're piloting a new map — can you add your space? It takes 5 minutes."

She clicks the map link. It loads. There's a pin near Lyon — grey, unclaimed. Her space. She clicks "Add your URL", pastes the URL of the JSON file she set up during the RFF workshop. Hits "Fetch & validate." The form confirms: name matches, address geocodes correctly, status reads "open". She submits. Her pin flips 🔵. She screenshots it and drops it in the RFF channel. She never logs in again. Six months later the pin is still blue.

**Capabilities required:** URL validation UX, geocoding feedback, pin state change confirmation, silent reliability.

---

### Journey 2 — The Coordinator: "Something broke and I don't know why"

**Same Sophie**, three months later. She changed her website and forgot the JSON file was on a subdomain that no longer resolves. Her pin shows a dashed outline — stale. She gets an email from the admin: last successful fetch date, error response, one-click link back to the "Add your URL" form pre-filled with her current URL. She updates the path. Pin goes back to 🔵 next sync.

**Capabilities required:** Automated diff/health detection, coordinator notification on failure, pre-filled recovery form, clear error messaging.

---

### Journey 3 — The Network Admin: "I need to know the state of the fleet"

**Meet Luca**, network coordinator at VOW. He manages 60+ member spaces across Germany. Every month: "are we on the map?" from members, "how many confirmed spaces?" from grant reviewers. He opens the admin dashboard: 23 confirmed (🔵), 18 seeded (⚪), 4 stale (dashed), 2 broken (🔴). Clicks broken ones — one 404, one CORS error. Hits "Send reminder" on both. Exports confirmed count for the grant report. Done in 8 minutes.

**Capabilities required:** Admin dashboard with fleet health overview, per-space drill-down, one-click coordinator contact, exportable stats, Oxigraph sync status.

---

### Journey 4 — The Maker (secondary): "I'm going to Hamburg next week"

**Meet Arjun**, maker based in Paris, going to Hamburg for a conference. Searches the group chat — three replies, none confirmed. Someone links him the Maps of Making embed on the RFF website. He filters "confirmed + open", zooms to Hamburg. Three pins. Clicks one — detail drawer: hours, specialties (electronics, laser cutting), space contact (generic email / webform / website link — never a person). He reaches out through the space's own channel. Response same day.

**Capabilities required:** Filter/search, detail drawer with contact info, embed on third-party site, confirmed status visible and trustworthy.

---

### Journey 5 — The Bot Query (Phase 2)

**Same Arjun**, next time. Types in RFF Mattermost: *"Des espaces confirmés avec du travail du bois à Hamburg ou Berlin ce week-end?"* Bot replies in 30 seconds: 2 confirmed spaces, opening hours, distance from Hamburg Hbf. He contacts one directly in the channel.

**Capabilities required:** Nanobot agent wired to Oxigraph, Discord slash command integration, SPARQL validation gate, French → query → French response round-trip.

---

### Journey Requirements Summary

| Journey | Capabilities Required |
|---|---|
| Coordinator onboarding | URL validation, geocoding, pin state confirmation |
| Coordinator recovery | Health monitoring, failure notification, pre-filled recovery UX |
| Admin dashboard | Fleet health view, per-space status, contact dispatch, export, sync status |
| Maker discovery | Filter/search, detail drawer, embed on third-party site |
| Bot query (Phase 2) | Agent + Oxigraph integration, channel bot, SPARQL validation |

## Domain-Specific Requirements

### Compliance & Regulatory

- **GDPR (light):** Public data model is space-level only, no personal data by design (see NFR-D1). The only personal data in the system is the coordinator's notification email on the admin side (registered for alerts on their space's endpoint health) — covered by a minimal privacy notice and right-to-erasure process.
- **GDPR closure logic (PoC-appropriate):** If a space endpoint is unreachable for N consecutive sync cycles → remove admin-side coordinator notification email → mark space as `closed` with `closed_at` timestamp. Historical record of the space preserved for map continuity. Revocation and full termination flows are out of scope for PoC.
- **Open data licensing:** All space data ingested into Oxigraph must preserve provenance (source URL, last-fetched timestamp). Re-publishing aggregated data requires attribution and open license declaration (CC-BY or similar).
- **No auth on public map:** The public map SPA must be fully accessible without login — no cookie consent wall on the map itself.

### Technical Constraints

- **Federated trust model:** The system never "owns" space data — it reads from source URLs. Stale cache must never be presented as live data. Provenance preserved in all aggregated outputs.
- **Schema governance:** JSON endpoint schema must be versioned. Parser must handle older schema versions gracefully (backwards-compatible, not hard failures). Minimum viable fields enforced via workshops.
- **SPARQL query safety:** LLM-generated SPARQL must pass a validation gate before reaching Oxigraph — no raw query execution, no injection vectors.
- **Graceful degradation:** Map SPA renders with zero confirmed endpoints (seed data fallback). Bot fails with plain-language error, not stack trace. Map usable if up to 50% of endpoints are unreachable.

### Integration Requirements

- **MapLibre GL JS + Protomaps/PMTiles:** Protocol registered client-side (`maplibregl.addProtocol("pmtiles", protocol.tile)`) — no tile server required. PMTiles file served from CDN/object storage (S3, Cloudflare R2). Regional FR+DE extract via `pmtiles extract` CLI. Basemap styles via `protomaps/basemaps` named flavors (`light`/`dark`/`white`) mapping to prototype tweaks. Vector tiles eliminate raster pin drift entirely.
- **Oxigraph:** SPARQL 1.1 query + update endpoints; RDF/JSON-LD ingestion.
- **Channel integrations (Phase 2):** Mattermost webhook/bot API first; Matrix and Discord as follow-on.
- **SpaceAPI-compatible schema:** JSON endpoint format extends SpaceAPI spec for cross-ecosystem reuse.

### Risk Mitigations

| Risk | Mitigation |
|---|---|
| Space endpoint goes dark silently | Automated diff detection + admin alert + coordinator notification |
| LLM generates invalid SPARQL | Validation gate + fallback "I couldn't parse that query" |
| Schema drift across spaces | Versioned schema + backwards-compatible parser + workshop-enforced minimum fields |
| Tile hosting goes down | CDN-backed PMTiles + graceful fallback (pins still render without basemap) |
| Coordinator never fixes broken endpoint | Reminder email with pre-filled recovery form + admin "send nudge" button |
| Contact PII retained after space closes | GDPR closure logic: N failed syncs → remove PII → mark closed with date |

### Vision (Post-PoC)

Multi-network expansion beyond RFF/VOW; LLM-assisted JSON generator for self-serve coordinator onboarding; multi-channel bot; individual maker data layer with consent model; semantic ontology aligned with Internet of Production vocabulary.

## Innovation & Novel Patterns

> *"Design for graceful failure acknowledgment, not just graceful success paths. The quality of your error states determines long-term user trust more than the quality of your success states."*
>
> **Core product principle:** When a query doesn't fit the available data, the system must (A) ask for clarification in plain language, and (B) log the gap as a schema enrichment signal — feeding ontology evolution and future workshop curriculum. Failure is data, not an endpoint.

### Detected Innovation Areas

**1. The Data Sovereignty Flip**
Every existing maker directory pulls data toward a central platform. Maps of Making inverts this: the space is the authoritative source, the map is a reader. The innovation isn't a new technology — it's a new *contract* between spaces and directories, built on SpaceAPI's proven pattern and extended to the broader maker ecosystem at network scale (RFF + VOW).

**2. Freshness as a First-Class Signal**
No existing maker map treats data freshness as a product concern. Maps of Making makes staleness *visible* and *self-healing*. Pin states: ⚪ seeded · 🔵 confirmed · dashed stale · 🔴 broken · 🟢 live now. The 🟢 state — future tier — is fed by edge device and webhook pings (door sensor, channel activity, fridge ping). Something happened; the place is alive. More trustworthy than any form field.

**3. IoP Ontology as SPARQL Guardrail**
The Nanobot agent (OpenRouter-compatible via LiteLLMProvider, model-agnostic) translates natural language to SPARQL queries constrained by the Internet of Production ontology vocabulary. The ontology is loaded into Oxigraph as queryable RDF; a curated schema prompt (~2–5K tokens) guides LLM output; a two-stage validation gate rejects queries with unmapped predicates before they reach the triplestore. The LLM never invents facts — it only reformulates queries within known schema bounds. Failure rate ~10–15% is accepted and logged as schema enrichment signal.

**4. Reciprocal Visibility — the Embed Incentive Loop**
The embed snippet (iframe/web component showing the space's live pin on their own website) creates reciprocal visibility: stale data degrades *the coordinator's own web presence*, not just the directory. This inverts the maintenance motivation of every previous directory. Secondary effect: the bot deployed in a network's own Mattermost/Matrix channel makes the map a tool used where the community already lives — coordinators with skin in their own data quality become invested in keeping it fresh. Future extension: documentation-as-data-source using SOLID protocol (out of scope for PoC, in development as side project).

**5. Group Chat as Broken Infrastructure Signal**
The product's validation metric — a question that used to go to 200 people gets answered by the map — frames the group chat not as competition but as a diagnostic. Measure success by *reducing* a community behaviour, not replacing it.

### Market Context & Competitive Landscape

- **Existing directories** (fablabs.io, hackerspaces.org, makery.info, etc.): centralised pull model, data freezes at registration, no freshness signal
- **SpaceAPI**: proven federated model for hackerspaces, ~1000 spaces — Maps of Making extends this to fablabs, open workshops, biolabs
- **Internet of Production**: semantic vocabulary for manufacturing resources — aligned ontology direction, different community
- **No known project** combines federated endpoint harvesting + IoP-ontology-constrained SPARQL + LLM query translation + reciprocal embed incentive for civic maker infrastructure

### Validation Approach

| Innovation | Validation Signal | Phase |
|---|---|---|
| Data sovereignty flip | ≥5 spaces publish + maintain live endpoints for 3+ months | Phase 2 |
| Freshness visibility | Admin reports fewer "is X still open?" questions in group chat | Phase 2 |
| IoP ontology guardrail | ≥1 real bot query answered correctly; failure logs seed schema improvements | Phase 2 |
| Reciprocal visibility embed | Coordinator keeps endpoint fresh because embed on their own site degrades if stale | Phase 2 |
| Group chat reduction | Qualitative: coordinator names a question the map answered without asking 200 people | Phase 2 |

## Web App Specific Requirements

### Project-Type Overview

Single-Page Application (SPA). One HTML file + vanilla JS (prototype), minimal framework overhead, embeddable as a self-contained unit. The map is the app — no routing, no multi-page navigation.

**Hosting:** VPS, Docker Compose stack with Oxigraph and Nanobot agent as services. PMTiles file served from the same VPS (or CDN-fronted object storage). Admin dashboard on a separate subdomain (e.g. `admin.mapsofmaking.org`).

### Technical Architecture Considerations

- **SPA:** Confirmed. One persistent canvas with drawer states. No SSR needed; data fetched client-side from federated endpoints.
- **Browser Support:** Modern evergreen browsers with WebGL (~97% of current traffic). No IE11.
- **SEO:** Not a concern for the map SPA. Embed landing pages benefit from lightweight static wrapper (OG tags, title, description). Admin dashboard is auth-gated, SEO irrelevant.
- **Real-time:** Soft real-time — pin state reflects last sync cycle. 🟢 live-now tier (Phase 2+ vision) would require SSE or WebSocket push channel; out of scope for PoC.
- **Accessibility:** WCAG 2.1 AA. Prototype baseline is solid (`aria-label`, `role`, `aria-pressed`, `.sr-only`, reduced-motion support). MapLibre markers need keyboard navigation.

### Browser Matrix

| Browser | Support |
|---|---|
| Chrome / Edge (latest 2) | Full |
| Firefox (latest 2) | Full |
| Safari 16+ | Full |
| Mobile Chrome / Safari | Full (responsive, 720px breakpoint) |
| Older / IE | Not supported |

### Performance Targets

Authoritative performance targets are defined in the Non-Functional Requirements section (NFR-P1 through NFR-P5). Summary:

| Metric | Target | NFR ref |
|---|---|---|
| Map tile first paint | <2s p50, <4s p95 | NFR-P1 |
| Filter/search update | <200ms | NFR-P2 |
| Space detail drawer open | <300ms | NFR-P3 |
| Bot query response | TBD from PoC telemetry | NFR-P4 |

### Implementation Considerations

- Stay close to prototype structure — minimal build toolchain, vanilla JS preferred for Phase 1
- Embed snippet must be responsive by default — drop-in, no coordinator tweaking required
- Docker Compose services: `map-spa` (static), `oxigraph` (SPARQL), `mak-agent` (Nanobot: Discord + Telegram + heartbeat scheduling), `mak-link-handler` (magic link validation HTTP endpoint), `nginx` (reverse proxy + PMTiles serving)
- Admin dashboard (`admin.*` subdomain) is a separate lightweight page — auth-gated, same VPS
- Scheduler runs as isolated service to ensure heartbeat loop continues even if bot process crashes

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Experience MVP — prove the product feels credible enough to demo and attract pilot spaces. Phase 1 is the bait; Phase 2 is the hook.

**Resource Requirements:** Solo or very small team (1–2 devs). No dedicated ops — Docker Compose keeps it manageable. Workshop facilitation handled by Nicolas + network partners (RFF/VOW).

### Phase 1 — Demo-Ready Map SPA (MVP)

**Core journeys supported:** Maker discovery (filters, search, detail drawer), coordinator awareness (map exists, pin states visible), network embed on partner sites.

**Must-have capabilities:**
- [ ] Protomaps PMTiles integration replacing OSM/Carto (fix 403 + pin drift)
- [ ] MapLibre SPA: filters, search, detail drawer, legend — all working
- [ ] Embed output: iframe snippet + web component, responsive by default
- [ ] "Add your URL" drawer: present + labelled "phase 2 — not wired"
- [ ] "Ask the map" bot: present + labelled "phase 2 — not wired"
- [ ] Seed data: synthetic FR+DE spaces (already in prototype)
- [ ] Tweaks panel: paper/dim/dark map styles (already implemented)
- [ ] Hosted on VPS, accessible via public URL

**Out of scope for Phase 1:** Any live endpoint ingestion, Oxigraph, bot logic, admin dashboard.

### Phase 2 — Federated PoC (Workshop + Grant Ready)

**Core journeys supported:** Coordinator onboarding (URL → confirmed pin), admin dashboard (fleet health), bot query in Mattermost.

**Must-have capabilities:**
- [ ] URL ingestion pipeline: fetch, validate, geocode coordinator JSON endpoints
- [ ] Oxigraph SPARQL triplestore: ingest RDF from endpoints, IoP ontology loaded
- [ ] ⚪→🔵 pin confirmation: live status from Oxigraph sync
- [ ] Diff detection + staleness monitoring: periodic re-fetch, flag stale/broken
- [ ] GDPR closure logic: N failed syncs → remove PII → mark `closed` with date
- [ ] Admin dashboard (`admin.*` subdomain): fleet health, per-space drill-down, coordinator contact dispatch, sync status, stats export
- [ ] Nanobot agent: Discord + Telegram built-in, Mattermost custom adapter at pilot; IoP-ontology-constrained SPARQL, validation gate, graceful failure → clarify → log gap
- [ ] Coordinator notification: email on endpoint failure with pre-filled recovery link

**Out of scope for Phase 2:** Matrix/Discord channels, 🟢 live-now edge pings, JSON generator, SOLID data layer.

### Phase 3 — Expansion (Post-PoC Vision)

Multi-network beyond RFF/VOW; Matrix + Discord bot; 🟢 live-now tier via webhook/edge device pings; LLM-assisted JSON generator; individual maker data layer with consent model (SOLID protocol); ontology enrichment loop from query failure logs.

### Risk Mitigation Strategy

| Risk | Mitigation |
|---|---|
| Protomaps spike takes too long | 2–3 day timebox; patch OSM referer via proxy as fallback |
| Oxigraph + LLM integration complexity | Phase 1 ships independently; federation is additive |
| Spaces don't publish endpoints post-workshop | Reciprocal visibility embed is the incentive; workshops lower the barrier |
| Solo dev bandwidth | Phase 1 is mostly fixing existing code; Phase 2 is containerised and scoped tight |
| PoC doesn't attract grant interest | Phase 1 demo probes interest before committing to Phase 2 |

### Innovation Risk Mitigation

| Risk | Mitigation |
|---|---|
| Spaces don't maintain endpoints | Reciprocal visibility embed; diff detection makes stale visible publicly |
| LLM query translation fails | IoP ontology validation gate; graceful failure → clarify → log gap |
| Ontology gaps block real queries | Log unmapped queries; feed back into IoP ontology evolution + workshops |
| Network coordinators don't adopt | Phase 1 demo lowers barrier; workshops + JSON schema guide reduce friction |
| Federated model too complex for PoC | Phase 1 ships independently; federation is additive |

## Functional Requirements

**Core principle:** The map is a pure reader. We never edit records — we only ingest and display fresh data. The latest JSON at the registered URL is the truth; previous versions are kept as dated snapshots for historical record.

### Map Display & Navigation (Phase 1)
- **FR1** Fullscreen MapLibre GL JS map with Protomaps PMTiles vector tiles
- **FR2** Pan, zoom, and cluster expansion with pin stability at all zoom levels
- **FR3** Pin states rendered visually: ⚪ seeded / 🔵 confirmed / dashed stale / 🔴 broken
- **FR4** Default view centered on FR/DE pilot area with graceful fallback tiles on network failure

### Filtering & Search (Phase 1)
- **FR5** Filter drawer with facets: machines/capabilities, services, open-now hours
- **FR6** Text search across space name, city, tags
- **FR7** Filters and search update map pins live (no reload)
- **FR8** Shareable URL state encoding active filters + map bounds
- **FR9** Filter state persists across drawer close/reopen in session
- **FR10** Empty-state messaging when no results match
- **FR11** Clear-all-filters control

### Space Detail (Phase 1 + 2)
- **FR12** Click pin → detail drawer with space info, hours, machines, contact, links
- **FR13** Detail drawer shows data provenance: endpoint URL + last-ingested timestamp
- **FR14** Copy-to-clipboard for contact/address
- **FR14b** Ingestion history visible: list of dated snapshots with diff summary

### Embed & Sharing (Phase 1 + 2)
- **FR15** Iframe embed snippet generator for any space or filter state
- **FR16** Web component `<maps-of-making>` with configurable props (center, zoom, filter)
- **FR17** Embeds render with attribution link back to full map (reciprocal visibility)
- **FR18** Share button produces deep-link URL for current map state

### Coordinator Registration (Phase 2)
- **FR19** Coordinators register a space by submitting one JSON endpoint URL (no account)
- **FR20** Registration form validates URL reachability + JSON schema compliance
- **FR21** On successful registration, pin flips ⚪ seeded → 🔵 confirmed
- **FR22** Coordinators receive a reciprocal embed snippet to place on their own website
- **FR23** No edit UI — coordinators update their data by editing their JSON at the URL

### Endpoint Health & Ingestion (Phase 2)
- **FR24** Periodic fetch of all registered endpoints (6-hour cadence, configurable)
- **FR25** Endpoint state machine: confirmed → stale (N failed fetches) → broken → closed
- **FR25b** Closure logic: JSON self-reports closed OR N consecutive fetch failures → PII removed, space marked closed-at-date, pin retained for historical record
- **FR26** Diff detection between snapshots flags meaningful changes
- **FR27** Ingestion failures logged with reason (timeout, 4xx, 5xx, schema invalid)
- **FR27b** Append-only versioned snapshots — ingested data never overwritten, each fetch stored with timestamp

### Admin Dashboard (Phase 2)
- **FR28** Admin dashboard on separate subdomain showing all endpoints with current state
- **FR29** Dashboard filters: all / confirmed / stale / broken / closed
- **FR30** Per-endpoint detail: fetch history, last diff, error log
- **FR31** Manual re-fetch trigger per endpoint
- **FR32** Oxigraph sync status per endpoint
- **FR33** Export endpoint registry (CSV/JSON)
- **FR33b** Admin audit log: all admin actions timestamped and attributable

### Federated Query Layer (Phase 2)
- **FR34** Oxigraph SPARQL 1.1 endpoint exposes federated graph of all ingested spaces
- **FR35** Queries validated against Internet of Production (IoP) ontology as guardrail
- **FR35b** Lenient validation: non-compliant data ingested with warnings logged as ontology enrichment signals
- **FR36** Public SPARQL endpoint (read-only) for third-party integrations

### Natural Language Bot (Phase 2)
- **FR37** "Ask the map" bot accepts natural language questions
- **FR38** Nanobot agent translates NL → SPARQL using IoP ontology as prompt context (OpenRouter API via LiteLLMProvider, model-agnostic via config)
- **FR39** Bot returns results with source space links + query transparency (show SPARQL)
- **FR40** Bot acknowledges gracefully when query can't be answered; offers clarification
- **FR41** Failed/ambiguous queries logged as ontology gap signals
- **FR42** Nanobot deployed to Discord (built-in), Telegram (built-in), then Mattermost (custom adapter at pilot)

### Auth (Phase 2)
- **FR43** Admin subdomain gated by simple shared password (PoC-grade)
- **FR44** Public map and coordinator registration require no authentication

---

**Select:** [A] Advanced Elicitation  [P] Party Mode  [C] Continue to Non-Functional Requirements (Step 10 of 13)

## Non-Functional Requirements

**Scale envelope:** PoC targets 10 spaces → RFF+VOW pilot ~500 spaces. Full Internet of Production horizon ~15k. NFRs below sized for PoC/pilot; scale-hardening notes flagged for future implementation.

### Performance
- **NFR-P1** Map tile first paint <2s p50, <4s p95 on typical broadband; fully interactive <4s p50. Measured via admin dashboard from production traffic.
- **NFR-P2** Filter/search updates render <200ms (client-side, no network roundtrip)
- **NFR-P3** Space detail drawer opens <300ms from pin click
- **NFR-P4** Bot NL→SPARQL→response target TBD from real telemetry; admin logs min/avg/max per query to set the threshold
- **NFR-P5** No hardcoded SLAs until PoC baseline collected; all targets tracked live on admin dashboard

### Reliability & Ingestion
- **NFR-R1** Endpoint fetch uses ETag / Last-Modified conditional requests — pull + ingest only when diff detected (fast trust signal when coordinator edits their JSON)
- **NFR-R2** Fetch timeout 60s per endpoint with incremental backoff on failure
- **NFR-R3** Fetch cadence (6h default), failure thresholds (stale/broken/closed), and retention policy are **config-file driven**, not hardcoded — tuned from real PoC data
- **NFR-R4** Per-endpoint fetch latency logged (min/avg/max ms) and surfaced on admin dashboard
- **NFR-R5** Map SPA remains functional when up to 50% of endpoints are unreachable — stale data served with explicit provenance timestamp; degrade-to-stale, never degrade-to-empty
- **NFR-R6** Fetch worker failures never take down the public map — pipeline isolation (SPA serves last-good Oxigraph state; scheduler runs as isolated background service)
- **NFR-R7 (scale note — future)** At >500 endpoints: add per-domain rate limiting, jittered schedule, robots.txt respect, content-addressed dedup (SHA-256 of normalized payload) to avoid DDoSing small self-hosted JSON endpoints

### Security
- **NFR-S1** Admin subdomain gated by a single shared password (Nicolas + Jason only, PoC-grade) stored as env secret; rotation documented. Pilot and production will implement stronger auth (per-user accounts, MFA).
- **NFR-S2** Public map requires no auth; public SPARQL endpoint read-only with basic rate limiting
- **NFR-S3** Coordinator-submitted URLs validated for scheme (https only) and fetched server-side
- **NFR-S4** Admin audit log (FR33b) immutable append-only, retained indefinitely
- **NFR-S5** Bot SPARQL generation passes validation gate against IoP ontology before execution
- **NFR-S6** Admin dashboard exposes **operational metrics only** — no raw endpoint payloads or coordinator identifiers beyond what's public on the map

### Data Model — Space-not-People
- **NFR-D1** JSON endpoints describe **spaces, not individuals**. Space-level contact only: generic email, webform URL, or website link. No personal names, personal emails, or personal phone numbers.
- **NFR-D2** Ingestion validator rejects any record containing person-identifiable fields (`contact_person`, personal `email`, personal `tel`, etc.) → quarantine queue + admin alert (not silently dropped)
- **NFR-D3** SPARQL validation gate rejects any triple resolving to `schema:Person` or equivalent — structural enforcement, not post-hoc cleanup
- **NFR-D4** Skills/capabilities modeled as properties of the space (e.g. `schema:knowsAbout`), never attached to named individuals

### Compliance (GDPR light)
- **NFR-C1** Space closure (FR25b) triggers removal of current contact fields even though they are space-level — keeps historical record without active outreach surface
- **NFR-C2** Because the data model excludes personal data by design (NFR-D1), standard GDPR burden is dramatically reduced. Grant reviewers should read this as mature data stewardship.
- **NFR-C3** Anonymized historical snapshots are candidates for **immutable public archive on IPFS/IPLD** — civic history of the maker ecosystem. Retrieval, pinning governance, and persistence funding remain open questions; Phase 3 exploration.

### Accessibility
- **NFR-A1** WCAG 2.1 AA conformance for public map and coordinator registration; axe-core in CI
- **NFR-A2** Keyboard navigation for all drawers, filters, pin selection, bot input
- **NFR-A3** Screen reader announces pin state changes, filter result counts, drawer content
- **NFR-A4** Color is never sole indicator of pin state — shape/pattern accompanies ⚪🔵 dashed 🔴
- **NFR-A5** Map has non-map fallback: accessible list view of filtered results

### Integration
- **NFR-I1** Protomaps PMTiles served from own CDN or self-hosted (avoids upstream referer blocks)
- **NFR-I2** Oxigraph exposes standard SPARQL 1.1 HTTP protocol — compatible with third-party SPARQL clients
- **NFR-I3** Bot adapters (Discord first, then Mattermost and Matrix) share a protocol-agnostic core
- **NFR-I4** Embed web component works in any modern browser without framework dependency
- **NFR-I5** JSON endpoint schema extends SpaceAPI where compatible — reuse over reinvent

### LLM / Bot Operations
- **NFR-L1** Prompt cache hit-rate tracked on admin dashboard; optimization target set after baseline
- **NFR-L2** Max tokens per request capped; monthly cost ceiling enforced at infra level with alerting
- **NFR-L3** Retry budget defined: max attempts, jitter, fallback "I couldn't answer, try rephrasing or browse the map" on LLM unavailability
- **NFR-L4** Bot response latency SLO tracked separately from map tile SLO

### Observability (cross-cutting)
- **NFR-O1** Admin dashboard exposes: fetch latency (min/avg/max per endpoint), success rate, diff-detection rate, Oxigraph sync lag, bot query latency + success rate, map load performance, quarantine queue depth
- **NFR-O2** All "TBD" thresholds (cadence, failure counts, retention, bot latency SLO, perf SLAs) set in config **after real PoC telemetry** — no premature optimization

---

**Select:** [A] Advanced Elicitation  [P] Party Mode  [C] Continue to Polish Document (Step 11 of 12)
