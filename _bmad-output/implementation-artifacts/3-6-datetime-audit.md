# Story 3.6 — `datetime.now()` Carry/Generate Audit

Audit of every `datetime.now()` / `utcnow()` call in the three legacy-path files.
Verified against commit `ebd3000` (Epic 3.5 correct-course re-arch).

---

## `infra/link_handler/transformer.py`

| Line | Variable / context | Payload fed | Persisted? | Verdict | Owner story |
|------|-------------------|-------------|------------|---------|-------------|
| 68 | `now` in `_log_unmapped_tags` | Gap-log file timestamp `{now}\tUNMAPPED_TAG\t{tag}` | Append-only log file | **GENERATE** — diagnostics only, not a data-model stamp | — (keep as-is) |
| 179 | `now` in `_build_pii_strip_sparql` | `mak:closedAt` triple | Oxigraph | **GENERATE** — closure event time is always "now"; no upstream token to carry | — (keep as-is) |
| 402 | `now` in `transform_to_sparql` | `mom:lastFetched`, `mom:lastUpdated` triples (200 path) | Oxigraph space graph | **CARRY** → replace with `observed_at` from snapshot store | Story 3.8 |
| 403 | `snapshot_date` in `transform_to_sparql` | Named-graph URI suffix `urn:mak:space/{slug}/{date}` | Graph URI only | **GENERATE** — structural graph naming, not a propagated token | Story 3.8 (delete when legacy path removed) |
| 521 | `now` in `snapshot_triples` (`mom:snapshotDate`) | `mom:snapshotDate` triple in snapshot graph | Oxigraph snapshot graph | **CARRY** → this is a stale re-stamp; clean model derives from `observed_at` | Story 3.8 |
| 624 | `now` in `update_last_content_updated` | `last_content_updated` column in `heartbeat_log.db` | SQLite | **GENERATE** in legacy path; clean path mints `observed_at` separately in Task 3 (this story) | Story 3.8 (delete on migration) |
| 670 | `now` in `fetch_endpoint_conditional` | `last_fetched` column in `heartbeat_log.db` (200/304/error rows) | SQLite | **GENERATE** — fetch-time record for ETag / bandwidth logic; feeds no `observedAt`-adjacent triple | Story 3.7 (clean path replaces this row) |
| 747 | `datetime.now` in `_days_since` | Transient age math feeding `endpoint_health` / `lifecycle_state` | Transient (not persisted) | **GENERATE — TRANSITIONAL** — remove in Story 3.10 (age-math moves to browser) | Story 3.10 |
| 759 | `datetime.now` in `_minutes_since` | Transient age math feeding endpoint health classification | Transient (not persisted) | **GENERATE — TRANSITIONAL** — remove in Story 3.10 | Story 3.10 |
| 808 | `_now_304` in `process_one_space` 304-path | `mom:lastFetched` triple via `build_state_only_update` | Oxigraph | **CARRY** → replace with `observed_at` snapshot token | Story 3.7 |

---

## `infra/link_handler/main.py`

| Line | Variable / context | Payload fed | Persisted? | Verdict | Owner story |
|------|-------------------|-------------|------------|---------|-------------|
| 39 | `_last_heartbeat_completed = datetime.now(...)` in `_heartbeat_job` | In-memory scheduler bookkeeping; returned by `/api/heartbeat/last-run` | In-memory only | **GENERATE** — scheduler telemetry, not a propagated token | — (keep as-is) |
| 478 | `now` in `_build_sparql_update` (legacy fallback builder) | `mom:lastFetched`, `mom:lastUpdated` triples | Oxigraph | **CARRY** → legacy builder deleted wholesale when all spaces migrated | Story 3.8 |
| 668 | `_last_heartbeat_completed = datetime.now(...)` in `heartbeat_run` | Same as L39 | In-memory only | **GENERATE** — same scheduler telemetry | — (keep as-is) |
| 687 | `now` in `heartbeat_space` cooldown logic | `_manual_refresh_cooldowns[space_id]` (in-memory dict) | In-memory only | **GENERATE** — rate-limit guard, not a data-model stamp | — (keep as-is) |
| 795 | `snapshot_date` in `register_url` | Named-graph URI `urn:mak:space/{slug}/{snapshot_date}` | Graph URI only | **GENERATE** — structural naming, same pattern as transformer.py L403 | Story 3.8 (legacy builder deletion) |

---

## `scripts/materialize_geojson.py`

No `datetime.now()` or `utcnow()` calls found. File-level `generated_at` field is
introduced later (Story 3.9), not present here.

---

## Summary

| Verdict | Count | Notes |
|---------|-------|-------|
| **GENERATE** (keep forever) | 7 | Diagnostics, structural naming, scheduler telemetry, rate-limit guard, closure event |
| **CARRY** (replace with `observed_at`) | 4 | Legacy path stamps that the clean pipeline eliminates |
| **GENERATE — TRANSITIONAL** (delete in 3.10) | 2 | Age-math helpers; replaced by browser-side `now − observed_at` |

Stories to act on carry/transitional calls:

- **Story 3.7** — `transformer.py:670` (heartbeat_log `last_fetched`), `transformer.py:808` (`_now_304` → `mom:lastFetched`)
- **Story 3.8** — `transformer.py:402/521/624`, `main.py:478/795` (all legacy-path stamps)
- **Story 3.10** — `transformer.py:747/759` (`_days_since` / `_minutes_since`)
