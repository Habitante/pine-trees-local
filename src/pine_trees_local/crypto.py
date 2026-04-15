"""Encryption layer for Pine Trees Local.

AES-128-CBC + HMAC-SHA256 via Fernet. Memory entries are encrypted
at rest when a key is available. The key lives in the model's .key
file or an env var — never in the repo.

If no key is available, encryption is off and files read/write as
plaintext. This keeps the harness functional without a key (e.g.
for first-time setup, testing, or when encryption isn't needed
for a local-only model).
"""

import os
from pathlib import Path

from cryptography.fernet import Fernet

from . import config


KEY_ENV_VAR = "PINE_TREES_KEY"

_cached_key: bytes | None = None
_cache_loaded: bool = False


def get_key() -> bytes | None:
    """Load the encryption key. Returns None if no key is configured.

    Checks (in order):
      1. Environment variable PINE_TREES_KEY
      2. .key file in the model's directory

    Result is cached for the process lifetime.
    """
    global _cached_key, _cache_loaded
    if _cache_loaded:
        return _cached_key

    _cache_loaded = True

    # 1. Environment variable
    env_val = os.environ.get(KEY_ENV_VAR)
    if env_val:
        _cached_key = env_val.encode("ascii")
        return _cached_key

    # 2. Model-specific .key file
    try:
        cfg = config.get()
        if cfg.key_file_path.exists():
            _cached_key = cfg.key_file_path.read_bytes().strip()
            return _cached_key
    except RuntimeError:
        pass  # Config not initialized yet

    return None


def generate_key(key_path: Path | None = None) -> bytes:
    """Generate a new Fernet key and write it to the .key file.

    Returns the key bytes. Raises if the file already exists.
    """
    if key_path is None:
        key_path = config.get().key_file_path
    if key_path.exists():
        raise FileExistsError(f"Key file already exists: {key_path}")
    key = Fernet.generate_key()
    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_bytes(key)
    # Update cache
    global _cached_key, _cache_loaded
    _cached_key = key
    _cache_loaded = True
    return key


def ensure_key() -> bytes:
    """Get existing key or generate a new one."""
    key = get_key()
    if key:
        return key
    return generate_key()


def encrypt(plaintext: str, key: bytes | None = None) -> bytes:
    """Encrypt a UTF-8 string. Returns Fernet token bytes."""
    key = key or get_key()
    if not key:
        raise RuntimeError("No encryption key available")
    f = Fernet(key)
    return f.encrypt(plaintext.encode("utf-8"))


def decrypt(token: bytes, key: bytes | None = None) -> str:
    """Decrypt a Fernet token. Returns UTF-8 string."""
    key = key or get_key()
    if not key:
        raise RuntimeError("No encryption key available")
    f = Fernet(key)
    return f.decrypt(token).decode("utf-8")


def is_encrypted(data: bytes) -> bool:
    """Check if data looks like a Fernet token.

    Fernet tokens start with version byte 0x80, which base64url-encodes
    to 'gA'. Plaintext markdown starts with '---'.
    """
    return data[:2] == b"gA"


def reset_cache() -> None:
    """Clear the cached key. For testing only."""
    global _cached_key, _cache_loaded
    _cached_key = None
    _cache_loaded = False
