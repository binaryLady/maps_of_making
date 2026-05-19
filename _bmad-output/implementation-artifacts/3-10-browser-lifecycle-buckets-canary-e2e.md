# Story 3.10: Browser Computes Three Axes Live — Canary Demo

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

> **Epic 3.5 done-condition story.** This is the final story of Epic 3.5. When it closes, the
> freshness propagation contract is demonstrably live: a stale endpoint visibly renders stale,
> a fresh one renders confirmed — proven on the operator-controlled Mother Sands canary, not a
> mock. This story also performs the **dead-code sweep**: every stored bucket/status field that
> the browser now computes live is deleted from the pipeline (operator request 2026-05-19 —
> "clean and lean, too much left-over").

## Story

As an operator demonstrating the Maps of Making freshness model,
I want `web/app.js` to compute all three freshness axes live in the browser from the three raw
tokens and the `thresholds` block in the GeoJSON header — and the pipeline to carry **only** the
raw tokens, no pre-computed buckets,
so that the lifecycle a space shows on the map is always `f(token, now, thresholds)` evaluated
at view time, never a stale stored verdict, and the codebase no longer carries dead
bucket-computation paths.

## Acceptance Criteria

1. **Axis A — endpoint health, computed live.** `web/app.js` derives endpoint health from
   `observed_at` + `last_fetch_status` + `thresholds.endpoint_health`:
   - `last_fetch_status === "unreachable"` (or no snapshot) → `broken`
   - else `age = now − observed_at` in minutes, bucketed by
     `unresponsive_minutes_threshold` / `warning_minutes_threshold` /
     `broken_minutes_threshold`.
   - `observed_at` null → treated as never-observed → `broken`/unknown (see Dev Notes).

2. **Axis B — content lifecycle, computed live.** `web/app.js` derives the content bucket
   (`confirmed` / `aging` / `zombie` / `dead`) from `updated_at` + `thresholds.operational_state`:
   `age = now − updated_at` in days, bucketed by `aging_days_threshold` /
   `zombie_days_threshold` / `dead_days_threshold`. `updated_at` null → treated as "content
   never observed to change", the oldest Axis B state the data supports (see Dev Notes — do NOT
   crash, do NOT silently render `confirmed`).

3. **Axis C — operational liveness, computed live.** `web/app.js` derives liveness from
   `open_now` + `last_open_change`: `open_now === true` → `open`; otherwise not-open. Axis C
   does not age — it is a current source claim.

4. **`effective_marker` computed live from the three axes.** A new function (e.g.
   `computeMarker(s)`) replaces the stored `status` field as the input to `markerKind()`. The
   marker precedence is the existing one: broken (Axis A) → dead/zombie/aging (Axis B) → open
   (Axis C) → confirmed → seeded. `markerKind()` reads the live-computed value, not
   `s.status`.

5. **`freshnessText()` rewired.** `freshnessText(s)` displays the three-axis state computed in
   ACs 1–4, using the live tokens. It no longer reads `s.status`, `s.last_updated`, or
   `s.last_fetched` (those fields are removed — see AC 8). `timeAgo()` is unchanged.

6. **Thresholds read from the GeoJSON header.** All numeric thresholds come from the
   `thresholds` block shipped in `spaces.geojson` (Story 3.9). No threshold value is hardcoded
   in `web/app.js`. If the `thresholds` block is absent or empty, the browser logs a clear
   console error and falls back to a single explicit default constant (defined once, named,
   commented as a fallback) — it must not silently render everything `confirmed`.

7. **Dead-code sweep — pipeline carries only raw tokens.** Remove the now-dead pre-computed
   bucket fields and their computation paths. After Story 3.9, the SPARQL SELECT no longer
   reads `operationalState`/`endpointHealth`, so `_binding_to_feature` computes
   `resolved_status` from `.get()` defaults only — pure dead code. Concretely:
   - `infra/link_handler/main.py`: delete the `effective_marker(...)` call and the
     `resolved_status` variable in `_binding_to_feature`; remove `status`,
     `endpoint_health`, `operational_state` from the emitted feature `properties`.
   - `scripts/materialize_geojson.py`: `binding_to_space` hardcodes `status: "unknown"` —
     remove that key; remove any matching `endpoint_health`/`operational_state` keys.
   - If `effective_marker()` in `main.py` has no remaining caller after this, delete the
     function. If it is reused elsewhere, leave it and note the caller.
   - Both materializers emit byte-identical feature property sets (the "kept in sync
     intentionally" contract from Story 3.9 still holds).

8. **`web/app.js` stops reading removed fields.** Every read of `s.status`, `s.last_updated`,
   `s.last_fetched`, `s.endpoint_health`, `s.operational_state` is replaced with the
   live-computed axis value or removed. Audit and update: `markerKind`, `filteredSpaces`
   (`HEALTH_STATUSES` check), `renderDetail` status bar / status sections, the refresh-button
   handler, chip filtering (`#chips-status`). No dead reference to a removed field remains.

9. **Gating test `tests/test_canary_three_axis_e2e.py` passes** (`@pytest.mark.live_integration`,
    full stack, operator-controlled Mother Sands canary):
    - Compress `thresholds` to seconds-scale values so axes move within the test.
    - Make the canary unreachable (`MODE=503` / `MODE=timeout`) → assert Axis A degrades to
      `broken` while Axis B is unaffected.
    - Leave canary content unchanged across responsive fetches → assert Axis B ages
      independently of Axis A.
    - Flip `open_now` → assert Axis C updates independently of A and B.
    - Assert the three axes are computed from tokens + header thresholds, not stored buckets.

10. **Full pytest suite remains green.** No regressions.

11. **Operator visual confirmation — this IS the epic done-condition.** Demonstrated live to
    Nicolas: load the map; the canary, driven through unreachable / stale-content / closed
    states, visibly renders the correct marker and freshness text for each axis, computed in
    the browser. A green pytest exit code alone is **not** done (Epic 3.5 test gate rule 2).

## Tasks / Subtasks

- [ ] Task 1 — Verify the GeoJSON contract from Story 3.9 (AC: 1, 2, 3, 6)
  - [ ] Run a materialization, confirm `spaces.geojson` features carry `observed_at`,
        `updated_at`, `last_open_change`, `open_now`, `last_fetch_status`
  - [ ] Confirm file-level `thresholds.endpoint_health` and `thresholds.operational_state`
        are present and non-empty (keys match `config.yaml`:
        `*_minutes_threshold`, `*_days_threshold`)
  - [ ] Note: if `thresholds` ships empty, that is the Story 3.9 deferred
        `_load_thresholds_from_config` swallow-all bug — fix it here (see Dev Notes), since
        AC 6 depends on a non-empty block

- [ ] Task 2 — Add live axis-computation functions to `web/app.js` (AC: 1, 2, 3)
  - [ ] `computeAxisA(s, thresholds)` → endpoint health bucket
  - [ ] `computeAxisB(s, thresholds)` → content lifecycle bucket
  - [ ] `computeAxisC(s)` → operational liveness
  - [ ] Store the parsed `thresholds` block on `state` at load time (`loadData`)
  - [ ] Handle null `observed_at` / null `updated_at` per Dev Notes (no crash, no
        silent-confirmed)

- [ ] Task 3 — Rewire `computeMarker` / `markerKind` / `freshnessText` (AC: 4, 5)
  - [ ] Add `computeMarker(s)` combining the three axes with existing precedence
  - [ ] `markerKind()` reads `computeMarker(s)` instead of `s.status`
  - [ ] Rewrite `freshnessText(s)` to use live axes and live tokens; keep `timeAgo()` as-is
  - [ ] Update `aria-label` / status-label rendering that depended on `s.status`

- [ ] Task 4 — Audit and replace all removed-field reads in `web/app.js` (AC: 8)
  - [ ] `filteredSpaces` `HEALTH_STATUSES` check → use `computeMarker`/Axis B
  - [ ] `renderDetail` status bar (`s.last_updated`, dot class) and status sections
        (`s.status === 'aging'|'zombie'|'dead'|'broken'|'seeded'`)
  - [ ] Refresh-button handler block (`lastFetched`, re-fetch `.map()` of features)
  - [ ] `#chips-status` filtering path
  - [ ] grep the whole file for `\.status`, `\.last_updated`, `\.last_fetched`,
        `\.endpoint_health`, `\.operational_state` — zero stale reads remain

- [ ] Task 5 — Dead-code sweep in the materializers (AC: 7)
  - [ ] `infra/link_handler/main.py`: remove `resolved_status`/`effective_marker` call in
        `_binding_to_feature`; drop `status`/`endpoint_health`/`operational_state` from
        emitted properties
  - [ ] Delete `effective_marker()` if no caller remains; otherwise document the caller
  - [ ] `scripts/materialize_geojson.py`: `binding_to_space` — drop hardcoded
        `status: "unknown"` and any `endpoint_health`/`operational_state` keys
  - [ ] Diff the two emitted property sets — confirm byte-identical key sets
  - [ ] grep both files for any other now-orphaned helper (imports, constants) and remove

- [ ] Task 6 — Write gating test `tests/test_canary_three_axis_e2e.py` (AC: 9)
  - [ ] `@pytest.mark.live_integration` — live Oxigraph, real snapshot store, real canary
        fixture HTTP server, seconds-scale thresholds
  - [ ] Axis A degradation under `MODE=503`/`timeout`
  - [ ] Axis B independent aging with unchanged content
  - [ ] Axis C flip on `open_now` change
  - [ ] Assert axes computed from tokens + header thresholds, not stored buckets

- [ ] Task 7 — Regression + operator confirmation (AC: 10, 11)
  - [ ] `python -m pytest tests/ -v` — full suite green, no new failures
  - [ ] Run the stack, drive the canary through all three axes, confirm marker + freshness
        text visually with Nicolas

## Dev Notes

### This story closes Epic 3.5

Story 3.10 is the epic done-condition. The acceptance test (AC 10 + AC 12) must flip the epic
done-condition from false to true, demonstrably and live:

> An operator loads the map; a space whose endpoint has stopped updating past the staleness
> threshold visibly renders as **stale** (aging/zombie/dead), and a space still fetching fresh
> renders **confirmed** — demonstrated live against the operator-controlled Mother Sands
> canary, not a mock.

Epic 3.5 test gate (both required, non-negotiable): (1) **real seams only** — no mocked
integration seams count; (2) **operator visual confirmation** — a green pytest exit code alone
is not done.

### The three-token model — what the browser receives

| Token | Feature property | Source store | Axis | Meaning |
|---|---|---|---|---|
| `observed_at` (ISO-8601) | `properties.observed_at` | SQLite `snapshot_store.db` | **A** | last responsive fetch (200/304) |
| `last_fetch_status` (string) | `properties.last_fetch_status` | SQLite snapshot row | **A** | `ok` / `not_modified` / `unreachable` |
| `updated_at` (ISO-8601) | `properties.updated_at` | Oxigraph `mom:updatedAt` | **B** | last real content diff |
| `last_open_change` (Unix s) | `properties.last_open_change` | Oxigraph `mom:lastOpenChange` | **C** | source flipped open/closed |
| `open_now` (bool) | `properties.open_now` | Oxigraph `mom:openNow` | **C** | current source claim |

`generated_at` (file-level) is the materialization stamp — NOT a freshness token. Do not use it
for age math.

**Storage holds facts, never derived buckets** (Epic 3.5 contract). After this story the
pipeline carries the five raw tokens above and nothing pre-computed. `operationalState` /
`endpointHealth` / `status` are `f(token, now, thresholds)` evaluated in the browser at view
time. This is the whole point of the epic — that is why AC 7 deletes them.

### Null-token handling (critical — do not get this wrong)

- **`observed_at` null** — space has no snapshot row (seeded / pre-3.7). Axis A cannot be
  computed → treat as `broken`/unknown endpoint health. Do NOT render `confirmed`.
- **`updated_at` null** — space seeded before Story 3.8b; no `mom:updatedAt` triple. Treat as
  "content never observed to change" — the **oldest** Axis B state the data supports. Do NOT
  crash and do NOT silently render `confirmed`. (Story 3.9 Dev Notes flagged this explicitly as
  the thing Story 3.10 must handle.)
- **`last_open_change` null** — Axis C has no flip history → `open_now` alone drives Axis C.

The failure mode this epic exists to kill is "a stale payload looks fresh because the stage
that last touched it ran recently". A null token rendering as `confirmed` re-introduces exactly
that bug. Fail visible, not silent.

### Thresholds — config keys (note the suffix)

`config.yaml` and therefore the GeoJSON `thresholds` block use these exact keys:

```yaml
endpoint_health:
  unresponsive_minutes_threshold: 10
  warning_minutes_threshold: 30
  broken_minutes_threshold: 60
operational_state:
  aging_days_threshold: 30
  zombie_days_threshold: 90
  dead_days_threshold: 180
```

Read them from `spaces.geojson` `thresholds.endpoint_health.*` and
`thresholds.operational_state.*`. Do not hardcode the numbers in `web/app.js`. The single
fallback constant (AC 6) is only for the missing-block error path.

### Fix the Story 3.9 deferred robustness bug while you are here

`_load_thresholds_from_config` (`main.py` and `scripts/materialize_geojson.py`) catches every
exception and ships an **empty** `thresholds` block with only a logged warning — deferred from
the Story 3.9 review as "minor robustness". Story 3.10 depends on a non-empty block (AC 6), so
fix it now: on a malformed/missing `config.yaml` the materializer should fail loud (non-zero
exit for the batch script; clear ERROR log for the async path) rather than ship a GeoJSON the
browser cannot compute against. This converts a silent downstream breakage into an immediate,
locatable failure — consistent with the `THREE_TOKENS_MISSING` fail-loud contract.

### Existing marker / freshness code being modified — READ BEFORE CHANGING

`web/app.js` (1403 lines). Current state of the code this story rewires:

- `loadData()` (L52–85) — fetches `/data/spaces.geojson`, flattens `f.properties` +
  `geometry.coordinates` into `state.spaces`. **Add:** parse and store the file-level
  `thresholds` block here.
- `markerKind(s)` (L248–258) — currently a ladder on `s.status` / `s.open_now`. **Rewire** to
  read the live-computed marker.
- `createMarkerSVG` / `MARKER_GLYPH` (L192–213) — glyphs for `broken/aging/zombie/dead`. The
  glyph set does not change; only the input does.
- `filteredSpaces()` (L281–300) — `HEALTH_STATUSES = {'aging','zombie','dead'}` checked
  against `s.status`. **Rewire** to the live Axis B bucket.
- `renderDetail` (L486–620 region) — status bar reads `s.last_updated`; status sections branch
  on `s.status === 'aging'|'zombie'|'dead'|'broken'|'seeded'`; reads `s.last_fetched`.
  **Rewire** all of these.
- `freshnessText(s)` (L772–793) — branches on `s.status`, reads `s.last_updated` /
  `s.last_fetched`. **Rewrite** per AC 5.
- `timeAgo(iso)` (L795–804) — appends `Z` if missing, returns `Ns/Nm/Nh/Nd`. **Unchanged** —
  reuse it for the live token ages.
- Refresh-button handler (L716–745 region) — reads `lastFetched`; re-fetches
  `spaces.geojson?t=...` and re-maps features. The re-map must produce the same flattened
  shape as `loadData` (incl. `thresholds`).
- `#chips-status` (L319, L324, L361) — `statuses = ['seeded','confirmed','open','unlinked','broken']`,
  filtered via `markerKind(s) === val`. Since `markerKind` now reads live values this keeps
  working; verify it does.

Whatever this story does, the map must still render every space correctly end-to-end — not
just the canary. Registered + seeded spaces that lack tokens must render sensibly per the
null-token rules.

### Two materializers stay in sync

`scripts/materialize_geojson.py` (standalone batch) and `_rematerialize_geojson()` in
`main.py` (in-process async) must emit byte-identical feature property sets. The
"kept in sync intentionally" comment near `main.py` `_SPARQL_SELECT` stays. The dead-code
sweep (AC 7) must touch both or it breaks the contract.

### Canary control surface for the e2e test

`data/canary/mother-sands-endpoint.py` — `MODE` env var injects HTTP behaviour:
`ok` (default, 200 + JSON), `timeout` (accept, never reply), `404`, `503`. `PORT` defaults to
`9191`. Drive Axis A by switching `MODE`. Drive Axis B by keeping `MODE=ok` with unchanged
content across fetches (no diff → `updated_at` does not advance → age grows). Drive Axis C by
editing the served file's `state.open` / `state.lastchange`. Compress the `thresholds` block to
seconds for the test so axes move within a test run.

Existing canary tests for reference: `tests/test_canary_scenarios.py`,
`tests/test_materializer_three_tokens.py`, `tests/test_transformer_three_token.py`.

### Scope guard (Epic 3.5)

Do NOT pull in: retry logic, lifecycle *policy* changes, per-stage gatekeeping, ontology work,
a real notification channel (email/webhook), GeoJSON payload-slimming of card-detail fields
(that is the separate Epic 5+ `spaces.geojson` payload-slimming item — this story removes only
the *dead computed-bucket* fields, not card-detail fields). This story re-architects the
freshness *consumption* end and removes the dead bucket-computation code. Nothing else.

### Project Structure

- `web/app.js` — `loadData`, `markerKind`, `createMarkerSVG`, `filteredSpaces`, `renderDetail`,
  `freshnessText`, refresh-button handler, `#chips-status` path; new axis-compute functions
- `infra/link_handler/main.py` — `_binding_to_feature` (remove `resolved_status` /
  `status` / `endpoint_health` / `operational_state`), `effective_marker` (delete if orphaned),
  `_load_thresholds_from_config` (fail-loud fix)
- `scripts/materialize_geojson.py` — `binding_to_space` (drop hardcoded `status`),
  `_load_thresholds_from_config` (fail-loud fix)
- `tests/test_canary_three_axis_e2e.py` — new gating test
- `data/canary/mother-sands-endpoint.py` — canary control surface (no change, used by test)
- `infra/link_handler/config.yaml` — threshold source (no change)

### Running the Stack

```bash
distrobox-host-exec podman compose -f infra/docker-compose.yml -f infra/docker-compose.dev.yml up -d
source venv/bin/activate
python -m pytest tests/ -v
python -m pytest tests/test_canary_three_axis_e2e.py -v -m live_integration
# verify the browser receives only raw tokens (no stored buckets)
python scripts/materialize_geojson.py
python -c "
import json
d = json.load(open('web/data/spaces.geojson'))
print('thresholds:', d.get('thresholds'))
p = d['features'][0]['properties']
for dead in ('status','endpoint_health','operational_state'):
    assert dead not in p, f'dead field still present: {dead}'
print('raw tokens:', {k: p.get(k) for k in ('observed_at','updated_at','last_open_change','open_now','last_fetch_status')})
print('OK — no stored buckets')
"
```

### References

- Three-token model + Epic 3.5 done-condition: `_bmad-output/planning-artifacts/epics.md`
  (Epic 3.5 section; Story 3.10 at L1162)
- Story 3.9 (predecessor — materializer carries the three tokens + thresholds):
  `_bmad-output/implementation-artifacts/3-9-materializer-three-tokens-geojson.md`
- Story 3.8b (corrected token model): `_bmad-output/implementation-artifacts/3-8b-corrected-token-model.md`
- Sprint change proposals: `_bmad-output/planning-artifacts/sprint-change-proposal-2026-05-19.md`
  and `-19b.md`
- Deferred work folded into this story (`_bmad-output/implementation-artifacts/deferred-work.md`):
  - *story-3.9 review* — "Dead `effective_marker`/`resolved_status` computation + `status`
    divergence between materializers" — explicitly scope-guarded to "Story 3.10
    field-slimming". → **AC 7, Task 5.**
  - *story-3.9 review* — "`_load_thresholds_from_config` swallows all exceptions and ships
    empty `thresholds` block silently". → **fixed here (Task 1 / Dev Notes)** because AC 6
    depends on a non-empty block.
  - *story-3.9 review* — "Materializer test fragility (`test_observed_at_from_sqlite_not_oxigraph`
    never asserts the negative; subprocess vs in-process import contexts)". → the new e2e test
    (AC 10) must assert axes are computed from tokens, not stored buckets — i.e. assert the
    negative. Existing test cleanup itself stays deferred (test-design only).

### Deferred / NOT in this story (carried forward)

These remain in `deferred-work.md` — do not pull them in, but be aware:

- *Story 2.0* — "Legend does not show health map states" and "Status filter chips don't
  include health states" (`web/maps-of-making.html`, `buildFilterChips`). Story 3.10 rewires
  marker computation but does not add legend/chip entries for `aging`/`zombie`/`dead`.
  → Epic 5 UI polish. (If trivial once `computeMarker` exists, raise with operator — but
  default is defer.)
- *3.8b review* — "304 path `last_open_now` goes stale during 304 streaks". Server-side Axis C
  staleness; not a browser concern. → stays deferred.
- *Epic 3 retro* — `spaces.geojson` card-detail payload-slimming. → Epic 5+.
- *epics.md Story 3.10 AC* — coordinator notification on bucket transition (the original
  "human safety net" line). → **Epic 4b**, with the magic-link work (operator decision
  2026-05-19). Not implemented in this story in any form.

## Resolved Decisions

1. **Coordinator notification on bucket transition — deferred to Epic 4b.** The original epic
   AC for Story 3.10 included "coordinator notification fires on bucket transition
   (aging→zombie→dead) — human safety net". Operator decision (2026-05-19): the
   email/notification channel is **deferred to Epic 4b** alongside the magic-link work. Story
   3.10 does NOT implement any notification, banner, or `console.warn` transition signal — the
   live-computed marker glyph change (aging ⚠️ / zombie 🧟 / dead 🪦) is the only transition
   surfacing in this story.

2. **`status` field removal blast radius — accepted.** Removing `status` from the GeoJSON is
   correct per the three-token model. The orphaned Epic 4 draft
   `4-0-admin-foundation-subdomain-auth-space-comparison.md` and any external GeoJSON consumer
   lose the stored field; Epic 4 is backlog and depends on Epic 3.5 output, so Epic 4 kickoff
   must expect live-computed status. Accepted by operator (2026-05-19).

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
