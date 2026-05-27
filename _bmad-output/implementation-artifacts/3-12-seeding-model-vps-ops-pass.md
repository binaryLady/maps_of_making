# Story 3.12: Seeding Model + VPS Ops Pass

Status: done (retro-recorded — implemented inline during operator session 2026-05-27)

> **Operator-driven cleanup session, not a planned story.** Captures a half-day of
> incremental work that landed during a single conversation: rewriting the VPS deploy
> targets, generalising the seed pipeline into list-based + bundle-based paths,
> consolidating coordinator/network conventions, and shipping the first coordinator-
> facing doc. Recorded as a story so the diff is traceable and the deferred items
> are not lost.

## Story

As an operator,
I want a clean separation between *publishing code* (no data mutation), *seeding lists* of
SpaceAPI endpoints (Path A), and *seeding bundles* of pre-coordinated records (Path B),
plus a coordinator-facing hosting guide,
so that I can grow the registry network by network without breaking the data, and so the
first wave of coordinator outreach has something to point at.

## What landed

### A. VPS deploy targets cleaned up

- **`make publish` no longer seeds.** Previously called the deprecated
  `seed_import.py`; that step is removed. `publish` now does only: `sync-app` →
  `docker compose down/up --build` → healthcheck → `/api/heartbeat/run` → gateway
  nginx reload. Data is never touched.
- **`make vps-reset`** (created earlier) folds in the gateway reload — fixes the
  502-after-rebuild gotcha (gateway's `resolver`-based `proxy_pass` fail-caches
  when `maps-nginx` restarts).
- **`docs/vps-operations.md`** — new runbook covering the two-layer nginx
  topology, domain table, publish vs reset comparison, the 502 fix, and quick-check
  commands. Documents the deprecation of `mapofmaking.debarquin.eu` (removed from
  gateway conf 2026-05-27).

### B. Path A — `make vps-seed LIST=… NETWORK=…`

- `scripts/seed_spaceapi.py` generalised: accepts `--list <url-or-path>` (URL **or**
  local JSON file) and `--network <slug>`. List shapes supported: `{name: url}`
  (the SpaceAPI directory shape) **and** `[{name, url, network?}, …]` (per-entry
  network override). Default still `directory.spaceapi.io` for back-compat.
- **Cross-network protect**: a seed run only overwrites graphs whose existing
  `mom:source` matches the current run's source-tag. Path A no longer clobbers
  Path B (or vice versa) under `--force`.
- `make vps-seed` runs the script *inside* the link-handler container via
  `docker cp` + `docker exec` (load_canary pattern — no Python venv needed on VPS).
  Local-file lists are scp'd to a VPS tmp path before docker-cp into the container.
- `data/seed-lists/test-batch.json` — 10 European SpaceAPI endpoints for end-to-end
  pipeline exercising. The full SpaceAPI directory was reseeded (~244 spaces).

### C. Path B — `make vps-seed-bundle BUNDLE=… NETWORK=… [SOURCE=…]`

- `scripts/seed_bundle.py` — new standalone seeder for mom:Space JSON-LD bundles
  (records with no SpaceAPI endpoint). Writes name, geo, address fields,
  `schema:url`, `mom:profileUrl`, `schema:knowsAbout`, `mom:source`,
  `mom:memberOf`, `mom:operationalState "seeded"`, `mom:geolocationFidelity`.
- **No `mom:endpointUrl` written** → heartbeat skips → pin stays grey/seeded
  forever until claimed. Confirmed via `web/app.js:341-350` — `markerKind() ===
  'seeded'` whenever both freshness tokens are absent.
- **URI scheme**: `urn:mak:space/<slug-name>-<slug-city>` (compound slug from VOW
  data, which carries structured `schema:addressLocality`). Falls back to just
  `<slug-name>` if no city.
- **Claim-merge in `register_url`**: new helper `_find_seeded_graph_by_name`
  (SPARQL, case-insensitive name match with `mom:source` starting `"scraped-"`).
  When a coordinator self-registers a SpaceAPI URL whose name matches a bundle
  record, the existing graph URI is reused — the existing `DROP SILENT + INSERT`
  envelope cleanly flips `mom:source` to `"self-registered"` in place. Grey →
  live, no orphan, no UI churn.
- All 566 VOW records (`data/archive/moms_seed.json`) seed successfully — no
  losses, all in-bbox.

### D. Coordinator-declared `memberOf`

- `scripts/spaceapi_extract/core.py` honors a top-level `memberOf` field (string
  or list of slugs; `ext_mom.memberOf` as fallback). Bare slugs auto-expand to
  `urn:mak:network/<slug>`; full URIs pass through.
- `scripts/spaceapi_extract/sparql.py` — new `_IRI_LIST_PREDS = {"mom:memberOf"}`
  for multi-value IRI emission (one triple per slug); `mom:profileUrl` added to
  `_IRI_PREDS`.
- Flows automatically through register, heartbeat (`write_payload_fields`), and
  canary loader. Seed-time path strips `mom:memberOf` from extracted fields so
  the `--network` envelope stays authoritative there.
- `data/canary/baseline.json` — added `memberOf: ["canary"]` (next heartbeat
  tick writes the triple). Also added `ext_fab.sdgs: [9, 11, 12, 14, 17]` as a
  placeholder field; no triples written yet (deferred).

### E. Heartbeat fediverse hygiene

- Heartbeat fetcher (`infra/link_handler/pipeline.py:57`) now sends
  `User-Agent: MapsOfMaking-heartbeat/1.0 (+https://mapsofmaking.org)`.
  Diagnosed via Ko-Lab: Cloudflare WAF rejected default `httpx` UA with 403,
  blocking heartbeat refresh and leaving the space stuck in `seeded` after a
  successful seed. Friendly UA is also good federation citizenship at the
  10-minute cadence.
- `infra/link_handler/config.yaml:17` — `heartbeat_concurrency` bumped 8 → 24
  in anticipation of growing space count.

### F. Country chip works again

- `web/app.js` — country filter now reads `s.country_code` (was `s.country`,
  which materializer never populates from SpaceAPI). Extended `countryLabel`
  to 18 European codes + `sol-3`. Empty buckets filtered out.

### G. Coordinator hosting guide

- `docs/host-your-space.md` — minimal page for coordinators: what to put in the
  JSON, where to host it (GitHub Pages / GitLab / own site / gist), how to
  submit, common pitfalls. Designed to be linkable from outreach DMs.

## Deferred (recorded in `deferred-work.md`)

- **Network membership handshake verification** — currently honor declared
  `memberOf` on trust; should cross-check declared network's directory contains
  the endpoint URL, emit `mom:membershipStatus "verified"` vs
  `"self-claimed-unverified"`.
- **SDG ontology + processing** — `ext_fab.sdgs` is stored verbatim; predicate
  + ontology namespace + UI badge all TBD.
- **Reverse-geocode for missing country_code** — only ~14% of SpaceAPI spaces
  publish `location.country_code`. VOW bundle masks this for German-language
  spaces; revisit once we see real coverage gaps.

## Not covered here (next sessions)

- **Self-registration claim flow end-to-end test** — `_find_seeded_graph_by_name`
  is wired but unexercised live; deferred to Epic 4-b along with the magic-link
  email flow.
- **RFF mockup bundle seed** — same script can ingest `data/archive/rff_mockup.json`
  via `make vps-seed-bundle BUNDLE=… NETWORK=rff`. One-line operator action;
  not run yet.
- **Logo-as-shortcut UI** — was the original quick-dev request that started the
  session; landed early as a small `web/app.js` + `maps-of-making.html` change
  (logo `#logo-shortcut` opens Mother Sands).

## Acceptance (retro-validated against live VPS)

1. `make publish` runs without seed errors; gateway reload prevents 502s.
2. `make vps-seed` (default args) seeds the full SpaceAPI directory; `make
   vps-seed LIST=… NETWORK=test-batch` seeds 10 spaces under their own chip.
3. `make vps-seed-bundle BUNDLE=data/archive/moms_seed.json NETWORK=vow` seeds
   566 VOW spaces as grey/seeded pins; VOW chip filter works; country chip
   populates from VOW's structured addresses.
4. Ko-Lab and other Cloudflare-fronted SpaceAPI endpoints heartbeat
   successfully under the new UA.
5. Logo click opens the Mother Sands canary card.
6. `docs/host-your-space.md` and `docs/vps-operations.md` are present and
   self-contained.

## Files touched

- `Makefile` — `publish` (remove seed), `vps-reset` (gateway reload), `vps-seed`
  (generalised), `vps-seed-bundle` (new), `seed-spaceapi` (LIST/NETWORK args),
  help text.
- `scripts/seed_spaceapi.py` — `--list` + `--network` args, cross-network protect.
- `scripts/seed_bundle.py` — new.
- `scripts/spaceapi_extract/core.py` — `memberOf` extraction.
- `scripts/spaceapi_extract/sparql.py` — `_IRI_LIST_PREDS`, `mom:profileUrl` in
  `_IRI_PREDS`.
- `infra/link_handler/main.py` — `_find_seeded_graph_by_name`, claim-merge in
  `register_url`.
- `infra/link_handler/pipeline.py` — heartbeat UA.
- `infra/link_handler/config.yaml` — `heartbeat_concurrency: 24`.
- `infra/gateway-nginx/06-mapsofmaking.conf` — debarquin.eu blocks removed.
- `web/app.js` — country chip uses `country_code`; `COUNTRY_LABELS` table; logo
  shortcut handler.
- `web/maps-of-making.html` — `#logo-shortcut` element.
- `data/canary/baseline.json` — `memberOf`, `ext_fab.sdgs`.
- `data/seed-lists/test-batch.json` — new (10 European SpaceAPI endpoints).
- `docs/vps-operations.md` — new.
- `docs/host-your-space.md` — new.
- `_bmad-output/implementation-artifacts/deferred-work.md` — 3 new entries.
