# Story 1.1: Integration Dependency Spike

**Status:** ready-for-dev
**Epic:** 1 — Federated Backend Foundation
**Story Key:** 1-1-integration-dependency-spike
**Created:** 2026-04-24

---

## User Story

As a developer,
I want a single `/ping` slash command that chains Discord → OpenRouter LLM call → Oxigraph health check and logs each leg's result,
So that all three external dependencies are proven reachable before any feature work begins — and failures are surfaced early with clear diagnostics.

---

## Tasks/Subtasks

- [ ] **Task 1: One-time Discord Developer Portal setup**
  - [ ] Create application `maps-of-making-bot`
  - [ ] Enable bot, copy token to `.env` as `DISCORD_BOT_TOKEN`
  - [ ] OAuth2 URL with `bot` + `applications.commands` scopes, `Send Messages` + `Use Slash Commands` permissions, invite to Openfab server
  - [ ] Disable "Public Bot"

- [ ] **Task 2: Create `harness/` directory structure**
  - [ ] `harness/main.py`
  - [ ] `harness/llm_client.py`
  - [ ] `harness/sparql_client.py`
  - [ ] `harness/requirements.txt`
  - [ ] `.env.example` at project root (or update existing one)

- [ ] **Task 3: Implement `sparql_client.py`**
  - [ ] `run_ask()` async function using httpx
  - [ ] Health check query with PREFIX declarations
  - [ ] Test against localhost:7878

- [ ] **Task 4: Implement `llm_client.py`**
  - [ ] `complete()` async function using AsyncOpenAI → OpenRouter
  - [ ] Returns string, logs latency

- [ ] **Task 5: Implement `main.py`**
  - [ ] Discord bot connects, logs "ready" via structlog
  - [ ] `/ping` slash command: defer → LLM call → SPARQL health check → structured response
  - [ ] `tree.sync()` in `setup_hook` (not on every message)
  - [ ] structlog with session_id bound at interaction entry

- [ ] **Task 6: Verify end-to-end**
  - [ ] `/ping` returns ✓/✗ for all three legs in Discord
  - [ ] Failures show plain-language error (no stack trace to user)
  - [ ] All three legs logged via structlog with session_id

---

## Acceptance Criteria

**Given** the one-time Discord Developer Portal setup is done (see Task 1) and `.env` contains `DISCORD_BOT_TOKEN`, `OPENROUTER_API_KEY`, `OXIGRAPH_ENDPOINT`

**When** `python harness/main.py` is run and a developer types `/ping` in the configured Openfab Discord channel

**Then** the bot defers (`thinking=True`), calls OpenRouter (one completion, any model), queries Oxigraph health endpoint (`ASK { ?s ?p ?o }`)

**And** responds with a structured message showing each leg:
```
✓ Discord auth
✓ OpenRouter — model: <name>, latency: <ms>ms
✓ Oxigraph — latency: <ms>ms
```

**And** if any leg fails, the error is logged via `structlog` with `session_id` bound and a plain-language failure message shown in Discord (no stack trace to user)

**And** slash commands are synced via `tree.sync()` in `setup_hook` only

**And** all three files follow AR-CONV1 naming (`snake_case`, `verb_noun()`) and AR-CONV2 logging (`structlog`, event `noun.verb_past`)

**And** the spike is marked done in sprint-status before any Epic 1 story beyond 1.2 is started

---

## Technical Requirements

### File Structure to Create

```
harness/
├── main.py              # Discord bot + /ping command
├── llm_client.py        # AsyncOpenAI → OpenRouter
├── sparql_client.py     # httpx async SPARQL health check
└── requirements.txt     # discord.py, openai, httpx, structlog
```

This is the spike scope. **Do NOT create** `tasks/`, `adapters/`, `config.py`, or any other harness files — those belong to subsequent Epic 1 stories.

### `sparql_client.py` — CRITICAL: Always include PREFIX declarations

**Every** SPARQL query must include PREFIX declarations. This bit us in Story 0.3 — Oxigraph returns `400 Bad Request` on any prefixed name without a declared PREFIX. The health check query uses no prefixes, so it's safe, but establish the pattern now:

```python
import httpx, time, structlog

log = structlog.get_logger()

OXIGRAPH_ENDPOINT = ""  # set from env in main.py

HEALTH_ASK = """ASK { ?s ?p ?o }"""

async def run_ask(query: str) -> tuple[bool, int]:
    """Run a SPARQL ASK query. Returns (boolean_result, latency_ms)."""
    t0 = time.monotonic()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{OXIGRAPH_ENDPOINT}/query",
            content=query,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
    latency = int((time.monotonic() - t0) * 1000)
    return resp.json()["boolean"], latency
```

**Do NOT use** SPARQLWrapper (sync-only). **Do NOT use** `requests`.

### `llm_client.py`

```python
from openai import AsyncOpenAI
import os, time, structlog

log = structlog.get_logger()

async def complete(prompt: str) -> tuple[str, str, int]:
    """One LLM completion via OpenRouter. Returns (text, model_used, latency_ms)."""
    client = AsyncOpenAI(
        api_key=os.environ["OPENROUTER_API_KEY"],
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://mapofmaking.debarquin.eu",
            "X-Title": "maps-of-making spike",
        },
    )
    t0 = time.monotonic()
    resp = await client.chat.completions.create(
        model="anthropic/claude-haiku-4-5",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=64,
    )
    latency = int((time.monotonic() - t0) * 1000)
    text = resp.choices[0].message.content or ""
    return text, resp.model, latency
```

### `main.py` — Discord bot with defer pattern

```python
import asyncio, os
import discord
from discord.ext import commands
import structlog
import llm_client, sparql_client

log = structlog.get_logger()

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def setup_hook():
    await bot.tree.sync()
    log.info("bot.synced")

@bot.event
async def on_ready():
    log.info("bot.ready", user=str(bot.user))

@bot.tree.command(name="ping", description="Check Discord, OpenRouter, and Oxigraph reachability")
async def ping(interaction: discord.Interaction):
    sid = str(interaction.id)
    bound = log.bind(session_id=sid, adapter="discord")
    await interaction.response.defer(thinking=True)
    bound.info("ping.received")

    lines = []

    # Discord leg: if we got here, it's up
    lines.append("✓ Discord auth")

    # OpenRouter leg
    try:
        _, model, latency = await llm_client.complete("reply with one word: ok")
        lines.append(f"✓ OpenRouter — model: {model}, latency: {latency}ms")
        bound.info("llm.checked", model=model, latency_ms=latency)
    except Exception as e:
        lines.append(f"✗ OpenRouter — {type(e).__name__}: check OPENROUTER_API_KEY")
        bound.error("llm.failed", error=str(e))

    # Oxigraph leg
    try:
        result, latency = await sparql_client.run_ask(sparql_client.HEALTH_ASK)
        lines.append(f"✓ Oxigraph — latency: {latency}ms")
        bound.info("sparql.checked", latency_ms=latency, result=result)
    except Exception as e:
        lines.append(f"✗ Oxigraph — {type(e).__name__}: check OXIGRAPH_ENDPOINT")
        bound.error("sparql.failed", error=str(e))

    await interaction.followup.send("\n".join(lines))

if __name__ == "__main__":
    sparql_client.OXIGRAPH_ENDPOINT = os.environ.get("OXIGRAPH_ENDPOINT", "http://localhost:7878")
    bot.run(os.environ["DISCORD_BOT_TOKEN"])
```

### `requirements.txt` for harness

```
discord.py>=2.3.0
openai>=1.30.0
httpx>=0.27.0
structlog>=24.0.0
```

### `.env.example` — add these keys (do not break existing keys if file exists)

```
DISCORD_BOT_TOKEN=your-bot-token-here
OPENROUTER_API_KEY=your-openrouter-key-here
OXIGRAPH_ENDPOINT=http://localhost:7878
```

---

## Architecture Compliance

### Framework clarification: custom spike now, Nanobot in Story 1.3

**Story 1.1 uses a custom 3-file harness** (discord.py + AsyncOpenAI + httpx). This is correct.

**ADR-013** specifies Nanobot as the production agent framework — this applies from Story 1.3 onward when the Docker Compose stack is assembled. Nanobot adds scheduling (CronService + HEARTBEAT.md), multi-channel adapters, and LiteLLM provider over OpenRouter. Story 1.1 is a pure dependency spike that proves auth before building the stack.

Do NOT add Nanobot to this story. Do NOT create a `Dockerfile` or Docker Compose changes here.

### Existing `infra/docker-compose.yml` — do NOT touch

The existing `infra/docker-compose.yml` is Phase 1 (maps-nginx + oxigraph). Phase 2 additions (`mak-agent`, `mak-link-handler`, nginx routing updates, renamed services per `mak-` prefix convention) happen in Story 1.3. Do not modify `infra/docker-compose.yml` in this story.

### Naming conventions (AR-CONV1, AR-CONV2)

- Python files: `snake_case`
- Functions: `async def verb_noun()` — `run_ask()`, `complete()`
- structlog events: `noun.verb_past` — `bot.ready`, `ping.received`, `llm.checked`, `sparql.failed`
- session_id bound at interaction entry, before any log calls

### Discord defer pattern (AR-AGT4) — mandatory

`await interaction.response.defer(thinking=True)` must be the FIRST thing in any slash command that calls LLM or SPARQL. The Discord 3s timeout is absolute. Error responses must go through `followup.send()`, never `response.send_message()`.

---

## Epic 0 → Epic 1 Handoffs (Critical Context)

These are lessons learned from Epic 0 that directly impact this story and all of Epic 1:

### 1. SPARQL PREFIX declarations are mandatory

**Source:** Story 0.3 code review (commit 7b1c82e)
Oxigraph returns `400 Bad Request` for any SPARQL query using prefixed names (`mom:`, `schema:`, `mak:`) without PREFIX declarations. This was caught only during live testing against a real Oxigraph — unit tests with mocked HTTP never surfaced it.

**In this story:** The health check ASK uses no prefixes so it's fine. But `sparql_client.py` must establish the correct pattern for future stories: include PREFIX block in every query constant.

**Confirmed SPARQL namespaces (from live Oxigraph at localhost:7878):**
```sparql
PREFIX mom: <https://mapsofmaking.eu/ns#>
PREFIX mak: <https://mapsofmaking.eu/resource/>
PREFIX schema: <https://schema.org/>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
```

### 2. Integration tests catch what unit tests miss

**Source:** Story 0.3 code review
Mock-heavy unit tests passed 100% but masked the SPARQL syntax bug. Add a comment in tests noting which bugs can only be caught against a real Oxigraph (this is documented in code-review for later integration test stories).

### 3. Live Oxigraph data is already loaded

567 named graphs are loaded in the localhost:7878 Oxigraph instance:
- 566 VOW spaces in `<urn:mak:space/{id}>` named graphs
- 1 shared RFF graph `<urn:mak:mock/rff-health>` (40 entries)

The `HEALTH_ASK` (`ASK { ?s ?p ?o }`) will return `true` against this instance. This is the expected result.

### 4. Local dev isolation (distrobox + Podman)

Start Oxigraph locally with:
```bash
distrobox-host-exec podman compose -f infra/docker-compose.yml up -d oxigraph
```

Oxigraph is then accessible at `http://localhost:7878` from inside the distrobox. Do NOT run this command inside the harness script.

### 5. `--force` RFF reload bug (outstanding, non-blocking)

`seed_import.py --force` duplicates triples on repeated runs (no CLEAR GRAPH before reload). Not blocking this story. Tracked for a future cleanup.

### 6. `venv` is managed externally

The user activates `venv` before running Python commands. Do not create `scripts/venv/` or `harness/venv/`. The harness requirements.txt will be installed into the existing venv.

---

## Definition of Done

- [ ] `harness/main.py`, `harness/llm_client.py`, `harness/sparql_client.py` exist
- [ ] `harness/requirements.txt` lists all deps
- [ ] `.env.example` documents all three required env vars
- [ ] `/ping` command returns ✓/✗ for Discord, OpenRouter, and Oxigraph in Discord
- [ ] Failures show plain-language message to user (no stack trace)
- [ ] All events logged via structlog with session_id
- [ ] `tree.sync()` called only in `setup_hook`
- [ ] Naming follows AR-CONV1 (snake_case, verb_noun)
- [ ] Spike verified working in Openfab Discord before Epic 1 proceeds past 1.2

---

## File List

- `harness/main.py` (NEW)
- `harness/llm_client.py` (NEW)
- `harness/sparql_client.py` (NEW)
- `harness/requirements.txt` (NEW)
- `.env.example` (NEW or MODIFIED — add Discord/OpenRouter/Oxigraph keys)

---

## Out of Scope

- Nanobot integration (Story 1.3)
- Docker Compose changes (Story 1.3)
- `harness/tasks/`, `harness/adapters/`, `harness/config.py` (Story 1.3+)
- nginx routing changes (Story 1.3)
- MOM ontology loading (Story 1.4)
- GeoJSON materialization (Story 1.5)
- Any command other than `/ping`
- Unit tests for the spike (no value — needs live Discord/OpenRouter/Oxigraph; integration test IS the test)

---

## Change Log

- 2026-04-24: Story created
