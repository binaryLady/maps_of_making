# Story 4.0: Admin Foundation — Subdomain, Auth, Space Comparison View

Status: draft

## Story

As a network admin,
I want to open `admin.mapsofmaking.org` in my browser and log in with a shared password,
so that I can see every registered space with its full ingestion lifecycle — seed data, live URL data, stored triples, and what the map card actually shows — side by side.

## Context

This story is the foundation of Epic 4. It establishes the admin subdomain, basic auth, and the core diagnostic view that makes the data lifecycle visible. The 4-column comparison (seed | url | stored | viewed) is the direct UI expression of `_bmad-output/planning-artifacts/data-lifecycle.md`.

Stories 4-1 through 4-5 build on top of this foundation.

**Demo goal:** during grant demos, a reviewer opens the admin page and can see a realistic spread of space states (confirmed Belgian spaces + RFF mockup stale/broken French spaces), drill into any space, and understand what's been ingested and what's missing.

---

## Acceptance Criteria

### AC1 — Admin subdomain routed and protected

**Given** nginx receives a request on `admin.mapsofmaking.org`

**When** no valid `Authorization: Basic` header is present

**Then** nginx returns `401 Unauthorized` with `WWW-Authenticate: Basic realm="mak-admin"`

**And** when valid credentials are supplied (`admin` / `MAK_ADMIN_PASSWORD` from `.env`), the request is proxied to the admin service

**And** the admin service is a minimal FastAPI app (`infra/admin/main.py`) running on `mak-admin:8001` inside the docker-compose network

**And** the nginx config uses `auth_basic` and `auth_basic_user_file` pointing to a `.htpasswd` file generated from `MAK_ADMIN_PASSWORD` at container startup (via entrypoint script, not committed)

### AC2 — Space list: all spaces with status summary

**Given** the admin is authenticated and loads `admin.mapsofmaking.org/`

**When** the page renders

**Then** a table lists all spaces from Oxigraph, one row per space, showing:
- Space name
- Space ID (slug)
- `mom:operationalState` (seeded / confirmed / broken)
- `mom:source` (scraped-vow / mock-rff / self-registered)
- `mom:lastFetched` (ISO datetime, formatted as relative time)
- Status badge using same colour vocabulary as the map (⚪🔵🔴)

**And** the table is sortable by status and source

**And** clicking a row opens the detail panel for that space (AC3)

**And** a header bar shows aggregate counts: `{n} confirmed · {n} seeded · {n} broken` (matching map pin states)

### AC3 — Per-space detail: 4-column comparison panel

**Given** the admin clicks a space row

**When** the detail panel opens (right-side drawer or full-page route `/space/{space_id}`)

**Then** four columns are shown side by side:

**Column A — Seed data** (what came from the VOW/RFF scrape):
- Reads from the space's named graph in Oxigraph
- Shows: name, address, profileUrl (VOW link), specialties (knowsAbout), geo fidelity
- Label: "Seed data" with source badge (VOW / RFF / —)

**Column B — URL data** (live fetch of the coordinator's endpoint):
- Performs a live `GET mom:endpointUrl` at page load time (or shows "seeded — no URL registered" if endpointUrl absent)
- Shows raw JSON-LD response (pretty-printed), or error message if unreachable
- Shows HTTP status code and fetch latency
- Label: "Live endpoint"

**Column C — Stored data** (all triples in Oxigraph for this space):
- SPARQL SELECT `?p ?o WHERE { GRAPH ?g { <space_uri> ?p ?o } }` across all named graphs
- Renders as a predicate → value table, grouped by graph
- Includes snapshot graphs (shows ingestion events as separate entries)
- Label: "Stored (Oxigraph)"

**Column D — Viewed data** (what the map card renders):
- Shows the GeoJSON feature for this space from the current `spaces.geojson`
- Renders it using the same `renderDetail()` logic as the public map (embedded iframe or JSON dump)
- Label: "Map card (current GeoJSON)"

**And** gaps are highlighted: a field present in Column B but absent or empty in Column D is shown with an amber `⚠ not surfaced` badge

### AC4 — Ingestion snapshot history per space

**Given** the detail panel is open for a confirmed or broken space

**When** the "Fetch history" section renders (below the 4-column view)

**Then** it calls `GET /api/space/{space_id}/snapshots` (Story 2.2 AC5) and renders the result as a timeline:
```
2026-04-26 14:32 · First registration · HTTP 200  ✓
```

**And** if no snapshots exist, shows: `"No fetch history yet."`

### AC5 — RFF mockup spaces visible in admin, togglable

**Given** the admin is logged in

**When** viewing the space list

**Then** RFF mockup spaces (`mom:source "mock-rff"`) are included by default

**And** a toggle "Show mock data" (on by default) excludes them when toggled off — so the admin can see only real pilot spaces

**And** the toggle state is remembered in `sessionStorage`

### AC6 — No regression on public map

**Given** the admin service is running

**When** a user opens the public map

**Then** there is no change in behaviour — admin routes are isolated to the `admin.*` subdomain

---

## Tasks / Subtasks

- [ ] **Task 1** — Infrastructure: admin service skeleton (AC1)
  - [ ] Create `infra/admin/` directory with `main.py` (FastAPI), `Dockerfile`, `requirements.txt`
  - [ ] Endpoints: `GET /` (space list page), `GET /space/{space_id}` (detail page)
  - [ ] Add `mak-admin` service to `docker-compose.yml` on internal port 8001
  - [ ] Generate `.htpasswd` from `MAK_ADMIN_PASSWORD` in Dockerfile entrypoint or init script
  - [ ] Add nginx server block for `admin.mapsofmaking.org` with `auth_basic` + proxy to `mak-admin:8001`

- [ ] **Task 2** — Space list API + page (AC2)
  - [ ] SPARQL SELECT: all spaces with name, slug, operationalState, source, lastFetched
  - [ ] Render as HTML table with status badges, sortable columns, aggregate count header
  - [ ] Row click → `/space/{space_id}` route

- [ ] **Task 3** — Per-space detail: Columns A + C + D (AC3, seeded and confirmed)
  - [ ] Column A: SPARQL SELECT seed triples from named graph
  - [ ] Column C: SPARQL SELECT all triples across all named graphs for space_uri
  - [ ] Column D: Read GeoJSON feature for space_id from `web/data/spaces.geojson`; render as JSON dump
  - [ ] Gap detection: compare Column B/C fields against Column D — amber badge on missing fields

- [ ] **Task 4** — Per-space detail: Column B — live URL fetch (AC3)
  - [ ] If `mom:endpointUrl` absent: show "No endpoint registered" placeholder
  - [ ] Else: `httpx.get(endpoint_url, timeout=10)` → display JSON-LD + HTTP status + latency
  - [ ] On error: display error message inline (no 500 to admin page)

- [ ] **Task 5** — Ingestion history section (AC4)
  - [ ] Call `GET /api/space/{space_id}/snapshots` (internal call via httpx, not browser fetch)
  - [ ] Render as timeline list below 4-column view

- [ ] **Task 6** — Mock data toggle (AC5)
  - [ ] Add toggle UI to space list header
  - [ ] Filter `mom:source "mock-rff"` spaces from list when toggled off
  - [ ] Persist in sessionStorage via JS

- [ ] **Task 7** — Integration verification (AC6)
  - [ ] Confirm public map at `mapsofmaking.org` unchanged
  - [ ] Confirm `admin.mapsofmaking.org` returns 401 without credentials
  - [ ] Confirm 4-column view renders for a registered space

---

## Dev Notes

### nginx: two server blocks

```nginx
# Public map — existing block
server {
    server_name mapsofmaking.org www.mapsofmaking.org;
    # ... existing config ...
}

# Admin dashboard
server {
    server_name admin.mapsofmaking.org;

    auth_basic "mak-admin";
    auth_basic_user_file /etc/nginx/auth/.htpasswd;

    location / {
        proxy_pass http://mak-admin:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

The `.htpasswd` file is generated at container startup using `htpasswd` from `apache2-utils` (or `openssl passwd -apr1`). The password comes from `MAK_ADMIN_PASSWORD` env var. Never committed.

### .env variable

`MAK_ADMIN_PASSWORD` already exists in `.env` with value `test-password`. This is the source of truth. The entrypoint script generates `.htpasswd` from it at startup:

```sh
echo "admin:$(openssl passwd -apr1 $MAK_ADMIN_PASSWORD)" > /etc/nginx/.htpasswd
```

### Gap detection logic (AC3)

The "viewed" fields are the GeoJSON feature properties. For each field in the data-lifecycle table that should flow to the card:

```python
LIFECYCLE_FIELDS = [
    ("name", "schema:name"),
    ("opening_hours", "schema:openingHours"),
    ("endpoint_url", "mom:endpointUrl"),
    ("last_fetched", "mom:lastFetched"),
    # etc.
]
for geojson_key, predicate in LIFECYCLE_FIELDS:
    if geojson_feature["properties"].get(geojson_key, "") == "":
        # check if predicate exists in Column C
        if predicate in stored_triples:
            flag_gap(geojson_key, predicate)  # amber badge
```

### Tech stack for admin pages

Use server-side HTML rendering (Jinja2 templates via FastAPI). No JS framework — this is an ops tool, not a polished UI. The same `el()` pattern from app.js is deliberately NOT used here. Tables and `<dl>` elements are fine.

### References

- Data lifecycle map: `_bmad-output/planning-artifacts/data-lifecycle.md`
- Snapshots API: Story 2.2 AC5
- nginx existing config: `infra/nginx/conf.d/app.conf`
- docker-compose: `docker-compose.yml`
- MAK_ADMIN_PASSWORD: `.env` line 5
- Epic 4 overview: `_bmad-output/planning-artifacts/epics.md:345-352`

---

## Dev Agent Record

### Agent Model Used

claude-sonnet-4-6 (story draft, 2026-04-26)

### Debug Log References

### Completion Notes List

### File List
