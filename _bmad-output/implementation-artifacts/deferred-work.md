# Deferred Work

## Deferred from: code review of 1-3-docker-compose-stack-nginx-security-routing (2026-04-24)

- **Docker images not pinned to specific versions** — `infra/link_handler/Dockerfile` uses `python:3.12-slim` (no patch pin); `docker-compose.yml` uses `:latest` tags. Future deploys may break silently.
- **CORS `*` overly permissive on /sparql/query** — Intentional for public endpoint now; consider restricting to known origins when admin/write paths are added in Epic 5.
- **LINK_SECRET env var never consumed in stub** — Passed to mak-link-handler but ignored until Epic 3 (Story 3.3) implements actual HMAC token signing.
- **nginx /claim/ has minimal proxy headers** — Missing `X-Forwarded-Proto`, `X-Forwarded-Host`. Full headers needed when claim handler does origin-aware logic in Epic 3.
- **No SPARQL query complexity limits / DoS protection** — No timeout or depth limit on public /sparql/query. Add nginx `limit_req` or oxigraph timeout config in future infra hardening story.
- **No graceful shutdown timeout for uvicorn** — Single-worker stub; add `--timeout-graceful-shutdown 30` when claim handler processes real transactions in Epic 3.
- **gateway network external precondition not verified** — `docker-compose up` fails if hetzner-gateway network doesn't exist. Add to VPS setup runbook.
- **nginx starts before upstreams are ready (early 502s on cold start)** — On `docker compose up -d`, first few requests may hit 502. Acceptable for current scale; add startup ordering with `condition: service_healthy` sweep if SLA requires cold-start reliability.
- **No upstream fallback for oxigraph or mak-link-handler downtime** — Bare 502 on upstream failure. Add `error_page 502 /50x.html` or upstream backup when resilience becomes a requirement.

## Deferred from: code review of 1-4-author-mom-ontology-v0-load-mom-iop-into-oxigraph (2026-04-24)

- **distrobox fallback silent failure when container not running** — `scripts/load_ontology.sh`: if `maps-oxigraph` is not running, `podman inspect` fails silently, `CONTAINER_IP` is empty, script proceeds with the original unreachable URL without a clear diagnostic error message.
- **No `--max-time` on curl PUTs in load_ontology.sh** — load script can hang indefinitely on slow VPS or stalled container; health check has `-m 1` but actual PUT calls don't.
