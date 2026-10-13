
import numpy as np
import pandas as pd

CATEGORIES = [
    "PTS", "REB", "AST", "STL", "BLK",
    "3PM", "FG%", "FT%", "TO",
]

LOWER_IS_BETTER = {"TO"}


def _weighted_baseline(
    reference: pd.DataFrame,
    percentage: str,
    attempts: str,
) -> float:
    """依出手量計算參考群體的加權命中率。"""
    pct = pd.to_numeric(reference[percentage], errors="coerce")
    att = pd.to_numeric(reference[attempts], errors="coerce")

    valid = pct.notna() & att.notna() & (att > 0)

    if not valid.any() or att[valid].sum() <= 0:
        return float(pct.mean())

    return float(
        (pct[valid] * att[valid]).sum() / att[valid].sum()
    )


def calculate_z_scores(
    players: pd.DataFrame,
    reference: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """計算 9-Cat Z-score；reference 用於定義比較基準。"""

    if players.empty:
        return pd.DataFrame(
            columns=["Player", *CATEGORIES, "Weighted Z"]
        )

    result = players.copy()
    ref = (
        reference.copy()
        if reference is not None and not reference.empty
        else players.copy()
    )

    for cat in CATEGORIES:
        if cat not in result.columns or cat not in ref.columns:
            raise ValueError(f"缺少必要欄位：{cat}")

        result[cat] = pd.to_numeric(
            result[cat], errors="coerce"
        )
        ref[cat] = pd.to_numeric(
            ref[cat], errors="coerce"
        )

    # FG% 和 FT% 分別依照出手量估算貢獻。
    for cat, attempts in [("FG%", "FGA"), ("FT%", "FTA")]:
        if attempts not in result.columns or attempts not in ref.columns:
            continue

        baseline = _weighted_baseline(ref, cat, attempts)

        player_attempts = pd.to_numeric(
            result[attempts], errors="coerce"
        ).fillna(0).clip(lower=0)

        reference_attempts = pd.to_numeric(
            ref[attempts], errors="coerce"
        ).fillna(0).clip(lower=0)

        result[f"{cat} contribution"] = (
            result[cat] - baseline
        ) * player_attempts

        ref[f"{cat} contribution"] = (
            ref[cat] - baseline
        ) * reference_attempts

    for cat in CATEGORIES:
        contribution_col = f"{cat} contribution"

        if contribution_col in result.columns:
            values = result[contribution_col]
            reference_values = ref[contribution_col]
        else:
            values = result[cat]
            reference_values = ref[cat]

        mean = reference_values.mean()
        std = reference_values.std(ddof=0)

        if pd.isna(std) or std == 0:
            z = pd.Series(0.0, index=result.index)
        else:
            z = (values - mean) / std

        if cat in LOWER_IS_BETTER:
            z = -z

        result[f"{cat} Z"] = z.replace(
            [np.inf, -np.inf], np.nan
        ).fillna(0.0)

    return result


def calculate_weighted_scores(
    players: pd.DataFrame,
    weights: dict[str, float],
    reference: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """依照 0 到 2 的類別權重計算加權 Z-score。"""

    result = calculate_z_scores(players, reference)

    if result.empty:
        result["Weighted Z"] = pd.Series(dtype=float)
        return result

    total = pd.Series(0.0, index=result.index)
    total_weight = 0.0

    for cat in CATEGORIES:
        weight = float(weights.get(cat, 1.0))
        weight = max(0.0, min(2.0, weight))

        total += result[f"{cat} Z"] * weight
        total_weight += weight

    if total_weight == 0:
        result["Weighted Z"] = 0.0
    else:
        result["Weighted Z"] = total / total_weight

    return result.sort_values(
        "Weighted Z", ascending=False
    ).reset_index(drop=True)

