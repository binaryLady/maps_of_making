"""Deploy-key generation and storage for the bot's write path (Story 6.1).

One ed25519 keypair per space, stored under BOT_KEYS_DIR (default
data/bot-keys/, bind-mounted into both mak-link-handler — read/write, this
module generates keys — and mak-agent-bot — read-only, infra/bot/git_ops.py
decrypts the private key for SSH git operations). The private key is
Fernet-encrypted at rest with BOT_KEY_SECRET, shared verbatim across both
containers (mismatched secrets silently break decryption — see Dev Notes).
"""
import os
from pathlib import Path

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519

BOT_KEYS_DIR = Path(os.environ.get("BOT_KEYS_DIR", "/app/bot-keys"))

TUTORIAL_TEMPLATE = """Here's your deploy key for `{space_id}`. Paste the line below into your \
repo's **Settings → Repository → Deploy Keys**, give it a title, and enable **Write access**:

```
{public_key}
```

1. Open your repo on GitLab and go to Settings → Repository → Deploy Keys.
2. Click "Add new deploy key" and paste the line above into the "Key" field.
3. Check "Write access allowed".
4. Click "Add key" — that's it, I can read and write your endpoint JSON now.
"""


def _key_path(space_id: str) -> Path:
    return BOT_KEYS_DIR / f"{space_id}.key"


def _pub_path(space_id: str) -> Path:
    return BOT_KEYS_DIR / f"{space_id}.pub"


def key_exists(space_id: str) -> bool:
    return _key_path(space_id).exists()


def generate_and_store(space_id: str) -> tuple[str, str]:
    """Generate an ed25519 keypair for space_id, encrypt+store the private key,
    write the plaintext public key, and return (public_key_openssh, tutorial_markdown)."""
    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    pub_openssh = public_key.public_bytes(
        encoding=serialization.Encoding.OpenSSH,
        format=serialization.PublicFormat.OpenSSH,
    ).decode() + " bernard@mapsofmaking"

    priv_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )

    fernet = Fernet(os.environ["BOT_KEY_SECRET"].encode())
    encrypted = fernet.encrypt(priv_pem)

    BOT_KEYS_DIR.mkdir(parents=True, exist_ok=True)
    _key_path(space_id).write_bytes(encrypted)
    _pub_path(space_id).write_text(pub_openssh + "\n")

    tutorial = TUTORIAL_TEMPLATE.format(space_id=space_id, public_key=pub_openssh)
    return pub_openssh, tutorial


def load_private_key(space_id: str) -> bytes:
    """Decrypt and return the PKCS8 PEM private key bytes for space_id.
    Raises FileNotFoundError if no key is stored, cryptography.fernet.InvalidToken
    if BOT_KEY_SECRET doesn't match the one used to encrypt it (fails loudly, not silently)."""
    encrypted = _key_path(space_id).read_bytes()
    fernet = Fernet(os.environ["BOT_KEY_SECRET"].encode())
    return fernet.decrypt(encrypted)
