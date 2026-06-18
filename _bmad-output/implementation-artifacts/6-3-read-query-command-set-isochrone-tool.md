# Story 6.3: Read/Query Command Set + Isochrone Tool

**Status:** done
**Epic:** 6 — Ask Bernard
**Story ID:** 6-3
**Depends on:** 6.0 (bot running, adapter + intent router live), Epic 3 (data in Oxigraph)

---

## User Story

As a maker,
I want templated discovery commands and a travel-time radius search,
So that I can find spaces fast without natural-language ambiguity (and without an LLM in the query path).

---

## Acceptance Criteria

**Given** confirmed spaces exist in Oxigraph
**When** Story 6.3 lands
**Then** the bot supports these literal commands (all checked in `commands.try_handle` before LLM classifier):
- `!mom status` — lifecycle state + last heartbeat for this room's linked space (available to all users; coordinators also see deploy-key setup status appended)
- `!mom hours` — opening hours from Oxigraph for this room's linked space
- `!mom find {tag} {city}` — confirmed spaces where `schema:knowsAbout` contains tag AND city matches
- `!mom nearby {city} {radius}` — spaces within bounding box (city geocode → bbox → SPARQL FILTER on lat/lon)
- `!mom network {network_name}` — spaces where `mom:memberOf` contains the network name (confirmed both directions where available)
- `!mom travel {origin} {hours}` — spaces reachable within N hours (ORS isochrone + shapely point-in-polygon)

**And** `harness/query_commands.py` contains the SPARQL dispatch for all read commands
**And** `harness/isochrone.py` implements the three-step ORS travel-time tool
**And** `harness/sparql_client.py` gains a `run_select()` function returning `list[dict]` of bindings
**And** `harness/router.py` wires the `query` intent to `query_commands.dispatch(message)` (replacing the current `unknown_ack()` stub)
**And** `ORS_API_KEY` is read from `.env` (free tier, 2000 req/day); new dep `shapely` added to `infra/bot/requirements.txt`
**And** results include seeded-but-unregistered spaces in range as a follow-up offer (Bernard's seeded fallback)
**And** an ORS timeout (>5s) degrades gracefully to the `!mom nearby` bounding-box fallback

**And** `!mom help` lists all commands, grouped by read vs write, filtered by the user's power_level (write commands only shown to power_level ≥ 100)
**And** bare `!mom` with no verb returns the same as `!mom help`
**And** a misspelled verb (e.g. `!mom stauts`) triggers a fuzzy-suggest reply before the LLM classifier is invoked
**And** `@bernard` mention is accepted as an entry point but returns a stub explaining NL queries are coming (deferred to 6.4); it does NOT alias `!mom` commands
**And** `!mom status` for power_level < 100 returns lifecycle data only — no deploy-key or endpoint internals exposed

**Done gate (operator confirmation):** `!mom travel Brussels 2h` returns confirmed spaces inside the isochrone with travel times; ORS timeout triggers graceful bounding-box fallback; `!mom find fab Brussels` returns matching confirmed spaces; `!mom help` shows read-commands to a power_level-0 user and both read+write to a coordinator.

---

## Technical Implementation Guide

### 1. File Map

| Action | Path | Notes |
|--------|------|-------|
| CREATE | `harness/query_commands.py` | SPARQL query dispatch for all read commands |
| CREATE | `harness/isochrone.py` | ORS isochrone + shapely point-in-polygon |
| UPDATE | `harness/sparql_client.py` | Add `run_select()` returning `list[dict]` |
| UPDATE | `harness/commands.py` | Add `hours`, `find`, `nearby`, `network`, `travel`, `help` verbs; restructure `status` to read-first; add fuzzy-suggest |
| UPDATE | `harness/router.py` | Wire `query` intent → `query_commands.dispatch` |
| UPDATE | `harness/main_matrix.py` | Add `@bernard` mention normalization stub (→ NL-stub reply) |
| UPDATE | `harness/bernard.py` | Add query response ack functions, `help()`, `did_you_mean_ack()`, `bernard_nl_stub_ack()` |
| UPDATE | `harness/bernard_voice.yaml` | Add query response strings + help/fuzzy/stub strings |
| UPDATE | `infra/bot/requirements.txt` | Add `shapely` |
| UPDATE | `harness/tests/test_commands.py` | Add tests for new verbs, help, fuzzy-suggest |
| CREATE | `harness/tests/test_query_commands.py` | Tests for SPARQL query commands |

**Critical:** All bot code lives in `harness/` — NOT `infra/bot/`. The `infra/bot/` directory contains link_handler sub-package (`bot_keys.py`, `git_ops.py`, `schema.py`), not the main bot modules. Do not get confused by the directory name.

### 2. Command Registry — The Spine

Build a single `COMMAND_REGISTRY` dict in `harness/commands.py` before the `try_handle` function. This one dict drives dispatch, `!mom help`, and fuzzy-suggest — so they can never drift from each other:

```python
# Each entry: verb → (min_power_level, one_line_description, arg_shape)
COMMAND_REGISTRY = {
    "status":  (0,   "Lifecycle state of this room's linked space", ""),
    "hours":   (0,   "Opening hours of this room's linked space", ""),
    "find":    (0,   "Search confirmed spaces by tag and city", "{tag} {city}"),
    "nearby":  (0,   "Spaces within a radius of a city", "{city} {radius_km}"),
    "network": (0,   "Confirmed spaces in a named network", "{network_name}"),
    "travel":  (0,   "Spaces reachable within N hours (ORS isochrone)", "{origin} {hours}[h] [by bike|by foot]"),
    "help":    (0,   "List available commands", "[verb]"),
    "link":    (100, "Link this room to a space endpoint", "{space_slug}"),
    "update":  (100, "Update a field in this space's JSON", "{field} {value}"),
    "open":    (100, "Mark this space as open", ""),
    "close":   (100, "Mark this space as closed", ""),
}
KNOWN_VERBS = frozenset(COMMAND_REGISTRY)
```

**`!mom help` implementation in `try_handle`:**
```python
if verb == "help" or not verb:  # bare `!mom` with no verb → help
    arg = parts[1] if len(parts) > 1 else ""
    return bernard.help(power_level, arg, COMMAND_REGISTRY)
```

`bernard.help(power_level, arg, registry)` renders differently by power_level:
- power_level < 100: show only verbs where `min_power == 0`, grouped as "Look things up" vs "Changes things (not available to you)"
- power_level ≥ 100: show all verbs in both groups
- `arg` is a specific verb → show one-line + arg_shape for just that verb
- All examples copy-pasteable, in Bernard's dry voice

**Fuzzy-suggest implementation** (immediately before the final `return None` in `try_handle`):
```python
import difflib

matches = difflib.get_close_matches(verb, KNOWN_VERBS, n=1, cutoff=0.7)
if matches:
    return bernard.did_you_mean_ack(verb, matches[0])
return None  # falls through to LLM classifier for genuine NL
```

`did_you_mean_ack` is advisory only — never auto-executes. "There's no `stauts`. Did you mean `!mom status`?"

**Result cap:** Add `LIMIT 10` to `find`/`network`, `LIMIT 20` to `nearby`. Travel caps at 15 confirmed results in `_filter_spaces`. If results hit the limit, Bernard appends "Showing first {n} — narrow it down with `!mom find {tag} {city}`."

### 2b. `@bernard` Mention Stub (`harness/main_matrix.py`)

Deferred to 6.4 (NL-SPARQL epic). In 6.3, add a mention-detection stub that intercepts `@bernard` before the command prefix check and returns the NL-coming-soon response — so the door is labelled, not a wall:

```python
# In the message handler, before the !mom prefix check:
if message.text and _is_bernard_mention(message.text, bot_user_id):
    await adapter.send(bernard.bernard_nl_stub_ack(), context)
    return

def _is_bernard_mention(text: str, bot_user_id: str) -> bool:
    """Match @bernard or display-name mention at start of message."""
    import re
    return bool(re.match(r"^@?bernard[\s,:]+", text, re.IGNORECASE))
```

`bernard_nl_stub_ack`: "Natural-language questions are on the roadmap. For now: `!mom help` lists what I can do."

### 3. SPARQL Client Extension (`harness/sparql_client.py`)

Currently `sparql_client.py` only has `run_ask()`. Add `run_select()`:

```python
async def run_select(query: str) -> tuple[list[dict], int]:
    """Run a SPARQL SELECT query. Returns (list_of_binding_dicts, latency_ms).
    Each binding dict maps variable name → {"type": ..., "value": ...}.
    Returns empty list on error (caller decides fallback)."""
    t0 = time.monotonic()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{OXIGRAPH_ENDPOINT}/query",
            content=query,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
            timeout=httpx.Timeout(connect=5.0, read=15.0),
        )
        resp.raise_for_status()
    latency = int((time.monotonic() - t0) * 1000)
    bindings = resp.json().get("results", {}).get("bindings", [])
    log.info("sparql.select_completed", count=len(bindings), latency_ms=latency)
    return bindings, latency
```

Use the same `OXIGRAPH_ENDPOINT` module-level variable (already set from env in main.py).

### 3. SPARQL Query Templates (`harness/query_commands.py`)

Use the **canonical namespace** throughout: `PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>`

**`!mom status` — lifecycle query for a linked space:**
```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
SELECT ?name ?openNow ?lastOpenChange ?updatedAt ?subset ?nextUnlock ?endpointUrl WHERE {
  GRAPH <urn:mak:space/{space_id}> {
    ?s a mom:Space ;
       schema:name ?name .
    OPTIONAL { ?s mom:openNow ?openNow }
    OPTIONAL { ?s mom:lastOpenChange ?lastOpenChange }
    OPTIONAL { ?s mom:updatedAt ?updatedAt }
    OPTIONAL { ?s mom:subset ?subset }
    OPTIONAL { ?s mom:nextUnlock ?nextUnlock }
    OPTIONAL { ?s mom:endpointUrl ?endpointUrl }
  }
}
```

The graph URI is `urn:mak:space/{space_id}` where `space_id` comes from `git_ops.resolve_space_for_room(room_id)` (already used in write commands). If room is not linked, return `bernard.status_no_link_ack()`.

**`!mom hours` — opening hours:**
```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
SELECT ?name ?openingHours WHERE {
  GRAPH <urn:mak:space/{space_id}> {
    ?s a mom:Space ; schema:name ?name .
    OPTIONAL { ?s schema:openingHours ?openingHours }
  }
}
```

**`!mom find {tag} {city}` — confirmed spaces matching tag + city:**
```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
SELECT ?name ?city ?website WHERE {
  GRAPH ?g {
    ?s a mom:Space ;
       schema:name ?name ;
       schema:knowsAbout ?specialty .
    OPTIONAL { ?s schema:addressLocality ?city }
    OPTIONAL { ?s schema:url ?website }
    FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
    FILTER(CONTAINS(LCASE(STR(?specialty)), LCASE("{tag}")))
    FILTER(CONTAINS(LCASE(STR(?city)), LCASE("{city}")))
  }
} LIMIT 10
```

**`!mom nearby {city} {radius_km}` — bounding box query:**
Geocode city via link_handler `/api/geocode` proxy (see §4 below for Nominatim pattern). Build bbox (lat ± delta, lon ± delta) where `delta = radius_km / 111.0`:
```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
SELECT ?name ?lat ?lon ?website WHERE {
  GRAPH ?g {
    ?s a mom:Space ;
       schema:name ?name ;
       schema:geo [schema:latitude ?lat ; schema:longitude ?lon] .
    OPTIONAL { ?s schema:url ?website }
    FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
    FILTER(?lat >= {min_lat} && ?lat <= {max_lat})
    FILTER(?lon >= {min_lon} && ?lon <= {max_lon})
  }
} ORDER BY ?name LIMIT 20
```

**`!mom network {network_name}` — member spaces:**
```sparql
PREFIX mom: <https://nicolasdb.github.io/mapsofmaking_ontology/ns#>
PREFIX schema: <https://schema.org/>
SELECT ?name ?city ?website WHERE {
  GRAPH ?g {
    ?s a mom:Space ;
       schema:name ?name ;
       mom:memberOf ?net .
    OPTIONAL { ?s schema:addressLocality ?city }
    OPTIONAL { ?s schema:url ?website }
    FILTER(STRSTARTS(STR(?g), "urn:mak:space/"))
    FILTER(CONTAINS(LCASE(STR(?net)), LCASE("{network_name}")))
  }
} LIMIT 20
```

### 4. Nominatim Pattern — Use Link Handler Proxy

Do **not** call Nominatim directly from the bot. The link_handler already runs a rate-limited Nominatim proxy at `/api/geocode`. Use it:

```python
async def geocode_city(city: str) -> tuple[float, float] | None:
    """Returns (lat, lon) or None on failure."""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{LINK_HANDLER_URL}/api/geocode",
            json={"query": city},
        )
        if resp.status_code != 200:
            return None
        data = resp.json()
        return data["lat"], data["lon"]
```

The `/api/geocode` endpoint (Story 9.3/9.4) already exists on the live VPS.

### 5. Isochrone Tool (`harness/isochrone.py`)

Three-step flow:

```python
async def travel_search(origin: str, hours: float, mode: str = "driving-car") -> dict:
    """
    Returns {
        "confirmed": [{"name": ..., "travel_min": ...}, ...],
        "seeded_count": int,
        "fallback": False,  # True if ORS timed out
    }
    Raises: IsochroneError on hard failure (caller degrades to !mom nearby).
    """
    # Step 1: resolve origin coordinates
    coords = await _resolve_origin(origin)  # Oxigraph space name first, Nominatim city second

    # Step 2: call ORS
    polygon = await _fetch_isochrone(coords, hours, mode)

    # Step 3: shapely point-in-polygon against all spaces from Oxigraph
    return await _filter_spaces(polygon, hours)
```

**ORS API call — verified against live ORS v2 docs (Context7, 2026-06-18):**

The endpoint is `POST https://api.openrouteservice.org/v2/isochrones/{profile}` where `{profile}` is in the **URL path** (not the body). Auth is via `Authorization` header. Request body key is `"range"` (array of ints in **seconds**), not `"ranges"`.

```python
ORS_API_KEY = os.environ.get("ORS_API_KEY", "")
ORS_BASE_URL = "https://api.openrouteservice.org"

async def _fetch_isochrone(coords: tuple[float, float], hours: float, mode: str) -> dict:
    """Returns GeoJSON polygon from ORS. Raises IsochroneTimeoutError if >5s.
    coords = (lat, lon); ORS receives [lon, lat] — inverted, see comment below.
    """
    if not ORS_API_KEY:
        raise IsochroneError("ORS_API_KEY not configured")
    body = {
        "locations": [[coords[1], coords[0]]],  # ⚠️ ORS v2 is [lon, lat], our tuple is (lat, lon)
        "range": [int(hours * 3600)],            # seconds; field name is "range", NOT "ranges"
        "range_type": "time",
    }
    async with httpx.AsyncClient(
        headers={"Authorization": ORS_API_KEY},
        timeout=httpx.Timeout(5.0),
    ) as client:
        resp = await client.post(
            f"{ORS_BASE_URL}/v2/isochrones/{mode}",  # profile in URL path
            json=body,
        )
        resp.raise_for_status()
    features = resp.json().get("features", [])
    if not features:
        raise IsochroneError("ORS returned no polygon")
    return features[0]["geometry"]  # GeoJSON Polygon geometry dict → feed to shapely.shape()
```

**ORS free-tier limits:** ~40 isochrone req/min, ~2000 req/day. A missing key → `IsochroneError` → Bernard ack "travel search unavailable", not a crash. Add a per-room ORS call cooldown (5 min) to prevent quota exhaustion from curious users.

**Shapely filter:**
```python
from shapely.geometry import Point, shape

async def _filter_spaces(polygon_geom: dict, hours: float) -> dict:
    poly = shape(polygon_geom)
    # Fetch all spaces from Oxigraph (confirmed + seeded)
    all_spaces, _ = await sparql_client.run_select(ALL_SPACES_QUERY)
    confirmed, seeded_count = [], 0
    for b in all_spaces:
        lat = float(b["lat"]["value"])
        lon = float(b["lon"]["value"])
        if poly.contains(Point(lon, lat)):
            has_endpoint = bool(b.get("endpointUrl", {}).get("value"))
            if has_endpoint:
                confirmed.append({"name": b["name"]["value"], ...})
            else:
                seeded_count += 1
    return {"confirmed": confirmed, "seeded_count": seeded_count, "fallback": False}
```

**Mode mapping from user input:**
- `!mom travel Brussels 2h` → `driving-car`
- `!mom travel Brussels 2h by bike` → `cycling-regular`
- `!mom travel Brussels 2h by foot` → `foot-walking`

### 7. Restructure `!mom status` in `commands.py`

**Current problem:** `_handle_status` (line 271) requires `power_level >= 100` and only checks deploy-key setup.

**6.3 fix:** Make `!mom status` universal — always query Oxigraph for lifecycle data (available to all users), then append deploy-key setup info for coordinators only. The power_level gate is dropped from the read path but retained for the coordinator section.

**Security constraint:** power_level < 100 must never see deploy-key data, endpoint URLs, or any field that reveals infrastructure. The lifecycle fields (name, openNow, lastOpenChange, updatedAt, subset, nextUnlock) are public-safe. `endpointUrl` and `verify_setup()` output are coordinator-only.

```python
async def _handle_status(room_id: str, power_level: int, bound) -> str:
    # Read path — available to all
    try:
        space_id = await git_ops.resolve_space_for_room(room_id)
    except NoEndpointError:
        return bernard.status_no_link_ack()

    # Fetch lifecycle data (public-safe fields only)
    lifecycle_report = await query_commands.space_status(space_id)

    # Coordinators additionally see deploy-key setup status
    if power_level >= 100:
        verify = await git_ops.verify_setup(space_id)
        return lifecycle_report + "\n\n" + bernard.status_report(verify)

    return lifecycle_report  # no endpointUrl or key material for non-coordinators
```

Add a test asserting that a power_level=0 `!mom status` response contains none of: endpoint URL, deploy key, `verify_setup` fields.

### 8. Router Update (`harness/router.py`)

Wire `query` intent to `query_commands.dispatch`:

```python
import query_commands

async def route(message: Message, session_id: str) -> str:
    intent = await intent_classifier.classify(message.text, session_id=session_id)

    if intent == "unknown":
        return bernard.unknown_ack()

    if intent == "query":
        return await query_commands.dispatch(message, session_id=session_id)

    # write | nl_discovery: not implemented yet (6.1-6.4 handled in commands.py / 6.4)
    log.warning("router.intent_not_implemented", intent=intent, session_id=session_id)
    return bernard.unknown_ack()
```

Note: write commands are handled by `commands.try_handle` BEFORE the router is invoked (in main_matrix.py). The `query` intent route here handles free-text queries that weren't caught by literal command parsing (e.g., a user asking "what spaces are near Ghent?").

### 9. Bernard Voice Additions (`harness/bernard_voice.yaml` + `harness/bernard.py`)

Add to `bernard_voice.yaml` under `bot:`:
```yaml
  # Query responses
  status_no_link_ack: "This room isn't linked to a space yet. Register one with `!mom link {slug}` first."
  status_lifecycle: "**{name}** · {state_line}\nLast updated: {updated_at}\n{unlock_line}"
  hours_found: "**{name}** opens: {hours}"
  hours_missing: "**{name}** hasn't listed opening hours yet."
  find_results: "Found {count} confirmed space(s) matching '{tag}' in {city}:\n{list}"
  find_empty: "No confirmed spaces match '{tag}' in {city}. {seeded_note}"
  nearby_results: "Within {radius}km of {city} — {count} confirmed space(s):\n{list}"
  nearby_empty: "Nothing confirmed within {radius}km of {city}. {seeded_note}"
  network_results: "**{network}** — {count} confirmed member(s):\n{list}"
  network_empty: "No confirmed spaces list '{network}' as a network. Check the exact name."
  travel_results: "Within {hours}h of {origin} by {mode} — {count} confirmed space(s):\n{list}\n{seeded_note}"
  travel_timeout: "ORS took too long — falling back to a bounding box. {fallback_result}"
  travel_ors_unavailable: "Travel search is temporarily unavailable. {fallback_result}"
  seeded_note: "{count} seeded space(s) also fall in range — they haven't registered an endpoint yet. Want me to list them?"
  # Help and fuzzy-suggest
  help_header: "Here's what I do."
  did_you_mean: "There's no `{verb}`. Did you mean `!mom {suggestion}`?"
  unknown_command: "I don't know `{verb}`. Try `!mom help`."
  result_cap_note: "Showing first {n} — narrow it down with `!mom find {tag} {city}`."
  # @bernard mention stub (NL deferred to 6.4)
  bernard_nl_stub: "Natural-language questions are on the roadmap. For now: `!mom help` lists what I can do."
```

### 10. Seeded Fallback Pattern

The seeded fallback is **Bernard's trust principle**: never return zero results without offering what he knows. In every spatial query, if confirmed results < 3 and seeded_count > 0, append `bernard.seeded_note_ack(seeded_count)`. The seeded spaces list is only shown if the user explicitly asks (avoids noise for large seeded datasets).

Seeded spaces are identified in SPARQL by `FILTER NOT EXISTS { ?s mom:endpointUrl ?e }` or by checking `mom:source` starts with `scraped-`.

### 11. `.env` Addition Required

Operator must add `ORS_API_KEY=<key>` to `.env` before running. Get free key at https://openrouteservice.org/dev/#/signup (2000 req/day).

Document in `infra/bot/config.yaml` under env vars section.

### 12. `infra/bot/requirements.txt` Update

Add `shapely` (no version pin needed — only standard point-in-polygon used):
```
shapely
```

---

## Deferred Items (named, not forgotten)

1. **ORS self-hosting** — free tier (~2000 req/day, ~40/min) is sufficient for PoC operator use. ORS is self-hostable (Docker + OSM regional extract) but is a real ops cost. Deferred until travel-reach is proven to matter to users. ORS is behind a thin `isochrone(profile, coord, range) → polygon` interface so this swap is reversible. → post-PoC
2. **Isochrone per-space travel-time** — ORS isochrone gives polygon membership but not per-space travel duration. N individual ORS `/directions` calls would be expensive. 6.3 returns straight-line km as a proxy. → deferred
3. **`@bernard` NL mention surface** — 6.3 stubs the `@bernard` mention with a "NL is coming" message. Full NL-SPARQL routing goes in 6.4. The stub labels the door now so the surface is reserved in the UX vocabulary. → Story 6.4
4. **`!mom info <space-slug>` / `!mom search <city>`** — John (PM) flagged this as the missing "result page" after a find/nearby. Decision: templated commands are for LLM-free deterministic queries; these discovery queries flow more naturally as NL with `@bernard`. The `!mom find` and `!mom nearby` results listing includes slugs/names for follow-up. `!mom info` deferred to 6.4 / NL epic — not worth a separate templated verb when NL covers it better. → Story 6.4 / NL epic
5. **Multi-result pagination** — 6.3 caps results (10 for find/network, 20 for nearby, 15 for travel) with a "narrow it down" hint. Proper pagination (next-page offset) deferred. → future story
6. **`query` intent LLM disambiguation** — free-text queries landing in `query` intent that don't match template commands get `unknown_ack()` + hint. Full NL→SPARQL in 6.4.
7. **Geocode result caching** — Nominatim calls not cached. Sufficient for PoC volume. → later story
8. **Per-room ORS rate throttle** — 6.3 adds a simple 5-min per-room ORS cooldown. A real token-bucket or Redis-backed throttle deferred. → later story

---

## Integration Test Requirements

Per `feedback_integration_testing`: no mocking protocol surface. Tests must hit real services where feasible.

**Test patterns for `harness/tests/test_query_commands.py`:**
- `test_status_no_linked_room` — mock `git_ops.resolve_space_for_room` raising `NoEndpointError`; assert `status_no_link_ack` returned
- `test_nearby_parse_radius` — unit test argument parsing from `"!mom nearby Brussels 50"` → city="Brussels", radius=50
- `test_isochrone_ors_timeout_degrades_to_nearby` — mock ORS call to raise `httpx.ReadTimeout`; assert fallback is triggered and response contains bounding-box results
- `test_find_returns_matching_spaces` — mock `sparql_client.run_select` returning two fake bindings; assert count=2 in response
- `test_seeded_fallback_offered_on_empty_confirmed` — mock returns 0 confirmed + 3 seeded; assert seeded note in response

**Live integration test** (marked `@pytest.mark.live`):
- `test_live_status_mother_sands` — requires Oxigraph running with mother-sands data; `!mom status` from mother-sands room returns non-empty lifecycle line

---

## Key Constraints and Gotchas

1. **Unencrypted rooms required** — Bernard does not handle `MegolmEvent` (E2E encrypted rooms). All `!mom` commands must be sent in unencrypted rooms. This is a known limitation from Story 6-deploy. Do not add E2E key handling in this story (deferred, no traction).

2. **SPARQL escaping** — interpolating user input into SPARQL templates is an injection risk. From Story 6.1 code review finding: always sanitize user-supplied strings before interpolation. Strip `{}()<>"` characters from tag/city/network_name before building query string. Do not use f-strings with raw user input.

3. **`commands.try_handle` is checked first** — the literal command parser in `commands.try_handle` fires before the LLM classifier. Verbs `status`, `hours`, `find`, `nearby`, `network`, `travel` are added here. The router's `query` intent is only reached for free-text queries.

4. **`run_select()` timeout** — spatial queries (all confirmed spaces for shapely filter) may return large result sets. Use 15s read timeout (larger than the current `run_ask()` 10s). Log a warning if count > 500 (could indicate schema issue).

5. **ORS coordinate order** — ORS `/v2/isochrones` expects `[lon, lat]` (longitude first), opposite of the standard `(lat, lon)` convention used everywhere else in the codebase. This is a common footgun. Comment clearly in `isochrone.py`.

6. **`shapely` import guard** — `shapely` is a new dependency. If it's missing (e.g., in CI without full requirements), the isochrone command should fail gracefully with `bernard.travel_ors_unavailable_ack()` rather than an `ImportError` crash.

7. **Every handler must catch-and-ack, not raise** — `main_matrix.py` fire-and-forget tasks absorb exceptions silently (the loop survives, but the user sees no reply). Every new handler MUST catch all exceptions and return a Bernard string. Never let an exception propagate from a handler.

8. **`text.split(maxsplit=2)` arg cap** — `commands.py:151` caps at 2 args. Multi-word queries (`!mom find laser cutter Brussels`) work because `parts[2]` holds the remainder as one string. But `!mom travel <origin> <hours>` is two distinct args — split internally in the travel handler, don't rely on `parts[2]` as both.

9. **`!mom` prefix check is in `main_matrix.py`** — the `!mom` prefix gate and the new `@bernard` mention stub both live in `main_matrix.py`, not `commands.py` or `router.py`. The `@bernard` stub check must come BEFORE the `!mom` prefix check in that file.

10. **SPARQL injection surface covers find/nearby free-text** — sanitize all user-supplied strings (tag, city, network_name, origin) before interpolation. Escape `"`, `\`, newlines, control chars. Add an injection test: `!mom find "} DROP GRAPH ...` should return an error response, not execute.

---

## Data Available in Oxigraph for Query Commands

Fields available in `urn:mak:space/` graphs (from Epic 3.5 + existing schema):
- `schema:name` — space name
- `schema:addressLocality` — city
- `schema:addressCountry` — country
- `schema:geo / schema:latitude + schema:longitude` — coordinates
- `schema:knowsAbout` — specialty tags (multi-valued, GROUP_CONCAT with `|` separator in materialize query)
- `schema:openingHours` — opening hours string (may be null for non-card spaces)
- `schema:url` — website
- `mom:endpointUrl` — registered endpoint (presence = confirmed space)
- `mom:memberOf` — network memberships (multi-valued)
- `mom:openNow` — current open state (boolean or null)
- `mom:lastOpenChange` — ISO datetime of last state.open change
- `mom:updatedAt` — ISO datetime of last listing update (stewardship track)
- `mom:subset` — lifecycle level (`mom:required`, `mom:card`, `spaceapi:compatible`)
- `mom:nextUnlock` — human-readable string describing what would unlock next tier

Canary graph (`urn:mak:canary`) has a subset of these fields. Include it in spatial queries by using `FILTER(STRSTARTS(STR(?g), "urn:mak:"))` instead of `urn:mak:space/` only.

---

## References

- `_bmad-output/planning-artifacts/mom_handoff_2026-06-16.md` §"Story 6.3"
- `_bmad-output/planning-artifacts/epics.md` §"Story 6.3: Read/Query Command Set + Isochrone Tool"
- Story 6.2 completion notes — deferred items list
- memory: `feedback_integration_testing` — no mocking protocol surface; live tests required
- memory: `project_three_token_freshness_model` — `observedAt`/`updatedAt`/`lastOpenChange` meaning
- memory: `project_stewardship_vs_liveness_tracks` — `updatedAt` = listing maintained (blue), not alive (green)
- ORS API docs: https://openrouteservice.org/dev/#/api-docs/v2/isochrones/{profile}/post

---

## Change Log

- 2026-06-18: Story 6.3 created — comprehensive dev guide for read/query command set + isochrone tool.
- 2026-06-18: Party-mode review amendments — added `!mom help` (power-level-aware listing), command registry spine (COMMAND_REGISTRY dict as single source for dispatch/help/fuzzy), fuzzy-suggest via `difflib.get_close_matches`, `@bernard` mention stub (→ NL-coming-soon, full NL deferred to 6.4), ORS contract verified against Context7 live docs (body key is `"range"` not `"ranges"`, profile in URL path, auth via `Authorization` header), per-room ORS rate cooldown, `!mom status` security constraint (redact coordinator fields at power_level < 100), result caps with "narrow it down" hint, `!mom info`/`!mom search` deferred to 6.4/NL epic.
- 2026-06-18: Story 6.3 implemented — all ACs satisfied; 56 tests passing (47 new + 34 existing + 9 prior); no regressions. Files: harness/sparql_client.py (run_select), harness/query_commands.py (new), harness/isochrone.py (new), harness/commands.py (COMMAND_REGISTRY + new verbs + restructured status + fuzzy-suggest), harness/router.py (query intent wired), harness/main_matrix.py (@bernard stub), harness/bernard.py + bernard_voice.yaml (query ack functions), harness/requirements.txt (shapely).
- 2026-06-18: Post-deploy operator testing exposed and fixed 6 bugs (see Debug Log below):
  1. `httpx.Timeout(connect=X, read=Y)` invalid — fixed to `httpx.Timeout(Y, connect=X)` in sparql_client.py
  2. Arg parsing: `find`/`nearby`/`travel` re-split `parts[2]` that split(maxsplit=2) had already separated — fixed to use `parts[1]`/`parts[2]` directly
  3. Bot replayed buffered messages on restart — fixed with `sync(timeout=0)` boot-time token + `server_timestamp` guard
  4. `geocode_city` sent `{"query": city}` but endpoint expects `{"address": "", "city": city}` — fixed in query_commands.py
  5. `ORS_API_KEY` not wired into mak-agent-bot environment block in docker-compose.yml — added
  6. `result_cap_note_ack` template had `{tag}` placeholder but `nearby` callers don't pass it — fixed to generic text
- 2026-06-18: Additional post-deploy bug fixes (round 2):
  7. `bernard_voice.yaml` had `{hours}h` in `travel_results` template — YAML overrides the Python fallback in `_bot()`, so fixing `bernard.py` alone had no effect; fixed in YAML (SSOT for all copy)
  8. Cooldown error message hardcoded "5 minutes" even after constant was changed to 60s — fixed to use `{ORS_COOLDOWN_SECONDS}` dynamically
  9. `!mom travel ... by car` → Usage error — "by car" not in mode suffix list; added alongside "by bike"/"by foot"
  10. Isochrone origin resolution: `_resolve_origin` now queries Oxigraph space names first (fuzzy CONTAINS match), falls back to Nominatim — enables `!mom travel superlab 20min` without knowing exact city name
- 2026-06-18: Post-testing UX/performance decisions:
  - ORS timeout bumped 5s → 15s (2h driving isochrone was consistently timing out)
  - Isochrone hour-bucket snapping added: arbitrary input snaps UP to nearest `[0.15, 0.30, 0.60, 1.0, 2.0]` bucket
  - In-memory polygon cache added (24h TTL, key = `(lat2dp, lon2dp, bucket, mode)`) — cache hits bypass ORS and skip cooldown
  - Above-2h requests pass through uncached, logged as `isochrone.above_bucket_range` signal for future regional discovery feature
  - Cooldown now only applies to live ORS calls, not cache hits
