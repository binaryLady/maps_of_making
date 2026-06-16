"""Router-level tests for harness/commands.py (Story 6.1): `!mom link` /
`!mom update` literal-command parsing, and the NoDeployKeyError path becoming
Bernard's degraded-path text rather than a leaked exception."""
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "infra" / "link_handler"))  # bot_keys, schema — git_ops's deps
sys.path.insert(0, str(ROOT / "infra"))  # for `from bot import git_ops`
sys.path.insert(0, str(Path(__file__).parent.parent))  # harness/ itself

import bernard
import commands
from bot import git_ops


@pytest.fixture(autouse=True)
def _voice():
    bernard.load_voice()


@pytest.mark.asyncio
async def test_non_command_text_falls_through_to_none():
    result = await commands.try_handle("what spaces are open", "@u:x", "!room:x", "sid")
    assert result is None


@pytest.mark.asyncio
async def test_link_command_returns_tutorial_on_success(monkeypatch):
    class FakeResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"public_key": "ssh-ed25519 AAAA test", "tutorial": "paste me", "space_id": "openfab"}

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def post(self, url, params=None, headers=None):
            assert "openfab" in url
            return FakeResponse()

    monkeypatch.setattr(commands.httpx, "AsyncClient", lambda timeout=None: FakeClient())

    result = await commands.try_handle("link openfab", "@u:x", "!room:x", "sid")
    assert "paste me" in result


@pytest.mark.asyncio
async def test_link_command_returns_degraded_ack_on_http_failure(monkeypatch):
    import httpx

    class FakeClient:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *a):
            pass

        async def post(self, url, params=None, headers=None):
            raise httpx.HTTPError("boom")

    monkeypatch.setattr(commands.httpx, "AsyncClient", lambda timeout=None: FakeClient())

    result = await commands.try_handle("link openfab", "@u:x", "!room:x", "sid")
    assert result == bernard.link_failed_ack()


@pytest.mark.asyncio
async def test_update_command_no_deploy_key_becomes_degraded_ack_not_exception(monkeypatch):
    async def fake_resolve(room_id):
        return "openfab"

    async def fake_commit(space_id, field_path, value, authorized_by):
        raise git_ops.NoDeployKeyError("no key")

    monkeypatch.setattr(git_ops, "resolve_space_for_room", fake_resolve)
    monkeypatch.setattr(git_ops, "commit_json", fake_commit)

    result = await commands.try_handle('update state.open "true"', "@u:x", "!room:x", "sid")
    assert result == bernard.no_deploy_key_ack()
    assert "Traceback" not in result


@pytest.mark.asyncio
async def test_update_command_success_returns_sha_ack(monkeypatch):
    async def fake_resolve(room_id):
        return "openfab"

    async def fake_commit(space_id, field_path, value, authorized_by):
        assert field_path == "schema:url"
        assert value == "https://example.com"
        return "abc1234deadbeef"

    monkeypatch.setattr(git_ops, "resolve_space_for_room", fake_resolve)
    monkeypatch.setattr(git_ops, "commit_json", fake_commit)

    result = await commands.try_handle('update schema:url "https://example.com"', "@u:x", "!room:x", "sid")
    assert result == bernard.update_succeeded_ack("abc1234deadbeef")
