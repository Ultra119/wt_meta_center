import pandas as pd
import numpy as np

RANK_PENALTY: dict[int, float] = {
    -4: 0.05,
    -3: 0.10,
    -2: 0.30,
    -1: 0.90,
     0: 1.00,
    +1: 1.00,
    +2: 0.35,
    +3: 0.15,
    +4: 0.06,
}

RANK_PENALTY_PREMIUM: dict[int, float] = {
    -4: 1.00,
    -3: 1.00,
    -2: 1.00,
    -1: 1.00,
     0: 1.00,
    +1: 1.00,
    +2: 0.35,
    +3: 0.15,
    +4: 0.06,
}

_MM_WINDOW = 1.0


def _br_decay(researcher_br: float, target_br: float) -> float:
    gap = target_br - researcher_br
    if gap <= _MM_WINDOW:
        return 1.0
    excess = gap - _MM_WINDOW
    return float(max(0.02, np.exp(-1.1 * excess)))

ROMAN: dict[int, str] = {
    1: "I", 2: "II", 3: "III", 4: "IV",
    5: "V", 6: "VI", 7: "VII", 8: "VIII",
}

VERDICT_MUST = "MUST"
VERDICT_PASS = "PASS"
VERDICT_SKIP = "SKIP"
VERDICT_PREM = "PREM"

_STD_CLASS   = "Standard"


def _shop_sort_key(df: pd.DataFrame) -> pd.Series:
    if "vdb_shop_order" in df.columns:
        order    = pd.to_numeric(df["vdb_shop_order"], errors="coerce").fillna(99999)
        fallback = df["BR"] * 10000
        return order.where(order < 99999, fallback)
    return df["BR"] * 10000


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
    wr = _minmax(branch_df["WR"])
    kd = _minmax(branch_df["KD"])
    if "META_SCORE" in branch_df.columns:
        meta_vals = branch_df["META_SCORE"].fillna(0)
        if meta_vals.std() > 0.1:
            meta = _minmax(meta_vals)
            return (0.40 * wr + 0.30 * kd + 0.30 * meta).clip(0, 100)
    return (0.55 * wr + 0.45 * kd).clip(0, 100)


def _rank_penalty_std(researcher_era: int, target_era: int) -> float:
    diff = target_era - researcher_era
    if diff < 0:
        return RANK_PENALTY.get(diff, 0.05)
    return RANK_PENALTY.get(diff, 0.06)


def _rank_penalty_prem(researcher_era: int, target_era: int) -> float:
    diff = target_era - researcher_era
    if diff <= 1:
        return RANK_PENALTY_PREMIUM.get(diff, 1.00)
    return RANK_PENALTY_PREMIUM.get(diff, 0.06)


def _combined_penalty(
    researcher_era: int, researcher_br: float,
    target_era: int,    target_br: float,
    is_prem: bool = False,
) -> float:
    rank_pen = (
        _rank_penalty_prem(researcher_era, target_era)
        if is_prem else
        _rank_penalty_std(researcher_era, target_era)
    )
    return rank_pen * _br_decay(researcher_br, target_br)


def _calc_prem_boost(
    prem_era: int,
    prem_br:  float,
    prem_score: float,
    std_branch: pd.DataFrame,
    target_era: int,
    target_br:  float,
) -> float:
    prem_grind = prem_score * _combined_penalty(
        prem_era, prem_br, target_era, target_br, is_prem=True
    )

    best_free = 0.0
    for _, row in std_branch.iterrows():
        eff = float(row["Local_Score"]) * _combined_penalty(
            int(row["_era_int"]), float(row["BR"]),
            target_era, target_br,
        )
        if eff > best_free:
            best_free = eff

    if best_free < 1e-3:
        return round(prem_grind / max(prem_score, 1e-3), 2)

    return round(prem_grind / best_free, 2)


def build_progression_data(df: pd.DataFrame, nation: str) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    out = df[df["Nation"] == nation].copy() if nation != "All" else df.copy()
    if out.empty:
        return pd.DataFrame()

    # ── Ранг ──────────────────────────────────────────────────────────────────
    if "vdb_era" in out.columns:
        eras = pd.to_numeric(out["vdb_era"], errors="coerce").fillna(0).astype(int)
        bad  = eras == 0
        eras[bad] = out.loc[bad, "BR"].apply(_br_to_era).values
        out["_era_int"] = eras.clip(1, 8)
    else:
        out["_era_int"] = out["BR"].apply(_br_to_era)

    out["_branch"] = out["Type"].fillna("unknown").astype(str)

    # ── Инициализация выходных колонок ────────────────────────────────────────
    out["Local_Score"]   = 0.0
    out["Verdict"]       = VERDICT_PASS
    out["Skip_Reason"]   = ""
    out["Alt_Vehicle"]   = ""
    out["Cross_Alt"]     = ""
    out["Cross_Hint"]    = ""
    out["Prem_Boost"]    = 0.0
    out["Prem_Pain_Fix"] = False

    is_prem = out["VehicleClass"] != _STD_CLASS
    std_df  = out[~is_prem].copy()
    prem_df = out[is_prem].copy()

    # ── Сортировка по позиции в дереве (shop_order) ───────────────────
    if not std_df.empty:
        std_df["_sort_key"] = _shop_sort_key(std_df)
        std_df = std_df.sort_values("_sort_key").drop(columns=["_sort_key"])
    if not prem_df.empty:
        prem_df["_sort_key"] = _shop_sort_key(prem_df)
        prem_df = prem_df.sort_values("_sort_key").drop(columns=["_sort_key"])

    # Проход 1-S: Local_Score только среди стандартной техники в каждой ветке
    for branch, grp in std_df.groupby("_branch"):
        scores = _local_score(grp)
        std_df.loc[grp.index, "Local_Score"] = scores.values

    # Проход 2-S: вердикты
    for branch, grp in std_df.groupby("_branch"):
        srt = grp.sort_values("BR")
        p60 = srt["Local_Score"].quantile(0.60)

        for pos, (row_idx, row) in enumerate(srt.iterrows()):
            era   = int(row["_era_int"])
            loc_s = float(row["Local_Score"])

            prev = srt.iloc[:pos]
            should_skip     = False
            reason          = ""
            alt_name        = ""

            if not prev.empty:
                best_eff         = 0.0
                best_name        = ""

                target_br = float(row["BR"])

                for prev_idx, prev_row in prev.iterrows():
                    if std_df.at[prev_idx, "Verdict"] == VERDICT_SKIP:
                        continue
                    pen = _combined_penalty(
                        researcher_era=int(prev_row["_era_int"]),
                        researcher_br=float(prev_row["BR"]),
                        target_era=era,
                        target_br=target_br,
                    )
                    eff = float(prev_row["Local_Score"]) * pen
                    if eff > best_eff:
                        best_eff  = eff
                        best_name = str(prev_row["Name"])

                if best_eff > loc_s * 1.05:
                    should_skip = True
                    reason = (
                        f"Эффективнее прокачивать ветку на «{best_name}» "
                        f"(RP {best_eff:.0f} vs {loc_s:.0f})"
                    )
                    alt_name = best_name

            if should_skip:
                std_df.at[row_idx, "Verdict"]     = VERDICT_SKIP
                std_df.at[row_idx, "Skip_Reason"] = reason
                std_df.at[row_idx, "Alt_Vehicle"] = alt_name
            elif loc_s >= p60:
                std_df.at[row_idx, "Verdict"] = VERDICT_MUST
            else:
                std_df.at[row_idx, "Verdict"] = VERDICT_PASS

    _CROSS_THRESHOLD  = 1.30
    _CROSS_BR_WINDOW  = 0.7

    _GROUND_BRANCHES   = {"medium_tank", "light_tank", "heavy_tank", "tank_destroyer", "spaa"}
    _AVIATION_BRANCHES = {"fighter", "bomber", "assault", "attack_helicopter", "utility_helicopter"}
    _SKIP_CROSS        = {"spaa"}   # ЗСУ не участвуют в межветочном сравнении

    def _super_cat(branch: str) -> str:
        if branch in _GROUND_BRANCHES:   return "Ground"
        if branch in _AVIATION_BRANCHES: return "Aviation"
        return "Fleet"

    # Предвычисляем суперкатегорию для каждой строки один раз
    std_df["_super_cat"] = std_df["_branch"].apply(_super_cat)

    if "META_SCORE" in std_df.columns:
        for row_idx, row in std_df.iterrows():
            if std_df.at[row_idx, "Verdict"] not in (VERDICT_MUST, VERDICT_PASS):
                continue

            our_meta   = float(row.get("META_SCORE", 0) or 0)
            our_br     = float(row["BR"])
            our_branch = str(row["_branch"])
            our_cat    = str(row["_super_cat"])

            if our_meta < 1e-3 or our_branch in _SKIP_CROSS:
                continue

            best_cross_meta = 0.0
            best_cross_name = ""
            best_cross_br   = 0.0

            mask = (
                (std_df["_branch"]    != our_branch) &
                (std_df["_super_cat"] == our_cat) &
                (std_df["BR"] >= our_br - _CROSS_BR_WINDOW) &
                (std_df["BR"] <= our_br + _CROSS_BR_WINDOW) &
                (std_df["Verdict"] != VERDICT_SKIP)
            )
            for alt_idx, alt_row in std_df[mask].iterrows():
                alt_meta = float(alt_row.get("META_SCORE", 0) or 0)
                if alt_meta > best_cross_meta:
                    best_cross_meta = alt_meta
                    best_cross_name = str(alt_row["Name"])
                    best_cross_br   = float(alt_row["BR"])

            if best_cross_meta > our_meta * _CROSS_THRESHOLD:
                std_df.at[row_idx, "Cross_Alt"]  = best_cross_name
                std_df.at[row_idx, "Cross_Hint"] = (
                    f"Для сетапа лучше «{best_cross_name}» ({best_cross_br:.1f}) "
                    f"— он сильнее в своём BR"
                )
                if std_df.at[row_idx, "Verdict"] == VERDICT_MUST:
                    std_df.at[row_idx, "Verdict"] = VERDICT_PASS

    std_df.drop(columns=["_super_cat"], errors="ignore", inplace=True)

    spaa_must = (std_df["_branch"] == "spaa") & (std_df["Verdict"] == VERDICT_MUST)
    std_df.loc[spaa_must, "Verdict"] = VERDICT_PASS

    if "Cross_Alt" not in std_df.columns:
        std_df["Cross_Alt"]  = ""
        std_df["Cross_Hint"] = ""

    # «Болезненные» ранги — нет ни одного MUST среди стандарта
    era_has_must = std_df.groupby("_era_int")["Verdict"].apply(
        lambda v: (v == VERDICT_MUST).any()
    )
    pain_eras = set(era_has_must[~era_has_must].index.tolist())

    if not prem_df.empty:
        # Local_Score внутри премиума по веткам
        for branch, grp in prem_df.groupby("_branch"):
            scores = _local_score(grp)
            prem_df.loc[grp.index, "Local_Score"] = scores.values

        for row_idx, row in prem_df.iterrows():
            prem_era   = int(row["_era_int"])
            prem_score = float(row["Local_Score"])
            branch     = str(row["_branch"])

            prem_df.at[row_idx, "Verdict"]       = VERDICT_PREM
            prem_df.at[row_idx, "Prem_Pain_Fix"] = prem_era in pain_eras

            std_branch = std_df[std_df["_branch"] == branch]
            boost = _calc_prem_boost(
                prem_era, float(row["BR"]), prem_score,
                std_branch,
                target_era=prem_era, target_br=float(row["BR"]),
            )
            prem_df.at[row_idx, "Prem_Boost"] = boost

    # ── Объединяем ────────────────────────────────────────────────────────────
    out.update(std_df)
    out.update(prem_df)

    return out
