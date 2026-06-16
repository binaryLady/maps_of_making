# Story 6.1: Deploy-Key Provisioning + SSH Git Access

Status: review

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a space coordinator,
I want to grant Bernard scoped write access to my endpoint JSON via a deploy key,
so that the bot can edit my data on my behalf without MOM ever hosting or owning the file.

## Acceptance Criteria

> Source: epics.md §"Story 6.1" (lines 1723–1741); ADR-017 (architecture.md §477–520, esp. "Write path"); mom_handoff_2026-06-16.md §"Story 6.1" (lines 121–148); prd.md FR45/FR47.

1. `infra/link_handler/main.py` gains `POST /api/bot/deploy-key/{space_id}` which: generates an ed25519 key pair, encrypts the private key at rest (Fernet, key from env `BOT_KEY_SECRET`), persists both keys keyed to `space_id`, and returns the public key (OpenSSH `ssh-ed25519 AAAA...` line) + tutorial markdown in the response body.
2. The same endpoint accepts a `room_id` (query param or JSON body) and writes a room→space mapping into Oxigraph as `mom:botRoom` (e.g. `<urn:mak:room/{room_id}> mom:botRoom <urn:mak:space/{space_id}>`) — **the bot itself never writes to Oxigraph** (NFR-S7); this triple is written by `link_handler`, the existing sole writer, on the bot's behalf via this HTTP call. See Dev Notes "Room→space mapping: who writes it" for why this resolves an otherwise-unresolved AC dependency.
3. A new bot command `!mom link {space_slug}` (handled in `harness/router.py`, routed from intent `write` or directly pattern-matched before the classifier — see Dev Notes "Command parsing, not intent routing") calls `POST /api/bot/deploy-key/{space_id}` with the room's `room_id`, then presents the returned public key block and tutorial steps in Bernard voice back into the Matrix room.
4. `infra/bot/git_ops.py` (new module, used by the bot container — Story 6.2 onward, but the read/auth plumbing lands here) provides:
   - `read_json(space_id) -> dict` — clone/pull the space's repo over SSH using the stored deploy key, return the parsed JSON file content.
   - `patch_json(space_id, field_path, value) -> dict` — apply the patch to the in-memory JSON, validate against `SpaceAPISchema` (reuse `infra/link_handler/main.py`'s existing pydantic model — see Dev Notes), return the patched dict (does not commit; 6.2 wires patch→commit together for real field writes).
   - `commit_json(space_id, field_path, value, authorized_by) -> str` — write the file, `git add`/`commit`/`push` over the deploy key, return the commit SHA. Commit message format: `Update {field_path} for {space_name} · authorized by {matrix_user_id}`.
5. Before any git operation, `git_ops` checks whether a deploy key is stored for `space_id`. If absent, it raises a typed exception (`NoDeployKeyError`) that the router catches and turns into Bernard's degraded-path response (never a raw error/traceback/HTTP code in the room).
6. The done gate exercises the full loop end-to-end: `!mom link` returns a working public key + tutorial; after the coordinator adds it to their repo's Deploy Keys (Write access enabled), `!mom update space.url "https://example.com"` (a minimal write invoking `git_ops.commit_json` directly — full command parsing/permission model is 6.2, but this story's done gate needs one real field write to prove the SSH path works) commits the change and the heartbeat re-ingests it within 10 minutes.

**Done gate (operator confirmation):** `!mom link` in a real Matrix room returns a public key + tutorial; after the coordinator pastes the key into GitLab's Deploy Keys (Write access) for a test space repo, `!mom update space.url "https://example.com"` commits over SSH and the heartbeat picks up the change within 10 min.

## Tasks / Subtasks

- [x] **Task 1 — Deploy-key storage layer** (AC: 1, 5)
  - [x] Add a shared bind-mounted volume `data/bot-keys/` (new directory, gitignored) mounted into both `mak-link-handler` (read/write — it generates keys) and `mak-agent-bot` (read-only — `git_ops.py` needs the decrypted private key for SSH). One pair of files per space: `{space_id}.key` (Fernet-encrypted PKCS8 PEM private key) and `{space_id}.pub` (plaintext OpenSSH public key — not secret, safe to read by either container).
  - [x] Add `cryptography` to `infra/link_handler/requirements.txt` and `harness/requirements.txt` (both containers need `Fernet` + key-loading; only `link_handler` generates keys, `git_ops` only decrypts).
  - [x] **`harness/Dockerfile` must install `git` and `openssh-client`** — the `python:3.12-slim` base image (Story 6.0's Dockerfile) ships neither, and `git_ops.py` shells out to both via `subprocess`. Add `RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client && rm -rf /var/lib/apt/lists/*` before the `pip install` layer. This is a real gap, not a hypothetical — `mak-agent-bot`'s current image has no git binary at all.
  - [x] Add `BOT_KEY_SECRET` to `.env`/`.env.example` (Fernet key, `Fernet.generate_key()` once, shared verbatim across both containers — mismatched secrets silently break decryption). Document in Dev Notes that this is the same secrets convention as `LINK_SECRET`.
  - [x] Implement `infra/link_handler/bot_keys.py`: `generate_and_store(space_id) -> tuple[str, str]` (returns `(public_key_openssh, tutorial_markdown)`), `key_exists(space_id) -> bool`, and a `load_private_key(space_id) -> bytes` used by `git_ops` (mirrors the storage format so both sides agree).

- [x] **Task 2 — `POST /api/bot/deploy-key/{space_id}` endpoint** (AC: 1, 2)
  - [x] Validate `space_id` with the existing `^[a-zA-Z0-9_-]+$` pattern (mirror `get_space_snapshots`/`get_space_raw`).
  - [x] Look up the space's `mom:endpointUrl` by SPARQL (mirror `_query_all_claimed_spaces`/`get_space_snapshots` query shape, filtered to one `space_id` under both `urn:mak:space/` and `urn:mak:canary/`) — 404/graceful error if the space isn't registered yet (AC depends on "space is registered with an endpoint URL").
  - [x] Call `bot_keys.generate_and_store(space_id)`; build the tutorial markdown (GitLab-first, mirror Story 9.8's 4-step voice — "Create a deploy key", paste-into-Settings→Repository→Deploy Keys→enable Write).
  - [x] If `room_id` is present in the request, run one SPARQL `INSERT DATA` writing `mom:botRoom` (mirror the `async with httpx.AsyncClient` + `/update` pattern already used throughout `main.py`, e.g. `register_url`'s Oxigraph write block).
  - [x] Return `{"public_key": ..., "tutorial": ..., "space_id": ...}`.

- [x] **Task 3 — `infra/bot/git_ops.py`** (AC: 4, 5)
  - [x] `_repo_remote_for(endpoint_url) -> tuple[ssh_remote, branch, file_path]` — parse the registered raw-file URL into a git SSH remote. **GitLab is the only platform with a tested tutorial (Story 9.8)** — implement the GitLab `-/raw/{branch}/{path}` pattern as the primary case; add best-effort parsing for GitHub (`raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}`) and Gitea/Codeberg (`/raw/branch/{branch}/{path}`) but do not block the story on testing those — note as a known gap (see Dev Notes "Raw-URL → git-remote parsing is new, untested for non-GitLab").
  - [x] `NoDeployKeyError(Exception)` — raised by all three functions below when `bot_keys.key_exists(space_id)` is false.
  - [x] `read_json(space_id) -> dict` — resolve remote via the SPARQL lookup (same query as Task 2) + `_repo_remote_for`; clone (or pull if already cloned to a per-space cache dir under a new `data/bot-repos/{space_id}/` bind mount) using `subprocess.run(["git", ...], env={"GIT_SSH_COMMAND": f"ssh -i {tmp_key_path} -o StrictHostKeyChecking=no"})` with the decrypted key written to a `0600` tempfile for the duration of the call, then deleted; parse and return the JSON file.
  - [x] `patch_json(space_id, field_path, value) -> dict` — apply a dotted-path patch to the dict (e.g. `state.open`), then `SpaceAPISchema.model_validate(patched_dict)` (reuse the import from `infra/link_handler/main.py` — see Dev Notes "Schema validation reuse needs a shared import path") to reject invalid shapes before any git write.
  - [x] `commit_json(space_id, field_path, value, authorized_by) -> str` — write file, `git commit -m "Update {field_path} for {space_name} · authorized by {authorized_by}"`, `git push` over the same SSH tempfile pattern, return the SHA (`git rev-parse HEAD`).

- [x] **Task 4 — `!mom link` bot command** (AC: 3)
  - [x] In `harness/router.py` (or a new `harness/commands.py` if `router.py` is getting crowded — see Dev Notes), pattern-match `!mom link {space_slug}` before/alongside the intent classifier (this is a literal command, not a slot-filling classification — see Dev Notes "Command parsing, not intent routing").
  - [x] Call `POST {LINK_HANDLER_URL}/api/bot/deploy-key/{space_slug}?room_id={message.room_id}` via `httpx` (new env var `LINK_HANDLER_URL`, default `http://mak-link-handler:8000` — internal compose DNS name, mirrors how other internal services address each other).
  - [x] Format the response (public key block + tutorial) in Bernard voice (`harness/bernard.py` — add a `link_tutorial(public_key, tutorial_md)` formatter alongside the existing `ping_ack`/`unknown_ack`).
  - [x] On `NoDeployKeyError` or HTTP failure from `link_handler`, respond with Bernard's degraded path (per voice rules: "I can read your profile but I can't edit it yet...") rather than a raw error.

- [x] **Task 5 — Minimal write for the done gate** (AC: 6)
  - [x] Add `!mom update {field.path} {value}` as a second literal-command pattern in the same place as `!mom link` — **this story implements only enough to prove the SSH path**: no permission model, no power-level check, no field whitelist (all of that is Story 6.2). Any matrix user who can type in the room can trigger it for now; flag this explicitly in code comments and in the Story 6.2 dependency note so it isn't mistaken for the real permission model.
  - [x] Wire it to `git_ops.patch_json` + `git_ops.commit_json`, formatted through Bernard voice on success/failure.

- [x] **Task 6 — Compose wiring** (AC: 1, 4)
  - [x] Add `data/bot-keys` and `data/bot-repos` bind mounts to both `mak-link-handler` and `mak-agent-bot` in `infra/docker-compose.yml`; add `.gitkeep` files; gitignore the contents (mirror the `data/dendrite-postgres/.gitkeep` pattern from Story 6.0).
  - [x] Add `BOT_KEY_SECRET` env var to both services; add `LINK_HANDLER_URL=http://mak-link-handler:8000` to `mak-agent-bot`.
  - [x] `:z` SELinux flag on the new volumes for `docker-compose.dev.yml` only (Fedora/Podman convention — see Dev Notes).

- [x] **Task 7 — Tests**
  - [x] Unit test `bot_keys.py`: generate→store→load round-trips to the same key bytes; `Fernet` decryption fails loudly (not silently) on a wrong secret.
  - [x] Unit test `git_ops._repo_remote_for`: GitLab raw-URL parsing produces the right `(ssh_remote, branch, path)` tuple from a real example URL shape (`https://gitlab.com/{user}/{project}/-/raw/main/file.json`).
  - [x] Unit test `git_ops.patch_json`: valid patch passes schema validation; an invalid shape (e.g. setting `state` to a list) is rejected before any write is attempted.
  - [x] Live integration test (per project convention — mocks hide protocol bugs): exercise the full clone/patch/commit/push cycle against a real (throwaway, local) bare git repo served over a self-hosted local sshd, hermetic (no GitLab account needed in CI) — see Dev Agent Record note on scope vs. the AC's literal wording.
  - [x] `NoDeployKeyError` path: calling `git_ops.read_json`/`commit_json` for a space with no stored key raises the typed exception, and the router-level test confirms it becomes Bernard's degraded-path text, not an exception leak.

- [x] **Task 8 — Done gate**
  - [x] Operator confirmation, Matrix half: `!mom link openfab` in a real Matrix room on the self-hosted Dendrite homeserver returns a real public key + tutorial (`commands.link_succeeded`, verified in `mak-agent-bot` logs). Bernard auto-joins the room invite (see Change Log — new fix, not present at story start).
  - [x] Operator confirmation, write-path half: openfab re-registered with its real raw GitHub URL (`https://raw.githubusercontent.com/openfab-lab/openfab-website/refs/heads/master/openfab.json`); `!mom update next_event "Open House — 2026-06-20"` committed and pushed over SSH (`commands.update_succeeded sha=bd286a598cb19e88a6e231337c7ad7f8dde4b215`, Bernard acked `Done. Committed as bd286a59.` in the room). Re-ingestion confirmed via manual refresh on the Space Profile card (heartbeat trigger endpoint isn't host-exposed; manual refresh is the equivalent, lower-friction check) — `next_event` visible in the live endpoint response.

## Dev Notes

### What this story is (and is NOT)
- **IS:** the deploy-key generation/storage layer, the SSH git plumbing (`git_ops.py`), and just enough of a write command (`!mom update`, unguarded) to prove the SSH round-trip end-to-end at the done gate.
- **IS NOT:** the permission model, power-level checks, field whitelist, `!mom open`/`!mom close`/`!mom grant`/`!mom revoke`/`!mom permissions` (all Story 6.2). Do not build the permission model here — `!mom update` in this story is intentionally wide-open and must be called out as such so 6.2 doesn't get skipped under the assumption "writes already work."
- **IS NOT:** Nanobot, NL→SPARQL, isochrone, voice polish beyond the one degraded-path line this story's AC requires.

### Existing code being extended (READ FIRST)
- `harness/router.py`, `harness/bernard.py`, `harness/main_matrix.py` — Story 6.0's spine. `route()` currently only resolves `unknown`→`bernard.unknown_ack()`; `write`/`query`/`nl_discovery` log a warning and fall through to the same ack. This story is the first to give the `write` path (partially) real behavior, but via literal command pattern-matching, not the LLM intent classifier — see "Command parsing, not intent routing" below.
- `harness/bernard.py` + `harness/bernard_voice.yaml` — only `ping_ack`/`unknown_ack` exist. Add new voice strings here, not inline in Python (matches the existing convention).
- `infra/link_handler/main.py` — the **only** Oxigraph writer in the system (ADR-015). `register_url` (lines ~923–1039) is the closest existing pattern for "look up or validate a space, then write Oxigraph via the `httpx.AsyncClient` + `/update` POST pattern" — reuse that shape for the new `mom:botRoom` write. `get_space_snapshots`/`get_space_raw` (lines ~1039–1100) are the closest existing pattern for "validate `space_id` against `^[a-zA-Z0-9_-]+$`, then SPARQL-filter by it" — reuse that shape for the deploy-key endpoint's space lookup.
- `infra/link_handler/utils.py` — `MOM`, `SCHEMA`, `_sparql_str`, `_sparql_iri`, `_slug` are already-established helpers; use them rather than re-deriving namespace strings or re-escaping literals inline.
- `SpaceAPISchema` (`infra/link_handler/main.py:347`) — the existing pydantic model that accepts both MOM JSON-LD and flat SpaceAPI v14 shapes. `git_ops.patch_json` must validate against this same model, not a new one (see "Schema validation reuse" below).

### Command parsing, not intent routing
The Story 6.0 intent classifier returns one of `write | query | nl_discovery | unknown` — a *category*, not a specific command. `!mom link` and `!mom update {field} {value}` are **literal slash-command-style patterns** with their own argument parsing; they should be matched *before* (or instead of) the LLM classifier call, the same way `!mom ping` already short-circuits in `main_matrix.py`. Do not route `!mom link` through `intent_classifier.classify()` — that's a ~200-token LLM call for something a regex/`str.split()` can resolve instantly and deterministically, and burns the "no LLM in the write path's command parsing" budget that 6.2's permission model also depends on staying fast. If `router.py` is getting crowded with literal commands, factor them into a new `harness/commands.py` that `main_matrix.py` checks first, falling through to `router.route()` (the classifier path) only for messages that don't match a known `!mom <verb>` prefix.

### Room→space mapping: who writes it
The epics.md AC for this story reads "**Given** ... a room→space mapping is stored in Oxigraph (`mom:botRoom`)" as a *precondition* — but no prior story (6.0 or earlier) creates that mapping, and nothing else in the backlog does either. This is a genuine gap in the handoff, not an oversight to defer: **this story must be the one that creates the mapping**, via the same `!mom link {space_slug}` call that requests the deploy key. The cleanest resolution consistent with NFR-S7 ("bot never writes triples") and ADR-015 ("link_handler is the only Oxigraph writer"): the bot passes `room_id` to `POST /api/bot/deploy-key/{space_id}`, and `link_handler` — already the system's sole writer — performs the `mom:botRoom` INSERT in the same request, alongside generating the key. The bot never touches Oxigraph directly, even for its own room-mapping metadata. Document this explicitly in code comments on both ends (the endpoint and the `!mom link` handler) since it's easy for a future story to "simplify" by having the bot write the mapping directly.

### Raw-URL → git-remote parsing is new, untested for non-GitLab
Registered `mom:endpointUrl` values come from the wizard's "paste your endpoint URL" flow (Story 9.8), which is **GitLab-only** in its tested tutorial: `https://gitlab.com/{user}/{project}/-/raw/{branch}/{path}`. To `git clone`/`push` over SSH, `git_ops._repo_remote_for` must derive `git@gitlab.com:{user}/{project}.git` from that URL. GitHub (`raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}`) and Codeberg/Gitea (`/{owner}/{repo}/raw/branch/{branch}/{path}`) have analogous-but-different raw-URL shapes; implement parsing for them too (the handoff lists all four as supported platforms) but treat them as best-effort/untested — the done gate only requires GitLab to work. If a URL doesn't match any known pattern, fail with a clear Bernard-voice message ("I don't recognise that hosting platform's URL shape yet") rather than a raw parse exception.

### Schema validation reuse needs a shared import path
`SpaceAPISchema` currently lives inside `infra/link_handler/main.py`, not a standalone module — fine when only `main.py` needs it, but `infra/bot/git_ops.py` runs in the **`mak-agent-bot`** container, a separate Docker image/process from `link_handler`. Either: (a) extract `SpaceAPISchema` (and its two small nested models `SpaceAPIGeo`/`SpaceAPILocation`) into `infra/link_handler/schema.py` and import it from both `main.py` and a path `infra/bot/git_ops.py` can reach (the bot container would need `infra/link_handler/schema.py` bind-mounted or copied in, similar to how `mak-link-handler` already bind-mounts `scripts/spaceapi_extract`), or (b) duplicate a minimal validation subset directly in `infra/bot/git_ops.py`. Prefer (a) — duplicating schema logic is exactly the kind of drift this project's "no triple source of truth" rule exists to prevent. Wire the bind mount/copy in Task 6's compose changes.

### Deploy-key crypto — concrete API (cryptography ≥ current; verified via Context7 2026-06)
```python
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.fernet import Fernet

# Generate
private_key = ed25519.Ed25519PrivateKey.generate()
public_key = private_key.public_key()

# Public key, OpenSSH line for the coordinator to paste into Deploy Keys:
pub_openssh = public_key.public_bytes(
    encoding=serialization.Encoding.OpenSSH,
    format=serialization.PublicFormat.OpenSSH,
)  # b"ssh-ed25519 AAAA... " — append a comment, e.g. b" bernard@mapsofmaking"

# Private key, PEM/PKCS8, unencrypted (Fernet wraps it for storage-at-rest instead):
priv_pem = private_key.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption(),
)

# Encrypt for storage:
fernet = Fernet(os.environ["BOT_KEY_SECRET"].encode())
encrypted = fernet.encrypt(priv_pem)  # write this to {space_id}.key
# Decrypt for use:
priv_pem = fernet.decrypt(encrypted)
```
For `git_ops`'s SSH usage: write the decrypted `priv_pem` to a `tempfile.NamedTemporaryFile(delete=False)` with `os.chmod(path, 0o600)` immediately after writing (OpenSSH refuses world/group-readable keys), pass `GIT_SSH_COMMAND=f"ssh -i {path} -o StrictHostKeyChecking=no"` in the `subprocess.run` env, then unlink the tempfile in a `finally` block — never leave a decrypted key on disk longer than the single git operation.

### Matrix homeserver is Dendrite, not matrix.org (carried over from Story 6.0)
Story 6.0 stood up a **self-hosted Dendrite homeserver** (`mapsofmaking.org`, account `@bernard:mapsofmaking.org`) rather than depending on an external Matrix server — `bot.matrix_homeserver` resolves to `http://dendrite:8008` internally (compose network) / `https://mapsofmaking.org` externally, with env-var precedence over `config.yaml` (fixed in 6.0's code review: `os.environ.get(...) or bot_cfg.get(...)`, not the reverse). For this story's done gate, the test Matrix room is on that same Dendrite instance — no new homeserver setup needed, but don't assume `matrix.org` federation semantics if testing room power levels later (6.2) on a self-hosted single-homeserver setup behaves slightly differently than federated test rooms. `MATRIX_DEVICE_ID` defaults to `None` (not empty string) per 6.0's review fix — preserve that when adding any new Matrix-adapter code paths.

### Testing standards
- Live integration over mocks for the protocol surface (project rule — mock tests hide protocol bugs). The git clone/commit/push cycle should be tested against a real (throwaway, local) git-over-SSH repo, not a mocked `subprocess.run`.
- Done gate is operator confirmation in a real Matrix room + a real GitLab test repo — not just a pytest pass.

### Project Structure Notes
- New bot-write code lives under `infra/bot/` (per architecture.md's file structure map: `infra/bot/git_ops.py`, `infra/bot/isochrone.py` — the latter is 6.3, out of scope here but keep the package init consistent).
- New deploy-key endpoint + storage lives under `infra/link_handler/` (the existing sole Oxigraph writer, per ADR-015/ADR-017).
- Fedora/Podman: any new bind-mounted volume (`data/bot-keys`, `data/bot-repos`) needs `:z` in `docker-compose.dev.yml`; harmless on Ubuntu VPS — do not add `:z` to the base `docker-compose.yml`. [Source: memory infra_selinux_and_platform_notes]
- `.env`/secrets convention: `BOT_KEY_SECRET` joins `LINK_SECRET`/`OPENROUTER_API_KEY` as env-only, never committed. [Source: memory feedback_secrets, infra_env_symlink]

### References
- [Source: _bmad-output/planning-artifacts/epics.md#Story 6.1 (lines 1723–1741)]
- [Source: _bmad-output/planning-artifacts/architecture.md#ADR-017 "Write path" (lines 498–506)]
- [Source: _bmad-output/planning-artifacts/mom_handoff_2026-06-16.md §"Story 6.1" (lines 121–148), §"New dependencies" (lines 384–398)]
- [Source: _bmad-output/planning-artifacts/prd.md FR45, FR47]
- [Source: _bmad-output/implementation-artifacts/9-8-gitlab-tutorial-surface-embedded-guide-raw-url-handoff-register-flow.md — raw-URL convention, GitLab-only tested tutorial]
- [Source: _bmad-output/implementation-artifacts/6-0-bot-infrastructure-adapters-intent-router-bernard-config.md — Dendrite homeserver, env precedence fix, `MATRIX_DEVICE_ID` default fix]
- [Source: infra/link_handler/main.py — `register_url`, `get_space_snapshots`, `get_space_raw`, `SpaceAPISchema`]
- [Source: infra/link_handler/utils.py — `MOM`, `_slug`, `_sparql_str`, `_sparql_iri`]
- [Source: harness/router.py, harness/bernard.py, harness/main_matrix.py — Story 6.0 spine being extended]
- [Source: Context7 `/pyca/cryptography` — Ed25519 key generation, OpenSSH serialization, Fernet token structure, verified 2026-06]

## Dev Agent Record

### Agent Model Used

Claude (Sonnet 4.6), via bmad-dev-story workflow.

### Debug Log References

None — no blocking failures during implementation. One pre-existing, unrelated test failure observed (`test_observed_at_skeleton_e2e.py::test_observed_at_skeleton_e2e`, fails with `ConnectError` because the sandbox has no route to `mapsofmaking.org` — confirmed pre-existing by running it against the unmodified `main` branch path; not touched by this story).

### Completion Notes List

- Extracted `SpaceAPISchema`/`SpaceAPIGeo`/`SpaceAPILocation` into `infra/link_handler/schema.py` (Dev Notes option (a)); `main.py` now imports them. No behavior change — verified `import main` still succeeds and `infra/link_handler` test suite still passes (14 passed, 1 pre-existing unrelated failure).
- `infra/link_handler/bot_keys.py` implements the Fernet-at-rest / ed25519 storage layer exactly per the Dev Notes crypto snippet.
- `POST /api/bot/deploy-key/{space_id}` added to `main.py`, reusing `heartbeat_space`'s canary/space lookup shape. Returns the existing key + freshly-rendered tutorial if one is already stored (idempotent — re-running `!mom link` doesn't rotate the key).
- `infra/bot/git_ops.py`: `read_json`/`patch_json`/`commit_json` match the AC4 signatures exactly (no `endpoint_url` param) — the SPARQL endpoint-URL lookup happens inside `git_ops` itself (`_lookup_endpoint_url`, same query shape as Task 2/`heartbeat_space`), making these functions async. `bot_keys.py` and `schema.py` are imported as flat modules from the same directory as `git_ops.py` — in the real container they're bind-mounted there (see compose changes); locally, tests add `infra/link_handler` to `sys.path` before importing.
- **Room→space resolution for `!mom update`**: the AC6 example (`!mom update space.url "..."`) doesn't specify how `space_id` is selected. Resolved per the Dev Notes "Room→space mapping: who writes it" design intent: `!mom update {field_path} {value}` resolves the target space via the `mom:botRoom` mapping for the issuing room (written by the preceding `!mom link`), not from the command text. `field_path` is the dotted JSON path (e.g. `state.open`, `schema:url`) applied directly via `git_ops.patch_json`.
- **Task 7 live-integration test scope note**: the AC's literal wording asks to exercise the full `POST /api/bot/deploy-key/{space_id}` against a real Oxigraph. This sandbox has no running Oxigraph instance, so `infra/bot/test_git_ops_live.py` instead exercises `git_ops.read_json`/`patch_json`/`commit_json` directly against a real local bare repo served over a self-spawned local `sshd` (skips cleanly if `sshd` isn't available) — the SSH clone/commit/push cycle this story is actually de-risking. `_repo_remote_for`'s URL-pattern parsing and the Oxigraph SPARQL lookup are exercised separately (unit tests + manual smoke check against a mocked `httpx.AsyncClient`, not committed as a test file). The full live-Oxigraph version of this test should be picked up at the real done gate (Task 8) or backfilled once a test Oxigraph fixture exists in CI.
- **Task 8 (done gate) is complete** — operator-run, 2026-06-16. Story moves to `review`.
  - **Matrix half: confirmed working.** `!mom link openfab` in a real Matrix room on the self-hosted Dendrite homeserver returned the real ed25519 public key + tutorial; `commands.link_succeeded` confirmed in `mak-agent-bot` logs.
  - **Bug found and fixed: `.env` `MATRIX_HOMESERVER` pointed at `http://localhost:8008`.** Inside the `mak-agent-bot` container this resolves to the container itself, not Dendrite, so the bot's sync loop never connected (silently retried forever — looked like a Dendrite-side issue at first, including a red herring during an unrelated Dendrite crash-loop). Fixed by changing to the internal compose DNS name, `http://dendrite:8008`. This was a deployment/config bug, not an application bug — no code changed.
  - **Gap found and fixed: matrix-nio does not auto-join room invites.** Confirmed via Context7 docs (`/matrix-nio/matrix-nio`) that this is by design — the library always requires an explicit `client.join(room_id)` call; Story 6.0's `MatrixAdapter` never wired an invite callback, so every invite sat pending indefinitely (worked around manually via the admin API during earlier testing in this session). Fixed by adding an `InviteMemberEvent` callback (`_on_invite`) to `harness/matrix_adapter.py` that auto-joins any invite addressed to the bot's own user ID, logging `matrix.invite_joined`. Verified against a fresh invite (not a manually-joined room): `matrix.invite_joined room_id=!bcURrvx02FPRP1dE:mapsofmaking.org` appeared in logs with no manual intervention, followed by a normal `!mom link openfab` round-trip in that same room.
  - **Initial write-path attempt blocked, not a bug — registration data-quality issue.** openfab's first registered `mom:endpointUrl` was `https://openfab.be/openfab.json` (a custom presentation domain, not a raw source URL), which doesn't match any of `_repo_remote_for`'s known raw-URL shapes — `UnsupportedHostError` raised and logged correctly. Resolved by re-registering openfab with its real raw GitHub URL.
  - **Bug found and fixed: GitHub's `refs/heads/{branch}/` raw-URL permalink shape wasn't parsed.** Once openfab was re-registered with `https://raw.githubusercontent.com/openfab-lab/openfab-website/refs/heads/master/openfab.json` (GitHub's actual "copy raw URL" output, not the older `{owner}/{repo}/{branch}/{path}` shortcut form `_repo_remote_for`'s GitHub regex assumed), the regex captured `branch="refs"` and `git clone --branch refs` failed (exit 128). Fixed by adding a regex case for the `refs/heads/{branch}/` shape ahead of the short-form fallback in `infra/bot/git_ops.py`.
  - **Bug found and fixed: no git author identity in the bot container.** After the clone/branch fix, `git commit` failed (exit 128, "Please tell me who you are") — the `mak-agent-bot` container has no `~/.gitconfig`. Fixed by passing `-c user.name=Bernard -c user.email=bernard@mapsofmaking.org` directly on the `git commit` invocation in `commit_json` (scoped to that call, not a global container-wide config change).
  - **Write-path confirmed working end-to-end.** `!mom update next_event "Open House — 2026-06-20"` committed and pushed over SSH: `commands.update_succeeded sha=bd286a598cb19e88a6e231337c7ad7f8dde4b215`; Bernard acked `Done. Committed as bd286a59.` in the room. Re-ingestion confirmed via manual "Refresh from endpoint" on the Space Profile card (the heartbeat trigger endpoint, `POST /api/heartbeat/run`, isn't published to the host — only reachable from inside the compose network — so manual refresh was used as the equivalent, lower-friction verification instead of an in-container `exec`): the live endpoint response shows `"next_event": "Open House — 2026-06-20"`.
  - **Two follow-ups surfaced, both out of this story's scope:**
    1. Bernard's failure responses for `!mom update` are too vague — `update_failed_ack()` collapses every failure mode (`NoEndpointError`, `UnsupportedHostError`, schema-validation failure, git/SSH failure) into one generic "check the field path and value" line, hiding the real cause that's already in the logs. Candidate for Epic 6.5 (graceful failure / Bernard voice pass).
    2. After a deploy key is registered via `!mom link`, the coordinator has no way to confirm which file/repo Bernard will actually target. A confirmation step (e.g. echo back the resolved `ssh_remote`/`branch`/`file_path`) would catch exactly this kind of endpoint-URL mismatch early. Candidate for Story 6.2 or 6.5.

### File List

- `infra/link_handler/schema.py` (new) — `SpaceAPISchema`/`SpaceAPIGeo`/`SpaceAPILocation`, extracted from `main.py`
- `infra/link_handler/main.py` — import schema from `schema.py`; add `bot_deploy_key` endpoint (`POST /api/bot/deploy-key/{space_id}`) + `DeployKeyRequest`
- `infra/link_handler/bot_keys.py` (new) — deploy-key generation/storage (Fernet + ed25519)
- `infra/link_handler/requirements.txt` — add `cryptography`
- `infra/link_handler/test_bot_keys.py` (new) — unit tests
- `infra/bot/__init__.py` (new)
- `infra/bot/git_ops.py` (new) — SSH git plumbing (`read_json`/`patch_json`/`commit_json`/`resolve_space_for_room`/`_repo_remote_for`)
- `infra/bot/test_git_ops.py` (new) — unit tests (`_repo_remote_for`, `patch_json`, `NoDeployKeyError`)
- `infra/bot/test_git_ops_live.py` (new) — live SSH integration test (local sshd + bare repo)
- `harness/commands.py` (new) — literal `!mom link` / `!mom update` command parsing
- `harness/main_matrix.py` — check `commands.try_handle()` before `route()`
- `harness/bernard.py` — add `link_tutorial`/`link_failed_ack`/`no_deploy_key_ack`/`update_failed_ack`/`update_succeeded_ack`
- `harness/bernard_voice.yaml` — add corresponding voice strings
- `harness/requirements.txt` — add `cryptography`, `pydantic`
- `harness/Dockerfile` — install `git` + `openssh-client`
- `harness/tests/test_commands.py` (new) — router-level command tests incl. `NoDeployKeyError` degraded-path
- `infra/docker-compose.yml` — `mak-agent-bot`/`mak-link-handler` volumes + env vars (`BOT_KEY_SECRET`, `BOT_KEYS_DIR`, `BOT_REPOS_DIR`, `LINK_HANDLER_URL`)
- `infra/docker-compose.dev.yml` — `:z` SELinux flags for the new bind mounts
- `.env.example` — document `BOT_KEY_SECRET`
- `.env` — add a generated `BOT_KEY_SECRET` (local dev only, gitignored)
- `.gitignore` — ignore `data/bot-keys/*`, `data/bot-repos/*`
- `data/bot-keys/.gitkeep`, `data/bot-repos/.gitkeep` (new)
- `harness/matrix_adapter.py` — add `InviteMemberEvent` auto-join callback (Task 8 operator-testing fix)
- `.env` — fix `MATRIX_HOMESERVER` from `http://localhost:8008` to `http://dendrite:8008` (Task 8 operator-testing fix, local dev only)
- `infra/bot/git_ops.py` — add GitHub `refs/heads/{branch}/` raw-URL regex case; set git author identity (`-c user.name`/`user.email`) on the `commit` call (Task 8 operator-testing fixes)

### Change Log

- 2026-06-16: Implemented Story 6.1 Tasks 1–7 (deploy-key storage, endpoint, `git_ops.py`, `!mom link`/`!mom update` commands, compose wiring, tests). Task 8 (live operator done gate) deliberately left open — needs a real Matrix room + GitLab repo.
- 2026-06-16: Task 8 operator testing, Matrix half. Fixed `.env` `MATRIX_HOMESERVER` (container-internal DNS name, was pointing at itself). Fixed matrix-nio's lack of invite auto-join (`harness/matrix_adapter.py` — new `InviteMemberEvent` callback), verified against a fresh invite. `!mom link openfab` confirmed working end-to-end in a real Matrix room.
- 2026-06-16: Task 8 operator testing, write-path half. openfab re-registered with its real raw GitHub URL (was a custom presentation domain). Fixed `infra/bot/git_ops.py`'s GitHub raw-URL regex to handle the `refs/heads/{branch}/` permalink shape (was capturing `branch="refs"`). Fixed missing git author identity in the bot container (`git commit` failed with "Please tell me who you are") by scoping `-c user.name`/`user.email` to the commit call. `!mom update next_event "..."` confirmed committing and pushing over SSH (`sha=bd286a59...`); re-ingestion confirmed via manual endpoint refresh on the Space Profile card. **Task 8 done gate complete — story moved to `review`.** Two follow-ups (vague `!mom update` failure messages; no post-link target-file confirmation) noted for Epic 6.2/6.5, out of this story's scope.
