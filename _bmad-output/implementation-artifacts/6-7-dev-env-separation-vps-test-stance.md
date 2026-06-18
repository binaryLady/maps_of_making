# Story 6.7: Dev Env Separation + VPS Test Stance

**Status:** ready-for-dev
**Epic:** 6 — Ask Bernard
**Story ID:** 6-7
**Depends on:** 6.3 (query commands live — this story enables testing them)

---

## User Story

As the operator,
I want a clean local dev `.env` that never conflicts with VPS credentials,
So that I can test bot changes locally without resetting production creds — and when testing on VPS is simpler, that stance is documented so I don't have to redecide it each time.

---

## Acceptance Criteria

**Given** the project has two Dendrite homeservers (local dev + VPS) with different Matrix credentials
**When** Story 6.7 lands
**Then**:

- `infra/.env-dev` exists (gitignored) as the local dev credential file — separate from `infra/.env` (VPS/prod)
- `infra/docker-compose.dev.yml` sets `env_file: .env-dev` for `mak-agent-bot` and `dendrite` services, overriding the prod `.env` used by `docker-compose.yml`
- `infra/.env.example` (or equivalent doc) lists all required vars for both files with comments distinguishing VPS vs dev values
- `infra/.env-dev` is added to `.gitignore` (`.env` was already there — confirm both are covered)
- A comment block in `docker-compose.dev.yml` clearly explains: "local dev uses `.env-dev`; VPS uses `.env`; never swap them"

**And** the canonical testing stance for Epic 6 is documented:
- **Primary testing target is VPS**, using the `#mapsofmaking:matrix.nicolas.be` room already set up
- Local dev Dendrite remains available for isolated protocol experiments but is NOT required for story DoD gates
- This stance is recorded in the story's Dev Notes and propagated to future story context (so 6.4+ dev agent knows)

**Done gate:** operator confirms `docker-compose.dev.yml up` uses `.env-dev` creds without touching `infra/.env`; VPS bot still responds in the test room.

---

## Technical Implementation Guide

### 1. File Map

| Action | Path | Notes |
|--------|------|-------|
| CREATE | `infra/.env-dev` | Local dev credentials — gitignored |
| CREATE | `infra/.env-dev.example` | Template with all required vars, VPS vs dev comments |
| UPDATE | `infra/docker-compose.dev.yml` | Add `env_file: .env-dev` override for bot + dendrite |
| UPDATE | `.gitignore` | Ensure `infra/.env-dev` is covered (infra/.env already there) |
| UPDATE | `infra/docker-compose.dev.yml` | Add comment block explaining env separation |

### 2. `env_file` Override Pattern

In `docker-compose.dev.yml`, add `env_file` to the bot and dendrite services:

```yaml
services:
  mak-agent-bot:
    env_file:
      - .env-dev   # path relative to infra/ (where compose is run from)

  dendrite:
    env_file:
      - .env-dev
```

`docker-compose.yml` continues to use `.env` (Docker Compose auto-loads `.env` from the compose file directory). The dev override file takes precedence for these services when the dev compose is layered on top.

### 3. Required Vars — `.env-dev.example`

```bash
# infra/.env-dev — LOCAL DEV ONLY. Never commit the real file.
# VPS values live in infra/.env (separate gitignored file).

# Matrix bot credentials — LOCAL Dendrite (http://localhost:8008)
MATRIX_HOMESERVER=http://dendrite:8008
MATRIX_USER_ID=@bernard:your-local-domain
MATRIX_ACCESS_TOKEN=<dev-access-token>
MATRIX_DEVICE_ID=<dev-device-id>

# Shared secrets — dev values (different from VPS)
BOT_KEY_SECRET=dev-secret-change-me
LINK_SECRET=dev-secret-change-me

# Dendrite postgres
DENDRITE_DB_PASSWORD=dev-password-change-me

# ORS (optional for dev — omit to disable travel search)
ORS_API_KEY=

# Infrastructure
LINK_HANDLER_URL=http://mak-link-handler:8000
OXIGRAPH_ENDPOINT=http://oxigraph:7878
```

### 4. `.gitignore` Check

Verify `infra/.env` and `infra/.env-dev` are both covered. The symlink `infra/.env → ../.env` is documented in `infra_env_symlink` memory — confirm `.env-dev` does not need to be a symlink (it's a standalone file for local dev, no VPS equivalent).

### 5. VPS Test Stance Documentation

Add a comment block at the top of `docker-compose.dev.yml`:

```yaml
# ENV SEPARATION:
# - Local dev: docker-compose.yml + docker-compose.dev.yml → uses .env-dev (local Dendrite creds)
# - VPS prod:  docker-compose.yml alone                   → uses .env (prod Dendrite creds)
# Never use .env-dev on VPS or .env locally — they contain different homeserver URLs and tokens.
#
# TESTING STANCE (Epic 6):
# Primary test target is VPS (mapsofmaking.nicolas.be). The #mapsofmaking:matrix.nicolas.be room
# is the live test room. Local Dendrite is available for protocol experiments but NOT required
# for story DoD gates. See Story 6.7 for rationale.
```

---

## Deferred Items

1. **Local Dendrite bot registration script** — currently bot must be registered manually via curl. A `make register-bot-local` target deferred — low priority given VPS-first test stance.
2. **Secret rotation docs** — how to rotate `BOT_KEY_SECRET` without breaking existing deploy keys. Deferred to an ops runbook.

---

## Change Log

- 2026-06-18: Story 6.7 created — dev env separation + VPS test stance.
