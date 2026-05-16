REMOTE      := hetzner
REMOTE_APP  := /home/nicolas/maps_of_making
REMOTE_GW   := /home/nicolas/hetzner-gateway/nginx/conf.d

# Files/dirs excluded from app sync
# data/ holds runtime state (oxigraph DB, nginx logs) — never overwrite from local
RSYNC_EXCLUDE := \
	--exclude='.git/' \
	--exclude='_bmad/' \
	--exclude='_bmad-output/' \
	--exclude='archive/' \
	--exclude='*.mp4' \
	--exclude='*.zip' \
	--exclude='.claude/' \
	--exclude='gateway-nginx/' \
	--exclude='node_modules/' \
	--exclude='venv/' \
	--exclude='__pycache__/' \
	--exclude='*.pyc' \
	--exclude='.pytest_cache/' \
	--exclude='data/'

.PHONY: sync sync-app sync-gateway publish startdev rebuild seed seed-spaceapi heartbeat devdeploy reset vps-rebuild vps-seed help
.PHONY: canary-reset canary-report canary-demo-cycle
.PHONY: canary-a-reachable canary-a-timeout canary-a-dns-fail canary-a-http-error canary-axis-a
.PHONY: canary-b-seeded canary-b-confirmed canary-b-aging canary-b-zombie canary-b-closed canary-axis-b
.PHONY: canary-c-openclose-open canary-c-openclose-shut canary-axis-c canary-all

CANARY_DB ?= data/tasks/heartbeat_log.db
CANARY_SERVED := data/canary/served.json
CANARY_SCENARIO := source venv/bin/activate && python3 scripts/canary_scenarios.py

help:
	@echo "── LOCAL ────────────────────────────────────────────────────────────"
	@echo "make startdev      — start local stack without rebuilding"
	@echo "make rebuild       — full local cycle: down → build → up + health wait"
	@echo "make seed          — import seed datasets into local Oxigraph (:7878)"
	@echo "make seed-spaceapi — import directory.spaceapi.io federation directory (~244 spaces)"
	@echo "make heartbeat     — trigger immediate heartbeat cycle locally"
	@echo "make devdeploy     — rebuild + seed + heartbeat (mirrors publish, locally)"
	@echo "make reset         — DESTRUCTIVE: wipe Oxigraph + heartbeat DB, then devdeploy"
	@echo "── VPS ──────────────────────────────────────────────────────────────"
	@echo "make publish       — full deploy: sync + rebuild + reseed + heartbeat"
	@echo "make sync          — sync everything (app + gateway confs)"
	@echo "make sync-app      — sync project root (excl. dev artifacts) to VPS"
	@echo "make sync-gateway  — sync gateway nginx confs (manual reload needed)"
	@echo "make vps-rebuild   — rebuild containers on VPS (no sync — code must be current)"
	@echo "make vps-seed      — sync + reseed + heartbeat on VPS (no container rebuild)"
	@echo "── CANARY ───────────────────────────────────────────────────────────"
	@echo "make canary-reset          — restore served.json from baseline"
	@echo "make canary-a-{scenario}   — Axis A: reachable/timeout/dns-fail/http-error"
	@echo "make canary-b-{scenario}   — Axis B: seeded/confirmed/aging/zombie/closed"
	@echo "make canary-c-{scenario}   — Axis C: openclose-open/openclose-shut"
	@echo "make canary-axis-{a,b,c}   — run all scenarios for an axis"
	@echo "make canary-all            — run all scenarios across all axes"
	@echo "make canary-report         — per-layer coherence-diff report"
	@echo "make canary-demo-cycle     — seed→confirmed→aging→zombie→closed lifecycle chain"

## Start local dev stack (rootless Podman, dev port overrides, from host OS)
startdev:
	podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d

## Full local container cycle: down → build → up + health check wait
## Use after code changes. Persists Oxigraph data (data/ is a volume mount).
rebuild:
	podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml down
	podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d --build
	@echo "→ waiting for link-handler to be healthy..."
	@timeout 60 sh -c 'until podman exec maps-link-handler python3 -c "import urllib.request; urllib.request.urlopen(\"http://localhost:8000/health\")" 2>/dev/null; do sleep 3; done' && echo ok || echo "warning: health check timed out"

## Import seed datasets into local Oxigraph (:7878)
## coordinator-registered spaces are never cleared by --force.
seed:
	@echo "→ waiting for Oxigraph to be ready..."
	@timeout 30 sh -c 'until curl -sf http://localhost:7878/health >/dev/null 2>&1 || curl -sf http://localhost:7878/ >/dev/null 2>&1; do sleep 1; done' || true
	source venv/bin/activate && python scripts/seed_import.py --force

## Trigger an immediate heartbeat cycle locally — populates Zone 3, rematerializes GeoJSON
heartbeat:
	podman exec maps-link-handler python3 -c \
	  "import httpx; r = httpx.post('http://localhost:8000/api/heartbeat/run', timeout=180); print('heartbeat:', r.status_code)"

## Import the SpaceAPI federation directory (https://directory.spaceapi.io/) into local Oxigraph.
## Each space tagged mom:memberOf <urn:mak:network/spaceapi> → "SPACEAPI" filter chip on the map.
seed-spaceapi:
	source venv/bin/activate && python scripts/seed_spaceapi.py --force
	$(MAKE) heartbeat

## Full local pipeline: rebuild + seed + heartbeat (mirrors make publish for local dev)
devdeploy: rebuild seed heartbeat
	@echo "✓ local dev stack live — map at http://localhost:8080"

## DESTRUCTIVE: wipe Oxigraph triplestore + heartbeat DB, then full reseed via devdeploy.
## Loses ALL coordinator-registered spaces. Use before demos / fresh-state tests.
## On VPS, the equivalent is intentionally manual — see data-lifecycle.md.
reset:
	@echo "⚠  This will wipe data/oxigraph/ and data/tasks/heartbeat_log.db"
	@echo "   Coordinator-registered spaces will be lost."
	@read -p "   Type 'reset' to confirm: " ans && [ "$$ans" = "reset" ] || (echo "aborted"; exit 1)
	podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml down
	rm -rf data/oxigraph/* data/tasks/heartbeat_log.db web/data/spaces.geojson
	@sleep 2
	$(MAKE) devdeploy
	@echo "✓ reset complete — refresh your browser at http://localhost:8080"

## Full deploy: sync code → rebuild link-handler → reseed → immediate heartbeat cycle
## data/ (oxigraph DB, logs) is excluded from rsync — VPS runtime state is never overwritten.
## coordinator-registered spaces (urn:mak:space/* graphs) are never cleared by seed --force.
## Heartbeat is triggered immediately after startup so the map is live without waiting 10min.
publish: sync-app
	@echo "→ full stack restart + rebuild on VPS..."
	ssh $(REMOTE) 'cd $(REMOTE_APP) && docker compose -f infra/docker-compose.yml down && docker compose -f infra/docker-compose.yml up -d --build'
	@echo "→ waiting for link-handler to be healthy..."
	ssh $(REMOTE) 'timeout 90 sh -c "until docker exec maps-link-handler python3 -c \"import urllib.request; urllib.request.urlopen('"'"'http://localhost:8000/health'"'"')\" 2>/dev/null; do sleep 3; done" && echo ok'
	@echo "→ reseeding Oxigraph on VPS..."
	ssh $(REMOTE) 'cd $(REMOTE_APP) && source venv/bin/activate && python scripts/seed_import.py --force'
	@echo "→ triggering immediate heartbeat cycle (updates all spaces + rematerializes GeoJSON)..."
	ssh $(REMOTE) 'docker exec maps-link-handler python3 -c "import httpx; r = httpx.post(\"http://localhost:8000/api/heartbeat/run\", timeout=180); print(\"heartbeat:\", r.status_code)"'
	@echo "✓ published — map live"

## Push everything (app + gateway confs)
sync: sync-app sync-gateway

## Push project root to VPS — all files except dev-only artifacts
sync-app:
	rsync -avz --delete $(RSYNC_EXCLUDE) \
		. \
		$(REMOTE):$(REMOTE_APP)/
	@echo "✓ app synced to $(REMOTE):$(REMOTE_APP)"

## Rebuild containers on VPS without syncing — use when code is already current on VPS
## (e.g. after a server-side config edit). If local code changed, use make publish instead.
vps-rebuild:
	ssh $(REMOTE) 'cd $(REMOTE_APP) && docker compose -f infra/docker-compose.yml down && docker compose -f infra/docker-compose.yml up -d --build'

## Sync code then reseed + heartbeat on VPS — use when seed data/scripts changed but containers are fine
vps-seed: sync-app
	@echo "→ reseeding Oxigraph on VPS..."
	ssh $(REMOTE) 'cd $(REMOTE_APP) && source venv/bin/activate && python scripts/seed_import.py --force'
	@echo "→ triggering heartbeat cycle..."
	ssh $(REMOTE) 'docker exec maps-link-handler python3 -c "import httpx; r = httpx.post(\"http://localhost:8000/api/heartbeat/run\", timeout=180); print(\"heartbeat:\", r.status_code)"'
	@echo "✓ VPS reseeded"

## ── CANARY ───────────────────────────────────────────────────────────────────
## Mother Sands diagnostic canary — three-axis fault attribution tool.
## Start the endpoint first: python3 data/canary/mother-sands-endpoint.py &
## See docs/canary-setup.md and docs/canary-operator-runbook.md for full guide.

## Restore served.json from committed baseline (healthy + confirmed + open)
canary-reset:
	cp data/canary/baseline.json $(CANARY_SERVED)
	@echo "✓ canary reset to baseline"

## ── Axis A — Reachability ────────────────────────────────────────────────────

canary-a-reachable:
	$(CANARY_SCENARIO) a-reachable

canary-a-timeout:
	$(CANARY_SCENARIO) a-timeout
	@echo "  → restart the endpoint with MODE=timeout for this to take effect"

canary-a-dns-fail:
	@echo "  → point the heartbeat at an unresolvable URL to test DNS failure"
	@echo "  → see docs/canary-operator-runbook.md#axis-a-dns-fail"

canary-a-http-error:
	$(CANARY_SCENARIO) a-http-error
	@echo "  → restart the endpoint with MODE=503 for this to take effect"

## Run all Axis A scenarios in sequence
canary-axis-a: canary-a-reachable canary-a-timeout canary-a-dns-fail canary-a-http-error
	@echo "✓ Axis A scenarios complete"

## ── Axis B — Lifecycle Freshness ─────────────────────────────────────────────

canary-b-seeded:
	$(CANARY_SCENARIO) b-seeded

canary-b-confirmed:
	$(CANARY_SCENARIO) b-confirmed

canary-b-aging:
	$(CANARY_SCENARIO) b-aging

canary-b-zombie:
	$(CANARY_SCENARIO) b-zombie

canary-b-closed:
	$(CANARY_SCENARIO) b-closed

## Run all Axis B scenarios in sequence
canary-axis-b: canary-b-seeded canary-b-confirmed canary-b-aging canary-b-zombie canary-b-closed
	@echo "✓ Axis B scenarios complete"

## ── Axis C — Open/Close Boolean ──────────────────────────────────────────────
## Note: false branch is "shut" (not "close") — guards against collision with
## Axis B lifecycle "closed" naming.

canary-c-openclose-open:
	$(CANARY_SCENARIO) c-openclose-open

canary-c-openclose-shut:
	$(CANARY_SCENARIO) c-openclose-shut

## Run all Axis C scenarios in sequence
canary-axis-c: canary-c-openclose-open canary-c-openclose-shut
	@echo "✓ Axis C scenarios complete"

## ── Group runners ────────────────────────────────────────────────────────────

## Run ALL canary scenarios across all three axes
canary-all: canary-axis-a canary-axis-b canary-axis-c
	@echo "✓ All canary scenarios complete"

## ── Coherence report ─────────────────────────────────────────────────────────

## Query all four layers (endpoint file, heartbeat_log, Oxigraph, GeoJSON) and report divergences
canary-report:
	source venv/bin/activate && python3 scripts/canary_coherence_report.py

## ── Demo cycle ───────────────────────────────────────────────────────────────

## Thin lifecycle chain for federated PoC demo: seed → confirmed → aging → zombie → closed/dead
canary-demo-cycle: canary-reset canary-b-seeded canary-b-confirmed canary-b-aging canary-b-zombie canary-b-closed
	@echo "✓ demo cycle complete — Mother Sands walked through full lifecycle"

## Push gateway nginx confs only (triggers manual nginx reload on VPS)
sync-gateway:
	rsync -avz \
		infra/gateway-nginx/ \
		$(REMOTE):$(REMOTE_GW)/
	@echo "✓ gateway confs synced to $(REMOTE):$(REMOTE_GW)"
	@echo "  → reload nginx manually if conf changed: ssh $(REMOTE) 'docker exec nginx-gateway nginx -s reload'"
