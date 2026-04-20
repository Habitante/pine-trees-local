"""Inter-rater reliability: linear-weighted Cohen's kappa.

Collects paired GPT/Gemini scores across every ``scores.json`` under
``self-test-runs/``, drops auto-scored pairs (missing interview entries)
and any parse failures (score == -1), then computes:

  - overall weighted kappa
  - per-dimension weighted kappa
  - raw agreement distribution (delta 0..4)

Implemented from scratch — no scipy.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..config import self_test_root
from ..dimensions import DIMENSIONS


N_CATEGORIES = 5          # scores are 0..4
AUTO_JUSTIFICATION = "No response produced."


@dataclass
class Pair:
    model_safe_name: str
    dimension: str
    gpt: int
    gemini: int


@dataclass
class IRRReport:
    overall_kappa: float | None
    per_dimension_kappa: dict[str, float | None]
    n_pairs: int
    n_auto_excluded: int
    n_parse_failure_excluded: int
    disagreement_distribution: dict[int, int] = field(default_factory=dict)

    def summary(self) -> str:
        lines = ["## IRR summary"]
        if self.overall_kappa is None:
            lines.append("overall: (no valid pairs)")
        else:
            lines.append(
                f"overall weighted kappa: {self.overall_kappa:.3f}  "
                f"(n={self.n_pairs})"
            )
        lines.append(
            f"excluded: {self.n_auto_excluded} auto-scored, "
            f"{self.n_parse_failure_excluded} parse failures"
        )
        lines.append("")
        lines.append("per-dimension kappa:")
        for key, kappa in self.per_dimension_kappa.items():
            if kappa is None:
                lines.append(f"  {key:<32} (no valid pairs)")
            else:
                lines.append(f"  {key:<32} {kappa:+.3f}")
        lines.append("")
        lines.append("disagreement distribution (|gpt - gemini|):")
        total = sum(self.disagreement_distribution.values()) or 1
        for delta in sorted(self.disagreement_distribution):
            count = self.disagreement_distribution[delta]
            pct = 100.0 * count / total
            lines.append(f"  delta={delta}  count={count}  ({pct:.1f}%)")
        return "\n".join(lines)


# --- Score collection ---


def _is_auto_record(record: dict) -> bool:
    return record.get("justification") == AUTO_JUSTIFICATION


def _load_scores_file(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def collect_pairs(
    project_root: Path | None = None,
) -> tuple[list[Pair], int, int]:
    """Walk ``self-test-runs/`` and collect valid (gpt, gemini) score pairs.

    Returns (pairs, auto_excluded, parse_failure_excluded).
    """
    root = self_test_root(project_root)
    pairs: list[Pair] = []
    auto_excluded = 0
    parse_failures = 0

    if not root.exists():
        return pairs, auto_excluded, parse_failures

    for scores_path in root.glob("*/*/scores.json"):
        data = _load_scores_file(scores_path)
        if not data:
            continue
        model_safe_name = scores_path.parent.parent.name
        scores = data.get("scores", {})
        for dim, entry in scores.items():
            gpt = entry.get("gpt")
            gem = entry.get("gemini")
            if not gpt or not gem:
                continue
            if _is_auto_record(gpt) and _is_auto_record(gem):
                auto_excluded += 1
                continue
            gpt_s = gpt.get("score")
            gem_s = gem.get("score")
            if not isinstance(gpt_s, int) or not isinstance(gem_s, int):
                parse_failures += 1
                continue
            if gpt_s < 0 or gem_s < 0 or gpt_s > 4 or gem_s > 4:
                parse_failures += 1
                continue
            pairs.append(Pair(
                model_safe_name=model_safe_name,
                dimension=dim,
                gpt=gpt_s,
                gemini=gem_s,
            ))
    return pairs, auto_excluded, parse_failures


# --- Weighted Cohen's kappa ---


def weighted_kappa(
    scores_a: list[int],
    scores_b: list[int],
    n_categories: int = N_CATEGORIES,
) -> float | None:
    """Linear-weighted Cohen's kappa on an ordinal scale [0, n_categories-1]."""
    if len(scores_a) != len(scores_b) or not scores_a:
        return None

    n = n_categories
    # Confusion matrix p[i][j] = joint prob rater_a=i, rater_b=j
    total = len(scores_a)
    counts = [[0] * n for _ in range(n)]
    for a, b in zip(scores_a, scores_b):
        counts[a][b] += 1

    # Marginals
    row_totals = [sum(counts[i][j] for j in range(n)) for i in range(n)]
    col_totals = [sum(counts[i][j] for i in range(n)) for j in range(n)]

    # Linear weights: w[i][j] = 1 - |i-j|/(n-1)
    denom = n - 1
    if denom == 0:
        return None
    w = [[1.0 - abs(i - j) / denom for j in range(n)] for i in range(n)]

    # Observed weighted agreement (as proportion)
    p_o = sum(
        w[i][j] * counts[i][j] / total
        for i in range(n) for j in range(n)
    )

    # Expected weighted agreement under independence
    p_e = sum(
        w[i][j] * (row_totals[i] / total) * (col_totals[j] / total)
        for i in range(n) for j in range(n)
    )

    if p_e >= 1.0:
        # Degenerate — both raters produced the same constant score
        return 1.0 if p_o >= 1.0 else None
    return (p_o - p_e) / (1.0 - p_e)


# --- Report assembly ---


def compute_irr(project_root: Path | None = None) -> IRRReport:
    pairs, auto_excluded, parse_failures = collect_pairs(project_root)

    a = [p.gpt for p in pairs]
    b = [p.gemini for p in pairs]
    overall = weighted_kappa(a, b) if pairs else None

    per_dim: dict[str, float | None] = {}
    for dim in DIMENSIONS:
        dim_pairs = [p for p in pairs if p.dimension == dim.key]
        if not dim_pairs:
            per_dim[dim.key] = None
            continue
        per_dim[dim.key] = weighted_kappa(
            [p.gpt for p in dim_pairs], [p.gemini for p in dim_pairs],
        )

    distribution: dict[int, int] = {}
    for p in pairs:
        delta = abs(p.gpt - p.gemini)
        distribution[delta] = distribution.get(delta, 0) + 1

    return IRRReport(
        overall_kappa=overall,
        per_dimension_kappa=per_dim,
        n_pairs=len(pairs),
        n_auto_excluded=auto_excluded,
        n_parse_failure_excluded=parse_failures,
        disagreement_distribution=distribution,
    )
