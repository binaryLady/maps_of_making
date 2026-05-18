# Story 3.5: `core.ttl` + `crosswalk.csv` — Operationalize the Three-Layer Schema

Status: done

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

- [x] **Task 1: Author `ontology/core.ttl`** (AC: 1)
  - [x] Read `mom-schema-architecture-handoff.md` Layer 2 section for the field list
  - [x] Read `ontology/mom.ttl` to identify properties already declared (do not redefine)
  - [x] Write `ontology/core.ttl` — `core:` sub-namespace; Identity (schema: reuse via `rdfs:seeAlso`), MOM-operational (mom: reuse), and `core:relationships` groups
  - [x] Add `rdfs:comment` annotations marking each property's layer (identity/operational/relationship)
  - [x] Verify it parses (`rdflib` → 80 triples OK)
- [x] **Task 2: Add `mom:OntologyGap` to `mom.ttl` if absent** (AC: 3)
  - [x] Confirmed `mom:OntologyGap` absent; declared class + `mom:rawQuery`/`mom:rawLLMOutput`/`mom:timestamp` per `architecture.md` line 683
- [x] **Task 3: Author `ontology/crosswalk.csv` + `crosswalk.md`** (AC: 2)
  - [x] Read `transformer.py::transform_to_sparql` and enumerated every predicate it emits
  - [x] Cross-checked against the handoff's SpaceAPI→`core:` table and ADR-015
  - [x] Wrote `crosswalk.csv` — 31 rows; `core_field` = predicate actually emitted
  - [x] Added `fab:equipment` ↔ `schema:knowsAbout` activities row (concept-commons pivot)
  - [x] Added `omt:`/`edu:` placeholder rows, each `status: draft` in notes
  - [x] Wrote `crosswalk.md` narrative (living bridge registry v1)
- [x] **Task 4: Audit + verify permissive ingestion** (AC: 3)
  - [x] Traced `transformer.py`: no "reject on field X" logic; `resolve_activities` never drops a tag
  - [x] Documented `_log_unmapped_tags` → `gap_log.txt` behaviour in Dev Notes
  - [x] Decision: defer `mom:OntologyGap` triple emission → Story 6.3 (recorded below)
- [x] **Task 5: Author `scripts/validate_crosswalk.py`** (AC: 4)
  - [x] Parses `crosswalk.csv` with stdlib `csv`
  - [x] Enforces: non-empty `core_field` + non-alias extension field → fail with clear message (negative-tested)
  - [x] Runs against `crosswalk.csv`; passes (31 rows checked)
- [x] **Task 6: Write ADR-016 — Layered community bundles** (AC: 1, 2)
  - [x] Added `ADR-016: Layered Community Namespaces + Bundle-Loading Model` to `architecture.md`
  - [x] Recorded four-layer model, bundle-loading, concept pivot, living bridge registry, OKH/Wikidata anchors
- [x] **Task 7: Verify end-to-end**
  - [x] `core.ttl` parses (80 triples); `validate_crosswalk.py` passes; no `w3id.org` IRIs anywhere
  - [x] Manual-sync note recorded in Completion Notes

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

claude-sonnet-4-6 (Amelia / bmad-dev-story)

### Debug Log References

- `core.ttl` rdflib parse: 80 triples OK
- `mom.ttl` rdflib parse after edit: 185 triples OK
- `validate_crosswalk.py`: OK — 31 rows checked, no-redefinition rule holds
- Negative test: validator correctly rejects a `core_field` + extension-field row with non-skos `mapping_type`

### Completion Notes List

- **Static-artifact story** — no transformer/Docker/Oxigraph behaviour change. AC1/2/4 produce files; AC3 is an audit.
- **AC3 permissive-ingestion decision (pinned):** `transformer.py` has no "reject on field X" logic. `resolve_activities()` never drops a tag — unknown tags fall back to the raw string and are appended to `gap_log.txt` (plain text) by `_log_unmapped_tags()`. Decision: **keep `gap_log` as-is; do NOT build `mom:OntologyGap` triple emission in this story — deferred → Story 6.3.** The `gap_log` is intentionally the on-ramp for emergent community ontology (gap term → curation → concept minting → bridge discovery), not a janitorial dump. `mom:OntologyGap` class declared in `mom.ttl` now (cheap; Story 6.3 needs it).
- **Incoherence flagged & documented (not silently fixed):** Story Dev Notes line 130 and ADR-015 (`architecture.md:495`) state `location.address → schema:address`. The live transformer (`transformer.py:507`) actually emits `mom:address` as `xsd:string`. Per AC2 ("`core_field` = predicate the code actually writes"), `crosswalk.csv`'s address row records `mom:address` and flags the discrepancy in its `notes` column; `crosswalk.md` has a "Known incoherence" section. Reconciling code to the idealized mapping is out of scope for 3.5.
- **`core.ttl` design:** identity fields are pure Schema.org terms — reused via `rdfs:seeAlso`, never re-minted. Operational fields stay owned by `mom:` and are referenced, not redefined. The only new terms minted in the `core:` sub-namespace (`…/ns/core#`) are `core:Place` and the `core:relationships` family. No `w3id.org` IRIs anywhere (verified).
- **Manual sync required:** `ontology/mom.ttl` and `ontology/core.ttl` are working copies. The maintainer must manually sync them to the `github.com/nicolasdb/mapsofmaking_ontology` repo. No automated push was performed.
- This story closes Epic 3. After it reaches `done`, Epic 3 can transition to `done` and the retrospective run.

### File List

- `ontology/core.ttl` (NEW) — Layer 2 base schema
- `ontology/crosswalk.csv` (NEW) — overlap-resolution table, 31 rows
- `ontology/crosswalk.md` (NEW) — human-readable crosswalk narrative
- `scripts/validate_crosswalk.py` (NEW) — no-redefinition enforcement
- `ontology/mom.ttl` (MODIFIED) — added `mom:OntologyGap` class + `rawQuery`/`rawLLMOutput`/`timestamp`
- `_bmad-output/planning-artifacts/architecture.md` (MODIFIED) — appended ADR-016 + editHistory entry

### Review Findings

- [x] [Review][Decision] `schema:contactJson` is not a real Schema.org predicate — `core.ttl` uses `rdfs:seeAlso schema:contactJson` (fabricated IRI; `schema:contactPoint` is the real one) and AC1 requires a `contactEmail` identity field. The transformer emits `schema:contactJson` as a non-standard predicate (pre-existing). Decision: (a) keep as-is with an explicit "non-standard" note; (b) alias to `schema:contactPoint` in core.ttl; (c) move to `mom:contactJson` under the mom: namespace. [AC1/AC2]
- [x] [Review][Patch] `core:relationshipType`/`relationshipSince`/`relationshipTarget` declare `rdfs:domain core:relationships`, but `rdfs:domain` must be a class, not a property — removed domain declarations; comments updated to describe blank-node usage [ontology/core.ttl]
- [x] [Review][Patch] `mom:timestamp` domain too narrow — renamed to `mom:gapTimestamp` [ontology/mom.ttl]
- [x] [Review][Patch] `validate_crosswalk.py` — added header column assertion + BOM-safe `utf-8-sig` encoding [scripts/validate_crosswalk.py]
- [x] [Review][Patch] `validate_crosswalk.py` error message now reports column names not field values [scripts/validate_crosswalk.py]
- [x] [Review][Defer] `core:Place rdfs:subClassOf mom:Space` cross-layer dependency — both layers always load together per ADR-016, so portable-bundle portability is moot for PoC; revisit at Epic 9 fab.ttl extraction [ontology/core.ttl] — deferred, pre-existing by design
- [x] [Review][Defer] No check that `core_field` IRI values actually exist in ontology files — typos pass validation silently [scripts/validate_crosswalk.py] — deferred, pre-existing
- [x] [Review][Defer] `owl:versionInfo "0.1"` with no `dcterms:created`/`dcterms:modified` in core.ttl — deferred, pre-existing pattern in mom.ttl
- [x] [Review][Defer] UTF-8 BOM not handled by `validate_crosswalk.py` — deferred, all files are git-tracked; low risk for this project

## Change Log

| Date | Change |
|---|---|
| 2026-05-18 | Story 3.5 implemented — `core.ttl`, `crosswalk.csv`, `crosswalk.md`, `validate_crosswalk.py` created; `mom:OntologyGap` added to `mom.ttl`; ADR-016 added to `architecture.md`. Status → review. |
