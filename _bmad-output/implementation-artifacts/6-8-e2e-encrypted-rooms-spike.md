# Story 6.8: E2E Encrypted Room Support — Spike

**Status:** ready-for-dev
**Epic:** 6 — Ask Bernard
**Story ID:** 6-8
**Depends on:** 6.7 (VPS test stance confirmed)

---

## User Story

As the operator,
I want to understand what it would take to make Bernard work in E2E encrypted Matrix rooms,
So that I can decide whether to implement it now or defer it with a clear cost estimate.

---

## Background

Story 6-deploy found that Bernard does not handle `MegolmEvent` (E2E encrypted messages). All `!mom` commands currently require unencrypted rooms. This is a known limitation, not a bug — E2E was intentionally deferred because matrix-nio's crypto stack requires non-trivial setup (key store, device trust, session management).

This story is a **spike**: investigate + prototype, produce a decision record, optionally ship if scope is confirmed small. It does NOT commit to full implementation upfront.

---

## Field Evidence (2026-06-19): the "verification spinner" symptom

While setting Bernard's Matrix profile (display name + avatar, now live), a second visible symptom of the missing crypto identity was confirmed: **Bernard's profile shows a perpetual loading spinner in Element**, in the verification-status slot directly under his Matrix ID.

This is NOT presence (presence was enabled in `dendrite.yaml` — `enable_inbound/outbound: true` — and verified working: Bernard reports `presence: online, currently_active: true`). It is the **cross-signing / verification lookup** that never resolves.

Confirmed by querying Dendrite `/_matrix/client/v3/keys/query` for `@bernard:mapsofmaking.org`:

```
devices with keys: []
master_keys:       []
self_signing:      []
```

Bernard has uploaded **no device keys and no cross-signing identity** — because matrix-nio runs without the `[e2e]` (olm) extra. Element queries his cross-signing keys to render the verification slot, gets nothing, and spins indefinitely.

Side-by-side comparison in the same room (Element profile panel):

| User | Verification slot | Why |
|------|-------------------|-----|
| `@nicolasdb:matrix.org` | green **✓ Verified** badge | cross-signed + verified |
| `@jason_p:matrix.org` | **Verify User** link | has cross-signing identity, not yet verified |
| `@bernard:mapsofmaking.org` | **perpetual spinner** | no cross-signing identity at all |

**Implication for this spike:** bootstrapping cross-signing (currently Deferred Item #1) is what makes that slot resolve. With a cross-signing identity, Bernard would show **Verify User** like `jason_p` (and could be verified into a green ✓). This is cosmetic in unencrypted rooms — nothing is broken, all `!mom` commands work — but it's the most user-visible artifact of the missing E2E stack, so the spike should explicitly note whether the chosen path clears it.

---

## Acceptance Criteria

**Given** the spike is complete
**When** Story 6.8 lands
**Then**:

- A written **Decision Record** exists (in this story's Dev Agent Record or a linked ADR) covering:
  - What matrix-nio requires for E2E (key store backend, device verification flow, session state)
  - Estimated implementation effort (hours) for a working prototype
  - Risks: key store persistence across bot restarts, room membership race conditions, key rotation
  - Recommended path: implement now, defer, or reject

- If the spike confirms effort ≤ 1 day:
  - Prototype is implemented and tested on VPS in the live test room
  - `infra/bot/` gains a persistent key store (SQLite or matrix-nio's built-in store)
  - `harness/main_matrix.py` handles `MegolmEvent` alongside `RoomMessageText`
  - Bernard responds correctly to `!mom help` in an encrypted room on VPS

- If effort > 1 day:
  - Decision Record documents the deferral with a clear "unlock condition" (e.g. "when coordinator adoption requires encrypted rooms")
  - A `TODO(e2e)` comment is added to `harness/main_matrix.py` at the MegolmEvent guard point

**Done gate (either path):** Decision Record written and operator-approved; if implemented, `!mom help` works in an encrypted room on VPS.

---

## Technical Investigation Guide

### 1. matrix-nio E2E Basics

matrix-nio supports E2E via `AsyncClient` with a `store_path` parameter. Key questions:

```python
# Current (no E2E):
client = AsyncClient(homeserver, user_id)

# With E2E:
client = AsyncClient(homeserver, user_id, store_path="/app/data/nio-store")
```

- Does `MatrixAdapter` in `harness/matrix_adapter.py` use `AsyncClient`? If yes, adding `store_path` may be sufficient to unlock E2E.
- Does it require `client.import_keys()` or auto-negotiation?

### 2. MegolmEvent Handling

Currently `harness/matrix_adapter.py` only processes `RoomMessageText`. E2E rooms deliver `MegolmEncryptedEvent` which must be decrypted:

```python
# Rough pattern — verify against matrix-nio docs:
if isinstance(event, MegolmEncryptedEvent):
    result = await client.decrypt_event(event)
    if isinstance(result, RoomMessageText):
        # handle as normal message
```

### 3. Key Store Persistence

The key store must survive bot restarts — it holds Megolm session keys. This means:
- Volume mount in `docker-compose.yml` for `/app/data/nio-store`
- The store path must be consistent across restarts (same device ID)

### 4. Device Verification

For encrypted rooms, the bot device must be trusted. Options:
- Auto-trust all devices (acceptable for PoC, security trade-off noted)
- Coordinator manually verifies bot device via their Matrix client
- Cross-signing (complex, out of scope for spike)

### 5. Files to Read First

- `harness/matrix_adapter.py` — current AsyncClient setup
- `harness/main_matrix.py` — message dispatch loop
- matrix-nio docs: https://matrix-nio.readthedocs.io/en/latest/nio.html#asyncclient

---

## Decision Record Template

_(Fill in during spike execution)_

**Date:** —
**Investigated by:** —

**Findings:**
- matrix-nio E2E requires: ...
- Key store backend: ...
- Device trust model for PoC: ...

**Effort estimate:** — hours

**Risks:**
- ...

**Recommendation:** [ ] Implement now  [ ] Defer — unlock condition: ...
[ ] Reject — reason: ...

---

## Deferred Items

1. **Cross-signing / verified devices** — PoC can use auto-trust. Full verification model deferred. NOTE: cross-signing is also what clears the profile verification spinner (see Field Evidence above); a message-only PoC using auto-trust will NOT clear the spinner unless it also bootstraps a cross-signing identity.
2. **Key backup / recovery** — if key store is lost, past messages are unrecoverable. Backup strategy deferred.
3. **Multi-device coordinator UX** — coordinator may need to verify bot on each device. Deferred.

---

## Change Log

- 2026-06-18: Story 6.8 created — E2E encrypted room spike with go/no-go decision gate.
- 2026-06-19: Added Field Evidence — confirmed Bernard's perpetual profile-verification spinner is the missing cross-signing identity (`keys/query` returns empty device + cross-signing keys), not presence. Flagged that a message-only auto-trust PoC won't clear the spinner without bootstrapping cross-signing.
