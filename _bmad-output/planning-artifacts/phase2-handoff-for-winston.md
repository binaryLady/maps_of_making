# Phase 2 Handoff — for Winston (Architect)

**Date:** 2026-04-21  
**From:** Amelia (dev agent) + Nicolas  
**To:** Winston (/bmad-agent-architect)  
**PRD:** `_bmad-output/planning-artifacts/prd.md` (all 12 steps complete)

---

## What exists today

### Live prototype
- URL: `https://mapofmaking.debarquin.eu`
- Stack: nginx:alpine serving static `web/` + Oxigraph SPARQL triplestore (deployed, empty, not wired)
- Infra: `infra/docker-compose.yml` on Hetzner VPS (128.140.72.105)

### Frontend (`web/`)
- `maps-of-making.html` + `app.js` — fullscreen MapLibre SPA
- Map tiles: OpenFreeMap vector tiles (dev). `TILES_URL` constant in `app.js` is the single swap point for self-hosted PMTiles.
- Data source: `data/moms_seed.json` — 30-ish synthetic spaces (FR + DE), loaded at boot via `fetch()`
- All UI features working: filters, search, detail drawer, embed snippet generator, embed-mode iframe detection
- "Add your URL" drawer exists in UI but is **fully simulated** — no real fetch, no validation, no persistence

### What is NOT built
- No ingestion pipeline
- No real URL fetch/validation
- Oxigraph not populated, not queried
- No admin dashboard
- No bot (NanoClaw/OpenClaw)
- No authentication of any kind

---

## Key decisions from Phase 1

### Architecture constraints confirmed
- **Map is pure reader** — no record editing, append-only versioned snapshots
- **JSON endpoints describe spaces, not people** — no personal contacts in public data
- **All thresholds in config** (fetch cadence, failure counts, retention) — set from real PoC telemetry, not hardcoded
- **Admin: shared password, Nicolas + Jason only** — PoC-grade; harden at pilot

### Data model (from `moms_seed.json` — agreed schema shape)
Each space has:
```json
{
  "id": "...",
  "name": "...",
  "city": "...",
  "country": "FR|DE",
  "address": "...",
  "coordinates": { "lat": 0.0, "lon": 0.0 },
  "status": "seeded|confirmed|open|stale|broken",
  "endpoint_url": "https://...",
  "last_fetched": "ISO8601",
  "open_now": false,
  "open_for_hosting": false,
  "opening_hours": "...",
  "founded": 2010,
  "capacity": 40,
  "contact": "...",
  "website": "...",
  "specialties": ["wood", "electronics", ...],
  "network_memberships": ["RFF", "VOW", ...]
}
```
The frontend already renders all these fields. The real backend must produce this shape (or a superset the frontend can consume).

### Tile strategy
- Dev: OpenFreeMap (`https://tiles.openfreemap.org/planet`) — CORS-enabled, no key, OpenMapTiles schema
- Prod target: self-hosted PMTiles on VPS, served from same origin. `pmtiles extract` for FR+DE bbox. PMTiles protocol already registered in boot.
- `TILES_URL` constant in `app.js` line ~5 is the only swap needed.

### Embed model
- Iframe snippet uses `window.location.origin + window.location.pathname` — works on any domain automatically
- Embed-mode detected via `window.self !== window.top` — hides all UI chrome, shows clean map only
- No server-side preset storage — URL params carry the full state (bbox, filters, center)

### UI pin states (frontend already handles all of these)
- `seeded` — unclaimed, no endpoint
- `confirmed` — endpoint verified, responding
- `open` — confirmed + open right now
- `stale` — endpoint not responding for N days
- `broken` — endpoint 404 or invalid schema

The **pin flip ⚪→🔵** (seeded → confirmed) is the Phase 2 hero moment. Everything in the architecture should optimise for that moment being fast and reliable.

---

## Phase 2 scope (from PRD)

### Must have for pilot
1. **URL ingestion** — coordinator pastes endpoint URL → system fetches, validates schema, flips pin
2. **Scheduled re-fetch** — periodic health check of all confirmed endpoints, updates status/freshness
3. **Oxigraph population** — ingest validated JSON into SPARQL triplestore
4. **Admin dashboard** — who's live/stale/broken at a glance, triage in <2 min
5. **Bot query (≥1)** — natural language → SPARQL over live endpoints, in real Mattermost or Matrix channel

### Parked (Phase 3)
- IPFS/IPLD archival of anonymized snapshots
- Multi-network beyond RFF + VOW
- Public API

---

## Lessons learned from Phase 1 (for architecture decisions)

1. **Oxigraph is already deployed** — don't redesign the triplestore choice. It works. Wire it.
2. **The frontend consumes a flat JSON array** — the backend must either serve `moms_seed.json`-compatible JSON or the frontend needs a thin adapter layer. Simplest: keep the static JSON as the map's read model, updated by the ingestion pipeline.
3. **BrowserSync ghost mode** caused apparent state-sharing between iframe and main tab in local dev. Non-issue in production — document it so future devs don't chase ghosts.
4. **Notion embeds work** (URL paste → live iframe), but tile loading is slow on first render. Not a blocker.
5. **`window.self !== window.top` embed detection is clean** — no extra URL params needed. Keep this pattern.
6. **"Add your URL" is the critical path for Phase 2** — the existing UI drawer is the right entry point. Architecture must make that flow real.
7. **Simulated data was enough for Phase 1** — but the schema must not drift. Any backend changes to the space data shape must be reflected in `moms_seed.json` and the frontend renderer.

---

## Questions for Winston to resolve

1. **Ingestion service** — standalone Python/Node microservice or something in the nginx+oxigraph compose stack?
2. **Read model** — does the map query Oxigraph via SPARQL at runtime, or does ingestion write a fresh `moms_seed.json`-equivalent that nginx serves statically? (Static JSON is simpler and already works; SPARQL at runtime enables richer queries but adds latency and a new failure mode.)
3. **Validation gateway** — schema validation before Oxigraph write: JSON Schema only, or semantic checks too (e.g. coordinates in expected bbox, status values)?
4. **Re-fetch cadence** — cron in compose, or event-driven? What triggers a re-check on a confirmed endpoint?
5. **Bot adapter interface** — Matrix only for PoC, or also Mattermost from day one?
6. **NanoClaw vs OpenClaw** — which agent for SPARQL generation? What's the validation gate before queries reach Oxigraph?

---

## How to start the Winston session

```
/bmad-agent-architect

Context: maps_of_making Phase 2. PRD at _bmad-output/planning-artifacts/prd.md.
Phase 1 complete — handoff at _bmad-output/planning-artifacts/phase2-handoff-for-winston.md.
Read both before designing. Focus on: ingestion pipeline, Oxigraph schema, read model strategy, bot adapter interface.
```
