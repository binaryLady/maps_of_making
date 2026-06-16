# MOM Handoff — 2026-06-16
# Epic 6 Restructure: Bernard Bot (one voice, two skillsets)

## Context

Planning session today resolved the architecture for Epic 6. The existing
story list (6.1–6.6) is superseded by this document. Update sprint-status.yaml
before starting any story.

Epic 9 stories 9.6, 9.7, 9.9, 9.10 are absorbed into Epic 6 write skillset
— do not create story files for them. 9.8 is done (GitLab tutorial surface,
the deploy key tutorial will live there). 9.11 is deferred, still valid later.

---

## The core decision

**One bot. One voice. Internal routing.**

Previous plan assumed two bots: a coordinator maintenance bot (Matrix) and a
discovery bot (Discord/Telegram). This is wrong for two reasons:

1. Coordinators should not have to know which bot handles what. "Ask Bernard"
   covers everything.
2. The platform is a transport, not a product. The bot is channel-agnostic;
   Matrix/Discord/Telegram/Mattermost are adapters.

The intent router is what separates the two skillsets internally. A coordinator
typing "update our Tuesday hours to 10–18" and a maker typing "find laser
cutters near Hamburg" both go through the same Bernard — different skill fires,
same voice responds.

---

## Architecture

```
channel message (Matrix / Discord / Telegram / Mattermost)
    ↓
platform adapter  ← strips transport, normalises to Message(text, user_id, room_id, platform)
    ↓
intent classifier ← LLM call (~200 token context), returns: write | query | nl_discovery | unknown
    ↓
skill router
    ├── write skill   → permission check → JSON patch → git commit via SSH
    ├── query skill   → SPARQL template → Oxigraph → formatted answer
    └── nl_discovery  → NL→SPARQL → IoP ontology guardrail → Oxigraph → answer
    ↓
response formatter ← Bernard voice, platform-aware markdown
    ↓
platform adapter  ← sends back
```

**LLM:** Gemma 4 12B via OpenRouter (LiteLLMProvider — same pattern as
`harness/llm_client.py` baseline). Haiku is acceptable fallback. This is a
slot-filling + response-formatting task, not open-ended reasoning. Do not use
a heavier model.

**No new agent framework.** `harness/` is the baseline (🟡 dormant,
Epic 6 entry). Extend it. Do not introduce Nanobot or a new orchestrator for
6.0–6.2. Nanobot is deferred — re-evaluate at 6.4.

**Oxigraph access:** read-only from the bot. No SPARQL UPDATE from bot.
Write path is always: JSON patch → git commit → heartbeat picks up on next
cycle → Oxigraph updated by the pipeline. The bot never writes triples
directly.

---

## Data sovereignty contract

Coordinators own their endpoint JSON. The bot edits it on their behalf via
SSH deploy key — it does not host the file.

**Deploy key model:**

1. MOM generates an SSH key pair per registered space (`ssh-keygen -t ed25519`)
2. Private key stored encrypted in the DB, keyed to `space_uri`
3. Bot presents the public key to the coordinator with tutorial steps:
   GitLab → Settings → Repository → Deploy Keys → paste → enable Write access
4. Bot commits to that one file path over SSH. Scope: one repo, one file.
   Nothing else is accessible.
5. Coordinator revokes access by removing the deploy key from their repo.
   MOM has no persistent access after revocation.

**Platforms supported:** GitLab, GitHub, Codeberg, Gitea — all support deploy
keys identically. Tutorial copy is the same for all four (Story 9.8 surface).

**Graceful degradation for non-git hosting:** if a space has no deploy key
registered, write commands respond with Bernard's degraded path (see voice
rules below). Read/query commands always work regardless.

---

## New story sequence

### Story 6.0 — Bot infrastructure
*Platform adapters, channel-agnostic core, intent router, Bernard config*

**Depends on:** Epic 1 (Oxigraph running), `harness/` baseline exists

New Docker Compose service: `mak-agent-bot`. Joins `maps_of_making_internal`
network (same pattern as planned Nanobot service — `external: true`).

Deliverables:
- `Message` dataclass: `text`, `user_id`, `room_id`, `platform`, `raw`
- `ChannelAdapter` protocol: `async receive() → Message`, `async send(response, context) → None`
- Matrix adapter via `matrix-nio` (async Python — fits existing stack)
- Intent classifier: LLM call with compact system prompt, returns one of:
  `write | query | nl_discovery | unknown`
- `config.yaml` entries: `bot.model`, `bot.platform_tokens`, `bot.matrix_homeserver`
- Bernard voice config loaded at startup (see voice rules section)
- `!mom ping` smoke test: bot responds, classifier returns `unknown`, Bernard
  acknowledges gracefully

**AC:** `/ping` in a Matrix room returns a Bernard-voice response within 5s.
Classifier result logged via structlog with `session_id` bound.

---

### Story 6.1 — Deploy key provisioning + SSH git access
*MOM generates key pair, coordinator adds public key, bot can commit*

**Depends on:** 6.0 (bot running), Epic 2 (spaces registered with endpoint URLs)

New FastAPI endpoint in `link_handler`: `POST /api/bot/deploy-key/{space_id}`
— generates ed25519 key pair, stores private key encrypted (Fernet, key from
env `BOT_KEY_SECRET`), returns public key + tutorial markdown.

New bot command: `!mom link` — triggers key generation for the space associated
with the room (room→space mapping stored in Oxigraph as `mom:botRoom`), presents
public key and tutorial steps in Bernard voice.

Git operations module `infra/bot/git_ops.py`:
- `read_json(space_uri) → dict` — clone/pull via SSH, return parsed JSON
- `patch_json(space_uri, field_path, value) → str` — apply patch, validate
  schema, return commit SHA
- `commit_json(space_uri, field_path, value, authorized_by) → str` — git
  commit + push. Commit message format:
  `Update {field_path} for {space_name} · authorized by {matrix_user_id}`

**No deploy key = no write.** Bot checks for stored key before any write
operation. If absent, responds with degraded path (see voice rules).

**AC:** `!mom link` in a Matrix room returns a public key block and step-by-step
tutorial. After coordinator adds the key to their repo, `!mom update space.url
"https://example.com"` commits the change and heartbeat picks it up within 10min.

---

### Story 6.2 — Write skillset
*Permission model, field updates, open/close shortcuts*

**Depends on:** 6.1 (git access working)

**Permission model** (Matrix power levels → bot policy):

| Power level | Role | Bot write permissions |
|---|---|---|
| 100 (room admin) | Coordinator | Any field, `!mom grant`, `!mom revoke` |
| 50 | Trusted member | Fields explicitly granted by coordinator |
| 0 | Member | Read-only |

Permission policy stored per room in Oxigraph:
```turtle
<urn:mak:room/{roomid}> mom:space <urn:mak:space/{slug}> ;
    mom:memberPermission [
        mom:matrixId "@luca:matrix.org" ;
        mom:allowedFields "state.open", "contact.irc"
    ] .
```

**Write commands:**

```
!mom update {field.path} {value}   — coordinator: any field
!mom open                          — shorthand: state.open = true
!mom close                         — shorthand: state.open = false
!mom grant @user {field}           — coordinator only
!mom revoke @user {field}          — coordinator only
!mom permissions                   — list current grants
```

**Field whitelist for member writes** (cannot be expanded by coordinator):
`state.open`, `contact.irc`, `contact.matrix`, `contact.twitter`.
Coordinator can grant subsets only. `space.name`, `location.*`, `url` are
coordinator-only regardless of grant.

**Commit attribution:** every commit includes `authorized_by: {matrix_user_id}`
in the commit message. This is the audit trail — no separate log needed.

**AC:** coordinator types `!mom update space.contact.irc "#atelier-commun:libera.chat"`,
bot patches JSON, commits, responds in Bernard voice confirming the change.
Heartbeat picks it up on next cycle. Member without grant receives graceful
refusal (see voice rules).

---

### Story 6.3 — Read/query command set + isochrone tool
*Template SPARQL queries + travel-time radius search*

**Depends on:** 6.0 (bot running), Epic 3 (data in Oxigraph)

All queries in this story are **templated** — no LLM involved. LLM only
formats the response in Bernard voice.

**Template query commands:**

```
!mom status                    → lifecycle state + last heartbeat for this room's space
!mom hours                     → opening hours from Oxigraph
!mom find {tag} {city}         → confirmed spaces WHERE tags CONTAIN + city match
!mom nearby {city} {radius}    → spaces within bounding box (Nominatim → bbox → SPARQL)
!mom network {network_name}    → spaces WHERE memberOf confirmed both directions
!mom travel {origin} {hours}   → spaces reachable within N hours (see isochrone below)
```

**Isochrone tool** (`infra/bot/isochrone.py`):

Three-step operation:
1. Resolve origin → coordinates (Oxigraph if space name, Nominatim if city name)
2. Call OpenRouteService (ORS) free tier: `GET /v2/isochrones/{profile}`
   with `locations`, `range` (seconds), `range_type: time`
   Returns GeoJSON polygon. Profile: `driving-car` default,
   `cycling-regular` and `foot-walking` available via `!mom travel ... by bike/foot`
3. Python point-in-polygon filter against all confirmed spaces from Oxigraph
   (not native SPARQL geo — post-filter in Python with `shapely`)

ORS API key in `.env` as `ORS_API_KEY`. Free tier: 2000 req/day, sufficient
for PoC. Self-hostable later if needed.

New dependency: `shapely` (point-in-polygon), `httpx` (already present via
pipeline) for ORS calls.

**Example interaction:**
```
@bernard: !mom travel Brussels 2h
Bernard: Within 2 hours of Brussels by car I can see 14 confirmed spaces.
         Closest: FabLab ULB (23 min), iMAL (31 min), Maakbib Gent (58 min).
         Furthest confirmed: WitteLab Amsterdam (1h 54min).
         3 seeded spaces also fall in range — they haven't registered an
         endpoint yet. Want me to list them?
```

**AC:** `!mom travel Brussels 2h` returns confirmed spaces within the isochrone
polygon with travel time estimates. ORS timeout (>5s) triggers graceful
degradation — Bernard offers bounding-box fallback via `!mom nearby`.

---

### Story 6.4 — NL→SPARQL full natural language
*IoP ontology guardrail, free-form discovery queries*

**Depends on:** 6.3 (template queries working), IoP ontology in Oxigraph (Story 1.4)

This is the original Epic 6 NL→SPARQL work, now arriving with proven
infrastructure underneath it. Model: Sonnet (`temperature=0.0`) for query
generation — same reasoning as original spec. Gemma handles everything else;
Sonnet is only for this step.

IoP ontology subset extraction, SPARQL mutation guard, ontology gap logging —
carry forward from original Story 6.1 spec in epics.md verbatim.

The classifier from Story 6.0 routes here when intent is `nl_discovery` and
the query doesn't match a known template pattern.

---

### Story 6.5 — Graceful failure + Bernard voice pass
*Retroactive voice audit across 6.0–6.4, failure path coverage*

**Depends on:** 6.0–6.4 all functional

This story is a pass over everything already built. Bernard's voice is easier
to tune once all failure paths are observable in testing. Do not attempt to
pre-tune voice before this story — write functional responses in 6.0–6.3,
polish here.

See Bernard voice rules section below — these are the acceptance criteria
for this story.

---

### Story 6.6 — Additional channel adapters
*Discord, Telegram, Mattermost (Matrix already in 6.0)*

**Depends on:** 6.0 (adapter protocol defined)

Discord and Telegram use the same `ChannelAdapter` protocol. Discord requires
the defer pattern (`interaction.response.defer(thinking=True)`) — mandatory
for any LLM-involved command (bot timeout is 3s). Mattermost uses outgoing
webhook → response via incoming webhook.

These adapters add channels, not features. The write skillset (deploy key,
JSON patch, git commit) is Matrix-first and is explicitly **not** available on
Discord/Telegram for the PoC. Reason: room-based permission model maps to
Matrix rooms; Discord/Telegram channels don't have the same power level
semantics. Discovery and read commands are available on all platforms.

---

## Epic 9 consequence

Stories 9.6 (wizard tier 2 mom: fields), 9.7 (state.open FSM), 9.9
(three-mode unification), 9.10 (wizard tier 3 ext_fab) are **superseded by
Epic 6 write skillset**. Mark them as `superseded` in sprint-status.yaml —
do not create story files.

Rationale: the wizard Tier 1 (stories 9.1–9.5, 9.8, 9.12) closes the
first-user vertical slice (compose JSON → host on GitLab → see pin on map).
Tier 2 and 3 fields are better served by the bot — the coordinator already
has a live file, the bot lets them update it conversationally without
re-running the wizard.

9.11 (validator error UX) is still valid, deferred.

---

## Bernard voice rules
### These are hard constraints, not style guidelines

**Bernard never says:**
- HTTP status codes or exception names ("Error 404", "ConnectionError",
  "NoneType", "null", "undefined")
- "I don't have permission to do that" (too corporate)
- "Your query returned no results" (dead end)
- "I cannot help with that" (without offering what he can do)

**Bernard always says:**
- What he knows first, then what he can't reach:
  > *"Mother Sands is confirmed — last seen 4 hours ago. Your endpoint
  > timed out just now; I'll try again on the next cycle."*

- Why write is unavailable, with the exact path forward:
  > *"I can read your profile but I can't edit it yet. You'll need to share
  > a deploy key with me — one-time setup, takes about 2 minutes:
  > [link to 9.8 tutorial]"*

- For zero results, the seeded fallback:
  > *"No confirmed spaces match within 2 hours of Brussels. There are 3
  > seeded spaces in that range — they haven't registered an endpoint yet.
  > Want me to list them anyway?"*

- For permission refusal:
  > *"That field is coordinator-only. Ask your space coordinator to grant
  > you access with `!mom grant @you state.open`, then try again."*

- For LLM unavailability (distinct from data absence):
  > *"The thinking part of my brain is temporarily busy. Template queries
  > still work — try `!mom find` or `!mom nearby` while I recover."*

**Commit messages are Bernard's voice too:**
```
Update hours.tuesday for Atelier Commun · authorized by @sophie:matrix.org
Mark Atelier Commun open · authorized by @luca:matrix.org
```

---

## Sprint-status.yaml updates required

Apply these changes before starting any story:

```yaml
# Epic 6 — replace existing story list
epic-6: in-progress
6-0-bot-infrastructure-adapters-intent-router-bernard-config: ready-for-dev
6-1-deploy-key-provisioning-ssh-git-access: backlog
6-2-write-skillset-json-patch-git-commit-permission-model: backlog
6-3-read-query-command-set-isochrone-tool: backlog
6-4-nl-sparql-natural-language-iop-ontology: backlog
6-5-graceful-failure-bernard-voice-pass: backlog
6-6-additional-channel-adapters-discord-telegram-mattermost: backlog

# Epic 9 — mark superseded stories
9-6-wizard-tier-2-mom-fields-opening-hours-memberof-mom-sdgs: superseded  # absorbed by Epic 6.2
9-7-wizard-state-open-fsm-cascading-questions-marker-mapping-opt-out: superseded  # absorbed by Epic 6.2
9-9-three-mode-unification-url-fetch-pre-fill-validator-mode-cache-resume-reconciliation: superseded
9-10-wizard-tier-3-ext-fab-fields-space-type-fuzzy-dropdown-equipment: superseded  # absorbed by Epic 6.2
```

---

## New dependencies to add

```
# Python (add to requirements.txt or pyproject.toml)
matrix-nio        # Matrix adapter (async)
shapely           # point-in-polygon for isochrone post-filter
cryptography      # Fernet for deploy key private key encryption (likely already present)

# External services
OpenRouteService  # ORS_API_KEY in .env — free tier, 2000 req/day
                  # https://openrouteservice.org/dev/#/signup
```

`httpx` is already in the pipeline. `matrix-nio` is the only truly new
dependency for 6.0.

---

## What NOT to build in 6.0–6.2

- No Nanobot integration. Defer to 6.4 re-evaluation.
- No SPARQL UPDATE from the bot. Pipeline is the only Oxigraph writer.
- No write commands on Discord/Telegram. Matrix-only for PoC.
- No per-coordinator GitLab OAuth. Deploy key model only — coordinator
  controls the key, not MOM.
- No membership handshake logic. That is a separate unscoped feature.
- No monetisation gating. Free for all spaces, no tier enforcement in code yet.

---

## Existing code anchors

```
harness/                 🟡 dormant — Epic 6 baseline, extend this
harness/llm_client.py    LiteLLMProvider pattern to follow
harness/main.py          Discord bot skeleton (defer pattern reference)
infra/link_handler/      FastAPI app — add deploy-key endpoint here
infra/docker-compose.yml add mak-agent-bot service (expose, not ports)
config.yaml              add bot.* config block
```

The `maps_of_making_internal` Docker network is already defined. New
`mak-agent-bot` service joins it with `external: true` (same pattern
as planned Nanobot integration noted in cross_epic_handoffs).

---

## Start here

Story 6.0. Verify `harness/` runs cleanly first — check if there is any
drift from the Epic 1 spike. Then build the `Message` dataclass and Matrix
adapter. The intent classifier can return hardcoded `unknown` for the smoke
test — wire the LLM call in a second pass once the adapter is confirmed
working in the Openfab Matrix room.

One room, one `!mom ping`, Bernard responds. That is the 6.0 done gate.
