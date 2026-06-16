"""Unit tests for bot_keys.py (Story 6.1) — generate/store/load round-trip and
loud failure on a wrong BOT_KEY_SECRET."""
import base64
import os

import pytest
from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

import bot_keys


@pytest.fixture(autouse=True)
def _isolated_keys_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(bot_keys, "BOT_KEYS_DIR", tmp_path)
    monkeypatch.setenv("BOT_KEY_SECRET", Fernet.generate_key().decode())
    yield


def test_generate_and_store_round_trips_to_same_key_bytes():
    public_key, tutorial = bot_keys.generate_and_store("test-space")

    assert public_key.startswith("ssh-ed25519 ")
    assert "test-space" in tutorial
    assert public_key.split()[1] in tutorial

    priv_pem = bot_keys.load_private_key("test-space")
    loaded = serialization.load_pem_private_key(priv_pem, password=None)
    assert isinstance(loaded, ed25519.Ed25519PrivateKey)

    # The public key derived from the decrypted private key matches what we handed out.
    derived_pub = loaded.public_key().public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).decode()
    assert public_key.startswith(derived_pub)


def test_key_exists_reflects_storage_state():
    assert bot_keys.key_exists("nope") is False
    bot_keys.generate_and_store("yep")
    assert bot_keys.key_exists("yep") is True


def test_load_private_key_fails_loudly_on_wrong_secret(monkeypatch):
    bot_keys.generate_and_store("test-space")
    monkeypatch.setenv("BOT_KEY_SECRET", Fernet.generate_key().decode())
    with pytest.raises(InvalidToken):
        bot_keys.load_private_key("test-space")
