---
stepsCompleted: [1, 2, 3]
---

# Implementation Readiness Assessment Report

**Date:** 2026-06-06
**Project:** maps_of_making
**Scope:** Story 5.0 — GL Rendering Substrate + World View Unlock

## Document Inventory

**PRD:** `planning-artifacts/prd.md` (41 KB, 2026-06-05)
**Architecture:** `planning-artifacts/architecture.md` (69 KB, 2026-06-06)
**Epics & Stories:** `planning-artifacts/epics.md` (184 KB, 2026-06-06)
**UX Design:** `planning-artifacts/ux-bernard-wizard-spec.md` (18 KB, 2026-06-02) *(Epic 9 scope — not directly relevant to Story 5.0)*
**Story file:** `implementation-artifacts/5-0-gl-rendering-substrate-world-view.md`

---

## PRD Analysis

**Total FRs: 44** (FR1–FR44 including FR14b, FR25b, FR27b, FR33b, FR35b)
**Total NFRs: 30** (NFR-P1–5, NFR-R1–7, NFR-S1–6, NFR-D1–4, NFR-C1–3, NFR-A1–5, NFR-I1–5, NFR-L1–4, NFR-O1–2)

### Functional Requirements (Story 5.0 relevant subset)

| FR | Text | Story 5.0 relevance |
|---|---|---|
| FR1 | Fullscreen MapLibre GL JS map | Direct — GL substrate |
| FR2 | Pan, zoom, cluster expansion, pin stability at all zoom levels | Direct — cluster + GL layers |
| FR3 | Pin states rendered visually: ⚪ seeded / 🔵 confirmed / dashed stale / 🔴 broken | Direct — full colour ladder in GL |
| FR4 | Default view centered on FR/DE pilot area | Superseded by Story 5.0 — world view replaces EU box |
| FR8 | Shareable URL state encoding active filters + map bounds | Touched — share URL gains lat/lon coords |
| FR15 | Iframe embed snippet generator | Touched — embed URL gains coord params |
| FR17 | Embeds carry attribution + last-confirmed caption | Downstream of 5.0 (embed polish in 5.3) |
| FR18 | Share button produces deep-link URL | Direct — viewport-first coord encoding |
| FR25 | Three-axis freshness state → computed marker | Direct — `computeMarker()` ported to GL paint |

### Non-Functional Requirements (Story 5.0 relevant)

| NFR | Text | Story 5.0 relevance |
|---|---|---|
| NFR-P2 | Filter/search updates <200ms | Direct — GL `setFilter()` vs DOM tear-down |
| NFR-P3 | Space detail drawer <300ms | Touched — selectSpace via feature-state |
| NFR-R5 | Map functional when ≤50% endpoints unreachable | Direct — GL source handles partial data gracefully |
| NFR-A4 | Color never sole indicator of pin state | Gap flagged below |

---

## Epic Coverage Validation

### FR Coverage Matrix (full product scope)

| FR | PRD Requirement (summary) | Epic Coverage | Status |
|---|---|---|---|
| FR1 | MapLibre GL + PMTiles | Epic 1 → Epic 5 (5.0) | ✓ Covered |
| FR2 | Pan/zoom/cluster stability | Epic 5 (5.0) | ✓ Covered |
| FR3 | Pin states rendered visually | Epic 1 → Epic 5 (5.0) | ✓ Covered |
| FR4 | Default view FR/DE + graceful fallback | Epic 1 → Epic 5 (5.0 replaces EU box) | ✓ Covered |
| FR5 | Filter drawer facets | Epic 5 (5.1) | ✓ Covered |
| FR6 | Text search | Epic 5 (5.1) | ✓ Covered |
| FR7 | Live filter/search update | Epic 5 (5.1) | ✓ Covered |
| FR8 | Shareable URL | Epic 5 (5.0 adds coords, 5.1 wires filters) | ✓ Covered |
| FR9 | Session filter persistence | Epic 5 | ✓ Covered |
| FR10 | Empty-state messaging | Epic 5 | ✓ Covered |
| FR11 | Clear-all-filters | Epic 5 | ✓ Covered |
| FR12 | Pin click → detail drawer | Epic 5 | ✓ Covered |
| FR13 | Provenance URL + last-fetched timestamp | Epic 2 | ✓ Covered |
| FR14 | Copy-to-clipboard | Epic 5 | ✓ Covered |
| FR14b | observed_at / updated_at tokens in drawer | Epic 2 / Epic 3.5 (done) | ✓ Covered |
| FR15 | Iframe embed snippet | Epic 5 (5.0 + 5.3) | ✓ Covered |
| FR16 | Web component `<maps-of-making>` | Epic 5 | ✓ Covered |
| FR17 | Attribution + last-confirmed in embeds | Epic 5 (5.3) | ✓ Covered |
| FR18 | Share URL deep-link | Epic 5 (5.0) | ✓ Covered |
| FR19 | Coordinator submits JSON URL | Epic 2 | ✓ Covered |
| FR20 | URL validation (reach + schema) | Epic 2 | ✓ Covered |
| FR21 | Pin flip ⚪→🔵 on registration | Epic 2 | ✓ Covered |
| FR22 | Reciprocal embed snippet | Epic 2 | ✓ Covered |
| FR23 | No edit UI | Epic 2 | ✓ Covered |
| FR24 | Periodic fetch (cadence configurable) | Epic 3 | ✓ Covered |
| FR25 | Three-axis marker computed in browser | Epic 3 (done) | ✓ Covered |
| FR25b | Closure logic, PII removed | Epic 3 | ✓ Covered |
| FR26 | Diff detection | Epic 2 | ✓ Covered |
| FR27 | Ingestion failure logging | Epic 3 | ✓ Covered |
| FR27b | Raw payload in SQLite receipt | Epic 2/3 (done) | ✓ Covered |
| FR28 | Admin dashboard: all endpoints | Epic 4 | ✓ Covered |
| FR29 | Dashboard status filters | Epic 4 | ✓ Covered |
| FR30 | Per-endpoint drill-down | Epic 4 | ✓ Covered |
| FR31 | Manual re-fetch | Epic 4 | ✓ Covered |
| FR32 | Oxigraph sync status | Epic 4 | ✓ Covered |
| FR33 | Export registry | Epic 4 | ✓ Covered |
| FR33b | Admin audit log | Epic 4 | ✓ Covered |
| FR34 | Oxigraph SPARQL 1.1 | Epic 1 (done) | ✓ Covered |
| FR35 | IoP ontology validation | Epic 6 | ✓ Covered |
| FR35b | Lenient validation + gap log | Epic 6 | ✓ Covered |
| FR36 | Public SPARQL read-only | Epic 1 (done) | ✓ Covered |
| FR37 | Bot NL questions | Epic 6 | ✓ Covered |
| FR38 | NL→SPARQL via Nanobot | Epic 6 | ✓ Covered |
| FR39 | Bot results + SPARQL transparency | Epic 6 | ✓ Covered |
| FR40 | Bot graceful failure | Epic 6 | ✓ Covered |
| FR41 | Failed queries logged as ontology gaps | Epic 6 | ✓ Covered |
| FR42 | Discord + Telegram + Mattermost | Epic 6 | ✓ Covered |
| FR43 | Admin shared-password auth | Epic 4 | ✓ Covered |
| FR44 | Public map no auth | Epic 1 (done) | ✓ Covered |

**Coverage: 44/44 FRs — 100%**

### Coverage drift notes (epics.md vs PRD)

The epics.md Requirements Inventory carries **stale text** on several FRs that diverge from the PRD's 2026-06-05 correction-pass:

| FR | epics.md text (stale) | PRD text (authoritative) | Risk |
|---|---|---|---|
| FR24 | "6-hour cadence" | "10-minute cadence" | Low — config-driven, but epics.md misrepresents the PoC default |
| FR25 | "state machine: confirmed→stale→broken→closed" | "three orthogonal axes computed in browser" | **Medium** — a dev reading epics.md Requirements Inventory could implement a server-side state machine. The Epic 3 stories and architecture ADRs correctly describe the three-token model; the stale text is in the **inventory section only**. |
| FR27b | "append-only versioned snapshots, each fetch stored" | "raw payload retained verbatim in SQLite, latest per space" | Low — Epic 3 stories reflect the correct model; inventory is stale wording |

**Recommendation:** Update the Requirements Inventory section of epics.md in a future editorial pass (not a blocker for Story 5.0).

---

## UX Alignment Assessment

### UX Document Status

`ux-bernard-wizard-spec.md` exists — scoped to **Epic 9 (Bernard's Workshop)**, the assisted SpaceAPI JSON composer. It is not a UX spec for the map SPA.

For Story 5.0 specifically, UX intent is documented in two bespoke planning artifacts that serve as the authoritative visual spec:
- `state-colour-ladder.html` — two-surface (Daylight/Depth) colour ladder, full 8-state taxonomy
- `overview-effect-north-stars.md` — continental-scale UX principles (label dissolve, freshness=fragility, restraint, no network colouring at altitude)

### Alignment Issues

| Area | Issue | Severity |
|---|---|---|
| NFR-A4 (colour not sole indicator) | Story 5.0 ACs specify colour-driven GL circles for all states. At street zoom the `broken` state uses red colour; `open` uses bright green+pulse; `shut` uses dimmed green. No shape/pattern variation is specified — colour IS the sole differentiator between states. The existing DOM markers used SVG shapes (✕ for broken, tombstone emoji for dead) which satisfied NFR-A4. GL circles risk losing that. | **Medium** — the story's Task 2 notes "broken: circle colour + (if needed) a small symbol layer with text glyphs" but leaves this as an implementation decision rather than an AC. |
| No overall map UX spec | The map SPA (Epics 1–5) lacks a formal UX document. UX decisions live distributed across `epics.md` UX Design Records (UX-DR1–27) and the planning artifacts above. This is workable but means a dev agent reads epics.md for UX intent — which is the current practice. | Low — by convention, not a gap |

### Warnings

⚠️ **NFR-A4 risk in Story 5.0:** The current story AC3 ("full colour ladder is honoured") does not explicitly require a non-colour differentiator for pin states. Recommend adding to Task 2: "Confirm `broken` state carries a visual marker beyond colour (e.g. a `×` symbol layer) to satisfy NFR-A4 — colour must not be the sole indicator."

---

## Epic Quality Review

### Epic Structure Validation (Story 5.0 focus + cross-epic scan)

**Epics assessed:** Epic 0 (done), 1 (done), 2 (done), 3 (done), 3.5 (done), 4 (backlog), 5 (in-progress), 6 (backlog), 7 (parked), 8 (stub), 9 (active), 10 (future)

#### User Value Focus — PASS

All active epics describe user/operator outcomes, not technical milestones:
- Epic 2: "Space coordinators can register a JSON URL and watch their pin flip confirmed" ✓
- Epic 3: "Endpoint health pipeline keeps pins fresh automatically" ✓
- Epic 4: "Operator can see system health and diagnose pipeline issues in one glance" ✓
- Epic 5: "Map renders correctly at every scale for every visitor" ✓
- Epic 9: "Bernard's Workshop — coordinator can compose a valid SpaceAPI JSON without knowing the format" ✓

#### Epic Independence — PASS with one noted coupling

Epic 5.0 explicitly gates all of 5.1–5.5, stated and intentional. This is a **designed prerequisite**, not a forward dependency violation — 5.0 is a `.0` substrate story, a BMAD-established pattern. Stories 5.1–5.5 do not require stories beyond Epic 5.

One legitimate cross-epic coupling to note: **Epic 5.1** (Filters + Search Wired to Real Federated Data) has a soft dependency on Epic 3 (ingestion pipeline). Epic 3 is done, so this is resolved, but the epics.md text should be read as "Epic 3 must be done before 5.1 goes to prod" — which it is.

#### Story Sizing — PASS

Story 5.0 is large by conventional sizing but justified: it is explicitly a *substrate migration* (delete + rewrite the rendering layer) that must land atomically. Splitting into "add GL source" + "remove DOM markers" would leave the app in a broken hybrid state between stories. The 7-task structure internally sequences the work.

#### Acceptance Criteria Quality — PASS with one flag

Story 5.0 ACs use full BDD Given/When/Then. Scenarios covered: GL source init, clustering, label dissolve, world view, viewport-first init, legacy fallback. **One gap:**

🟠 **(RESOLVED 2026-06-06)** An earlier draft of AC2 specified "status-weighted cluster blend," which was stale ideation — the map does **not** cluster. Corrected to a **zoom-scaled point field**: every space is its own ladder-coloured dot, `circle-radius` ramps with zoom (field of light → street dots). Visual reference is the MapTiler `helpers/point` example (reproduced in vanilla GL, no SDK). No aggregation algorithm needed; the flag is void.

#### Dependency Analysis — PASS

No forward dependencies detected in Story 5.0. All referenced functions (`computeMarker`, `filteredSpaces`, `selectSpace`, `applyUrlParams`) exist in the current codebase. All design references (`state-colour-ladder.html`, `overview-effect-north-stars.md`, ADR-017) are already written.

#### Brownfield Integration Check — PASS

Story 5.0 is explicit about brownfield context: it migrates, not replaces, the functional behaviour. `computeMarker()`, `filteredSpaces()`, `selectSpace()`, `applyUrlParams()` are preserved with adapted interfaces. The "What is preserved / What is retired" lists in ADR-017 are replicated in the story Dev Notes.

---

## Final Assessment

### Story 5.0 Implementation Readiness

| Area | Status | Notes |
|---|---|---|
| FR coverage | ✅ 100% (44/44) | No missing FRs |
| Story ACs completeness | ✅ Pass | 6 ACs, full BDD |
| Architecture alignment | ✅ Pass | ADR-017 matches story scope exactly |
| UX alignment | ⚠️ Warning | NFR-A4 non-colour indicator not explicitly required in ACs |
| AC2 model | ✅ Corrected | Was "status-weighted clusters" (stale) → now zoom-scaled point field; no clustering |
| Epic quality | ✅ Pass | Substrate story pattern valid; sizing justified |
| Stale epics inventory | 🟡 Minor | FR24/FR25/FR27b wording drift vs PRD (editorial, not story-blocking) |
| Dependencies | ✅ Clear | No forward deps; referenced code exists |

### Readiness Verdict

**Story 5.0 is READY FOR DEV.** Both review findings have been applied to the story file:

1. **✅ AC2 corrected** — the "status-weighted cluster blend" was stale ideation. The map does not cluster. AC2/AC3/Task 1/Task 3 rewritten to a **zoom-scaled point field**: every space is its own ladder-coloured dot, radius ramps with zoom (field of light → street dots), reproducing the MapTiler `helpers/point` look in vanilla GL. Ladder surface (Daylight/Depth) follows the tweaks-panel theme toggle, not zoom.

2. **✅ NFR-A4 enforced** — Task 2 now *requires* the `broken ×` symbol layer (and non-colour markers for `dead`/`zombie`/`aging`), so colour is never the sole state differentiator.

3. **✅ Stale epics inventory wording fixed** — FR24/FR25/FR27b reconciled to the PRD three-token model.

One open implementation note carried into the story (not a blocker): the dev must **retro-engineer the MapTiler `helpers/point` behaviour** (size+colour-by-value over a dense field, possible opacity falloff) and reproduce the *look* with pure GL expressions — escalating to Nicolas only if a desired effect genuinely can't be done without the SDK.
