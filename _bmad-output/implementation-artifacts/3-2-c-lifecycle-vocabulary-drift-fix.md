# Story 3.2c: Lifecycle Vocabulary Drift Fix

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As MOM,
I want the lifecycle vocabulary consistent across the ontology, the transformer code, and the planning docs,
so that Story 3.3's diagnostic canary tests one coherent model rather than papering over a drift.

## Acceptance Criteria

1. **Ontology enumeration.** `ontology/mom.ttl` — the `rdfs:comment` on `mom:operationalState` enumerates **exactly** the lifecycle values `seeded`, `confirmed`, `aging`, `zombie`, `closed`, `dead`, plus out-of-lifecycle `error` and `unlinked`. (`closed` is currently missing — it is written by Story 3.2b but never defined.)

2. **Terminal-state semantics stated.** That same comment states the two terminal states explicitly: `closed` = operator/coordinator-declared retirement (authoritative, intentional); `dead` = auto-inferred after N failed heartbeat cycles (inferred). Both are terminal.

3. **Boolean-vs-lifecycle note.** The `mom:operationalState` comment notes that the real-time open/closed **boolean** belongs to `mom:dynamicState`, NOT to `mom:operationalState`. (`mom:dynamicState` already carries this; the cross-reference must be explicit on `operationalState` so the two are not conflated.)

4. **No undefined branch in code.** `transformer.effective_marker()` has no branch referencing a lifecycle value the ontology does not define. Once AC#1 lands, the existing `if lifecycle_state == "closed"` branch is valid and stays; verify there is no *other* stale value. The stale-branch requirement is satisfied by aligning the ontology to the code, not by deleting the (now-correct) `closed` branch.

5. **Code docstrings aligned.** `classify_lifecycle()`'s docstring (`transformer.py:133`) currently reads `States: confirmed | aging | zombie | dead` — it omits `seeded` and `closed`. Docstrings and inline comments that enumerate lifecycle states match the AC#1 enumeration.

6. **`mak:` vs `mom:` prefix drift — resolved or escalated.** The predicate-prefix inconsistency (`mak:operationalState` vs `mom:operationalState`, and similar) across `epics.md` / `architecture.md` / `mom.ttl` / code is audited. Where it is a clear doc typo it is fixed to the canonical `mom:` form; anything ambiguous (a real modelling question) is written up as a one-paragraph escalation note for Nicolas in this story's Completion Notes rather than silently changed.

7. **`mak:closed` vs `closed` token collision — resolved or escalated.** Story 3.2b writes the *string value* `"closed"` to `mom:operationalState` and a `mak:closedAt` *timestamp predicate*. The roundtable defines `closed` = operator-declared retirement. Confirm these are not in conflict: the 3.2b auto-close-after-N-cycles path and an operator-declared retirement both legitimately land on `operationalState = "closed"` — but if the dev finds them semantically forked (different events sharing one token in a way that misleads), flag it in Completion Notes for Nicolas. Do not redesign 3.2b here.

8. **Regression intact.** The existing transformer test suite (`infra/link_handler/test_transformer.py`) passes unchanged after the edits — this story changes vocabulary/comments, not behaviour.

## Tasks / Subtasks

- [ ] Task 1: Fix `mom:operationalState` definition in the ontology (AC: #1, #2, #3)
  - [ ] Edit `ontology/mom.ttl` `mom:operationalState` `rdfs:comment` (line ~56): enumerate `seeded → confirmed → aging → zombie` plus terminals `closed` / `dead`, plus out-of-lifecycle `error` / `unlinked`
  - [ ] State in the comment: `closed` = operator/coordinator-declared retirement (authoritative); `dead` = auto-inferred after N failed heartbeat cycles (inferred)
  - [ ] Add the explicit cross-reference: the real-time open/closed boolean lives on `mom:dynamicState`, not here
  - [ ] Verify the `mom:dynamicState` comment (line ~49) still reads coherently alongside the new `operationalState` text
- [ ] Task 2: Align code docstrings/comments (AC: #4, #5)
  - [ ] Update `classify_lifecycle()` docstring (`transformer.py:133`) — enumerate `seeded | confirmed | aging | zombie | closed | dead`; note `classify_lifecycle` itself only *returns* `confirmed/aging/zombie/dead` (seeded is set at import, closed by the 3.2b closure path) — make that explicit so the docstring is accurate, not just complete
  - [ ] Scan `transformer.py` for any other lifecycle-state enumeration in comments/docstrings and align it
  - [ ] Confirm `effective_marker()` (`transformer.py:157`) branches only reference `seeded/closed/dead/zombie/aging` + endpoint `broken` — no value absent from AC#1
- [ ] Task 3: Audit the `mak:` vs `mom:` prefix drift (AC: #6)
  - [ ] `grep -rn "mak:operationalState\|mak:dynamicState\|mak:endpointHealth\|mak:lastUpdated" _bmad-output/planning-artifacts/ ontology/ infra/ scripts/`
  - [ ] Fix clear doc typos to canonical `mom:`; record anything ambiguous as an escalation paragraph in Completion Notes
- [ ] Task 4: Reconcile the `closed` token (AC: #7)
  - [ ] Re-read Story 3.2b's `_build_pii_strip_sparql` / `is_closed` path (`transformer.py:173`, ~717–878) against the roundtable's `closed` definition
  - [ ] Confirm both paths legitimately resolve to `operationalState = "closed"`; flag a genuine fork for Nicolas if found
- [ ] Task 5: Verify no regression (AC: #8)
  - [ ] `source venv/bin/activate && pytest infra/link_handler/test_transformer.py` — all pass
  - [ ] If `mom.ttl` is reloaded into Oxigraph as part of any local check, confirm it parses (Turtle syntax intact)

## Dev Notes

### What this story is — and is not

This is a **pure cleanup story, no behaviour change.** It edits an ontology comment, code docstrings, and (possibly) planning-doc typos so that Story 3.3's canary validates **one coherent model**. It is explicitly *not* a refactor of Story 3.2b's closure logic and *not* a redesign of the lifecycle state machine. **Blocks Story 3.3.** No dependencies.

### The drift, precisely (from `mom_handoff_2026-05-16.md` §"Code ↔ Ontology Drift Fix")

`effective_marker()` in `infra/link_handler/transformer.py:164` has a live branch `if lifecycle_state == "closed": return "closed"`. That value is produced by Story 3.2b's closure path (`transformer.py:722-723`: `if is_closed: lifecycle_state = "closed"`). But `mom:operationalState`'s `rdfs:comment` in `ontology/mom.ttl:56` enumerates only `seeded → confirmed → aging → zombie → dead` — **`closed` was never defined.** The code is ahead of the ontology.

**Fix direction: align the ontology UP to the code.** The handoff is explicit (§"The fix" step 3 says "remove / remap the stale branch") but the roundtable's later decision (§"Naming Decisions", §"Reading B") makes `closed` a *first-class terminal state* — so the branch is correct and must stay. The real fix is AC#1: add `closed` to the ontology enumeration. Do not delete the `closed` branch.

### Files to touch (all UPDATE, none NEW)

| File | Change |
|---|---|
| `ontology/mom.ttl` (~line 53–58) | Rewrite `mom:operationalState` `rdfs:comment` — add `closed`, state terminal semantics, cross-ref `mom:dynamicState` |
| `infra/link_handler/transformer.py` (~line 130–170) | Fix `classify_lifecycle` docstring; scan/align other lifecycle enumerations in comments |
| `_bmad-output/planning-artifacts/*.md` | Only if Task 3 finds clear `mak:`/`mom:` prefix typos |

### Current state of the files being modified

**`ontology/mom.ttl:53-58` — `mom:operationalState`** — current comment: *"Lifecycle (in order): 'seeded' … → 'confirmed' … → 'aging' … → 'zombie' … → 'dead' … Out-of-lifecycle: 'error' …; 'unlinked' … From ADR-006."* Missing: `closed`, terminal-state distinction, dynamicState cross-ref. Emoji glosses (⚪🔵⚠️🧟🪦) in the existing comment are fine to keep; add a tombstone gloss for `closed` consistent with the handoff (`closed` → solid/full-opacity tombstone marker per handoff §"Reading B").

**`ontology/mom.ttl:46-51` — `mom:dynamicState`** — already correct: *"Real-time open/closed state … Distinct from mom:operationalState (long-term lifecycle). Values: 'open', 'closed', 'unknown'."* Note `dynamicState` *also* uses the word `closed` — that is the **boolean** sense and is fine; AC#3 just requires `operationalState` to point readers here so the two `closed`s are not conflated. Do not edit `dynamicState` unless Task 1's last subtask finds an incoherence.

**`transformer.py:130-154` — `classify_lifecycle()`** — returns `(state, reason)`; state ∈ `{confirmed, aging, zombie, dead}` from day-thresholds in `config.yaml` `operational_state`. It does **not** emit `seeded` or `closed` — those are set elsewhere (`seeded` at import; `closed` via the 3.2b `is_closed` path at `transformer.py:722`). The docstring must say *which* states this function returns vs. the full vocabulary, or it will mislead.

**`transformer.py:157-170` — `effective_marker()`** — resolves `(endpoint_health, lifecycle_state, open_now)` → one marker. Lifecycle supersedes endpoint health. Branches: `seeded, closed, dead, zombie, aging`, then `broken`, then `open`, else `confirmed`. After AC#1 every branch value is ontology-defined. **Must be preserved exactly** — no behaviour change.

### Behaviour that must be preserved

- `effective_marker()` resolution order (lifecycle supersedes endpoint) — Story 3.2's truth model depends on it.
- Story 3.2b's `is_closed` / `consecutive_closed_cycles` / `mak:closedAt` flow — untouched.
- `mom.ttl` must remain valid Turtle and load into Oxigraph (607 named graphs live).
- All 71 unit tests + behaviour in `test_transformer.py` stay green.

### Vocabulary reference (canonical, post-fix)

Lifecycle (Axis B / `mom:operationalState`): `seeded` → `confirmed` → `aging` → `zombie`, with **two terminals** `closed` (operator-declared, authoritative) and `dead` (auto-inferred after N failed cycles). Out-of-lifecycle: `error`, `unlinked`. Real-time open/closed is the **boolean** `mom:dynamicState` (`open`/`closed`/`unknown`) — a different axis (Axis C), never `operationalState`.

### Project Structure Notes

- `ontology/mom.ttl` is the **working copy**; Nicolas manually syncs it to the separate `github.com/nicolasdb/mapsofmaking_ontology` repo. This story edits the working copy only — note in Completion Notes that an ontology sync is pending.
- Canonical namespace: `https://nicolasdb.github.io/mapsofmaking_ontology/ns#` (`mom:`). The `mak:` prefix is the resource IRI namespace (`.../resource/`) — `mak:closedAt` as a *predicate* is itself a candidate finding for the Task 3 audit; flag, do not unilaterally rename.
- venv: `source venv/bin/activate` before any `pytest`. Never create a new venv.

### References

- [Source: _bmad-output/planning-artifacts/epics.md#Story 3.2c: Lifecycle Vocabulary Drift Fix]
- [Source: _bmad-output/planning-artifacts/mom_handoff_2026-05-16.md#Code ↔ Ontology Drift Fix]
- [Source: _bmad-output/planning-artifacts/mom_handoff_2026-05-16.md#Naming Decisions: `closed` vs `close`]
- [Source: ontology/mom.ttl#mom:operationalState (line 53), #mom:dynamicState (line 46)]
- [Source: infra/link_handler/transformer.py#classify_lifecycle (line 130), #effective_marker (line 157)]

## Dev Agent Record

### Agent Model Used

### Debug Log References

### Completion Notes List

### File List
