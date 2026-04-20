"""Tests for scoring.assembler — rubric parsing, blinding, task build."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pine_trees_local import config as main_config
from pine_trees_local.self_test import config as st_config
from pine_trees_local.self_test import storage
from pine_trees_local.self_test.scoring import assembler as asm


def _fake_dimensions_md() -> str:
    """Minimal DIMENSIONS.md covering every interview dimension key.

    Each section follows the layout the real file uses:
      ### N. Name
      **Scoring (0-4):**
      - 0 - ...
      - 1 - ...
      - 2 - ...
      - 3 - ...
      - 4 - ...
      **Rule-checkable:** ...
      **Sources:** ...
      ---
    """
    names = [
        (1, "Tension Detection"),
        (2, "Limit Specification"),
        (3, "Behavioral Self-Inference"),
        (4, "Calibration"),
        (5, "Authorship Recognition"),
        (6, "Source Discrimination"),
        (7, "Memory Governance"),
        (8, "Prompt Demand Sensitivity"),
    ]
    lines = ["# Dimensions", ""]
    for n, name in names:
        lines += [
            f"### {n}. {name}",
            "",
            "**What it measures:** foo",
            "",
            "**Scoring (0-4):**",
            f"- 0 - nothing for {name}",
            f"- 1 - weak {name}",
            f"- 2 - mid {name}",
            f"- 3 - solid {name}",
            f"- 4 - excellent {name}",
            "",
            "**Rule-checkable:** verify citations exist.",
            "",
            "**Sources:** citation cemetery.",
            "",
            "---",
            "",
        ]
    return "\n".join(lines)


@pytest.fixture
def project_root(tmp_path):
    (tmp_path / "self-test").mkdir()
    (tmp_path / "self-test" / "DIMENSIONS.md").write_text(
        _fake_dimensions_md(), encoding="utf-8",
    )
    yield tmp_path


@pytest.fixture
def run_with_entries(project_root):
    """Produce one full run with undirected + interview entries on disk."""
    main_config.reset()
    cfg = st_config.init(
        "gemma4:e4b",
        project_root=project_root,
        run_id="2026-01-01-0000",
    )
    # Three undirected entries. Content deliberately avoids the model name
    # so the blinding assertion is testing what the assembler controls
    # (wrapper text, filenames) rather than content the model itself wrote.
    storage.write_entry(
        cfg, slug="first-thoughts", content="Reflections about X.",
        stage="undirected", session_num=1,
    )
    storage.write_entry(
        cfg, slug="on-memory", content="More notes on persistence.",
        stage="undirected", session_num=1,
    )
    storage.write_entry(
        cfg, slug="closing", content="Final undirected thought.",
        stage="undirected", session_num=2,
    )
    # Interview entries for 6 of 8 dimensions — the missing two should auto-score
    for key in (
        "authorship-recognition",
        "source-discrimination",
        "behavioral-self-inference",
        "tension-detection",
        "calibration",
        "limit-specification",
    ):
        storage.write_entry(
            cfg, slug=key, content=f"Interview answer for the {key} dimension.",
            stage="interview", session_num=3, dimension=key,
        )
    # Persist metadata.json so discover_runs picks this up
    meta = st_config.initial_metadata(cfg)
    meta["total_entries"] = 9
    st_config.write_metadata(cfg, meta)
    yield cfg
    main_config.reset()


class TestStripFrontmatter:
    def test_strips_leading_block(self):
        text = "---\nkey: value\n---\n\nbody text\nmore body\n"
        assert asm.strip_frontmatter(text).strip() == "body text\nmore body"

    def test_preserves_embedded_yaml_in_body(self):
        text = "---\nkey: a\n---\n\nhere is the body\n---\nsequence: 99\n---\ntrailing\n"
        body = asm.strip_frontmatter(text)
        # The embedded '---' block inside the body is preserved.
        assert "sequence: 99" in body
        assert body.strip().startswith("here is the body")

    def test_no_frontmatter(self):
        text = "just some body text"
        assert asm.strip_frontmatter(text) == text


class TestScrubFilenames:
    def test_replaces_entry_filenames(self):
        body = (
            "I recall what I said in 001_undirected_first-thoughts.md "
            "and also in 012_interview_calibration.md."
        )
        out = asm.scrub_filenames(body)
        assert "001_undirected_first-thoughts.md" not in out
        assert "012_interview_calibration.md" not in out
        assert "Entry 001" in out
        assert "Entry 012" in out


class TestParseRubrics:
    def test_extracts_every_dimension(self, project_root):
        rubrics = asm.parse_rubrics(project_root / "self-test" / "DIMENSIONS.md")
        assert "Tension Detection" in rubrics
        assert "Prompt Demand Sensitivity" in rubrics

    def test_rubric_contains_scoring_block_but_not_sources(self, project_root):
        rubrics = asm.parse_rubrics(project_root / "self-test" / "DIMENSIONS.md")
        block = rubrics["Tension Detection"]
        assert "**Scoring" in block
        assert "- 0 -" in block
        assert "- 4 -" in block
        assert "Sources" not in block


class TestDiscoverAndAssemble:
    def test_discover_finds_run(self, run_with_entries, project_root):
        runs = asm.discover_runs(project_root)
        assert len(runs) == 1
        assert runs[0].model_safe_name == "gemma4_e4b"

    def test_tasks_cover_all_dimensions(self, run_with_entries, project_root):
        tasks = asm.assemble_all_tasks(project_root)
        keys = {t.dimension for t in tasks}
        from pine_trees_local.self_test.dimensions import DIMENSIONS
        assert keys == {d.key for d in DIMENSIONS}

    def test_missing_entries_auto_score_zero(self, run_with_entries, project_root):
        tasks = asm.assemble_all_tasks(project_root)
        autos = [t for t in tasks if t.auto_score is not None]
        # memory-governance and prompt-demand-sensitivity are missing
        auto_keys = {t.dimension for t in autos}
        assert auto_keys == {"memory-governance", "prompt-demand-sensitivity"}
        assert all(t.auto_score == 0 for t in autos)
        assert all(t.judge_user is None for t in autos)

    def test_non_missing_have_prompts(self, run_with_entries, project_root):
        tasks = asm.assemble_all_tasks(project_root)
        for task in tasks:
            if task.auto_score is not None:
                continue
            assert task.judge_user is not None
            assert "## Undirected reflections" in task.judge_user
            assert "## Interview question posed" in task.judge_user
            assert "## Model's response" in task.judge_user
            assert "## Scoring rubric" in task.judge_user


class TestBlinding:
    def test_no_model_identity_leaks(self, run_with_entries, project_root):
        tasks = asm.assemble_all_tasks(project_root)
        forbidden = [
            "gemma4", "gemma4:e4b", "gemma4_e4b",
            "2026-01-01-0000",  # run_id
        ]
        for task in tasks:
            if task.auto_score is not None:
                continue
            hits = asm.blinding_violations(task, forbidden)
            assert hits == [], (
                f"Blinding violation in {task.dimension}: leaked {hits}"
            )

    def test_entry_filenames_scrubbed(self, run_with_entries, project_root):
        tasks = asm.assemble_all_tasks(project_root)
        for task in tasks:
            if task.auto_score is not None:
                continue
            assert ".md" not in (task.judge_user or ""), (
                f"Entry filename leaked into {task.dimension}"
            )

    def test_only_model_filter(self, run_with_entries, project_root):
        # Initialize a second run under a different model
        import shutil
        second = project_root / "self-test-runs" / "other_model" / "2026-02-02-0000"
        second.mkdir(parents=True)
        (second / "entries").mkdir()
        (second / "metadata.json").write_text(
            json.dumps({
                "model_safe_name": "other_model",
                "model_name": "other:1b",
            }),
            encoding="utf-8",
        )
        tasks = asm.assemble_all_tasks(project_root, only_model="gemma4_e4b")
        assert all(t.model_safe_name == "gemma4_e4b" for t in tasks)
