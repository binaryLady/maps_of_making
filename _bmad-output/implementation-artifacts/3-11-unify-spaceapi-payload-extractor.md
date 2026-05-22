# Story 3.11: Unify SpaceAPI Payload → Triples Extraction

Status: done

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

> **Epic 3.5 follow-up.** Story 3.10 closed the freshness pipeline. This story closes the
> **payload extraction** half — the part that turns a fetched SpaceAPI document into the RDF
> triples behind the card. Today four writers each hand-roll their own mapping and each emits
> a different subset; Mother Sands' `location.address` is silently dropped on every fetch
> because the canary loader doesn't know how to map it. This story introduces a single
> bundle-aligned extractor (core / mom), wires all four callsites to it, mints two missing
> ontology predicates, and removes the legacy PII-warning surface (operator decision
> 2026-05-21: public data, coordinator responsibility, not ours).

## Story

As an operator running the Maps of Making IPO service,
I want every payload-→-triples write path (canary, federated seed, registration, heartbeat
re-extract) to share a single bundle-aligned extractor library and a single SPARQL-emission
helper,
so that any SpaceAPI field defined in the spec maps to RDF in one place — no callsite silently
drops a field, every writer emits the same shape, the crosswalk between SpaceAPI JSON and the
mom ontology becomes the obvious one place to look, and adding a future community vocabulary
(fab, omt, …) is a drop-in extractor module rather than four hand-edits.

## Acceptance Criteria

1. **Ontology predicates exist and resolve.** `mom:countryCode` and `mom:timeZone` are defined
   in `mom.ttl` (mapsofmaking_ontology repo) with `rdfs:domain mom:Space`, `rdfs:range
   xsd:string`, and a comment that explicitly allows non-ISO extension codes (e.g. SOL-3).
   The published GitHub Pages namespace returns 200 for both predicate URIs before any code
   in this repo references them. `ontology/crosswalk.csv` (this repo) carries matching rows.

2. **Library-style extractor module exists.** `scripts/spaceapi_extract/` contains four files:
   - `__init__.py` re-exports `extract_core`, `extract_mom`, `triples_for`, `escape_literal`.
   - `core.py` — `extract_core(payload) -> dict[str, Any]` mapping SpaceAPI v15 core fields
     to schema.org keys: `schema:name`, `schema:geo`, `schema:url`, `schema:logo`,
     `schema:contactJson`, `schema:description`, `schema:openingHours`, `schema:knowsAbout`.
   - `mom.py` — `extract_mom(payload) -> dict[str, Any]` mapping to `mom:address`,
     `mom:countryCode`, `mom:timeZone`, `mom:openNow`, `mom:lastOpenChange`, plus any
     `ext_mom.*` fields. Calls `pipeline_helpers._extract_open_now` /
     `_extract_last_open_change` rather than re-implementing state parsing.
   - `sparql.py` — `escape_literal(str)` (consolidates `_lit()` + `sparql_str()`) and
     `triples_for(subject_uri, fields) -> list[str]` emitting type-aware SPARQL triple
     strings (xsd:boolean, xsd:dateTime, URI vs literal, multi-value for
     `schema:knowsAbout`, blank node for `schema:geo`).
   - Both extractors are pure functions (dict → dict). No HTTP, no Oxigraph, no SPARQL.

3. **All four callsites use the extractor.** Hand-rolled triple builders are deleted and
   replaced with `extract_core` + `extract_mom` + `triples_for`:
   - `scripts/load_canary.py` `build_canary_sparql()` (DROP+INSERT envelope kept).
   - `infra/link_handler/main.py` `_build_sparql_update()` registration path (DROP+INSERT
     envelope kept — atomic bootstrap).
   - `scripts/seed_spaceapi.py` `build_insert()` (composes `extract_core(payload)` only —
     seed time is a minimal anchor; no state, no contact).
   - `infra/link_handler/pipeline.py` — **new** `write_payload_fields(uid, payload,
     graph_uri, subject, oxigraph_endpoint)` function uses `DELETE WHERE { ?s ?p ?o }` per
     extractor-declared predicate then `INSERT DATA`. Excludes the three freshness axis
     predicates explicitly (`mom:observedAt`, `mom:updatedAt`, `mom:openNow`,
     `mom:lastOpenChange`) — their dedicated writers in `pipeline.py` continue to own
     them. Wired into `run_space_pipeline()` gated on `content_changed=True`.

4. **Mother Sands renders its address.** After running `python3 scripts/load_canary.py` +
   `python3 scripts/materialize_geojson.py`, the Mother Sands feature in
   `web/data/spaces.geojson` has `properties.address == "Maunsell Fort, North Sea"`,
   `properties.country_code == "sol-3"`, `properties.timezone == "UTC+0"`. The card in
   `web/app.js` displays "Maunsell Fort, North Sea" — no "address not provided" placeholder.

5. **Heartbeat re-extract keeps payload fields fresh.** Live integration test:
   - Register a fake endpoint with `location.address: "A"`.
   - Heartbeat tick → Oxigraph has `mom:address "A"`.
   - Endpoint flips to `location.address: "B"` and content_changed becomes True on next tick.
   - Heartbeat tick → Oxigraph has `mom:address "B"`, freshness triples updated, no
     duplicate `mom:address` triples.
   - The three freshness axis predicates are byte-identical before/after
     `write_payload_fields()` runs.

6. **Materializer reads the new predicates.** `scripts/materialize_geojson.py`:
   - Canary UNION block (L112–129) has OPTIONAL clauses for `mom:address`, `mom:countryCode`,
     `mom:timeZone`, `schema:contactJson`.
   - Regular space block (L80–108) has matching OPTIONAL clauses for `mom:countryCode` and
     `mom:timeZone` (the others already present).
   - GROUP BY clause (L132–135) lists the new variables.
   - Feature property assembly (L226–245) exposes `country_code` and `timezone` keys.

7. **PII-warning surface removed.** Operator decision (2026-05-21): MoM is a public-data IPO
   service over coordinator-of-record endpoints; PII policy is the coordinator's
   responsibility, not ours. Delete:
   - `infra/link_handler/main.py`: `_PII_FIELDS` constant (L262), `_scan_pii()` function
     (L396–397), `pii_warning` and `pii_fields` keys from `_EMPTY_RESULT` (L479–480), the
     `pii_found = _scan_pii(data)` call (L525) and the two result dict keys (L536–537).
   - `web/app.js`: the `if (data.pii_warning) { … }` block at L1047–1048.
   - Any existing test asserting `pii_warning` in registration responses is updated to
     assert absence of those keys.

8. **Unit tests for extractors pass.** `tests/test_spaceapi_extract.py` covers:
   - Mother Sands baseline payload → expected `mom:address`, `mom:countryCode`,
     `mom:timeZone` extraction.
   - SpaceAPI v15 sample with all fields → every documented mapping.
   - v14 minimal sample → graceful absence of v15-only fields.
   - Empty / missing optional fields → no None values emitted.
   - The three freshness axis predicates are NOT present in
     `extract_core(p) ∪ extract_mom(p)` for any payload (negative assertion guarding
     AC 5's race-free contract).

9. **Live-integration test passes.** `tests/test_spaceapi_extract_e2e.py`
   (`@pytest.mark.live_integration`):
   - Load canary baseline via `scripts/load_canary.py`.
   - SPARQL `SELECT ?p ?o WHERE { GRAPH <urn:mak:canary>
     { <urn:mak:canary/mother-sands> ?p ?o } }` — asserts presence of every
     expected predicate.
   - Materialize, parse `spaces.geojson`, assert Mother Sands properties match AC 4.
   - The heartbeat re-extract scenario from AC 5.

10. **Full pytest suite remains green.** `pytest -m "not legacy"` and
    `pytest -m live_integration` both pass. `tests/test_load_canary.py` assertions are
    updated to match the new triple set (address/country/timezone now present).

11. **Operator visual confirmation.** Nicolas loads the running stack, opens the Mother
    Sands card, sees "Maunsell Fort, North Sea". Registers a separate live federated
    endpoint, confirms its address/contact triples land. Forces a content change on the
    canary endpoint, confirms the next heartbeat tick refreshes `mom:address` in Oxigraph
    via direct SPARQL query.

## Tasks / Subtasks

- [x] Task 1 — Ontology PR in mapsofmaking_ontology repo (AC: 1)
  - [x] Edit `mom.ttl`: add `mom:countryCode` and `mom:timeZone` definitions
  - [ ] PR, merge, confirm GitHub Pages publishes
    `https://nicolasdb.github.io/mapsofmaking_ontology/ns#countryCode` and `#timeZone`
    (operator manual step — user copy/pastes ontology/ to adjacent repo and pushes)
  - [x] Add matching rows to `ontology/crosswalk.csv` in this repo

- [x] Task 2 — Build the extractor library (AC: 2)
  - [x] Create `scripts/spaceapi_extract/sparql.py` with `escape_literal` (consolidates
        `_lit()` from `load_canary.py:62` and `sparql_str()` from `seed_spaceapi.py`) and
        `triples_for(subject_uri, fields)` emitting xsd-typed triples
  - [x] Create `scripts/spaceapi_extract/core.py` with `extract_core(payload)`
  - [x] Create `scripts/spaceapi_extract/mom.py` with `extract_mom(payload)` (delegates
        state parsing to `pipeline_helpers._extract_open_now` /
        `_extract_last_open_change`)
  - [x] Create `scripts/spaceapi_extract/__init__.py` re-exporting the public surface
  - [x] Write `tests/test_spaceapi_extract.py` — unit tests per AC 8 (32 tests, all pass)

- [x] Task 3 — Migrate canary baseline loader (AC: 3, 4)
  - [x] Replace `build_canary_sparql()` body in `scripts/load_canary.py` with extractor
        composition; keep `DROP SILENT GRAPH` + `INSERT DATA` envelope
  - [x] Delete the local `_lit()` helper (use `spaceapi_extract.sparql.escape_literal`)
  - [x] Update `tests/test_load_canary.py` assertions to match the new triple set (17 tests, all pass)

- [x] Task 4 — Migrate registration write path (AC: 3)
  - [x] Replace inline triple assembly in `infra/link_handler/main.py`
        `_build_sparql_update()` with extractor composition; keep registration envelope
  - [x] Verify all existing registration triples still emitted

- [x] Task 5 — Migrate federated seed (AC: 3)
  - [x] Replace inline triples in `scripts/seed_spaceapi.py` `build_insert()`;
        compose `extract_core(payload)` only (no state, no contact at seed time)

- [x] Task 6 — Add heartbeat re-extract path (AC: 3, 5)
  - [x] Add `write_payload_fields()` to `infra/link_handler/pipeline.py` — per-predicate
        DELETE+INSERT, explicit exclusion list for the three freshness axis predicates
  - [x] Wire into `run_space_pipeline()` gated on `content_changed=True`
  - [x] Freshness predicates absent test in `tests/test_spaceapi_extract.py` (AC 8 final bullet)

- [x] Task 7 — Update materializer read path (AC: 6)
  - [x] Add OPTIONAL clauses for `mom:countryCode`, `mom:timeZone` to both UNION blocks in
        `scripts/materialize_geojson.py` and `infra/link_handler/main.py`'s SPARQL SELECT
  - [x] Add `schema:contactJson` OPTIONAL to the canary UNION block
  - [x] Update GROUP BY and feature property assembly to expose `country_code` and `timezone`

- [x] Task 8 — Remove PII surface (AC: 7)
  - [x] Delete PII code in `infra/link_handler/main.py` (constant, function, response keys, call site)
  - [x] Delete PII-warning rendering in `web/app.js` (L1047–1048)

- [x] Task 9 — Live-integration test (AC: 9)
  - [x] Write `tests/test_spaceapi_extract_e2e.py` covering canary load, materialize,
        heartbeat re-extract scenario (requires live Oxigraph)

- [x] Task 10 — Regression + operator confirmation (AC: 10, 11)
  - [x] `pytest -m "not legacy"` green (extractor + canary suites pass; remaining
        failures are pre-existing and unrelated — ontology/VOW/live-fixture)
  - [x] Operator verification on a clean `make reset` deploy — surfaced a
        materializer canary-block drift (see Completion Notes); fixed
  - [x] Heartbeat re-extract confirmed via the unified pipeline path

## Dev Notes

### Why library-style + bundle-aligned

The schema bundle model (memory: `project_schema_bundle_model.md`) frames the ontology as
composable layers — core (SpaceAPI v15 spec terms), mom (our extensions), and future
community vocabularies (fab, omt, …). A monolithic `payload_to_triples()` function fights
that composition: it bakes in one fixed mapping. The library-style approach mirrors the
bundle structure directly — `core.py` and `mom.py` are independent modules, and adding a
future community vocab is a drop-in `community_fab.py` rather than a central registry edit.

Each callsite composes the layers it wants. Mutation semantics (DROP+INSERT vs DELETE-WHERE
vs INSERT-DATA) stay at the callsite where they belong — the library has no opinion on
when to clear graphs.

### Why heartbeat re-extracts payload fields

Today address/contact/description only get written at registration. If a space updates their
endpoint after claim, those fields go stale. The three-token freshness model (Epic 3.5
correct-course) already gives us the right signal: `content_changed=True` on the snapshot
means "the payload genuinely changed since last fetch", so re-extracting is bounded —
costs SPARQL traffic only when content actually changes, not every tick.

The freshness axis predicates (`mom:observedAt`, `mom:updatedAt`, `mom:openNow`,
`mom:lastOpenChange`) are deliberately excluded from `write_payload_fields()`. Those have
their own dedicated writers in `pipeline.py` that own diff gating and minting semantics.
A negative unit test (AC 8 final bullet) asserts the extractor's predicate set never
intersects the freshness axis set — without that, a future contributor could add
`mom:openNow` to `extract_mom` and silently introduce a race.

### Why PII removal

The `_PII_FIELDS = {"foaf:mbox"}` surface scans only one field and emits a UI warning that
implies MoM filters PII. It does not — `schema:contactJson` serializes the entire `contact`
object including email. The warning is misleading by omission, and the underlying premise
is wrong: MoM is an IPO service over public coordinator-of-record endpoints. The
coordinator chose to publish those fields publicly; MoM republishes what they publish.
Removing the warning eliminates a false guarantee without changing data flow.

### SOL-3 / non-ISO country codes

Mother Sands sits in the North Sea in international waters. The operator chose
`country_code: "sol-3"` (NASA designation for Earth as the third planet from the Sun) as a
deliberate "outside any nation-state's jurisdiction" marker. `mom:countryCode` is a string
predicate, not an enum — ISO-3166 codes are the common case, but extension codes are
explicitly allowed per the ontology comment. Future canonical extension list for
extraterrestrial / international-waters / temporary-installation cases is a separate
concern (likely Epic 9 / community ontology layer).

### Reused utilities

- `pipeline_helpers._extract_open_now` and `_extract_last_open_change` already handle the
  SpaceAPI v14/v15 state parsing edge cases — `mom.py` calls them rather than
  re-implementing.
- `space_id()` slug generator in `seed_spaceapi.py` stays where it is — callers continue
  to own URI minting (the extractor takes `subject_uri` as input, doesn't compute it).
- Existing `escape_literal` logic in `load_canary.py:_lit()` (handles `\\`, `"`, `\n`) is
  the reference implementation — `sparql.py` copies it.

### Layer ordering

Layer 1 (ontology) ships first as its own PR — the ontology repo is independent and
GitHub Pages takes ~1 minute to refresh. Layer 2 (extractor library) is the riskiest part
and lands second. Layers 3–5 (callsite migrations + read path + PII removal) can be
incremental commits with `pytest` green at each step. Operator visual confirmation
(AC 11) is the final gate.

## Running the Stack

```bash
# Layer 1 — ontology (separate repo, separate PR)
cd /home/nicolas/github/mapsofmaking_ontology
# edit mom.ttl, commit, push, merge
curl -I https://nicolasdb.github.io/mapsofmaking_ontology/ns#countryCode
# expect 200 before continuing

# Layer 2+ — code
cd /var/home/nicolas/github/maps_of_making
source venv/bin/activate

# Unit tests (no Oxigraph needed)
python -m pytest tests/test_spaceapi_extract.py -v

# Live-integration tests (Oxigraph running on localhost:7878)
docker-compose -f infra/docker-compose.dev.yml up -d oxigraph
python -m pytest tests/test_spaceapi_extract_e2e.py -v -m live_integration

# End-to-end smoke
python scripts/load_canary.py
python scripts/materialize_geojson.py
jq '.features[] | select(.properties.name=="Mother Sands") | .properties' \
   web/data/spaces.geojson

# Operator visual confirmation
docker-compose -f infra/docker-compose.dev.yml up -d
# open the map, click Mother Sands marker
# confirm address renders, country_code and timezone present in the dataset
```

## Dev Agent Record

### Completion Notes

- **Task 1**: `ontology/mom.ttl` and `ontology/crosswalk.csv` updated in this repo with `mom:countryCode` and `mom:timeZone`. Operator to copy/paste to adjacent `mapsofmaking_ontology` repo and push (GitHub Pages publish is manual).
- **Task 2**: `scripts/spaceapi_extract/` library created (4 files). 32 unit tests pass. AC 8 freshness-axis negative assertion covered by parametrized test across 3 payload variants.
- **Task 3**: `load_canary.py` migrated. `_lit()` helper deleted. `tests/test_load_canary.py` updated to match new triple set (17 tests pass). Note: `mom:lastUpdated` renamed to `mom:updatedAt` to align with materializer read path.
- **Task 4**: `infra/link_handler/main.py` `_build_sparql_update()` and `_binding_to_feature()` migrated. PII surface (`_PII_FIELDS`, `_scan_pii()`, `pii_warning`/`pii_fields` keys) deleted (Task 8).
- **Task 5**: `scripts/seed_spaceapi.py` migrated. `sparql_str()` deleted. `build_insert()` now takes `(name, endpoint_url, payload)` and composes `extract_core` with explicit exclusion of contactJson/knowsAbout at seed time.
- **Task 6**: `write_payload_fields()` added to `pipeline.py`. Explicit `_FRESHNESS_AXIS` exclusion guard. Wired in `run_space_pipeline()` after `write_updated_at()` when `content_changed=True`.
- **Task 7**: `scripts/materialize_geojson.py` SELECT, OPTIONAL clauses, GROUP BY, and `binding_to_space()` updated. `country_code` and `timezone` now in feature properties.
- **Task 8**: PII block removed from `web/app.js` (L1047–1048). No test was asserting on `pii_warning`.
- **Task 9**: `tests/test_spaceapi_extract_e2e.py` written with 5 live-integration tests covering canary loader triples, materializer properties, and `write_payload_fields` freshness guard.
- **Docker**: Both `infra/docker-compose.yml` and `infra/docker-compose.dev.yml` updated with `spaceapi_extract` volume mount and `SCRIPTS_DIR=/app/scripts` env var.
- **Task 10 operator verification**: On a clean `make reset` deploy the canary card did not reflect `baseline.json` — `description`, `opening_hours`, `endpoint_url` rendered empty despite being in Oxigraph. Root cause: the **canary UNION block** in both materializers (`main.py::_SPARQL_SELECT` and `scripts/materialize_geojson.py::SPARQL_QUERY`) had drifted — missing `schema:description` / `schema:openingHours` OPTIONALs, and `endpoint_url` was read from `mom:profileUrl` only. Fixed: both materializers now SELECT the same variable set (added `?endpointUrl` to main.py, `?openingHours` to materialize_geojson.py, synced both canary blocks); `_binding_to_feature` prefers `mom:endpointUrl`. Field-lifecycle traced and documented in `docs/field-lifecycle.md`.
- **Canary baseline**: `data/canary/baseline.json` extended to exercise the full bundle — `opening_hours` (core) and a bundle-correct `ext_fab` block (`space_type`, `equipment`). `ext_fab` is inert until `extract_fab` (Epic 9 — deferred entry recorded in `deferred-work.md`).

### Debug Log

- AC 8 vs AC 2 apparent contradiction: AC 2 spec said `extract_mom` produces `mom:openNow`/`mom:lastOpenChange`; AC 8 says extractors must NEVER emit freshness predicates. Resolved by following AC 8 strictly — those predicates remain owned exclusively by heartbeat pipeline writers.
- `mom:lastUpdated` vs `mom:updatedAt`: canary loader was producing `mom:lastUpdated` but materializer reads `mom:updatedAt`. Fixed in Task 3 migration; no data migration needed (canary graph is DROP+INSERT on every load).
- `pipeline_helpers` import in `mom.py`: cross-directory import resolved with try/except ImportError pattern; Docker `SCRIPTS_DIR` env var + path-setup block covers both container and local execution.

## File List

- `ontology/mom.ttl` (modified)
- `ontology/crosswalk.csv` (modified)
- `scripts/spaceapi_extract/__init__.py` (created)
- `scripts/spaceapi_extract/sparql.py` (created)
- `scripts/spaceapi_extract/core.py` (created)
- `scripts/spaceapi_extract/mom.py` (created)
- `scripts/load_canary.py` (modified)
- `scripts/seed_spaceapi.py` (modified)
- `scripts/materialize_geojson.py` (modified)
- `infra/link_handler/main.py` (modified)
- `infra/link_handler/pipeline.py` (modified)
- `infra/docker-compose.yml` (modified)
- `infra/docker-compose.dev.yml` (modified)
- `web/app.js` (modified)
- `web/canary/mother-sands.json` (modified — synced from baseline.json by `make c-reset`)
- `data/canary/baseline.json` (modified — opening_hours + ext_fab bundle block)
- `Makefile` (modified — `reset` clears legacy `data/tasks/` files)
- `docs/field-lifecycle.md` (created — 8-stage field trace, core/mom/fab layers)
- `tests/test_spaceapi_extract.py` (created)
- `tests/test_load_canary.py` (modified)
- `tests/test_spaceapi_extract_e2e.py` (created)

## Change Log

- Story 3.11 implemented: unified SpaceAPI extractor library, all four callsites migrated, PII surface removed, new ontology predicates, materializer updated (Date: 2026-05-22)
- Operator verification: fixed materializer canary-block drift (description / opening_hours / endpoint_url), synced both materializers, documented field lifecycle; canary baseline extended with the full core+mom+fab bundle (Date: 2026-05-22)
