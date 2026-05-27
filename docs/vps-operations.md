# VPS Operations Runbook

Operational reference for the Hetzner VPS hosting Maps of Making.

## Topology

Two-layer nginx, single host:

```
Internet ──► nginx-gateway (host: hetzner-gateway stack)
                │ TLS termination, fronts multiple unrelated services
                ▼
              maps-nginx (host: maps_of_making stack)
                │ static site + reverse proxy to mak-link-handler
                ▼
              mak-link-handler ──► oxigraph
```

- `nginx-gateway` lives in `/home/nicolas/hetzner-gateway/` and is **not** part of this repo. Its conf.d is at `/home/nicolas/hetzner-gateway/nginx/conf.d/`.
- The Maps-of-Making slices of that conf (`06-mapsofmaking.conf`, `07-admin-mapsofmaking.conf`) are version-controlled here under `infra/gateway-nginx/` and pushed with `make sync-gateway`.
- `maps-nginx` joins both the `gateway` external network (for the proxy hop) and the project-internal network (for `oxigraph` + `mak-link-handler`).

## Domains

| Domain | Status | Behavior |
|---|---|---|
| `mapsofmaking.org` | **Primary** | Serves the app |
| `mapsofmaking.com` | Active | 301 → `mapsofmaking.org` |
| `admin.mapsofmaking.org` | Active | Admin UI |
| `mapofmaking.debarquin.eu` | **Deprecated 2026-05-27** | Removed from gateway conf; cert at `/etc/letsencrypt/live/mapofmaking.debarquin.eu/` is unreferenced (safe to `certbot delete` when convenient) |

Wildcard cert lives at `/etc/letsencrypt/live/mapsofmaking.org/` and covers `.org` + `.com`.

## `make publish` vs `make vps-reset`

| | `publish` | `vps-reset` |
|---|---|---|
| Intent | Push latest dev code | Factory-reset all state |
| Touches code on VPS | Yes (rsync) | No (uses whatever is there) |
| Touches `data/` | No | **Wipes** Oxigraph + SQLite + materialized GeoJSON |
| Rebuilds containers | Yes | Yes |
| Seeds canary | No | Yes (Mother Sands only) |
| Triggers heartbeat | No | No (next 10-min cycle picks it up) |
| Reloads gateway | (recommended) | Yes |

The bulk-seed path (`scripts/seed_import.py`) was deprecated in Story 3.4b. Neither target uses it.

## The 502-after-rebuild gotcha

Whenever the maps-nginx container is recreated (any `down`/`up --build`, or `vps-reset`), the **outer** `nginx-gateway` may keep returning 502 for a while even after maps-nginx is healthy.

Cause: the gateway's `proxy_pass` uses a `set $upstream http://maps-nginx:80;` variable with `resolver 127.0.0.11`. When the upstream disappears mid-flight, nginx fail-caches the resolution and doesn't recheck reliably.

Fix (idempotent, safe):

```bash
ssh hetzner 'docker exec nginx-gateway nginx -s reload'
```

This is now baked into `make vps-reset`. After `make publish`, run it manually if you see 502s — or we can fold it into `publish` once that target is rewritten.

## Clean re-deploy from scratch (when `rm -rf maps_of_making` route is taken)

There are **no named Docker volumes** for this project — all persistent state is bind-mounted from `./data/`, `./web/data/`, and `./infra/`. So deleting the repo folder genuinely wipes everything. Verify with `docker volume ls` (should show nothing project-related).

To rebuild from zero:

1. `rsync` (or `git clone`) the repo to `/home/nicolas/maps_of_making/`
2. Recreate `.env` and `infra/.env` symlink (see `infra_env_symlink` memory)
3. `make vps-reset` (runs full down → wipe → up → canary → reload)
4. Claim additional spaces via the admin UI

## Quick checks

```bash
# public reachability
curl -sI https://mapsofmaking.org/ | head -3

# inner stack health (from host)
ssh hetzner 'docker ps --filter name=maps- --format "{{.Names}} {{.Status}}"'

# gateway → maps-nginx reachability (bypasses external DNS / TLS)
ssh hetzner 'docker exec nginx-gateway curl -sI http://maps-nginx/'

# count features in materialized GeoJSON
curl -s https://mapsofmaking.org/data/spaces.geojson | jq '.features | length'

# gateway error log (filter out unrelated services)
ssh hetzner 'docker logs nginx-gateway --tail 200 2>&1 | grep -i mapsofmaking'
```
