"""SSH git plumbing for the bot's write path (Story 6.1).

Runs inside the mak-agent-bot container. `bot_keys.py` and `schema.py` are
the canonical copies from infra/link_handler/ — bind-mounted alongside this
file in docker-compose (see Story 6.1 Dev Notes "Schema validation reuse
needs a shared import path") so there is exactly one SpaceAPISchema and one
key-storage format shared by both containers.
"""
import asyncio
import json
import os
import re
import subprocess
import sys
import tempfile
from collections import defaultdict
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent))

import bot_keys  # noqa: E402  (mounted alongside this file — see module docstring)
from schema import SpaceAPISchema  # noqa: E402

import httpx  # noqa: E402

OXIGRAPH_ENDPOINT = os.environ.get("OXIGRAPH_ENDPOINT", "http://localhost:7878")
BOT_REPOS_DIR = Path(os.environ.get("BOT_REPOS_DIR", "/app/bot-repos"))
MOM = "https://nicolasdb.github.io/mapsofmaking_ontology/ns#"

# Per-space lock so concurrent !mom update/!mom link for the same space can't
# double-clone or race a non-fast-forward push (Story 6.1 code review finding).
_space_locks: dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


def _sparql_iri(value: str) -> Optional[str]:
    """Minimal IRI-safety check mirroring infra/link_handler/utils.py's
    _sparql_iri — duplicated here because this module runs in the bot
    container, which doesn't have utils.py bind-mounted. Rejects characters
    that would let `value` break out of the surrounding <...> IRI literal."""
    if not value or "<" in value or ">" in value or " " in value or "\n" in value:
        return None
    return value


class NoDeployKeyError(Exception):
    """Raised when a git operation is attempted for a space with no stored deploy key."""


class UnsupportedHostError(Exception):
    """Raised when an endpoint URL's hosting platform can't be parsed into a git remote."""


class NoEndpointError(Exception):
    """Raised when a space has no registered mom:endpointUrl in Oxigraph."""


class NoChangeError(Exception):
    """Raised when a commit_json call would produce no diff (value already set)."""


async def resolve_space_for_room(room_id: str) -> str:
    """Resolve the space_id linked to a Matrix room via the mom:botRoom mapping
    written by `!mom link` (POST /api/bot/deploy-key/{space_id}, see Story 6.1
    Dev Notes "Room→space mapping: who writes it"). Raises NoEndpointError if
    the room has no linked space."""
    safe_room_id = _sparql_iri(f"urn:mak:room/{room_id}")
    if safe_room_id is None:
        raise NoEndpointError(f"Room {room_id!r} is not a valid room id")

    sparql = f"""PREFIX mom: <{MOM}>
SELECT ?space WHERE {{
  <{safe_room_id}> mom:botRoom ?space .
}}"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{OXIGRAPH_ENDPOINT}/query",
            content=sparql,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
        )
        resp.raise_for_status()
    bindings = resp.json().get("results", {}).get("bindings", [])
    if not bindings:
        raise NoEndpointError(f"Room {room_id!r} has no space linked yet — run !mom link first")
    space_uri = bindings[0]["space"]["value"]
    return space_uri.rstrip("/").rsplit("/", 1)[-1]


async def _lookup_endpoint_url(space_id: str) -> str:
    """Same lookup shape as link_handler's heartbeat_space/bot_deploy_key endpoints:
    canary lives in urn:mak:canary, regular spaces in urn:mak:space/<slug>."""
    if space_id == "mother-sands":
        graph_uri = "urn:mak:canary"
        subject = f"urn:mak:canary/{space_id}"
    else:
        graph_uri = f"urn:mak:space/{space_id}"
        subject = graph_uri

    sparql = f"""PREFIX mom: <{MOM}>
SELECT ?endpointUrl WHERE {{
  GRAPH <{graph_uri}> {{
    <{subject}> mom:endpointUrl ?endpointUrl .
  }}
}}"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        resp = await client.post(
            f"{OXIGRAPH_ENDPOINT}/query",
            content=sparql,
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": "application/sparql-results+json",
            },
        )
        resp.raise_for_status()
    bindings = resp.json().get("results", {}).get("bindings", [])
    if not bindings:
        raise NoEndpointError(f"Space {space_id!r} has no registered endpoint URL")
    return bindings[0]["endpointUrl"]["value"]


def _repo_remote_for(endpoint_url: str) -> tuple[str, str, str]:
    """Parse a registered raw-file endpoint URL into (ssh_remote, branch, file_path).

    GitLab is the only platform with a tested tutorial (Story 9.8) and is the
    primary case. GitHub and Gitea/Codeberg parsing is best-effort/untested —
    see Story 6.1 Dev Notes "Raw-URL → git-remote parsing is new, untested for
    non-GitLab".
    """
    # GitLab: https://gitlab.com/{user}/{project}/-/raw/{branch}/{path}
    m = re.match(r"^https?://gitlab\.com/(?P<repo>[^/]+/[^/]+)/-/raw/(?P<branch>[^/]+)/(?P<path>.+)$", endpoint_url)
    if m:
        return f"git@gitlab.com:{m['repo']}.git", m["branch"], m["path"]

    # GitHub raw, explicit refs form: https://raw.githubusercontent.com/{owner}/{repo}/refs/heads/{branch}/{path}
    # GitHub's "copy raw URL" button emits this shape, not the older {branch}/{path} shortcut below.
    m = re.match(
        r"^https?://raw\.githubusercontent\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/refs/heads/(?P<branch>[^/]+)/(?P<path>.+)$",
        endpoint_url,
    )
    if m:
        return f"git@github.com:{m['owner']}/{m['repo']}.git", m["branch"], m["path"]

    # GitHub raw, short form: https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{path}
    m = re.match(r"^https?://raw\.githubusercontent\.com/(?P<owner>[^/]+)/(?P<repo>[^/]+)/(?P<branch>[^/]+)/(?P<path>.+)$", endpoint_url)
    if m:
        return f"git@github.com:{m['owner']}/{m['repo']}.git", m["branch"], m["path"]

    # Gitea/Codeberg: https://{host}/{owner}/{repo}/raw/branch/{branch}/{path}
    m = re.match(r"^https?://(?P<host>[^/]+)/(?P<owner>[^/]+)/(?P<repo>[^/]+)/raw/branch/(?P<branch>[^/]+)/(?P<path>.+)$", endpoint_url)
    if m:
        return f"git@{m['host']}:{m['owner']}/{m['repo']}.git", m["branch"], m["path"]

    raise UnsupportedHostError(f"I don't recognise that hosting platform's URL shape yet: {endpoint_url}")


def _require_key(space_id: str) -> None:
    if not bot_keys.key_exists(space_id):
        raise NoDeployKeyError(f"No deploy key stored for space {space_id!r}")


def _run_git_ssh(args: list[str], cwd: Optional[Path], space_id: str) -> subprocess.CompletedProcess:
    """Run a git subcommand with the space's decrypted deploy key as GIT_SSH_COMMAND.
    The decrypted key never touches disk longer than this single call."""
    priv_pem = bot_keys.load_private_key(space_id)
    tmp = tempfile.NamedTemporaryFile(delete=False)
    try:
        tmp.write(priv_pem)
        tmp.close()
        os.chmod(tmp.name, 0o600)
        env = {**os.environ, "GIT_SSH_COMMAND": f"ssh -i {tmp.name} -o StrictHostKeyChecking=no"}
        return subprocess.run(["git", *args], cwd=cwd, env=env, capture_output=True, text=True, check=True)
    finally:
        os.unlink(tmp.name)


def _clone_or_pull(space_id: str, ssh_remote: str, branch: str) -> Path:
    repo_dir = BOT_REPOS_DIR / space_id
    if repo_dir.exists():
        _run_git_ssh(["pull", "origin", branch], cwd=repo_dir, space_id=space_id)
    else:
        BOT_REPOS_DIR.mkdir(parents=True, exist_ok=True)
        _run_git_ssh(["clone", "--branch", branch, ssh_remote, str(repo_dir)], cwd=None, space_id=space_id)
    return repo_dir


def _patch_dict(data: dict, field_path: str, value) -> dict:
    """Apply a dotted-path patch to `data` in place. Raises ValueError on an
    empty/dot-only field_path or a path that walks through a non-dict
    intermediate value, instead of silently mis-writing or raising a raw
    AttributeError (Story 6.1 code review finding)."""
    keys = [k for k in field_path.split(".")]
    if not keys or any(k == "" for k in keys):
        raise ValueError(f"field_path {field_path!r} must be a non-empty dot-separated path")

    target = data
    for key in keys[:-1]:
        nxt = target.setdefault(key, {})
        if not isinstance(nxt, dict):
            raise ValueError(f"field_path {field_path!r} expects {key!r} to be an object, found {type(nxt).__name__}")
        target = nxt
    target[keys[-1]] = value
    return data


async def _resolve_repo_unlocked(space_id: str) -> tuple[Path, str, str]:
    """Returns (repo_dir, branch, file_path) after clone/pull. Caller must
    hold `_space_locks[space_id]` — see read_json/patch_json/commit_json."""
    endpoint_url = await _lookup_endpoint_url(space_id)
    ssh_remote, branch, file_path = _repo_remote_for(endpoint_url)
    repo_dir = _clone_or_pull(space_id, ssh_remote, branch)
    return repo_dir, branch, file_path


async def read_json(space_id: str) -> dict:
    """Clone/pull the space's repo over SSH using the stored deploy key, return
    the parsed JSON file content."""
    _require_key(space_id)
    async with _space_locks[space_id]:
        repo_dir, _branch, file_path = await _resolve_repo_unlocked(space_id)
        return json.loads((repo_dir / file_path).read_text())


async def patch_json(space_id: str, field_path: str, value) -> dict:
    """Apply a dotted-path patch to the space's JSON, validate against
    SpaceAPISchema, and return the patched dict (does not commit)."""
    _require_key(space_id)
    async with _space_locks[space_id]:
        repo_dir, _branch, file_path = await _resolve_repo_unlocked(space_id)
        data = json.loads((repo_dir / file_path).read_text())
        _patch_dict(data, field_path, value)
        SpaceAPISchema.model_validate(data)  # raises if the patched shape is invalid
        return data


def _ssh_cmd(space_id: str) -> str:
    """Build GIT_SSH_COMMAND value from the space's decrypted key in a tempfile.
    Caller is responsible for cleanup (use _run_git_ssh for the common case)."""
    priv_pem = bot_keys.load_private_key(space_id)
    tmp = tempfile.NamedTemporaryFile(delete=False)
    tmp.write(priv_pem)
    tmp.close()
    os.chmod(tmp.name, 0o600)
    return f"ssh -i {tmp.name} -o StrictHostKeyChecking=no"


async def verify_setup(space_id: str) -> dict:
    """Non-destructive setup check. Runs automatically after !mom link and on !mom status."""
    result: dict = {"ok": False, "checks": {}, "remote": None, "branch": None, "file_path": None, "errors": []}

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
        result["checks"]["remote"] = False
        result["errors"].append("Remote check skipped — no deploy key.")
        result["ok"] = False
        return result

    # Check 3: git ls-remote (proves SSH auth + branch exists; read-only, no write proof)
    try:
        priv_pem = bot_keys.load_private_key(space_id)
        tmp = tempfile.NamedTemporaryFile(delete=False)
        try:
            tmp.write(priv_pem)
            tmp.close()
            os.chmod(tmp.name, 0o600)
            ssh_cmd = f"ssh -i {tmp.name} -o StrictHostKeyChecking=no"
            proc = await asyncio.create_subprocess_exec(
                "git", "ls-remote", "--heads", remote, branch,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env={**os.environ, "GIT_SSH_COMMAND": ssh_cmd},
            )
            stdout, _ = await proc.communicate()
            result["checks"]["remote"] = proc.returncode == 0 and branch.encode() in stdout
            if not result["checks"]["remote"]:
                result["errors"].append(f"Branch '{branch}' not found at remote, or key not accepted.")
        finally:
            os.unlink(tmp.name)
    except Exception as e:
        result["checks"]["remote"] = False
        result["errors"].append(f"Remote check failed: {e}")

    result["ok"] = all(result["checks"].values())
    return result


async def commit_json(space_id: str, field_path: str, value, authorized_by: str) -> str:
    """Write the patched file, git add/commit/push over the deploy key, return the commit SHA.

    The whole clone/patch/write/commit/push sequence runs under the space's
    lock so two concurrent !mom update calls for the same space can't
    double-clone or race a non-fast-forward push (Story 6.1 code review
    finding)."""
    _require_key(space_id)
    async with _space_locks[space_id]:
        repo_dir, branch, file_path = await _resolve_repo_unlocked(space_id)
        raw = (repo_dir / file_path).read_text()
        data = json.loads(raw)
        before = json.dumps(data, sort_keys=True)
        patched = _patch_dict(data, field_path, value)
        if json.dumps(patched, sort_keys=True) == before:
            raise NoChangeError(f"{field_path} is already set to {value!r}")
        SpaceAPISchema.model_validate(patched)  # raises if the patched shape is invalid

        (repo_dir / file_path).write_text(json.dumps(patched, indent=2) + "\n")

        space_name = patched.get("name") or patched.get("space") or space_id
        message = f"Update {field_path} for {space_name} · authorized by {authorized_by}"

        _run_git_ssh(["add", file_path], cwd=repo_dir, space_id=space_id)
        _run_git_ssh(
            [
                "-c", "user.name=Bernard",
                "-c", "user.email=bernard@mapsofmaking.org",
                "commit", "-m", message,
            ],
            cwd=repo_dir,
            space_id=space_id,
        )
        _run_git_ssh(["push", "origin", branch], cwd=repo_dir, space_id=space_id)
        sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_dir, capture_output=True, text=True, check=True)
        return sha.stdout.strip()
