# Story 9.6: Wizard Tier 2 — `mom:` Fields (opening_hours, memberOf, mom:sdgs)

Status: ready-for-dev

## Story

As a space coordinator who has completed Tiers 0 + 1,
I want to fill in the MoM-specific horizontal fields that unlock network features (membership, opening hours, SDGs),
So that my space appears correctly in network filters and benefits from the cross-network features MoM provides.

## Context

**Dependencies:**
- **Story C.X (namespace pass)** — `mom:opening_hours`, `mom:memberOf`, and `mom:sdgs` must be declared in `mom.ttl` before the transformer maps them. This story assumes C.X is complete.
- **Stories 9.3 + 9.5** — Tier 0/1 wizard exists; Bernard voice artifact locked in `bernard_copy.yaml`.

**Tier gate philosophy:**
Tier 2 is unlocked only after Tier 1 (SpaceAPI core) is complete. The three fields here are MoM extensions (`mom:` namespace), not SpaceAPI native. This gates access to MoM-specific network features: membership discovery, opening-hours-based search, SDG alignment filtering.

**Upstream sealing (Story 9.3):**
Story 9.3 export includes an optional `mom:memberOf: null` seed key to telegraph Tier 2 existence. This story fills that slot.

---

## Acceptance Criteria

### AC1 — Tier 2 section presents three fields in order

**Given** the coordinator has passed Tier 1 and advances to Tier 2
**When** Story 9.6 lands
**Then** the Tier 2 section is rendered with three input fields in order, each with a one-line label and a max two-line hint (all copy from `bernard_copy.yaml`):

1. **`mom:opening_hours`** — text input
   - Placeholder: `Mo-Fr 10:00-18:00`
   - Label: "Opening hours"
   - Hint from `COPY.field_hints.opening_hours`: *"When are you open? We use OSM opening_hours format."*
   - A client-side "validate hours format" check (regex or minimal OSM parser) highlights **invalid** OSM format strings with an amber border (non-blocking — user can export anyway)
   - Validation message if invalid: from `COPY.validation_messages` (if a key exists for this; defer to implementation — see Dev Notes)

2. **`mom:memberOf`** — text input (or comma-separated URLs)
   - Placeholder: `https://network.example.org`
   - Label: "Network memberships"
   - Hint from `COPY.field_hints.memberOf`: *"Which network(s) is this space part of? URL preferred."*
   - Accepts free text if URL validation fails (e.g. "Hackerspace.sg") — logs as `mom:OntologyGap` on ingestion, does not block export
   - Comma-separated URLs are supported (split on `,` at export time; trim whitespace)

3. **`mom:sdgs`** — multi-select chip grid
   - Label: "UN Sustainable Development Goals"
   - Hint from `COPY.field_hints.sdgs`: *"Which UN Sustainable Development Goals does your space contribute to? Numbers only."*
   - Renders 17 chips in a compact grid, labeled `1 — No Poverty` through `17 — Partnerships for the Goals` (SDG short titles, not full names)
   - Selection is additive; clicking a chip toggles it (visual feedback: filled vs. unfilled); selected chips show a visual state (colour + checkmark or similar)
   - No more than 17 items — one per SDG
   - Mobile-friendly: chips stack/wrap without horizontal overflow

**And** the Tier 2 exit banner renders (from `COPY.tier_2_exit`): *"MoM fields filled. Network features unlocked: membership, opening hours, SDGs."* (exact text from `bernard_copy.yaml` — do not hardcode)

### AC2 — Export includes `mom:` fields if filled

**Given** the coordinator reaches Tier 2 and fills any or all three fields
**When** clicking "Export JSON" (available at any point after Tier 1)
**Then** the downloaded SpaceAPI v15 document includes `mom:opening_hours`, `mom:memberOf`, `mom:sdgs` **only if they are filled**:
  - Unfilled fields are **omitted entirely** (not `null`) — "present = declared" principle
  - `mom:opening_hours` exports as-is (string)
  - `mom:memberOf` exports as an array of URLs (split comma-separated input into `[url1, url2, ...]`)
  - `mom:sdgs` exports as an array of integers (e.g. `[4, 5, 8, 13]` — the selected SDG numbers)

**And** the export continues to validate **non-blockingly** against the bundled SpaceAPI v15 schema (AC4 from Story 9.3):
  - Schema allows `additionalProperties` at top-level, so `mom:` fields pass
  - If validation fails (rare), a non-blocking warning lists invalid fields; export is NOT blocked

### AC3 — SDG chip selection persists in localStorage

**Given** the coordinator selects SDG chips
**When** any SDG selection changes
**Then** the selected SDG set is persisted in the `localStorage.getItem('genjson_draft')` object (same save-on-change pattern as Tier 1)
**And** on page reload, if a draft exists, SDG selections are restored from the saved state (no loss of selection)

### AC4 — Gating test: export and ingest to Oxigraph

**Gating test** — `test_wizard_tier2_export` (browser E2E, operator manual):
  1. Fill Tier 1 (name + address + one core field)
  2. Advance to Tier 2
  3. Fill all three Tier 2 fields:
     - `opening_hours`: `Tu-Th 14:00-20:00, Sa 12:00-18:00` (multi-range OSM format)
     - `memberOf`: `https://rff-hub.fr, https://makerspace.network` (two URLs, comma-separated)
     - `sdgs`: select chips 4, 5, 8 (Quality Education, Gender Equality, Decent Work)
  4. Click "Export JSON"
  5. Validate exported JSON contains:
     - `mom:opening_hours: "Tu-Th 14:00-20:00, Sa 12:00-18:00"` (string)
     - `mom:memberOf: ["https://rff-hub.fr", "https://makerspace.network"]` (array)
     - `mom:sdgs: [4, 5, 8]` (array of integers)
  6. Submit via Story 2.1 registration endpoint (`POST /api/validate-url`)
  7. Assert triples present in Oxigraph:
     - `ASK { ?s mom:opening_hours "Tu-Th 14:00-20:00, Sa 12:00-18:00" }`
     - `ASK { ?s mom:memberOf ?url . FILTER(contains(str(?url), "rff-hub.fr")) }`
     - `ASK { ?s mom:sdgs "4"^^xsd:integer }` (or similar, depending on schema — verify against mom.ttl)

**And** operator visual confirmation: SDG chips render correctly on mobile without overflow, multiple URLs parse correctly on ingest, opening-hours format validation feedback is visible but non-blocking.

### AC5 — Backward compatibility: existing Tier 1 drafts load without error

**Given** a coordinator has an existing localStorage draft from Story 9.3 (before Tier 2 existed)
**When** Story 9.6 lands and the wizard loads
**Then** the draft loads successfully, Tier 2 fields are empty (not `null`), and the wizard can still be exported and re-submitted without error
**And** no migration warning is shown (graceful backward compatibility)

---

## Tasks / Subtasks

- [ ] **Tier 2 section UI** (AC1)
  - [ ] Add Tier 2 container to `genjson.js` with three input sections (opening_hours, memberOf, sdgs)
  - [ ] Render opening_hours text input with placeholder `Mo-Fr 10:00-18:00`
  - [ ] Render memberOf text input with placeholder `https://network.example.org`
  - [ ] Render SDG chip grid (17 chips, numbered 1–17 with titles)
  - [ ] Wire up `COPY.field_hints.opening_hours`, `COPY.field_hints.memberOf`, `COPY.field_hints.sdgs` from `bernard_copy.yaml`
  - [ ] Render Tier 2 exit banner using `COPY.tier_2_exit`

- [ ] **OSM opening_hours validation** (AC1)
  - [ ] Implement minimal regex or parser for OSM format (e.g. `Mo-Fr 10:00-20:00` or comma-separated ranges)
  - [ ] On blur of opening_hours input, validate format and show visual feedback (amber border if invalid)
  - [ ] Validation is **non-blocking** — user can export with invalid format (logs as gap on ingestion)
  - [ ] See Dev Notes for OSM format reference and validation approach

- [ ] **Export assembly** (AC2)
  - [ ] Modify export logic to include `mom:opening_hours`, `mom:memberOf`, `mom:sdgs` in the output JSON
  - [ ] Omit unfilled fields entirely (not as `null`)
  - [ ] Split comma-separated `memberOf` input into URL array (trim whitespace)
  - [ ] Convert SDG chip selection array to `[integer, integer, ...]` format
  - [ ] Confirm export continues to pass non-blocking schema validation from Story 9.3

- [ ] **localStorage persistence** (AC3)
  - [ ] Update `saveDraft()` to persist Tier 2 field values
  - [ ] Update `loadDraft()` to restore Tier 2 values
  - [ ] SDG selection state saved as array of selected integers (e.g. `[4, 5, 8]`)
  - [ ] No loss of state on page reload

- [ ] **Backward compatibility** (AC5)
  - [ ] Test that a draft from Story 9.3 (no Tier 2 keys) loads without error
  - [ ] Tier 2 section renders with empty fields, no warnings
  - [ ] Confirm existing Tier 1 export still works

- [ ] **E2E gating test** (AC4)
  - [ ] Follow test scenario: fill Tier 1 + Tier 2, export, submit, validate Oxigraph triples
  - [ ] Operator manual verification (Nicolas)
  - [ ] Confirm mobile rendering (no horizontal overflow on SDG chips)

---

## Dev Notes

### OSM opening_hours format

The Open Street Map `opening_hours` tag is a semi-standardized format for recurring opening hours. Examples:
- `Mo-Fr 10:00-20:00` — Monday to Friday, 10 AM to 8 PM
- `Mo-Fr 10:00-13:00, 14:00-20:00; Sa 10:00-16:00` — weekday split (lunch break) + Saturday
- `24/7` — always open
- `off` — always closed (seasonal closure, etc.)

**Full grammar:** https://wiki.openstreetmap.org/wiki/Key:opening_hours

For this story, a **minimal validation** is sufficient:
- Reject if it contains invalid weekday abbreviations (e.g. `Xy-Zq`)
- Reject if time format is clearly broken (e.g. `25:99`)
- Allow free text otherwise (e.g. "By appointment only" — logs as gap on ingestion, doesn't block)

**Implementation approach:**
```javascript
function validateOpeningHours(input) {
  if (!input) return true; // empty is valid (omitted from export)
  
  const validDays = ['Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa', 'Su'];
  const pattern = /^[A-Za-z0-9\-\:,;\s\/]+$/; // permissive: alphanumeric + delimiters
  
  if (!pattern.test(input)) return false; // reject control chars, etc.
  
  // Minimal: reject if it contains a day abbreviation not in the list
  const dayPattern = /\b[A-Z][a-z]\b/g;
  const foundDays = input.match(dayPattern) || [];
  return foundDays.every(day => validDays.includes(day));
}
```

If validation fails, render an amber border on the input + a small message (from `COPY.validation_messages` if a key exists, or a generic "Format check failed — you can still export").

### SDG titles (17 items)

Full SDG list with short names (for chip labels):
1. No Poverty
2. Zero Hunger
3. Good Health and Well-Being
4. Quality Education
5. Gender Equality
6. Clean Water and Sanitation
7. Affordable and Clean Energy
8. Decent Work and Economic Growth
9. Industry, Innovation and Infrastructure
10. Reducing Inequalities
11. Sustainable Cities and Communities
12. Responsible Consumption and Production
13. Climate Action
14. Life Below Water
15. Life on Land
16. Peace, Justice and Strong Institutions
17. Partnerships for the Goals

Render as a grid of 17 clickable chips. Selected state: visual toggle (e.g. filled background + checkmark, vs. outlined/unfilled). No limit on selections (can select all 17).

### Export format for `mom:` fields

The exported JSON should look like:
```json
{
  "api_compatibility": ["15"],
  "space": "Openfab Brussels",
  ...
  "mom:opening_hours": "Tu-Th 14:00-20:00, Sa 12:00-18:00",
  "mom:memberOf": ["https://rff-hub.fr", "https://makerspace.network"],
  "mom:sdgs": [4, 5, 8]
}
```

**Key rules:**
- Omit any field if unfilled (not as `null`)
- `mom:memberOf` is an array of URLs (split comma-separated input on export)
- `mom:sdgs` is an array of integers (the selected chip numbers)

At ingestion (Story 3.0 transformer / Epic 3.5 snapshot pipeline):
- `mom:opening_hours` (string) → stored as-is (OSM format validation deferred to search/UI layer)
- `mom:memberOf` (array) → each URL becomes a triple: `<space> mom:memberOf <url>`
- `mom:sdgs` (array) → each integer becomes a triple: `<space> mom:sdgs "4"^^xsd:integer` (or verify exact data type in mom.ttl)

**Transformer contract (story 3.0 / epic 3.5):**
Assumes the SpaceAPI input from the wizard is passed directly through; transformer does not modify `mom:*` fields (it preserves them from input to Oxigraph). Verify this with the current transformer code before landing.

### localStorage key structure

The `genjson_draft` key already holds Tier 1 values. Extend it to include Tier 2:

```javascript
const draft = {
  // Tier 0
  space: "Openfab",
  address: "...",
  city: "Brussels",
  postcode: "1000",
  country_code: "BE",
  lat: 50.85,
  lon: 4.36,
  
  // Tier 1
  logo: "https://...",
  url: "https://...",
  description: "...",
  contact_email: "...",
  contact_matrix: "@room:example.org",
  state_open: null,
  
  // Tier 2 (new)
  mom_opening_hours: "Mo-Fr 10:00-20:00",
  mom_memberOf: "https://rff.fr, https://fab.network",  // comma-separated string in storage
  mom_sdgs: [4, 5, 8]  // array of integers
};
```

When exporting:
- `mom_sdgs` is already an array — use directly
- `mom_memberOf` is a comma-separated string in storage — split and trim at export time

### Gating test scenario

```
1. Load genjson.mapsofmaking.org
2. Fill Tier 0: Openfab, Rue Jozef Wybran 1, Brussels, 1000, BE
3. Coordinates derive: 50.85, 4.36
4. Advance to Tier 1
5. Fill: logo (URL), url (https://openfab.be), description (one sentence)
6. Advance to Tier 2 (first time seeing these fields)
7. Fill:
   - Opening hours: Tu-Th 14:00-20:00, Sa 12:00-18:00
   - Memberships: https://rff-hub.fr, https://makerspace.network
   - SDGs: click chips 4, 5, 8
8. Click Export JSON
9. Validate the downloaded JSON:
   - Contains mom:opening_hours: "Tu-Th 14:00-20:00, Sa 12:00-18:00"
   - Contains mom:memberOf: ["https://rff-hub.fr", "https://makerspace.network"]
   - Contains mom:sdgs: [4, 5, 8]
   - All Tier 1 fields present
   - api_compatibility: ["15"] present
10. Upload to a test coordinator URL (or use Story 2.1 endpoint)
11. In Oxigraph, confirm triples:
    - ASK { ?s mom:opening_hours "Tu-Th 14:00-20:00, Sa 12:00-18:00" }
    - ASK { ?s mom:memberOf ?url FILTER(contains(str(?url), "rff-hub.fr")) }
    - ASK { ?s mom:sdgs ?n FILTER(?n = 4 || ?n = 5 || ?n = 8) }
12. Reload page; draft auto-loads with all fields intact
13. Mobile test: view Tier 2 on phone (< 768px); SDG chips wrap without horizontal overflow
```

### Backward compatibility test

```
1. Create a localStorage draft from Story 9.3 (pre-Tier 2):
   { space: "Test", address: "...", contact_email: "test@example.com" }
2. Load genjson.mapsofmaking.org
3. Wizard should render with Tier 0/1 loaded, Tier 2 fields empty
4. No error, no migration warning
5. Advance to Tier 2; fields are empty (no "null" confusion)
6. Export and confirm no Tier 2 keys appear (only Tier 1 fields present)
```

### Previous story intelligence (Story 9.5 — done)

Story 9.5 locked the `bernard_copy.yaml` artifact with the following keys this story depends on:
- `field_hints.opening_hours`, `field_hints.memberOf`, `field_hints.sdgs`
- `tier_2_exit`
- Optional: `validation_messages.*` keys for format errors (see AC1)

If a `validation_messages` key does not exist for opening_hours validation, use a generic message or leave the feedback visual-only (amber border).

### Story 9.3 integration

Story 9.3 export includes an optional `mom:memberOf: null` seed key:
```json
{
  ...
  "mom:memberOf": null
}
```

This story **replaces** that `null` with actual data if the user fills the field, or **omits it entirely** if unfilled (per AC2). The seed key from 9.3 is a placeholder to telegraph the existence of Tier 2 — this story fulfills the contract.

### Source tree

- `web/genjson/genjson.js` — UPDATE (add Tier 2 section, OSM validation, export assembly, localStorage Tier 2 keys)
- `web/genjson/bernard_copy.yaml` — already complete (Story 9.5); this story reads `COPY.field_hints.opening_hours/memberOf/sdgs` + `COPY.tier_2_exit`
- `web/genjson/bernard_copy.json` — regenerated from YAML (existing `make bernard-copy` target)

No backend changes, no schema changes (C.X is prerequisite, already done). No nginx changes. No new containers.

### Isolation Notes

- **Frontend only** — serve `web/genjson/` locally via `python3 -m http.server 8080` or maps-nginx
- Activate venv (`source venv/bin/activate`) for any Python test work
- No container restart needed
- To test gating test: use the local dev stack (`distrobox-host-exec podman compose ...`) to run a local registration endpoint or manually submit the export JSON to a real coordinator space

### References

- [Source: _bmad-output/planning-artifacts/epics.md § Story 9.6]
- [Source: _bmad-output/planning-artifacts/bernard-bible.md § voice rules, tone]
- [Source: _bmad-output/implementation-artifacts/9-5-bernard-voice-copy-pass-curated-voice-artifact.md § AC1 YAML structure]
- [Source: _bmad-output/implementation-artifacts/9-3-wizard-core-tiers-0-1-name-address-spaceapi-v15-core-localstorage-export.md § localStorage contract, export assembly, AC4 schema validation]
- [Source: _bmad-output/planning-artifacts/architecture.md § ADR-016 ontology namespaces, ADR-015 ingestion transformation]
- [Source: https://wiki.openstreetmap.org/wiki/Key:opening_hours — OSM format specification]
- [Source: UN SDGs official list — https://sdgs.un.org/ — for chip labels]
- [Source: memory/project_three_token_freshness_model.md — three-axis model, observed_at contract]

---

## Out of Scope

- `state.open` FSM — Story 9.7
- Tier 3 `ext_fab` fields — Story 9.10
- URL-fetch pre-fill / validator mode — Story 9.9
- Visual design (colors, spacing, contrast) — Story 9.12
- Wizard error UX / inline per-field error messages — Story 9.11
- Opening hours / memberOf / SDG **validation at ingestion** (ontology gap logging, schema conformance) — Epic 3.5 (transformer + Story 3.0)

---

## Completion Checklist

Use this checklist to track progress during implementation. Move to completion notes when done.

- [ ] AC1 — Tier 2 UI rendered with three fields + copy from `bernard_copy.yaml`
  - [ ] opening_hours text input with OSM validation (amber border if invalid, non-blocking)
  - [ ] memberOf text input (accepts comma-separated URLs or free text)
  - [ ] SDG chip grid (17 chips, toggleable selection, mobile-friendly)
  - [ ] Tier 2 exit banner rendering `COPY.tier_2_exit`

- [ ] AC2 — Export includes `mom:` fields if filled, omits if empty
  - [ ] `mom:opening_hours` exports as string (if filled)
  - [ ] `mom:memberOf` splits comma-separated input to array (if filled)
  - [ ] `mom:sdgs` exports as array of integers (if filled)
  - [ ] Non-blocking schema validation still works

- [ ] AC3 — SDG selection persists in localStorage
  - [ ] saveDraft() stores Tier 2 values
  - [ ] loadDraft() restores Tier 2 values
  - [ ] Reload test: values retained

- [ ] AC4 — Gating test passes
  - [ ] Fill Tier 1 + Tier 2, export, submit, validate Oxigraph triples
  - [ ] Operator manual E2E confirmation
  - [ ] Mobile chip rendering confirmed

- [ ] AC5 — Backward compatibility
  - [ ] Existing Story 9.3 draft loads without error
  - [ ] Tier 2 fields start empty (no `null` confusion)
  - [ ] Export of old draft omits Tier 2 keys

---

## Completion Notes

*(To be filled when the story is done.)*

**Status:** ready-for-dev  
**Target:** demoable Tier 2 input with network features unlock messaging  
**Risk:** OSM format validation UX (non-standard syntax); backward compatibility with pre-Tier-2 drafts  
**Key decision:** Tier 2 fields are optional MoM extensions, not SpaceAPI required — gates post-Tier 1 access, telegraphis Story 9.8 (hosting tutorial) and Story 9.6+ pedagogy  

