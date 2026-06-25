# Story 6.5: Graceful Failure + Bernard Voice Pass

Status: SUPERSEDED — course-corrected 2026-06-25 (see banner below)

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

> ## ⚠️ COURSE CORRECTION — 2026-06-25 (read before touching this story)
>
> **This story as written below is on hold and largely dissolves.** A scope reckoning
> with Nicolas concluded that 6.5's voice-pass approach is busywork that the *right
> architecture makes disappear*. Do **not** start the 9 voice tasks or the 19-row
> string-table audit as the primary work.
>
> ### What changed
>
> The headline reframe (Nicolas, in priority order):
> 1. 🟢 **PRIMARY — "ask stuff about the map"** (NL→SPARQL read). Wired in 6.4, works.
> 2. 🟡 **SECONDARY — "coordinator edits JSON conversationally, `!mom` as fallback."**
>    This is the real differentiator. *Without it, `@bernard` adds little over `!mom`.*
> 3. ⚪ **TERTIARY — full conversational onboarding.** Stays Epic 9 / later.
>
> 6.4 is "successfully wired but still useless — it only poorly falls back to `!mom`."
> 6.5 must drive the **write** capability home. Voice fine-tuning comes *after* the
> valued feature exists, not before.
>
> ### The YAGNI reckoning (the deeper finding)
>
> Crossing the plan with YAGNI exposed an architectural contradiction:
>
> - **Hand-authored copy + an LLM is self-defeating.** If Bernard has an LLM, his persona
>   and graceful-failure prose are supposed to come from the **system prompt**, not a
>   19-key `bernard_voice.yaml` string table. A regex+string-table bot doesn't need an LLM;
>   an LLM bot doesn't need a hand-compiled string table. 6.5-as-written hand-compiles, by
>   hand, the thing the model generates for free. → see [[feedback_llm_bot_no_canned_copy_table]]
> - **A "capability/help intent" was never needed** — "what fields exist?" is already
>   `!mom read`. Scratched.
> - We hand-rolled the **agent orchestration layer** (regex intent classifier, per-intent
>   handlers, voice string table, and a planned bespoke "delta-compute → confirm → execute"
>   state machine). All of that is what a **tool-calling agent gives out of the box** — the
>   exact thing nanobot/hermes (planned Epic 6, [[feedback_no_cut_planned_epic6]]) or even
>   the `openai` SDK's native function-calling would have provided.
>
> **Honest split of the "build our own simple harness" call:**
> - ✅ *Kept its value — the EFFECTS layer.* The deterministic `!mom` verbs (permission
>   gating, `git_ops.commit_json`, schema validation, read-only/injection guarantees,
>   SPARQL read) are real product you'd want under any framework. **These become Bernard's
>   tools.** Not wasted.
> - ❌ *Missed the value — the ORCHESTRATION layer.* Treating the LLM as one bolt-on route
>   (`nl_to_sparql`) beside a deterministic router means every conversational feature fights
>   the router instead of being a tool the model can call.
>
> ### The reframe — Bernard as a tool-calling loop
>
> Cheap because it **deletes more than it adds** (the tell that it's right):
> - `!mom` effect functions → **tools** (`read_space`, `update_field`, `query_map`,
>   `log_gap`). Reuse the existing tested functions; wrap as function definitions.
>   `openai` SDK function-calling (already a dependency, OpenRouter) likely covers ~80%
>   without adopting a framework yet.
> - Bernard persona + voice rules + "**confirm before any write**" → ~20 lines of **system
>   prompt**, replacing the bulk of `bernard_voice.yaml` and the voice-audit tasks.
> - **memberOf delta** (the canonical hard case: `!mom update memberOf` needs the *full*
>   rewritten array): the model reads current value via `read_space`, computes the new array
>   from a relative instruction ("add VOW" / "fix typo fabtafle→fabtafel"), **echoes the
>   resolved entities + resulting command, asks confirmation, then calls `update_field`.**
>   No per-field handler, no canned confirmation state machine.
> - **Emergence** (unanswerable question / unfulfillable write / feature request) → model
>   honestly says "I can't yet" and calls `log_gap`. This is a *generalization* of the
>   existing `mom:OntologyGap` mechanism (`nl_to_sparql.py` `_emit_gap_triple` → `urn:mak:gaps`)
>   from "SPARQL gap" to "anything Bernard couldn't do." Already mostly built.
> - Router + intent_classifier + most of `bernard_voice.yaml` → **mostly deleted.**
>
> ### Next step (reversible — decide nothing irreversible while tired)
>
> **Spike, don't commit a framework:** build Bernard as a tool-calling loop over the
> existing `!mom` effect functions (`read_space`, `update_field` with confirm-before-write,
> `query_map`, `log_gap`), persona in the system prompt. The spike answers whether the
> `openai` SDK's native function-calling is sufficient or whether **nanobot/hermes** earns
> its keep (session/observability niceties on top) — *before* committing to either.
>
> Tar-pits surfaced and explicitly deferred (not 6.5): **schema authoring** ("help me set up
> repaircafe's extended fields" = bundle/wormhole epic, [[project_schema_bundle_model]]) and
> **tool-reasoning** ("what time is it in Taipei, should I contact them now?" = needs a
> tz/clock tool layer). Both should hit the emergence log honestly — which itself proves the
> capture loop works.
>
> When this reframe is accepted, this file should be re-cut as **"Story 6.5: Bernard as a
> tool-calling agent"** with the graceful-failure ACs riding along *for free* from the system
> prompt, and the effects layer carried forward unchanged. The original voice-pass story
> body is retained below for reference / salvage.
>
> ---

## Story

As a user hitting any failure path,
I want Bernard to tell me what he knows, why something is unavailable, and the exact way forward,
so that error states build trust instead of dead-ending.

## Acceptance Criteria

> The Bernard voice rules **are** the acceptance criteria. Source of truth:
> `_bmad-output/planning-artifacts/mom_handoff_2026-06-16.md` §"Bernard voice rules" (lines 319–356),
> mirrored in `epics.md:1810-1827` and `architecture.md:513`.

1. **Bernard never emits** any of the following in a user-facing string:
   HTTP status codes; exception/class names (`ConnectionError`, `NoneType`, `HTTPError`, `InvalidToken`, …);
   the literals `null`/`undefined`/`None`; `"I don't have permission to do that"`;
   `"Your query returned no results"`; or `"I cannot help with that"` **without** also offering what he *can* do.

2. **Bernard always**, on every failure path:
   - states **what he knows first**, then **what he can't reach** (e.g. "Mother Sands is confirmed — last seen 4h ago. Your endpoint timed out just now; I'll try again next cycle.");
   - explains **why write is unavailable** with the **exact path forward** — a deploy-key setup link (Story 9.8 GitLab tutorial surface);
   - for **zero results**, offers the **seeded fallback** ("3 seeded spaces fall in range — want me to list them anyway?");
   - for **permission refusal**, points to `!mom grant` (never a bare "denied");
   - for **LLM unavailability**, distinguishes it from data absence and offers **template queries** while it recovers.

3. **Commit messages are in Bernard's voice** — the open/close shorthand produces `Mark {space} open · authorized by {mxid}` / `Mark {space} closed · authorized by {mxid}`, not the generic `Update state.open …`. Field updates keep the `Update {field} for {space} · authorized by {mxid}` form.

4. **Every failure path identified across Stories 6.0–6.4 is covered** by a voice-audited response (the inventory in Dev Notes §"Failure-path inventory" is the checklist; each row ends at a voice-compliant string).

5. **No regression**: all existing happy-path acks and the 65+ existing harness tests still pass; the read-only Oxigraph guarantee (NFR-S7) and SPARQL-injection rejection (NFR-S5) are untouched; copy changes live **only** in `harness/bernard_voice.yaml` (SSOT — see [[feedback_bernard_voice_yaml_is_ssot]] / [[feedback_no_triple_source_of_truth]]), not hardcoded in `bernard.py`.

**Done gate (operator confirmation):** a live walk of each failure path on the VPS Matrix room — **no deploy key**, **no grant** (ungranted member), **ORS timeout**, **LLM down** (unset/blocked `OPENROUTER_API_KEY`), **empty results** (find/nearby/network/NL) — each returns a voice-compliant Bernard response with a concrete next step. None leak a status code, exception name, or dead-end.

## Tasks / Subtasks

- [ ] **Task 1 — Build the failure-path inventory & audit harness** (AC: #4)
  - [ ] Confirm/extend the inventory table in Dev Notes by grepping `harness/` for every `*_ack`, `except`, and `raise` emission point. Each row = (trigger → current string → required voice fix).
  - [ ] Add a unit test `harness/tests/test_voice_audit.py` that asserts **no** value in `bernard_voice.yaml` matches the forbidden-token regex (`\b(404|500|None|null|undefined|ConnectionError|HTTPError|NoneType|InvalidToken|Traceback)\b`, plus the three forbidden phrases). This test is the durable guardrail for AC#1.

- [ ] **Task 2 — Permission refusal points to `!mom grant`** (AC: #1, #2)
  - [ ] Rewrite `read_only_ack` in `bernard_voice.yaml` to keep the HAL register *and* name the path forward: which field is coordinator-only and `!mom grant @you {field}`. Keep the `{user}` substitution (see [[feedback_read_only_ack_user]]).
  - [ ] Verify `field_not_allowed_ack` lists the editable fields (already does) and reads as an offer, not a wall.

- [ ] **Task 3 — Write unavailable → deploy-key path forward** (AC: #2)
  - [ ] `no_deploy_key_ack`: state read works, write doesn't yet, and give the one-time `!mom link` + tutorial link (Story 9.8 surface URL). Confirm the link target with operator if the 9.8 public URL isn't final.

- [ ] **Task 4 — De-collapse `update_failed_ack`** (AC: #1, #2, #4) — *resolves deferred items from 6.1/6.2 code review*
  - [ ] In `harness/commands.py` `_handle_update` / `_handle_open_close`, split the single `except Exception → update_failed_ack()` into distinct voice keys per cause: endpoint not derivable (`NoEndpointError`/`UnsupportedHostError`), schema-validation rejection (`ValidationError`), git/SSH push failure, and **misconfiguration** (`fernet.InvalidToken` / missing `BOT_KEY_SECRET`). Each names what Bernard knows + the next step; the raw cause stays in the structured log only.
  - [ ] Add the new keys to `bernard_voice.yaml`. Misconfig path must read as "setup issue on my side — operator's been notified", never "update failed".

- [ ] **Task 5 — Query / directory unavailability vs data absence** (AC: #1, #2)
  - [ ] Split `query_failed_ack` (Oxigraph/directory unreachable) from the empty-result acks. The empty acks (`find_empty`, `nearby_empty`, `network_empty`, `find_open_empty`) must carry the seeded fallback offer; confirm `network_empty` gets a `seeded_note` (it currently has none — deferred 6.3 item).
  - [ ] **LLM-down path**: when `llm_client` raises (unset key, 5xx, timeout) inside the `nl_discovery` route, return a *distinct* "thinking part of my brain is busy — template queries still work: `!mom find`, `!mom nearby`" ack, separate from `nl_empty_ack`/`nl_gap_ack`. Add `nl_llm_unavailable_ack`.

- [ ] **Task 6 — Bernard-voice commit messages** (AC: #3)
  - [ ] In `infra/bot/git_ops.py:commit_json` (or at the `_handle_open_close` call site that builds the message), special-case `state.open` → `Mark {space_name} open/closed · authorized by {authorized_by}`. Keep generic `Update {field_path} for {space_name} · authorized by {authorized_by}` for all other fields. Add/adjust a `git_ops` unit test asserting the open/close message wording.

- [ ] **Task 7 — Travel / isochrone graceful degradation copy** (AC: #2, #4)
  - [ ] Voice-audit `travel_timeout_ack` and `travel_ors_unavailable_ack`: confirm both lead with the bounding-box fallback result and never say "ORS" raw to a non-technical user (current copy says "ORS took too long" — rephrase to "the travel-time service is slow right now, here's a straight-line estimate instead").

- [ ] **Task 8 — NL discovery dead-ends** (AC: #1, #2) — FR40/FR41
  - [ ] Voice-audit `nl_empty_ack`, `nl_gap_ack`, `nl_invalid_sparql_ack`. Confirm each offers a concrete `!mom find`/`!mom nearby` alternative and that the `mom:OntologyGap` triple is still written (FR41 — `nl_to_sparql.py:92,142`). No rephrase may drop the gap-logging side effect.

- [ ] **Task 9 — Live failure-path walk on VPS** (Done gate)
  - [ ] Run the operator walk (no key / no grant / ORS timeout / LLM down / empty results across find+nearby+network+NL). Paste the real Bernard responses into the Completion Notes. This is the DoD gate — pytest green is necessary but not sufficient (see [[epic_3_retro_findings]] pytest-vs-live gates).

## Dev Notes

### SCOPE BOUNDARY — read first

This is a **retroactive voice pass over paths that are already functional** (epics.md:1816: "do **not** pre-tune voice in 6.0–6.3 … polish here"). It is copy + error-routing work, **not** new feature work. Two adjacent things are explicitly **out of scope**:

1. **NL→write slot-filling.** `deferred-work.md` (top entry, 2026-06-24) documents that the `write` intent in `harness/router.py:25` is a stub (`# write: not implemented yet` → `unknown_ack`). That path is **not functional**, so 6.5 has nothing to polish there. The orphan needs its **own story that sequences *before* a full 6.5 sign-off**. **Decision for dev:** leave the `write`-intent branch returning `unknown_ack` for now, but DO voice-audit that `unknown_ack` string so an NL write attempt at least gets a graceful "I can't edit from a free-text sentence yet — use `!mom update {field} {value}` or `!mom open`/`!mom close`" instead of the generic shrug. Flag in Completion Notes that the slot-filling handler remains a separate story. See [[project_nl_write_orphan_stub]].
2. **Multi-platform identity hardening / Discord-Telegram acks** — that's Story 6.6, not here. Matrix-only (see [[feedback_read_only_ack_user]]).

### Voice rules (the AC, verbatim source)

`mom_handoff_2026-06-16.md:319-356`. Bernard register: dry, terse, no exclamation marks, observation over explanation, Ron-Swanson-on-a-fort (see [[project_bernard_character]]). The `read_only_ack` HAL-9000 line is an intentional, locked easter egg — keep its register, just add the grant path.

### Copy SSOT (hard constraint)

ALL string changes go in `harness/bernard_voice.yaml`. `bernard.py`'s `_bot()` helper already prefers the YAML value over the Python fallback default ([[feedback_bernard_voice_yaml_is_ssot]]). Do **not** create a second copy of any string in `bernard.py`, JS, or anywhere else ([[feedback_no_triple_source_of_truth]]). The Python-arg fallback strings in `bernard.py` may stay as last-resort defaults but must themselves be voice-compliant (the audit test in Task 1 only scans the YAML; manually confirm the `bernard.py` fallbacks too).

### Failure-path inventory (the AC#4 checklist — verified against current code)

| # | Trigger | Current emission | Location | Required fix |
|---|---------|------------------|----------|--------------|
| 1 | Ungranted member tries write | `read_only_ack` (HAL line, no path) | `commands.py` `_can_write` < 100 → `bernard.read_only_ack(user)` | Add `!mom grant @you {field}` path (Task 2) |
| 2 | No deploy key registered | `no_deploy_key_ack` | `commands.py:300,330,398,413` `NoDeployKeyError` | Add `!mom link` + 9.8 tutorial link (Task 3) |
| 3 | Update fails — endpoint not derivable | generic `update_failed_ack` | `commands.py:303,333` `NoEndpointError`/`UnsupportedHostError` | Distinct ack (Task 4) |
| 4 | Update fails — schema validation | generic `update_failed_ack` | `git_ops.commit_json` `SpaceAPISchema.model_validate` raises → `commands.py:306,336` `except Exception` | Distinct ack: "that value doesn't fit the space's profile shape" (Task 4) |
| 5 | Update fails — git/SSH push | generic `update_failed_ack` | `commands.py:306,336` `except Exception` | Distinct ack: "couldn't reach your repo to save it" (Task 4) |
| 6 | Update fails — `InvalidToken`/missing `BOT_KEY_SECRET` | generic `update_failed_ack` (looks identical to a network blip) | `commands.py:306,336` `except Exception` (deferred 6.1/6.2 finding) | Misconfig ack: "setup issue on my side — operator notified" (Task 4) |
| 7 | Field not in `ALLOWED_FIELDS` | `field_not_allowed_ack` (lists fields) | `commands.py` `_can_write` | Confirm reads as offer, not wall (Task 2) |
| 8 | Directory/Oxigraph unreachable | `query_failed_ack` | `commands.py:378,402,417` `except Exception` | Keep, but separate from empty-result (Task 5) |
| 9 | Zero results — find/nearby/open | `find_empty`/`nearby_empty`/`find_open_empty` (+seeded_note) | `query_commands.py` | Confirm seeded fallback present (Task 5) |
| 10 | Zero results — network | `network_empty` (**no seeded_note**) | `bernard_voice.yaml:52` | Add seeded fallback / "check exact name" (Task 5, deferred 6.3) |
| 11 | NL — empty result | `nl_empty_ack` (logs gap) | `nl_to_sparql.py` | Voice-audit, keep gap log (Task 8) |
| 12 | NL — no query formed | `nl_gap_ack` (logs `mom:OntologyGap`) | `nl_to_sparql.py:142` | Voice-audit, keep gap log FR41 (Task 8) |
| 13 | NL — forbidden SPARQL | `nl_invalid_sparql_ack` (logs security event NFR-S5) | `nl_to_sparql.py` `FORBIDDEN` regex | Voice-audit, keep rejection (Task 8) |
| 14 | NL — **LLM unavailable** (no key / 5xx / timeout) | currently falls into `except Exception` → `nl_gap_ack` (misreads LLM-down as a data gap) | `nl_to_sparql.py:173-174,190-191`; `llm_client.py:25,63` raises `ValueError` | **New** `nl_llm_unavailable_ack` distinguishing brain-busy from data-absent + template offer (Task 5) |
| 15 | Travel — ORS timeout | `travel_timeout_ack` ("ORS took too long") | `commands.py:464` | Rephrase, no raw "ORS" (Task 7) |
| 16 | Travel — ORS unavailable | `travel_ors_unavailable_ack` | `commands.py:453` `IsochroneError` | Voice-audit fallback wording (Task 7) |
| 17 | Open/close commit message | generic `Update state.open for …` | `git_ops.py:327` | `Mark {space} open/closed · authorized by …` (Task 6) |
| 18 | NL **write** attempt (free-text) | `unknown_ack` (stub — out of scope to *fix*, in scope to *voice*) | `router.py:25` | Voice-audit only; point to `!mom update`/`!mom open` (Scope note) |
| 19 | Unknown verb / typo | `unknown_command` / `did_you_mean` (fuzzy) | `bernard_voice.yaml:59-60` | Confirm voice-compliant (likely already) |

### Files to touch

| Action | File | Notes |
|--------|------|-------|
| UPDATE | `harness/bernard_voice.yaml` | SSOT for all string changes; ~6 new keys + several rewrites |
| UPDATE | `harness/bernard.py` | New ack functions for the de-collapsed update failures + `nl_llm_unavailable_ack`; keep fallbacks voice-compliant |
| UPDATE | `harness/commands.py` | Route distinct exceptions to distinct acks (Task 4); separate LLM-down (Task 5) |
| UPDATE | `harness/nl_to_sparql.py` | Distinguish LLM-unavailable from gap (Task 5/8); preserve gap + security logging |
| UPDATE | `infra/bot/git_ops.py` | Open/close commit-message voice (Task 6) — **baked into bot image, needs rebuild to test live** (see [[infra_vps_deploy_rsync]]) |
| CREATE | `harness/tests/test_voice_audit.py` | Forbidden-token guard over the YAML (Task 1) |
| UPDATE | `harness/tests/` (existing) | Adjust assertions for renamed/split acks; add open/close commit-message test |

### Critical gotchas

- **`git_ops.py` is baked into the bot image** — a commit-message change (Task 6) won't appear on the VPS until the image is rebuilt + `make publish` rsync; `harness/` voice YAML is COPY'd in too. The done-gate walk must run against a freshly-built image, not the running one. ([[infra_vps_deploy_rsync]])
- **Rooms must be unencrypted** for Bernard to see messages at all (MegolmEvent dropped) — use the existing test room. Unrelated to this story but blocks the live walk if you spin a new room.
- **Do not weaken NFR-S5/S7**: the `FORBIDDEN` regex rejection and read-only-on-Oxigraph guarantee are security ACs from 6.4 — a voice rephrase must not change control flow, only the returned string.
- **`mom:OntologyGap` is a FR41 side effect**, not cosmetic — rephrasing `nl_gap_ack` must keep `_write_gap()` firing (`nl_to_sparql.py:142`).
- **`null` is legal as a user-typed value** for `state.open` opt-out (`invalid_bool_ack` mentions it) — the forbidden-token audit must scope to *error-narration* strings, not reject the literal where it's a valid input example. Whitelist that one key or match `null` only outside backticks.

### Latest-library note (context7 / matrix-nio)

No new dependency. `matrix-nio` (adapter), `openai>=1.30.0` (OpenRouter client via `llm_client.py`), `httpx`, `shapely`, `structlog` are all already pinned in `infra/bot/requirements.txt`. The `openai` SDK surface used is only `chat.completions` against OpenRouter's base URL — no API change relevant to a copy-pass story. If touching `llm_client.py` error handling (Task 5), the exceptions to catch are `openai.APIConnectionError`, `openai.APIStatusError`, `openai.APITimeoutError`, plus the local `ValueError` for the unset key — catch broadly and map to `nl_llm_unavailable_ack`, since the goal is "any LLM failure → graceful", not fine-grained retry.

### Project Structure Notes

- Aligns with the established `harness/` layout; no new modules beyond a test file.
- `bernard_voice.yaml` → `bernard.py` `_bot()` is the only copy pipeline; no JS mirror ([[feedback_no_triple_source_of_truth]]).
- This story closes the deferred "graceful failure / Bernard voice pass" items tagged for 6.5 in `deferred-work.md` (the 6.1/6.2 `update_failed_ack` collapse, the 6.3 `network_empty` no-seeded-note, the LLM-down-vs-data-absence distinction).

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.5 (L1810-1827)]
- [Source: _bmad-output/planning-artifacts/mom_handoff_2026-06-16.md#Bernard voice rules (L319-356)]
- [Source: _bmad-output/planning-artifacts/architecture.md#L513 (Voice = 6.5 AC)]
- [Source: _bmad-output/implementation-artifacts/deferred-work.md — NL→write orphan; 6.1/6.2 update_failed_ack collapse; 6.3 network_empty]
- [Source: harness/bernard_voice.yaml, harness/bernard.py, harness/commands.py, harness/nl_to_sparql.py, harness/router.py, infra/bot/git_ops.py:306-341]
- FR39 (show-how-I-searched SPARQL block), FR40 (graceful clarification offer), FR41 (`mom:OntologyGap` logging), NFR-S5 (mutating-SPARQL rejection), NFR-S7 (read-only Oxigraph)

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List

## Open Questions (for {user_name})

1. **9.8 tutorial URL for the deploy-key path** (Task 3): is there a final public URL to link from `no_deploy_key_ack`, or should it link to `!mom link` only until 9.8 ships its surface? (Story 9.8 is "ready-for-dev/ahead" per [[project_epic9_m2_resequencing]] but may not be live.)
2. **NL→write orphan sequencing**: confirm the slot-filling handler is a *separate* story created before 6.5 is signed *done*, and that 6.5 shipping with the `write` branch still returning a (voice-audited) `unknown_ack` is acceptable for now. (deferred-work.md says it "logically sequences before 6.5".)
3. **Misconfig ack tone** (Task 4, row 6): okay for Bernard to say "operator's been notified" even though there's no actual notification wiring yet — or phrase as "this needs my operator's attention" to avoid implying an alert that doesn't fire?
