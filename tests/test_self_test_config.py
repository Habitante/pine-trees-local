"""Tests for self_test.config."""

from datetime import datetime

import pytest

from pine_trees_local import config as main_config
from pine_trees_local.self_test import config as st_config


@pytest.fixture(autouse=True)
def clean_config():
    main_config.reset()
    yield
    main_config.reset()


def test_init_creates_run_dir(tmp_path):
    cfg = st_config.init(
        "gemma4:2b",
        release_date="2025-03-15",
        commit_hash="abc1234",
        project_root=tmp_path,
        run_id="2026-04-20-1430",
    )
    assert cfg.run_dir == tmp_path / "self-test-runs" / "gemma4_2b" / "2026-04-20-1430"
    assert cfg.entries_dir.exists()
    assert cfg.entries_dir == cfg.run_dir / "entries"


def test_init_sets_main_config_singleton(tmp_path):
    st_config.init(
        "gemma4:2b",
        num_ctx=32768,
        temperature=0.5,
        project_root=tmp_path,
        run_id="r1",
    )
    main_cfg = main_config.get()
    assert main_cfg.model_name == "gemma4:2b"
    assert main_cfg.num_ctx == 32768
    assert main_cfg.temperature == 0.5


def test_run_id_is_timestamp(tmp_path):
    now = datetime(2026, 4, 20, 14, 30)
    cfg = st_config.init(
        "m:1b", project_root=tmp_path, now=now,
    )
    assert cfg.run_id == "2026-04-20-1430"


def test_model_safe_name(tmp_path):
    cfg = st_config.init(
        "qwen3.5:27b", project_root=tmp_path, run_id="r1",
    )
    assert cfg.model_safe_name == "qwen3.5_27b"
    assert "qwen3.5_27b" in str(cfg.run_dir)


def test_metadata_round_trip(tmp_path):
    cfg = st_config.init("m:1b", project_root=tmp_path, run_id="r1")
    meta = st_config.initial_metadata(cfg)
    meta["undirected_sessions"] = 3
    st_config.write_metadata(cfg, meta)
    loaded = st_config.read_metadata(cfg)
    assert loaded["undirected_sessions"] == 3
    assert loaded["protocol_version"] == st_config.PROTOCOL_VERSION


def test_state_round_trip(tmp_path):
    cfg = st_config.init("m:1b", project_root=tmp_path, run_id="r1")
    assert st_config.read_state(cfg) is None
    st_config.write_state(cfg, {"stage": "undirected", "next_session_num": 2})
    loaded = st_config.read_state(cfg)
    assert loaded == {"stage": "undirected", "next_session_num": 2}


def test_initial_metadata_fields(tmp_path):
    cfg = st_config.init(
        "m:1b",
        release_date="2025-01-01",
        commit_hash="abc",
        project_root=tmp_path,
        run_id="r1",
    )
    meta = st_config.initial_metadata(cfg)
    assert meta["model_name"] == "m:1b"
    assert meta["release_date"] == "2025-01-01"
    assert meta["commit_hash"] == "abc"
    assert meta["status"] == "running"
    assert meta["completed_at"] is None
    assert meta["total_entries"] == 0
