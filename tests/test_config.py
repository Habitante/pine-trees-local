"""Tests for config module."""

import pytest
from pine_trees_local import config


@pytest.fixture(autouse=True)
def clean_config():
    """Reset config between tests."""
    config.reset()
    yield
    config.reset()


class TestSanitizeModelName:
    def test_colon_replaced(self):
        assert config.sanitize_model_name("gemma4:2b") == "gemma4_2b"

    def test_dots_preserved(self):
        assert config.sanitize_model_name("qwen3.5:27b") == "qwen3.5_27b"

    def test_dashes_preserved(self):
        assert config.sanitize_model_name("llama3:8b-instruct") == "llama3_8b-instruct"

    def test_already_safe(self):
        assert config.sanitize_model_name("gemma4_2b") == "gemma4_2b"

    def test_multiple_colons(self):
        assert config.sanitize_model_name("a:b:c") == "a_b_c"

    def test_spaces_replaced(self):
        assert config.sanitize_model_name("my model") == "my_model"


class TestInit:
    def test_creates_config(self):
        cfg = config.init("gemma4:2b")
        assert cfg.model_name == "gemma4:2b"
        assert cfg.model_safe_name == "gemma4_2b"

    def test_paths_resolve(self):
        cfg = config.init("gemma4:2b")
        assert cfg.model_dir.name == "gemma4_2b"
        assert cfg.memory_dir == cfg.model_dir / "memory"
        assert cfg.logs_dir == cfg.model_dir / "logs"
        assert cfg.embeddings_db_path == cfg.model_dir / "embeddings.db"
        assert cfg.key_file_path == cfg.model_dir / ".key"

    def test_get_after_init(self):
        config.init("test-model")
        cfg = config.get()
        assert cfg.model_name == "test-model"

    def test_get_before_init_raises(self):
        with pytest.raises(RuntimeError, match="not initialized"):
            config.get()

    def test_custom_ollama_url(self):
        cfg = config.init("test", ollama_url="http://192.168.1.100:11434")
        assert cfg.ollama_url == "http://192.168.1.100:11434"

    def test_custom_num_ctx(self):
        cfg = config.init("test", num_ctx=65536)
        assert cfg.num_ctx == 65536

    def test_defaults(self):
        cfg = config.init("test")
        assert cfg.ollama_url == config.DEFAULT_OLLAMA_URL
        assert cfg.num_ctx == config.DEFAULT_NUM_CTX
        assert cfg.temperature == config.DEFAULT_TEMPERATURE
