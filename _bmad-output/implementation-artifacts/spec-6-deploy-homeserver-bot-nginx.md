---
title: 'Deploy Dendrite + Bernard bot + nginx Matrix routing'
type: 'chore'
created: '2026-06-17'
status: 'done'
---

<frozen-after-approval reason="human-owned intent — do not modify unless human renegotiates">

## Intent

**Problem:** Stories 6.0–6.2 are done locally but nothing is deployed — Dendrite, its Postgres, and the bot service exist in `docker-compose.yml` but are not running on the VPS; nginx has no Matrix routes; no `@bernard` account exists.

**Approach:** Add Matrix path routes to the gateway nginx conf (path-based, shares `mapsofmaking.org` with the map), deploy services on VPS, register `@bernard`, wire `.env`, and walk the full E2E test sequence through to a write commit.

## Boundaries & Constraints

**Always:**
- Use well-known delegation (`/.well-known/matrix/server → mapsofmaking.org:443`) — no port 8448, no firewall change needed.
- `DENDRITE_DB_PASSWORD` and `BOT_KEY_SECRET` must already be in VPS `.env` before starting services.
- `infra/dendrite/config/dendrite.yaml` is gitignored (contains signing key + DB password) — edit on VPS directly if `well_known_server_name` needs to be set.
- Never commit `.env` or tokens.

**Ask First:**
- If `dendrite.yaml` is absent on VPS (first deploy), generate it via `docker run --rm ghcr.io/element-hq/dendrite-monolith:latest generate-config` before starting Dendrite.
- If `DENDRITE_DB_PASSWORD` is not yet in VPS `.env`, HALT and ask before proceeding.

**Never:**
- Open port 8448 — well-known delegation makes it unnecessary.
- Add `/_matrix/` routes to any nginx block other than `mapsofmaking.org` (no subdomain confusion).
- Change the existing `location /` block — map website routing must be untouched.

## I/O & Edge-Case Matrix

| Scenario | Input / State | Expected Output / Behavior | Error Handling |
|----------|--------------|---------------------------|----------------|
| Well-known lookup | `GET /.well-known/matrix/server` | `{"m.server":"mapsofmaking.org:443"}` | If nginx returns 404, federation fails silently — check conf reload |
| Client API check | `GET /_matrix/client/versions` | JSON with `{"versions":[...]}` | 502 = Dendrite not running; check `docker logs maps-dendrite` |
| Bot ping | `!mom ping` in a Matrix room | Bernard ack within 5s | Bot not running: `docker logs maps-agent-bot`; token wrong: 401 in logs |
| Ungranted write | Member (power 0) sends `!mom update space.name "X"` | Graceful Bernard refusal, no crash | Must NOT surface raw exception |

</frozen-after-approval>

## Code Map

- `infra/gateway-nginx/06-mapsofmaking.conf` — gateway nginx conf for mapsofmaking.org; add `/_matrix/` + `/.well-known/matrix/` location blocks here
- `infra/docker-compose.yml` — defines `dendrite-postgres`, `dendrite`, `mak-agent-bot`; no changes needed
- `infra/dendrite/config/dendrite.yaml` — gitignored; lives on VPS; check `well_known_server_name` is empty (well-known served by nginx, not Dendrite)
- `Makefile` — `sync-app`, `sync-gateway`, `vps-rebuild` are the deploy verbs
- `harness/main_matrix.py` — bot entrypoint; reads `MATRIX_*` env vars via `.env`

## Tasks & Acceptance

**Execution:**
- [ ] `infra/gateway-nginx/06-mapsofmaking.conf` — inside the `server_name mapsofmaking.org` HTTPS block, add two location blocks after the existing `location /` block:
  ```nginx
  # Matrix client + federation API
  location /_matrix/ {
      set $upstream http://maps-dendrite:8008;
      proxy_pass $upstream;
      proxy_set_header Host $host;
      proxy_set_header X-Real-IP $remote_addr;
      proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
      proxy_set_header X-Forwarded-Proto $scheme;
      proxy_redirect off;
  }

  # Well-known federation delegation — tells remote servers to connect on 443, not 8448
  location /.well-known/matrix/server {
      add_header Content-Type application/json;
      add_header Access-Control-Allow-Origin *;
      return 200 '{"m.server":"mapsofmaking.org:443"}';
  }

  location /.well-known/matrix/client {
      add_header Content-Type application/json;
      add_header Access-Control-Allow-Origin *;
      return 200 '{"m.homeserver":{"base_url":"https://mapsofmaking.org"}}';
  }
  ```

- [ ] **VPS ops — sync + reload nginx** (run locally):
  ```bash
  make sync-gateway
  ssh REMOTE 'docker exec nginx-gateway nginx -s reload'
  # verify:
  curl https://mapsofmaking.org/.well-known/matrix/server
  curl https://mapsofmaking.org/_matrix/client/versions
  ```

- [ ] **VPS ops — start Dendrite** (first-time: ensure `dendrite.yaml` + signing key exist on VPS):
  ```bash
  ssh REMOTE 'cd REMOTE_APP && docker compose -f infra/docker-compose.yml up -d dendrite-postgres'
  # wait ~10s for postgres healthy, then:
  ssh REMOTE 'cd REMOTE_APP && docker compose -f infra/docker-compose.yml up -d dendrite'
  ssh REMOTE 'docker logs maps-dendrite --tail 30'
  ```

- [ ] **VPS ops — register @bernard** (one-time; `registration_shared_secret` is in `infra/dendrite/config/dendrite.yaml`):
  ```bash
  # On VPS, inside or alongside the dendrite container:
  docker exec maps-dendrite /usr/bin/create-account \
    --config /etc/dendrite/dendrite.yaml \
    --username bernard --password <choose-strong-password>
  ```
  Then login to get the access token:
  ```bash
  curl -s -X POST https://mapsofmaking.org/_matrix/client/v3/login \
    -H "Content-Type: application/json" \
    -d '{"type":"m.login.password","user":"bernard","password":"<password>"}' \
    | jq '{access_token, device_id}'
  ```

- [ ] **VPS ops — populate `.env`** with Matrix vars:
  ```
  MATRIX_HOMESERVER=https://mapsofmaking.org
  MATRIX_USER_ID=@bernard:mapsofmaking.org
  MATRIX_ACCESS_TOKEN=<from login above>
  MATRIX_DEVICE_ID=<from login above>
  ```

- [ ] **VPS ops — start the bot**:
  ```bash
  ssh REMOTE 'cd REMOTE_APP && docker compose -f infra/docker-compose.yml up -d mak-agent-bot'
  ssh REMOTE 'docker logs maps-agent-bot --tail 30'
  ```

**Acceptance Criteria:**
- Given nginx is reloaded, when `curl https://mapsofmaking.org/.well-known/matrix/server`, then response is `{"m.server":"mapsofmaking.org:443"}`
- Given Dendrite is running, when `curl https://mapsofmaking.org/_matrix/client/versions`, then response includes `versions` array
- Given the bot is running with valid tokens, when `!mom ping` is sent in a Matrix room with Bernard invited, then Bernard responds within 5s
- Given `!mom link` is sent by coordinator, then Bernard returns public key block + tutorial markdown
- Given a deploy key is registered and `!mom update space.contact.irc "#test:libera.chat"` is sent, then Bernard confirms with a commit SHA
- Given a power-0 member sends `!mom update space.name "X"`, then Bernard returns a graceful refusal (no raw error, points to `!mom grant`)

## Design Notes

**Why well-known over port 8448:** Dendrite supports both. Well-known is simpler — no extra firewall rule, reuses the existing Let's Encrypt cert, and the `maps-dendrite` container already joins the `gateway` Docker network so it's reachable from nginx.

**`create-account` vs shared_secret registration:** Dendrite's monolith image ships `create-account` binary; it's cleaner than crafting a HMAC-signed shared_secret registration request. Use it.

**`well_known_server_name` in dendrite.yaml:** Leave it empty — nginx serves the well-known JSON directly, so Dendrite doesn't need to emit it. Setting it would cause Dendrite to override nginx's response.

## Verification

**Commands:**
- `curl https://mapsofmaking.org/.well-known/matrix/server` — expected: `{"m.server":"mapsofmaking.org:443"}`
- `curl https://mapsofmaking.org/_matrix/client/versions` — expected: JSON with versions array
- `ssh REMOTE 'docker logs maps-agent-bot --tail 50'` — expected: `sync_forever` running, no auth errors
- `!mom ping` in a Matrix room — expected: Bernard ack within 5s

**Manual checks:**
- Federation tester: https://federationtester.matrix.org/ → enter `mapsofmaking.org` → should pass server discovery
- Invite `@bernard:mapsofmaking.org` from an Element account on matrix.org (cross-server invite confirms federation works)

## Spec Change Log

