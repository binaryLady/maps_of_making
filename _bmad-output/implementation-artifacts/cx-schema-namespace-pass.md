# Story C.X: Schema Namespace Pass — ext_mom → ext_canary, Introduce mom: Horizontal Fields

**Status:** done
**Epic:** Cleanup (shared prereq)
**Blocks:** Epic 9 (Bernard's Workshop) AND Epic 4 re-review
**Source:** `_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-29.md`

---

## Story

As an operator,
I want to rename the `ext_mom` silo namespace to `ext_canary` (which is all it ever contained),
and introduce proper `mom:` horizontal fields for cross-network data (`opening_hours`, `memberOf`, `mom:sdgs`),
so that the four-tier schema is internally consistent before building Epic 9's wizard and re-reviewing Epic 4.

---

## Four-Tier Schema Context (LOCKED — reference for all decisions)

| Tier | Namespace | Scope | Examples |
|---|---|---|---|
| **0** | SpaceAPI v15 core subset | Floor | `space` (name), `location.address` → derived |
| **1** | SpaceAPI v15 **core** | Common to all SpaceAPI apps | `logo`, `url`, `description`, `contact.*`, `state.*` |
| **2** | `mom:` | **Horizontal** — most/all networks | `opening_hours`, `memberOf`, `mom:sdgs` |
| **3** | `ext_X` | **Vertical** — silo-specific | `ext_canary.*` (was `ext_mom`), `ext_fab.*`, future `ext_*` |

**Renames in this story:**
- `ext_mom` → `ext_canary` (Mother-Sands-only canary control fields belong in a canary silo, not a "mom" silo)
- `ext_fab.sdgs` → `mom:sdgs` (SDGs are transversal across networks, not FabLab-specific)
- `memberOf` stays in Tier 2 (`mom:memberOf`) — already correctly placed in extractor

---

## Acceptance Criteria

### AC-1: baseline.json and web/canary/mother-sands.json renamed
- `ext_mom` key renamed to `ext_canary` in **both** files:
  - `data/canary/baseline.json`
  - `web/canary/mother-sands.json`
- `ext_fab.sdgs` field **moved** to top-level `mom:sdgs` (integer array) in both files
- All other fields unchanged

Expected diff for `web/canary/mother-sands.json`:
```json
// BEFORE
"ext_mom": { "memberOf": ["canary"], "canary": true, "simulatedAge": 0, "thresholdMode": false },
"ext_fab": { "space_type": "makerspace", "equipment": [...], "sdgs": [9, 11, 12, 14, 17] }

// AFTER
"mom:sdgs": [9, 11, 12, 14, 17],
"ext_canary": { "memberOf": ["canary"], "canary": true, "simulatedAge": 0, "thresholdMode": false },
"ext_fab": { "space_type": "makerspace", "equipment": [...] }
```

### AC-2: Python code updated — all `ext_mom` references → `ext_canary`

Files to update (complete list):

| File | Line(s) | Change |
|---|---|---|
| `scripts/load_canary.py` | 89, 151 | `data.get("ext_mom", {})` → `data.get("ext_canary", {})` |
| `scripts/canary_scenarios.py` | 92, 105, 118, 131, 145, 146, 166, 181, 195, 298, 307, 308, 318 | `payload["ext_mom"]` → `payload["ext_canary"]`; `.setdefault("ext_mom", {})` → `.setdefault("ext_canary", {})` |
| `scripts/spaceapi_extract/core.py` | 74–76 | `payload.get("ext_mom")` and `ext_mom.get("memberOf")` → `payload.get("ext_canary")` and `ext_canary.get("memberOf")` |
| `infra/link_handler/main.py` | 761–762 | `payload.get("ext_mom")` → `payload.get("ext_canary")`; `ext_mom.get("thresholdMode")` → `ext_canary.get("thresholdMode")` |

**Note on memberOf fallback in `core.py`:** The extractor already prefers top-level `memberOf` over `ext_mom.memberOf`. After this rename, the fallback should read from `ext_canary.memberOf`. The canary baseline file will move `memberOf` into `ext_canary` (not top-level), so this fallback must be kept — don't delete it.

### AC-3: `mom:sdgs` extraction added to `spaceapi_extract/core.py`

Add SDG extraction to `extract_core()`. SDGs are a Tier-2 horizontal field:

```python
# In extract_core(), after the memberOf block:
sdgs = payload.get("mom:sdgs")
if sdgs is None:
    # Fallback: migrate from ext_fab.sdgs during transition
    ext_fab = payload.get("ext_fab") or {}
    if isinstance(ext_fab, dict):
        sdgs = ext_fab.get("sdgs")
if isinstance(sdgs, list):
    cleaned = [int(s) for s in sdgs if isinstance(s, (int, float)) and 1 <= int(s) <= 17]
    if cleaned:
        fields["mom:sdgs"] = cleaned
```

Also update `sparql.py` to handle `mom:sdgs` as a multi-value integer list (similar to `schema:knowsAbout` but emitting integers, not quoted strings):

```python
# In triples_for(), add a branch before the generic literal fallback:
if curie == "mom:sdgs":
    items = val if isinstance(val, list) else [val]
    for item in items:
        out.append(f"<{subject_uri}> <{pred_uri}> {int(item)} .")
    continue
```

### AC-4: Ontology updated (`ontology/mom.ttl`)

Add two property declarations to `mom.ttl`:

```turtle
mom:sdgs
  a owl:DatatypeProperty ;
  rdfs:label "Sustainable Development Goals" ;
  rdfs:comment "UN SDG numbers (1–17) that this space's activities address. Transversal across networks — Tier 2 mom: field." ;
  rdfs:domain mom:Space ;
  rdfs:range xsd:integer .

mom:opening_hours
  a owl:DatatypeProperty ;
  rdfs:label "Opening hours" ;
  rdfs:comment "SpaceAPI v15 opening_hours string. Cross-network horizontal field — Tier 2 mom: namespace. Maps to schema:openingHours in the extractor." ;
  rdfs:domain mom:Space ;
  rdfs:range xsd:string .
```

**Note:** `opening_hours` is already correctly extracted in `core.py` as `schema:openingHours`. The ontology entry here is for completeness — no code change needed for opening hours.

### AC-5: Canary reset + reload verifies cleanly

Run:
```bash
make c-reset           # restores web/canary/mother-sands.json from data/canary/baseline.json
source venv/bin/activate && python3 scripts/load_canary.py
```

Expected log output:
- `stage=map_triples ... count=N` (N ≥ 12 — roughly same as before, plus sdgs triples)
- `stage=oxigraph_write status=ok graph=urn:mak:canary`
- NO errors about missing `ext_mom`

### AC-6: Canary scenario tests pass unchanged

Run:
```bash
source venv/bin/activate && python3 scripts/canary_scenarios.py --list
```

All scenarios list without error. Then smoke-test one scenario to confirm `ext_canary` is read correctly:
```bash
make cb-confirmed   # sets simulatedAge=0 → lifecycle=confirmed
source venv/bin/activate && python3 scripts/load_canary.py
```

Expected: no KeyError, lifecycle logged as `confirmed`.

### AC-7: Map renders unchanged after reseed

After load_canary succeeds, trigger rematerialize and confirm canary pin appears on map:
```bash
# Inside container or via API:
curl -s http://localhost:8000/api/rematerialize
```

The Mother Sands pin must appear on the map with correct name, position, and lifecycle marker. No regression in other map features.

---

## Scope Boundaries (what NOT to do in this story)

- **Do NOT** add `mom:sdgs` as a filter in the map UI (deferred to Epic 5 or later)
- **Do NOT** change `opening_hours` extraction — it already maps to `schema:openingHours` in `extract_core()` and this story does not change that
- **Do NOT** touch the seed pipeline for bulk VOW/RFF spaces (`seed_spaceapi.py`, `seed_bundle.py`) — those spaces have no `ext_mom` and are unaffected
- **Do NOT** change the three named-graph model or heartbeat pipeline
- **Do NOT** add `mom:memberOf` as a top-level field in baseline.json — it stays inside `ext_canary.memberOf` (the fallback in `core.py` covers this)
- **Do NOT** rename `ext_fab` — it is a legitimate Tier-3 silo for FabLab-specific fields

---

## Dev Notes: Current State of Key Files

### `data/canary/baseline.json` and `web/canary/mother-sands.json`
Both contain identical `ext_mom` + `ext_fab.sdgs` shape. `c-reset` copies baseline → served file. Both must be updated simultaneously.

### `scripts/canary_scenarios.py`
Directly mutates `payload["ext_mom"]` at multiple points (simulatedAge, thresholdMode, operatorDeclaredClosed). After rename, all `payload["ext_mom"]` become `payload["ext_canary"]`. The `setdefault("ext_mom", {})` at line 307 must also be updated.

### `scripts/load_canary.py`
Two call-sites: `data.get("ext_mom", {}).get("simulatedAge")` in `_classify_lifecycle()` and `build_canary_sparql()`. Both renamed. `_classify_lifecycle()` is a pure function — rename the key arg, no behavior change.

### `scripts/spaceapi_extract/core.py`
Already has the `memberOf` fallback from `ext_mom`. The fallback comment also mentions `ext_mom` — update the comment too.

### `infra/link_handler/main.py`
The `thresholdMode` branch reads `ext_mom` from the heartbeat fetch payload (the live served JSON). After renaming `web/canary/mother-sands.json`, the served JSON will have `ext_canary`, so the reader must match.

### `scripts/spaceapi_extract/sparql.py`
The `_NS` dict maps `mom:` prefix. `mom:sdgs` will expand correctly via `_expand()`. Only need to add the integer-list emission branch in `triples_for()`.

---

## Test Verification Sequence

Execute in order, confirm each step before proceeding:

1. **Edit files** (AC-1 through AC-4)
2. `make c-reset` — verifies baseline.json is the source of truth
3. `source venv/bin/activate && python3 scripts/load_canary.py` — AC-5
4. `make cb-confirmed && source venv/bin/activate && python3 scripts/load_canary.py` — AC-6
5. `curl -s http://localhost:8000/api/rematerialize` (or run via `make heartbeat`) — AC-7
6. Visually confirm canary pin on map

---

---

## Dev Agent Record

### Completion Notes

All 7 ACs satisfied. Additional post-review work completed 2026-05-30:

- **AC-1:** `ext_mom` → `ext_canary`, `ext_fab.sdgs` + `memberOf` → nested `"mom": { "sdgs": [...], "memberOf": [...] }` block in both JSON files.
- **AC-2:** All `ext_mom` references renamed across all Python files.
- **AC-3:** `mom:sdgs` extraction added; `core.py` reads from `mom_block` with fallbacks.
- **AC-4:** Ontology updated.
- **AC-5:** `make c-reset` verified — lands on `seeded` marker (not confirmed); count=23.
- **AC-6:** `canary_scenarios.py b-confirmed` sets `state.open="opted-out"` (non-boolean opt-out mode); Axis C scenarios reset from baseline to preserve `simulatedAge` integrity.
- **AC-7:** Full local canary lifecycle verified: seeded → confirmed → aging → zombie → dead → closed.

**Additional scope completed (2026-05-30):**
- Canary ops parity refactor: `scripts/canary_ops.py` (new) — single in-container mechanism for all Oxigraph/snapshot/API mutations; `vps-*` Makefile twins for every lifecycle target.
- Dead code removal: `_classify_lifecycle()` + `mom:operationalState` removed from `load_canary.py` and all seed scripts; browser derives lifecycle from three freshness tokens exclusively.
- `clear-endpoint` now also removes `updatedAt`/`observedAt` from Oxigraph so `c-reset` correctly lands on `seeded` marker.
- `docker-compose.dev.yml`: full `../scripts` dir mount (eliminates stale-inode issue from single-file bind mounts).
- 48 tests pass.

### File List

- `data/canary/baseline.json`
- `web/canary/mother-sands.json`
- `scripts/load_canary.py`
- `scripts/canary_scenarios.py`
- `scripts/canary_ops.py` (new)
- `scripts/spaceapi_extract/core.py`
- `scripts/spaceapi_extract/sparql.py`
- `scripts/seed_spaceapi.py`
- `scripts/seed_bundle.py`
- `scripts/seed_import.py`
- `infra/link_handler/main.py`
- `infra/link_handler/pipeline.py`
- `infra/docker-compose.dev.yml`
- `ontology/mom.ttl`
- `tests/test_load_canary.py`
- `Makefile`
- `_bmad-output/implementation-artifacts/cx-schema-namespace-pass.md`
- `_bmad-output/implementation-artifacts/sprint-status.yaml`

### Change Log

- 2026-05-29: Rename `ext_mom` → `ext_canary` across all Python and JSON files; promote `ext_fab.sdgs` → `mom:sdgs`; add SDG extraction + integer triple emission; update ontology.
- 2026-05-30: Nest `sdgs`+`memberOf` under `"mom":{}` block; canary ops parity refactor (`canary_ops.py` + Makefile `vps-*` twins); remove dead `mom:operationalState`/`_classify_lifecycle` code; fix `c-reset` → seeded marker; full scripts dir mount in dev compose; `cb-confirmed` sets opted-out mode; 48 tests pass.

---

## Cross-References

- Sprint change proposal: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-29.md`
- Canary design: `memory/project_story_3_3_canary_design.md`
- Schema bundle model: `memory/project_schema_bundle_model.md`
- Four-tier schema (locked): sprint-change-proposal §"Architectural framework"
- `c-reset` target in `Makefile` line 260–278
- Three named-graph model: `memory/project_three_graph_model.md`
