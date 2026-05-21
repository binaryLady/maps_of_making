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

.PHONY: sync sync-app sync-gateway publish startdev rebuild seed seed-spaceapi heartbeat devdeploy reset vps-rebuild vps-seed help endpoint
.PHONY: c-reset c-activate c-report c-demo c-all
.PHONY: ca-reachable ca-timeout ca-dns-fail ca-http-error caxis-a
.PHONY: cb-seeded cb-confirmed cb-aging cb-zombie cb-dead cb-closed caxis-b c-demo-on c-demo-off
.PHONY: cc-open cc-shut caxis-c

CANARY_DB ?= data/tasks/heartbeat_log.db
CANARY_SERVED := web/canary/mother-sands.json
CANARY_SCENARIO := source venv/bin/activate && python3 scripts/canary_scenarios.py

# Back-date helper: rewrites mom:updatedAt in urn:mak:canary to (now - N days)
# via direct SPARQL UPDATE against Oxigraph (port 7878, exposed on dev), then
# triggers a rematerialize-only inside the container so the new timestamp
# lands in the GeoJSON. Usage: $(call BACKDATE_CANARY,45)
define BACKDATE_CANARY
TS=$$(date -u -d '-$(1) days' +%Y-%m-%dT%H:%M:%SZ) ; \
curl -s -X POST http://localhost:7878/update \
  -H "Content-Type: application/sparql-update" \
  -d "PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#> \
      PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> \
      DELETE WHERE { GRAPH <urn:mak:canary> { <urn:mak:canary/mother-sands> mom:updatedAt ?t } } ; \
      INSERT DATA { GRAPH <urn:mak:canary> { <urn:mak:canary/mother-sands> mom:updatedAt \"$$TS\"^^xsd:dateTime } }" \
  && echo "✓ mom:updatedAt back-dated to $$TS ($(1)d ago)" ; \
podman exec maps-link-handler python3 -c \
  "import httpx; r = httpx.post('http://localhost:8000/api/rematerialize', timeout=30); print('rematerialize:', r.status_code)"
endef

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
	@echo "make c-reset      — restore canary from baseline (seeded, no endpointUrl)"
	@echo "make c-activate   — add mom:endpointUrl to canary (simulates claiming step)"
	@echo "make c-report     — per-layer coherence-diff report"
	@echo "make c-demo-on    — turn on seconds-scale canary thresholds (live demo)"
	@echo "make c-demo-off   — restore normal day-scale thresholds"
	@echo "make c-demo       — seeded→confirmed→aging→zombie→dead→closed lifecycle chain"
	@echo "make c-all        — run all scenarios across all axes"
	@echo "make ca-{reachable,timeout,dns-fail,http-error}     — Axis A"
	@echo "make cb-{seeded,confirmed,aging,zombie,dead,closed} — Axis B"
	@echo "make cc-{open,shut}                              — Axis C"
	@echo "make caxis-{a,b,c}   — run full axis"
	@echo "make endpoint     — push canary JSON + logo to VPS"

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

## DEPRECATED (Story 3.4b) — bulk seed data archived; use coordinator URL onboarding or fresh canary.
seed:
	@echo "❌ make seed is deprecated (Story 3.4b clean slate)"
	@echo "   Bulk seed files archived to data/archive/"
	@echo "   Use: make canary-reset, or register spaces via coordinator URL onboarding"
	@exit 1

## Trigger an immediate heartbeat cycle locally — populates Zone 3, rematerializes GeoJSON
heartbeat:
	podman exec maps-link-handler python3 -c \
	  "import httpx; r = httpx.post('http://localhost:8000/api/heartbeat/run', timeout=180); print('heartbeat:', r.status_code)"

## Import the SpaceAPI federation directory (https://directory.spaceapi.io/) into local Oxigraph.
## Each space tagged mom:memberOf <urn:mak:network/spaceapi> → "SPACEAPI" filter chip on the map.
seed-spaceapi:
	source venv/bin/activate && python scripts/seed_spaceapi.py --force
	$(MAKE) heartbeat

## Full local pipeline: rebuild + heartbeat (no bulk seed — Story 3.4b clean slate)
## Pre-seeded spaces load via coordinator URL onboarding or fresh canary injection.
devdeploy: rebuild heartbeat
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
## Single source of truth: https://mapsofmaking.org/canary/mother-sands.json
## Scenario cycle: make cb-zombie → writes web/canary/mother-sands.json → push to VPS → heartbeat
## See docs/canary-setup.md and docs/canary-operator-runbook.md for full guide.

## Push canary JSON + logo to VPS static server
endpoint:
	@mkdir -p web/canary
	rsync -avz web/canary/mother-sands.json $(REMOTE):$(REMOTE_APP)/web/canary/
	rsync -avz web/mother-sands-logo.png $(REMOTE):$(REMOTE_APP)/web/
	@echo "✓ canary + logo pushed → https://mapsofmaking.org/canary/mother-sands.json"

## Restore web/canary/mother-sands.json from committed baseline (seeded state, no endpoint URL)
## Also removes mom:endpointUrl from Oxigraph so heartbeat skips it — simulates fresh seeded space.
c-reset:
	@mkdir -p web/canary
	cp data/canary/baseline.json $(CANARY_SERVED)
	@chmod 644 $(CANARY_SERVED)
	$(MAKE) endpoint
	source venv/bin/activate && python3 scripts/load_canary.py
	curl -s -X POST http://localhost:7878/update \
	  -H "Content-Type: application/sparql-update" \
	  -d "PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#> \
	      DELETE WHERE { GRAPH <urn:mak:canary> { <urn:mak:canary/mother-sands> mom:endpointUrl ?u } }" \
	  && echo "✓ endpointUrl removed from Oxigraph — canary is seeded"
	@# Wipe snapshot_store row — load_canary.py only touches Oxigraph; the SQLite
	@# snapshot would otherwise carry observed_at / fetch_status forward into the
	@# rematerialized GeoJSON and the marker would not be cleanly seeded.
	@podman exec maps-link-handler python3 -c "import sqlite3, os; from snapshot_store import _get_db_path; c=sqlite3.connect(_get_db_path()); c.execute(\"DELETE FROM snapshots WHERE uid='mother-sands'\"); c.commit(); c.close(); print('✓ snapshot_store row cleared')" 2>/dev/null || echo "  (snapshot_store wipe skipped — container not running)"
	podman exec maps-link-handler python3 -c \
	  "import httpx; r = httpx.post('http://localhost:8000/api/heartbeat/run', timeout=60); print('rematerialize:', r.status_code)" \
	  && echo "✓ GeoJSON rematerialized"
	@echo "✓ canary reset to seeded baseline"

## Add mom:endpointUrl to canary (simulates the operator "claiming" their space).
## After c-reset the canary is seeded with no endpointUrl, so the heartbeat
## transformer skips it (no mom:updatedAt → Axis B silent). This target adds the
## endpointUrl back so the next heartbeat runs the full fetch→diff→updatedAt
## path against the canary. Lets us skip the manual claiming flow during dev.
c-activate:
	@CANARY_URL="$${CANARY_ENDPOINT_URL:-https://mapsofmaking.org/canary/mother-sands.json}" ; \
	curl -s -X POST http://localhost:7878/update \
	  -H "Content-Type: application/sparql-update" \
	  -d "PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#> \
	      INSERT DATA { GRAPH <urn:mak:canary> { <urn:mak:canary/mother-sands> mom:endpointUrl <$$CANARY_URL> } }" \
	  && echo "✓ endpointUrl added to Oxigraph — canary is claimed ($$CANARY_URL)"
	$(MAKE) heartbeat
	@echo "✓ canary activated — Axis B (mom:updatedAt) will advance on content change"

## ── Axis A — Reachability ────────────────────────────────────────────────────

ca-reachable:
	$(CANARY_SCENARIO) a-reachable
	$(MAKE) endpoint heartbeat

ca-timeout:
	$(CANARY_SCENARIO) a-timeout
	@echo "  → MODE=timeout: endpoint accepts TCP but never replies"
	$(MAKE) endpoint heartbeat

ca-dns-fail:
	@echo "  → point the heartbeat at an unresolvable URL to test DNS failure"
	@echo "  → see docs/canary-operator-runbook.md#axis-a-dns-fail"

ca-http-error:
	$(CANARY_SCENARIO) a-http-error
	@echo "  → MODE=503: endpoint returns Service Unavailable"
	$(MAKE) endpoint heartbeat

caxis-a: ca-reachable ca-timeout ca-dns-fail ca-http-error
	@echo "✓ Axis A complete"

## ── Axis B — Lifecycle Freshness ─────────────────────────────────────────────
## Naming:
##   cb-seeded    = no endpointUrl yet — alias of c-reset (clean slate, no claim)
##   cb-confirmed = endpointUrl registered, recent updated_at — alias of c-activate
##   cb-aging/zombie/dead = real updated_at exists but is back-dated to land in
##                          that bucket (real pipeline ran; only the timestamp
##                          is shifted)
##   cb-closed    = explicit operator-declared closure (terminal-by-declaration);
##                  distinct from cb-dead (terminal-by-inactivity)
## Back-dating posts to /api/canary/backdate which rewrites mom:updatedAt in
## the canary graph and re-emits the GeoJSON. No re-fetch — preserves the live
## scenario payload visible in the Source Data terminal.

# 30/86400 ≈ 30s. With CANARY_THRESHOLD_MODE=demo, the canary's
# thresholds_override compresses the bucket walk to seconds; pick a days value
# above the relevant compressed threshold so the bucket sticks.
cb-aging:
	$(CANARY_SCENARIO) b-aging
	$(MAKE) endpoint heartbeat
	@$(call BACKDATE_CANARY,45)

cb-zombie:
	$(CANARY_SCENARIO) b-zombie
	$(MAKE) endpoint heartbeat
	@$(call BACKDATE_CANARY,120)

cb-dead:
	$(CANARY_SCENARIO) b-zombie
	$(MAKE) endpoint heartbeat
	@$(call BACKDATE_CANARY,365)

cb-closed:
	$(CANARY_SCENARIO) b-closed
	$(MAKE) endpoint heartbeat
	@curl -s -X POST http://localhost:7878/update \
	  -H "Content-Type: application/sparql-update" \
	  -d "PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#> \
	      PREFIX xsd: <http://www.w3.org/2001/XMLSchema#> \
	      DELETE WHERE { GRAPH <urn:mak:canary> { <urn:mak:canary/mother-sands> mom:operatorDeclaredClosed ?c } } ; \
	      INSERT DATA { GRAPH <urn:mak:canary> { <urn:mak:canary/mother-sands> mom:operatorDeclaredClosed \"true\"^^xsd:boolean } }" \
	  && echo "✓ mom:operatorDeclaredClosed=true (terminal-by-declaration)"
	@podman exec maps-link-handler python3 -c \
	  "import httpx; r = httpx.post('http://localhost:8000/api/rematerialize', timeout=30); print('rematerialize:', r.status_code)"

# Aliases — natural lifecycle entry points
cb-seeded: c-reset
cb-confirmed: c-activate

caxis-b: cb-seeded cb-confirmed cb-aging cb-zombie cb-dead cb-closed
	@echo "✓ Axis B complete"

## ── Axis C — Open/Close Boolean ──────────────────────────────────────────────

cc-open:
	$(CANARY_SCENARIO) c-openclose-open
	$(MAKE) endpoint heartbeat

cc-shut:
	$(CANARY_SCENARIO) c-openclose-shut
	$(MAKE) endpoint heartbeat

caxis-c: cc-open cc-shut
	@echo "✓ Axis C complete"

## ── Group runners ────────────────────────────────────────────────────────────

c-all: caxis-a caxis-b caxis-c
	@echo "✓ All canary scenarios complete"

## ── Coherence report ─────────────────────────────────────────────────────────

c-report:
	source venv/bin/activate && python3 scripts/canary_coherence_report.py

## ── Demo cycle ───────────────────────────────────────────────────────────────
## c-demo-on / c-demo-off restart the link-handler with seconds-scale thresholds
## on (or off) for the canary feature only. With demo mode ON, after cb-confirmed
## the canary will naturally walk aging → zombie → dead in ~minutes against the
## real (recent) mom:updatedAt timestamp. Use cb-aging/zombie/dead/closed to pin
## a specific bucket via back-dating instead of waiting.

## Demo mode lives in the canary payload itself (ext_mom.thresholdMode).
## Single source of truth — the canary endpoint tells the link-handler whether
## to emit a compressed thresholds_override. Symmetric with how simulatedAge
## injects state into the payload.
c-demo-on:
	$(CANARY_SCENARIO) threshold-mode on
	$(MAKE) endpoint heartbeat
	@echo "✓ canary demo thresholds ON (aging≈30s, zombie≈60s, dead≈120s)"

c-demo-off:
	$(CANARY_SCENARIO) threshold-mode off
	$(MAKE) endpoint heartbeat
	@echo "✓ canary demo thresholds OFF (normal day-scale)"

c-demo: c-reset c-activate cb-aging cb-zombie cb-dead cb-closed
	@echo "✓ demo cycle complete — Mother Sands walked seeded → confirmed → aging → zombie → dead → closed"

## Push gateway nginx confs only (triggers manual nginx reload on VPS)
sync-gateway:
	rsync -avz \
		infra/gateway-nginx/ \
		$(REMOTE):$(REMOTE_GW)/
	@echo "✓ gateway confs synced to $(REMOTE):$(REMOTE_GW)"
	@echo "  → reload nginx manually if conf changed: ssh $(REMOTE) 'docker exec nginx-gateway nginx -s reload'"
