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

## Deferred from: code review of 1-5-map-reads-from-oxigraph-geojson-materialization (2026-04-25)

- **Fixed temp filename `.geojson.tmp`** — `scripts/materialize_geojson.py`: concurrent invocations write to the same temp file, last writer wins then renames. Low risk while manually invoked; becomes real when Epic 3 scheduler triggers materialize on each ingest cycle. Fix: use `tempfile.NamedTemporaryFile` in the same directory.
- **GROUP_CONCAT `|` separator** — SPARQL query uses `|` as separator for specialties. A specialty containing `|` (possible with user-supplied data in Epic 2) will be split incorrectly. Epic 2 normalization pass should enforce no-pipe constraint in specialty values.
- **countryLabel() only handles FR/DE** — `web/app.js`: all other countries display raw ISO codes (e.g. `BE`, `NL`). Needs a full country lookup map. Defer to Epic 5 UI polish.

## Deferred from: code review of 1-4-author-mom-ontology-v0-load-mom-iop-into-oxigraph (2026-04-24)

- **distrobox fallback silent failure when container not running** — `scripts/load_ontology.sh`: if `maps-oxigraph` is not running, `podman inspect` fails silently, `CONTAINER_IP` is empty, script proceeds with the original unreachable URL without a clear diagnostic error message.
- **No `--max-time` on curl PUTs in load_ontology.sh** — load script can hang indefinitely on slow VPS or stalled container; health check has `-m 1` but actual PUT calls don't.

## Deferred from: Story 2.0 — UI Dataset Toggle and User Preferences (2026-04-25)

- **Legend does not show health map states** — `web/maps-of-making.html`: legend only lists seeded/confirmed/open/unlinked/broken. When health map is ON, aging ⚠️ / zombie 🧟 / dead 🪦 markers appear with no legend entry. Add a conditional legend section that shows when health map is active. → Epic 5 UI polish.
- **Status filter chips don't include health states** — `web/app.js` `buildFilterChips()`: statuses array is `['seeded','confirmed','open','unlinked','broken']`. When health map is ON, users can't filter by aging/zombie/dead. → Epic 5 (Story 5-5 tweaks panel decision).
- **Emoji in SVG markers: cross-browser rendering risk** — aging/zombie/dead markers use SVG `<text>` with emoji (⚠️🧟🪦). Rendering is browser/OS-dependent; may be invisible or misaligned on some Android WebViews. Replace with inline SVG glyphs if reported. → monitor, fix if bug reported.

## Deferred from: code review of Story 2.0 (2026-04-26)

- **Orphaned selected marker after GeoJSON reload** — Selection state in UI diverges from GeoJSON state if selection changes during reload. Requires larger state management refactor. → Epic 5 architecture pass.
- **DOM race: highlightSelected() async to renderMarkers()** — Visual glitch on slow networks when highlight called before tiles render. Timing issue from initial architecture, not introduced by this story. → Epic 5 rendering optimization.
- **geolocationFidelity enum not validated** — Future features using fidelity-based filtering will silently break on invalid enum values. Requires schema validation layer in SPARQL or backend. → Epic 2/5 data validation scope.
- **Search with untrusted data** — Specialty field concatenated directly into search haystack with no sanitization. Low risk in text search context but fragile pattern for future features. → Data validation and trust boundary refactor (Epic 2 scope).

## Deferred from: code review of 2-1-coordinator-url-onboarding-e2e (2026-04-26)

- **F7 — No auth on `/api/register-url`** — open-registration is spec-mandated ("without creating an account"); endpoint is open write to triplestore. Add rate-limiting and/or simple token in Epic 5 hardening story.
- **F8 — DROP SILENT overwrites on slug collision** — spec says "creating or overwriting `<urn:mak:space/{slug}>`"; two different spaces with the same slug silently clobber each other. Add collision detection / disambiguation in Epic 5.
- **F14 — Trailing slash on URI produces empty `space_id` in `_binding_to_feature`** — only triggered by externally sourced URIs with trailing slash; current internal generation cannot produce this.
- **F15 — GeoJSON re-fetch failure leaves new space out of `state.spaces`** — `selectSpace`/`embedSpace` silently find nothing if rematerialization hasn't completed when the browser re-fetches. Spec explicitly allowed re-fetch approach; patch in Epic 5 UX pass (patch state from API response as fallback).
- **F19 — `confirmed_at` column in `seed_transition.py` shows `mom:lastFetched`** — no distinct `mom:confirmedAt` triple is written at registration time; if the space is ever re-fetched, the column drifts from actual registration time. Add a `mom:confirmedAt` triple in the SPARQL UPDATE if this distinction matters in Epic 3+ tooling.

## Deferred from: Story 2.6 — Mobile Responsive Layout (2026-04-27 / 2026-04-28)

### Feature Requests & Design Decisions

- **Shareable query URL** — "I filtered to confirmed + open + electronics in Hamburg — here's the link." Implies URL state management for active filters as query params (e.g. `?filter=confirmed&city=hamburg&specialty=electronics`). Similar to the embed code snippet but as a shareable URL. Right for pilot when coordinators share filtered map views to communities. → Epic 5 or dedicated pilot story.
- **Swipe-to-dismiss bottom sheets** — drag-handle is visual only in 2.6; actual swipe gesture to dismiss requires a touch event handler. Low priority until user feedback confirms it's missed. → Epic 5 polish.
- **Health map suppressed on mobile** — design decision: health map toggle (Tweaks panel) is a desktop analytics feature; mobile defaults to fresh/confirmed view only. If a mobile health map use case emerges from pilot, revisit. → monitor.
- **Brave browser geolocation** — Brave on Android 16 silently blocks the permission prompt even when site is "allowed" in Brave settings. Not our bug; could add a "please use Chrome/Firefox" tooltip on silent denial if user research shows it's a real friction point for pilots. → monitor.
- **Near me button: no proximity highlight** — map flies to user location but spaces are not visually emphasised. Story spec marked this optional; implement distance-based dimming if pilot feedback requests it. → Epic 5.
- **Makefile `publish` does not pin `--force` semantics** — `seed_import.py --force` always clears and reloads the RFF mock graph. Once we have real coordinator data in prod we may want to skip RFF reload by default; add a `make publish-seed` vs `make publish` split. → Epic 3 / infra hardening.

### Code Review Findings (2026-04-28)

- **Redundant marker re-render optimization** [web/app.js:337] — Renders all markers on chip click instead of toggling filter state and selectively updating. Works correctly but inefficient; optimization deferred to post-launch refactor. Lower priority than functional patches.
- **Drawer state race condition** [web/app.js:780-803] — Rapid drawer open/close mutations could cause double syncTopbar() calls. Unlikely to manifest in real usage; defensive fix deferred to Epic 5 polish phase. Pre-emptive complexity not needed for current scope.
- **Inconsistent error handling pattern** [web/app.js:673-678] — Uses string interpolation for error messages inconsistently; Promise.reject() on line 473 already covers the core issue. Code quality improvement deferred to next refactor cycle. Not a functional bug.

## Deferred from: Story 2.2 — Detail Drawer (2026-04-26)

- **Admin: delete test/self-registered spaces** — No way to remove a space once registered. Test fixtures (e.g. `herberts-lab`) accumulate in Oxigraph. Cleanup requires `DROP GRAPH <urn:mak:space/{slug}>` plus `DROP SILENT` over snapshot graphs `urn:mak:space/{slug}/{YYYY-MM-DD}`, then rematerialize. Implement as admin row action: `DELETE /api/admin/space/{slug}` on `mak-link-handler`, gated by basic-auth at `/admin` (already wired in `infra/nginx/conf.d/app.conf:93`). → Story 4.5 (audit log) or new Story 4.6.

## Deferred from: Story 2.1 — Coordinator URL Onboarding E2E (2026-04-26)

- **Fixed temp filename in `_rematerialize_geojson()`** — `infra/link_handler/main.py` writes to a fixed `.geojson.tmp` path, same race condition as `materialize_geojson.py` (already noted above). Low risk while single-worker; becomes real when Epic 3 scheduler triggers concurrent rematerializations. Fix: `tempfile.NamedTemporaryFile` in same directory. → Epic 3 scheduler story.
- **Description and opening hours written to Oxigraph but not surfaced** — `register-url` writes `schema:description` and `schema:openingHours` to the named graph but the SPARQL SELECT (and therefore the space card) doesn't read them back. Gap between what's stored and what's displayed. → Story 2.2 detail drawer scope.
- **PII enforcement deferred** — Only `foaf:mbox` and `schema:Person` trigger the soft warning; `schema:email` / `schema:telephone` removed (business contact info). Full enforcement (hard block + admin alert for unambiguous personal data) is a separate hardening story. → Epic 5 or dedicated security hardening.
- **Geocoding hint for spaces missing coordinates** — When `coords_found: false`, the UI tells the user to add `schema:geo`. A nice-to-have improvement: if the JSON-LD contains `schema:address`, offer a geocoding lookup to pre-fill the latitude/longitude for them to paste into their file. No cost (Nominatim free tier), reduces friction. → Epic 5 UI polish or dedicated onboarding UX story.
