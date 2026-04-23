---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-04-22'
inputDocuments: ['_bmad-output/planning-artifacts/prd.md', '_bmad-output/planning-artifacts/next-session.md', 'archive/docs/architecture/architecture.md', 'archive/docs/project-overview.md', 'archive/docs/index.md']
workflowType: 'architecture'
project_name: 'maps_of_making'
user_name: 'nicolas'
date: '2026-04-22'
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

1. **Space managers** — submit one JSON endpoint URL, see their pin flip ⚪→🔵, get nudged if their endpoint goes stale
2. **Network admins** — fleet health dashboard, identify aging/broken spaces, dispatch nudges, export stats
3. **Makers (secondary)** — browse confirmed spaces, use bot queries in their community channel

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

**Freshness lifecycle (unclaimed seeds only):**

```
⚪ seeded → [30d no claim] → aging → [90d] → zombie → [180d] → 💀 dead
```

Dead seeds: removed from default map view, retained in Oxigraph for admin query and historical record.

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

**Decision:** Materialized status triples written by a scheduled job. Not computed at query time.

**Status graph structure:**
```turtle
<seed:xyz> mak:healthStatus [
  mak:visibility "public" ;          # ⚪🔵🟢🔴 — always rendered
  mak:operationalState "aging" ;     # admin toggle layer
  mak:lastChecked "2026-04-22T..."^^xsd:dateTime ;
  mak:consecutiveFailures 3 ;
] .
```

**Status lifecycle (written by scheduler):**

| Status | Written by | Trigger |
|---|---|---|
| `mak:seeded` | Seed ingest | moms_seed.json import |
| `mak:confirmed` | Heartbeat agent | First successful JSON-LD fetch |
| `mak:aging` | Scheduler | 30d no fetch |
| `mak:zombie` | Scheduler | 90d no fetch |
| `mak:dead` | Scheduler | 180d no fetch |
| `mak:error` | Heartbeat agent | HTTP error / timeout |

**Map queries:** Base query filters on `mak:visibility = "public"`. Admin toggle fires a second SPARQL query overlaying `mak:operationalState` for aging/zombie/dead — no page reload, no separate endpoint.

**Scheduler:** Single cron job every 6h, Python script against Oxigraph SPARQL update endpoint. Idempotent — only writes on status change. No new infrastructure.

**Seed→claim transition:** On first successful fetch of a self-hosted JSON-LD, heartbeat agent overwrites seed triples in the space's named graph, sets `mak:confirmed`. Seed triples tagged `mak:source mak:seed` — preserved one cycle as diff baseline, then dropped.

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
├── admin/                               # Phase 2 — admin dashboard
│   ├── index.html                       # auth-gated, separate subdomain
│   └── admin.js                         # fleet health, per-space drill-down
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
├── tasks/                               # Custom task modules (invoked by Nanobot)
│   ├── heartbeat.py                     # fetch URL, diff JSON-LD, write triples (invoked by HEARTBEAT.md)
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
| FR19–23 Coordinator registration | `harness/tasks/heartbeat.py` + `harness/magic_link.py` |
| FR24–27b Endpoint health / ingestion | `harness/tasks/heartbeat.py` + `harness/tasks/notify_dispatch.py` |
| FR28–33b Admin dashboard | `admin/` |
| FR34–36 SPARQL federated query | Oxigraph service + nginx routing |
| FR37–42 NL bot | `harness/tasks/nl_to_sparql.py` + `harness/tasks/answer_format.py` + `harness/adapters/` |
| FR43–44 Auth | nginx (shared-password basic auth header) |

### Data Flow

```
Space publishes JSON-LD at URL
  ↓ (scheduled heartbeat, conditional GET)
harness/tasks/heartbeat.py
  → diff against stored snapshot
  → SPARQL UPDATE → <urn:mak:space/{id}> named graph
  → SPARQL UPDATE → <urn:mak:status> (mak:confirmed)
  ↓ (if stale/error)
harness/tasks/notify_dispatch.py
  → read <urn:mak:notifications>
  → fill template + generate magic link token
  → send email / Discord DM
  ↓ (on magic link YES click)
harness/magic_link.py
  → validate token (single-use, 72h TTL)
  → SPARQL UPDATE reset timer → mak:confirmed

User query in Discord channel
  ↓
harness/adapters/discord_adapter.py
  → defer(thinking=True)
  → harness/tasks/nl_to_sparql.py (OpenRouter Sonnet, temp=0)
  → sparql_client.run_select(sparql)
  → harness/tasks/answer_format.py (OpenRouter Minimax)
  → followup.send(answer)

Admin opens dashboard
  ↓
admin/admin.js → nginx /sparql/query
  → SELECT on <urn:mak:status> — fleet health overview
  → toggle ON → SELECT on mak:operationalState aging/zombie/dead
```
