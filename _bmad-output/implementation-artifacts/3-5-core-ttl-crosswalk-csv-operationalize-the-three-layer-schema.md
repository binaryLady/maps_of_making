# Story 3.5: `core.ttl` + `crosswalk.csv` — Operationalize the Three-Layer Schema

Status: ready-for-dev

**Story ID:** 3.5
**Epic:** 3 (Ingestion Pipeline + Endpoint Health + Stale Detection) — closes Epic 3
**Branch:** mom-demo
**Dependencies:** none hard. **Not demo-blocking.** Builds on the clean-slate foundation from Story 3.4b.
**Sequenced:** last in Epic 3.

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As MOM,
I want the three-layer schema model (SpaceAPI v15 input → `core:` base → community extension namespaces) operationalized as concrete, dereferenceable artifacts,
so that the SpaceAPI→`core:` mapping ingestion already performs is documented, validatable, and ready for a second community.

## Context

### Why this story exists

Ingestion already maps SpaceAPI v15 fields to MOM predicates (ADR-015), but the **Layer 2 base vocabulary** and the **cross-namespace overlap rules** exist only as prose in `_bmad-output/planning-artifacts/mom-schema-architecture-handoff.md`. The handoff names two missing deliverables:

- `core.ttl` — the Layer 2 base schema (the minimum shared vocabulary every MOM community inherits).
- `crosswalk.csv` — the overlap-resolution table (which SpaceAPI field maps to which `core:` / `fab:` field, and how).

Both are needed before the "Article 2" publication and before a second community (`omt:` health network) can be onboarded.

### Critical correction — read before touching any IRI

The handoff document body uses illustrative `https://w3id.org/maps-of-making/core/` IRIs. **These are wrong and must NOT appear in any `.ttl`, `.csv`, query, or code.** The handoff's own correction block (lines 9–14) is authoritative over its body:

1. **Canonical namespace** is `https://nicolasdb.github.io/mapsofmaking_ontology/ns#` (prefix `mom:`). The three-layer `core:` / `fab:` / `omt:` / `edu:` split is real, but it lives **under** this canonical namespace — not under `w3id.org`.
2. The ontology repo `github.com/nicolasdb/mapsofmaking_ontology` already exists (published via GitHub Pages). It currently holds only `mom.ttl` + `LICENSE` — the `core/ fab/ omt/ edu/` tree drawn in the handoff is a *future target*, not current state.
3. **Sync model:** `ontology/mom.ttl` in *this* repo is the working copy. The maintainer manually syncs it to the `mapsofmaking_ontology` repo. Any ontology edit lands in `ontology/` here first.

### What "documents the mapping ingestion already performs" means

`crosswalk.csv` must reflect the **actual predicates the code emits today**, not the idealized `core:` names in the handoff table. The current transformer (`infra/link_handler/transformer.py::transform_to_sparql`) emits a mix of `schema:` and `mom:` predicates — for example `schema:name`, `schema:geo`, `schema:url`, `schema:address`, `mom:operationalState`, `mom:endpointUrl`, `mom:openNow`. The crosswalk's "actual predicate" column must match what `transform_to_sparql` writes, verified by reading the code. Where the handoff's idealized `core:` name differs from the emitted predicate, record both and note the discrepancy.

### The data lifecycle this story formalizes

The flow diagram (`_bmad-output/planning-artifacts/26.05.17_data-lifecycle.excalidraw`) shows: SpaceAPI endpoints → heartbeat conditional GET → `transformer.py` (SpaceAPI → RDF triples) → Oxigraph named graphs (`urn:mak:space/{slug}`, `urn:mak:canary`, `urn:mak:ontology/{mom,iop}`, reserved `urn:mak:public_ledger`) → materialization → `web/data/spaces.geojson` → browser map. This story does **not** change that flow. It adds the missing *schema specification* the transform step maps **to**, so the transform becomes documented and validatable rather than implicit.

## Acceptance Criteria

### AC 1: `core.ttl` exists and is dereferenceable

**Given** the Layer 2 field list in the schema-architecture handoff (`mom-schema-architecture-handoff.md`, "Layer 2 — `core:` base schema" section)
**When** the dev creates `ontology/core.ttl`
**Then** `core.ttl` declares, at minimum, the three property groups:
- **Identity** (inherited from SpaceAPI): name, website, logo, address, location/geo, contactEmail, description, isOpen
- **MOM-operational** (not in SpaceAPI): endpointUrl, freshness/`operationalState`, lastFetched, source/`sourceLabel`, communities
- **`core:relationships`** — the typed cross-community link property (array of `{type, target_url, tags, since}`)

**And** `core.ttl` declares its MOM-owned terms (`core:Place`, `core:relationships`) in the **sub-namespace `https://nicolasdb.github.io/mapsofmaking_ontology/ns/core#`** (prefix `core:`); pure Schema.org identity fields (name, logo, url, geo, address) are **reused directly as `schema:` terms** and referenced from `core.ttl` via `rdfs:seeAlso` — not re-minted; **no `w3id.org` IRIs anywhere**
**And** the file is valid Turtle (parses with `rdflib` or loads into Oxigraph without error)
**And** properties already declared in `mom.ttl` (e.g. `mom:operationalState`, `mom:geolocationFidelity`) are referenced/reused, not redefined with conflicting ranges

### AC 2: `crosswalk.csv` documents the real mapping

**Given** the SpaceAPI v15 → MOM mapping `transform_to_sparql` actually performs
**When** the dev creates `ontology/crosswalk.csv`
**Then** each row records: `concept, core_field, spaceapi_field, fab_field, omt_field, edu_field, mapping_type, notes` (the column format from the handoff's "crosswalk.csv format" section)
**And** every SpaceAPI→predicate mapping the current transformer emits has a row, with `core_field` set to the **predicate the code actually writes** (verified against `transformer.py`)
**And** the `fab:equipment` ↔ `schema:knowsAbout` row is present (activity-tag mapping — see `resolve_activities` + `activity_map.yaml`); `schema:knowsAbout` is the **shared concept pivot** (the wormhole hub) — every community's specialised skill field aliases to it via `skos:closeMatch`
**And** activity/skill concepts are labelled in the `notes` column as **"concept commons (shared layer) — future: own namespace"** so the future `fab.ttl` extraction does NOT mis-file them into `fab:`
**And** `omt:` and `edu:` rows are present but every such row carries `status: draft` in its `notes` column (namespace design is out of scope — community input required)
**And** a companion `ontology/crosswalk.md` gives a short human-readable narrative AND states explicitly that `crosswalk.csv` is a **living bridge registry, v1** — future `skos:closeMatch` rows are appended as cross-community bridges are discovered (see ADR-016)

### AC 3: Permissive-ingestion rule is verified

**Given** the permissive-ingestion rule (ingest everything parseable; never reject; log unrecognised fields)
**When** the dev audits `transformer.py` and `infra/link_handler/main.py`
**Then** it is confirmed (and documented in Dev Notes) that the pipeline logs unrecognised fields/tags as ontology-gap signals — never rejects them
**And** the **decision is pinned** (confirmed by the maintainer): keep the existing `gap_log` collection for unmapped activity tags; **do NOT build `mom:OntologyGap` triple emission in this story** — that is deferred, tagged `→ Story 6.3`. The `gap_log` is intentionally the **on-ramp for emergent community ontology** (gap term → curation → concept minting → bridge discovery), not a janitorial dump — document it in Dev Notes as such
**And** `mom:OntologyGap` is confirmed declared in `mom.ttl` (add the class + its properties if absent — Story 6.3 will need it; declaring it now is cheap)

### AC 4: `validate_crosswalk.py` enforces the no-redefinition rule

**Given** the rule "no extension namespace may redefine a `core:` field — alias only via `skos:exactMatch`/`skos:closeMatch`"
**When** the dev creates `scripts/validate_crosswalk.py`
**Then** the script parses `crosswalk.csv` and fails (non-zero exit, clear message) if any row has a non-empty `core_field` **and** a non-empty extension field (`fab_field`/`omt_field`/`edu_field`) that is not an explicit alias declaration
**And** the script passes cleanly against the `crosswalk.csv` produced in AC2
**And** the script is runnable standalone (`python scripts/validate_crosswalk.py`) and prints a one-line summary on success

## Tasks / Subtasks

- [ ] **Task 1: Author `ontology/core.ttl`** (AC: 1)
  - [ ] Read `mom-schema-architecture-handoff.md` Layer 2 section for the field list
  - [ ] Read `ontology/mom.ttl` to identify properties already declared (do not redefine)
  - [ ] Write `ontology/core.ttl` using the canonical `mom:` namespace prefix — Identity, MOM-operational, and `core:relationships` property groups; reuse `mom:operationalState`, `mom:geolocationFidelity`, etc.
  - [ ] Add `rdfs:comment` annotations marking each property's layer (base/operational/relationship)
  - [ ] Verify it parses (load into local Oxigraph or `python -c "import rdflib; rdflib.Graph().parse('ontology/core.ttl')"`)
- [ ] **Task 2: Add `mom:OntologyGap` to `mom.ttl` if absent** (AC: 3)
  - [ ] Check `mom.ttl` for `mom:OntologyGap`; if missing, declare the class + `mom:rawQuery`/`mom:rawLLMOutput`/`mom:timestamp` (or field-gap equivalent) per `architecture.md`
- [ ] **Task 3: Author `ontology/crosswalk.csv` + `crosswalk.md`** (AC: 2)
  - [ ] Read `transformer.py::transform_to_sparql` and enumerate every predicate it emits and the SpaceAPI field it derives from
  - [ ] Cross-check against the handoff's SpaceAPI→`core:` table and ADR-015's field-mapping table
  - [ ] Write `crosswalk.csv` with one row per real mapping; `core_field` = predicate actually emitted
  - [ ] Add `fab:equipment` ↔ `schema:knowsAbout` row (activity tags)
  - [ ] Add `omt:`/`edu:` placeholder rows, each `status: draft` in notes
  - [ ] Write `crosswalk.md` narrative
- [ ] **Task 4: Audit + verify permissive ingestion** (AC: 3)
  - [ ] Trace field handling in `transformer.py` and `main.py`: confirm no "reject on field X" logic exists
  - [ ] Document in Dev Notes how unrecognised fields/tags are currently handled (`_log_unmapped_tags` → `gap_log.txt`)
  - [ ] Decide: extend to `mom:OntologyGap` triples now, or defer tagged `→ Story 6.3` — record decision + rationale
- [ ] **Task 5: Author `scripts/validate_crosswalk.py`** (AC: 4)
  - [ ] Parse `crosswalk.csv` with stdlib `csv`
  - [ ] Enforce: non-empty `core_field` + non-alias extension field → fail with clear message
  - [ ] Run it against `crosswalk.csv`; confirm it passes
- [ ] **Task 6: Write ADR-016 — Layered community bundles** (AC: 1, 2)
  - [ ] Add `ADR-016: Layered Community Namespaces + Bundle-Loading Model` to `architecture.md` (follow the existing ADR format, e.g. ADR-015)
  - [ ] Record: the four-layer model (core / mom / concept commons / community); `config.yaml` bundle-loading (analogous to `docker-compose`); bundles = view config, graph = universal; `schema:knowsAbout` as the concept pivot; `crosswalk.csv` as a living bridge registry; OKH/Wikidata as external concept anchors (candidates, not wired)
- [ ] **Task 7: Verify end-to-end**
  - [ ] `core.ttl` parses; `validate_crosswalk.py` passes; all files committed under `ontology/` and `scripts/`
  - [ ] Note in Completion Notes that `ontology/mom.ttl` (and now `core.ttl`) require **manual sync** to the `mapsofmaking_ontology` repo by the maintainer — do not attempt to push there

## Dev Notes

### Authoritative facts (override the handoff body)

- **Namespace authority:** `https://nicolasdb.github.io/mapsofmaking_ontology/` only — never `w3id.org`. `mom:` = `…/ns#` (unchanged); `core:` = the new `…/ns/core#` sub-namespace. See "Resolved design decision" below. [Source: mom-schema-architecture-handoff.md correction block lines 9–14; maintainer decision 2026-05-18]
- **Sync model:** `ontology/mom.ttl` here is the working copy; maintainer manually syncs to the `mapsofmaking_ontology` GitHub repo. Edits land in `ontology/` in *this* repo. Do not git-push to the ontology repo.
- **`omt:`/`edu:` namespace design is out of scope** — needs OMT/education community input. Placeholder draft rows only. [Source: epics.md Story 3.5; mom-schema-architecture-handoff.md "Deferred" section]

### Current pipeline state (read these before writing the crosswalk)

- `infra/link_handler/transformer.py::transform_to_sparql` (lines ~368–544) is the live SpaceAPI→RDF mapping. It emits `schema:name`, `schema:geo` (nested `schema:GeoCoordinates`-style blank node), `schema:url`, `schema:address`, `schema:openingHours`, `schema:description`, `schema:logo`, `schema:contactJson`, `schema:knowsAbout`, and `mom:operationalState`, `mom:endpointHealth`, `mom:lastFetched`, `mom:lastUpdated`, `mom:source`, `mom:endpointUrl`, `mom:geolocationFidelity`, `mom:geolocationNote`, `mom:openNow`, `mom:lastOpenChange`, `mom:memberOf`, `mom:apiCompatibility`, `mom:networks`, `mom:subset`, `mom:nextUnlock`, `mom:snapshotDate`, `mom:snapshotSummary`, `mom:lastHttpStatus`, `mom:rawContent`.
- **Note the predicate reality:** the handoff's idealized `core:name`/`core:website`/`core:isOpen` correspond to the code's `schema:name`/`schema:url`/`mom:openNow`. The crosswalk documents *what the code does* — capture both the idealized `core:` concept name and the real emitted predicate.
- Unmapped activity tags are logged today via `_log_unmapped_tags()` → `gap_log.txt` (a plain text file, NOT RDF triples). `resolve_activities()` never drops a tag — unknown tags fall back to the raw string. This is the "permissive ingestion" behavior for tags. There is currently **no** `mom:OntologyGap` triple emission for unrecognised top-level fields — AC3 forces an explicit decision on this.

### Source tree — files to create / touch

| File | Action | Purpose |
|---|---|---|
| `ontology/core.ttl` | NEW | Layer 2 base schema |
| `ontology/crosswalk.csv` | NEW | Overlap-resolution table |
| `ontology/crosswalk.md` | NEW | Human-readable crosswalk narrative |
| `scripts/validate_crosswalk.py` | NEW | No-redefinition enforcement |
| `ontology/mom.ttl` | UPDATE (only if `mom:OntologyGap` absent) | Add gap class if missing |

`ontology/` already contains `mom.ttl`, `iop/iop.ttl`, `context/space.jsonld`. `scripts/` already contains `load_ontology.sh`, `load_canary.py` — follow their conventions (shebang, `cd` to repo root, clear stdout messages).

### Resolved design decision — the four-layer bundle model

The namespace question was worked through with the maintainer (2026-05-18). **Decision: layered sub-namespaces under the one canonical authority** `https://nicolasdb.github.io/mapsofmaking_ontology/`. The handoff's `w3id.org` IRIs remain illegal; the layer split is real and lives *under* the canonical authority as sub-namespaces.

Four layers:

| Layer | Namespace / file | Loaded | Role |
|---|---|---|---|
| `core` | `…/ns/core#` — `ontology/core.ttl` | always | portable identity (name, logo, website, geoloc, address, `core:relationships`) |
| `mom` | `…/ns#` — `ontology/mom.ttl` (unchanged) | always | federation engine — `operationalState`, `endpointHealth`, `lastFetched`, `lastUpdated`, `memberOf`, `description`, `source` |
| concept commons | currently inside `mom.ttl` (`mom:ActivityScheme`) — future own namespace | always (in the graph) | the SKOS concept graph `schema:knowsAbout` resolves into (CNC, 3D-printing…) — owned by nobody, traversable by everybody |
| community (`fab`/`omt`/`edu`/`agri`…) | future per-community `.ttl` | per `config.yaml` bundle | community vocabulary + fields + CSS |

Key principles the dev must respect (they shape `core.ttl` and the crosswalk, even though most are future work):
- **Bundles are *view* configuration; the Oxigraph graph is universal.** A community map renders its bundle by default, but the graph holds every node — the wormhole is a backend traversal, surfaced only on query.
- **The concept commons is NOT a community bundle.** A dentist who never loaded `fab:` is still discoverable by a woodworker's "who does CNC near me" query, because both `knowsAbout` values resolve to the *same* concept IRI. This is "design for emergence" — zero coordination between the two communities.
- For 3.5: **do not move the activity scheme out of `mom.ttl`.** Just label those concepts in `crosswalk.csv` as "concept commons" so the future `fab.ttl` extraction (separate epic) doesn't mis-file them.
- `mom.ttl` today is impure (engine + makerspace activity concepts). The `fab.ttl` extraction is future work (see Epic 9 stub), not this story.

### Testing standards

- No live-integration test required (this story produces static artifacts + a validator script).
- `core.ttl` validity = parses with `rdflib` or loads into Oxigraph.
- `validate_crosswalk.py` is itself the test for `crosswalk.csv`; it must pass against the committed CSV. Add a deliberately-bad fixture row in a docstring example or a `--self-test` mode if quick to do, but a clean pass against the real CSV is the bar.
- Activate venv for any Python command: `source venv/bin/activate` (venv is managed externally — never create one).

### Project Structure Notes

- Artifacts live in `ontology/` and `scripts/`, consistent with `mom.ttl`, `iop.ttl`, `load_ontology.sh`.
- No Docker, Oxigraph schema, or transformer behavior change is required by ACs 1, 2, 4. AC3 *may* introduce a transformer change (OntologyGap triples) — if so, it touches `transformer.py`/`main.py` and would warrant a live heartbeat check; otherwise the change is deferred.
- This story closes Epic 3. After it reaches `done`, Epic 3 can transition to `done` and the retrospective run.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.5]
- [Source: _bmad-output/planning-artifacts/mom-schema-architecture-handoff.md] — correction block (lines 9–14), Layer 1/2/3 sections, crosswalk.csv format, "What Claude Code needs to do"
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-015] — SpaceAPI→MOM field mapping contract; `mom:OntologyGap` pattern (~line 683)
- [Source: infra/link_handler/transformer.py] — `transform_to_sparql`, `resolve_activities`, `_log_unmapped_tags`
- [Source: ontology/mom.ttl] — existing canonical vocabulary
- [Source: scripts/load_ontology.sh] — script conventions; how ontology graphs load into Oxigraph
- [Source: _bmad-output/planning-artifacts/26.05.17_data-lifecycle.excalidraw] — data lifecycle flow diagram (context only; not modified)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
