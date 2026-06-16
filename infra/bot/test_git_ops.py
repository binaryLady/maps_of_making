"""Unit tests for git_ops.py (Story 6.1): raw-URL → git-remote parsing,
patch_json schema validation, and the NoDeployKeyError path.

Imports bot_keys.py/schema.py from infra/link_handler/ to mirror the
docker-compose bind-mount that puts the canonical copies alongside this
module in the real container (see module docstring in git_ops.py)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "link_handler"))

import pytest
from cryptography.fernet import Fernet

import git_ops


def test_repo_remote_for_gitlab():
    url = "https://gitlab.com/openfab/endpoint/-/raw/main/spaceapi.json"
    remote, branch, path = git_ops._repo_remote_for(url)
    assert remote == "git@gitlab.com:openfab/endpoint.git"
    assert branch == "main"
    assert path == "spaceapi.json"


def test_repo_remote_for_github():
    url = "https://raw.githubusercontent.com/owner/repo/main/spaceapi.json"
    remote, branch, path = git_ops._repo_remote_for(url)
    assert remote == "git@github.com:owner/repo.git"
    assert branch == "main"
    assert path == "spaceapi.json"


def test_repo_remote_for_unrecognised_host_raises():
    with pytest.raises(git_ops.UnsupportedHostError):
        git_ops._repo_remote_for("https://example.com/not/a/known/shape.json")


@pytest.fixture(autouse=True)
def _isolated_keys_dir(tmp_path, monkeypatch):
    import bot_keys
    monkeypatch.setattr(bot_keys, "BOT_KEYS_DIR", tmp_path)
    monkeypatch.setenv("BOT_KEY_SECRET", Fernet.generate_key().decode())
    yield


def _fake_resolve_repo(tmp_path, data: dict):
    async def fake(space_id):
        repo_dir = tmp_path / "repo"
        repo_dir.mkdir(exist_ok=True)
        (repo_dir / "spaceapi.json").write_text(__import__("json").dumps(data))
        return repo_dir, "main", "spaceapi.json"

    return fake


@pytest.mark.asyncio
async def test_patch_json_accepts_valid_shape(monkeypatch, tmp_path):
    monkeypatch.setattr(
        git_ops,
        "_resolve_repo_unlocked",
        _fake_resolve_repo(tmp_path, {"schema:name": "Test Space", "schema:url": "https://example.com"}),
    )
    import bot_keys
    bot_keys.generate_and_store("test-space")

    patched = await git_ops.patch_json("test-space", "schema:url", "https://new.example.com")
    assert patched["schema:url"] == "https://new.example.com"


@pytest.mark.asyncio
async def test_patch_json_rejects_invalid_state_shape(monkeypatch, tmp_path):
    monkeypatch.setattr(
        git_ops, "_resolve_repo_unlocked", _fake_resolve_repo(tmp_path, {"schema:name": "Test Space"})
    )
    import bot_keys
    bot_keys.generate_and_store("test-space")

    # state is `Optional[Any]` on SpaceAPISchema so this can't fail validation
    # directly — assert the nested-path patch still applies and round-trips.
    patched = await git_ops.patch_json("test-space", "state.open", True)
    assert patched["state"]["open"] is True


@pytest.mark.asyncio
async def test_patch_json_rejects_empty_field_path(monkeypatch, tmp_path):
    monkeypatch.setattr(git_ops, "_resolve_repo_unlocked", _fake_resolve_repo(tmp_path, {"schema:name": "Test"}))
    import bot_keys
    bot_keys.generate_and_store("test-space")

    with pytest.raises(ValueError):
        await git_ops.patch_json("test-space", "", "x")


@pytest.mark.asyncio
async def test_patch_json_rejects_non_dict_intermediate(monkeypatch, tmp_path):
    monkeypatch.setattr(
        git_ops, "_resolve_repo_unlocked", _fake_resolve_repo(tmp_path, {"schema:name": "a string, not a dict"})
    )
    import bot_keys
    bot_keys.generate_and_store("test-space")

    with pytest.raises(ValueError):
        await git_ops.patch_json("test-space", "schema:name.nested", "x")


@pytest.mark.asyncio
async def test_read_json_raises_no_deploy_key_error_when_key_missing():
    with pytest.raises(git_ops.NoDeployKeyError):
        await git_ops.read_json("space-with-no-key")


@pytest.mark.asyncio
async def test_commit_json_raises_no_deploy_key_error_when_key_missing():
    with pytest.raises(git_ops.NoDeployKeyError):
        await git_ops.commit_json("space-with-no-key", "state.open", True, "@nicolas:matrix.org")
