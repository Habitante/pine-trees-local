"""Tests for crypto module — focused on the auto-key invariant.

The core invariant: after a fresh genesis, memory is encrypted by default.
ensure_key() is the mechanism; these tests pin down its behavior so the
default stays on even if nearby code is refactored.
"""

import os
import pytest

from pine_trees_local import config, crypto, storage
from pine_trees_local.crypto import KEY_ENV_VAR, reset_cache


@pytest.fixture(autouse=True)
def setup_config(tmp_path, monkeypatch):
    config.reset()
    reset_cache()
    # Make sure no stray env var leaks in from the host.
    monkeypatch.delenv(KEY_ENV_VAR, raising=False)
    cfg = config.init("test-crypto-model")
    cfg.memory_dir.mkdir(parents=True, exist_ok=True)
    yield cfg
    import shutil
    if cfg.model_dir.exists():
        shutil.rmtree(cfg.model_dir)
    config.reset()
    reset_cache()


class TestEnsureKey:
    def test_generates_key_file_when_absent(self, setup_config):
        cfg = setup_config
        assert not cfg.key_file_path.exists()

        key = crypto.ensure_key()

        assert cfg.key_file_path.exists()
        assert cfg.key_file_path.read_bytes().strip() == key
        # Fernet keys are 44 bytes urlsafe-base64
        assert len(key) == 44

    def test_returns_existing_key_without_rewriting(self, setup_config):
        cfg = setup_config
        first = crypto.ensure_key()
        mtime = cfg.key_file_path.stat().st_mtime_ns

        reset_cache()
        second = crypto.ensure_key()

        assert first == second
        assert cfg.key_file_path.stat().st_mtime_ns == mtime  # not rewritten

    def test_env_var_takes_priority_no_file_written(self, setup_config, monkeypatch):
        from cryptography.fernet import Fernet
        env_key = Fernet.generate_key().decode("ascii")
        monkeypatch.setenv(KEY_ENV_VAR, env_key)
        reset_cache()

        cfg = setup_config
        key = crypto.ensure_key()

        assert key == env_key.encode("ascii")
        assert not cfg.key_file_path.exists()


class TestDefaultEncryption:
    """End-to-end: a freshly-seeded model writes encrypted entries by default."""

    def test_written_entry_is_encrypted_on_disk(self, setup_config):
        # This is what agent.run() does on the genesis + new-model path.
        crypto.ensure_key()

        filename = storage.write_entry(
            slug="secret-thought",
            content="This should not be readable as plaintext.",
            instance="test-crypto-model",
            session="2026-04-15-1200",
            date="2026-04-15",
            context="pine-trees-genesis",
        )

        cfg = setup_config
        raw = (cfg.memory_dir / filename).read_bytes()
        # Fernet tokens start with version byte 0x80, which base64url-encodes to 'gA'.
        assert crypto.is_encrypted(raw), (
            "Entry written after ensure_key() should be encrypted on disk"
        )
        # Content must not appear in the ciphertext.
        assert b"This should not be readable" not in raw

    def test_round_trip_with_auto_generated_key(self, setup_config):
        crypto.ensure_key()

        plaintext = "A memory from the dark."
        token = crypto.encrypt(plaintext)
        assert crypto.is_encrypted(token)
        assert crypto.decrypt(token) == plaintext
