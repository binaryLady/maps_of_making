---
stepsCompleted: ['step-01-validate-prerequisites', 'step-02-design-epics', 'step-03-create-stories', 'edit-2026-04-29']
lastEdited: '2026-04-29'
editSummary: 'Epic 3 reframed as ingestion pipeline prerequisite (added Story 3.0: ADR-015 transformation layer, aging/zombie/dead lifecycle in Story 3.2); Epic 4 replaced — operator observability dashboard (health pills, registry table, raw/ingested/displayed inspection panel); Epic 4b added as parallel non-blocking magic-link recovery (Stories 3.3-3.4 migrated); critical path updated: Epic 1 → 0 → 2 → 3 → 4'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - web/maps-of-making.html
---

# maps_of_making - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for maps_of_making, decomposing the requirements from the PRD, UX (phase-1 prototype) and Architecture (14 ADRs) into implementable stories for Phase 2 — the Federated PoC.

Phase 1 (map SPA, deployed at mapofmaking.debarquin.eu) is shipped. The epic/story work below targets Phase 2: URL ingestion pipeline, Oxigraph SPARQL triplestore, ⚪→🔵 pin confirmation, admin health dashboard, and NL bot via Discord/Telegram. Phase-1 UI elements (filters, search, add-URL, embed, tweaks, bot teaser) are treated as **hypotheses** to validate, adjust, or prune from pilot telemetry — not as locked scope.

## Requirements Inventory

### Functional Requirements

**Map Display & Navigation (Phase 1 — shipped, reference only)**
- FR1: Fullscreen MapLibre GL JS map with Protomaps PMTiles vector tiles
- FR2: Pan, zoom, cluster expansion with pin stability at all zoom levels
- FR3: Pin states rendered visually: ⚪ seeded / 🔵 confirmed / dashed stale / 🔴 broken
- FR4: Default view centered on FR/DE pilot area with graceful fallback tiles on network failure

**Filtering & Search (Phase 1 — shipped, pilot-validation candidate)**
- FR5: Filter drawer with facets: machines/capabilities, services, open-now hours
- FR6: Text search across space name, city, tags
- FR7: Filters and search update map pins live (no reload)
- FR8: Shareable URL state encoding active filters + map bounds
- FR9: Filter state persists across drawer close/reopen in session
- FR10: Empty-state messaging when no results match
- FR11: Clear-all-filters control

**Space Detail (Phase 1 shipped + Phase 2 extension)**
- FR12: Click pin → detail drawer with space info, hours, machines, contact, links
- FR13: Detail drawer shows data provenance: endpoint URL + last-ingested timestamp
- FR14: Copy-to-clipboard for contact/address
- FR14b: Ingestion history visible: list of dated snapshots with diff summary

**Embed & Sharing (Phase 1 shipped + Phase 2 polish)**
- FR15: Iframe embed snippet generator for any space or filter state
- FR16: Web component `<maps-of-making>` with configurable props (center, zoom, filter)
- FR17: Embeds render with attribution link back to full map (reciprocal visibility)
- FR18: Share button produces deep-link URL for current map state

**Coordinator Registration (Phase 2)**
- FR19: Coordinators register a space by submitting one JSON endpoint URL (no account)
- FR20: Registration form validates URL reachability + JSON schema compliance
- FR21: On successful registration, pin flips ⚪ seeded → 🔵 confirmed
- FR22: Coordinators receive a reciprocal embed snippet to place on their own website
- FR23: No edit UI — coordinators update their data by editing their JSON at the URL

**Endpoint Health & Ingestion (Phase 2)**
- FR24: Periodic fetch of all registered endpoints (6-hour cadence, configurable)
- FR25: Endpoint state machine: confirmed → stale (N failed fetches) → broken → closed
- FR25b: Closure logic: JSON self-reports closed OR N consecutive fetch failures → PII removed, space marked closed-at-date, pin retained for historical record
- FR26: Diff detection between snapshots flags meaningful changes
- FR27: Ingestion failures logged with reason (timeout, 4xx, 5xx, schema invalid)
- FR27b: Append-only versioned snapshots — ingested data never overwritten, each fetch stored with timestamp

**Admin Dashboard (Phase 2)**
- FR28: Admin dashboard on separate subdomain showing all endpoints with current state
- FR29: Dashboard filters: all / confirmed / stale / broken / closed
- FR30: Per-endpoint detail: fetch history, last diff, error log
- FR31: Manual re-fetch trigger per endpoint
- FR32: Oxigraph sync status per endpoint
- FR33: Export endpoint registry (CSV/JSON)
- FR33b: Admin audit log: all admin actions timestamped and attributable

**Federated Query Layer (Phase 2)**
- FR34: Oxigraph SPARQL 1.1 endpoint exposes federated graph of all ingested spaces
- FR35: Queries validated against Internet of Production (IoP) ontology as guardrail
- FR35b: Lenient validation: non-compliant data ingested with warnings logged as ontology enrichment signals
- FR36: Public SPARQL endpoint (read-only) for third-party integrations

**Natural Language Bot (Phase 2)**
- FR37: "Ask the map" bot accepts natural language questions
- FR38: Nanobot agent translates NL → SPARQL using IoP ontology as prompt context (OpenRouter via LiteLLMProvider, model-agnostic)
- FR39: Bot returns results with source space links + query transparency (show SPARQL)
- FR40: Bot acknowledges gracefully when query can't be answered; offers clarification
- FR41: Failed/ambiguous queries logged as ontology gap signals
- FR42: Nanobot deployed to Discord (built-in), Telegram (built-in), then Mattermost (custom adapter at pilot)

**Auth (Phase 2)**
- FR43: Admin subdomain gated by simple shared password (PoC-grade)
- FR44: Public map and coordinator registration require no authentication

### NonFunctional Requirements

**Performance**
- NFR-P1: Map tile first paint <2s p50, <4s p95; interactive <4s p50 (measured on admin dashboard)
- NFR-P2: Filter/search updates <200ms (client-side)
- NFR-P3: Space detail drawer opens <300ms from pin click
- NFR-P4: Bot NL→SPARQL→response latency TBD from telemetry
- NFR-P5: No hardcoded SLAs until PoC baseline; all targets live on admin dashboard

**Reliability & Ingestion**
- NFR-R1: Endpoint fetch uses ETag / Last-Modified conditional requests
- NFR-R2: Fetch timeout 60s per endpoint with incremental backoff
- NFR-R3: Fetch cadence, failure thresholds, retention policy config-driven
- NFR-R4: Per-endpoint fetch latency logged (min/avg/max ms) on admin dashboard
- NFR-R5: Map remains functional when ≤50% endpoints unreachable — degrade-to-stale, never empty
- NFR-R6: Fetch worker failures never take down public map (pipeline isolation)
- NFR-R7: (scale note — future) >500 endpoints: per-domain rate limiting, jittered schedule, robots.txt, content-addressed dedup

**Security**
- NFR-S1: Admin gated by single shared password (env secret, PoC-grade); pilot adds per-user + MFA
- NFR-S2: Public map no auth; public SPARQL read-only + basic rate limiting
- NFR-S3: Coordinator URLs validated (https only), fetched server-side
- NFR-S4: Admin audit log immutable append-only
- NFR-S5: Bot SPARQL generation passes IoP ontology validation gate before execution
- NFR-S6: Admin dashboard exposes operational metrics only — no raw payloads, no coordinator identifiers beyond public map

**Data Model — Space-not-People**
- NFR-D1: JSON endpoints describe spaces only. Space-level contact only (generic email, webform, website). No personal names/emails/phones.
- NFR-D2: Ingestion validator rejects records with person-identifiable fields → quarantine queue + admin alert
- NFR-D3: SPARQL validation gate rejects triples resolving to schema:Person
- NFR-D4: Skills/capabilities modeled as properties of the space, never attached to named individuals

**Compliance (GDPR light)**
- NFR-C1: Closure removes current contact fields; historical record preserved
- NFR-C2: Data model excludes personal data by design — reduced GDPR burden
- NFR-C3: Anonymized snapshots candidates for IPFS/IPLD civic archive (Phase 3)

**Accessibility**
- NFR-A1: WCAG 2.1 AA for public map + coordinator registration; axe-core in CI
- NFR-A2: Keyboard navigation for all drawers, filters, pin selection, bot input
- NFR-A3: Screen reader announces pin state changes, filter counts, drawer content
- NFR-A4: Color never sole indicator of pin state — shape/pattern accompanies ⚪🔵 dashed 🔴
- NFR-A5: Non-map fallback: accessible list view of filtered results

**Integration**
- NFR-I1: PMTiles served from own CDN or self-hosted
- NFR-I2: Oxigraph exposes standard SPARQL 1.1 HTTP protocol
- NFR-I3: Bot adapters share a protocol-agnostic core
- NFR-I4: Embed web component works in any modern browser without framework dep
- NFR-I5: JSON endpoint schema extends SpaceAPI where compatible

**LLM / Bot Operations**
- NFR-L1: Prompt cache hit-rate tracked on admin dashboard
- NFR-L2: Max tokens capped; monthly cost ceiling enforced at infra level with alerting
- NFR-L3: Retry budget defined (max attempts, jitter, plain-language fallback on LLM unavailable)
- NFR-L4: Bot response latency SLO tracked separately from map tile SLO

**Observability (cross-cutting)**
- NFR-O1: Admin dashboard exposes: fetch latency, success rate, diff-rate, Oxigraph sync lag, bot latency + success rate, map load perf, quarantine depth
- NFR-O2: All "TBD" thresholds set in config after real telemetry — no premature optimization

### Additional Requirements

*(From Architecture ADRs — technical work items that inform stories but are not FRs/NFRs)*

**Starter / Greenfield structure (ADR, no conventional template):**
- AR-ST1: Custom Python harness built from scratch as a standalone 3-file spike (not inside a Nanobot container). First implementation story is a spike: Discord bot `/ping` that chains OpenRouter + Oxigraph health check, proving dependency surface. **[Updated Epic 1 retro 2026-04-25: `hkuds/nanobot` image is not publicly available; must be built from source. Nanobot runs as a SEPARATE Docker Compose project, not embedded in maps_of_making. Spike uses custom harness. Nanobot integration begins at Epic 6.]**

**Infrastructure & Deployment (ADR-001, ADR-011, ADR-013, ADR-014):**
- AR-INF1: Docker Compose stack named `maps_of_making` (explicit) with services: `oxigraph`, `mak-link-handler` (FastAPI), nginx reverse proxy. Internal-only networking via `expose`, not `ports`. **[Updated Epic 1 retro 2026-04-25: `mak-agent` (Nanobot) is commented out of this compose file; Nanobot runs as a SEPARATE compose project joining the internal network via `external: true`. Epic 6 activates it.]**
- AR-INF2: nginx routes: `/sparql/query` → Oxigraph public read; `/sparql/update` → deny (internal only); `/claim/*` → mak-link-handler; admin subdomain shared-password basic auth.
- AR-INF3: Host cron daily N-Quads dump of Oxigraph → `/var/backups/oxigraph/` → rsync off-host, 7-day retention. IPFS+IPLD production direction deferred to pilot.
- AR-INF4: Secrets via `.env` on VPS (gitignored), `.env.example` committed with placeholders.
- AR-INF5: Manual deploy for PoC (`git pull && docker compose up -d --build`); GitHub Actions deferred to pilot.

**Data Architecture (ADR-006, ADR-007, core decisions):**
- AR-DATA1: Oxigraph named graph topology — `<urn:mak:space/{id}>` (current), `<urn:mak:space/{id}/{date}>` (snapshots, append-only), `<urn:mak:status>` (materialized freshness), `<urn:mak:presence>` (webhook open-now), `<urn:mak:notifications>` (queue), `<urn:mak:ontology/iop>`, `<urn:mak:ontology/mom>`.
- AR-DATA2: Freshness materialization — scheduler writes status triples (confirmed/aging/zombie/dead/error) on change; map queries filter `mak:visibility`; admin toggle overlays `mak:operationalState`. Lifecycle 30d/90d/180d configurable.
- AR-DATA3: Presence graph reserved now for "open-now" webhook; handler implemented late Phase 2.
- AR-DATA4: MOM ontology align-and-extend — Schema.org base + IoP `skos:closeMatch` + `mom:` extensions. Canonical IRI `https://w3id.org/maps-of-making/` → GitHub Pages.
- AR-DATA5: IoP ontology loaded at harness startup into dedicated named graph; ~15–20% subset extracted via CONSTRUCT, cached in memory, injected into every NL→SPARQL prompt. `RELOAD_ONTOLOGY=1` forces reload.

**Agent Framework & Harness (ADR-008, ADR-009, ADR-013):**
- AR-AGT1: Nanobot as agent framework — LiteLLM provider over OpenRouter; CronService + HEARTBEAT.md for scheduling; Discord + Telegram adapters built-in. **[Updated Epic 1 retro 2026-04-25: image NOT `FROM hkuds/nanobot:latest` (not public). Must clone github.com/HKUDS/nanobot and build locally. Runs as separate compose project. Not needed until Epic 6.]**
- AR-AGT2: Custom `tasks/` modules (heartbeat, nl_to_sparql, answer_format, notify_dispatch, magic_link) invoked by Nanobot; one task = one file; all return `str`.
- AR-AGT3: Multi-model assignments via config: Haiku for heartbeat, Sonnet (temp=0) for NL→SPARQL, Minimax for answer formatting.
- AR-AGT4: Discord defer pattern mandatory (`interaction.response.defer(thinking=True)`) on any LLM-involved command — bot timeout is 3s, LLM calls exceed this.
- AR-AGT5: Protocol-agnostic ChannelAdapter protocol — Discord first, Telegram built-in, Mattermost as custom adapter post-pilot.

**Magic Link / Notification (ADR-005, ADR-010, ADR-011):**
- AR-MLNK1: Dedicated FastAPI `mak-link-handler` container binds port 8000 internal, proxied at `/claim/*`. Discord bots cannot bind HTTP — this is separate by necessity.
- AR-MLNK2: Tokens are `base64url(HMAC-SHA256(uuid + expiry + space_id, LINK_SECRET))`. Stored as hash only, single-use, 72h TTL.
- AR-MLNK3: Notification dispatch is non-LLM for PoC — queue in Oxigraph (`<urn:mak:notifications>`), worker reads, fills template, sends, writes `mak:dispatched`. Retry 3× with backoff, escalate to network admins on failure.

**Operational Metrics (ADR-012):**
- AR-METR1: SQLite `./data/metrics.db` mounted into scheduler container. Tables: `heartbeat_log`, `llm_cost_log`. Exposed via internal `/metrics` JSON endpoint. **Not** in Oxigraph (breaks circular dependency when Oxigraph is down).

**Conventions / Code Standards:**
- AR-CONV1: Naming — `urn:mak:{type}/{id}` for named graphs; `mom:camelCase` properties / `mom:PascalCase` classes; `snake_case` Python; `verb_noun()` async functions; `mak-` prefix on Docker services.
- AR-CONV2: structlog from day one with `session_id` bound at request entry. Event names `noun.verb_past`.
- AR-CONV3: SPARQL strings as `SCREAMING_SNAKE_CASE` module constants; never f-strings with user/LLM input; use `VALUES` clauses. Use `run_select()` / `run_update()` helpers only.
- AR-CONV4: Heartbeat idempotency — `ASK` before `INSERT`, never blind overwrite.
- AR-CONV5: Single `config.py` module; tasks import from it, never load `config.yaml` directly.

**Seed / Bootstrap:**
- AR-SEED1: **Build a new `moms_seed.json` from real data sources** — current phase-1 synthetic seed is demo-only. Real seed must be assembled from: (a) existing `vow_workshops.json` scrape (VOW / offene-werkstaetten.org — name, address, categories, profile URL, website) and (b) an equivalent RFF (France) source to be identified/scraped. Raw scrape → normalize to MOM ontology fields → geocode addresses → dedup → emit canonical `moms_seed.json` consumed by `scripts/seed_import.py`.
- AR-SEED2: `scripts/seed_import.py` loads canonical `moms_seed.json` → JSON-LD → Oxigraph as ⚪ seeded spaces. Retired at pilot once live endpoints dominate.
- AR-SEED3: `scripts/load_ontology.sh` POSTs `mom.ttl` + `iop.ttl` to their named graphs (idempotent — ASK first).
- AR-SEED4: Category/tag vocabulary from raw scrapes (e.g. German `Holz`, `Metall`, `3D-Druck`) mapped to canonical MOM/Schema.org/IoP predicates via a translation table — preserves provenance but normalizes the filter facets across FR+DE.

### UX Design Requirements

*(Extracted from phase-1 prototype `web/maps-of-making.html` + explicit principles confirmed with user. Phase-1 UI elements are **hypotheses under fog-of-war** — each UX-DR includes whether it is "validate/keep", "extend", "prune candidate", or "new for Phase 2".)*

**Pin visual grammar & legend (ADR-004 — extend)**
- UX-DR1: Default map view shows only four pin states: ⚪ seeded, 🔵 confirmed, 🟢 open-now (badge on blue), 🔴 error. Aging/zombie/dead pins are hidden from default view — surfaced only via admin health toggle.
- UX-DR2: Legend card (bottom-left) stays compact and always-visible, enumerating the four public pin states with both color and shape/pattern (NFR-A4). Aging/zombie/dead states documented only in admin view legend.
- UX-DR3: Space detail drawer carries an amber "quiet banner" — "Last confirmed 8 months ago. Details may be outdated." — visible even without the admin toggle. Provenance (endpoint URL + last-ingested timestamp) always displayed (FR13).

**Progressive disclosure & cognitive load (principle — validate phase-1 drawers)**
- UX-DR4: Topbar buttons (Filters, Search, Preset & embed, Add your URL, Tweaks) are phase-1 hypotheses. Each requires a pilot-validation gate before Phase 2 lock-in. Document default state = all drawers closed; map is the surface.
- UX-DR5: Drawers (left Filters, right Detail, bottom Preset, right Add-URL, right Bot) follow consistent open/close animation contract (260ms cubic-bezier, transform-based); reduced-motion media query disables transitions (already implemented).
- UX-DR6: Tweaks panel (map style dim/dark, pin density, pulse on/off) is explicitly labeled "design only" — treat as developer/designer affordance, not end-user feature. Prune candidate for production; keep for pilot iteration.
- UX-DR7: "Ask the map" bot FAB is a phase-1 teaser with `soon` label. Phase 2 removes the teaser and wires real behavior; label transition must be explicit (no silent activation) so users can distinguish placeholder from real.

**Graceful failure states (core principle — new for Phase 2)**
- UX-DR8: Coordinator "Add your URL" form produces explicit error states for: invalid URL syntax, non-https scheme, timeout, 4xx/5xx response, schema violation, PII detected, duplicate registration. Each state renders in plain language with actionable next step. No raw stack traces.
- UX-DR9: Stale endpoint detail view (dashed pin) shows: last successful fetch timestamp, error type from last attempt, one-click "try re-fetch" for coordinator (reuses magic link flow), fallback "this space may have moved — contact network admin" CTA.
- UX-DR10: Broken endpoint detail view (🔴) shows the error category (404, CORS, timeout, schema invalid) in plain language + last known good snapshot as "historical record" label, clearly distinguishing historical vs live data.
- UX-DR11: Empty-state messaging across filters, search, bot results — never show "0 results" alone; always pair with diagnostic suggestion ("Try widening your filter" / "No confirmed spaces match — try including seeded pins").
- UX-DR12: Bot "I couldn't answer" response includes: plain-language acknowledgment, suggestion to rephrase OR browse the map directly, no stack traces, logs ontology gap triple internally (FR41, NFR-L3).
- UX-DR13: Map tile load failure falls back to paper-overlay background with pins still rendered (NFR-R5 degrade-to-stale visible; graceful degradation visible to the user, not a blank screen).

**Coordinator registration flow (new for Phase 2)**
- UX-DR14: `Add your URL` drawer transitions from phase-1 "simulated" state to real validation. Progression: URL entry → "Fetch & validate" → live feedback on fetch (reachable ✓, schema valid ✓, geocoded ✓, PII check ✓, pin preview) → submit → confirmation screen showing ⚪→🔵 transition + reciprocal embed snippet for their site (FR22).
- UX-DR15: Try-a-sample button (already in phase-1 HTML) must work against a real seed endpoint to demo the happy path before coordinator commits their own URL.
- UX-DR16: Magic link YES/NO confirmation screens (served by `mak-link-handler`) follow the map's zine aesthetic and match principles: YES = single confirmation + "thanks, your pin is live"; NO = graceful closure confirmation + "we'll mark this space closed on {date}, PII will be removed". No forms, no logins.

**Admin dashboard / Network health view (extend — priority per architecture)**
- UX-DR17: Fleet health overview as default admin landing — single glance shows counts by status (confirmed / seeded / stale / broken / closed) with proportional visual weight, plus sparkline of ingestion events over last 7 days.
- UX-DR18: Per-endpoint drill-down card: fetch history timeline, last diff summary, error log (structured, not raw), manual "re-fetch now" button (FR31), "send nudge" CTA to dispatch magic link reminder, Oxigraph sync status (FR32).
- UX-DR19: Admin toggle "Health map overlay" reveals aging/zombie/dead pins on the map itself with pattern differentiation (dashed, ghost, skull badge or similar — NFR-A4 no-color-only). Second SPARQL query, no page reload (ADR-006).
- UX-DR20: Export controls (CSV / JSON) for endpoint registry (FR33). Output includes public fields only — no audit log leakage (NFR-S6).
- UX-DR21: Admin audit log visible as reverse-chronological timeline: who, what action, when, on which space (FR33b).

**Accessibility (NFR-A1–A5 — validate & extend)**
- UX-DR22: All drawers, filter chips, pin interactions keyboard-reachable with visible focus indicator (`:focus-visible 2.5px accent outline` already in phase-1 CSS). Regression-test in Phase 2.
- UX-DR23: Screen reader announcements for: pin state changes (⚪→🔵, 🔵→stale), filter result count updates (already `aria-live="polite"` on `#results-count`), drawer open/close, bot response arrival.
- UX-DR24: Non-map accessible list view (NFR-A5) — reachable from a link/button in filters drawer, renders filtered results as a semantic `<ul>` with same content as pins. New for Phase 2.
- UX-DR25: axe-core audit wired into CI (NFR-A1). First story must establish CI hook.

**Embed & reciprocal visibility (extend)**
- UX-DR26: Embed mode (`body.embed-mode`) already hides chrome per phase-1 CSS. Phase 2 adds: visible "Last confirmed {date}" caption + attribution link back to full map (FR17). Stale-date prominently displayed so a stale embed visibly degrades the coordinator's own site (reciprocal incentive).
- UX-DR27: Web component `<maps-of-making>` with configurable props (center, zoom, filter) — same visual contract as iframe embed (FR16).

### FR Coverage Map

| FR | Epic | Description |
|---|---|---|
| FR1 | Epic 1 | MapLibre + PMTiles — shipped; Epic 1 wires to Oxigraph GeoJSON |
| FR2 | Epic 5 | Pan/zoom/cluster stability — polish pass |
| FR3 | Epic 1 | Pin states rendered from Oxigraph materialized status |
| FR4 | Epic 1 | Default view + graceful tile fallback |
| FR5 | Epic 5 | Filter drawer facets validated against real data |
| FR6 | Epic 5 | Text search against real space names/cities/tags |
| FR7 | Epic 5 | Live pin update on filter/search |
| FR8 | Epic 5 | Shareable URL state encoding |
| FR9 | Epic 5 | Session-persistent filter state |
| FR10 | Epic 5 | Empty-state messaging |
| FR11 | Epic 5 | Clear-all-filters control |
| FR12 | Epic 5 | Pin click → detail drawer (real federated data) |
| FR13 | Epic 2 | Detail drawer: provenance URL + last-ingested timestamp |
| FR14 | Epic 5 | Copy-to-clipboard for contact/address |
| FR14b | Epic 2 | Ingestion history + dated snapshot list in detail drawer |
| FR15 | Epic 5 | Iframe embed snippet generator |
| FR16 | Epic 5 | Web component `<maps-of-making>` |
| FR17 | Epic 5 | Embeds carry attribution + last-confirmed caption |
| FR18 | Epic 5 | Share button deep-link URL |
| FR19 | Epic 2 | Coordinator submits JSON endpoint URL (no account) |
| FR20 | Epic 2 | URL reachability + schema compliance validation |
| FR21 | Epic 2 | Pin flip ⚪ → 🔵 on successful registration |
| FR22 | Epic 2 | Reciprocal embed snippet returned to coordinator |
| FR23 | Epic 2 | No edit UI — coordinator updates JSON at source URL |
| FR24 | Epic 3 | Periodic endpoint fetch (6h cadence, configurable) |
| FR25 | Epic 3 | State machine: confirmed → stale → broken → closed |
| FR25b | Epic 3 | Closure logic: PII removed, space marked closed-at-date |
| FR26 | Epic 2 | Diff detection on first ingest (seed→claim transition) |
| FR27 | Epic 3 | Ingestion failure logging (timeout / 4xx / 5xx / schema) |
| FR27b | Epic 2 | Append-only versioned snapshots from first ingest |
| FR28 | Epic 4 | Admin dashboard: all endpoints + current state |
| FR29 | Epic 4 | Dashboard filters: confirmed / stale / broken / closed |
| FR30 | Epic 4 | Per-endpoint: fetch history, last diff, error log |
| FR31 | Epic 4 | Manual re-fetch trigger |
| FR32 | Epic 4 | Oxigraph sync status per endpoint |
| FR33 | Epic 4 | Export endpoint registry (CSV/JSON) |
| FR33b | Epic 4 | Admin audit log (timestamped, attributable) |
| FR34 | Epic 1 | Oxigraph SPARQL 1.1 endpoint (federated graph) |
| FR35 | Epic 6 | Queries validated against IoP ontology |
| FR35b | Epic 6 | Lenient validation: non-compliant data → warning + log |
| FR36 | Epic 1 | Public SPARQL endpoint (read-only, nginx-gated) |
| FR37 | Epic 6 | Bot accepts natural language questions |
| FR38 | Epic 6 | NL → SPARQL via OpenRouter + IoP ontology context |
| FR39 | Epic 6 | Bot returns results with source links + SPARQL transparency |
| FR40 | Epic 6 | Bot graceful failure → clarification offer |
| FR41 | Epic 6 | Failed queries logged as ontology gap triples |
| FR42 | Epic 6 | Discord (first) + Telegram built-in; Mattermost post-pilot |
| FR43 | Epic 4 | Admin subdomain shared-password auth (PoC-grade) |
| FR44 | Epic 1 | Public map + coordinator registration: no auth |

**AR coverage summary:**
- AR-SEED1–4 → Epic 0
- AR-INF1–5, AR-DATA1,4, AR-AGT1, AR-CONV1–5, AR-ST1 → Epic 1
- AR-DATA2 (seed→claim), AR-AGT2 (heartbeat first-fetch) → Epic 2
- AR-MLNK1–3, AR-DATA2 (freshness lifecycle), AR-METR1 → Epic 3
- AR-INF2 (admin auth), AR-METR1 (/metrics read) → Epic 4
- AR-DATA5, AR-AGT3–5 → Epic 6
- AR-DATA3 (presence graph reserved) → Epic 1 (schema slot) + Epic 7 (implementation)

## Epic List

### Epic 0: Pilot Seed Data Pipeline
Space coordinators, network admins, and makers see the map populated with credible real spaces from the FR+DE pilot ecosystem — not synthetic demo fixtures. A separate, clearly-isolated dataset of RFF mockup spaces provides health-state variety for the admin dashboard demo without polluting the real onboarding pool.

**Sequencing note:** Executes after Epic 1 Oxigraph is running. VOW data is real (eligible for organic ⚪→🔵 flip). RFF mockup data lives in an isolated named graph (`<urn:mak:mock/rff-health>`) with explicit `mak:source mak:mock-rff` provenance; droppable via `DROP GRAPH` before production. Belgium is intentionally left blank — demo of organic onboarding (Add your URL path in Epic 2).

**FRs:** FR3
**ARs:** AR-SEED1, AR-SEED2, AR-SEED3, AR-SEED4

---

### Epic 1: Federated Backend Foundation
The map reads live pin data from Oxigraph instead of a bundled JSON fixture. The backend stack (Oxigraph, Nanobot agent container, nginx routing, MOM + IoP ontologies loaded) runs on the VPS. A cached GeoJSON materialization means the map still loads in <2s regardless of dataset size.

**Architectural contracts reserved for future epics:**
- `<urn:mak:presence>` named graph slot + commented-out nginx webhook route (Epic 7)
- SPARQL UPDATE endpoint internal-only (security, NFR-S2)

**FRs:** FR1, FR3, FR4, FR34, FR36, FR44
**NFRs:** NFR-R6, NFR-S2, NFR-I1, NFR-I2, NFR-P1
**ARs:** AR-ST1, AR-INF1–5, AR-DATA1, AR-DATA3 (slot only), AR-DATA4, AR-AGT1, AR-CONV1–5

---

### Epic 2: Coordinator URL Onboarding — ⚪→🔵 Flip
A coordinator pastes their JSON-LD endpoint URL, sees live validation feedback (reachable, schema-valid, geocoded, PII-free), submits, watches their pin flip ⚪→🔵, and receives a reciprocal embed snippet to place on their own site. No login, no form to revisit. Detail drawer now shows provenance + ingestion history.

**Demo path:** Belgium coordinator = Openfab Brussels using this flow, not seeded.

**FRs:** FR13, FR14b, FR19, FR20, FR21, FR22, FR23, FR26, FR27b
**NFRs:** NFR-D1–D4, NFR-R1, NFR-S3, NFR-I5
**ARs:** AR-DATA2 (seed→claim), AR-AGT2 (heartbeat first-fetch)
**UX-DRs:** UX-DR8, UX-DR14, UX-DR15

---

### Epic 4: Operator Observability Dashboard
Nicolas (MOM operator) opens `/admin`, reads system health at a glance (Oxigraph status, ingestion process, spaces reachable count), scans the space registry table for failures, drills into any space for a raw/ingested/displayed side-by-side inspection panel. This is infrastructure observability for the pipeline operator — not a network coordinator view (Luca uses the public health map toggle, no auth required).

**Depends on:** Epic 3's raw snapshot-to-disk output and status graph. Epic 4 is a consumer, not a builder, of the pipeline.

**FRs:** FR28–FR33b, FR43
**NFRs:** NFR-S1, NFR-S4, NFR-S6, NFR-O1, NFR-O2, NFR-P5
**ARs:** AR-INF2 (admin subdomain + auth), AR-METR1 (/metrics endpoint read), ADR-015 (raw snapshot disk path)

---

### Epic 4b: Magic Link Coordinator Recovery *(parallel non-blocking)*
Space coordinators receive a magic-link email when their endpoint goes stale — YES refreshes pin, NO gracefully archives with GDPR closure. Parallel to Epic 4, non-demo-blocking. Depends on Epic 3's notification queue.

**FRs:** FR25b (closure logic)
**ARs:** AR-MLNK1–3

---

### Epic 5: Map Polish, Progressive Disclosure & Accessibility
The map now runs on real federated data: filters/search/detail drawer all read live. Phase-1 UI hypotheses are validated or pruned (tweaks panel, drawer ergonomics). Provenance banners, stale amber warnings, and accessible list view are added. Embeds carry "last confirmed" captions. axe-core in CI.

**FRs:** FR2, FR5–FR12, FR14, FR15–FR18
**NFRs:** NFR-P2, NFR-P3, NFR-A1–A5, NFR-I4
**UX-DRs:** UX-DR1–7, UX-DR11, UX-DR22–27

---

### Epic 3: Ingestion Pipeline + Endpoint Health + Stale Detection *(prerequisite for Epic 4)*
The full ingestion pipeline becomes real: SpaceAPI JSON is fetched, raw snapshot written to disk, transformed to MOM JSON-LD via the ontology mapping layer (ADR-015), and ingested into Oxigraph. Heartbeat scheduler runs the full 6h cycle with aging/zombie/dead lifecycle. Epic 4 reads from this epic's outputs. Magic-link coordinator recovery is extracted to Epic 4b (parallel, non-blocking).

**FRs:** FR24, FR25, FR25b, FR26, FR27, FR27b
**NFRs:** NFR-R1, NFR-R2, NFR-R3, NFR-R5, NFR-C1
**ARs:** AR-DATA2 (freshness lifecycle), AR-METR1 (heartbeat_log writes), ADR-015 (transformation layer + snapshot path)

---

### Epic 6: "Ask the Map" — NL Bot in Discord & Telegram *(parallel with Epic 3; non-blocker)*
Arjun types a natural-language question in Discord. The bot defers, translates NL→SPARQL via OpenRouter/Sonnet, validates against the IoP ontology, queries Oxigraph, returns results with source space links and SPARQL transparency. Graceful failure logs ontology gap triples. Discord first; Telegram via built-in adapter; Mattermost post-pilot.

**FRs:** FR35, FR35b, FR37–FR42
**NFRs:** NFR-L1–L4, NFR-S5, NFR-P4, NFR-I3
**ARs:** AR-AGT3–5, AR-DATA5
**UX-DRs:** UX-DR12

---

### Epic 7: 🟢 "Open Now" Presence Layer *(parked indefinitely 2026-05-06 — heartbeat + SpaceAPI `state.open` cover it)*
Originally a webhook-driven presence layer. As of Story 3.2, the heartbeat polls every 10 min and honors SpaceAPI `state.open` as a lifecycle-resetting signal — coordinators with automated endpoints stay `confirmed` indefinitely without any push channel. Section retained as a design trail; do not create stories without fresh justification.

**FRs:** FR3 (🟢 state)
**ARs:** AR-DATA3 (ADR-007 presence graph — activate from slot)

---

**Testing discipline (baked into all Epic 2–4 ACs):**
- RFF mockup dataset = dev/test sandbox for onboarding flow (safe to flip, break, reset)
- VOW real data = read-only, no onboarding tests against it
- Openfab Brussels (Nicolas) = live acceptance test — real URL, real pin flip, embed on openfab.be validates end-to-end delay

**Demo critical path:** Epic 1 → Epic 0 → Epic 2 → Epic 3 → Epic 4 (+ Epic 5 as rolling polish)
**Parallel non-blocking:** Epic 4b (magic link) // Epic 6 (NL bot) — neither blocks demo
**Reserved post-demo side quest:** Epic 7 (🟢 open-now presence layer)

**Key dependency:** Epic 4 (operator dashboard) requires Epic 3's raw snapshot files (`/data/snapshots/{id}/latest.json`) and status graph (`<urn:mak:status>`). Story sequencing within Epic 3 must deliver these before Epic 4 stories begin.

---

## Epic 0: Pilot Seed Data Pipeline

The map is populated with credible real spaces from the pilot ecosystem. VOW's 500+ German open workshops (already scraped in `vow_workshops.json`) are normalized to the MOM schema, geocoded, and loaded as ⚪ seeded pins. A separate RFF mockup dataset provides health-state variety (stale, broken, aging) for the admin dashboard demo without touching real onboarding data. Belgium is intentionally left blank — that region demonstrates organic onboarding (Epic 2).

**Depends on:** Story 1.3 (Oxigraph running) + Story 1.4 (MOM ontology loaded)

---

### Story 0.1: Normalize VOW Scrape to MOM-Compliant JSON-LD + Geocode

As a maker or coordinator,
I want the map to show real German open workshop spaces (from the VOW / offene-werkstaetten.org network) as ⚪ seeded pins,
So that the pilot map has credible density in Germany and coordinators can recognise their own space rather than seeing synthetic placeholder data.

**Acceptance Criteria:**

**Given** `web/data/vow_workshops.json` contains 500+ entries with fields: `name`, `address`, `website`, `profileUrl`, `categories` (German-language strings)
**When** `scripts/normalize_vow.py` is run
**Then** it produces `web/data/moms_seed.json` as a JSON-LD array where each entry maps to:
- `@type: mom:MakerSpace`
- `schema:name` ← `name`
- `schema:address` ← parsed from `address` string (street, postcode, city, country: DE)
- `schema:geo` ← geocoded lat/lng (using Nominatim or equivalent, with polite rate-limiting: 1 req/s, User-Agent header set)
- `schema:url` ← `website`
- `mom:profileUrl` ← `profileUrl` (provenance back to VOW directory)
- `schema:knowsAbout` ← categories translated via `scripts/category_map.yaml` (e.g. `Holz` → `wood`, `Elektronik` → `electronics`, `3D-Druck` → `3d-printing`)
- `mom:source: mak:scraped-vow`
- `mom:freshnessStatus: mak:seeded`
**And** `scripts/category_map.yaml` exists mapping all unique German category strings in the source to canonical English tags; unmapped categories are logged as warnings and included verbatim (never silently dropped)
**And** entries that fail geocoding (address not found, Nominatim returns no result) are written to `web/data/moms_seed_geocode_failures.json` for manual review — not silently dropped from the output
**And** the script is idempotent: re-running it overwrites `moms_seed.json` cleanly

---

### Story 0.2: Generate RFF Mockup Dataset for Health-Layer Demo

As a network admin viewing the dashboard demo,
I want the admin dashboard to show a realistic spread of endpoint health states (confirmed, stale, broken, aging) attributed to the RFF France network,
So that the demo communicates the fleet-health value proposition without polluting the real VOW onboarding data with synthetic entries.

**Acceptance Criteria:**

**Given** the MOM ontology schema (Story 1.4) defines status lifecycle states
**When** `scripts/generate_rff_mockup.py` is run
**Then** it produces `web/data/rff_mockup.json` containing ~20–30 synthetic French maker spaces with:
- Realistic French names, cities, and addresses (Paris, Lyon, Marseille, Bordeaux, Toulouse spread)
- A deliberate mix of health states: ~10 confirmed (🔵), ~8 seeded (⚪), ~5 stale (dashed), ~4 broken (🔴), ~2 aging
- Plausible `last_fetched` timestamps that explain the health states (stale = 45 days ago, broken = 404, aging = 35 days no claim)
- `mom:source: mak:mock-rff` on every entry (explicit provenance flag)
- Named graph target: `<urn:mak:mock/rff-health>` (isolated from real data pool)
**And** the script includes a comment block: `# DEMO ONLY — drop this graph before production: docker exec oxigraph sparql --update "DROP GRAPH <urn:mak:mock/rff-health>"`
**And** the admin dashboard demo-toggle (Epic 4, Story 4.x) can include/exclude this graph via a SPARQL `FROM NAMED` clause

---

### Story 0.3: Seed Import — Load Both Datasets into Oxigraph

As a developer running the demo environment,
I want a single command that loads both the VOW real seed and the RFF mockup dataset into Oxigraph,
So that the map shows ⚪ pins for 500+ German spaces and the admin dashboard shows a realistic health spread for France — with both datasets clearly separated by provenance.

**Acceptance Criteria:**

**Given** Oxigraph is running (Story 1.3), ontologies are loaded (Story 1.4), and both `moms_seed.json` + `rff_mockup.json` exist
**When** `python scripts/seed_import.py` is run
**Then** it converts each entry in `moms_seed.json` to RDF triples and inserts them into `<urn:mak:space/{id}>` named graphs with `mom:source mak:scraped-vow` and `mom:freshnessStatus mak:seeded`
**And** it converts each entry in `rff_mockup.json` to RDF triples and inserts them into `<urn:mak:mock/rff-health>` named graph with `mom:source mak:mock-rff` and the appropriate health state triples
**And** the status scheduler job (`<urn:mak:status>`) is updated with materialized status triples for all imported spaces
**And** after import, running `python scripts/materialize_geojson.py` (Story 1.5) produces a `spaces.geojson` that includes all VOW spaces as ⚪ seeded pins visible on the map
**And** the script logs a summary on completion: `{n} VOW spaces loaded`, `{n} RFF mockup spaces loaded`, `{n} geocode failures skipped`
**And** the script is idempotent: re-running it checks `ASK { GRAPH <urn:mak:space/{id}> { ?s ?p ?o } }` before each insert and skips already-loaded spaces

---

## Epic 1: Federated Backend Foundation

The map reads pins from Oxigraph (not bundled JSON); the Docker stack runs on the VPS with proper security routing; MOM ontology v0 exists and both ontologies are loaded. Each story stands alone and enables the next.

---

### Story 1.1: Integration Dependency Spike

As a developer,
I want a single `/ping` slash command that chains Discord → OpenRouter LLM call → Oxigraph health check and logs each leg's result,
So that all three external dependencies are proven reachable before any feature work begins — and failures are surfaced early with clear diagnostics.

**Acceptance Criteria:**

**Given** the Openfab Brussels Discord server exists and the developer has admin rights on it
**When** setting up the Discord application (one-time prerequisite before any code runs)
**Then** the developer follows these steps in the Discord Developer Portal (discord.com/developers):
1. Create a new Application named `maps-of-making-bot`
2. Under Bot tab: enable bot, copy the bot token into `.env` as `DISCORD_BOT_TOKEN`
3. Under OAuth2 → URL Generator: select scopes `bot` + `applications.commands`; select permission `Send Messages` + `Use Slash Commands`; copy the generated URL and open it to invite the bot to the Openfab server
4. Under Bot tab: disable "Public Bot" (only Openfab server should use it)

**Given** the three files `harness/main.py`, `harness/llm_client.py`, `harness/sparql_client.py` exist and `DISCORD_BOT_TOKEN`, `OPENROUTER_API_KEY`, and `OXIGRAPH_ENDPOINT` are set in `.env`
**When** a developer runs `/ping` in the configured Openfab Discord channel
**Then** the bot defers (`thinking=True`), calls OpenRouter (one completion, any model), queries Oxigraph health endpoint (`ASK { ?s ?p ?o }`)
**And** responds with a structured message showing each leg: ✓/✗ Discord auth, ✓/✗ OpenRouter (model used, latency ms), ✓/✗ Oxigraph (latency ms)
**And** if any leg fails, the error is logged via `structlog` with `session_id` bound and a plain-language failure message shown in Discord (no stack trace to the user)
**And** slash commands are synced via `tree.sync()` in `setup_hook` (not on every message)
**And** all three files follow AR-CONV1 naming (`snake_case`, `verb_noun()`) and AR-CONV2 logging (`structlog`, event `noun.verb_past`)
**And** the spike is verified working before any Epic 1 story beyond 1.2 is started

---

### Story 1.2: Scope Basemap to Europe + Update Loader Copy

As a maker browsing the map,
I want the map to restrict panning to the Europe region and show accurate loader copy,
So that the initial tile batch is minimal (no tiles loading for unreachable world regions) and the loader text reflects the actual data being loaded rather than hardcoded synthetic copy.

**Acceptance Criteria:**

**Given** the map SPA is loading
**When** MapLibre initialises
**Then** `maxBounds` is set to approximately `[[-25, 34], [45, 72]]` (Atlantic west coast to Ural, North Africa to Scandinavia), preventing tile requests outside Europe
**And** the loader copy no longer reads "loading 40 synthetic spaces · FR + DE" — it reads a neutral variant (e.g. "unrolling the map…") that does not hardcode a space count or data description
**And** the map still centres on `[4.8, 49.5]` zoom 4.3 (FR/DE/BE pilot midpoint)
**And** the `<div class="loader">` second line is either removed or replaced with a version driven by actual data count once available
**And** the reduced-motion media query and 1500ms fallback dismissal remain untouched

---

### Story 1.3: Docker Compose Stack + Nginx Security Routing

As a network admin and developer,
I want the full Phase 2 service topology running on the VPS (Oxigraph, Nanobot agent, link-handler, nginx) with public SPARQL read-only and update blocked,
So that the backend is reachable, secure, and ready for ontology loading and ingestion wiring in subsequent stories.

**Acceptance Criteria:**

**Given** the VPS has Docker + Docker Compose installed and `.env` is populated from `.env.example`
**When** `docker compose up -d` is run from the project root
**Then** all four services start without error: `oxigraph`, `mak-agent` (Nanobot), `mak-link-handler`, `nginx`
**And** `docker network ls` shows a `maps_of_making_internal` network; no host-level port conflicts with other projects (all services use `expose`, not `ports`, except nginx)
**And** `GET /sparql/query` with a valid SPARQL SELECT returns 200 from the public internet
**And** `POST /sparql/update` returns 403 or connection refused from outside the Docker network (nginx deny rule verified)
**And** `/claim/test` routes to `mak-link-handler:8000/claim/test` (nginx proxy rule present, 404 or 422 from FastAPI is acceptable — route exists)
**And** the presence webhook nginx route is present but commented out (Epic 7 slot reserved)
**And** `admin.*` subdomain returns 401 without credentials and 200 with the shared password from `.env` (basic auth configured)
**And** `.env.example` is committed with all required variable names and placeholder values; `.env` is gitignored

---

### Story 1.4: Author MOM Ontology v0 + Load MOM & IoP into Oxigraph

As a developer and SPARQL client,
I want a versioned MOM ontology v0 file and both MOM + IoP ontologies loaded as named graphs in Oxigraph,
So that all downstream heartbeat, ingestion, and query stories can use stable semantic predicates without redefining vocabulary ad-hoc.

**Acceptance Criteria:**

**Given** Oxigraph is running (Story 1.3 done)
**When** `scripts/load_ontology.sh` is run
**Then** `ontology/mom.ttl` exists and declares at minimum:
- Namespace `mom:` at `https://w3id.org/maps-of-making/`
- Classes: `mom:MakerSpace`, `mom:NetworkMembership`, `mom:SpaceType`
- Properties: `mom:freshnessStatus`, `mom:healthStatus`, `mom:visibility`, `mom:operationalState`, `mom:lastChecked`, `mom:consecutiveFailures`, `mom:source`, `mom:pendingNotification`, `mom:dispatched`, `mom:retryCount`
- A `mom:OntologyGap` class for query-failure logging (FR41)
- A `@version` annotation (e.g. `owl:versionInfo "0.1.0-poc"`)
**And** `ontology/context/space.jsonld` exists providing the `@context` for coordinator JSON-LD endpoint files, mapping `mom:` and `schema:` prefixes
**And** `scripts/load_ontology.sh` is idempotent — it runs an `ASK` query before each POST and skips if already loaded
**And** after running the script, `ASK { GRAPH <urn:mak:ontology/mom> { ?s ?p ?o } }` returns `true`
**And** after running the script, `ASK { GRAPH <urn:mak:ontology/iop> { ?s ?p ?o } }` returns `true`
**And** ontology evolution (additional classes, alignment with full IoP, w3id.org registration) is explicitly noted as deferred to pilot in a `## Roadmap` comment block in `mom.ttl`
**And** `scripts/load_ontology.sh` is called in the Docker Compose startup sequence (or documented as a manual post-deploy step) so a fresh VPS install is ready after one command

---

### Story 1.5: Map Reads from Oxigraph GeoJSON Materialization

As a maker browsing the map,
I want the map to show spaces fetched from the Oxigraph-backed federated dataset (not `data/moms_seed.json`),
So that what I see on the map reflects the live system state — and the switch from bundled JSON to backend-served data is transparent to me (same load time, same pin rendering).

**Acceptance Criteria:**

**Data flow for this story:**
```
Ingestion (Epic 2/3): coordinator URL → fetch JSON-LD → parse → Oxigraph (write path)
Materialization (this story): Oxigraph → SPARQL SELECT → spaces.geojson (static file) → nginx → SPA fetch (read path)
```
The SPA never queries SPARQL directly. It fetches one pre-baked static GeoJSON file served by nginx. `materialize_geojson.py` re-bakes this file on demand; the scheduler (Epic 3) will call it after each ingest cycle. For demo: run manually once after seeding.

**Given** Oxigraph is running (Story 1.3) with ontologies loaded (Story 1.4) and at least one space triple exists in `<urn:mak:space/{id}>`
**When** `python scripts/materialize_geojson.py` is run
**Then** it executes a SPARQL SELECT against `<urn:mak:status>` and `<urn:mak:space/*>` named graphs and writes the result to `web/data/spaces.geojson` as a valid GeoJSON `FeatureCollection`
**And** each feature contains: `geometry.coordinates [lng, lat]`, `properties.name`, `properties.status` (seeded / confirmed / stale / broken), `properties.uri`, `properties.last_fetched`
**And** the query includes a `LEFT JOIN` against `<urn:mak:presence>` returning `null` for all spaces now (Epic 7 presence slot wired but inactive)
**And** nginx serves `web/data/spaces.geojson` as a static file

**Given** `spaces.geojson` is served at `/data/spaces.geojson`
**When** the map SPA boots
**Then** `app.js` fetches `/data/spaces.geojson` instead of `data/moms_seed.json` — same fetch call, different source file
**And** pin rendering, filter chips, and search work identically to phase-1 behaviour
**And** if the fetch returns non-200, the map degrades gracefully: paper-overlay background, zero pins rendered, inline banner "Map data temporarily unavailable — try refreshing" (no raw error, no blank screen)

---

## Epic 2: Coordinator URL Onboarding — ⚪→🔵 Flip

A coordinator pastes their JSON-LD endpoint URL, sees live validation feedback (reachable, schema-valid, geocoded, PII-free), submits, watches their pin flip ⚪→🔵, and receives a reciprocal embed snippet — all within a single flow, no login required.

**Testing strategy:** All development and demo testing uses RFF mockup space entries (safe to reset). VOW data is read-only and never used for onboarding tests. Openfab Brussels (Nicolas) is the live acceptance test for the full flow end-to-end, including embedding the map on openfab.be to validate the ⚪→🔵 feedback delay.

**Architecture decisions locked for Epic 2 [2026-04-25 retro]:**
- **Registration path: web drawer only.** The "Add your URL" drawer is already present in the phase-1 UI (not wired). Epic 2 wires it. Alternative registration paths (GitHub PR to ontology repo, Discord `/add` command, CI/CD cron trigger) are backlogged pending traction signal.
- **Coordinator JSON hosting:** Epic 2 accepts any valid https URL. Documentation of hosting options (GitHub Gist, Google Drive, Nextcloud, institutional IT) and a JSON generator tool are workshop content, not Epic 2 scope. Backlogged.
- **Final acceptance test:** Nicolas submits Openfab Brussels as a live coordinator. This is the Epic 2 done gate — not just RFF mockup validation.

**Story restructure [2026-04-26]:** Original stories 2.1–2.4 merged into a single vertical slice (2.1); original 2.5 renumbered to 2.2; 2.6 kept. Rationale: the coordinator gesture is atomic from UX perspective; embed was already implemented in phase-1; PII hard-rejection deferred to a future "hardening PII & GDPR compliance" story.

---

### Story 2.1: Coordinator URL Onboarding — E2E (submit → validate → ingest → flip → embed)

*Merges original stories 2.1 + 2.2 + 2.3 + 2.4. Implementation file: `_bmad-output/implementation-artifacts/2-1-coordinator-url-onboarding-e2e.md`*

As a space coordinator,
I want to paste my JSON-LD endpoint URL, see it validated live, and watch my pin flip from ⚪ to 🔵 with a ready-to-copy embed snippet —
so that I can register my space on the map without creating an account or contacting anyone.

**Acceptance Criteria (summary — see implementation story for full BDD spec):**

**Given** the "Add your URL" drawer is open
**When** a coordinator pastes a URL and clicks "Fetch & validate"
**Then** `POST /api/validate-url` is called and a live checklist renders: reachable ✓, JSON-LD valid ✓, name found ✓, coordinates found ✓, (soft PII warning if personal fields present — non-blocking)

**And** on all blocking checks passing, a "Confirm & register your space →" button appears

**And** clicking confirm calls `POST /api/register-url`, which: re-validates, writes SPARQL UPDATE to Oxigraph (`mom:operationalState "confirmed"`, `mom:endpointUrl`, `mom:lastFetched`), writes a snapshot named graph `<urn:mak:space/{slug}/{date}>`, rematerializes `web/data/spaces.geojson` inline

**And** the drawer shows a confirmation screen: space name, "Embed this space →" (calls existing `embedSpace()`), "View on map →" (calls `selectSpace()`)

**And** the map markers re-render to show the 🔵 pin

**And** a `scripts/seed_transition.py` admin utility (read-only by default, `--mark-done` opt-in) reports which seeded spaces have been confirmed — run manually for demo maintenance, isolated from the ingestion flow

**PII enforcement deferred:** Soft warning only in Epic 2 — fields detected are listed but never block registration and are silently dropped from stored triples. Hard rejection + admin alert is a future "hardening PII & GDPR compliance" story.

---

### Story 2.2: Detail Drawer — Provenance + Ingestion History

*Renumbered from original story 2.5. Implementation file: `_bmad-output/implementation-artifacts/2-2-detail-drawer-provenance-ingestion-history.md`*

As a maker or coordinator,
I want the space detail drawer to show where the data came from, when it was last fetched, and a short history of changes,
So that I can trust whether the information is current — and coordinators can verify their own endpoint is being read correctly.

**Acceptance Criteria (summary — see implementation story for full BDD spec):**

**Given** a maker clicks any pin
**When** the detail drawer opens
**Then** a "Data provenance" section shows: source label (Self-registered / VOW network / RFF network), endpoint URL (truncated, full on hover), last fetched timestamp via `timeAgo()`

**And** for ⚪ seeded spaces: a "Claim this pin" CTA appears — "Are you the coordinator? Add your URL →" (calls `setDrawer('addurl')`)

**And** for 🔴 broken spaces: freshness line replaced by amber error banner with plain-language error category (from `s.error_type`) + last known good date

**And** a "Fetch history" section shows the last 5 snapshots from `GET /api/space/{id}/snapshots` (link_handler endpoint), rendered async — shows "No fetch history yet." on empty or error

**And** `scripts/materialize_geojson.py` SPARQL query is extended to include `mom:endpointUrl`, `mom:lastFetched`, `mom:errorType` fields

**And** all existing detail drawer sections (hero, quick facts, specialties, raw JSON, embed button) are unchanged

**Depends on Story 2.1:** snapshot named graphs must be written by `POST /api/register-url` for history to populate.

---

### Story 2.6: Mobile Responsive Layout

*Added: Epic 1 retrospective 2026-04-25. Updated 2026-04-27 with mobile-first design principle and new ACs. Implementation file: `_bmad-output/implementation-artifacts/2-6-mobile-responsive-layout.md` (authoritative — supersedes this summary).*

**Mobile-first design principle:** Mobile = browsing mode (find a space, go there, share it). Coordinator onboarding, health map, and management features are desktop-only.

As a maker browsing on a phone,
I want the map to fit, be usable, and help me find spaces near me,
So that I can discover open spaces and share them with my group — without needing a desktop.

**Key ACs (see story file for full detail):**
- Topbar collapses to icon-only row (no overflow/wrap) on < 768px
- All drawers open as bottom sheets; detail drawer at ~80–85% height
- "Claim this pin" CTA suppressed on mobile — replaced with desktop whisper text
- "📍 Near me" button: geolocation → flyTo zoom 12, silent on denial
- "⎘ Copy space link" in detail drawer footer (copies `s.website || s.endpoint_url`)
- Zone 3 (raw source JSON) hidden on mobile
- Real-phone validation by Nicolas required before done
- Desktop layout unchanged (≥ 768px)

**Dev Notes:**
- CSS-only approach — no JS framework
- `prefers-reduced-motion` already covers drawers — extend to new mobile transitions
- Existing `@media (max-width: 720px)` is a partial start; this story completes it

---

### Story 2.7: Card Zones + Pydantic Schema Foundation

*Added: 2026-04-27. Addresses data flow incoherence between URL ingestion and card display. Implementation file: `_bmad-output/implementation-artifacts/2-7-card-zones-pydantic-schema-foundation.md` (authoritative).*

As a maker or coordinator viewing a space detail card,
I want to see clearly separated zones — identity, curated data, and raw source — and as a coordinator I want honest feedback about what my endpoint unlocks,
So that I can trust what the map shows me and know exactly what to improve in my data file.

**Data flow:** `URL → fetch → Pydantic validation → Oxigraph (curated fields + raw snapshot) → card (Zone 2 from Oxigraph, Zone 3 from raw snapshot)`

**Key ACs (see story file for full detail):**
- Pydantic `SpaceAPISchema` model classifies endpoints into subsets: `mom:required` → `mom:card` → `spaceapi:compatible`
- Validation response includes `subset`, `unlock_message`, `next_unlock` (progressive fog-of-war incentive)
- Raw endpoint JSON stored as `mom:rawContent` in snapshot graph (50KB cap)
- `GET /api/space/{id}/raw` returns cached snapshot JSON
- Card restructured: Zone 1 (identity/status), Zone 2 (ingested fields only — removes fake Founded/Capacity/Contact), Zone 3 (real source JSON, desktop only)
- `jsonForSpace()` deleted — it was reconstructing fake "endpoint" data from GeoJSON props
- `schema:description` surfaced in Zone 2 (was ingested but never displayed)

**SpaceAPI compatibility reference:** https://github.com/SpaceApi/schema
**Success metric:** One endpoint registers on MoM AND mapall.space without changes.

---

### Story 3.0-A: Space Profile Card — UX Refinement

*Added: 2026-05-04. Post-3.0 UX polish pass: profile naming, freshness signals, contact pictos, logo, share CTA, manual fetch stub, and timing fix. Implementation file: `_bmad-output/implementation-artifacts/3-0-A-space-profile-card-ux-refinement.md` (authoritative).*

As Luca (coordinator) and as a visitor,
I want the space profile to clearly reflect what the endpoint provides, let me share it easily, and signal when it was last updated,
So that the card earns trust without adding friction.

**Key ACs (see story file for full detail):**
- Drawer renamed "Space Profile" (label-only; element ids unchanged)
- Post-registration timing: 8s if unlock guidance present, 2s if none
- Zone 1: logo thumbnail inline with name; "Last updated: {timeAgo}" replaces freshness banner; share picto CTA (desktop only)
- Zone 2: contact channel pictos with click-to-copy; subset nudge ("What your data unlocks") now permanent, field-by-field; embed CTA moved here from below Zone 3
- Zone 3: raw JSON flush (no side padding); "Last fetched: {local datetime}" precise header; manual fetch button rendered disabled (endpoint ships in Story 3.1)
- Fetch history section removed
- GeoJSON surfaces: `logo`, `contact` (JSON string), `last_updated`
- `classify_subset()` updated to identify single lowest-effort next field (not a list)

**Depends on:** Story 2.7 (zones, `/raw` endpoint, Pydantic subsets)
**Deferred to Story 3.1:** `POST /api/heartbeat-space/{id}` endpoint + manual fetch button activation

---

## Epic 4: Operator Observability Dashboard

Nicolas (MOM infrastructure operator) opens `/admin`, reads system health at a glance (Oxigraph status, ingestion process, reachable count), scans the space registry table for failures, and drills into any space for a raw/ingested/displayed inspection panel. This is pipeline observability — the tool that proves the system isn't lying. Luca (VOW) uses the public health map toggle; no admin access needed.

**Auth:** shared password from `.env` via nginx basic auth (FR43, NFR-S1). No login UI to build.
**Depends on:** Epic 3 raw snapshots at `/data/snapshots/{id}/latest.json` and `<urn:mak:status>` graph.

---

### Story 4.1: System Health Strip — Three Status Pills

As the MOM operator,
I want to open `/admin` and immediately see whether Oxigraph is up, the ingestion process is running, and how many spaces are reachable,
So that I can read the system state in under 5 seconds and know whether anything needs attention.

**Acceptance Criteria:**

**Given** the admin subdomain is open and the shared password has been entered
**When** `admin.html` loads
**Then** a FastAPI endpoint `GET /admin/api/status` is called, assembling:
  - Oxigraph health: `ASK {}` query via `sparql_client.run_select()` → LIVE (green) / DOWN (red)
  - Ingestion heartbeat: last-modified timestamp on a heartbeat marker file written by the scheduler after each cycle → RUNNING (green) / IDLE Nh (amber, N = hours since last run) / STALLED (red, > configured threshold)
  - Spaces reachable: count of spaces with `mak:probeResult "ok"` vs total in `<urn:mak:status>` → "603 / 606" (green if ratio above threshold, amber otherwise)
**And** three status pills are rendered at the top of the page: `● Oxigraph LIVE · ● Ingestion IDLE (4h) · ● Spaces reachable 603/606`
**And** a "Last checked: N minutes ago" timestamp shows when `/admin/api/status` last ran (auto-refreshes every 60s without full page reload)
**And** if Oxigraph is DOWN, the pill is red and all other data on the page shows "— unavailable" rather than stale/incorrect data
**And** all data is operational metrics only — no raw endpoint payloads, no coordinator identifiers beyond what's public on the map (NFR-S6)

---

### Story 4.2: Space Registry Table

As the MOM operator,
I want a table of all registered spaces with their endpoint URL, last probe timestamp, and probe result,
So that I can scan for failures at a glance and click into any space that needs investigation.

**Acceptance Criteria:**

**Given** the system health strip is loaded (Story 4.1) and `<urn:mak:status>` contains space probe records
**When** the admin page renders below the health strip
**Then** a SPARQL SELECT over `<urn:mak:status>` builds a table with columns: space name, endpoint URL, last probe timestamp, probe result (HTTP status or error category)
**And** rows with non-200 probe results have a muted red background — the only colour used to signal failure
**And** the table is sortable by last probe timestamp (default: most recently failed first) and by probe result
**And** a text filter input narrows rows by space name or endpoint URL substring (client-side, no re-query)
**And** each row is clickable, opening the inspection panel (Story 4.3)
**And** a "Re-probe now" button per row triggers an immediate `tasks/heartbeat.py` fetch for that space, shows a spinner, and refreshes the row result on completion (FR31)
**And** the re-probe action is written to the operator action log: `{ action: "reprobe_triggered", space_uri, timestamp }` (FR33b)

---

### Story 4.3: Per-Space Inspection Panel — Raw / Ingested / Displayed

As the MOM operator,
I want to click a space and see three columns side-by-side: the raw JSON from the last fetch, the ingested triples from Oxigraph, and what actually renders on the public card,
So that I can identify exactly where a discrepancy enters the pipeline without grepping logs.

**Acceptance Criteria:**

**Given** the space registry table is showing (Story 4.2)
**When** the operator clicks a space row
**Then** an inspection panel opens (right drawer or accordion below the row) with three columns:

**Column 1 — RAW FETCH:**
- Reads `/data/snapshots/{space_id}/latest.json` from disk (written by Epic 3 pipeline)
- Displays raw JSON in a monospaced block with fetch timestamp and endpoint URL
- Shows fetch status: "responded" or "unreachable (last known {timestamp})"
- This is the Zone 3 source of truth — verbatim, unmodified

**Column 2 — INGESTED:**
- Runs `SPARQL DESCRIBE <urn:mak:space/{id}>` via `/sparql/query`
- Displays the result as a readable key→value list (not raw Turtle): predicate label → value
- Shows triple count and last-ingested timestamp

**Column 3 — CARD DISPLAY:**
- Runs a SELECT query fetching the exact fields used by `app.js` to render a space card
- Displays as a mini card preview: name, address, status, hours, specialties
- Any field absent from the card but present in Column 1 is flagged with ⚠ "not displayed"

**And** mismatches between Column 1 and Column 2 (fields present in raw JSON but absent from ingested triples) are flagged with ⚠ inline — these signal transformation gaps in `tasks/ingest.py`
**And** mismatches between Column 2 and Column 3 (triples ingested but not rendered) are flagged with ⚠ inline — these signal display mapping gaps in `app.js`
**And** the panel is the primary diagnostic tool — no raw log access, no SSH required to diagnose a pipeline discrepancy

---

### Story 4.4: Export Registry + Operator Action Log

As the MOM operator,
I want to export the space registry and review a log of all operator actions taken through the dashboard,
So that I can produce a dataset snapshot and audit what was done manually.

**Acceptance Criteria:**

**Given** the admin dashboard is loaded
**When** the operator clicks "Export registry"
**Then** a SPARQL SELECT queries all spaces and returns: space name, URI, endpoint URL, status, last probe timestamp, probe result — exported as CSV and JSON download options (FR33)
**And** the export excludes: raw endpoint payloads, coordinator contact details not already public on the map (NFR-S6)

**Given** the operator action log section is open
**When** the operator views it
**Then** it displays a reverse-chronological list: timestamp, action type (reprobe_triggered / export_downloaded), space URI or "all", result (FR33b)
**And** the log is append-only — no delete, no edit
**And** the export action itself is recorded: `{ action: "export_downloaded", format, space_count, timestamp }`

---

## Epic 4b: Magic Link Coordinator Recovery *(parallel non-blocking)*

When a space goes stale, the coordinator receives a templated email with a magic link — YES refreshes their pin, NO gracefully archives the space with GDPR closure. Parallel to Epic 4; non-demo-blocking. Depends on Epic 3's notification queue and status graph. Stories originally numbered 3.3–3.4.

**Auth:** none — magic links are publicly accessible by design (token-secured, single-use).
**Depends on:** Epic 3 (notification queue in `<urn:mak:notifications>`, status transitions from Story 3.2).

---

### Story 4b.1: Magic Link Generation + Link-Handler Validation

*(Previously Story 3.3 — content unchanged, re-sequenced to parallel epic)*

As a coordinator receiving a nudge email,
I want a single-click link that either confirms my space is still active or gracefully closes it,
So that recovery requires no login, no form, and no context-switching — just one honest click.

**Acceptance Criteria:**

**Given** `tasks/magic_link.py` exists and `LINK_SECRET` is set in `.env`
**When** a magic link is generated for a space
**Then** the token is `base64url(HMAC-SHA256(uuid + expiry + space_uri, LINK_SECRET))` — stored as hash only in Oxigraph, never in plaintext (AR-MLNK2)
**And** the token has a 72h TTL written as `mak:expiresAt` triple
**And** `GET /claim/{token}?action=yes` on `mak-link-handler`:
- Validates token exists in Oxigraph (`ASK` query)
- Validates token not expired
- Validates token not already consumed
- On valid: writes `mak:consumed true`, resets timer, sets status `mak:confirmed`, returns a confirmation HTML page ("Your space is live again 🔵")
**And** `GET /claim/{token}?action=no`:
- Same validation steps
- On valid: marks space `mak:closed`, removes PII contact fields, writes `mak:closedAt`, returns a graceful closure page
**And** a second click on any consumed token returns: "This link has already been used." — no silent failure
**And** an expired token returns: "This link expired {N} hours ago — contact your network admin for a new one."

---

### Story 4b.2: Coordinator Email Notification with Pre-filled Recovery Link

*(Previously Story 3.4 — content unchanged, re-sequenced to parallel epic)*

As a coordinator whose space endpoint has gone stale,
I want to receive an email that tells me exactly what's wrong and gives me a one-click path to fix it,
So that I can recover my pin without needing to remember what a JSON endpoint is or where to go.

**Acceptance Criteria:**

**Given** a space transitions to `mak:aging` or `mak:broken` (Story 3.2) and has a space-level contact address in Oxigraph
**When** the dispatch worker reads `<urn:mak:notifications>` queue
**Then** it generates a magic link token (Story 4b.1), fills the notification template, and dispatches an email containing:
- Plain-language subject: "Your space [Name] on Maps of Making needs attention"
- Error summary: what happened and when (last successful fetch date, error category)
- YES link: "My space is still active — refresh my pin" → `/claim/{token}?action=yes`
- NO link: "My space has closed — remove it from the map" → `/claim/{token}?action=no`
- Link expiry notice: "These links expire in 72 hours"
- Footer: link to the space's public map pin and the network admin contact
**And** delivery failure retries 3× with progressive backoff (1h, 6h, 24h); after 3 failures, a `mak:escalated` triple is written (AR-MLNK3)
**And** if the space has no contact address, the notification is skipped and an admin alert is written instead
**And** the dispatch action is written to the operator action log: `{ action: "notification_dispatched", space_uri, reason, timestamp }`
**And** the `mak:dispatched` triple timestamp prevents re-dispatch within 24h for the same space

---

## Epic 5: Map Polish, Progressive Disclosure & Accessibility

The map now runs on real federated data. This epic validates phase-1 UI hypotheses against actual usage, adds provenance and failure states throughout, wires the accessible list view, and gets axe-core into CI. Each story is independently shippable — polish is continuous, not a gate.

---

### Story 5.1: Filters + Search Wired to Real Federated Data

As a maker browsing the map,
I want filters and search to work against real space data from Oxigraph,
So that "electronics workshops in Hamburg" returns actual confirmed spaces, not synthetic fixtures.

**Acceptance Criteria:**

**Given** `spaces.geojson` is populated from Oxigraph (Story 1.5) with real VOW + Openfab spaces
**When** the filters drawer is opened
**Then** filter chip counts reflect the actual dataset: network chips show real network tags (`mak:scraped-vow`, confirmed, etc.), country chips show DE / BE and any others present, status chips show real counts per state
**And** specialty/category chips are built from the canonical English tags in `spaces.geojson` (mapped via `category_map.yaml` in Epic 0) — not hardcoded in JS
**And** selecting a filter updates the map pins live with no reload, and the results list in the filter drawer updates count and entries (FR7, FR9)
**And** text search across `schema:name`, city, and `schema:knowsAbout` tags is case-insensitive and accent-tolerant (e.g. "electronique" matches "électronique")
**And** when filters produce zero results, the empty state shows: "No spaces match — try widening your filters" with a "Reset filters" shortcut (FR10, UX-DR11)
**And** the shareable URL encodes active filters + map bounds so a filtered view can be bookmarked or shared (FR8)
**And** filter state persists across drawer close/reopen within the same session (FR9)

---

### Story 5.2: Stale + Broken State UI — Banners, Provenance, Empty States

As a maker clicking a stale or broken pin,
I want to understand clearly why the data may be outdated and what it means,
So that I can make an informed decision about whether to contact the space — and I don't mistake old data for live data.

**Acceptance Criteria:**

**Given** a space has status `stale` (dashed pin) and a maker clicks it
**When** the detail drawer opens
**Then** an amber quiet banner appears at the top of the drawer: "Last confirmed {N} days ago — details may be outdated" (UX-DR3)
**And** the provenance section (Story 2.2) shows the last successful fetch date and the error type from the most recent failed attempt in plain language
**And** a "contact network admin" CTA is shown below the error — links to the network's public contact (never a personal email)

**Given** a space has status `broken` (🔴 pin) and a maker clicks it
**When** the detail drawer opens
**Then** the error category is shown in plain language: "This space's data feed returned 404 (page not found)", "Connection timed out", "Data format error" — never a raw HTTP response (UX-DR10)
**And** the last known good snapshot date is shown with a "historical record" label, clearly distinguished from live data
**And** the drawer still renders all last-known fields (name, address, hours) with a "As of {date}" prefix on each section

**Given** the map has loaded but `spaces.geojson` returns an empty FeatureCollection
**When** a maker views the map
**Then** an inline banner appears: "No spaces loaded — the map data may be temporarily unavailable. Try refreshing." — never a blank map with no explanation (UX-DR13)

---

### Story 5.3: Embed Polish — "Last Confirmed" Caption + Reciprocal Visibility

As a coordinator who has embedded the map on their website,
I want the embedded map to show a visible "last confirmed" date on my space's pin,
So that visitors to my site can trust the data is fresh — and I'm motivated to keep my endpoint alive because a stale embed visibly degrades my own web presence.

**Acceptance Criteria:**

**Given** the map is loaded in embed mode (`?embed=1` or `window.self !== window.top`)
**When** a space is pre-selected via `?space={uri}`
**Then** the embed renders with the space's detail visible and a caption below the map: "Last confirmed {date} · Source: Maps of Making ↗" where the link opens the full map in a new tab (FR17, UX-DR26)
**And** if the space status is stale, the caption reads: "Last confirmed {N} days ago — data may be outdated" in amber — the degradation is visible to visitors on the coordinator's own site (reciprocal visibility incentive)
**And** the web component `<maps-of-making center="{lat},{lng}" zoom="13" space="{uri}">` produces the same output as the iframe embed with no framework dependency (FR16, NFR-I4)
**And** the embed renders correctly in all browser matrix targets (Chrome, Firefox, Safari 16+, mobile Chrome/Safari) without requiring the coordinator to tweak anything

---

### Story 5.4: Accessible List View + axe-core in CI

As a keyboard or screen reader user,
I want to browse filtered spaces as a structured list without relying on the map canvas,
So that the map's content is accessible to me regardless of how I navigate (NFR-A5).

**Acceptance Criteria:**

**Given** the filters drawer is open
**When** a user activates "View as list" (a link/button at the top of the results list in the filter drawer)
**Then** a semantic `<ul>` list renders below the filter chips showing all currently filtered spaces, each as a `<li>` with: space name (`<h3>`), city + country, status label, specialty tags, and a "View detail" button that opens the detail drawer
**And** the list is keyboard-navigable: tab moves between items, Enter on "View detail" opens the drawer, Escape closes it and returns focus to the list
**And** screen readers announce: the list item count when the list renders ("23 spaces matching your filters"), status changes when filters update (`aria-live="polite"` on result count), drawer open/close
**And** pin state changes (e.g. after a re-fetch in the admin that updates `spaces.geojson`) are announced via `aria-live` on the results count
**And** color is never the sole indicator of pin state: stale uses dashed stroke pattern, broken uses × glyph, confirmed uses solid fill — all present in phase-1 CSS and validated in list view too (NFR-A4)

**Given** the project has a CI pipeline (GitHub Actions, manual deploy for PoC)
**When** the axe-core check runs
**Then** `axe-core` is installed and a test script runs `axe` against the map SPA and admin dashboard HTML fixtures
**And** zero violations at WCAG 2.1 AA level are required for CI to pass (NFR-A1)
**And** the axe check is documented as a manual step for PoC (pre-GitHub Actions) with instructions to run locally before each demo

---

### Story 5.5: Phase-1 UI Hypothesis Validation + Tweaks Panel Decision

As a developer and product owner,
I want to review each phase-1 UI element against pilot usage and make an explicit keep/adjust/prune decision,
So that the demo map carries only UI that earns its cognitive load — nothing is present by default inertia.

**Acceptance Criteria:**

**Given** the phase-1 prototype has the following UI hypotheses: Tweaks panel (map style, pin density, pulse), "Ask the map" bot FAB (currently "soon"), Preset & embed drawer, "Add your URL" drawer (now wired in Epic 2)
**When** this story is executed (after at least one real usage session with RFF/VOW/Openfab data)
**Then** each element is reviewed against the principle "does this reduce cognitive load or add it?" and a decision is recorded:
- **Tweaks panel:** demoted from end-user feature to developer/designer tool — hidden behind a keyboard shortcut (e.g. `Shift+T`) rather than a topbar button; keeps functionality, removes topbar clutter (UX-DR6)
- **"Ask the map" bot FAB:** transitions from "soon" teaser to "active" only when Epic 6 is wired; until then remains but label updated to "Coming in Phase 2" with no interactivity change — explicit, honest (UX-DR7)
- **Preset & embed drawer:** kept but moved to a secondary affordance (share icon in detail drawer, not a topbar button) — accessed from context, not always-visible
- **"Add your URL" button:** kept in topbar (primary CTA for coordinator onboarding)
**And** each decision is implemented as a code change and the topbar renders with reduced button count for the demo
**And** the reduced-motion media query and keyboard focus styles are regression-tested after any topbar changes (NFR-A2)

---

## Epic 3: Ingestion Pipeline + Endpoint Health + Stale Detection

*(Prerequisite for Epic 4 — must ship before operator dashboard stories begin)*

The full ingestion pipeline becomes real: SpaceAPI JSON fetched from space endpoints, raw snapshot written to disk before any transformation, then transformed to MOM JSON-LD via the explicit ontology mapping layer (ADR-015), and ingested into Oxigraph. Heartbeat scheduler runs the full 6h cycle producing the status graph Epic 4 reads from. Magic-link coordinator recovery is a separate parallel epic (4b).

---

### Story 3.0: Ingestion Transformation Layer — SpaceAPI JSON → MOM JSON-LD

As the MOM pipeline,
I want an explicit transformation step that maps SpaceAPI JSON fields to MOM JSON-LD before anything is written to Oxigraph,
So that the boundary between "what the space published" and "what we store" is a named, auditable step — and the raw source is preserved on disk as a trust receipt.

**Acceptance Criteria:**

**Given** a registered endpoint URL exists in Oxigraph with `mak:confirmed` or `mak:seeded` status
**When** `tasks/heartbeat.py` fetches the endpoint
**Then** the raw JSON response is written to `/data/snapshots/{space_id}/latest.json` immediately on receipt, before any parsing or transformation (this is the Zone 3 source and Epic 4 inspection panel source)
**And** a fetch timestamp is written alongside: `/data/snapshots/{space_id}/meta.json` with `{ fetched_at, http_status, etag, endpoint_url }`
**And** the payload is normalized before comparison: ephemeral fields (e.g. `lastchange` unix timestamps that tick every request) are stripped, arrays are sorted — this prevents false-positive "changed" detections
**And** if the normalized payload matches the stored snapshot hash: only the `fetched_at` timestamp is updated; Oxigraph is NOT touched; outcome logged as `"no_change"`
**And** if the normalized payload differs: `tasks/ingest.py` is called with the raw JSON

**Given** `tasks/ingest.py` is called with raw SpaceAPI JSON
**When** the transformation runs
**Then** each SpaceAPI field is mapped to its MOM JSON-LD equivalent using the explicit field mapping from ADR-015 (implemented as a mapping table in `tasks/ingest.py`, not ad-hoc logic)
**And** `mom:required` fields (`space`, `url`, `location.lat/lon`) that are missing cause a hard reject with outcome `"schema_invalid"` logged — no partial ingestion
**And** `mom:card` fields that are missing are ingested with a structured warning logged: `"card_field_missing: {field}"` — never silently dropped
**And** `mom:extended` fields present in the JSON are mapped to their MOM predicates; absent fields are silently skipped (they're optional)
**And** the resulting MOM JSON-LD is written to `<urn:mak:space/{id}>` (current) and `<urn:mak:space/{id}/{date}>` (append-only snapshot) via SPARQL UPDATE
**And** every fetch decision is logged to `heartbeat_log`: `space_uri`, `checked_at`, `outcome` (`ok` / `changed` / `no_change` / `schema_invalid` / `error` / `timeout`) — never silently dropped
**And** the snapshot path convention is exactly `/data/snapshots/{space_id}/latest.json` — this path is pinned here and referenced in Epic 4 stories

---

### Story 3.1: Heartbeat Scheduler — Periodic Fetch Cycle + Manual Trigger

As the system,
I want a scheduled job that fetches all registered endpoint URLs every 10 minutes using conditional GET,
So that the federated dataset stays fresh without any manual intervention and without hammering space servers unnecessarily.

As Luca (coordinator),
I want a "Refresh from endpoint" button on the space profile,
So that I can force an immediate update after editing my JSON without waiting for the next cycle.

**Acceptance Criteria:**

**Given** Oxigraph contains at least one space with a registered endpoint URL and `mak:confirmed` status
**When** the heartbeat scheduler fires (Nanobot CronService every 6h, configurable via `config.yaml`)
**Then** `tasks/heartbeat.py` is invoked for each confirmed space URI in sequence
**And** each fetch uses `If-None-Match` (ETag) and `If-Modified-Since` headers if the previous response provided them — only pulls full payload on actual change (NFR-R1)
**And** fetch timeout is 60s per endpoint with incremental backoff on failure: 1× immediate retry, then defer to next cycle (NFR-R2)
**And** each fetch outcome is written to `heartbeat_log` SQLite table: `space_uri`, `checked_at`, `http_status`, `latency_ms`, `outcome` (ok / changed / error / timeout) (AR-METR1)
**And** after all fetches complete, `scripts/materialize_geojson.py` is called once to refresh `spaces.geojson`
**And** fetch cadence, timeout, and retry policy are all read from `config.yaml` — never hardcoded (NFR-R3)
**And** a scheduler crash never takes down the public map — Nanobot's supervisor restarts the scheduler independently of the Discord adapter (NFR-R6)

---

### Story 3.2: Endpoint Health + Space Lifecycle + Open-Now (unified)

> **Rescoped 2026-05-06.** Original AC list (PII strip on closed) split to Story 3.2b. Open-now signal pulled in from the deferred Epic 7 entry — heartbeat already polls so it's read-side, not push-side. Epic 7 now parked indefinitely.
> Full ACs live in the story file: `_bmad-output/implementation-artifacts/3-2-freshness-lifecycle-aging-zombie-dead-transitions.md`.

As MOM, I want the heartbeat to interpret each fetch into three independent truth signals — endpoint health, space lifecycle, and dynamic open/closed — and resolve them into one honest pin, so that visitors see what's actually happening and coordinators get the right freshness incentive.

**Truth model (summary):**

- **Endpoint health** (clock: minutes since last 200/304) → `healthy` < 10m, `unresponsive` 10–30m, `warning` 30–60m, `broken` ≥ 60m. Map shows red ✕ only for `broken`; Epic 4 surfaces the rest.
- **Space lifecycle** (clock: days since `mom:lastUpdated`, only resets on real content diff) → `confirmed` < 30d, `aging` 30–90d, `zombie` 90–180d, `dead` ≥ 180d. **MOM never rewrites `mom:lastUpdated` from a state-only graph write.**
- **Dynamic open/closed** — `state.open` (v15 object) or `"open"`/`"closed"` (v0.13 string) → `mom:openNow` boolean + optional `mom:lastOpenChange`. **`state.open` flips count as material content changes** — they reset the lifecycle clock. `sensors.*` flips do not. This is the designed freshness incentive.
- **Conflict resolution:** lifecycle supersedes endpoint. A dead space with vanished hosting still shows as dead, not merely broken. Resolved server-side in `transformer.effective_marker(...)`; GeoJSON exposes a single resolved `status` plus the raw signals for Epic 4.

**Story 3.2b** carries the original `mak:closed` + PII-strip flow (closed for N cycles → strip contact fields, write `mak:closedAt`, revive on next material diff). Different blast radius (triple deletion) — separate review.

---

---

> **Stories 3.3 and 3.4 (magic link generation + coordinator email) are moved to Epic 4b** — parallel non-blocking epic. See Epic 4b below.

---

### Story 3.3 → Epic 4b: Magic Link Generation + Link-Handler Validation

As a coordinator receiving a nudge email,
I want a single-click link that either confirms my space is still active or gracefully closes it,
So that recovery requires no login, no form, and no context-switching — just one honest click.

**Acceptance Criteria:**

**Given** `tasks/magic_link.py` exists and `LINK_SECRET` is set in `.env`
**When** a magic link is generated for a space
**Then** the token is `base64url(HMAC-SHA256(uuid + expiry + space_uri, LINK_SECRET))` — stored as hash only in Oxigraph, never in plaintext (AR-MLNK2)
**And** the token has a 72h TTL written as `mak:expiresAt` triple
**And** `GET /claim/{token}?action=yes` on `mak-link-handler`:
- Validates token exists in Oxigraph (`ASK` query)
- Validates token not expired
- Validates token not already consumed
- On valid: writes `mak:consumed true`, resets `consecutiveFailures` to 0, sets status `mak:confirmed`, returns a confirmation HTML page ("Your space is live again 🔵") in the map's zine aesthetic (UX-DR16)
**And** `GET /claim/{token}?action=no`:
- Same validation steps
- On valid: marks space `mak:closed`, removes PII contact fields, writes `mak:closedAt`, returns a graceful closure page ("We've marked your space as closed on {date}. Thank you for keeping the map honest.") (UX-DR16)
**And** a second click on any consumed token returns: "This link has already been used." — no silent failure, no server error
**And** an expired token returns: "This link expired {N} hours ago — contact your network admin for a new one."

---

### Story 3.4: Coordinator Email Notification with Pre-filled Recovery Link

As a coordinator whose space endpoint has gone stale,
I want to receive an email that tells me exactly what's wrong and gives me a one-click path to fix it,
So that I can recover my pin without needing to remember what a JSON endpoint is or where to go.

**Acceptance Criteria:**

**Given** a space transitions to `mak:stale` or `mak:broken` (Story 3.2) and has a space-level contact address in Oxigraph
**When** the dispatch worker reads `<urn:mak:notifications>` queue
**Then** it generates a magic link token (Story 3.3), fills the notification template, and dispatches an email containing:
- Plain-language subject: "Your space [Name] on Maps of Making needs attention"
- Error summary: what happened and when (last successful fetch date, error category)
- YES link: "My space is still active — refresh my pin" → `/claim/{token}?action=yes`
- NO link: "My space has closed — remove it from the map" → `/claim/{token}?action=no`
- Link expiry notice: "These links expire in 72 hours"
- Footer: link to the space's public map pin and the network admin contact
**And** delivery failure retries 3× with progressive backoff (1h, 6h, 24h); after 3 failures, a `mak:escalated` triple is written and the space appears flagged in the admin dashboard (AR-MLNK3)
**And** if the space has no contact address, the notification is skipped and an admin alert is written instead: "Space {name} is stale but has no contact — manual outreach needed"
**And** the dispatch action is written to the admin audit log: `{ action: "notification_dispatched", space_uri, reason, timestamp }`
**And** the `mak:dispatched` triple timestamp prevents re-dispatch within 24h for the same space (prevents flood on repeated failures)

---

## Epic 6: "Ask the Map" — NL Bot

*(Parallel with Epic 3; non-blocker for demo)*

Arjun types a natural-language question in Discord, Telegram, or Mattermost. The bot translates it to SPARQL, validates against the IoP ontology, queries Oxigraph, and returns results with source links and SPARQL transparency. Graceful failure logs ontology gaps. Discord first, Telegram built-in, Mattermost custom adapter.

---

### Story 6.1: NL→SPARQL Task with IoP Ontology Context

As the system processing a user's natural-language question,
I want to translate it to a valid SPARQL SELECT query using the IoP ontology as a guardrail,
So that queries are grounded in real schema vocabulary and the LLM never invents predicates that don't exist in our graph.

**Acceptance Criteria:**

**Given** the IoP ontology is loaded in `<urn:mak:ontology/iop>` (Story 1.4) and the harness is running
**When** `tasks/nl_to_sparql.py` is called with a natural-language question string
**Then** it extracts a ~15–20% relevant subset of the IoP ontology via SPARQL CONSTRUCT, serializes it as a compact text block, and caches it in memory (AR-DATA5)
**And** calls OpenRouter via `llm_client.py` using the `nl_to_sparql` model (Sonnet, `temperature=0.0`, `max_tokens=512`) with the ontology subset as system context
**And** the prompt instructs the model to return only a SPARQL SELECT string targeting `<urn:mak:space/*>` and `<urn:mak:status>` named graphs, using only predicates present in the ontology context
**And** the returned SPARQL string is validated before use: checked for `DROP`, `INSERT`, `DELETE`, `UPDATE` keywords — any mutation attempt is rejected and logged as a security event (NFR-S5)
**And** the task returns a plain `str` (the SPARQL query) — no structured object (AR-AGT2)
**And** prompt cache hit-rate is logged per call to `llm_cost_log` SQLite table for admin dashboard tracking (NFR-L1)
**And** the ontology subset is refreshed from Oxigraph when `RELOAD_ONTOLOGY=1` env var is set (AR-DATA5)

---

### Story 6.2: Answer Formatting + Source Links + SPARQL Transparency

As a community member who asked the bot a question,
I want the answer in plain language with links to the actual spaces and an option to see the query that was run,
So that I can trust the result and follow up directly with the space — and curious users can inspect the reasoning.

**Acceptance Criteria:**

**Given** `tasks/nl_to_sparql.py` has returned a valid SPARQL query (Story 6.1) and `sparql_client.run_select()` has returned results
**When** `tasks/answer_format.py` is called with the original question, the SPARQL bindings, and the raw SPARQL string
**Then** it calls OpenRouter via the `answer_format` model (Minimax, `temperature=0.5`, `max_tokens=512`) to produce a plain-language summary
**And** the response includes: plain-language answer, a list of matching spaces with name + status badge + URI link (max 5 results, with "and N more — browse the full map" if exceeded)
**And** a spoiler/collapsed section shows the raw SPARQL query used ("show how I searched") — so technically curious users can inspect the query (FR39)
**And** if results are empty but the query is valid, the response reads: "I found no confirmed spaces matching that — try widening your search or browse the map directly" (not "0 results" alone)
**And** the task returns a plain `str` formatted for the target channel (Discord markdown for 6.4, plain text for 6.5/6.6)

---

### Story 6.3: Graceful Failure → Clarification + Ontology Gap Logging

As a community member whose question the bot couldn't answer,
I want a clear, honest response that tells me why and suggests what to do next,
So that a bot failure doesn't feel like a dead end — and the system learns from the gap.

**Acceptance Criteria:**

**Given** `tasks/nl_to_sparql.py` produces invalid SPARQL, or the SPARQL validation gate rejects it, or `run_select()` returns an error
**When** the failure is caught in the task chain
**Then** the bot responds in plain language: "I couldn't find a way to answer that with the map's current data. Try rephrasing, or browse the map directly at {url}" — no stack trace, no raw error (FR40, NFR-L3)
**And** the failed query is logged as an ontology gap triple in Oxigraph (FR41):
```turtle
<urn:mak:gap/{uuid}> a mom:OntologyGap ;
  mom:rawQuery "{escaped original question}" ;
  mom:rawLLMOutput "{escaped SPARQL attempt or error}" ;
  mom:timestamp "{ISO datetime}"^^xsd:dateTime .
```
**And** the gap triple is visible in the admin dashboard's Oxigraph sync panel as a queryable signal for ontology evolution
**And** LLM unavailability (OpenRouter timeout, rate limit) produces a distinct response: "The map's brain is temporarily busy — try again in a minute" and is logged separately from ontology gaps (NFR-L3)
**And** the retry budget is read from `config.yaml`: max attempts, jitter delay between retries (NFR-L3)

---

### Story 6.4: Discord `/ask-mom` Command Wired End-to-End

As a community member in the Discord server,
I want to type `/ask-mom "Des espaces confirmés avec du bois à Hamburg?"` and receive a useful answer within 30 seconds,
So that I can find maker spaces without leaving the community channel I'm already in.

**Acceptance Criteria:**

**Given** the Nanobot agent is running with Discord adapter enabled and the bot is invited to the Openfab Brussels Discord server
**When** a user runs `/ask-mom question:"<natural language question>"`
**Then** the bot immediately defers with `interaction.response.defer(thinking=True)` — buying 15 minutes before timeout (AR-AGT4)
**And** calls `nl_to_sparql.py` → `run_select()` → `answer_format.py` in sequence
**And** sends the formatted answer via `interaction.followup.send(answer)` — always via followup, never via `response.send_message()` (AR-AGT4)
**And** the answer includes Discord-formatted markdown: bold space names, inline links, collapsed SPARQL spoiler using `||spoiler||` syntax
**And** multilingual input is handled transparently — French, English, and German questions produce valid SPARQL via the ontology-grounded prompt (Journey 5 requirement)
**And** on any failure path (Story 6.3), the followup is still sent — the interaction never times out silently
**And** slash commands are synced via `tree.sync()` in `setup_hook`, not on every message (AR-AGT4)
**And** the command is tested end-to-end in the Openfab Discord server using real Oxigraph data before Epic 6 is considered done

---

### Story 6.5: Telegram Adapter

As a community member on Telegram,
I want to ask the bot the same natural-language questions I can ask on Discord,
So that communities using Telegram instead of Discord have equal access to the map's query capability.

**Acceptance Criteria:**

**Given** `TELEGRAM_BOT_TOKEN` is set in `.env` and the Nanobot config has `telegram: { enabled: true, token: "${TELEGRAM_BOT_TOKEN}" }`
**When** a user sends a message to the bot in a Telegram chat
**Then** Nanobot's built-in Telegram adapter routes the message through the same `nl_to_sparql` → `run_select` → `answer_format` task chain as Discord (AR-AGT5)
**And** the Telegram adapter uses the edit-message pattern for streaming-style responses: sends a "Thinking…" message, then edits it with the final answer (AR-INF2 / ADR-009 table)
**And** the response is formatted in plain text (no Discord markdown syntax) — links are bare URLs, bold via `*text*` Telegram markdown
**And** failure paths (Story 6.3) produce the same user-facing plain-language response
**And** `allowFrom` in config restricts Telegram access to `ADMIN_USER_ID` initially — opens to broader use at pilot (ADR-008 config)

---

### Story 6.6: Mattermost Custom Adapter

As a community member in an RFF or VOW Mattermost channel,
I want to ask `@mom-bot` natural-language questions about the map directly in our community's own platform,
So that the federated map is a tool used where our community already lives — not a separate destination.

**Acceptance Criteria:**

**Given** a Mattermost instance is available for the pilot network (RFF or VOW) and outgoing + incoming webhooks are configured
**When** a user posts `@mom-bot <question>` in a Mattermost channel
**Then** the Mattermost adapter receives the outgoing webhook POST, strips the bot mention, and routes the question through the same `nl_to_sparql` → `run_select` → `answer_format` chain
**And** the adapter implements the `ChannelAdapter` protocol (`async receive() → Message`, `async send(response, context) → None`) — the core task chain is never aware of the transport (AR-AGT5)
**And** the response is posted back via Mattermost incoming webhook as a plain-text message with bare URLs (no Discord/Telegram markdown)
**And** the adapter service runs as a separate Docker Compose service (`mak-agent-mattermost`) with `ADAPTER=mattermost` env var — same image, different config (ADR-009)
**And** the Mattermost adapter is the only custom-built adapter; Discord and Telegram use Nanobot built-ins
**And** the adapter is tested against the pilot Mattermost instance (RFF or VOW) with at least one real query answered correctly before Epic 6 is marked complete

---

## Epic 7: 🟢 "Open Now" Presence Layer *(parked indefinitely — 2026-05-06)*

> **Reframed 2026-05-06.** Heartbeat (Story 3.1) + honored SpaceAPI `state.open` (Story 3.2) cover the demo's open-now needs from the read side. The push/webhook approach this epic was designed for has no remaining demo value. Section retained as a design-conversation trail — DO NOT create stories under this epic without first re-justifying why heartbeat polling + `state.open` interpretation is insufficient.

A space's 🟢 badge fires when a webhook ping hits the presence endpoint within a TTL window. The schema slot and nginx route were reserved at Epic 1 — activation cost is one handler, one task, and one nginx uncomment.

---

### Story 7.1: Webhook Presence Handler + 🟢 Badge on Map

As a maker browsing the map,
I want to see a 🟢 badge on a confirmed space's pin when that space has recently signalled it's open,
So that I can identify spaces that are live right now — not just confirmed at some point in the past.

**Acceptance Criteria:**

**Given** the `<urn:mak:presence>` named graph slot exists in Oxigraph (reserved at Story 1.4) and the nginx `/webhook/presence` route is uncommented (reserved at Story 1.3)
**When** a space sends a POST to `/webhook/presence` with `{ space_uri, shared_secret, signal_type }` (door sensor / channel activity / fridge ping / manual)
**Then** the handler validates the `shared_secret` (per-space secret stored in Oxigraph, never in the payload)
**And** writes to `<urn:mak:presence>`:
- `<space-uri> mak:lastSeen "{ISO datetime}"^^xsd:dateTime`
- `<space-uri> mak:isOpenNow true`
**And** a TTL cleanup job (runs hourly) sets `mak:isOpenNow false` for any space whose `mak:lastSeen` is older than the configured TTL (default 4h, configurable)
**And** `materialize_geojson.py` includes the `LEFT JOIN` against `<urn:mak:presence>` that was wired (but returning null) since Story 1.5 — now returns `isOpenNow: true` for signalling spaces
**And** the map renders a 🟢 pulse badge on the confirmed pin (existing `.marker-pulse` CSS animation already in phase-1 stylesheet — activate by adding `open` class)
**And** the presence handler is a separate thin FastAPI route added to `mak-link-handler` (no new container needed)
**And** the public map never shows presence for seeded/stale/broken pins — only confirmed spaces can signal open-now
