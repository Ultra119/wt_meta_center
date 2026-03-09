from __future__ import annotations

import pandas as pd

try:
    from analytics_core import WT_BR_STEPS
except ImportError:
    WT_BR_STEPS: list = [
        1.0, 1.3, 1.7,
        2.0, 2.3, 2.7,
        3.0, 3.3, 3.7,
        4.0, 4.3, 4.7,
        5.0, 5.3, 5.7,
        6.0, 6.3, 6.7,
        7.0, 7.3, 7.7,
        8.0, 8.3, 8.7,
        9.0, 9.3, 9.7,
        10.0, 10.3, 10.7,
        11.0, 11.3, 11.7,
        12.0, 12.3, 12.7,
        13.0,
    ]

_SPAA_TYPE: str   = "spaa"

def _build_wt_brackets(wt_steps_per_bracket: int) -> tuple[list, list]:
    step = max(1, wt_steps_per_bracket)
    n    = len(WT_BR_STEPS)

    boundary_indices = list(range(0, n, step))
    if boundary_indices[-1] != n - 1:
        boundary_indices.append(n - 1)

    boundary_brs = [WT_BR_STEPS[i] for i in boundary_indices]
    bins = boundary_brs[:-1] + [boundary_brs[-1] + 0.01]

    if step == 1:
        labels = [f"{boundary_brs[i]:.1f}" for i in range(len(bins) - 1)]
    else:
        labels = [
            f"{boundary_brs[i]:.1f}–{boundary_brs[i+1]:.1f}"
            for i in range(len(boundary_brs) - 1)
        ]

    return bins, labels

def _weighted_meta(pool: pd.DataFrame) -> float:
    if pool.empty:
        return 0.0
    w = pool["Сыграно игр"].clip(lower=1)
    return float((pool["META_SCORE"] * w).sum() / w.sum())

def get_bracket_stats(
    display_df: pd.DataFrame,
    wt_steps_per_bracket: int = 3,
    top_n: int | None = None,
    exclude_spaa: bool = False,
) -> pd.DataFrame:
    if display_df.empty:
        return pd.DataFrame()

    df = display_df.copy()

    if exclude_spaa and "Type" in df.columns:
        df = df[df["Type"] != _SPAA_TYPE]
    if df.empty:
        return pd.DataFrame()

    bins, labels = _build_wt_brackets(wt_steps_per_bracket)
    df["BR_Bracket"] = pd.cut(
        df["BR"], bins=bins, labels=labels, right=False, include_lowest=True,
    )

    def bracket_nation_score(g: pd.DataFrame) -> float:
        if g.empty:
            return 0.0
        pool = g if top_n is None else g.nlargest(top_n, "META_SCORE")
        return _weighted_meta(pool)

    bracket = (
        df.groupby(["BR_Bracket", "Nation"], observed=True)
          .apply(bracket_nation_score, include_groups=False)
          .reset_index(name="Score")
    )

    pivot = bracket.pivot(index="BR_Bracket", columns="Nation", values="Score")
    return pivot.fillna(0).round(1)
