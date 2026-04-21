# Next Session — Maps of Making

**Snapshot date:** 2026-04-21 (drift investigation complete)
**PRD:** `_bmad-output/planning-artifacts/prd.md` — COMPLETE (all 12 steps)

---

## Phase 1 — Start immediately, no architecture needed

Three tasks on the existing prototype (`maps_of_making-handoff.zip`):

1. **Protomaps spike** — swap OSM/Carto raster tiles → PMTiles in `Maps-of-Making.html` + `app.js`. 3-line MapLibre protocol registration + extract FR+DE regional PMTiles file. Fixes 403 referer block. ###DONE
2. **Pin drift fix** — comes for free with vector tile switch (raster tile anchoring issue disappears).  ###DONE
3. **UI polish** — clean up drawers, legend, filter panel against the PRD spec. Prototype is already close.
4. deploy on vps, test embed snippet

**How to start:** brief Amelia (dev agent) directly with the PRD + prototype as spec. No epics needed for Phase 1.

---

## Phase 2 — Architecture first, then epics

Sequence before writing Phase 2 code:

1. **`/bmad-agent-architect`** — Winston session: Docker Compose services, ingestion pipeline design, Oxigraph schema, SPARQL validation gateway, bot adapter interface, CID-based snapshot storage
2. **`/bmad-create-epics-and-stories`** — break PRD into epics + stories from the architecture
3. **`/bmad-sprint-planning`** — generates `sprint-status.yaml` once epics exist

---

## Key decisions to remember

- Map is pure reader — no editing records, append-only versioned snapshots
- JSON endpoints describe spaces, not people (no personal contacts in public data)
- All thresholds (fetch cadence, failure counts, retention) in config — set from real PoC telemetry
- Admin: shared password, Nicolas + Jason only (PoC-grade); harden at pilot
- IPFS/IPLD archival of anonymized snapshots: Phase 3 exploration


