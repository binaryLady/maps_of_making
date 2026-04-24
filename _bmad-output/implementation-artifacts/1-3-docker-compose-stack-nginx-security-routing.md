# Story 1.3: Docker Compose Stack + Nginx Security Routing

Status: ready-for-dev

## Story

As a network admin and developer,
I want the full Phase 2 service topology running on the VPS (Oxigraph, Nanobot agent, link-handler, nginx) with public SPARQL read-only and update blocked,
so that the backend is reachable, secure, and ready for ontology loading and ingestion wiring in subsequent stories.

## Acceptance Criteria

1. **Given** the VPS has Docker + Docker Compose installed and `.env` is populated from `.env.example`
   **When** `docker compose up -d` is run from the project root on the VPS
   **Then** all four services start without error: `oxigraph`, `mak-agent` (Nanobot), `mak-link-handler`, `maps-nginx`

2. **And** `docker network ls` shows a `maps_of_making_internal` network; no host-level port conflicts — all services use `expose`, not `ports`, except `maps-nginx` (which joins the external `gateway` network and is only reachable via hetzner-gateway)

3. **And** `GET /sparql/query` with a valid SPARQL SELECT returns 200 from the public internet (via hetzner-gateway → maps-nginx → oxigraph proxy)

4. **And** `POST /sparql/update` returns 403 from outside the Docker network (nginx `deny all` rule verified)

5. **And** `/claim/test` routes to `mak-link-handler:8000/claim/test` (nginx proxy rule present; 404 or 422 from FastAPI is acceptable — the route exists and proxies correctly)

6. **And** the presence webhook nginx route (`/webhook/presence`) is present but commented out (Epic 7 slot reserved)

7. **And** `admin.debarquin.eu` returns 401 without credentials and 200 with the shared password from `.env` (basic auth on `maps-nginx` `/admin` location)

8. **And** `.env.example` is committed with all required variable names and placeholder values; `.env` is in `.gitignore`

## Tasks / Subtasks

- [ ] **Task 1: Extend docker-compose.yml with mak-agent and mak-link-handler** (AC: #1, #2)
  - [ ] Add `mak-agent` service (image: `hkuds/nanobot:latest`, networks: `[internal]`, env: `OPENROUTER_API_KEY`, `OXIGRAPH_ENDPOINT=http://oxigraph:7878`, volumes: `./nanobot-config:/root/.nanobot`, `./tasks:/app/tasks`, depends_on: `[oxigraph]`)
  - [ ] Add `mak-link-handler` service (build: `./link_handler`, expose: `["8000"]`, env: `OXIGRAPH_ENDPOINT=http://oxigraph:7878`, `LINK_SECRET`, depends_on: `[oxigraph]`, networks: `[internal]`)
  - [ ] Remove the `ports: "127.0.0.1:7878:7878"` from oxigraph (use `expose` only; oxigraph is internal-only — access via nginx proxy on VPS)
  - [ ] Ensure `maps-nginx` is on both `gateway` and `internal` networks; other services on `internal` only
  - [ ] Explicit `name: maps_of_making` on the compose file to avoid network collision with other projects on the VPS

- [ ] **Task 2: Create stub mak-link-handler FastAPI service** (AC: #5)
  - [ ] Create `infra/link_handler/Dockerfile` — `FROM python:3.12-slim`, install `fastapi uvicorn`, `COPY . /app`, `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]`
  - [ ] Create `infra/link_handler/main.py` — minimal FastAPI stub with `GET /claim/{token}` returning 422 (not implemented yet), `GET /health` returning 200
  - [ ] Create `infra/link_handler/requirements.txt` — `fastapi`, `uvicorn[standard]`
  - [ ] This is a stub only — full implementation in Epic 3 (Story 3.3)

- [ ] **Task 3: Create stub nanobot-config** (AC: #1)
  - [ ] Create `infra/nanobot-config/` directory with a minimal `config.json` placeholder so the volume mount doesn't fail on start
  - [ ] Config.json can be empty `{}` or minimal valid Nanobot config — full config in Story 1.4+
  - [ ] Nanobot integration is explicitly deferred to post-1.3 (sprint-status note: `nanobot_start: "Story 1.3 — not Story 1.1"` means services are wired up now, not fully configured)

- [ ] **Task 4: Update nginx app.conf — SPARQL security routing** (AC: #3, #4, #5, #6, #7)
  - [ ] Split `/sparql` location into `/sparql/query` (proxy_pass → `http://oxigraph:7878/query`) and `/sparql/update` (`deny all; return 403`)
  - [ ] Add `/claim/` location: `proxy_pass http://mak-link-handler:8000/claim/;` with standard proxy headers
  - [ ] Add `/webhook/presence` location — commented out block (Epic 7 slot)
  - [ ] Add `/admin` location with `auth_basic "Maps Admin"; auth_basic_user_file /etc/nginx/.htpasswd;`
  - [ ] Add CORS header on `/sparql/query`: `add_header Access-Control-Allow-Origin "*" always;`

- [ ] **Task 5: Admin basic auth htpasswd** (AC: #7)
  - [ ] Add `htpasswd` generation to VPS setup instructions — `htpasswd -bc /etc/nginx/.htpasswd admin $MAK_ADMIN_PASSWORD`
  - [ ] Mount `/etc/nginx/.htpasswd` into the maps-nginx container via volume in docker-compose.yml
  - [ ] Add `MAK_ADMIN_PASSWORD` to `.env.example` with placeholder

- [ ] **Task 6: Update .env.example** (AC: #8)
  - [ ] Add all required vars: `DISCORD_BOT_TOKEN`, `OPENROUTER_API_KEY`, `OXIGRAPH_ENDPOINT`, `LINK_SECRET`, `MAK_ADMIN_PASSWORD`
  - [ ] Verify `.env` is in `.gitignore` (add if missing)

- [ ] **Task 7: Deploy to VPS and verify** (AC: #1–#7)
  - [ ] Run `make sync` from local machine to push `web/`, `infra/`, `data/` to VPS and sync gateway nginx confs
  - [ ] SSH to VPS: `ssh hetzner`
  - [ ] On VPS: `cd ~/maps_of_making && docker compose up -d`
  - [ ] Verify all 4 containers running: `docker compose ps`
  - [ ] Verify network: `docker network ls | grep maps_of_making`
  - [ ] Verify SPARQL query: `curl https://mapofmaking.debarquin.eu/sparql/query?query=SELECT+*+WHERE{?s+?p+?o}+LIMIT+1`
  - [ ] Verify SPARQL update blocked: `curl -X POST https://mapofmaking.debarquin.eu/sparql/update -d "..."` → 403
  - [ ] Verify /claim route: `curl https://mapofmaking.debarquin.eu/claim/test` → 404 or 422 (acceptable)
  - [ ] Verify admin auth: `curl https://admin.debarquin.eu/admin` → 401; with credentials → 200

## Dev Notes

### Isolation Notes

- **Distrobox / local dev**: The Docker Compose stack already runs locally. `distrobox-host-exec` is used to access Podman containers from within distrobox. However, **this story's deployment target is the VPS**, not local. Local verification is secondary.
- **VPS connection**: `ssh hetzner` (configured in ~/.ssh/config)
- **Sync command**: `make sync` — rsync pushes `web/`, `infra/`, `data/` to `hetzner:/home/nicolas/maps_of_making/` and gateway nginx confs to `hetzner:/home/nicolas/hetzner-gateway/nginx/conf.d/`
- **Container name prefix**: `maps-` (e.g., `maps-nginx`, `maps-oxigraph`) — keep consistent to avoid VPS collisions

### Architecture Decisions (Do Not Deviate)

- **`expose` not `ports`**: All internal services (`oxigraph`, `mak-agent`, `mak-link-handler`) use `expose`, not `ports`. Only `maps-nginx` reaches outside via the `gateway` Docker network shared with `hetzner-gateway`. [Source: architecture.md#AR-INF1, line ~127]
- **Explicit compose `name: maps_of_making`**: Required so Docker creates `maps_of_making_internal` network, not a generic name that could collide. [Source: architecture.md, line ~127]
- **Oxigraph port**: Currently has `ports: "127.0.0.1:7878:7878"` in docker-compose.yml — **remove this for VPS deploy** (internal-only via nginx proxy). Keep the healthcheck pointing to `http://localhost:7878/health` (Docker-internal).
- **mak-link-handler is a stub**: Full magic link logic is Epic 3 Story 3.3. The stub just needs to respond (even 422) so nginx proxy verification passes.
- **Nanobot config**: `hkuds/nanobot:latest` is the image. Full `config.json` is deferred to Story 1.4+. An empty or minimal config prevents startup failure for now.
- **SPARQL routing pattern** [Source: architecture.md#lines 518-521]:
  - `GET|POST /sparql/query` → `http://oxigraph:7878/query` (public, CORS open)
  - `POST /sparql/update` → `deny all` (return 403)
- **Admin auth**: `auth_basic` with `.htpasswd` file mounted into maps-nginx. Password sourced from `.env` via htpasswd generation on first VPS setup.

### File Structure

```
infra/
  docker-compose.yml          # MODIFY — add mak-agent, mak-link-handler; fix oxigraph ports
  nginx/
    conf.d/
      app.conf                # MODIFY — SPARQL security, /claim, /admin auth, /webhook/presence slot
  link_handler/               # CREATE
    Dockerfile
    main.py                   # stub FastAPI
    requirements.txt
  nanobot-config/             # CREATE
    config.json               # minimal placeholder
.env.example                  # MODIFY — add LINK_SECRET, MAK_ADMIN_PASSWORD
.gitignore                    # VERIFY — .env is gitignored
```

### Makefile Commands (Phase 1 pattern)

```bash
make sync          # sync everything (app + gateway confs) — use this after all local changes
make sync-app      # sync web/, infra/, data/ to VPS only
make sync-gateway  # sync gateway nginx confs only (then reload manually)
```

After gateway conf changes: `ssh hetzner 'docker exec nginx-gateway nginx -s reload'`

### VPS Deploy Sequence

```bash
# 1. Local: push files
make sync

# 2. Remote: bring up stack
ssh hetzner
cd ~/maps_of_making
docker compose pull           # pull latest nanobot image
docker compose up -d --build  # build link_handler, start all services

# 3. Admin htpasswd (first-time setup only)
docker exec maps-nginx htpasswd -bc /etc/nginx/.htpasswd admin <password>
# OR mount pre-generated file via volume in docker-compose.yml

# 4. Verify
docker compose ps
docker network ls | grep maps_of_making
```

### nginx conf: SPARQL Update Blocking

```nginx
# SPARQL — public read, update blocked
location /sparql/query {
    proxy_pass http://oxigraph:7878/query;
    add_header Access-Control-Allow-Origin "*" always;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_connect_timeout 10s;
    proxy_read_timeout 30s;
}

location /sparql/update {
    deny all;
    return 403;
}

# /claim/* — magic link handler (stub, full impl Epic 3)
location /claim/ {
    proxy_pass http://mak-link-handler:8000/claim/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}

# /webhook/presence — Epic 7 slot (commented out intentionally)
# location /webhook/presence {
#     proxy_pass http://mak-agent:9000/presence;
# }

# /admin — basic auth
location /admin {
    auth_basic "Maps Admin";
    auth_basic_user_file /etc/nginx/.htpasswd;
    try_files $uri $uri/ /admin/index.html =404;
}
```

### Acceptance Verification Commands

```bash
# SPARQL read (should return 200)
curl "https://mapofmaking.debarquin.eu/sparql/query?query=SELECT+*+WHERE{?s+?p+?o}+LIMIT+1"

# SPARQL update blocked (should return 403)
curl -X POST "https://mapofmaking.debarquin.eu/sparql/update" \
  -H "Content-Type: application/sparql-update" -d "INSERT DATA { <x:s> <x:p> <x:o> }"

# /claim route (should return 404 or 422)
curl "https://mapofmaking.debarquin.eu/claim/test"

# Admin without credentials (should return 401)
curl "https://mapofmaking.debarquin.eu/admin"

# Admin with credentials (should return 200)
curl -u "admin:$MAK_ADMIN_PASSWORD" "https://mapofmaking.debarquin.eu/admin"
```

### Known Non-Blocking Issue

- `seed_import.py --force` duplicates triples (no `CLEAR GRAPH` before reload) — pre-existing bug, do not address in this story. [Source: sprint-status.yaml#outstanding_bugs]

### Previous Story Context

Story 1.2 was a pure frontend change (`maxBounds` + loader copy). No infra changes were made. Story 1.1 proved Oxigraph/OpenRouter/Discord reachability using a 3-file harness spike — that harness is **not** the production pattern; Nanobot replaces it starting this story.

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6

### Debug Log References

### Completion Notes List

### File List
