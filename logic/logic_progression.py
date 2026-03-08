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
VERDICT_FILL = "FILL"

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


_MUST_MIN_META = 42.0
_SKIP_MAX_META = 30.0
_SKIP_FLOOR_META = 30.0


def _minmax(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx - mn < 1e-9:
        return pd.Series(50.0, index=series.index)
    return (series - mn) / (mx - mn) * 100.0


def _get_score(row: pd.Series) -> float:
    return float(row.get("META_SCORE", 0) or 0)


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


def build_progression_data(
    df: pd.DataFrame,
    nation: str,
    min_lineup: int = 4,
    excluded_types: list | None = None,
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()

    out = df[df["Nation"] == nation].copy() if nation != "All" else df.copy()
    if out.empty:
        return pd.DataFrame()

    if excluded_types:
        out = out[~out["Type"].isin(excluded_types)]
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

    # Проход 1-S: Local_Score = META_SCORE напрямую (глобальный, не нормализуем)
    if "META_SCORE" in std_df.columns:
        std_df["Local_Score"] = pd.to_numeric(std_df["META_SCORE"], errors="coerce").fillna(0)

    # Проход 2-S: вердикты
    _GROUND_BRANCHES   = {"medium_tank", "light_tank", "heavy_tank", "tank_destroyer"}
    _AVIATION_BRANCHES = {"fighter", "bomber", "assault", "attack_helicopter", "utility_helicopter"}

    def _super_cat(branch: str) -> str:
        if branch == "spaa":              return "AntiAir"
        if branch in _GROUND_BRANCHES:   return "Ground"
        if branch in _AVIATION_BRANCHES: return "Aviation"
        return "Fleet"

    has_groups = "vdb_shop_group" in std_df.columns

    for branch, grp in std_df.groupby("_branch"):
        srt   = grp.sort_values(["BR", "Local_Score"], ascending=[True, False])
        p60   = srt["Local_Score"].quantile(0.60)

        for pos, (row_idx, row) in enumerate(srt.iterrows()):
            era     = int(row["_era_int"])
            loc_s   = float(row["Local_Score"])
            no_data = loc_s < 1.0

            # Группа папки — не скипаем технику из той же shop-группы
            our_group = str(row.get("vdb_shop_group", "") or "") if has_groups else ""

            prev = srt.iloc[:pos]
            should_skip = False
            reason      = ""
            alt_name    = ""

            if not prev.empty and not no_data:
                best_eff  = 0.0
                best_name = ""
                best_br   = -1.0
                target_br = float(row["BR"])

                for prev_idx, prev_row in prev.iterrows():
                    if std_df.at[prev_idx, "Verdict"] in (VERDICT_SKIP, VERDICT_MUST):
                        continue
                    if float(prev_row.get("META_SCORE", 0) or 0) < 1.0:
                        continue
                    prev_br = float(prev_row["BR"])
                    if target_br - prev_br > _MM_WINDOW:
                        continue
                    prev_group = str(prev_row.get("vdb_shop_group", "") or "") if has_groups else ""
                    if our_group and our_group == prev_group:
                        continue
                    pen = _combined_penalty(
                        researcher_era=int(prev_row["_era_int"]),
                        researcher_br=float(prev_row["BR"]),
                        target_era=era,
                        target_br=target_br,
                    )
                    eff = float(prev_row["Local_Score"]) * pen
                    if eff > best_eff or (eff >= best_eff * 0.999 and prev_br > best_br):
                        best_eff  = eff
                        best_name = str(prev_row["Name"])
                        best_br   = prev_br

                if best_eff > loc_s * 1.05:
                    should_skip = True
                    reason = (
                        f"Эффективнее прокачивать ветку на «{best_name}» "
                        f"(META {best_eff:.0f} vs {loc_s:.0f})"
                    )
                    alt_name = best_name

            if should_skip:
                std_df.at[row_idx, "Verdict"]     = VERDICT_SKIP
                std_df.at[row_idx, "Skip_Reason"] = reason
                std_df.at[row_idx, "Alt_Vehicle"] = alt_name
            elif not no_data and loc_s < _SKIP_MAX_META:
                # Абсолютно слабая техника — скип без объяснений через альтернативу
                std_df.at[row_idx, "Verdict"]     = VERDICT_SKIP
                std_df.at[row_idx, "Skip_Reason"] = (
                    f"Слабая техника (META {loc_s:.0f} < {_SKIP_MAX_META:.0f}) — "
                )
            else:
                qualifies_must = (
                    not no_data
                    and (loc_s >= p60)
                    and (loc_s >= _MUST_MIN_META)
                )
                std_df.at[row_idx, "Verdict"] = VERDICT_MUST if qualifies_must else VERDICT_PASS

    _CROSS_THRESHOLD      = 1.30
    _CROSS_SKIP_THRESHOLD = 1.40
    _CROSS_BR_WINDOW      = 0.7
    _NO_CROSS_BRANCHES = {"spaa"}

    # Предвычисляем суперкатегорию один раз
    std_df["_super_cat"] = std_df["_branch"].apply(_super_cat)

    if "META_SCORE" in std_df.columns:
        for row_idx, row in std_df.iterrows():
            if std_df.at[row_idx, "Verdict"] not in (VERDICT_MUST, VERDICT_PASS):
                continue

            our_meta   = float(row.get("META_SCORE", 0) or 0)
            our_br     = float(row["BR"])
            our_branch = str(row["_branch"])
            our_cat    = str(row["_super_cat"])

            if our_meta < 1e-3 or our_branch in _NO_CROSS_BRANCHES:
                continue

            best_cross_meta = 0.0
            best_cross_name = ""
            best_cross_br   = 0.0

            our_era    = int(row["_era_int"])

            mask = (
                (std_df["_branch"]    != our_branch) &
                (std_df["_super_cat"] == our_cat) &
                (std_df["_era_int"]   == our_era) &
                (std_df["BR"] >= our_br - _CROSS_BR_WINDOW) &
                (std_df["BR"] <= our_br + _CROSS_BR_WINDOW) &
                (std_df["Verdict"]    != VERDICT_SKIP)
            )
            for alt_idx, alt_row in std_df[mask].iterrows():
                alt_meta = float(alt_row.get("META_SCORE", 0) or 0)
                alt_br   = float(alt_row["BR"])
                decay        = _br_decay(alt_br, our_br)
                eff_meta     = alt_meta * decay
                if eff_meta > best_cross_meta:
                    best_cross_meta = eff_meta
                    best_cross_name = str(alt_row["Name"])
                    best_cross_br   = alt_br

            if best_cross_meta > our_meta * _CROSS_THRESHOLD:
                std_df.at[row_idx, "Cross_Alt"]  = best_cross_name
                std_df.at[row_idx, "Cross_Hint"] = (
                    f"Для сетапа лучше «{best_cross_name}» ({best_cross_br:.1f}) "
                    f"— он сильнее в своём BR"
                )
                cur_verdict = std_df.at[row_idx, "Verdict"]
                if cur_verdict == VERDICT_MUST:
                    std_df.at[row_idx, "Verdict"] = VERDICT_PASS
                elif (
                    cur_verdict == VERDICT_PASS
                    and best_cross_meta > our_meta * _CROSS_SKIP_THRESHOLD
                ):
                    std_df.at[row_idx, "Verdict"]     = VERDICT_SKIP
                    std_df.at[row_idx, "Skip_Reason"] = (
                        f"Лучше качать «{best_cross_name}» ({best_cross_br:.1f}) "
                        f"из соседней ветки (META {best_cross_meta:.0f} vs {our_meta:.0f})"
                    )
                    std_df.at[row_idx, "Alt_Vehicle"] = best_cross_name
                    std_df.at[row_idx, "Cross_Hint"]  = ""

    if "Cross_Alt" not in std_df.columns:
        std_df["Cross_Alt"]  = ""
        std_df["Cross_Hint"] = ""

    std_df["Forward_Hint"] = ""


    _FORWARD_THRESHOLD = 1.35

    if "META_SCORE" in std_df.columns:
        for branch, grp in std_df.groupby("_branch"):
            srt = grp.sort_values("BR")

            for pos, (row_idx, row) in enumerate(srt.iterrows()):
                if std_df.at[row_idx, "Verdict"] not in (VERDICT_PASS,):
                    continue

                our_meta = float(row.get("META_SCORE", 0) or 0)
                if our_meta < 1e-3:
                    continue

                # Смотрим только на технику ВПЕРЕДИ (выше по BR)
                ahead = srt.iloc[pos + 1:]
                if ahead.empty:
                    continue

                best_meta = 0.0
                best_name = ""
                best_br   = 0.0

                for _, ahead_row in ahead.iterrows():
                    a_idx  = ahead_row.name
                    a_meta = float(ahead_row.get("META_SCORE", 0) or 0)
                    if std_df.at[a_idx, "Verdict"] == VERDICT_SKIP:
                        continue
                    if a_meta > best_meta:
                        best_meta = a_meta
                        best_name = str(ahead_row["Name"])
                        best_br   = float(ahead_row["BR"])

                if best_meta > our_meta * _FORWARD_THRESHOLD:
                    std_df.at[row_idx, "Forward_Hint"] = (
                        f"Терпи — впереди «{best_name}» ({best_br:.1f}) "
                        f"намного сильнее"
                    )

    # «Болезненные» ранги — нет ни одного MUST среди стандарта
    era_has_must = std_df.groupby("_era_int")["Verdict"].apply(
        lambda v: (v == VERDICT_MUST).any()
    )
    pain_eras = set(era_has_must[~era_has_must].index.tolist())

    _BR_FILL_WINDOW = 1.0

    std_df["_super_cat"] = std_df["_branch"].apply(_super_cat)

    for (super_cat, era), grp in std_df.groupby(["_super_cat", "_era_int"]):
        must_rows = grp[grp["Verdict"] == VERDICT_MUST]
        n_must    = len(must_rows)
        if n_must >= min_lineup:
            continue

        # Опорный BR — лучший MUST в этом ранге; если MUST нет — медиана ранга
        if not must_rows.empty:
            anchor_br = float(must_rows.loc[
                must_rows["META_SCORE"].idxmax(), "BR"
            ])
        else:
            anchor_br = float(grp["BR"].median())

        need = min_lineup - n_must

        candidates = grp[
            (grp["Verdict"].isin([VERDICT_PASS, VERDICT_SKIP])) &
            (grp["BR"] >= anchor_br - _BR_FILL_WINDOW) &
            (grp["BR"] <= anchor_br + _BR_FILL_WINDOW)
        ].copy()

        if candidates.empty:
            continue

        candidates = candidates.sort_values("META_SCORE", ascending=False)
        for fill_idx in candidates.index[:need]:
            std_df.at[fill_idx, "Verdict"]     = VERDICT_FILL
            std_df.at[fill_idx, "Skip_Reason"] = ""
            std_df.at[fill_idx, "Alt_Vehicle"] = ""

    std_df.drop(columns=["_super_cat"], errors="ignore", inplace=True)

    skip_names: set[str] = set(
        std_df.loc[std_df["Verdict"] == VERDICT_SKIP, "Name"].tolist()
    )
    if skip_names:
        for row_idx in std_df.index:
            alt = str(std_df.at[row_idx, "Alt_Vehicle"] or "")
            if alt in skip_names:
                std_df.at[row_idx, "Skip_Reason"] = ""
                std_df.at[row_idx, "Alt_Vehicle"] = ""
                std_df.at[row_idx, "Verdict"]     = VERDICT_PASS

            cross = str(std_df.at[row_idx, "Cross_Alt"] or "")
            if cross in skip_names:
                std_df.at[row_idx, "Cross_Alt"]  = ""
                std_df.at[row_idx, "Cross_Hint"] = ""

            fwd = str(std_df.at[row_idx, "Forward_Hint"] or "")
            if fwd and any(name in fwd for name in skip_names):
                std_df.at[row_idx, "Forward_Hint"] = ""

    if not prem_df.empty:
        # Local_Score для премиума = его META_SCORE напрямую
        for idx in prem_df.index:
            prem_df.at[idx, "Local_Score"] = _get_score(prem_df.loc[idx])

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
