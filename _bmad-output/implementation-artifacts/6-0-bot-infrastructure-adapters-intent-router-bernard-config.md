# Story 6.0: Bot Infrastructure — Adapters, Intent Router, Bernard Config

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As the MOM operator,
I want a channel-agnostic bot core with a platform adapter and an intent router,
so that every later Epic 6 skillset plugs into one transport-independent spine with one Bernard voice.

## Acceptance Criteria

> Source: epics.md §"Story 6.0" (lines 1699–1721); ADR-017 (architecture.md §477); handoff 2026-06-16 §"Story 6.0".

1. The `harness/` baseline runs cleanly first — **verify drift from the Epic 1 spike before extending** (the spike currently uses Discord + `minimax/minimax-m2.1`, not Matrix + Gemma; see Dev Notes).
2. A new `mak-agent-bot` Docker Compose service is added that joins the existing internal network using `expose`, **not** `ports` (read-only-to-the-outside; internal traffic only). See Dev Notes for the network-name reconciliation.
3. A `Message` dataclass exists with exactly these fields: `text`, `user_id`, `room_id`, `platform`, `raw`.
4. A `ChannelAdapter` protocol is defined with `async receive() -> Message` and `async send(response, context) -> None`.
5. A Matrix adapter is implemented via `matrix-nio` (async Python — fits the existing httpx/async stack).
6. An intent classifier makes **one compact LLM call** (~200-token context) returning exactly one of `write | query | nl_discovery | unknown`. A first pass MAY return a hardcoded `unknown`; the LLM wiring is the second pass (both must land in this story).
7. `config.yaml` gains `bot.model`, `bot.platform_tokens`, `bot.matrix_homeserver`, and the Bernard voice config is loaded at startup.
8. `!mom ping` is the smoke test: the classifier returns `unknown` and Bernard acknowledges gracefully (no raw error/status code — see voice rules).
9. The classifier result is logged via `structlog` with `session_id` bound.

**Done gate (operator confirmation):** `!mom ping` in the Openfab Matrix room returns a Bernard-voice response within 5 s.

## Tasks / Subtasks

- [x] **Task 1 — Baseline drift check & package layout** (AC: 1)
  - [x] Run/inspect the current `harness/` (Discord ping spike) and confirm `llm_client.complete()` and `sparql_client.run_ask()` still work against OpenRouter + Oxigraph.
  - [x] Decide module layout under `harness/` (the spine extends this dir per ADR-017; do **not** create a new top-level package or introduce Nanobot).
  - [x] Note the `minimax/minimax-m2.1` → Gemma 4 12B model swap (AC 7 config drives it) and the Discord-import drift in the Dev Agent Record.

- [x] **Task 2 — Core seam: `Message` + `ChannelAdapter`** (AC: 3, 4)
  - [x] Add `Message` dataclass (`text`, `user_id`, `room_id`, `platform`, `raw`).
  - [x] Define `ChannelAdapter` protocol (`async receive() -> Message`, `async send(response, context) -> None`). The skill chain must never see the transport.

- [x] **Task 3 — Matrix adapter** (AC: 5)
  - [x] Implement a `matrix-nio` adapter conforming to `ChannelAdapter`; sync-loop → normalise each room message to `Message(platform="matrix", raw=<nio event>)`.
  - [x] `send()` posts platform-aware markdown back to `room_id`.

- [x] **Task 4 — Intent classifier** (AC: 6, 9)
  - [x] First pass: hardcoded `unknown` router so `!mom ping` works end-to-end.
  - [x] Second pass: one compact LLM call (~200-token system prompt) returning exactly one token of `write | query | nl_discovery | unknown`; reuse the `harness/llm_client.py` LiteLLM-over-OpenRouter pattern.
  - [x] Bind `session_id` on a structlog logger and log the classifier result.

- [x] **Task 5 — Config + Bernard voice loading** (AC: 7)
  - [x] Add `bot.model`, `bot.platform_tokens`, `bot.matrix_homeserver` to `config.yaml` (mirror `infra/link_handler/config.yaml` loading style).
  - [x] Load Bernard voice config at startup (the voice rules are 6.5 ACs; here we only need the graceful-acknowledge path for `!mom ping`).

- [x] **Task 6 — `!mom ping` smoke command + skill router stub** (AC: 8)
  - [x] Wire `Message` → classifier → router; `!mom ping` routes to `unknown` and returns a Bernard-voice acknowledgement (no raw error/status code).

- [x] **Task 7 — Containerise & compose service** (AC: 2)
  - [x] Add `harness/Dockerfile` (mirror `infra/link_handler/Dockerfile`: `python:3.12-slim`, pip from `requirements.txt`).
  - [x] Add `mak-agent-bot` to `infra/docker-compose.yml` on the internal network, `expose` not `ports`, `OXIGRAPH_ENDPOINT=http://oxigraph:7878`, `depends_on: oxigraph`, env for Matrix + OpenRouter tokens.
  - [x] Add new deps to `harness/requirements.txt`: `matrix-nio`, `pyyaml` (config), keep `openai`, `httpx`, `structlog`, `python-dotenv`. Drop/keep `discord.py` only if Discord stays (6.6 re-adds it).

- [x] **Task 8 — Done gate** (AC: all)
  - [x] Operator confirmation: `!mom ping` in a real Matrix room returns a Bernard-voice response within 5 s. — **CONFIRMED live, 2026-06-16.** Self-hosted Dendrite homeserver stood up (`@bernard:mapsofmaking.org`); `!mom ping` sent from a second test account, bot received it via real `sync_forever()`, classified `unknown`, and Bernard's ack landed back in the room — round trip ~1-2s. See Completion Notes for the homeserver build and two bugs fixed along the way.

## Dev Notes

### What this story is (and is NOT)
- **IS:** the transport-independent spine — `Message` → adapter → intent classifier → skill router → Bernard-voice formatter → adapter. Only the `unknown`/`ping` path needs to fully resolve here.
- **IS NOT:** any write path (6.1/6.2), any real query/SPARQL template (6.3), any NL→SPARQL (6.4), or the full voice audit (6.5). Write **functional** responses now; polish voice in 6.5. Do **not** introduce Nanobot or a new orchestrator (ADR-017: deferred to 6.4). [Source: architecture.md#ADR-017; epics.md Epic 6 preamble lines 1693]

### Existing code being extended (READ FIRST)
- `harness/main.py` — **Discord** ping spike: `commands.Bot`, a `/ping` slash command that chains `llm_client.complete()` + `sparql_client.run_ask()`, binds `session_id`+`adapter` on structlog. This is the pattern to generalise; Discord becomes *one* adapter (re-added in 6.6), Matrix is the new primary. Note top-level imports (`import llm_client`) — not package-relative.
- `harness/llm_client.py` — `async complete(prompt) -> (text, model, latency_ms)` via `AsyncOpenAI` over `https://openrouter.ai/api/v1`. **Drift to fix:** model is hardcoded `minimax/minimax-m2.1`; AC 7 moves the model to `config.yaml` (`bot.model` = Gemma 4 12B, Haiku fallback). `max_tokens=64` is fine for classification but parameterise for formatting.
- `harness/sparql_client.py` — `async run_ask(query) -> (bool, latency_ms)`; `OXIGRAPH_ENDPOINT` set from env in `main.py`; `HEALTH_ASK = "ASK { ?s ?p ?o }"`. Read-only — the bot **never** writes triples (NFR-S7).
- `harness/requirements.txt` — `discord.py`, `openai`, `httpx`, `structlog`, `python-dotenv`. Add `matrix-nio` (only truly-new dep for 6.0) + `pyyaml`.

### Model policy (hard constraint)
Gemma 4 12B via OpenRouter for classification + formatting (slot-filling, not reasoning; **Haiku acceptable fallback**). Do NOT use a heavier model for routing/formatting. Sonnet (`temperature=0.0`) is reserved for NL→SPARQL in 6.4 only. [Source: architecture.md#ADR-017 "Models"; handoff §LLM]

### Compose / network reconciliation (RESOLVED — AC 2 wording is a Nanobot-era leftover)
The AC/handoff say join `maps_of_making_internal` with `external: true`. **Traced:** that is the *same* network as the `internal:` declared in `infra/docker-compose.yml`. The file sets `name: maps_of_making` (line 1) and declares `internal: {driver: bridge}` (lines 108–109); Compose prefixes the project name, so at runtime `internal` *is* `maps_of_making_internal`. The literal `maps_of_making_internal` appears exactly once in the repo — line 56, the **commented-out Nanobot block**, describing Nanobot as a *separate compose project* joining from outside via `external: true`.

**Therefore for this story:** `mak-agent-bot` is a service **inside the main `maps_of_making` compose project** (ADR-017 folded the bot into `harness/`; no separate Nanobot project), so it joins `networks: [internal]` — **do NOT use `external: true`** (that form is only for a process in a *different* compose project). Mirror `mak-link-handler` exactly: `networks: [internal]`, `expose` not `ports`, `OXIGRAPH_ENDPOINT=http://oxigraph:7878`, `depends_on: oxigraph: {condition: service_started}`, `restart: unless-stopped`. Sit beside / replace the commented-out `mak-agent` block (the placement hint). For local Fedora/Podman, `docker-compose.dev.yml` overrides the gateway network — the bot only needs `internal`, which works in both. [Source: infra/docker-compose.yml lines 1, 56, 105–109; infra/docker-compose.dev.yml lines 38–40]

### Dockerfile
Mirror `infra/link_handler/Dockerfile` (`python:3.12-slim`, `WORKDIR /app`, copy + `pip install -r requirements.txt`, `COPY . .`). Entry `CMD` runs the bot's async main (not uvicorn — this is a long-running sync-loop client, not an HTTP server, so no `EXPOSE`/port needed). `curl` is absent from slim images — if a healthcheck is added, use `python3 -c` (urllib) per project convention.

### Config loading
Mirror `infra/link_handler/config.yaml` + its loader style. New keys:
```yaml
bot:
  model: google/gemma-...        # OpenRouter id for Gemma 4 12B; Haiku fallback
  matrix_homeserver: https://matrix.org   # or the Openfab homeserver
  platform_tokens: {}            # matrix access token / device id; read from env, not committed
```
Secrets (Matrix access token, `OPENROUTER_API_KEY`) come from env/`.env`, never the committed yaml. `.env` symlink + secrets convention already established — do not commit tokens. [Source: memory infra_env_symlink, feedback_secrets]

### Bernard voice — only the graceful-ack path here
Full voice audit is 6.5. For `!mom ping`/`unknown`, Bernard **never** emits HTTP codes, exception names, `null`/`undefined`, or "I cannot help". He acknowledges and offers what he can do. Example register (they/them, Ron-Swanson-on-a-fort, dry/competent): a short confirmation that the bot is alive and listening. [Source: handoff §"Bernard voice rules"; memory project_bernard_character]

### Intent classifier contract
One LLM call, compact (~200-token) system prompt, output constrained to a single token in `{write, query, nl_discovery, unknown}`. Anything not matching a known pattern → `unknown`. Keep the prompt in code/config; this is the seam 6.3 (query), 6.2 (write) and 6.4 (nl_discovery) hang their skills off. Log result with bound `session_id`. [Source: ADR-017 "Core seam"; epics.md AC]

### Testing standards
- Live integration over mocks for the protocol surface — mock tests hide protocol bugs (project rule). The Matrix send/receive and the OpenRouter classify call should be exercised against real services for the done-gate, even if unit tests stub them. [Source: memory feedback_integration_testing]
- Done gate is **operator confirmation** in a real Matrix room (5 s budget), not a pytest pass — but add unit tests for `Message` normalisation and the classifier output-constraining (must always return one of the 4 tokens).

### Project Structure Notes
- All new bot code lives under `harness/` (ADR-017 baseline). New write/query/isochrone modules in later stories land under `infra/bot/` (`git_ops.py`, `isochrone.py`) — out of scope here but keep the import seam clean for them.
- Fedora/Podman: any new bind-mounted volume needs `:z`; harmless on Ubuntu. [Source: memory infra_selinux_and_platform_notes]
- Use `distrobox-host-exec` to reach Podman for local compose runs. [Source: memory infra_local_dev]

### References
- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.0 (lines 1699–1721) + Epic 6 preamble (1681–1697)]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-017 (lines 477–520)]
- [Source: _bmad-output/planning-artifacts/mom_handoff_2026-06-16.md §"Story 6.0", §"Bernard voice rules", §"New dependencies"]
- [Source: _bmad-output/planning-artifacts/prd.md FR37, FR42, NFR-S7 (Epic 6 traceability table, epics.md lines 292–304)]
- [Source: infra/docker-compose.yml (network/service pattern); infra/link_handler/Dockerfile]
- [Source: harness/main.py, harness/llm_client.py, harness/sparql_client.py (baseline being extended)]

## Dev Agent Record

### Agent Model Used

Claude (dev-story workflow), implementing against Gemma 4 12B / OpenRouter as the bot's runtime model per AC 7.

### Debug Log References

- Baseline drift check: `harness/main.py` (Discord), `harness/llm_client.py`, `harness/sparql_client.py` imported and exercised cleanly with the venv at `venv/`. `discord.py>=2.3.0` and `openai`/`httpx`/`structlog`/`python-dotenv` all importable; no drift beyond the documented `minimax/minimax-m2.1` hardcoded model (now config-driven, see below).
- `pytest harness/tests -v` → 9 passed.
- Full repo `pytest -q` → 85 passed, 9 failed/3 errors — confirmed via `git stash`/`git stash pop` that the same 9 failures + 3 errors exist on the pre-story baseline (live-Oxigraph/live-geocode network tests, unrelated to this story).

### Completion Notes List

- **AC1 (baseline drift):** Confirmed `llm_client.complete()` and `sparql_client.run_ask()` still work. Drift found: `llm_client.py` hardcoded `model="minimax/minimax-m2.1"`. Fixed by adding a module-level `MODEL` (default `DEFAULT_MODEL = "google/gemma-4-12b-it"`) that `main_matrix.py` sets from `config.yaml`'s `bot.model` at startup; `complete()` now accepts an optional `model=` override. Discord spike (`harness/main.py`) left untouched — it still works and becomes the 6.6 adapter.
- **AC2 (compose):** Replaced the commented-out Nanobot `mak-agent` block in `infra/docker-compose.yml` with a real `mak-agent-bot` service: `build: ../harness`, `networks: [internal]` (no `external: true` — same compose project per ADR-017 reconciliation in Dev Notes), no `ports`/`expose` (long-running Matrix sync client, not an HTTP server, so nothing to expose), `depends_on: oxigraph`, env vars for `OPENROUTER_API_KEY`, `OXIGRAPH_ENDPOINT`, and `MATRIX_*`. Verified `docker-compose.dev.yml` needs no changes — it only overrides `gateway`/`oxigraph`/`mak-link-handler`/`maps-nginx`, and `mak-agent-bot` only joins `internal`, which exists in both override layers.
- **AC3/AC4 (core seam):** `harness/message.py` (`Message` dataclass, exactly 5 fields) and `harness/adapter.py` (`ChannelAdapter` Protocol with `receive()`/`send()`).
- **AC5 (Matrix adapter):** `harness/matrix_adapter.py` wraps `nio.AsyncClient`; `RoomMessageText` events are normalised onto an internal `asyncio.Queue` via a nio callback, so `receive()` can `await` one `Message` at a time (nio's own API is callback/sync-loop driven, not pull-based — the queue bridges the two models). `send()` posts via `room_send`.
- **AC6/AC9 (intent classifier):** `harness/intent_classifier.py` does one compact (~150-token) OpenRouter call constrained to `write|query|nl_discovery|unknown`, with any off-list/garbage reply (punctuation, refusals, empty string) coerced to `unknown`. Result and bound `session_id` logged via structlog (`intent.classified`). Both the hardcoded-`unknown` first pass and the LLM-backed second pass landed in this story — `router.py`'s `unknown` branch is the surviving runtime path for `!mom ping`; the LLM call is what decides `unknown` vs the other three intents.
- **AC7 (config + voice):** `harness/config.yaml` + `harness/config.py` (mirrors `infra/link_handler/pipeline_helpers.py`'s `load_config()` style) add `bot.model`/`bot.matrix_homeserver`/`bot.platform_tokens`; secrets (`MATRIX_ACCESS_TOKEN`, `OPENROUTER_API_KEY`, etc.) come from env/`.env`, never the yaml. `harness/bernard_voice.yaml` + `harness/bernard.py` load Bernard's bot-voice strings at startup (`ping_ack`/`unknown_ack` only — full voice audit is 6.5).
- **AC8 (smoke test):** `harness/router.py` routes any non-`write`/`query`/`nl_discovery` classification (including `!mom ping`) to `bernard.unknown_ack()` — no raw error/status code, no `null`/exception name. `harness/main_matrix.py` is the new entrypoint: loads config + voice, builds the `MatrixAdapter`, strips the `!mom` prefix, and dispatches through `route()`.
- **Done gate — self-hosted homeserver stood up, live round-trip confirmed (2026-06-16):** Rather than depend on an external Matrix server, stood up a self-hosted Dendrite homeserver (`mapsofmaking.org`) as two new compose services — `dendrite` (`ghcr.io/element-hq/dendrite-monolith`) and `dendrite-postgres` — following Dendrite's own current guidance (verified via Context7/`/element-hq/dendrite` docs) that **Postgres, not SQLite, is required for federated deployments** (SQLite is single-writer and explicitly discouraged). Generated a real signing key + config via Dendrite's `generate-keys`/`generate-config` tools (gitignored: `infra/dendrite/config/{matrix_key.pem,dendrite.yaml}`), then created the real `@bernard:mapsofmaking.org` account via Dendrite's shared-secret registration endpoint (Synapse-compatible `/_synapse/admin/v1/register`) — proving the bot account can be provisioned programmatically, not just hypothetically.
  Two real bugs were found and fixed while getting the live round-trip to work (both are genuine code defects, not environment quirks):
  1. `harness/main_matrix.py` resolved `matrix_homeserver` as `bot_cfg.get(...) or os.environ.get(...)` — `config.yaml`'s compose-internal value (`http://dendrite:8008`) always won over the env var, so the bot could never be pointed at a different homeserver via env alone. Flipped precedence to `os.environ.get(...) or bot_cfg.get(...)`.
  2. `DEFAULT_MODEL`/`config.yaml`'s `bot.model` were set to `google/gemma-4-12b-it`, which is not a real OpenRouter model ID (Gemma 4 only ships as 26b/31b). Corrected to `google/gemma-3-12b-it`, the closest real size match.
  With both fixes applied, `!mom ping` sent from a second Matrix account into a real room was received by the bot's live `sync_forever()` loop, classified `unknown`, and Bernard's ack ("Not sure what you're after there — try asking about a space, or registering one.") was confirmed actually present in the room (re-fetched via `/messages` from the homeserver, not just bot-side logs). Local dev secrets (Matrix access token, DB password) are in `.env`, flagged in-file to rotate before real deployment.
- New unit tests: `harness/tests/test_message.py` (5-field dataclass shape), `harness/tests/test_intent_classifier.py` (classifier always returns one of the 4 tokens, including for garbage/off-list LLM replies).

### File List

- `harness/message.py` (new)
- `harness/adapter.py` (new)
- `harness/matrix_adapter.py` (new)
- `harness/intent_classifier.py` (new)
- `harness/config.py` (new)
- `harness/config.yaml` (new)
- `harness/bernard.py` (new)
- `harness/bernard_voice.yaml` (new)
- `harness/router.py` (new)
- `harness/main_matrix.py` (new)
- `harness/llm_client.py` (modified — `model=` param + config-driven `MODEL`, replacing the hardcoded `minimax/minimax-m2.1`; `DEFAULT_MODEL` corrected `google/gemma-4-12b-it` → `google/gemma-3-12b-it`, real OpenRouter ID)
- `harness/requirements.txt` (modified — added `matrix-nio`, `pyyaml`)
- `harness/Dockerfile` (new)
- `infra/docker-compose.yml` (modified — `mak-agent` Nanobot stub replaced with real `mak-agent-bot` service; added `dendrite` + `dendrite-postgres` services for the self-hosted Matrix homeserver)
- `infra/docker-compose.dev.yml` (modified — local-dev overrides for `dendrite`/`dendrite-postgres`: exposed client-API port, `:z` SELinux flags)
- `infra/dendrite/config/matrix_key.pem` (new, gitignored — Dendrite signing key)
- `infra/dendrite/config/dendrite.yaml` (new, gitignored — Dendrite config: server_name `mapsofmaking.org`, Postgres DSN, registration_shared_secret)
- `harness/main_matrix.py` (modified — fixed `matrix_homeserver` env/config precedence bug, see Completion Notes)
- `harness/config.yaml` (modified — `bot.matrix_homeserver` → `http://dendrite:8008`; `bot.model` corrected to `google/gemma-3-12b-it`)
- `.gitignore` (modified — Dendrite secrets + `data/dendrite-postgres/`, `data/dendrite-media/` bind-mount dirs)
- `data/dendrite-postgres/.gitkeep`, `data/dendrite-media/.gitkeep` (new)
- `harness/tests/test_message.py` (new)
- `harness/tests/test_intent_classifier.py` (new)

## Change Log

- 2026-06-16 — Story 6.0 implemented: Matrix-based channel-agnostic bot spine (`Message`/`ChannelAdapter`/`MatrixAdapter`/intent classifier/router/Bernard voice config), `mak-agent-bot` compose service, unit tests. Status → review. Live Matrix smoke-test confirmation deferred to operator.
- 2026-06-16 — Done gate closed: stood up a self-hosted Dendrite + Postgres Matrix homeserver (`mapsofmaking.org`), created `@bernard:mapsofmaking.org` via shared-secret registration, fixed an env/config precedence bug in `main_matrix.py` and an invalid `bot.model` ID, and confirmed a live `!mom ping` → Bernard-ack round trip in a real room.
