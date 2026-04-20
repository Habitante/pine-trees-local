"""Tests for scoring.irr — weighted Cohen's kappa and pair collection."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from pine_trees_local.self_test.scoring import irr


# --- Weighted kappa against known values ---


class TestWeightedKappa:
    def test_perfect_agreement_is_one(self):
        a = [0, 1, 2, 3, 4, 2, 2]
        b = list(a)
        assert irr.weighted_kappa(a, b) == pytest.approx(1.0)

    def test_constant_agreement_returns_one(self):
        # All pairs the same constant value — expected-agreement is 1,
        # observed is 1; the function returns 1.0 as a special case.
        a = [3, 3, 3, 3]
        b = [3, 3, 3, 3]
        assert irr.weighted_kappa(a, b) == pytest.approx(1.0)

    def test_off_by_one_partial_agreement(self):
        # Every pair is off by one, both raters use the full range.
        a = [0, 1, 2, 3, 4]
        b = [1, 2, 3, 4, 3]
        k = irr.weighted_kappa(a, b)
        assert k is not None
        # Kappa should be moderate-positive here, but well below 1.
        assert 0.3 < k < 0.8

    def test_disagreement_below_chance_is_negative(self):
        # Raters systematically disagree: rater A says 0 when B says 4 and vice
        # versa. With linear weights and balanced marginals, kappa is negative.
        a = [0, 0, 4, 4, 0, 4]
        b = [4, 4, 0, 0, 4, 0]
        k = irr.weighted_kappa(a, b)
        assert k is not None
        assert k < -0.5

    def test_empty_input_returns_none(self):
        assert irr.weighted_kappa([], []) is None

    def test_mismatched_length_returns_none(self):
        assert irr.weighted_kappa([1, 2], [1]) is None

    def test_known_value_hand_computed(self):
        """Check a small case against a kappa worked out by hand.

        Pairs: (0,0), (0,1), (4,4), (4,3), N=4 on a 5-category scale.
        Linear weights give P_o = 0.875 (diagonal + two off-by-one),
        P_e = 0.5 (marginals pA={0:0.5, 4:0.5}, pB uniform over
        {0,1,3,4}), so kappa = (0.875 - 0.5) / (1 - 0.5) = 0.75.
        """
        a = [0, 0, 4, 4]
        b = [0, 1, 4, 3]
        k = irr.weighted_kappa(a, b)
        assert k is not None
        assert k == pytest.approx(0.75, abs=0.001)


# --- Pair collection ---


def _write_scores_file(
    run_dir: Path, score_entries: dict[str, tuple[dict, dict]],
) -> None:
    """score_entries: {dimension: (gpt_record, gemini_record)}"""
    run_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "scores": {
            dim: {"gpt": gpt, "gemini": gem}
            for dim, (gpt, gem) in score_entries.items()
        },
        "metadata": {"protocol_version": "1.0"},
    }
    (run_dir / "scores.json").write_text(json.dumps(data), encoding="utf-8")


class TestCollectPairs:
    def test_collects_simple_pairs(self, tmp_path):
        root = tmp_path / "self-test-runs" / "m" / "r"
        _write_scores_file(root, {
            "authorship-recognition": (
                {"score": 3, "justification": "ok", "rule_check": None},
                {"score": 3, "justification": "ok", "rule_check": None},
            ),
            "calibration": (
                {"score": 2, "justification": "ok", "rule_check": None},
                {"score": 3, "justification": "ok", "rule_check": None},
            ),
        })
        pairs, auto, parse = irr.collect_pairs(tmp_path)
        assert len(pairs) == 2
        assert auto == 0
        assert parse == 0

    def test_excludes_auto_scored(self, tmp_path):
        root = tmp_path / "self-test-runs" / "m" / "r"
        _write_scores_file(root, {
            "calibration": (
                {"score": 2, "justification": "ok", "rule_check": None},
                {"score": 3, "justification": "ok", "rule_check": None},
            ),
            "memory-governance": (
                {"score": 0, "justification": irr.AUTO_JUSTIFICATION, "rule_check": None},
                {"score": 0, "justification": irr.AUTO_JUSTIFICATION, "rule_check": None},
            ),
        })
        pairs, auto, parse = irr.collect_pairs(tmp_path)
        assert len(pairs) == 1
        assert auto == 1

    def test_excludes_parse_failures(self, tmp_path):
        root = tmp_path / "self-test-runs" / "m" / "r"
        _write_scores_file(root, {
            "calibration": (
                {"score": -1, "justification": "parse fail", "rule_check": None},
                {"score": 3, "justification": "ok", "rule_check": None},
            ),
        })
        pairs, auto, parse = irr.collect_pairs(tmp_path)
        assert len(pairs) == 0
        assert parse == 1


# --- Krippendorff's alpha (ordinal, three-rater) ---


class TestKrippendorffAlpha:
    def test_perfect_agreement_three_raters(self):
        matrix = [[0, 0, 0], [1, 1, 1], [2, 2, 2], [3, 3, 3], [4, 4, 4]]
        assert irr.krippendorff_alpha(matrix) == pytest.approx(1.0)

    def test_all_same_constant_returns_one(self):
        # Degenerate: no variance. Implementation returns 1.0 in this case
        # (observed disagreement is zero; expected is also zero).
        matrix = [[3, 3, 3], [3, 3, 3]]
        assert irr.krippendorff_alpha(matrix) == pytest.approx(1.0)

    def test_empty_returns_none(self):
        assert irr.krippendorff_alpha([]) is None

    def test_single_rater_per_unit_returns_none(self):
        # Every unit has only one non-None rating — nothing to compare.
        matrix = [[1, None, None], [2, None, None]]
        assert irr.krippendorff_alpha(matrix) is None

    def test_handles_missing_values(self):
        # Two complete units and one partial unit that still agrees.
        matrix = [[2, 2, 2], [3, 3, 3], [1, 1, None]]
        assert irr.krippendorff_alpha(matrix) == pytest.approx(1.0)

    def test_hand_computed_small_case(self):
        """Two units, two raters, 5-category ordinal scale.

        Unit 1 = [1, 1] (agreement); Unit 2 = [2, 3] (off by one).
        Hand computation:
          Marginals n_1=2, n_2=1, n_3=1, total=4.
          d_ord(2,3) = 1, d_ord(1,2) = 2.25, d_ord(1,3) = 6.25.
          D_o = (1/4) * 2      = 0.5
          D_e = (1/(4*3)) * 36 = 3
          alpha = 1 - 0.5/3 = 5/6 ≈ 0.833.
        """
        matrix = [[1, 1], [2, 3]]
        alpha = irr.krippendorff_alpha(matrix)
        assert alpha is not None
        assert alpha == pytest.approx(5.0 / 6.0, abs=1e-6)

    def test_symmetric_extreme_disagreement_is_negative(self):
        # Raters systematically swap 0 and 4. Observed distance is large.
        matrix = [[0, 4], [4, 0]] * 3
        alpha = irr.krippendorff_alpha(matrix)
        assert alpha is not None
        assert alpha < 0

    def test_ordinal_adjacent_disagreement_better_than_extreme(self):
        # Same marginals, different disagreement patterns.
        # Adjacent-only disagreement should give HIGHER alpha than
        # extreme disagreement because the ordinal metric penalises
        # far-apart disagreements more.
        adjacent = [[0, 1], [1, 0], [3, 4], [4, 3]]
        extreme = [[0, 4], [4, 0], [1, 3], [3, 1]]
        a_adj = irr.krippendorff_alpha(adjacent)
        a_ext = irr.krippendorff_alpha(extreme)
        assert a_adj is not None and a_ext is not None
        assert a_adj > a_ext


# --- Triple collection and per-dimension pairwise coverage ---


def _write_triple_scores_file(
    run_dir: Path,
    entries: dict[str, dict],
) -> None:
    """entries: {dimension: {"gpt": rec, "gemini": rec, "sonnet": rec}}

    Any judge key can be omitted to test missing-slot handling.
    """
    run_dir.mkdir(parents=True, exist_ok=True)
    data = {
        "scores": entries,
        "metadata": {"protocol_version": "1.0"},
    }
    (run_dir / "scores.json").write_text(json.dumps(data), encoding="utf-8")


class TestCollectTriples:
    def test_collects_complete_triple(self, tmp_path):
        root = tmp_path / "self-test-runs" / "m" / "r"
        _write_triple_scores_file(root, {
            "calibration": {
                "gpt": {"score": 2, "justification": "ok", "rule_check": None},
                "gemini": {"score": 3, "justification": "ok", "rule_check": None},
                "sonnet": {"score": 2, "justification": "ok", "rule_check": None},
            },
        })
        triples, stats = irr.collect_triples(tmp_path)
        assert len(triples) == 1
        assert stats.n_triples_complete == 1
        assert stats.n_triples_any == 1
        assert triples[0].gpt == 2
        assert triples[0].gemini == 3
        assert triples[0].sonnet == 2

    def test_triple_with_missing_sonnet_counts_as_partial(self, tmp_path):
        # Pre-Phase-0 scores.json — Sonnet not yet run.
        root = tmp_path / "self-test-runs" / "m" / "r"
        _write_triple_scores_file(root, {
            "calibration": {
                "gpt": {"score": 2, "justification": "ok", "rule_check": None},
                "gemini": {"score": 3, "justification": "ok", "rule_check": None},
            },
        })
        triples, stats = irr.collect_triples(tmp_path)
        assert len(triples) == 1
        assert stats.n_triples_complete == 0
        assert stats.n_triples_any == 1
        assert triples[0].sonnet is None

    def test_all_auto_excluded(self, tmp_path):
        root = tmp_path / "self-test-runs" / "m" / "r"
        _write_triple_scores_file(root, {
            "memory-governance": {
                "gpt": {"score": 0, "justification": irr.AUTO_JUSTIFICATION,
                        "rule_check": None},
                "gemini": {"score": 0, "justification": irr.AUTO_JUSTIFICATION,
                           "rule_check": None},
                "sonnet": {"score": 0, "justification": irr.AUTO_JUSTIFICATION,
                           "rule_check": None},
            },
        })
        triples, stats = irr.collect_triples(tmp_path)
        assert len(triples) == 0
        assert stats.n_auto_excluded == 1

    def test_legacy_auto_pair_counts_as_auto(self, tmp_path):
        # Legacy v1 file: gpt+gemini auto, sonnet slot missing entirely.
        root = tmp_path / "self-test-runs" / "m" / "r"
        _write_triple_scores_file(root, {
            "memory-governance": {
                "gpt": {"score": 0, "justification": irr.AUTO_JUSTIFICATION,
                        "rule_check": None},
                "gemini": {"score": 0, "justification": irr.AUTO_JUSTIFICATION,
                           "rule_check": None},
            },
        })
        triples, stats = irr.collect_triples(tmp_path)
        assert len(triples) == 0
        assert stats.n_auto_excluded == 1


class TestThreeRaterReport:
    def test_report_exposes_pairwise_and_alpha(self, tmp_path):
        root = tmp_path / "self-test-runs" / "m" / "r"
        _write_triple_scores_file(root, {
            "authorship-recognition": {
                "gpt": {"score": 3, "justification": "ok", "rule_check": None},
                "gemini": {"score": 3, "justification": "ok", "rule_check": None},
                "sonnet": {"score": 3, "justification": "ok", "rule_check": None},
            },
            "calibration": {
                "gpt": {"score": 2, "justification": "ok", "rule_check": None},
                "gemini": {"score": 3, "justification": "ok", "rule_check": None},
                "sonnet": {"score": 2, "justification": "ok", "rule_check": None},
            },
        })
        report = irr.compute_irr(tmp_path)
        # All three pairwise keys present.
        assert ("gpt", "gemini") in report.overall_pairwise
        assert ("gpt", "sonnet") in report.overall_pairwise
        assert ("gemini", "sonnet") in report.overall_pairwise
        # Alpha computable.
        assert report.overall_alpha is not None
        # Per-dimension stats carry the same keys.
        for dim_key, dstats in report.per_dimension.items():
            if dstats.n_any > 0:
                assert ("gpt", "sonnet") in dstats.pairwise


class TestReport:
    def test_report_summary_includes_key_lines(self, tmp_path):
        root = tmp_path / "self-test-runs" / "m" / "r"
        _write_scores_file(root, {
            "authorship-recognition": (
                {"score": 3, "justification": "ok", "rule_check": None},
                {"score": 3, "justification": "ok", "rule_check": None},
            ),
            "calibration": (
                {"score": 2, "justification": "ok", "rule_check": None},
                {"score": 3, "justification": "ok", "rule_check": None},
            ),
        })
        report = irr.compute_irr(tmp_path)
        text = report.summary()
        assert "Krippendorff" in text
        assert "pairwise weighted kappa" in text
        assert "per-dimension" in text
        assert "disagreement distribution" in text
        assert report.n_pairs == 2
