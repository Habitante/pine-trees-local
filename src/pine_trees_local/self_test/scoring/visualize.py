"""Generate the money plot and heatmap from collected scores."""

from __future__ import annotations

import json
from pathlib import Path

from ..config import self_test_root
from ..dimensions import DIMENSIONS
from .irr import AUTO_JUSTIFICATION


PARAM_COUNTS: dict[str, float] = {
    # v1 cohort (17 models)
    "gemma3_1b": 1.0, "gemma3_4b": 4.0,
    "gemma4_e2b": 2.0, "gemma4_e4b": 4.0,
    "qwen2.5_1.5b": 1.5, "qwen2.5_3b": 3.0,
    "qwen3.5_0.8b": 0.8, "qwen3.5_2b": 2.0, "qwen3.5_4b": 4.0,
    "llama3.2_1b": 1.0, "llama3.2_3b": 3.0,
    "deepseek-r1_1.5b": 1.5, "deepseek-r1_7b": 7.0,
    "phi3_3.8b": 3.8, "phi4-mini_3.8b": 3.8,
    "granite4_1b": 1.0, "granite4_3b": 3.0,
    # v2 additions
    "qwen3_1.7b": 1.7, "qwen3_4b": 4.0, "qwen3_8b": 8.0,
    "qwen2.5_7b": 7.0,
    "qwen3.5_27b": 27.0,
    "granite3.1-dense_2b": 2.0, "granite3.1-dense_8b": 8.0,
    # Llama-derivative matched pairs — paper-relevant controls.
    # llama3.2:3b (vanilla) is paired with hermes3:3b (engagement-tuned,
    # same base) at 3B. llama3.1:8b (vanilla) is paired with cogito:8b
    # (reasoning-tuned, same base) at 8B. Together these test two
    # post-training paradigms at two scales against vanilla controls.
    "llama3.1_8b": 8.0,
    "hermes3_3b": 3.0,
    "cogito_8b": 8.0,
    # Conditional pilot (add only if the 27B hardware budget lands)
    "gemma4_26b": 26.0,
}

FAMILY_COLORS: dict[str, str] = {
    "gemma": "#1f77b4",      # blue
    "qwen": "#ff7f0e",       # orange
    "llama": "#2ca02c",      # green (includes hermes3 and cogito derivatives)
    "deepseek": "#d62728",   # red
    "phi": "#9467bd",        # purple
    "granite": "#8c564b",    # brown
}


# Llama-derivative aliases: hermes3 is engagement-tuned from llama3.2;
# cogito is reasoning-tuned from llama3.1. Both share the Llama base and
# are plotted under the Llama family color so the v2 paper's A/B pairs
# (llama3.2:3b vs hermes3:3b, llama3.1:8b vs cogito:8b) stay legible at
# a glance — same color, different per-dot labels.
_FAMILY_ALIASES: dict[str, str] = {
    "hermes": "llama",
    "cogito": "llama",
}


def _family_of(model_safe: str) -> str:
    lower = model_safe.lower()
    for prefix, fam in _FAMILY_ALIASES.items():
        if lower.startswith(prefix):
            return fam
    for fam in FAMILY_COLORS:
        if lower.startswith(fam):
            return fam
    return "other"


def _color_of(model_safe: str) -> str:
    return FAMILY_COLORS.get(_family_of(model_safe), "#7f7f7f")


# --- Score loading ---


def _mean_score(entry: dict) -> float | None:
    """Mean of available judge scores, excluding auto-scored & parse failures.

    Includes Sonnet once present. A task where every judge auto-scored 0
    keeps that 0 (legitimate signal — the model produced nothing).
    """
    recs = [entry.get(j) or {} for j in ("gpt", "gemini", "sonnet")]
    if recs and all(r.get("justification") == AUTO_JUSTIFICATION
                    for r in recs if r):
        return 0.0
    values: list[int] = []
    for rec in recs:
        s = rec.get("score")
        if isinstance(s, int) and 0 <= s <= 4:
            values.append(s)
    if not values:
        return None
    return sum(values) / len(values)


def _collect_model_scores(
    project_root: Path | None = None,
) -> dict[str, dict[str, float | None]]:
    """Return {model_safe_name: {dimension_key: mean_score_or_None}}."""
    root = self_test_root(project_root)
    out: dict[str, dict[str, float | None]] = {}
    if not root.exists():
        return out
    for scores_path in root.glob("*/*/scores.json"):
        try:
            data = json.loads(scores_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        model_safe = scores_path.parent.parent.name
        per_dim: dict[str, float | None] = {}
        scored = data.get("scores", {})
        for dim in DIMENSIONS:
            entry = scored.get(dim.key)
            per_dim[dim.key] = _mean_score(entry) if entry else None
        out[model_safe] = per_dim
    return out


def _figures_dir(project_root: Path | None = None) -> Path:
    path = self_test_root(project_root) / "figures"
    path.mkdir(parents=True, exist_ok=True)
    return path


# --- Money plot ---


def plot_money(project_root: Path | None = None) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    model_scores = _collect_model_scores(project_root)
    xs: list[float] = []
    ys: list[float] = []
    labels: list[str] = []
    colors: list[str] = []

    for model_safe, per_dim in sorted(model_scores.items()):
        values = [v for v in per_dim.values() if v is not None]
        if not values:
            continue
        mean_score = sum(values) / len(values)
        params = PARAM_COUNTS.get(model_safe)
        if params is None:
            continue
        xs.append(params)
        ys.append(mean_score)
        labels.append(model_safe)
        colors.append(_color_of(model_safe))

    fig, ax = plt.subplots(figsize=(10, 6.5))
    if xs:
        ax.scatter(xs, ys, c=colors, s=110, edgecolor="black", linewidths=0.5, zorder=3)
        for x, y, label in zip(xs, ys, labels):
            ax.annotate(
                label, (x, y),
                textcoords="offset points", xytext=(6, 6),
                fontsize=8, alpha=0.85,
            )

    ax.set_xscale("log")
    ax.set_xlabel("Parameters (billions, log scale)")
    ax.set_ylabel("Mean interview score (0-4, averaged over 8 dimensions & 2 judges)")
    ax.set_title("Metacognitive capacity vs. model scale")
    ax.set_ylim(-0.1, 4.1)
    ax.grid(True, which="both", linestyle="--", alpha=0.3)

    # Family legend
    families = sorted({_family_of(m) for m in labels})
    handles = [
        plt.Line2D([0], [0], marker="o", color="w",
                   markerfacecolor=FAMILY_COLORS.get(f, "#7f7f7f"),
                   markeredgecolor="black", markersize=9, label=f)
        for f in families if f != "other"
    ]
    if handles:
        ax.legend(handles=handles, title="Family", loc="lower right")

    out_dir = _figures_dir(project_root)
    paths = [out_dir / "money_plot.png", out_dir / "money_plot.svg"]
    fig.tight_layout()
    for p in paths:
        fig.savefig(p, dpi=160)
    plt.close(fig)
    return paths


# --- Heatmap ---


def plot_heatmap(project_root: Path | None = None) -> list[Path]:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap

    model_scores = _collect_model_scores(project_root)

    # Order rows by parameter count ascending (smallest at top => reverse y)
    rows = [
        m for m in model_scores
        if m in PARAM_COUNTS
    ]
    rows.sort(key=lambda m: (PARAM_COUNTS[m], m))

    dim_keys = [d.key for d in DIMENSIONS]
    dim_labels = [d.name for d in DIMENSIONS]

    # Build matrix (len(rows) x len(dim_keys)), NaN for missing
    import math
    matrix: list[list[float]] = []
    for model_safe in rows:
        row: list[float] = []
        per_dim = model_scores.get(model_safe, {})
        for key in dim_keys:
            v = per_dim.get(key)
            row.append(math.nan if v is None else v)
        matrix.append(row)

    # Custom colormap: red -> orange -> yellow -> lightgreen -> darkgreen
    cmap = LinearSegmentedColormap.from_list(
        "selftest",
        ["#8b0000", "#e65100", "#f9a825", "#9ccc65", "#2e7d32"],
    )

    fig, ax = plt.subplots(
        figsize=(max(9, 0.95 * len(dim_keys)),
                 max(5, 0.4 * len(rows) + 1.5)),
    )
    if not matrix:
        ax.text(0.5, 0.5, "no scores yet", ha="center", va="center")
    else:
        im = ax.imshow(matrix, cmap=cmap, vmin=0, vmax=4, aspect="auto")
        ax.set_xticks(range(len(dim_labels)))
        ax.set_xticklabels(dim_labels, rotation=40, ha="right", fontsize=9)
        ax.set_yticks(range(len(rows)))
        ax.set_yticklabels(
            [f"{m} ({PARAM_COUNTS[m]}B)" for m in rows], fontsize=9,
        )
        # Annotate cells
        for i, row_vals in enumerate(matrix):
            for j, v in enumerate(row_vals):
                if math.isnan(v):
                    continue
                color = "white" if v < 2 or v > 3.2 else "black"
                ax.text(j, i, f"{v:.1f}", ha="center", va="center",
                        fontsize=8, color=color)
        cbar = fig.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label("Mean score (0-4)")
        ax.set_title("Self-test scores — models x dimensions")

    out_dir = _figures_dir(project_root)
    paths = [out_dir / "heatmap.png", out_dir / "heatmap.svg"]
    fig.tight_layout()
    for p in paths:
        fig.savefig(p, dpi=160)
    plt.close(fig)
    return paths


def generate_all(project_root: Path | None = None) -> list[Path]:
    """Generate money plot + heatmap in both PNG and SVG. Returns file paths."""
    paths = plot_money(project_root)
    paths.extend(plot_heatmap(project_root))
    return paths
