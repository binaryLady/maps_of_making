# Story 6.2: Write Skillset — Permission Model, CDN-Aware Commit Flow, Setup Verification

**Epic:** 6 — Bernard Bot (one voice, two skillsets)
**Story ID:** 6.2
**Status:** ready-for-dev

---

## Story

As a space coordinator,
I want Bernard to enforce who can update my space's JSON, confirm the commit landed, and
tell me when the map has actually updated,
So that I can trust the bot is doing what I asked without having to check the repo myself.

**Depends on:** Story 6.1 (deploy key provisioning + SSH git write path confirmed working).
**Absorbs:** Epic 9 stories 9.6, 9.7, 9.10 — coordinator conversational field updates replace wizard tiers 2 & 3.

---

## Acceptance Criteria

### AC1 — Write gate: power level 100 only

**Given** a member in the Matrix room issues any write command (`!mom update`, `!mom open`, `!mom close`)
**When** their Matrix power level is below 100
**Then** Bernard refuses with a Bernard-voice message pointing to the coordinator, never a raw error

**Given** the coordinator (power level 100) issues a write command
**When** a deploy key is registered for the room's linked space
**Then** Bernard executes the write

### AC2 — Whitelisted fields only

**Given** a coordinator issues `!mom update {field_path} {value}`
**When** `field_path` is not in `ALLOWED_FIELDS`
**Then** Bernard refuses with a message listing what IS editable

Hard-coded `ALLOWED_FIELDS` (coordinator-only for PoC — no grant/revoke in this story):
`state.open`, `contact.irc`, `contact.matrix`, `contact.twitter`

### AC3 — Five-step commit + CDN-propagation flow

**Given** a valid write command from a coordinator
**When** the commit succeeds
**Then** Bernard immediately sends an ack (step 2) confirming the commit sha and setting CDN-lag expectations,
**Then** Bernard polls the raw endpoint URL until the committed value is visible (step 3),
**Then** Bernard triggers `POST /api/heartbeat-space/{space_id}` to force MOM re-ingest (step 4),
**Then** Bernard sends a follow-up message confirming propagation and hinting to hard-refresh the browser (step 5)

The five steps in detail:
1. `git_ops.commit_json` → sha (already exists from 6.1)
2. **Immediate ack** (synchronous return): `"Saved — committed as abc1234. Waiting for CDN propagation before the map updates…"`
3. **CDN poll** (background task): httpx GET the raw endpoint URL; parse JSON; compare `field_path` value; exponential backoff 5s→10s→20s→40s→60s→60s…; wall-clock budget 10 min
4. **Trigger space refresh**: `POST /api/heartbeat-space/{space_id}` on link_handler (no auth required — endpoint is unauthenticated; handles 429 gracefully by reading `retry_after_seconds`)
5. **Follow-up message** (sent from background task via adapter): `"Propagation confirmed. Endpoint refresh triggered. You may need to hard-refresh your browser to see the update on the map."`

If CDN budget exhausted (10 min): `"Commit abc1234 landed but CDN hasn't propagated after 10 minutes — the map will catch up on its own. Hard-refresh when you see it."`

### AC4 — `!mom open` / `!mom close` shorthands

**Given** a coordinator types `!mom open` or `!mom close`
**Then** these are sugar over `_handle_update("state.open", "true"/"false")` — same flow, same gate, same CDN-poll sequence
**And** commit messages use Bernard's shorthand voice:
`Mark {space_name} open · authorized by @user:server`
`Mark {space_name} closed · authorized by @user:server`

`state.open` accepts `true`, `false`, or `null` (opt-out). Value validation enforced.

### AC5 — Setup verification: `!mom status` + auto-run after `!mom link`

**Given** a coordinator types `!mom status` (or after any `!mom link` succeeds)
**Then** Bernard runs three non-destructive checks and reports the result:
1. Registered endpoint URL parses to a usable git SSH remote (`_repo_remote_for` — catches the GitHub-Pages-URL failure mode from 6.1 Task 8)
2. Deploy key is present for the space (`bot_keys.key_exists(space_id)`)
3. `git ls-remote {remote} {branch}` succeeds — proves key authenticates + branch exists (read-only proof; write-proof deferred — see below)

**And** Bernard echoes the resolved `remote`, `branch`, and `file_path` so the coordinator sees exactly what Bernard will target

**And** if any check fails, Bernard names the specific failure with the actionable fix — never a raw exception

### AC6 — Field value validation

**Given** `state.open` is being set
**Then** value must be `true`, `false`, or `null` (case-insensitive); anything else is refused with explanation

**Given** `contact.matrix` is being set
**Then** value must match `@user:server` pattern; otherwise refused with example

`contact.irc` and `contact.twitter` — basic non-empty string check sufficient for PoC.

### Done gate (operator confirmation)

In a live Matrix room on the Dendrite homeserver:
1. `!mom open` from coordinator → commit confirmed + CDN poll starts + follow-up when map updates
2. `!mom update contact.irc "#room:libera.chat"` from coordinator → same flow
3. `!mom open` from a power-level-0 member → graceful refusal
4. `!mom update space.name "..."` from coordinator → refused (field not in `ALLOWED_FIELDS`)
5. `!mom status` → echoes remote/branch/file_path, all three checks pass
6. `!mom link` on a GitHub-Pages URL → `!mom status` auto-runs and catches the bad URL shape before any commit attempt

---

## Dev Notes

### Two-message architecture (the key structural change from 6.1)

`_handle_update` currently returns a single string. The CDN-poll flow requires **two messages**: an
immediate ack and a later follow-up. Matrix has no open-response model — the follow-up must
come from a background `asyncio.create_task`.

Minimal change: pass `adapter` and `context` into `try_handle` and forward to `_handle_update`:

```python
# main_matrix.py — handle_message
response = await commands.try_handle(
    stripped.text, message.user_id, message.room_id, session_id,
    adapter=adapter, context=message   # NEW
)
```

```python
# commands.py — try_handle signature
async def try_handle(text, user_id, room_id, session_id, *, adapter=None, context=None) -> Optional[str]:
```

Only `_handle_update` (and open/close) uses `adapter`/`context`. All other verbs (`link`, `status`)
ignore them — backward-compatible, no existing tests break.

`_handle_update` spawns the background task and returns the immediate ack string as before:

```python
async def _handle_update(space_id, field_path, value, authorized_by, adapter, context) -> str:
    sha = await git_ops.commit_json(space_id, field_path, value, authorized_by)
    asyncio.create_task(_poll_and_refresh(space_id, field_path, value, sha, adapter, context))
    return bernard.update_committed_ack(sha, field_path, value)
```

### `_poll_and_refresh` in `commands.py`

Lives in `commands.py`, not `git_ops.py` — git_ops is git-only, HTTP/link_handler calls stay in commands.

```python
async def _poll_and_refresh(space_id, field_path, value, sha, adapter, context) -> None:
    endpoint_url = await git_ops._lookup_endpoint_url(space_id)
    raw_url = _to_raw_url(endpoint_url)   # helper: ensure raw delivery URL, not GitHub Pages

    delay, budget, elapsed, confirmed = 5.0, 600.0, 0.0, False
    while elapsed < budget:
        await asyncio.sleep(delay)
        elapsed += delay
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                r = await client.get(raw_url)
            if r.status_code == 200:
                actual = _extract_field(r.json(), field_path)
                if _values_match(actual, value):
                    confirmed = True
                    break
        except Exception:
            pass
        delay = min(delay * 2, 60.0)

    if confirmed:
        refresh_note = await _trigger_heartbeat(space_id)
        await adapter.send(bernard.propagation_confirmed_ack(refresh_note), context)
    else:
        await adapter.send(bernard.propagation_timeout_ack(sha), context)
```

The background task must **never let an exception bubble unhandled** — wrap the entire body in
`try/except Exception` and send a degraded follow-up if something unexpected happens.

### `_trigger_heartbeat` in `commands.py`

```python
async def _trigger_heartbeat(space_id: str) -> str:
    url = f"{LINK_HANDLER_URL}/api/heartbeat-space/{space_id}"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            r = await client.post(url, timeout=15.0)
        if r.status_code == 200:
            return "Endpoint refresh triggered."
        if r.status_code == 429:
            retry = r.json().get("retry_after_seconds", 60)
            return f"A refresh was already triggered recently — re-ingest will complete within {retry}s."
        return f"Endpoint refresh returned {r.status_code} — map will re-ingest on next scheduled cycle (every ~60s+)."
    except httpx.HTTPError as e:
        return f"Endpoint refresh unreachable ({e}) — map will re-ingest on next scheduled cycle."
```

**No auth header** — `POST /api/heartbeat-space/{space_id}` is unauthenticated (confirmed in
`infra/link_handler/main.py:759`). The 60s cooldown (`COOLDOWN_SECONDS = 60`) means if Lucas
clicked "Refresh from endpoint" in the last minute, Bernard gets 429 and surfaces the retry time —
this is fine and the message covers it.

Note: the global heartbeat fetches all endpoints and takes 60+ seconds. The per-space endpoint
is the right tool here — targeted, fast, and already exists.

### `_to_raw_url` helper

The raw endpoint URL must serve the JSON content directly (not a GitHub Pages URL). This helper
is the complement of `_repo_remote_for` — it ensures the GET target is the raw delivery URL:

```python
def _to_raw_url(endpoint_url: str) -> str:
    """Return a raw-content URL for polling CDN propagation.
    If the registered URL is already raw (raw.githubusercontent.com, etc.), return as-is.
    If it's a Pages/custom-domain URL, this can't be converted — raise ValueError
    (verify_setup should have caught this before any commit)."""
    if "raw.githubusercontent.com" in endpoint_url:
        return endpoint_url
    if "raw.gitea." in endpoint_url or "codeberg.org/raw" in endpoint_url:
        return endpoint_url
    # GitLab raw: /-/raw/ path
    if "/-/raw/" in endpoint_url:
        return endpoint_url
    raise ValueError(f"Cannot derive a raw polling URL from: {endpoint_url}")
```

Note: `_repo_remote_for` in `git_ops.py` already parses the URL into git SSH remote — the bad
GitHub-Pages-URL case fails there before `commit_json` is ever called. `_to_raw_url` is a
second guard for the CDN-poll step specifically.

### `_extract_field` + `_values_match` helpers

```python
def _extract_field(data: dict, field_path: str):
    """Navigate a dotted field path (e.g. 'state.open', 'contact.irc') into a dict."""
    parts = field_path.split(".")
    for part in parts:
        if not isinstance(data, dict):
            return None
        data = data.get(part)
    return data

def _values_match(actual, expected_str: str) -> bool:
    """Compare the actual JSON value to the expected string value.
    Handles bool: 'true'/'false' → Python bool; 'null' → None."""
    if expected_str.lower() == "null":
        return actual is None
    if expected_str.lower() == "true":
        return actual is True
    if expected_str.lower() == "false":
        return actual is False
    return str(actual) == expected_str
```

### Permission check — single `_can_write` function (extension seam)

All three write handlers (`update`, `open`, `close`) must call one function, not inline `< 100`:

```python
ALLOWED_FIELDS = frozenset({"state.open", "contact.irc", "contact.matrix", "contact.twitter"})
COORDINATOR_ONLY_FIELDS = frozenset({"space.name", "url"})  # cannot be in ALLOWED_FIELDS

def _can_write(power_level: int, field_path: str) -> tuple[bool, str]:
    """Returns (allowed, reason). Single point for future grant expansion."""
    if power_level < 100:
        return False, "read_only"
    if field_path not in ALLOWED_FIELDS:
        return False, "field_not_allowed"
    return True, "ok"
```

Future: swap the body of `_can_write` to also check per-user grants from Oxigraph — the three
call sites don't change.

### `Message` dataclass — add `power_level`

`harness/message.py`: add `power_level: int = 0` (default 0 = conservative, read-only).

`harness/matrix_adapter.py` `_on_message`: set it from `room.power_levels.get_user_level(event.sender)`.

Default 0 is backward-compatible — all existing tests that construct `Message` without `power_level`
continue to work and correctly deny writes.

### `verify_setup` in `infra/bot/git_ops.py`

Confirmed existing anchors in git_ops.py:
- `_lookup_endpoint_url(space_id)` — SPARQL metadata read (acceptable: reads MOM registration
  metadata, not SpaceAPI content; same call `commit_json` already makes)
- `_repo_remote_for(endpoint_url)` — parses URL → `(remote, branch, file_path)`; raises
  `UnsupportedHostError` on GitHub-Pages-URL shape (this is the 6.1 Task 8 regression case)

Confirmed in `infra/link_handler/bot_keys.py`:
- `bot_keys.key_exists(space_id) -> bool` — checks both `.key` and `.pub` present (partial-state
  safe per 6.1 code review finding)

```python
async def verify_setup(space_id: str) -> dict:
    """Non-destructive setup check. Runs automatically after !mom link and on !mom status."""
    result = {"ok": False, "checks": {}, "remote": None, "branch": None, "file_path": None, "errors": []}

    # Check 1: endpoint URL registered and parseable
    try:
        endpoint_url = await _lookup_endpoint_url(space_id)
        remote, branch, file_path = _repo_remote_for(endpoint_url)
        result["checks"]["url"] = True
        result.update(remote=remote, branch=branch, file_path=file_path)
    except NoEndpointError:
        result["checks"]["url"] = False
        result["errors"].append("No endpoint URL registered. Run `!mom link` first.")
        return result
    except UnsupportedHostError as e:
        result["checks"]["url"] = False
        result["errors"].append(f"Endpoint URL can't be used for git writes: {e}. Re-register with the raw file URL.")
        return result

    # Check 2: deploy key present
    result["checks"]["key"] = bot_keys.key_exists(space_id)
    if not result["checks"]["key"]:
        result["errors"].append("No deploy key found. Run `!mom link` to generate one.")

    # Check 3: git ls-remote (proves SSH auth + branch exists; read-only, no write proof)
    try:
        proc = await asyncio.create_subprocess_exec(
            "git", "ls-remote", "--heads", remote, branch,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "GIT_SSH_COMMAND": _ssh_cmd(space_id)},
        )
        stdout, _ = await proc.communicate()
        result["checks"]["remote"] = proc.returncode == 0 and branch.encode() in stdout
        if not result["checks"]["remote"]:
            result["errors"].append(f"Branch '{branch}' not found at remote, or key not accepted.")
    except Exception as e:
        result["checks"]["remote"] = False
        result["errors"].append(f"Remote check failed: {e}")

    result["ok"] = all(result["checks"].values())
    return result
```

`_ssh_cmd(space_id)` is the same helper `commit_json` uses to build the `GIT_SSH_COMMAND` env var
from the decrypted private key tempfile — reuse that pattern exactly.

**Deferred — write-proof:** `git ls-remote` proves read auth but succeeds on a read-only deploy key.
True write proof requires clone + empty commit + push + revert — mutates history, racy, bloats this
story. Deferred. `!mom status` will document this honestly ("read access confirmed; write access
will be confirmed on first commit").

### New `!mom status` verb in `commands.py`

```python
if verb == "status":
    return await _handle_status(room_id, bound)
```

`_handle_status`: resolves room→space via `resolve_space_for_room`, calls `verify_setup`, formats
the result via `bernard.status_report(result)`.

### Auto-verify at tail of `!mom link`

After `_handle_link` returns the tutorial string, immediately run `verify_setup` and append the
result to the response. If the URL check already fails (e.g. Pages URL), Bernard surfaces it in
the same message — no second round-trip needed.

```python
async def _handle_link(space_slug, room_id, bound) -> str:
    # ... existing httpx call to deploy-key endpoint ...
    tutorial_msg = bernard.link_tutorial(data["public_key"], data["tutorial"])

    # Auto-verify: catch the GitHub-Pages-URL bug immediately
    try:
        verify = await git_ops.verify_setup(space_slug)
        tutorial_msg += "\n\n" + bernard.status_report(verify)
    except Exception:
        pass  # verify failure is non-fatal here; !mom status covers it
    return tutorial_msg
```

### New Bernard voice strings

Add to `harness/bernard_voice.yaml` under `bot:`:

```yaml
# Commit + CDN flow
update_committed_ack: "Saved — committed as {sha}. Waiting for CDN to propagate before the map updates…"
propagation_confirmed_ack: "Map updated. {refresh_note} You may need to hard-refresh your browser to see the change."
propagation_timeout_ack: "Commit {sha} landed but CDN hasn't propagated after 10 minutes — the map will catch up on its own. Hard-refresh when you see it."

# Open/close shorthands
open_ack: "Marked as open — committed as {sha}. Waiting for CDN propagation…"
close_ack: "Marked as closed — committed as {sha}. Waiting for CDN propagation…"

# Permission refusals
read_only_ack: "That's a write command — only the space coordinator (power level 100) can make changes. You can ask them to run it, or ask me anything about the space."
field_not_allowed_ack: "That field isn't editable through me. Fields I can update: {fields}."

# Value validation
invalid_bool_ack: "state.open needs to be `true`, `false`, or `null` (to opt out). Example: `!mom update state.open true`"
invalid_matrix_id_ack: "contact.matrix should look like `@username:server`. Example: `!mom update contact.matrix @atelier:matrix.org`"

# Setup / status
status_ok_ack: "Everything looks set up.\n• Remote: {remote}\n• Branch: {branch}\n• File: {file_path}\n\nNote: read access confirmed; write access will be confirmed on your first commit."
status_error_ack: "Setup check found {n} issue(s):\n{errors}\nRun `!mom link` to fix the key or re-register with the correct URL."
```

### Testing strategy

**Unit tests (`harness/tests/test_commands.py`):**
- `_can_write` field whitelist + power-level gate (pure Python, no I/O)
- `_extract_field` dotted-path navigation including missing keys
- `_values_match` for bool/null/string cases
- `_trigger_heartbeat` 200/429/error branches (monkeypatch httpx)
- `_poll_and_refresh` — unit-test directly: monkeypatch httpx.get to return stale then fresh; assert follow-up sent via mock adapter; monkeypatch asyncio.sleep to no-op
- `try_handle` routing for `open`, `close`, `status` verbs
- `_handle_update` spawns background task (monkeypatch `asyncio.create_task`, assert called once)
- Permission refusals for power_level=0 and field_not_in_whitelist

**Unit tests (`infra/bot/test_git_ops.py`):**
- `verify_setup` happy path (monkeypatch `_lookup_endpoint_url`, `_repo_remote_for`, `bot_keys.key_exists`, `asyncio.create_subprocess_exec`)
- `verify_setup` — UnsupportedHostError (Pages URL) → check["url"]=False, right error message
- `verify_setup` — key absent → check["key"]=False
- `verify_setup` — ls-remote exit code != 0 → check["remote"]=False

**Live done gate (operator confirmation):** real Matrix room + real GitHub repo.

### Project structure — files touched

- `harness/message.py` — add `power_level: int = 0`
- `harness/matrix_adapter.py` — set `power_level` in `_on_message`
- `harness/main_matrix.py` — pass `adapter=adapter, context=message` into `try_handle`
- `harness/commands.py` — `try_handle` signature; `_handle_update` (permission gate + background task); `_handle_open_close` (new); `_handle_status` (new); `_can_write`; `ALLOWED_FIELDS`; `_poll_and_refresh`; `_trigger_heartbeat`; `_to_raw_url`; `_extract_field`; `_values_match`
- `harness/bernard.py` — new ack functions for all new strings
- `harness/bernard_voice.yaml` — new strings (listed above)
- `harness/tests/test_commands.py` — extend existing suite
- `infra/bot/git_ops.py` — add `verify_setup`
- `infra/bot/test_git_ops.py` — add `verify_setup` tests

**No new files. No new compose changes. No link_handler endpoint changes (heartbeat-space used as-is).**

### SELinux / Fedora

No new volumes. Existing `:z` flags sufficient.

### Deferred items (named, not forgotten)

1. **`POST /api/heartbeat-space/{space_id}` auth hardening** — endpoint is currently
   unauthenticated and rate-limited only by the 60s cooldown. Low blast radius (worst case:
   forced re-ingest of public data), but unauthenticated POSTs on a public-facing route are
   a hardening gap. Add `X-Bot-Secret` check (same pattern as deploy-key endpoint) in a future
   story when hardening the `/api/` surface generally.

2. **Write-proof in `!mom status`** — `git ls-remote` proves read auth but not write. True write
   proof (real push or `push --dry-run` — though `--dry-run` reliability varies by host's
   pre-receive hook) deferred to a follow-up. `!mom status` is honest about this limitation.

3. **`!mom grant` / `!mom revoke` / trusted-member tier** — not built in this PoC. Trigger for
   re-evaluation: first real coordinator who asks "can my co-organizer flip the open sign?"

### References

- `harness/commands.py:66` — explicit `# Story 6.2` TODO comment in `_handle_update`
- `infra/link_handler/main.py:759` — `POST /api/heartbeat-space/{space_id}`, `COOLDOWN_SECONDS=60`, no auth
- `infra/link_handler/bot_keys.py:41` — `key_exists(space_id) -> bool`
- `infra/bot/git_ops.py` — `_lookup_endpoint_url`, `_repo_remote_for`, `commit_json`, `_ssh_cmd`
- `_bmad-output/planning-artifacts/mom_handoff_2026-06-16.md` §"Story 6.2", §"Bernard voice rules"
- Story 6.1 completion notes — Task 8 follow-ups (GitHub Pages URL bug, vague failure messages)
- memory: `feedback_integration_testing` — no mocking protocol surface
- memory: `feedback_no_triple_source_of_truth` — JSON is write-target only; Oxigraph is query layer

---

## Dev Agent Record

### Agent Model Used
_to be filled by dev agent_

### Debug Log References
_to be filled by dev agent_

### Completion Notes List
_to be filled by dev agent_

### File List
_to be filled by dev agent_

### Change Log
_to be filled by dev agent_
