# Story 6.1: Deploy-Key Provisioning + SSH Git Access

Status: ready-for-dev

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

- [ ] **Task 1 — Deploy-key storage layer** (AC: 1, 5)
  - [ ] Add a shared bind-mounted volume `data/bot-keys/` (new directory, gitignored) mounted into both `mak-link-handler` (read/write — it generates keys) and `mak-agent-bot` (read-only — `git_ops.py` needs the decrypted private key for SSH). One pair of files per space: `{space_id}.key` (Fernet-encrypted PKCS8 PEM private key) and `{space_id}.pub` (plaintext OpenSSH public key — not secret, safe to read by either container).
  - [ ] Add `cryptography` to `infra/link_handler/requirements.txt` and `harness/requirements.txt` (both containers need `Fernet` + key-loading; only `link_handler` generates keys, `git_ops` only decrypts).
  - [ ] **`harness/Dockerfile` must install `git` and `openssh-client`** — the `python:3.12-slim` base image (Story 6.0's Dockerfile) ships neither, and `git_ops.py` shells out to both via `subprocess`. Add `RUN apt-get update && apt-get install -y --no-install-recommends git openssh-client && rm -rf /var/lib/apt/lists/*` before the `pip install` layer. This is a real gap, not a hypothetical — `mak-agent-bot`'s current image has no git binary at all.
  - [ ] Add `BOT_KEY_SECRET` to `.env`/`.env.example` (Fernet key, `Fernet.generate_key()` once, shared verbatim across both containers — mismatched secrets silently break decryption). Document in Dev Notes that this is the same secrets convention as `LINK_SECRET`.
  - [ ] Implement `infra/link_handler/bot_keys.py`: `generate_and_store(space_id) -> tuple[str, str]` (returns `(public_key_openssh, tutorial_markdown)`), `key_exists(space_id) -> bool`, and a `load_private_key(space_id) -> bytes` used by `git_ops` (mirrors the storage format so both sides agree).

- [ ] **Task 2 — `POST /api/bot/deploy-key/{space_id}` endpoint** (AC: 1, 2)
  - [ ] Validate `space_id` with the existing `^[a-zA-Z0-9_-]+$` pattern (mirror `get_space_snapshots`/`get_space_raw`).
  - [ ] Look up the space's `mom:endpointUrl` by SPARQL (mirror `_query_all_claimed_spaces`/`get_space_snapshots` query shape, filtered to one `space_id` under both `urn:mak:space/` and `urn:mak:canary/`) — 404/graceful error if the space isn't registered yet (AC depends on "space is registered with an endpoint URL").
  - [ ] Call `bot_keys.generate_and_store(space_id)`; build the tutorial markdown (GitLab-first, mirror Story 9.8's 4-step voice — "Create a deploy key", paste-into-Settings→Repository→Deploy Keys→enable Write).
  - [ ] If `room_id` is present in the request, run one SPARQL `INSERT DATA` writing `mom:botRoom` (mirror the `async with httpx.AsyncClient` + `/update` pattern already used throughout `main.py`, e.g. `register_url`'s Oxigraph write block).
  - [ ] Return `{"public_key": ..., "tutorial": ..., "space_id": ...}`.

- [ ] **Task 3 — `infra/bot/git_ops.py`** (AC: 4, 5)
  - [ ] `_repo_remote_for(endpoint_url) -> tuple[ssh_remote, branch, file_path]` — parse the registered raw-file URL into a git SSH remote. **GitLab is the only platform with a tested tutorial (Story 9.8)** — implement the GitLab `-/raw/{branch}/{path}` pattern as the primary case; add best-effort parsing for GitHub (`raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}`) and Gitea/Codeberg (`/raw/branch/{branch}/{path}`) but do not block the story on testing those — note as a known gap (see Dev Notes "Raw-URL → git-remote parsing is new, untested for non-GitLab").
  - [ ] `NoDeployKeyError(Exception)` — raised by all three functions below when `bot_keys.key_exists(space_id)` is false.
  - [ ] `read_json(space_id) -> dict` — resolve remote via the SPARQL lookup (same query as Task 2) + `_repo_remote_for`; clone (or pull if already cloned to a per-space cache dir under a new `data/bot-repos/{space_id}/` bind mount) using `subprocess.run(["git", ...], env={"GIT_SSH_COMMAND": f"ssh -i {tmp_key_path} -o StrictHostKeyChecking=no"})` with the decrypted key written to a `0600` tempfile for the duration of the call, then deleted; parse and return the JSON file.
  - [ ] `patch_json(space_id, field_path, value) -> dict` — apply a dotted-path patch to the dict (e.g. `state.open`), then `SpaceAPISchema.model_validate(patched_dict)` (reuse the import from `infra/link_handler/main.py` — see Dev Notes "Schema validation reuse needs a shared import path") to reject invalid shapes before any git write.
  - [ ] `commit_json(space_id, field_path, value, authorized_by) -> str` — write file, `git commit -m "Update {field_path} for {space_name} · authorized by {authorized_by}"`, `git push` over the same SSH tempfile pattern, return the SHA (`git rev-parse HEAD`).

- [ ] **Task 4 — `!mom link` bot command** (AC: 3)
  - [ ] In `harness/router.py` (or a new `harness/commands.py` if `router.py` is getting crowded — see Dev Notes), pattern-match `!mom link {space_slug}` before/alongside the intent classifier (this is a literal command, not a slot-filling classification — see Dev Notes "Command parsing, not intent routing").
  - [ ] Call `POST {LINK_HANDLER_URL}/api/bot/deploy-key/{space_slug}?room_id={message.room_id}` via `httpx` (new env var `LINK_HANDLER_URL`, default `http://mak-link-handler:8000` — internal compose DNS name, mirrors how other internal services address each other).
  - [ ] Format the response (public key block + tutorial) in Bernard voice (`harness/bernard.py` — add a `link_tutorial(public_key, tutorial_md)` formatter alongside the existing `ping_ack`/`unknown_ack`).
  - [ ] On `NoDeployKeyError` or HTTP failure from `link_handler`, respond with Bernard's degraded path (per voice rules: "I can read your profile but I can't edit it yet...") rather than a raw error.

- [ ] **Task 5 — Minimal write for the done gate** (AC: 6)
  - [ ] Add `!mom update {field.path} {value}` as a second literal-command pattern in the same place as `!mom link` — **this story implements only enough to prove the SSH path**: no permission model, no power-level check, no field whitelist (all of that is Story 6.2). Any matrix user who can type in the room can trigger it for now; flag this explicitly in code comments and in the Story 6.2 dependency note so it isn't mistaken for the real permission model.
  - [ ] Wire it to `git_ops.patch_json` + `git_ops.commit_json`, formatted through Bernard voice on success/failure.

- [ ] **Task 6 — Compose wiring** (AC: 1, 4)
  - [ ] Add `data/bot-keys` and `data/bot-repos` bind mounts to both `mak-link-handler` and `mak-agent-bot` in `infra/docker-compose.yml`; add `.gitkeep` files; gitignore the contents (mirror the `data/dendrite-postgres/.gitkeep` pattern from Story 6.0).
  - [ ] Add `BOT_KEY_SECRET` env var to both services; add `LINK_HANDLER_URL=http://mak-link-handler:8000` to `mak-agent-bot`.
  - [ ] `:z` SELinux flag on the new volumes for `docker-compose.dev.yml` only (Fedora/Podman convention — see Dev Notes).

- [ ] **Task 7 — Tests**
  - [ ] Unit test `bot_keys.py`: generate→store→load round-trips to the same key bytes; `Fernet` decryption fails loudly (not silently) on a wrong secret.
  - [ ] Unit test `git_ops._repo_remote_for`: GitLab raw-URL parsing produces the right `(ssh_remote, branch, path)` tuple from a real example URL shape (`https://gitlab.com/{user}/{project}/-/raw/main/file.json`).
  - [ ] Unit test `git_ops.patch_json`: valid patch passes schema validation; an invalid shape (e.g. setting `state` to a list) is rejected before any write is attempted.
  - [ ] Live integration test (per project convention — mocks hide protocol bugs): exercise the full `POST /api/bot/deploy-key/{space_id}` against a real (test) Oxigraph + a throwaway local git repo served over SSH (e.g. a bare repo on `localhost`, not GitLab, to keep the test hermetic) to prove the clone/patch/commit/push cycle works end-to-end without needing a live GitLab account in CI.
  - [ ] `NoDeployKeyError` path: calling `git_ops.read_json`/`commit_json` for a space with no stored key raises the typed exception, and the router-level test confirms it becomes Bernard's degraded-path text, not an exception leak.

- [ ] **Task 8 — Done gate**
  - [ ] Operator confirmation: `!mom link` in the Openfab/test Matrix room (the same Dendrite homeserver Story 6.0 stood up — `@bernard:mapsofmaking.org`, see Dev Notes "Matrix homeserver is Dendrite, not matrix.org") returns a real public key; after pasting it into a real GitLab test repo's Deploy Keys with Write access, `!mom update space.url "https://example.com"` commits and the heartbeat re-ingests within 10 minutes.

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

### Debug Log References

### Completion Notes List

### File List
