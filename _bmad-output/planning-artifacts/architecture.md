---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-04-22'
lastEdited: '2026-04-29'
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '_bmad-output/planning-artifacts/next-session.md', 'archive/docs/architecture/architecture.md', 'archive/docs/project-overview.md', 'archive/docs/index.md']
workflowType: 'architecture'
project_name: 'maps_of_making'
user_name: 'nicolas'
date: '2026-04-22'
editHistory:
  - date: '2026-04-29'
    changes: 'Added ADR-015 (SpaceAPI JSON → MOM JSON-LD transformation layer, raw snapshot to disk); updated Primary Users (3-way split: coordinator / network coordinator Luca / operator Nicolas); updated Data Flow (3-stage pipeline, operator inspection panel, Luca public toggle); updated FR mapping table; added /data/snapshots/ to project structure'
  - date: '2026-05-18'
    changes: 'Added ADR-016 (Layered Community Namespaces + Bundle-Loading Model) — four-layer schema, bundle = view config, schema:knowsAbout concept pivot, crosswalk.csv as living bridge registry; Story 3.5'
---

# Architecture Decision Document — maps_of_making

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## Project Context Analysis

### Project Overview

Maps of Making is federated infrastructure for the European maker ecosystem, piloting with RFF (France) and VOW (Germany). The core model: each space publishes one JSON-LD file at a URL they control; a heartbeat agent monitors those URLs for diffs; changes update an Oxigraph RDF triplestore; queries are answered via SPARQL or NL→SPARQL from the webapp or channel bots.

**Phase 1 (shipped):** MapLibre GL JS SPA + PMTiles vector tiles, filters, search, detail drawer, embed snippet. Deployed at mapofmaking.debarquin.eu.

**Phase 2 (this architecture):** Federated backend — URL ingestion pipeline, Oxigraph SPARQL triplestore, pin state confirmation, admin dashboard, NL bot via Discord.

### Primary Users

1. **Space coordinators** — submit one JSON endpoint URL (SpaceAPI-compatible), see their pin flip ⚪→🔵, get nudged if their endpoint goes stale. They own and publish their data; MOM only reads it.
2. **Network coordinators (e.g. Luca/VOW)** — use the public health map toggle (Tweaks panel) to read fleet state at a glance. No login, no admin access. Available to any interested party.
3. **MOM operator (Nicolas)** — infrastructure observability: system health (Oxigraph, ingestion process), space registry with last-probe timestamps, raw/ingested/displayed inspection panel for pipeline diagnosis. This is the `/admin` dashboard audience.
4. **Makers (secondary)** — browse confirmed spaces, use bot queries in their community channel

### Functional Requirements Summary

44 functional requirements across 2 phases. Phase 2 key areas: coordinator registration (FR19–23), endpoint health/ingestion (FR24–27b), admin dashboard (FR28–33b), federated SPARQL query (FR34–36), NL bot (FR37–42).

### Non-Functional Requirements — Architecturally Load-Bearing

- **NFR-R1** Conditional GET (ETag/Last-Modified) — heartbeat must be stateful
- **NFR-R3** All fetch thresholds config-file-driven, not hardcoded
- **NFR-R5** Map usable with 50% endpoints unreachable — degrade to stale, never empty
- **NFR-D1/D2/D3** Spaces not people — PII rejected at ingestion; SPARQL gate rejects `schema:Person`
- **NFR-A1–A5** WCAG 2.1 AA including non-map accessible list view
- **NFR-L1–L4** LLM cost ceiling enforced, prompt cache tracked, retry budget defined

### Scale & Complexity

- Phase 2 complexity: **High** — three distinct subsystems (heartbeat pipeline, admin dashboard, NL bot) sharing Oxigraph
- PoC target: 10 spaces → RFF+VOW pilot ~500 spaces → IoP horizon ~15k
- All thresholds (fetch cadence, failure counts, retention) set from real PoC telemetry — not pre-optimized

### Technical Constraints Already Decided (Pre-Architecture)

| Decision | Status |
|---|---|
| MapLibre GL JS + PMTiles | ✅ Shipped |
| Vanilla JS SPA, no framework | ✅ Shipped |
| Oxigraph RDF triplestore (SPARQL 1.1) | ✅ ADR-001 |
| JSON-LD as space endpoint format | ✅ ADR-003 |
| Docker Compose on VPS | ✅ Decided |
| MOM ontology + Schema.org + IoP vocabulary | ✅ Decided |

### Cross-Cutting Concerns

1. **Pin visual language** — must be defined before backend data model (it defines what the map endpoint serves)
2. **Ontology scope** — MOM vocab vs Schema.org vs IoP: which predicates are authoritative?
3. **LLM harness selection** — NL→SPARQL + heartbeat diff + answer formatting + notification dispatch
4. **Heartbeat agent boundary** — HTTP fetch+diff scope vs LLM interpretation scope
5. **Append-only snapshots** — named graphs in Oxigraph temporal versioning strategy

---

## Starter Template Evaluation

### Primary Technology Domain
Mixed brownfield stack — no conventional starter template applies.
- **Frontend SPA:** shipped vanilla JS prototype (Phase 1) — no changes
- **Python harness:** custom module built from scratch per ADR-008 structure
- **Infrastructure:** Docker Compose extending Phase 1 stack

### Nanobot Agent Dependencies
Nanobot includes all required dependencies:
```
nanobot              # Agent framework (Discord, Telegram, Slack adapters built-in)
litellm              # OpenRouter + multi-provider LLM support
asyncio              # Scheduling via CronService + HEARTBEAT.md
httpx                # async SPARQL client (not SPARQLWrapper — sync only)
pyyaml               # config loading for custom tasks
```
Custom tasks (heartbeat.py, nl_to_sparql.py, etc.) run inside Nanobot's executor. No custom event loop or APScheduler needed — CronService + HEARTBEAT.md handle all scheduling.

### First Implementation Story (Spike)
Build exactly three files, nothing else:
- `harness/main.py` — Discord bot connects, logs "ready"
- `harness/llm_client.py` — one `AsyncOpenAI` call to OpenRouter, returns string
- `harness/sparql_client.py` — one `httpx` query to Oxigraph health endpoint

One `/ping` slash command calls SPARQL + LLM in sequence. Proves: Discord auth, OpenRouter auth, Oxigraph reachability, async chain. That's the full dependency risk surface.

### Docker Compose Additions (Phase 2)
```yaml
name: maps_of_making    # explicit — prevents network name drift across VPS projects

services:
  oxigraph:
    image: ghcr.io/oxigraph/oxigraph:latest
    command: ["--location", "/data", "--bind", "0.0.0.0:7878"]
    volumes:
      - oxigraph_data:/data
    expose: ["7878"]          # internal only — never host-bound
    networks: [internal]

  harness:
    build: ./harness          # python:3.12-slim base
    environment:
      - ADAPTER=discord       # env var selects channel adapter
      - OXIGRAPH_ENDPOINT=http://oxigraph:7878
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - DISCORD_BOT_TOKEN=${DISCORD_BOT_TOKEN}
    depends_on: [oxigraph]
    networks: [internal]
```

### Port Isolation from Side Projects
`expose` (not `ports`) = no host-level port conflict. Explicit `name: maps_of_making` = separate `maps_of_making_default` Docker network. Two stacks with the same Oxigraph port are fully isolated. Verify with `docker network ls`.

### Secondary Channel Adapters (same image, planned)
| Adapter | Library | Defer/thinking pattern | Start mode |
|---|---|---|---|
| Telegram | `python-telegram-bot` | Placeholder message + `edit_message_text` | Polling (no public URL needed) |
| Mattermost | `httpx` (webhook model) | Silent or throwaway message | Outgoing + incoming webhooks |

One service per active adapter (`ADAPTER=telegram`, `ADAPTER=mattermost`). Heartbeat scheduler runs in the primary (Discord) service only.

### Backup Strategy
Host cron daily — outside harness, no backup logic in application code:
```bash
curl -s "http://localhost:7878/dump?format=application/n-quads" \
  > /var/backups/oxigraph/dump-$(date +%Y%m%d).nq
find /var/backups/oxigraph -name "*.nq" -mtime +7 -delete
```

---

## Architectural Decisions (Party Mode Sessions)

### ADR-004: Pin Visual Grammar

**Decision:** Two-layer progressive disclosure model.

**Default view (always visible):**
- ⚪ Hollow grey circle — seeded, unconfirmed (from moms_seed.json bootstrap)
- 🔵 Solid blue circle — confirmed (space-owned JSON-LD endpoint, successfully ingested)
- 🟢 Green badge on blue pin — open right now (webhook/device ping, Phase 2 late feature)
- 🔴 Solid red circle — error state (URL unresponsive, fetch failed)

**Health map toggle (admin/researcher layer):**
- Reveals aging / zombie / dead states for unclaimed seeds
- Never shown by default — diagnostic layer, not exploratory layer
- In the space detail drawer: amber quiet banner ("Last confirmed 8 months ago. Details may be outdated.") visible even without the toggle

**Pin shape:** Circles only. No shape-based type differentiation for PoC or pilot. Type disambiguation handled by filter panel and bot queries (LOD approach). Shape grammar revisited post-pilot if needed.

**Freshness lifecycle:**

```
⚪ seeded → confirmed → [aging] → [zombie] → 💀 dead  /  🪦 closed
```

> ⚠ **Superseded — see Story 3.2's three-axis truth model (`epics.md`) and `mom_handoff_2026-05-16.md`.**
> Lifecycle is no longer "unclaimed seeds only" — the heartbeat drives it for confirmed spaces too. The current model has **three orthogonal axes** resolved into one pin by `transformer.effective_marker()`: endpoint reachability (`healthy/unresponsive/warning/broken`), lifecycle freshness (`seeded/confirmed/aging/zombie` + two terminals), and the open/close boolean. Two terminal lifecycle states: **`closed`** (operator-declared retirement) and **`dead`** (auto-inferred after N failed cycles) — both render as a tombstone marker but preserve provenance.

Dead/closed spaces: removed from default map view, retained in Oxigraph for admin query; significant life-events recorded in the append-only `<urn:mak:public_ledger>` graph.

**Rationale:** Keeps the first-look map clean and trustworthy. Admin layer serves network coordinators who want to identify spaces needing outreach. Shape complexity deferred — filters and bot search solve type disambiguation more elegantly at scale.

---

### ADR-005: Space Coordinator Nudge — Magic Link

**Decision:** When a space's heartbeat goes stale, openclaw dispatches a templated email to the last known contact in Oxigraph containing a time-limited, single-use magic link.

**Flow:**
1. Heartbeat scheduler detects endpoint aging threshold crossed
2. Writes `mak:pendingNotification` triple to Oxigraph notification queue
3. Dispatch worker reads queue, generates magic link token, sends email
4. **YES link** (still active) → refreshes status, resets timer, marks confirmed
5. **NO link** (we've closed) → graceful confirmation screen, space marked closed with date, PII removed per GDPR closure logic
6. **No response** → timer continues → zombie → dead by timeout
7. **Bounce/delivery failure** → retry 3× with progressive backoff → escalate to network admins listed on the space card

**Magic link properties:** Single-use, time-limited (72h), signed token. Prevents stale email chains from refreshing a closed space.

**Rationale:** Zero friction for space coordinators (one click, no login). Honest about the "no" path. Graceful degradation when contact is wrong. Network admin escalation closes the loop.

---

### ADR-006: Freshness Status Model in Oxigraph

> ⚠ **Partially superseded (2026-05-16).** The materialized-not-query-time decision still holds. The flat single-axis lifecycle below is superseded by Story 3.2's **three-axis truth model** (endpoint health / lifecycle freshness / open-close), the `mom:` predicate namespace (not `mak:` — drift fixed in Story 3.2c), and **two terminal states** `closed` (declared) + `dead` (inferred). Heartbeat cadence is 10 min, not 6 h. Authoritative model: `epics.md` Story 3.2 + `mom_handoff_2026-05-16.md`.
>
> **LOD design note (Story 3.2c, 2026-05-16):** Lifecycle state values are `xsd:string` literals (`"confirmed"`, `"seeded"`, etc.) — a deliberate 4-star LOD choice for current scope. Earlier drafts used `mak:confirmed`, `mak:seeded` etc. as apparent RDF IRIs; this reflected a deferred 5-star LOD upgrade path (state values as dereferenceable `skos:Concept` resources). That upgrade is out of scope for the demo. Do not reintroduce IRI-style state values without first minting those concepts in `mom.ttl`.

**Decision:** Materialized status triples written by a scheduled job. Not computed at query time.

**Status graph structure:**
```turtle
<seed:xyz> mom:healthStatus [
  mom:visibility "public" ;          # ⚪🔵🟢🔴 — always rendered
  mom:operationalState "aging" ;     # admin toggle layer
  mom:lastChecked "2026-04-22T..."^^xsd:dateTime ;
  mom:consecutiveFailures 3 ;
] .
```

**Status lifecycle (written by scheduler):**

| Status | Written by | Trigger |
|---|---|---|
| `"seeded"` | Seed ingest | moms_seed.json import |
| `"confirmed"` | Heartbeat agent | First successful JSON-LD fetch |
| `"aging"` | Scheduler | 30d no fetch |
| `"zombie"` | Scheduler | 90d no fetch |
| `"dead"` | Scheduler | 180d no fetch |
| `"error"` | Heartbeat agent | HTTP error / timeout |

**Map queries:** Base query filters on `mom:visibility = "public"`. Admin toggle fires a second SPARQL query overlaying `mom:operationalState` for aging/zombie/dead — no page reload, no separate endpoint.

**Scheduler:** Single cron job every 6h, Python script against Oxigraph SPARQL update endpoint. Idempotent — only writes on status change. No new infrastructure.

**Seed→claim transition:** On first successful fetch of a self-hosted JSON-LD, heartbeat agent overwrites seed triples in the space's named graph, sets `mom:operationalState` to "confirmed". Seed triples tagged `mom:source` as "seed" — preserved one cycle as diff baseline, then dropped.

---

### ADR-007: Real-Time "Open Now" Signal

**Decision:** Webhook pings write to a separate `presence` named graph. Never coupled to heartbeat.

```turtle
GRAPH <urn:mak:presence> {
  <space-uri> mak:lastSeen "2026-04-22T14:32:00Z"^^xsd:dateTime .
  <space-uri> mak:isOpenNow true .
}
```

Heartbeat agent owns `<urn:mak:space>` graph. Webhook handler owns `<urn:mak:presence>` graph. Map query does `LEFT JOIN`. No coupling. Webhook endpoint: thin HTTP handler, validates shared secret, writes one triple, returns 200.

**Phase placement:** Data model slot reserved now. Webhook handler implemented as late Phase 2 feature — no schema changes required when added.

---

### ADR-008: LLM Harness — Custom Python over OpenRouter

**Decision:** Custom Python harness using `AsyncOpenAI` client pointed at OpenRouter. No third-party agent framework (NanoClaw disqualified on model lock-in; OpenClaw disqualified on complexity).

**Rationale:**
- NanoClaw: Anthropic SDK only — cannot use OpenRouter/Minimax/Kimi. Cost-disqualifying.
- OpenClaw: 500k lines, 70+ deps, 53 config files. Unnecessary complexity for 4 constrained tasks.
- Custom harness: ~200 lines, full control, model swap is one config line, auditable.

**Project structure:**
```
harness/
├── config.yaml              # model assignments + endpoints
├── main.py                  # Discord bot + background scheduler
├── llm_client.py            # AsyncOpenAI → OpenRouter, headers baked in
├── sparql_client.py         # httpx async SELECT + UPDATE
├── tasks/
│   ├── heartbeat.py         # diff two JSON-LD versions
│   ├── nl_to_sparql.py      # NL → SPARQL string (temp=0.0)
│   ├── answer_format.py     # SPARQL result → plain language
│   └── notify_dispatch.py   # pure logic: read queue, send, write back
└── adapters/
    └── discord_adapter.py   # slash commands + defer pattern
```

**Nanobot config.json (LiteLLM provider + multi-model):**
```json
{
  "providers": {
    "default": {
      "type": "litellm",
      "api_key": "${OPENROUTER_API_KEY}",
      "base_url": "https://openrouter.ai/api/v1",
      "models": {
        "heartbeat": { "model": "anthropic/claude-haiku-4-5", "temperature": 0.2, "max_tokens": 1024 },
        "nl_to_sparql": { "model": "anthropic/claude-sonnet-4-5", "temperature": 0.0, "max_tokens": 512 },
        "answer_format": { "model": "minimax/minimax-01", "temperature": 0.5, "max_tokens": 512 }
      }
    }
  },
  "channels": {
    "discord": { "enabled": true, "token": "${DISCORD_BOT_TOKEN}" },
    "telegram": { "enabled": true, "token": "${TELEGRAM_BOT_TOKEN}", "allowFrom": ["${ADMIN_USER_ID}"] }
  }
}
```

**Custom tasks in Nanobot:**
```python
# tasks/heartbeat.py — invoked by Nanobot's HEARTBEAT.md scheduler
async def heartbeat_task(oxigraph_endpoint: str, space_uri: str) -> str:
    # Fetch space JSON-LD, diff against snapshot, write SPARQL UPDATE
    # Returns structured message for chat or silent execution
    
# tasks/nl_to_sparql.py — invoked by Discord/Telegram slash commands
async def nl_to_sparql(user_question: str, ontology_context: str, model: str = "default") -> str:
    # Use Nanobot's LiteLLM provider to call model
```

**SPARQL client:** `httpx.AsyncClient` directly — SPARQLWrapper is synchronous, skip it.

---

### ADR-009: Channel Bot — Protocol-Agnostic Core, Discord First

**Decision:** Discord first (Nicolas is admin at Openfab Brussels). Protocol-agnostic core with thin channel adapters.

**Adapter interface:**
```python
class ChannelAdapter(Protocol):
    async def receive(self) -> Message: ...
    async def send(self, response: str, context: dict) -> None: ...
```

**Discord defer pattern** (mandatory — LLM calls exceed 3s slash command timeout):
```python
@bot.tree.command(name="ask", description="Ask a question about the map")
async def ask(interaction: discord.Interaction, question: str):
    await interaction.response.defer(thinking=True)   # buys 15 minutes
    sparql = await nl_to_sparql.run(question)
    results = await run_select(sparql)
    answer = await answer_format.run(question, results)
    await interaction.followup.send(answer)
```

**Bot invite requirements:** `applications.commands` + `bot` scopes. Commands synced via `tree.sync()` in `setup_hook`.

**Future adapters:** Matrix, Mattermost — same `ChannelAdapter` Protocol, different transport. Docker Compose adds one service per active channel (`openclaw-discord`, `openclaw-matrix`). Core never imports from adapters.

---

### ADR-010: Notification Dispatch Architecture

**Decision:** Pending notification queue in Oxigraph. Separate dispatch worker. No LLM for PoC.

```turtle
<space:xyz> mak:pendingNotification [
  mak:recipient <coordinator:abc> ;
  mak:preferredContactChannel "email" ;
  mak:reason "unresponsive_url" ;
  mak:since "2026-04-22T..."^^xsd:dateTime ;
  mak:retryCount 0 ;
] .
```

Dispatch worker: reads queue → fills template → sends → writes `mak:dispatched` triple. Retry logic: 3× with progressive backoff on delivery failure → escalate to network admins listed on space card. LLM added to this task only if payload becomes unstructured — explicit `model: null` in config signals this is intentional.

---

### ADR-011: Magic Link HTTP Endpoint — Separate `link_handler` Service ⚠️ BLOCKER

**Decision:** The magic link YES/NO handler is a dedicated FastAPI container (`link_handler/`), proxied by nginx at `/claim/*`. It is **not** part of the Discord harness process.

**Problem:** There is no HTTP listener inside the harness process. Discord bots don't bind ports. When a space coordinator clicks the YES/NO link in their email, there's nowhere to receive it unless a separate HTTP service exists.

**Solution:**
```python
# link_handler/main.py (~50 lines)
from fastapi import FastAPI
import httpx, os, hashlib, time

app = FastAPI()
ENDPOINT = os.environ["OXIGRAPH_ENDPOINT"]
SECRET = os.environ["LINK_SECRET"]

@app.get("/claim/{token}")
async def claim(token: str, action: str):  # action = "yes" | "no"
    # 1. Validate token exists and not expired (ASK query to Oxigraph)
    # 2. Validate token not already consumed
    # 3. Execute SPARQL UPDATE: mark consumed + update space status
    # 4. Return confirmation HTML page
```

**nginx routing:**
```nginx
location /claim/ {
    proxy_pass http://mak-link-handler:8000/claim/;
}
```

**Why separate service:** FastAPI binds a port, Discord bot doesn't. Keeping them merged would require threading or an embedded ASGI server inside the bot process — unnecessary coupling and complexity.

**Implementation note:** `LINK_SECRET` is the HMAC signing key. Tokens are `base64url(HMAC-SHA256(uuid + expiry + space_id, secret))`. Never store tokens in plaintext — only the hash.

---

### ADR-012: Operational Metrics — SQLite in Scheduler Container

**Decision:** SQLite database at `./data/metrics.db` (mounted volume), written by `mak-scheduler`. Exposed via a simple `/metrics` REST endpoint on the scheduler service. **Not** stored in Oxigraph.

**Rationale:** Storing operational metrics (heartbeat success/failure counts, response times, LLM cost per task) in Oxigraph creates a circular dependency: the heartbeat monitoring Oxigraph health cannot query Oxigraph if it's down. SQLite is a mounted file, survives container restarts, zero infrastructure overhead.

**Schema (minimal):**
```sql
CREATE TABLE heartbeat_log (
    id INTEGER PRIMARY KEY,
    space_uri TEXT,
    checked_at DATETIME,
    http_status INTEGER,
    latency_ms INTEGER,
    outcome TEXT  -- 'ok' | 'changed' | 'error' | 'timeout'
);

CREATE TABLE llm_cost_log (
    id INTEGER PRIMARY KEY,
    task TEXT,
    model TEXT,
    input_tokens INTEGER,
    output_tokens INTEGER,
    called_at DATETIME
);
```

**Access:** `/metrics` endpoint on `mak-scheduler` (internal Docker network) returns JSON summary. Admin dashboard queries it directly. No public exposure.

---

### ADR-013: Agent Framework — Nanobot with One Custom Adapter

**Decision:** Use Nanobot as the primary agent framework. Discord and Telegram adapters built-in; implement one custom Mattermost adapter if needed post-pilot.

**Rationale:**
- **OpenRouter native:** LiteLLMProvider handles `anthropic/claude-*`, `minimax/minimax-01`, OpenRouter transparently — full model-swap control via config
- **Scheduler included:** CronService + HEARTBEAT.md (30-minute polling) — heartbeat pattern ready, no custom event loop
- **Channel adapters free:** Discord (defer pattern), Telegram (polling), Slack built-in; Mattermost is the only custom adapter needed
- **Maintained project:** ~4,000 lines, high source reputation (77.6 benchmark score), active development

**Trade-off analysis:**
- Custom harness: ~200 lines base, but add Discord defer logic (~50), Telegram edit pattern (~50), scheduler loop (~100), SPARQL bindings normaliser (~50), magic link validation (~50), structured logging (~100) = **~600 lines actual**
- Nanobot: ~4,000 lines but multi-channel support + scheduling included = **less custom code overall + fewer moving parts**

**Mattermost adapter:** If needed, implement as custom extension after pilot. Nanobot's adapter protocol is straightforward (send/receive interface).

**Implementation:** Dockerfile `FROM hkuds/nanobot:latest`. Port `config.yaml` to Nanobot's `config.json` format. Keep `tasks/` directory structure for LLM tasks (heartbeat.py, nl_to_sparql.py, etc.) — they stay the same, just invoked from Nanobot instead of harness/main.py.

---

### ADR-015: Ingestion Transformation Layer — SpaceAPI JSON → MOM JSON-LD

**Decision:** Spaces publish flat SpaceAPI-compatible JSON. MOM provides an explicit transformation layer that converts this into MOM JSON-LD before writing to Oxigraph. The raw pre-transformation payload is written to disk before any transformation occurs.

**The pipeline — three explicit stages:**

```
Stage 1 — FETCH
  Space publishes SpaceAPI JSON at their URL
  Heartbeat does conditional GET (ETag / Last-Modified)
  Raw JSON written to disk: /data/snapshots/{id}/latest.json
  (with fetch timestamp — this is the Zone 3 source and audit trail)

Stage 2 — TRANSFORM
  SpaceAPI JSON → MOM JSON-LD mapping (ontology applied)
  Explicit field-by-field mapping defined in tasks/ingest.py
  Normalize before compare: strip ephemeral timestamps, sort arrays
  If payload unchanged vs stored snapshot → update timestamp only, skip Stage 3
  If changed → proceed to Stage 3

Stage 3 — INGEST
  MOM JSON-LD → Oxigraph triples
  Write to <urn:mak:space/{id}> (current) + <urn:mak:space/{id}/{date}> (snapshot)
  Write decision log: "ingested" | "no_change" | "error" — every fetch logged
```

**Why raw snapshot to disk, not Oxigraph:**
The raw pre-transformation JSON is the audit trail and Zone 3 source. Storing it in Oxigraph would couple the debugging tool to the triplestore — fragile if Oxigraph is what's being diagnosed. Disk is boring and correct. The admin inspection panel reads raw from disk; transformed from Oxigraph.

**The ontology's role in transformation:**
The `.ttl` is the specification; `tasks/ingest.py` is its implementation. They are coupled. If `mom.ttl` declares `mom:MakerSpace rdfs:subClassOf schema:LocalBusiness`, the transformation must emit `@type: ["mom:MakerSpace", "schema:LocalBusiness"]`. Drift between spec and implementation means silent data errors.

**SpaceAPI → MOM field mapping (explicit contract):**

| SpaceAPI field | MOM JSON-LD mapping | Notes |
|---|---|---|
| `space` | `schema:name` | Required |
| `url` | `schema:url` | Required |
| `location.lat/lon` | `schema:geo` → `schema:GeoCoordinates` | Required |
| `location.address` | `schema:address` → `schema:PostalAddress` | Card subset |
| `contact.website` | `schema:url` (space website) | Card subset |
| `state.open` | `mom:isCurrentlyOpen` | Card subset |
| `opening_hours` | `schema:openingHoursSpecification` | Card subset |
| `linked_spaces[]` | `mom:NetworkMembership` | Extended subset |
| `membership_plans[]` | `mom:membershipPlans` | Extended subset |
| *(no SpaceAPI equivalent)* | `mom:consortium` | MOM extension |
| *(no SpaceAPI equivalent)* | `mom:residency` | MOM extension |
| *(no SpaceAPI equivalent)* | `mom:specialties`, `mom:equipment` | MOM extension |

**MOM extension fields (no SpaceAPI equivalent):** live in `mom:extended` subset. Ingested when present; never required. Progressive unlock UX signals which subset a space has reached.

**Long-term ambition:** This transformation layer is MOM's core value-add. Spaces need zero knowledge of linked data. The bridge pattern at community scale is MOM's argument for SpaceAPI adopting JSON-LD natively — making this implementation the reference.

**Snapshot file convention (pinned — Epic 3 must write this path):**
```
/data/snapshots/{space_id}/latest.json      # always the most recent raw fetch
/data/snapshots/{space_id}/{timestamp}.json # append-only archive (optional, configurable)
```

> **[Transition note, 2026-05-19]:** This ADR describes the **legacy pipeline** (registered spaces → `heartbeat_log.db` → transformer → Oxigraph). Story 3.6 (Epic 3.5) builds a **new clean snapshot pipeline** alongside it, canary-only, implementing the snapshot-as-unit model (payload + observed_at + UID). Stories 3.7–3.10 migrate registered spaces onto the clean path and delete the legacy code wholesale. During transition, both pipelines run in parallel, isolated by named graph and GeoJSON features.

---

### ADR-016: Layered Community Namespaces + Bundle-Loading Model

**Decision:** The MOM schema is organised as four layers under the **single canonical authority** `https://nicolasdb.github.io/mapsofmaking_ontology/`. Communities are loaded as composable *bundles* — a view configuration, not a separate graph. The handoff document's `w3id.org` IRIs are illegal; the layer split is real and lives *under* the canonical authority as sub-namespaces. Operationalized by Story 3.5 (`core.ttl`, `crosswalk.csv`).

**The four layers:**

| Layer | Namespace / file | Loaded | Role |
|---|---|---|---|
| `core` | `…/ns/core#` — `ontology/core.ttl` | always | portable identity (name, logo, website, geoloc, address) + `core:relationships` |
| `mom` | `…/ns#` — `ontology/mom.ttl` | always | federation engine — `operationalState`, `endpointHealth`, `lastFetched`, `lastUpdated`, `memberOf`, `source` |
| concept commons | currently inside `mom.ttl` (`mom:ActivityScheme`); future own namespace | always (in the graph) | the SKOS concept graph `schema:knowsAbout` resolves into (CNC, 3D-printing…) — owned by nobody, traversable by everybody |
| community (`fab`/`omt`/`edu`/`agri`…) | future per-community `.ttl` | per `config.yaml` bundle | community vocabulary, fields, and CSS |

**Bundles are *view* configuration; the Oxigraph graph is universal.** A community map renders its bundle by default, but the graph holds every node. Bundle loading is analogous to `docker-compose` — the `config.yaml` composes which layers a given map surfaces; the underlying data is one shared graph.

**`schema:knowsAbout` is the concept pivot (the "wormhole hub").** Every community's specialised skill field — `fab:equipment`, `omt:treatmentFocus`, `edu:subjects` — aliases to `schema:knowsAbout` via `skos:closeMatch`. Because all of them resolve to the *same* concept IRIs, a query crossing two communities works with **zero coordination** between them: a dentist who never loaded `fab:` is still discoverable by a woodworker's "who does CNC near me" query. This is design for emergence.

**`crosswalk.csv` is a living bridge registry.** `ontology/crosswalk.csv` records, per concept, the predicate the pipeline actually emits, its SpaceAPI source, and the community fields that alias to it. It is **v1 and never "finished"** — new `skos:closeMatch` bridge rows are appended as cross-community overlaps are discovered. `scripts/validate_crosswalk.py` enforces the no-redefinition rule: an extension may alias a `core:`/`mom:` field but never redefine it.

**External concept anchors (candidates, not wired):** OpenKnowHow (OKH) and Wikidata are candidate external anchors for the concept commons — `owl:sameAs` / `skos:closeMatch` targets that would let MOM concepts align with vocabularies beyond the federation. Not implemented; noted for continuity.

**`mom.ttl` is currently impure** — it mixes the federation engine with makerspace activity concepts (`mom:ActivityScheme`). Extracting the activity scheme into a dedicated `fab.ttl` (or a standalone concept-commons namespace) is future work, tracked under the Epic 9 stub. Story 3.5 deliberately does **not** move it; `crosswalk.csv` labels those concepts "concept commons (shared layer)" so the future extraction does not mis-file them into `fab:`.

**Ontology-gap on-ramp.** `mom:OntologyGap` is declared in `mom.ttl` (added by Story 3.5). Today, unrecognised activity tags are logged to `gap_log.txt` as plain text by `transformer.py::_log_unmapped_tags` — no gap *triples* are emitted yet. Emitting `mom:OntologyGap` triples is deferred to **Story 6.3**. The gap log is intentionally the on-ramp for emergent community ontology (gap term → curation → concept minting → bridge discovery), not a janitorial dump.

**Sync model:** `ontology/mom.ttl` and `ontology/core.ttl` in this repo are the working copies. The maintainer manually syncs them to the `github.com/nicolasdb/mapsofmaking_ontology` repo (published via GitHub Pages). Ontology edits land in `ontology/` here first; nothing git-pushes to the ontology repo automatically.

---

### ADR-014: Backup Strategy — rsync for PoC, IPFS+IPLD Direction for Production

**Decision:** PoC uses host-level rsync/cron for daily N-Quads dumps. IPFS+IPLD is the production target but not implemented at PoC.

**What's actually at risk:** Not the space data (spaces republish from their own URLs). The provenance of aggregation — named graph snapshots showing when we saw what, diff history proving our ingestion pipeline's accuracy. This is the civic record that needs immutable archival.

**PoC backup (host cron):**
```bash
# /etc/cron.daily/backup-oxigraph
curl -s "http://localhost:7878/dump?format=application/n-quads" \
  > /var/backups/oxigraph/dump-$(date +%Y%m%d).nq
rsync -az /var/backups/oxigraph/ backup-user@backup-host:/backups/maps-of-making/
find /var/backups/oxigraph -name "*.nq" -mtime +7 -delete
```

**Production direction:** IPFS+IPLD for named graph snapshots (immutable CIDs). Solid pods as W3C alternative if IPFS operational overhead is too high at pilot. Decision deferred to pilot — requires real PoC telemetry on snapshot size and frequency.

---

### Epic 3.5 Transition State — Snapshot-as-Unit Model (2026-05-19 onwards)

**Decision:** Dual-pipeline transition from legacy `heartbeat_log` pipeline (noisy, independently-stamped columns) to clean snapshot-as-unit pipeline (payload + observed_at + UID = single source of truth).

**The new model:**
- Snapshot = {JSON payload + observed_at (UTC fetch instant) + space UID}
- One snapshot minted per successful fetch; every lifecycle fact derived from it, never re-stamped
- `observed_at` carried byte-identical through Oxigraph → minimal GeoJSON → browser (age = now − observed_at)

**Dual-pipeline approach:**
- **Clean path (Story 3.6):** New snapshot store (recommended SQLite table, keyed by UID) + clean transform + minimal canary GeoJSON → browser age display. Canary only; old pipeline untouched.
- **Legacy path (registered spaces, being migrated):** `heartbeat_log.db` + transformer + fat GeoJSON. Unchanged during 3.6. Stories 3.7–3.10 move each seam to the clean path and delete legacy code.
- **Isolation:** Different named graphs (`urn:mak:canary` vs `urn:mak:space/*`), different GeoJSON features. No shared mutable state except Oxigraph (read-only during transition).

**New snapshot store (ADR-017, pending):**
- Dedicated store, NOT columns on `heartbeat_log.db`
- Fields: UID, `observed_at` (UTC instant), JSON payload (TEXT/BLOB), etag, last_modified
- Keyed by space UID; one row per successful fetch (REPLACE on next fetch)
- Clean model: no derived columns (no `last_fetched`, `last_updated`, etc.)

**Why clean rebuild, not patch:**
- Legacy pipeline accumulated independently-stamped noise columns — the retro-3 bug class
- Grafting a clean token onto that foundation builds on noise
- Everything is on git; a rebuild is reversible; a patched-on-noise foundation is not
- Walking-skeleton discipline: Story 3.6 is a thin end-to-end slice of new clean code

**Stories 3.7–3.10 — Migration sequence:**
- 3.7: Fetch seam — registered spaces → clean snapshot store; 304/unreachable rules; delete `heartbeat_log` noise columns
- 3.8: Transform seam — read from snapshot; write `mom:observedAt`; delete transform-time stamping
- 3.9: Materializer seam — generalize to full graph; slim GeoJSON (render-critical only); fail-loud on missing token
- 3.10: Browser seam — lifecycle buckets; on-demand field loading from slimmed GeoJSON

**End state (after 3.10):** One pipeline, the clean one. `heartbeat_log.db` and legacy transformer code deleted.

---

## Core Architectural Decisions

### Decision Priority Analysis

**Critical (block implementation):**
- MOM ontology strategy — align-and-extend (decided)
- `@context` IRI stability — w3id.org + GitHub Pages (decided)
- IoP integration pattern — named graph + cached prompt slice (decided)
- Logging — structlog from day one (decided)

**Deferred (post-PoC):**
- CI/CD pipeline — manual deploy for PoC; GitHub Actions at pilot
- Advanced ontology governance — MOM namespace versioning strategy

### Data Architecture

**Oxigraph named graph structure:**

| Named graph | Owner | Contents |
|---|---|---|
| `<urn:mak:space/{id}>` | Heartbeat agent | Space triples (current version) |
| `<urn:mak:space/{id}/{date}>` | Heartbeat agent | Dated snapshots (append-only) |
| `<urn:mak:status>` | Scheduler job | Materialized status triples |
| `<urn:mak:presence>` | Webhook handler | Ephemeral open-now signals |
| `<urn:mak:notifications>` | Heartbeat agent | Pending notification queue |
| `<urn:mak:canary>` | Canary scenario tools (Story 3.3) | Synthetic "Mother Sands" space — isolated from real-space graphs |
| `<urn:mak:public_ledger>` | Ledger writer (future epic) | Append-only, immutable, IPFS/IPLD-anchored space life-events (registration, relocation, schema upgrade, `closed`, `dead`). Name + append-only principle locked 2026-05-16; event schema deferred. |
| `<urn:mak:snapshot/{id}>` | Clean snapshot pipeline (Story 3.6+) | Current snapshot (payload + observed_at + UID), replaced on each successful fetch. Clean alternative to `heartbeat_log.db` noise columns (legacy path being migrated). |
| `<urn:mak:ontology/iop>` | Init script | IoP ontology (read-only) |
| `<urn:mak:ontology/mom>` | Init script | MOM vocabulary (read-only) |

**MOM ontology strategy — align-and-extend:**
- Base: `schema:LocalBusiness`, `schema:openingHours`, `schema:geo` (Schema.org)
- Equipment/capabilities: `skos:closeMatch` to IoP classes — reference without hard dependency
- Maker-specific: `mom:NetworkMembership`, `mom:HostingCapacity`, `mom:SpaceType`, `mom:freshnessStatus`
- Canonical IRI: `https://w3id.org/maps-of-making/` (w3id.org registration) → redirects to GitHub Pages
- File lives in repo at `ontology/mom.ttl`, served via GitHub Pages, w3id.org as stable redirect

**IoP integration in Oxigraph:**
- Loaded at harness startup into `<urn:mak:ontology/iop>` via idempotent `ASK` check
- Full ontology stored, ~15-20% relevant subset extracted via SPARQL CONSTRUCT at init
- Subset serialized as compact text block, cached in memory, injected into every NL→SPARQL prompt
- `RELOAD_ONTOLOGY=1` env var forces reload on update
- Load command: `curl -X POST -H 'Content-Type: text/turtle' -G 'http://oxigraph:7878/store' --data-urlencode 'graph=urn:mak:ontology/iop' --data-binary @ontology/iop.ttl`

### Authentication & Security

| Surface | Auth method |
|---|---|
| Public map SPA | None — fully open |
| Public SPARQL query endpoint (`/sparql/query`) | None — read-only, rate-limited by nginx |
| SPARQL update endpoint (`/sparql/update`) | Blocked at nginx — internal Docker network only |
| Admin dashboard | Shared password, env-var secret (PoC); per-user accounts at pilot |
| Magic link tokens | Single-use, 72h TTL, signed |
| OpenRouter / Discord / Telegram tokens | `.env` file on VPS, never committed |

### API & Communication Patterns

**SPARQL endpoint routing (nginx):**
- `GET|POST /sparql/query` → `http://oxigraph:7878/query` (public)
- `POST /sparql/update` → `deny all` (internal Docker only)
- CORS: `Access-Control-Allow-Origin: *` on query endpoint (browser clients)

**Bot command response contract:**
- Defer immediately on all LLM-involved commands (`interaction.response.defer(thinking=True)`)
- On success: `interaction.followup.send(answer)`
- On LLM failure: user-facing — "I couldn't answer that, try rephrasing or browse the map directly"
- On LLM failure: internal — log structured event + write ontology gap triple to Oxigraph (FR41)
- Error responses always via `followup.send()` after defer — never `response.send_message()`

**SPARQL result binding normalisation:**
```python
# Always flatten SPARQL JSON bindings before passing to LLM tasks
[{k: v["value"] for k, v in row.items()} for row in data["results"]["bindings"]]
```

### Infrastructure & Deployment

**Deploy for PoC — manual:**
```bash
git pull
docker compose pull
docker compose up -d --build harness
```

No CI/CD pipeline for PoC. GitHub Actions at pilot stage.

**Secrets management:** `.env` file on VPS, gitignored. `.env.example` committed with placeholder values. All secret vars scoped to the services that need them.

**Backup:** Host cron daily, 7-day retention. Outside Docker — host-level cron calls `GET /dump?format=application/n-quads`.

---

## Implementation Patterns & Consistency Rules

### Naming Patterns

**RDF / Named graphs:** `urn:mak:{type}/{id}` — lowercase, colon-separated. Never use hash URIs for named graphs.

**MOM vocabulary predicates:** `mom:camelCase` for properties, `mom:PascalCase` for classes.
Examples: `mom:freshnessStatus`, `mom:NetworkMembership`, `mom:SpaceType`

**Python — harness files:** `snake_case` throughout. Module names match their task name exactly.
- `tasks/nl_to_sparql.py` not `tasks/nlToSparql.py`
- `adapters/discord_adapter.py` not `adapters/DiscordAdapter.py`

**Python — functions:** `async def verb_noun()` — verb first, noun second.
- `run_select()`, `run_update()`, `complete()`, `handle_ask()`

**Config keys:** `snake_case` in `config.yaml`. Match the Python variable they configure.

**Discord slash commands:** lowercase, underscore-separated. `/ask_map` not `/askMap`.

**Docker service names:** hyphen-separated, prefixed with `mak-` for maps-of-making services.
- `mak-harness`, `mak-oxigraph` — avoids collision with side project services.

### Structure Patterns

**One task = one file in `tasks/`.** No shared task logic files. If two tasks share utility code, it goes in a `utils/` module, not in either task file.

**Tests:** `tests/` directory at harness root, mirroring the module structure.
- `tests/tasks/test_nl_to_sparql.py` mirrors `tasks/nl_to_sparql.py`

**Config access:** Always via a single `config.py` module that loads `config.yaml` once. Tasks import from `config`, never load YAML directly.

### Format Patterns

**Structured logs — always via structlog, always with session context:**
```python
log = structlog.get_logger()
log = log.bind(session_id=sid, adapter="discord")
log.info("query.received", query=q)
log.error("sparql.generation_failed", error=str(e), raw_output=llm_output)
```
Log event names: `noun.verb_past` — `query.received`, `sparql.generated`, `dispatch.sent`

**LLM task return contract:** All tasks return `str`. No task returns a dict or structured object. Formatting is the task's responsibility.

**SPARQL strings:** Always defined as module-level constants with `SCREAMING_SNAKE_CASE` names.
```python
PENDING_NOTIFICATIONS_QUERY = """
SELECT ?id ?type ?contact ...
"""
```
Never build SPARQL strings with f-strings containing user input — always parameterise via `VALUES` clauses.

**Error ontology gap triples format:**
```turtle
<urn:mak:gap/{uuid}> a mom:OntologyGap ;
  mom:rawQuery "{escaped query text}" ;
  mom:rawLLMOutput "{escaped output}" ;
  mom:timestamp "{ISO datetime}"^^xsd:dateTime .
```

### Process Patterns

**Heartbeat idempotency:** Every write operation checks current state before writing. No blind overwrites. Use `ASK` queries before `INSERT`.

**Magic link token lifecycle:** Generate UUID → store hash in Oxigraph with TTL → validate on click → mark consumed immediately → reject any second click. Tokens never stored in plaintext.

**All agents MUST:**
- Import config from `config.py`, never load `config.yaml` directly
- Use `structlog` for all log output, never `print()`
- Bind `session_id` at request entry before any log calls
- Use `run_select()` / `run_update()` from `sparql_client.py` — never call Oxigraph HTTP directly
- Never build SPARQL with f-strings containing user or LLM-generated content
- Return `str` from all task functions
- Defer Discord interactions before any `await` that touches LLM or SPARQL

---

## Project Structure & Boundaries

### Complete Project Directory Structure

```
maps_of_making/
├── .env.example                         # required env vars documented
├── .gitignore                           # includes .env, harness/__pycache__
├── docker-compose.yml                   # Phase 2 full stack (name: maps_of_making)
│
├── web/                                 # Phase 1 SPA — unchanged
│   ├── maps-of-making.html              # main SPA entry point
│   ├── app.js                           # map logic, filters, drawers, embed
│   ├── test_embed.html                  # embed test harness
│   └── data/
│       ├── moms_seed.json               # bootstrap seed data (retire at pilot)
│       └── vow_workshops.json           # VOW seed data
│
├── admin.html                           # Phase 2 — admin landing page (auth-gated, served at /admin)
├── admin.js                             # fleet health, per-space drill-down (Story 4.0+)
│
├── ontology/                            # MOM vocabulary + IoP reference
│   ├── mom.ttl                          # MOM ontology (GitHub Pages hosted, w3id.org IRI)
│   ├── context/
│   │   └── space.jsonld                 # @context for space endpoint JSON-LD files
│   └── iop/
│       └── iop.ttl                      # IoP ontology snapshot (loaded into Oxigraph at init)
│
├── nanobot-config/                      # Nanobot agent configuration
│   └── config.json                      # channel adapters, LLM models, scheduling
│
├── data/
│   └── snapshots/                       # Raw pre-transformation JSON, one dir per space
│       └── {space_id}/
│           ├── latest.json              # most recent raw fetch (Zone 3 source + audit trail)
│           └── {timestamp}.json         # append-only archive (configurable retention)
│
├── tasks/                               # Custom task modules (invoked by Nanobot)
│   ├── heartbeat.py                     # Stage 1: fetch URL, conditional GET, write snapshot to disk
│   ├── ingest.py                        # Stage 2+3: SpaceAPI JSON → MOM JSON-LD → Oxigraph (ADR-015)
│   ├── nl_to_sparql.py                  # NL → SPARQL string (temp=0.0, Sonnet)
│   ├── answer_format.py                 # SPARQL result dict → plain language str
│   ├── notify_dispatch.py               # read queue, fill template, send, mark dispatched
│   ├── sparql_client.py                 # httpx async run_select() + run_update()
│   ├── magic_link.py                    # token generation, validation, single-use + TTL
│   ├── sparql/
│   │   ├── queries.py                   # SELECT query constants (SCREAMING_SNAKE_CASE)
│   │   └── updates.py                   # UPDATE/INSERT query constants
│   └── tests/
│       ├── test_heartbeat.py
│       ├── test_nl_to_sparql.py
│       ├── test_answer_format.py
│       ├── test_notify_dispatch.py
│       ├── test_sparql_client.py
│       └── test_magic_link.py
│
├── nginx/
│   └── maps-of-making.conf              # routes: SPA, /sparql/query, deny /sparql/update
│
├── scripts/
│   ├── load_ontology.sh                 # POST mom.ttl + iop.ttl to Oxigraph named graphs
│   ├── backup_oxigraph.sh               # daily N-Quads dump → /var/backups/oxigraph/
│   └── seed_import.py                   # moms_seed.json → JSON-LD → Oxigraph (⚪ seeded)
│
├── link_handler/                            # Phase 2 — magic link HTTP service (ADR-011)
│   ├── Dockerfile                           # python:3.12-slim, FastAPI
│   ├── requirements.txt
│   └── main.py                              # GET /claim/{token} → validate + SPARQL update
│
└── _bmad-output/planning-artifacts/
    ├── prd.md
    └── architecture.md
```

### Docker Compose — Full Service Topology

```yaml
name: maps_of_making

services:
  oxigraph:
    image: ghcr.io/oxigraph/oxigraph:latest
    command: ["--location", "/data", "--bind", "0.0.0.0:7878"]
    volumes: [oxigraph_data:/data, ./data/metrics.db:/data/metrics.db]
    expose: ["7878"]
    networks: [internal]

  mak-agent:                          # Nanobot agent (Discord + Telegram + tasks)
    image: hkuds/nanobot:latest
    environment:
      - OPENROUTER_API_KEY=${OPENROUTER_API_KEY}
      - OXIGRAPH_ENDPOINT=http://oxigraph:7878
    volumes:
      - ./nanobot-config:/root/.nanobot
      - ./tasks:/app/tasks
    depends_on: [oxigraph]
    networks: [internal]

  mak-link-handler:                   # magic link HTTP endpoint (ADR-011)
    build: ./link_handler
    expose: ["8000"]
    environment:
      - OXIGRAPH_ENDPOINT=http://oxigraph:7878
      - LINK_SECRET=${LINK_SECRET}
    depends_on: [oxigraph]
    networks: [internal]

volumes:
  oxigraph_data:

networks:
  internal:
    driver: bridge
```

**Nanobot integration:** CronService runs alongside chat adapters in the same container. Nanobot's supervisor ensures both systems survive crashes — heartbeat.md tasks execute on schedule even if Discord connection drops.

---

### Architectural Boundaries

| Boundary | Owner | Transport |
|---|---|---|
| SPA ↔ Oxigraph | SPA reads via nginx `/sparql/query` | SPARQL SELECT → GeoJSON |
| Harness ↔ Oxigraph | Direct `http://oxigraph:7878` (Docker network) | httpx async |
| Harness ↔ OpenRouter | `AsyncOpenAI(base_url=...)` | HTTPS |
| Harness ↔ Discord | `discord.py` WebSocket | Bot gateway |
| Harness ↔ Telegram | `python-telegram-bot` polling | HTTPS |
| Admin ↔ Oxigraph | Via nginx (shared-password auth) | SPARQL SELECT |
| Magic link ↔ link_handler | HTTP GET signed token | nginx → mak-link-handler:8000/claim/ |
| Scheduler ↔ Oxigraph | Direct Docker network | httpx async SPARQL UPDATE |
| Admin ↔ Scheduler metrics | Internal Docker network | REST GET /metrics JSON |
| Heartbeat ↔ Space endpoints | Direct HTTP GET (conditional, ETag) | httpx |

### Requirements to Structure Mapping

| FR group | Location |
|---|---|
| FR1–11 Map display, filters, search | `web/app.js` |
| FR12–14b Space detail drawer | `web/app.js` |
| FR15–18 Embed & sharing | `web/app.js` + nginx iframe headers |
| FR19–23 Coordinator registration | `tasks/heartbeat.py` + `link_handler/main.py` |
| FR24–27b Endpoint health / ingestion | `tasks/heartbeat.py` (fetch+compare) + `tasks/ingest.py` (transform) + `tasks/notify_dispatch.py` + `/data/snapshots/` (raw disk store) |
| FR28–33b Operator dashboard | `web/admin.html` + `web/admin.js` + FastAPI `/admin/api/status` endpoint in `infra/link_handler/main.py` |
| FR34–36 SPARQL federated query | Oxigraph service + nginx routing |
| FR37–42 NL bot | `harness/tasks/nl_to_sparql.py` + `harness/tasks/answer_format.py` + `harness/adapters/` |
| FR43–44 Auth | nginx (shared-password basic auth header) |

## External Schema References

### SpaceAPI Compatibility

Maps of Making aims for interoperability with the SpaceAPI ecosystem so that a hackerspace can register the same endpoint with both MoM and SpaceAPI-compatible services (e.g. [mapall.space](https://mapall.space/)).

**Authoritative schema:** https://github.com/SpaceApi/schema
- Current stable: `14.json` / `15.json`
- Active draft: `16-draft.json` (most detailed — use as design reference)
- Migration guide: `MIGRATION.md` in same repo

**SpaceAPI v14 required fields** (minimum a space endpoint must contain):
`api_compatibility`, `space` (name), `logo`, `url`, `location` (lat+lon), `contact`

**SpaceAPI v16 required fields** (draft): same core set; `location` demoted to optional (≥1 property required if present); `linked_spaces` added for federation.

**Key v16 additions relevant to MoM:**
- `linked_spaces[]` — array of related spaces with `endpoint` or `website` URL → maps to consortium/network membership
- `membership_plans[]` — pricing/access tiers → useful for long-term membership discovery ("I want to join a space near me") and newcomer onboarding queries; residency matchmaking is separate (EU-grant-financed programs, not membership subscriptions) and lives in `mom:extended`
- `location.areas[]` — named zones with `square_meters` → equipment/workshop areas
- `state.lastchange` — Unix timestamp of last open/closed change → freshness signal (Epic 7)
- `spacefed.spacenet` / `spacefed.spacesaml` — federation auth → long-term interop

**SpaceAPI has no native tags/specialties/equipment fields.** These are MoM extensions and must live in `mom:extended` subset. When publishing alongside SpaceAPI fields, extra JSON-LD properties are allowed by SpaceAPI validators — no breakage.

**MoM schema subset model** (enforced via Pydantic in `link_handler/main.py` from Story 2.7):

| Subset | Fields | Gate behaviour | Unlocks |
|---|---|---|---|
| `mom:required` | `space`, `url`, `location.lat/lon` | Hard reject if missing | Pin on map |
| `mom:card` | `+location.address`, `contact.website`, `state.open`, `schema:openingHours` | Ingest with warning if missing | Full detail card |
| `spaceapi:compatible` | Full SpaceAPI v14+ field set | Ingest; surface compatibility score | Interop with mapall.space etc. |
| `mom:extended` | `mom:specialties`, `mom:equipment`, `mom:consortium`, `mom:residency`, `mom:membershipPlans` | Ingest; unlock advanced features | Consortium queries, residency matchmaking, membership discovery |
| `mom:live` | `state.open` + presence webhook TTL | Epic 7 — schema slot reserved | "Open now" badge |

**Progressive unlock UX (Story 2.7):** After ingestion, the validation response tells the coordinator which subset they've reached and what completing the next subset unlocks — fog-of-war incentive to enrich their endpoint over time.

**`mom:extended` field definitions** (agreed 2026-04-27 — implemented from Epic 4+):

```json
"legal": { "type": "non-profit", "country": "BE", "founded": 2011 },
"outward": {
  "grant_experience": ["Erasmus+ KA210", "NLnet NGI"],
  "partnership_scale": ["local", "national", "european"],
  "working_languages": ["fr", "en", "nl"],
  "thematic_areas": ["education", "neurodiversity", "open-hardware"],
  "seeking_partners": true,
  "grant_programme": "Erasmus+ KA220",
  "seeking_description": "digital fabrication + youth, 2027 call"
},
"inward": {
  "residency_open": true,
  "residency_duration_weeks": { "min": 2, "max": 8 },
  "residency_support": ["workspace", "materials"],
  "residency_deadline": "2026-09-01",
  "residency_profile": "Makers with textile or biofab background"
}
```

Note: `seeking_partners_for` is split into structured `grant_programme` + free `seeking_description` for queryability. `residency` ≠ `membership_plans` (SpaceAPI): residency is project-based/EU-grant-funded; membership is local subscription/newcomer discovery. The maker schema (consent-gated individual layer) is future scope — see memory file for full field definitions.

**Conceptual model:** Cell (maker) → Organ (space) → Organism (network) → Ecosystem (network of networks). Space schema = organ's public signal. Maker schema = cell's consented output. Nobody owns the cell.

**Success metric:** A hackerspace registers one JSON endpoint and appears correctly on Maps of Making AND mapall.space AND any future SpaceAPI-compatible service. One endpoint, multiple maps, multiple publics.

---

### Data Flow

```
Space publishes SpaceAPI JSON at their URL
  ↓ (scheduled heartbeat, conditional GET — ETag/Last-Modified)
tasks/heartbeat.py — STAGE 1: FETCH
  → raw JSON written to /data/snapshots/{id}/latest.json (with timestamp)
  → normalize payload (strip ephemeral timestamps, sort arrays)
  → compare with stored snapshot
  → if UNCHANGED: update timestamp only, log "no_change", STOP
  → if CHANGED: proceed to Stage 2

tasks/ingest.py — STAGE 2: TRANSFORM  (ADR-015)
  → SpaceAPI JSON → MOM JSON-LD (ontology applied, field-by-field mapping)
  → validate against mom:required subset (hard reject if missing)
  → validate against mom:card / mom:extended subsets (warn + log if missing)

tasks/heartbeat.py — STAGE 3: INGEST
  → SPARQL UPDATE → <urn:mak:space/{id}> (current triples)
  → SPARQL UPDATE → <urn:mak:space/{id}/{date}> (append-only snapshot)
  → SPARQL UPDATE → <urn:mak:status> (mom:operationalState = "confirmed" + mom:confirmedAt)
  → log decision: "ingested" with diff summary

  ↓ (if stale/error threshold crossed)
tasks/notify_dispatch.py
  → read <urn:mak:notifications>
  → fill template + generate magic link token
  → send email / Discord DM
  ↓ (on magic link YES click)
link_handler/main.py
  → validate token (single-use, 72h TTL)
  → SPARQL UPDATE reset timer → mom:operationalState "confirmed"

User query in Discord channel
  ↓
adapters/discord_adapter.py
  → defer(thinking=True)
  → tasks/nl_to_sparql.py (OpenRouter Sonnet, temp=0)
  → sparql_client.run_select(sparql)
  → tasks/answer_format.py (OpenRouter Minimax)
  → followup.send(answer)

Operator opens /admin dashboard
  ↓
admin.js → FastAPI /admin/api/status
  → Oxigraph ping (ASK {}) → health pill: Oxigraph LIVE/DOWN
  → ingestion heartbeat file mtime → health pill: Ingestion RUNNING/IDLE(Nh)
  → SELECT on <urn:mak:status> → spaces reachable count + registry table
  → operator clicks space row → inspection panel:
      col 1: read /data/snapshots/{id}/latest.json (raw fetch, from disk)
      col 2: SPARQL DESCRIBE <urn:mak:space/{id}> (ingested triples)
      col 3: card display fields query (what public map renders)

Network coordinator opens public map
  ↓
web/app.js → Tweaks panel health map toggle
  → SELECT on mom:operationalState aging/zombie/dead (overlay layer)
  → pin colour reflects freshness lifecycle — no auth, no admin access
```
