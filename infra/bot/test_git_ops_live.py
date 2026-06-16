"""Live integration test for git_ops.py (Story 6.1 Task 7) — exercises the
full clone/patch/commit/push cycle against a real (throwaway, local) bare git
repo served over SSH, per project convention (mocks hide protocol bugs — see
memory feedback_integration_testing). Kept hermetic by running our own local
sshd on a random high port rather than touching a real GitLab account.

_repo_remote_for's URL-pattern parsing (GitLab/GitHub/Gitea) is unit-tested
separately in test_git_ops.py — here we monkeypatch it to point at the local
sshd so this test doesn't depend on internet access.

Skips cleanly if no local sshd binary is available (e.g. minimal CI images).
"""
import shutil
import socket
import subprocess
import sys
import time
from pathlib import Path

import pytest
from cryptography.fernet import Fernet

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent / "link_handler"))

import bot_keys
import git_ops

SSHD_BIN = shutil.which("sshd") or "/usr/sbin/sshd"

pytestmark = pytest.mark.network


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def local_ssh_repo(tmp_path, monkeypatch):
    if not Path(SSHD_BIN).exists():
        pytest.skip("no local sshd binary available — skipping live SSH integration test")

    monkeypatch.setattr(bot_keys, "BOT_KEYS_DIR", tmp_path / "bot-keys")
    monkeypatch.setenv("BOT_KEY_SECRET", Fernet.generate_key().decode())
    monkeypatch.setattr(git_ops, "BOT_REPOS_DIR", tmp_path / "bot-repos")

    space_id = "live-test-space"
    public_key, _tutorial = bot_keys.generate_and_store(space_id)

    bare_repo = tmp_path / "repo.git"
    subprocess.run(["git", "init", "--bare", "-q", "-b", "main", str(bare_repo)], check=True)

    seed_dir = tmp_path / "seed"
    seed_dir.mkdir()
    (seed_dir / "spaceapi.json").write_text(
        '{"schema:name": "Live Test Space", "schema:url": "https://example.com"}\n'
    )
    subprocess.run(["git", "init", "-q", "-b", "main", str(seed_dir)], check=True)
    subprocess.run(["git", "-C", str(seed_dir), "add", "."], check=True)
    subprocess.run(
        ["git", "-C", str(seed_dir), "-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "-m", "seed"],
        check=True,
    )
    subprocess.run(["git", "-C", str(seed_dir), "push", "-q", str(bare_repo), "main"], check=True)

    hostkey = tmp_path / "hostkey"
    subprocess.run(["ssh-keygen", "-q", "-t", "ed25519", "-f", str(hostkey), "-N", ""], check=True)
    authorized_keys = tmp_path / "authorized_keys"
    authorized_keys.write_text(public_key + "\n")

    port = _free_port()
    sshd_config = tmp_path / "sshd_config"
    sshd_config.write_text(
        f"Port {port}\n"
        f"HostKey {hostkey}\n"
        f"AuthorizedKeysFile {authorized_keys}\n"
        f"ListenAddress 127.0.0.1\n"
        f"UsePAM no\nStrictModes no\nPasswordAuthentication no\n"
    )

    proc = subprocess.Popen([SSHD_BIN, "-f", str(sshd_config), "-D"])
    time.sleep(0.5)
    if proc.poll() is not None:
        pytest.skip("local sshd failed to start — skipping live SSH integration test")

    import getpass
    ssh_remote = f"ssh://{getpass.getuser()}@127.0.0.1:{port}{bare_repo}"

    async def fake_lookup_endpoint_url(sid):
        return "https://example.com/fake/spaceapi.json"

    monkeypatch.setattr(git_ops, "_lookup_endpoint_url", fake_lookup_endpoint_url)
    monkeypatch.setattr(git_ops, "_repo_remote_for", lambda url: (ssh_remote, "main", "spaceapi.json"))

    try:
        yield space_id, bare_repo
    finally:
        proc.terminate()
        proc.wait(timeout=5)


@pytest.mark.asyncio
async def test_read_patch_commit_push_cycle_over_ssh(local_ssh_repo):
    space_id, bare_repo = local_ssh_repo

    data = await git_ops.read_json(space_id)
    assert data["schema:name"] == "Live Test Space"

    patched = await git_ops.patch_json(space_id, "schema:url", "https://updated.example.com")
    assert patched["schema:url"] == "https://updated.example.com"

    sha = await git_ops.commit_json(space_id, "schema:url", "https://updated.example.com", "@nicolas:matrix.org")
    assert sha

    verify_dir = bare_repo.parent / "verify"
    subprocess.run(["git", "clone", "-q", str(bare_repo), str(verify_dir)], check=True)
    pushed = (verify_dir / "spaceapi.json").read_text()
    assert "https://updated.example.com" in pushed

    log = subprocess.run(
        ["git", "-C", str(verify_dir), "log", "-1", "--pretty=%s"], capture_output=True, text=True, check=True
    )
    assert "authorized by @nicolas:matrix.org" in log.stdout
