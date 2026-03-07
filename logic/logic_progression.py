import pandas as pd
import numpy as np

RANK_PENALTY: dict[int, float] = {
    -4: 0.05,
    -3: 0.10,
    -2: 0.30,
    -1: 0.90,

     0: 1.00,
    +1: 1.00,

    +2: 0.40,
    +3: 0.30,
    +4: 0.20,
}

RANK_PENALTY_PREMIUM: dict[int, float] = {
    -4: 1.00,
    -3: 1.00,
    -2: 1.00,
    -1: 1.00,
     0: 1.00,
    +1: 1.00,
    +2: 0.40,
    +3: 0.30,
    +4: 0.20,
}

ROMAN: dict[int, str] = {
    1: "I", 2: "II", 3: "III", 4: "IV",
    5: "V", 6: "VI", 7: "VII", 8: "VIII",
}

# Вердикты
VERDICT_MUST = "MUST"
VERDICT_PASS = "PASS"
VERDICT_SKIP = "SKIP"
VERDICT_PREM = "PREM"

def _br_to_era(br: float) -> int:
    thresholds = [2.3, 3.7, 5.3, 6.7, 8.3, 9.7, 11.3]
    for i, t in enumerate(thresholds):
        if br <= t:
            return i + 1
    return 8


def _minmax(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx - mn < 1e-9:
        return pd.Series(50.0, index=series.index)
    return (series - mn) / (mx - mn) * 100.0


def _local_score(branch_df: pd.DataFrame) -> pd.Series:
    wr   = _minmax(branch_df["WR"])
    kd   = _minmax(branch_df["KD"])

    if "META_SCORE" in branch_df.columns:
        meta_vals = branch_df["META_SCORE"].fillna(0)
        if meta_vals.std() > 0.1:
            meta = _minmax(meta_vals)
            return (0.40 * wr + 0.30 * kd + 0.30 * meta).clip(0, 100)

    return (0.55 * wr + 0.45 * kd).clip(0, 100)


def _rank_penalty(researcher_era: int, target_era: int, is_premium: bool = False) -> float:
    diff = target_era - researcher_era
    if is_premium:
        if diff <= 1:
            return RANK_PENALTY_PREMIUM.get(diff, 1.00)
        return RANK_PENALTY_PREMIUM.get(diff, 0.20)
    if diff < 0:
        return RANK_PENALTY.get(diff, 0.05)
    return RANK_PENALTY.get(diff, 0.20)

def build_progression_data(df: pd.DataFrame, nation: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    out = df[df["Nation"] == nation].copy() if nation != "All" else df.copy()
    if out.empty:
        return pd.DataFrame()

    # ── Разрешаем ранг ────────────────────────────────────────────────────
    if "vdb_era" in out.columns:
        eras = pd.to_numeric(out["vdb_era"], errors="coerce").fillna(0).astype(int)
        bad = eras == 0
        eras[bad] = out.loc[bad, "BR"].apply(_br_to_era).values
        out["_era_int"] = eras.clip(1, 8)
    else:
        out["_era_int"] = out["BR"].apply(_br_to_era)

    out["_branch"] = out["Type"].fillna("unknown").astype(str)

    # ── Инициализация выходных колонок ────────────────────────────────────
    out["Local_Score"] = 0.0
    out["Verdict"]     = VERDICT_PASS
    out["Skip_Reason"] = ""
    out["Alt_Vehicle"] = ""

    is_prem = out["VehicleClass"].isin(["Premium", "Pack", "Squadron", "Marketplace"])

    # ── Проход 1: вычисляем Local_Score для каждой ветки ─────────────────
    for branch, grp in out.groupby("_branch"):
        scores = _local_score(grp)
        out.loc[grp.index, "Local_Score"] = scores.values

    # ── Проход 2: вердикты с анализом скипа ──────────────────────────────
    for branch, grp in out.groupby("_branch"):
        srt = grp.sort_values("BR")
        p60 = srt["Local_Score"].quantile(0.60)

        for pos, (row_idx, row) in enumerate(srt.iterrows()):
            era      = int(row["_era_int"])
            loc_s    = float(row["Local_Score"])
            vclass   = str(row.get("VehicleClass", "Standard"))
            prem_row = vclass in ("Premium", "Pack", "Squadron", "Marketplace")

            if prem_row:
                out.at[row_idx, "Verdict"] = VERDICT_PREM
                continue

            prev_all = srt.iloc[:pos]

            should_skip = False
            reason      = ""
            alt_name    = ""

            if not prev_all.empty:
                best_eff   = 0.0
                best_name  = ""
                best_penalty_pct = 0.0

                for _, prev_row in prev_all.iterrows():
                    prev_vclass   = str(prev_row.get("VehicleClass", "Standard"))
                    prev_is_prem  = prev_vclass in ("Premium", "Pack", "Squadron", "Marketplace")
                    prev_era      = int(prev_row["_era_int"])
                    prev_score    = float(prev_row["Local_Score"])

                    pen = _rank_penalty(prev_era, era, is_premium=prev_is_prem)
                    eff = prev_score * pen

                    if eff > best_eff:
                        best_eff          = eff
                        best_name         = str(prev_row["Name"])
                        best_penalty_pct  = pen * 100.0

                if best_eff > loc_s * 1.05:
                    should_skip = True
                    reason = (
                        f"Скип. Выгоднее исследовать на «{best_name}» "
                        f"(эфф.RP {best_eff:.0f} vs {loc_s:.0f}). "
                        f"Коэф. ОИ: {best_penalty_pct:.0f}%."
                    )
                    alt_name = best_name

            if should_skip:
                out.at[row_idx, "Verdict"]     = VERDICT_SKIP
                out.at[row_idx, "Skip_Reason"] = reason
                out.at[row_idx, "Alt_Vehicle"] = alt_name
            elif loc_s >= p60:
                out.at[row_idx, "Verdict"] = VERDICT_MUST
            else:
                out.at[row_idx, "Verdict"] = VERDICT_PASS

    # ── Проход 3: «Premium Fix» для болезненных рангов ────────────────────
    std_df = out[~is_prem]
    era_has_must = std_df.groupby("_era_int")["Verdict"].apply(
        lambda v: (v == VERDICT_MUST).any()
    )
    pain_eras = set(era_has_must[~era_has_must].index.tolist())

    prem_in_pain = is_prem & out["_era_int"].isin(pain_eras)
    out.loc[prem_in_pain, "Verdict"] = VERDICT_PREM

    return out
