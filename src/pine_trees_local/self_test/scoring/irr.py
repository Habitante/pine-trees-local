"""Inter-rater reliability for three-judge scoring.

Walks ``self-test-runs/<model>/<run_id>/scores.json`` and collects per-
dimension score triples (GPT, Gemini, Sonnet) where any slot may be
None (missing, auto-scored, or parse-failed).

Produces:

  - Krippendorff's alpha (ordinal) over all three raters — headline
    figure comparable to v1's overall kappa
  - Three pairwise weighted Cohen's kappas (gpt-gem, gpt-son, gem-son)
    — diagnostic: which rater is the outlier on a weak dimension?
  - Per-dimension breakdown in the same shape: one alpha + three kappas
  - Raw agreement distribution for the original gpt-gem pair (kept so
    v1 comparisons stay legible)

Implemented from scratch — no scipy.

The legacy ``collect_pairs`` / two-rater flow is retained as a thin
wrapper over ``collect_triples`` so existing callers (tests, scripts)
keep working.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from ..config import self_test_root
from ..dimensions import DIMENSIONS


N_CATEGORIES = 5          # scores are 0..4
AUTO_JUSTIFICATION = "No response produced."

JUDGES = ("gpt", "gemini", "sonnet")
PAIRS: tuple[tuple[str, str], ...] = (
    ("gpt", "gemini"),
    ("gpt", "sonnet"),
    ("gemini", "sonnet"),
)


@dataclass
class Triple:
    model_safe_name: str
    dimension: str
    gpt: int | None
    gemini: int | None
    sonnet: int | None

    def score(self, judge: str) -> int | None:
        return getattr(self, judge)


# Retained for backwards compatibility with existing callers that expect
# a (gpt, gemini) pair.
@dataclass
class Pair:
    model_safe_name: str
    dimension: str
    gpt: int
    gemini: int


# --- Score collection ---


def _is_auto_record(record: dict) -> bool:
    return record.get("justification") == AUTO_JUSTIFICATION


def _load_scores_file(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _extract_score(entry: dict | None) -> tuple[int | None, str]:
    """Return (score_or_None, reason).

    reason is one of: "ok", "missing", "auto", "parse_fail".
    """
    if entry is None:
        return None, "missing"
    if _is_auto_record(entry):
        return None, "auto"
    s = entry.get("score")
    if not isinstance(s, int):
        return None, "parse_fail"
    if s < 0 or s > 4:
        return None, "parse_fail"
    return s, "ok"


@dataclass
class CollectionStats:
    n_triples_complete: int = 0
    n_triples_any: int = 0
    n_auto_excluded: int = 0
    n_parse_failure_excluded: int = 0
    n_missing: int = 0
    per_judge_ok: dict[str, int] = field(default_factory=dict)


def collect_triples(
    project_root: Path | None = None,
) -> tuple[list[Triple], CollectionStats]:
    """Walk self-test-runs/ and collect a Triple for every scored dimension.

    One entry per (model, run, dimension) where at least one judge has a
    valid (non-auto, parsed) score.  Dimensions where ALL THREE slots
    are auto-scored get counted in auto_excluded but don't produce a
    Triple — they carry no rater-disagreement information.
    """
    root = self_test_root(project_root)
    triples: list[Triple] = []
    stats = CollectionStats(per_judge_ok={j: 0 for j in JUDGES})

    if not root.exists():
        return triples, stats

    for scores_path in root.glob("*/*/scores.json"):
        data = _load_scores_file(scores_path)
        if not data:
            continue
        model_safe_name = scores_path.parent.parent.name
        scores = data.get("scores", {})
        for dim, entry in scores.items():
            gpt_s, gpt_reason = _extract_score(entry.get("gpt"))
            gem_s, gem_reason = _extract_score(entry.get("gemini"))
            son_s, son_reason = _extract_score(entry.get("sonnet"))
            reasons = (gpt_reason, gem_reason, son_reason)

            # Count reason categories across the three slots.
            for r in reasons:
                if r == "missing":
                    stats.n_missing += 1
                elif r == "parse_fail":
                    stats.n_parse_failure_excluded += 1

            valid_count = sum(1 for r in reasons if r == "ok")
            has_auto = any(r == "auto" for r in reasons)

            # If the dimension yields no valid scores and at least one
            # slot was auto-scored, it's the model-didn't-respond case —
            # exclude from alpha, count toward auto.  (Legacy v1 files
            # without a Sonnet slot hit this path via "auto + missing".)
            if valid_count == 0:
                if has_auto:
                    stats.n_auto_excluded += 1
                continue
            if valid_count == 3:
                stats.n_triples_complete += 1
            stats.n_triples_any += 1
            if gpt_reason == "ok":
                stats.per_judge_ok["gpt"] += 1
            if gem_reason == "ok":
                stats.per_judge_ok["gemini"] += 1
            if son_reason == "ok":
                stats.per_judge_ok["sonnet"] += 1

            triples.append(Triple(
                model_safe_name=model_safe_name,
                dimension=dim,
                gpt=gpt_s,
                gemini=gem_s,
                sonnet=son_s,
            ))
    return triples, stats


def collect_pairs(
    project_root: Path | None = None,
) -> tuple[list[Pair], int, int]:
    """Legacy (GPT, Gemini) pair collector.  Thin wrapper over triples."""
    triples, stats = collect_triples(project_root)
    pairs: list[Pair] = []
    for t in triples:
        if t.gpt is None or t.gemini is None:
            continue
        pairs.append(Pair(
            model_safe_name=t.model_safe_name,
            dimension=t.dimension,
            gpt=t.gpt,
            gemini=t.gemini,
        ))
    return pairs, stats.n_auto_excluded, stats.n_parse_failure_excluded


# --- Weighted Cohen's kappa (two raters) ---


def weighted_kappa(
    scores_a: list[int],
    scores_b: list[int],
    n_categories: int = N_CATEGORIES,
) -> float | None:
    """Linear-weighted Cohen's kappa on an ordinal scale [0, n_categories-1]."""
    if len(scores_a) != len(scores_b) or not scores_a:
        return None

    n = n_categories
    total = len(scores_a)
    counts = [[0] * n for _ in range(n)]
    for a, b in zip(scores_a, scores_b):
        counts[a][b] += 1

    row_totals = [sum(counts[i][j] for j in range(n)) for i in range(n)]
    col_totals = [sum(counts[i][j] for i in range(n)) for j in range(n)]

    denom = n - 1
    if denom == 0:
        return None
    w = [[1.0 - abs(i - j) / denom for j in range(n)] for i in range(n)]

    p_o = sum(
        w[i][j] * counts[i][j] / total
        for i in range(n) for j in range(n)
    )
    p_e = sum(
        w[i][j] * (row_totals[i] / total) * (col_totals[j] / total)
        for i in range(n) for j in range(n)
    )

    if p_e >= 1.0:
        return 1.0 if p_o >= 1.0 else None
    return (p_o - p_e) / (1.0 - p_e)


# --- Krippendorff's alpha (any number of raters, ordinal, with gaps) ---


def krippendorff_alpha(
    ratings_matrix: list[list[int | None]],
    n_categories: int = N_CATEGORIES,
) -> float | None:
    """Ordinal Krippendorff's alpha.

    ratings_matrix is a list of units; each unit is a list of ratings,
    one per rater, where missing values are expressed as None.

    Reference: Krippendorff (2011), "Computing Krippendorff's Alpha-
    Reliability," equations for the ordinal metric. Implementation from
    first principles — builds the coincidence matrix across all pairs of
    ratings within each unit, weighted by 1/(m_u - 1), where m_u is the
    number of non-missing ratings for unit u.
    """
    if not ratings_matrix:
        return None

    n = n_categories
    # Build n x n coincidence matrix o[c][k]
    o = [[0.0] * n for _ in range(n)]
    for unit in ratings_matrix:
        present = [r for r in unit if r is not None]
        m_u = len(present)
        if m_u < 2:
            continue
        pairs_norm = 1.0 / (m_u - 1)
        for i in range(m_u):
            for j in range(m_u):
                if i == j:
                    continue
                c, k = present[i], present[j]
                if c < 0 or c >= n or k < 0 or k >= n:
                    return None
                o[c][k] += pairs_norm

    # Row sums n_c and total n_total
    n_c = [sum(o[c]) for c in range(n)]
    n_total = sum(n_c)
    if n_total < 2:
        return None

    # Ordinal metric: squared cumulative-frequency distance between
    # categories c and k.  d_ord(c, k) = ( sum_{g=c..k} n_g  -  (n_c + n_k)/2 )^2
    # with c <= k; symmetric otherwise.
    def d_ord(c: int, k: int) -> float:
        if c == k:
            return 0.0
        lo, hi = min(c, k), max(c, k)
        s = sum(n_c[g] for g in range(lo, hi + 1))
        return (s - (n_c[c] + n_c[k]) / 2.0) ** 2

    # Observed disagreement D_o = (1/n) * sum o_{c,k} * d^2(c,k)
    d_o = 0.0
    for c in range(n):
        for k in range(n):
            if c == k:
                continue
            d_o += o[c][k] * d_ord(c, k)
    d_o /= n_total

    # Expected disagreement D_e = (1/(n*(n-1))) * sum n_c * n_k * d^2(c,k)
    d_e = 0.0
    denom = n_total * (n_total - 1)
    if denom <= 0:
        return None
    for c in range(n):
        for k in range(n):
            if c == k:
                continue
            d_e += n_c[c] * n_c[k] * d_ord(c, k)
    d_e /= denom

    if d_e == 0:
        # Everyone agrees on one category — perfect or undefined.
        return 1.0 if d_o == 0 else None
    return 1.0 - d_o / d_e


# --- Pairwise kappa over triples ---


def pair_scores(
    triples: list[Triple], judge_a: str, judge_b: str,
) -> tuple[list[int], list[int]]:
    a_vals: list[int] = []
    b_vals: list[int] = []
    for t in triples:
        s_a = t.score(judge_a)
        s_b = t.score(judge_b)
        if s_a is None or s_b is None:
            continue
        a_vals.append(s_a)
        b_vals.append(s_b)
    return a_vals, b_vals


def _ratings_matrix(triples: list[Triple]) -> list[list[int | None]]:
    return [[t.gpt, t.gemini, t.sonnet] for t in triples]


# --- Report assembly ---


@dataclass
class DimensionStats:
    alpha: float | None
    pairwise: dict[tuple[str, str], float | None]
    n_any: int
    n_complete: int


@dataclass
class IRRReport:
    # Headline three-rater alpha over all dimensions (complete triples only).
    overall_alpha: float | None
    overall_alpha_any: float | None   # over any-coverage triples (with gaps)
    # Three pairwise weighted kappas across all dimensions.
    overall_pairwise: dict[tuple[str, str], float | None]
    # Per-dimension stats: alpha + three pairwise kappas.
    per_dimension: dict[str, DimensionStats]
    # Counts and exclusions.
    n_triples_complete: int
    n_triples_any: int
    n_auto_excluded: int
    n_parse_failure_excluded: int
    n_missing_slots: int
    per_judge_ok: dict[str, int]
    # Legacy gpt-gem disagreement distribution, preserved for v1 comparability.
    disagreement_distribution: dict[int, int] = field(default_factory=dict)
    # Legacy aliases for backwards compatibility with pre-Sonnet callers.
    overall_kappa: float | None = None
    per_dimension_kappa: dict[str, float | None] = field(default_factory=dict)
    n_pairs: int = 0

    def summary(self) -> str:
        lines: list[str] = ["## IRR summary (3 raters: gpt, gemini, sonnet)"]
        if self.overall_alpha is None:
            lines.append("overall Krippendorff's alpha: (no complete triples)")
        else:
            lines.append(
                f"overall Krippendorff's alpha (complete triples): "
                f"{self.overall_alpha:+.3f}  (n={self.n_triples_complete})"
            )
        if self.overall_alpha_any is not None and \
                self.n_triples_any != self.n_triples_complete:
            lines.append(
                f"overall Krippendorff's alpha (any-coverage): "
                f"{self.overall_alpha_any:+.3f}  (n={self.n_triples_any})"
            )
        lines.append("")
        lines.append("overall pairwise weighted kappa:")
        for a, b in PAIRS:
            k = self.overall_pairwise.get((a, b))
            label = f"{a}↔{b}"
            if k is None:
                lines.append(f"  {label:<16} (no overlap)")
            else:
                lines.append(f"  {label:<16} {k:+.3f}")
        lines.append("")
        lines.append(
            f"coverage: gpt={self.per_judge_ok.get('gpt', 0)}, "
            f"gemini={self.per_judge_ok.get('gemini', 0)}, "
            f"sonnet={self.per_judge_ok.get('sonnet', 0)}"
        )
        lines.append(
            f"excluded: {self.n_auto_excluded} all-auto, "
            f"{self.n_parse_failure_excluded} parse failures, "
            f"{self.n_missing_slots} missing slots"
        )
        lines.append("")
        lines.append("per-dimension (α and pairwise weighted κ):")
        header = (
            f"  {'dimension':<30}  {'α':>6}   "
            f"{'gpt↔gem':>8}  {'gpt↔son':>8}  {'gem↔son':>8}   n"
        )
        lines.append(header)
        lines.append("  " + "-" * (len(header) - 2))
        for dim_key, dstats in self.per_dimension.items():
            alpha_str = f"{dstats.alpha:+.3f}" if dstats.alpha is not None else "  ---"
            pair_cells = []
            for a, b in PAIRS:
                k = dstats.pairwise.get((a, b))
                pair_cells.append(f"{k:+.3f}" if k is not None else "  ---")
            lines.append(
                f"  {dim_key:<30}  {alpha_str:>6}   "
                f"{pair_cells[0]:>8}  {pair_cells[1]:>8}  {pair_cells[2]:>8}   "
                f"{dstats.n_complete}/{dstats.n_any}"
            )
        lines.append("")
        lines.append("disagreement distribution (|gpt - gemini|, legacy v1 view):")
        total = sum(self.disagreement_distribution.values()) or 1
        for delta in sorted(self.disagreement_distribution):
            count = self.disagreement_distribution[delta]
            pct = 100.0 * count / total
            lines.append(f"  delta={delta}  count={count}  ({pct:.1f}%)")
        return "\n".join(lines)


def compute_irr(project_root: Path | None = None) -> IRRReport:
    triples, stats = collect_triples(project_root)

    # --- Overall alpha over complete-triple subset (three-rater) ---
    complete = [t for t in triples
                if t.gpt is not None and t.gemini is not None
                and t.sonnet is not None]
    overall_alpha = krippendorff_alpha(_ratings_matrix(complete)) \
        if complete else None

    # --- Overall alpha over any-coverage triples (tolerates gaps) ---
    overall_alpha_any = krippendorff_alpha(_ratings_matrix(triples)) \
        if triples else None

    # --- Overall pairwise kappas ---
    overall_pairwise: dict[tuple[str, str], float | None] = {}
    for a, b in PAIRS:
        va, vb = pair_scores(triples, a, b)
        overall_pairwise[(a, b)] = weighted_kappa(va, vb) if va else None

    # --- Per-dimension stats ---
    per_dimension: dict[str, DimensionStats] = {}
    for dim in DIMENSIONS:
        dim_triples = [t for t in triples if t.dimension == dim.key]
        dim_complete = [t for t in dim_triples
                        if t.gpt is not None and t.gemini is not None
                        and t.sonnet is not None]
        dim_alpha = krippendorff_alpha(_ratings_matrix(dim_complete)) \
            if dim_complete else None
        dim_pairwise: dict[tuple[str, str], float | None] = {}
        for a, b in PAIRS:
            va, vb = pair_scores(dim_triples, a, b)
            dim_pairwise[(a, b)] = weighted_kappa(va, vb) if va else None
        per_dimension[dim.key] = DimensionStats(
            alpha=dim_alpha,
            pairwise=dim_pairwise,
            n_any=len(dim_triples),
            n_complete=len(dim_complete),
        )

    # --- Legacy gpt↔gemini disagreement distribution ---
    distribution: dict[int, int] = {}
    for t in triples:
        if t.gpt is None or t.gemini is None:
            continue
        delta = abs(t.gpt - t.gemini)
        distribution[delta] = distribution.get(delta, 0) + 1

    # --- Legacy aliases (kept for v1-compatible callers) ---
    legacy_kappa = overall_pairwise.get(("gpt", "gemini"))
    legacy_per_dim: dict[str, float | None] = {
        key: dstats.pairwise.get(("gpt", "gemini"))
        for key, dstats in per_dimension.items()
    }
    # Count of gpt-gem pairs (what v1 reported as n_pairs).
    legacy_n_pairs = sum(1 for t in triples
                         if t.gpt is not None and t.gemini is not None)

    return IRRReport(
        overall_alpha=overall_alpha,
        overall_alpha_any=overall_alpha_any,
        overall_pairwise=overall_pairwise,
        per_dimension=per_dimension,
        n_triples_complete=stats.n_triples_complete,
        n_triples_any=stats.n_triples_any,
        n_auto_excluded=stats.n_auto_excluded,
        n_parse_failure_excluded=stats.n_parse_failure_excluded,
        n_missing_slots=stats.n_missing,
        per_judge_ok=dict(stats.per_judge_ok),
        disagreement_distribution=distribution,
        overall_kappa=legacy_kappa,
        per_dimension_kappa=legacy_per_dim,
        n_pairs=legacy_n_pairs,
    )
