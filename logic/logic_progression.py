from __future__ import annotations

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

_MM_WINDOW       = 1.0
_BR_FILL_WINDOW  = 1.0
_JUNK_FLOOR      = 35.0
_YELLOW_FLOOR    = 35.0
_GREEN_FLOOR     = 65.0
_YELLOW_PCTILE   = 0.30
_GREEN_PCTILE    = 0.70
_STAY_PREV_THRESHOLD = 0.85


ROMAN: dict[int, str] = {
    1: "I", 2: "II", 3: "III", 4: "IV",
    5: "V", 6: "VI", 7: "VII", 8: "VIII",
}

VERDICT_MUST = "MUST"
VERDICT_PASS = "PASS"
VERDICT_SKIP = "SKIP"
VERDICT_PREM = "PREM"
VERDICT_FILL = "FILL"

_STD_CLASS = "Standard"

def _br_decay(researcher_br: float, target_br: float) -> float:
    gap = target_br - researcher_br
    if gap <= _MM_WINDOW:
        return 1.0
    excess = gap - _MM_WINDOW
    return float(max(0.02, np.exp(-1.1 * excess)))


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


def _get_score(row: pd.Series) -> float:
    return float(row.get("META_SCORE", 0) or 0)


def _super_cat(branch: str) -> str:
    _GROUND   = {"medium_tank", "light_tank", "heavy_tank", "tank_destroyer"}
    _AVIATION = {"fighter", "bomber", "assault", "attack_helicopter", "utility_helicopter"}
    if branch == "spaa":          return "AntiAir"
    if branch in _GROUND:         return "Ground"
    if branch in _AVIATION:       return "Aviation"
    return "Fleet"

def _compute_dynamic_thresholds(all_meta: pd.Series) -> tuple[float, float, float]:
    valid = all_meta[all_meta > 1.0]
    if valid.empty:
        return _JUNK_FLOOR, _YELLOW_FLOOR, _GREEN_FLOOR

    p30 = float(valid.quantile(_YELLOW_PCTILE))
    p70 = float(valid.quantile(_GREEN_PCTILE))

    yellow = max(p30, _YELLOW_FLOOR)
    green  = max(p70, _GREEN_FLOOR)
    junk   = yellow

    return junk, yellow, green

def _lineup_score(
    era_grp:    pd.DataFrame,
    anchor_br:  float,
    junk_thresh: float,
    min_lineup: int,
) -> float:
    candidates = era_grp[
        (era_grp["META_SCORE"] >= junk_thresh) &
        (era_grp["BR"]         >= anchor_br - _BR_FILL_WINDOW) &
        (era_grp["BR"]         <= anchor_br)
    ]

    depth = len(candidates)
    if depth == 0:
        return 0.0

    avg_meta    = float(candidates["META_SCORE"].mean())
    depth_ratio = min(depth, min_lineup) / max(min_lineup, 1)
    return avg_meta * depth_ratio


def _best_anchor_for_era(
    era_grp:     pd.DataFrame,
    junk_thresh: float,
    yellow_thresh: float,
    min_lineup:  int,
) -> tuple[int | None, float, float]:
    anchor_candidates = era_grp[era_grp["META_SCORE"] >= yellow_thresh]

    if anchor_candidates.empty:
        return None, 0.0, 0.0

    best_idx   = None
    best_br    = 0.0
    best_score = -1.0

    for idx, row in anchor_candidates.iterrows():
        anchor_br = float(row["BR"])
        ls        = _lineup_score(era_grp, anchor_br, junk_thresh, min_lineup)
        if ls > best_score:
            best_score = ls
            best_br    = anchor_br
            best_idx   = idx

    return best_idx, best_br, best_score

def _rank_penalty_std(researcher_era: int, target_era: int) -> float:
    diff = target_era - researcher_era
    return RANK_PENALTY.get(diff, 0.05 if diff < 0 else 0.06)


def _rank_penalty_prem(researcher_era: int, target_era: int) -> float:
    diff = target_era - researcher_era
    return RANK_PENALTY_PREMIUM.get(diff, 1.00 if diff <= 1 else 0.06)


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

    all_meta = pd.to_numeric(out.get("META_SCORE", pd.Series(dtype=float)), errors="coerce").fillna(0)
    junk_thresh, yellow_thresh, green_thresh = _compute_dynamic_thresholds(all_meta)

    _MUST_MIN_META = yellow_thresh
    _SKIP_MAX_META = junk_thresh

    # ── Инициализация колонок ─────────────────────────────────────────────────
    out["Local_Score"]   = 0.0
    out["Verdict"]       = VERDICT_PASS
    out["Skip_Reason"]   = ""
    out["Alt_Vehicle"]   = ""
    out["Cross_Alt"]     = ""
    out["Cross_Hint"]    = ""
    out["Forward_Hint"]  = ""
    out["Prem_Boost"]    = 0.0
    out["Prem_Pain_Fix"] = False

    is_prem = out["VehicleClass"] != _STD_CLASS
    std_df  = out[~is_prem].copy()
    prem_df = out[is_prem].copy()

    # ── Сортировка по позиции в дереве ────────────────────────────────────────
    if not std_df.empty:
        std_df["_sort_key"] = _shop_sort_key(std_df)
        std_df = std_df.sort_values("_sort_key").drop(columns=["_sort_key"])
    if not prem_df.empty:
        prem_df["_sort_key"] = _shop_sort_key(prem_df)
        prem_df = prem_df.sort_values("_sort_key").drop(columns=["_sort_key"])

    # ── Local_Score = META_SCORE напрямую ─────────────────────────────────────
    if "META_SCORE" in std_df.columns:
        std_df["Local_Score"] = pd.to_numeric(std_df["META_SCORE"], errors="coerce").fillna(0)

    # ── Проход 1: MUST / PASS / SKIP ─────────────────────────────────────────
    has_groups = "vdb_shop_group" in std_df.columns

    for branch, grp in std_df.groupby("_branch"):
        srt = grp.sort_values(["BR", "Local_Score"], ascending=[True, False])
        p60 = srt["Local_Score"].quantile(0.60)

        for pos, (row_idx, row) in enumerate(srt.iterrows()):
            era     = int(row["_era_int"])
            loc_s   = float(row["Local_Score"])
            no_data = loc_s < 1.0

            our_group = str(row.get("vdb_shop_group", "") or "") if has_groups else ""

            prev         = srt.iloc[:pos]
            should_skip  = False
            reason       = ""
            alt_name     = ""

            if not prev.empty and not no_data:
                best_eff  = 0.0
                best_name = ""
                target_br = float(row["BR"])

                for _, prev_row in prev.iterrows():
                    prev_era = int(prev_row["_era_int"])
                    prev_br  = float(prev_row["BR"])
                    prev_s   = float(prev_row["Local_Score"])
                    prev_grp = str(prev_row.get("vdb_shop_group", "") or "") if has_groups else ""

                    # Не сравниваем технику из одной папки (линейки разных версий)
                    if our_group and prev_grp == our_group:
                        continue

                    pen = _combined_penalty(prev_era, prev_br, era, target_br)
                    eff = prev_s * pen
                    if eff > best_eff:
                        best_eff  = eff
                        best_name = str(prev_row["Name"])

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
                std_df.at[row_idx, "Verdict"]     = VERDICT_SKIP
                std_df.at[row_idx, "Skip_Reason"] = (
                    f"Слабая техника (META {loc_s:.0f} < {_SKIP_MAX_META:.0f})"
                )
            else:
                qualifies_must = (
                    not no_data
                    and loc_s >= p60
                    and loc_s >= _MUST_MIN_META
                )
                std_df.at[row_idx, "Verdict"] = VERDICT_MUST if qualifies_must else VERDICT_PASS

    # ── Проход 2: кросс-хинты ─────────────────────────────────────────────────
    _CROSS_THRESHOLD      = 1.30
    _CROSS_SKIP_THRESHOLD = 1.40
    _CROSS_BR_WINDOW      = 0.7
    _NO_CROSS_BRANCHES    = {"spaa"}

    std_df["_super_cat"] = std_df["_branch"].apply(_super_cat)

    if "META_SCORE" in std_df.columns:
        for row_idx, row in std_df.iterrows():
            if std_df.at[row_idx, "Verdict"] not in (VERDICT_MUST, VERDICT_PASS):
                continue

            our_meta   = float(row.get("META_SCORE", 0) or 0)
            our_br     = float(row["BR"])
            our_branch = str(row["_branch"])
            our_cat    = str(row["_super_cat"])
            our_era    = int(row["_era_int"])

            if our_meta < 1e-3 or our_branch in _NO_CROSS_BRANCHES:
                continue

            best_cross_meta = 0.0
            best_cross_name = ""
            best_cross_br   = 0.0

            mask = (
                (std_df["_branch"]    != our_branch) &
                (std_df["_super_cat"] == our_cat) &
                (std_df["_era_int"]   == our_era) &
                (std_df["BR"]         >= our_br - _CROSS_BR_WINDOW) &
                (std_df["BR"]         <= our_br + _CROSS_BR_WINDOW) &
                (std_df["Verdict"]    != VERDICT_SKIP)
            )
            for _, alt_row in std_df[mask].iterrows():
                alt_meta = float(alt_row.get("META_SCORE", 0) or 0)
                alt_br   = float(alt_row["BR"])
                eff_meta = alt_meta * _br_decay(alt_br, our_br)
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
                cur_v = std_df.at[row_idx, "Verdict"]
                if cur_v == VERDICT_MUST:
                    std_df.at[row_idx, "Verdict"] = VERDICT_PASS
                elif cur_v == VERDICT_PASS and best_cross_meta > our_meta * _CROSS_SKIP_THRESHOLD:
                    std_df.at[row_idx, "Verdict"]     = VERDICT_SKIP
                    std_df.at[row_idx, "Skip_Reason"] = (
                        f"Лучше качать «{best_cross_name}» ({best_cross_br:.1f}) "
                        f"из соседней ветки (META {best_cross_meta:.0f} vs {our_meta:.0f})"
                    )
                    std_df.at[row_idx, "Alt_Vehicle"] = best_cross_name
                    std_df.at[row_idx, "Cross_Hint"]  = ""

    # ── Проход 3: forward-хинты ───────────────────────────────────────────────
    _FORWARD_THRESHOLD = 1.35

    if "META_SCORE" in std_df.columns:
        for branch, grp in std_df.groupby("_branch"):
            srt = grp.sort_values("BR")
            for pos, (row_idx, row) in enumerate(srt.iterrows()):
                if std_df.at[row_idx, "Verdict"] != VERDICT_PASS:
                    continue
                our_meta = float(row.get("META_SCORE", 0) or 0)
                if our_meta < 1e-3:
                    continue

                best_meta = 0.0
                best_name = ""
                best_br   = 0.0
                our_era_int = int(row["_era_int"])
                for _, ahead_row in srt.iloc[pos + 1:].iterrows():
                    a_idx      = ahead_row.name
                    a_era      = int(ahead_row.get("_era_int", 0))
                    # Смотрим только в пределах текущего и следующего ранга
                    if a_era > our_era_int + 1:
                        break
                    a_meta = float(ahead_row.get("META_SCORE", 0) or 0)
                    if std_df.at[a_idx, "Verdict"] == VERDICT_SKIP:
                        continue
                    if a_meta > best_meta:
                        best_meta = a_meta
                        best_name = str(ahead_row["Name"])
                        best_br   = float(ahead_row["BR"])

    # ── «Болезненные» ранги (нет ни одного MUST) ─────────────────────────────
    era_has_must = std_df.groupby("_era_int")["Verdict"].apply(
        lambda v: (v == VERDICT_MUST).any()
    )
    pain_eras = set(era_has_must[~era_has_must].index.tolist())

    lineup_scores: dict[tuple[str, int], float] = {}
    for (super_cat, era), grp in std_df.groupby(["_super_cat", "_era_int"]):
        _, _, ls = _best_anchor_for_era(
            grp.assign(META_SCORE=pd.to_numeric(grp["META_SCORE"], errors="coerce").fillna(0)),
            junk_thresh, yellow_thresh, min_lineup,
        )
        lineup_scores[(super_cat, int(era))] = ls

    _MAIN_CATS = {"Ground", "Aviation", "Fleet"}

    era_main_cats: dict[int, set[str]] = {}
    for (super_cat, era) in lineup_scores:
        if super_cat in _MAIN_CATS:
            era_main_cats.setdefault(int(era), set()).add(super_cat)

    era_all_bad: dict[int, bool] = {}
    for era_int, cats in era_main_cats.items():
        any_good = any(lineup_scores.get((cat, era_int), 0.0) > 0 for cat in cats)
        era_all_bad[era_int] = not any_good

    era_best_ls: dict[int, float] = {}
    for era_int, cats in era_main_cats.items():
        era_best_ls[era_int] = max(
            (lineup_scores.get((cat, era_int), 0.0) for cat in cats),
            default=0.0,
        )

    # Второй проход: расставляем FILL и Stay_Era_Hint
    for (super_cat, era), grp in std_df.groupby(["_super_cat", "_era_int"]):
        era_int = int(era)
        grp_meta = grp.assign(
            META_SCORE=pd.to_numeric(grp["META_SCORE"], errors="coerce").fillna(0)
        )

        best_idx, best_anchor_br, best_ls = _best_anchor_for_era(
            grp_meta, junk_thresh, yellow_thresh, min_lineup
        )

        if era_all_bad.get(era_int, False):
            if best_idx is None:
                continue

        elif best_idx is None:
            continue

        else:
            prev_era_ls  = era_best_ls.get(era_int - 1, 0.0)
            cur_era_ls   = era_best_ls.get(era_int, 0.0)
            eff_prev_era = prev_era_ls * RANK_PENALTY.get(-1, 0.90)

            hint_already = any(
                bool(std_df.at[r, "Stay_Era_Hint"])
                for r in grp.index
                if "Stay_Era_Hint" in std_df.columns
            )
            if (
                not hint_already
                and prev_era_ls > 0
                and cur_era_ls < eff_prev_era * _STAY_PREV_THRESHOLD
            ):
                hint = (
                    f"⚠️ Ранг {ROMAN.get(era_int, str(era_int))}: "
                    f"слабая линейка (эффективность {cur_era_ls:.0f} "
                    f"< {eff_prev_era:.0f} предыдущего ранга). "
                    f"Рассмотри вариант остаться на ранге "
                    f"{ROMAN.get(era_int - 1, str(era_int - 1))}."
                )
                for row_idx in grp.index:
                    std_df.at[row_idx, "Stay_Era_Hint"] = hint

        must_count = int((grp["Verdict"] == VERDICT_MUST).sum())
        if must_count >= min_lineup:
            continue

        need = min_lineup - must_count

        candidates = grp_meta[
            (grp_meta["META_SCORE"] >= junk_thresh) &
            (grp_meta["BR"]         >= best_anchor_br - _BR_FILL_WINDOW) &
            (grp_meta["BR"]         <= best_anchor_br) &
            (~grp_meta["Verdict"].isin([VERDICT_MUST]))
        ].sort_values("META_SCORE", ascending=False)

        if candidates.empty:
            continue

        must_brs = grp_meta.loc[
            grp_meta["Verdict"] == VERDICT_MUST, "BR"
        ].tolist()

        filtered_candidates = []
        for fill_idx in candidates.index:
            cand_br = float(candidates.at[fill_idx, "BR"])
            nearby_must = any(
                abs(cand_br - mbr) <= _BR_FILL_WINDOW
                for mbr in must_brs
            )
            if not nearby_must:
                filtered_candidates.append(fill_idx)

        if not filtered_candidates:
            continue

        filled = 0
        for fill_idx in filtered_candidates:
            if filled >= need:
                break
            std_df.at[fill_idx, "Verdict"]     = VERDICT_FILL
            std_df.at[fill_idx, "Skip_Reason"] = ""
            std_df.at[fill_idx, "Alt_Vehicle"] = ""
            filled += 1

    std_df.drop(columns=["_super_cat"], errors="ignore", inplace=True)

    # ── Чистим ссылки на технику с вердиктом SKIP ─────────────────────────────
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

    # ── Премиум ───────────────────────────────────────────────────────────────
    if not prem_df.empty:
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
