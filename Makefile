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

.PHONY: sync sync-app sync-gateway publish startdev rebuild seed seed-spaceapi heartbeat devdeploy reset vps-rebuild vps-seed vps-reset help endpoint
.PHONY: c-reset c-activate c-demo c-all
.PHONY: ca-reachable ca-timeout ca-dns-fail ca-http-error caxis-a
.PHONY: cb-seeded cb-confirmed cb-aging cb-zombie cb-dead cb-closed caxis-b c-demo-on c-demo-off
.PHONY: cc-open cc-shut caxis-c

CANARY_DB ?= data/tasks/snapshot_store.db
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
	@echo "make publish       — push code: sync + down/up --build + heartbeat + gateway reload (no seed)"
	@echo "make sync          — sync everything (app + gateway confs)"
	@echo "make sync-app      — sync project root (excl. dev artifacts) to VPS"
	@echo "make sync-gateway  — sync gateway nginx confs (manual reload needed)"
	@echo "make vps-rebuild   — rebuild containers on VPS (no sync — code must be current)"
	@echo "make vps-seed [LIST=… NETWORK=…] — seed SpaceAPI list on VPS (default: directory.spaceapi.io, network=spaceapi)"
	@echo "make vps-seed-bundle BUNDLE=… NETWORK=… [SOURCE=…] — seed Path B bundle (grey/claimable pins, no endpoint)"
	@echo "make vps-reset     — DESTRUCTIVE: wipe VPS Oxigraph + SQLite, rebuild, reload canary only"
	@echo "── CANARY ───────────────────────────────────────────────────────────"
	@echo "make c-reset      — restore canary from baseline (seeded, no endpointUrl)"
	@echo "make c-activate   — add mom:endpointUrl to canary (simulates claiming step)"
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

## Seed a SpaceAPI endpoint list into local Oxigraph. LIST = URL or local path
## (default: directory.spaceapi.io). NETWORK = filter-chip slug (default: spaceapi).
## Examples:
##   make seed-spaceapi
##   make seed-spaceapi LIST=data/seed-lists/test-batch.json NETWORK=test-batch
seed-spaceapi:
	source venv/bin/activate && python scripts/seed_spaceapi.py --list "$(LIST)" --network "$(NETWORK)" --force
	$(MAKE) heartbeat

## Full local pipeline: rebuild + heartbeat (no bulk seed — Story 3.4b clean slate)
## Pre-seeded spaces load via coordinator URL onboarding or fresh canary injection.
devdeploy: rebuild heartbeat
	@echo "✓ local dev stack live — map at http://localhost:8080"

## DESTRUCTIVE: wipe Oxigraph triplestore + heartbeat DB, then full reseed via devdeploy.
## Loses ALL coordinator-registered spaces. Use before demos / fresh-state tests.
## On VPS, the equivalent is intentionally manual — see data-lifecycle.md.
reset:
	@echo "⚠  This will wipe data/oxigraph/ and data/tasks/snapshot_store.db"
	@echo "   Coordinator-registered spaces will be lost."
	@read -p "   Type 'reset' to confirm: " ans && [ "$$ans" = "reset" ] || (echo "aborted"; exit 1)
	podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml down
	rm -rf data/oxigraph/* data/tasks/snapshot_store.db data/tasks/heartbeat_log.db data/tasks/gap_log.txt data/tasks/oxigraph.db web/data/spaces.geojson
	@sleep 2
	$(MAKE) devdeploy
	@echo "✓ reset complete — refresh your browser at http://localhost:8080"

## Push latest code: sync → docker down → up --build → heartbeat → gateway reload.
## Does NOT touch data/ (rsync excludes it) and does NOT seed — use `make vps-reset`
## to factory-reset, or `make vps-seed LIST=…` to add a network. Heartbeat refreshes
## already-claimed spaces so the map updates immediately instead of waiting 10min.
publish: sync-app
	@echo "→ full stack restart + rebuild on VPS..."
	ssh $(REMOTE) 'cd $(REMOTE_APP) && docker compose -f infra/docker-compose.yml down && docker compose -f infra/docker-compose.yml up -d --build'
	@echo "→ waiting for link-handler to be healthy..."
	ssh $(REMOTE) 'timeout 90 sh -c "until docker exec maps-link-handler python3 -c \"import urllib.request; urllib.request.urlopen('"'"'http://localhost:8000/health'"'"')\" 2>/dev/null; do sleep 3; done" && echo ok'
	@echo "→ triggering immediate heartbeat cycle (refreshes claimed spaces + rematerializes GeoJSON)..."
	ssh $(REMOTE) 'docker exec maps-link-handler python3 -c "import httpx; r = httpx.post(\"http://localhost:8000/api/heartbeat/run\", timeout=300); print(\"heartbeat:\", r.status_code)"'
	@echo "→ reloading gateway nginx (clears stale upstream cache after maps-nginx recreate)..."
	ssh $(REMOTE) 'docker exec nginx-gateway nginx -s reload'
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

## Seed a SpaceAPI endpoint list onto the VPS. LIST = URL or local path (default:
## directory.spaceapi.io). NETWORK = filter-chip slug (default: spaceapi).
## Runs the seed script inside the link-handler container; no venv needed on VPS.
## Examples:
##   make vps-seed                                                   # full SpaceAPI directory
##   make vps-seed LIST=data/seed-lists/test-batch.json NETWORK=test-batch
##   make vps-seed LIST=https://example.org/my-list.json NETWORK=vow
LIST    ?= https://directory.spaceapi.io/
NETWORK ?= spaceapi
vps-seed:
	@echo "→ staging seed script into maps-link-handler..."
	ssh $(REMOTE) 'cd $(REMOTE_APP) && docker cp scripts/seed_spaceapi.py maps-link-handler:/app/scripts/seed_spaceapi.py'
	@case "$(LIST)" in \
	  http://*|https://*) \
	    echo "→ seeding from URL: $(LIST) (network=$(NETWORK))..." ; \
	    ssh $(REMOTE) 'docker exec -e OXIGRAPH_ENDPOINT=http://oxigraph:7878 -e PYTHONPATH=/app maps-link-handler python3 /app/scripts/seed_spaceapi.py --list "$(LIST)" --network "$(NETWORK)" --force' ;; \
	  *) \
	    echo "→ uploading local list $(LIST) → VPS /tmp → container..." ; \
	    scp -q "$(LIST)" $(REMOTE):/tmp/mom-seed-list.json ; \
	    ssh $(REMOTE) 'docker cp /tmp/mom-seed-list.json maps-link-handler:/tmp/seed-list.json && rm -f /tmp/mom-seed-list.json' ; \
	    echo "→ seeding from file: $(LIST) (network=$(NETWORK))..." ; \
	    ssh $(REMOTE) 'docker exec -e OXIGRAPH_ENDPOINT=http://oxigraph:7878 -e PYTHONPATH=/app maps-link-handler python3 /app/scripts/seed_spaceapi.py --list /tmp/seed-list.json --network "$(NETWORK)" --force' ;; \
	esac
	@echo "→ triggering heartbeat cycle..."
	ssh $(REMOTE) 'docker exec maps-link-handler python3 -c "import httpx; r = httpx.post(\"http://localhost:8000/api/heartbeat/run\", timeout=300); print(\"heartbeat:\", r.status_code)"'
	@echo "→ rematerializing GeoJSON..."
	ssh $(REMOTE) 'docker exec maps-link-handler python3 -c "import httpx; r = httpx.post(\"http://localhost:8000/api/rematerialize\", timeout=30); print(\"rematerialize:\", r.status_code)"'
	@echo "✓ VPS seeded (network=$(NETWORK))"

## Seed a bundle of mom:Space JSON-LD records (Path B — spaces without an endpoint).
## BUNDLE = URL or local path to a JSON array of records. NETWORK = filter-chip slug.
## SOURCE = mom:source tag (default: scraped-<NETWORK>). Records become grey/seeded
## pins that coordinators can later claim in place by registering a SpaceAPI URL.
## Examples:
##   make vps-seed-bundle BUNDLE=data/archive/moms_seed.json NETWORK=vow
##   make vps-seed-bundle BUNDLE=data/archive/rff_mockup.json NETWORK=rff SOURCE=mock-rff
BUNDLE  ?= data/archive/moms_seed.json
SOURCE  ?=
vps-seed-bundle:
	@echo "→ staging bundle seed script into maps-link-handler..."
	ssh $(REMOTE) 'cd $(REMOTE_APP) && docker cp scripts/seed_bundle.py maps-link-handler:/app/scripts/seed_bundle.py'
	@case "$(BUNDLE)" in \
	  http://*|https://*) \
	    echo "→ seeding bundle from URL: $(BUNDLE) (network=$(NETWORK))..." ; \
	    ssh $(REMOTE) 'docker exec -e OXIGRAPH_ENDPOINT=http://oxigraph:7878 -e PYTHONPATH=/app maps-link-handler python3 /app/scripts/seed_bundle.py --bundle "$(BUNDLE)" --network "$(NETWORK)" $(if $(SOURCE),--source "$(SOURCE)") --force' ;; \
	  *) \
	    echo "→ uploading local bundle $(BUNDLE) → VPS /tmp → container..." ; \
	    scp -q "$(BUNDLE)" $(REMOTE):/tmp/mom-seed-bundle.json ; \
	    ssh $(REMOTE) 'docker cp /tmp/mom-seed-bundle.json maps-link-handler:/tmp/seed-bundle.json && rm -f /tmp/mom-seed-bundle.json' ; \
	    echo "→ seeding from file: $(BUNDLE) (network=$(NETWORK))..." ; \
	    ssh $(REMOTE) 'docker exec -e OXIGRAPH_ENDPOINT=http://oxigraph:7878 -e PYTHONPATH=/app maps-link-handler python3 /app/scripts/seed_bundle.py --bundle /tmp/seed-bundle.json --network "$(NETWORK)" $(if $(SOURCE),--source "$(SOURCE)") --force' ;; \
	esac
	@echo "→ rematerializing GeoJSON..."
	ssh $(REMOTE) 'docker exec maps-link-handler python3 -c "import httpx; r = httpx.post(\"http://localhost:8000/api/rematerialize\", timeout=60); print(\"rematerialize:\", r.status_code)"'
	@echo "✓ VPS bundle seeded (network=$(NETWORK))"

## DESTRUCTIVE: VPS analog of `make reset`. Wipes Oxigraph store + SQLite
## (heartbeat_log, snapshot_store) and materialized GeoJSON on the VPS, then
## rebuilds containers and seeds only the Mother Sands canary. Use to factory-
## reset the deployment; claim additional URLs afterwards through the admin UI.
vps-reset:
	@echo "⚠  This will wipe data/oxigraph/ and data/tasks/*.db on $(REMOTE)."
	@echo "   All coordinator-registered spaces will be lost. Only the Mother Sands"
	@echo "   canary will be reloaded."
	@read -p "   Type 'vps-reset' to confirm: " ans && [ "$$ans" = "vps-reset" ] || (echo "aborted"; exit 1)
	@echo "→ stopping containers on VPS..."
	ssh $(REMOTE) 'cd $(REMOTE_APP) && docker compose -f infra/docker-compose.yml down'
	@echo "→ wiping Oxigraph + SQLite + materialized GeoJSON on VPS..."
	ssh $(REMOTE) 'cd $(REMOTE_APP) && rm -rf data/oxigraph/* data/tasks/snapshot_store.db data/tasks/heartbeat_log.db data/tasks/gap_log.txt data/tasks/oxigraph.db web/data/spaces.geojson'
	@echo "→ rebuilding containers on VPS..."
	ssh $(REMOTE) 'cd $(REMOTE_APP) && docker compose -f infra/docker-compose.yml up -d --build'
	@echo "→ waiting for link-handler to be healthy..."
	ssh $(REMOTE) 'timeout 90 sh -c "until docker exec maps-link-handler python3 -c \"import urllib.request; urllib.request.urlopen('"'"'http://localhost:8000/health'"'"')\" 2>/dev/null; do sleep 3; done" && echo ok'
	@echo "→ staging canary loader + payload into container..."
	ssh $(REMOTE) 'cd $(REMOTE_APP) && docker cp scripts/load_canary.py maps-link-handler:/app/scripts/load_canary.py && docker exec maps-link-handler mkdir -p /app/web/canary && docker cp web/canary/mother-sands.json maps-link-handler:/app/web/canary/mother-sands.json'
	@echo "→ loading Mother Sands canary into Oxigraph..."
	ssh $(REMOTE) 'docker exec -e OXIGRAPH_URL=http://oxigraph:7878 -e PYTHONPATH=/app maps-link-handler python3 /app/scripts/load_canary.py'
	@echo "→ rematerializing GeoJSON..."
	ssh $(REMOTE) 'docker exec maps-link-handler python3 -c "import httpx; r = httpx.post(\"http://localhost:8000/api/rematerialize\", timeout=30); print(\"rematerialize:\", r.status_code)"'
	@echo "→ reloading gateway nginx (clears stale upstream cache after maps-nginx restart)..."
	ssh $(REMOTE) 'docker exec nginx-gateway nginx -s reload'
	@echo "✓ vps-reset complete — only Mother Sands canary in graph; claim additional URLs through the admin UI."

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
