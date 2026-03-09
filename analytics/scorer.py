from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.constants import ROLE_WEIGHTS


_MODE_PRIORITY: list[str] = ["Realistic", "Simulator", "Arcade"]
_C_CONF = 500.0

_TYPE_GROUP: dict[str, str] = {
    "medium_tank":      "Ground",
    "light_tank":       "Ground",
    "heavy_tank":       "Ground",
    "tank_destroyer":   "Ground",
    "spaa":             "Ground",

    "fighter":          "Aviation",
    "bomber":           "Aviation",
    "assault":          "Aviation",
    "utility_helicopter":  "Aviation",
    "attack_helicopter":   "Aviation",

    "destroyer":        "Fleet",
    "heavy_cruiser":    "Fleet",
    "light_cruiser":    "Fleet",
    "battleship":       "Fleet",
    "battlecruiser":    "Fleet",
    "boat":             "Fleet",
    "heavy_boat":       "Fleet",
    "frigate":          "Fleet",
    "barge":            "Fleet",
}


def aggregate_modes(x: pd.DataFrame) -> pd.Series:
    if len(x) == 1:
        return x.iloc[0].copy()
    if "Mode" in x.columns:
        for preferred in _MODE_PRIORITY:
            subset = x[x["Mode"] == preferred]
            if not subset.empty:
                res = subset.iloc[0].copy()
                res["Mode"] = "Mixed"
                return res
    res = x.iloc[0].copy()
    res["Mode"] = "Mixed"
    return res

def _wilson_lower(wr_pct: pd.Series, n_games: pd.Series, z: float) -> pd.Series:
    p  = (wr_pct / 100.0).clip(0.0, 1.0)
    n  = n_games.clip(lower=1.0)
    z2 = z ** 2
    denom  = 1.0 + z2 / n
    center = (p + z2 / (2.0 * n)) / denom
    margin = (z * np.sqrt(p * (1.0 - p) / n + z2 / (4.0 * n ** 2))) / denom
    return (center - margin).clip(0.0, 1.0)


def _weighted_avg(values: pd.Series, weights: pd.Series) -> float:
    w = weights.clip(lower=0)
    total = w.sum()
    if total < 1e-9:
        return float(values.mean())
    return float((values * w).sum() / total)

def score(df: pd.DataFrame, settings: dict) -> pd.DataFrame:
    df = df.copy()

    mm_window = float(settings.get("mm_window",     1.0))
    sig_scale = float(settings.get("sigmoid_scale", 1.5))
    z_clip    = float(settings.get("z_clip",         3.0))
    wilson_z  = float(settings.get("wilson_z",      1.96))

    C_battles = 200.0
    C_spawns  = 300.0

    spawns = df["Возрождения"].clip(lower=1)
    df["_ks_g_raw"] = df["Наземные убийства"]  / spawns
    df["_ks_a_raw"] = df["Воздушные убийства"] / spawns
    df["_ks_n_raw"] = df["Морские убийства"]   / spawns
    df["_kd_raw"]   = df["KD"]
    df["_surv_raw"] = (1.0 - (df["Смерти"] / spawns)).clip(0.0, 1.0)
    df["_wr_raw"]   = _wilson_lower(df["WR"], df["Сыграно игр"], wilson_z)

    df["_type_group"] = df["Type"].map(_TYPE_GROUP).fillna("_other")

    metric_keys  = ["_wr", "_kd", "_ks_g", "_ks_a", "_ks_n", "_surv"]
    unique_brs   = df["BR"].unique()
    type_groups  = df["_type_group"].unique()

    for k in metric_keys:
        df[k] = 0.0

    for br in unique_brs:
        for tg in type_groups:
            mask_peer = (
                (df["BR"] >= br - mm_window) &
                (df["BR"] <= br + mm_window) &
                (df["_type_group"] == tg)
            )
            mask_self = (df["BR"] == br) & (df["_type_group"] == tg)

            peers = df.loc[mask_peer]
            if peers.empty:
                continue

            avg_wr   = _weighted_avg(peers["_wr_raw"],   peers["Сыграно игр"])
            avg_kd   = _weighted_avg(peers["_kd_raw"],   peers["Сыграно игр"])
            avg_ks_g = _weighted_avg(peers["_ks_g_raw"], peers["Возрождения"])
            avg_ks_a = _weighted_avg(peers["_ks_a_raw"], peers["Возрождения"])
            avg_ks_n = _weighted_avg(peers["_ks_n_raw"], peers["Возрождения"])
            avg_surv = _weighted_avg(peers["_surv_raw"],  peers["Возрождения"])

            row_slice = df.loc[mask_self]
            n_g = row_slice["Сыграно игр"]
            n_s = row_slice["Возрождения"]

            df.loc[mask_self, "_wr"] = (
                (row_slice["_wr_raw"] * n_g + avg_wr * C_battles)
                / (n_g + C_battles)
            ) * 100.0

            df.loc[mask_self, "_kd"] = (
                (row_slice["_kd_raw"] * n_g + avg_kd * C_battles)
                / (n_g + C_battles)
            )

            df.loc[mask_self, "_ks_g"] = (
                (row_slice["_ks_g_raw"] * n_s + avg_ks_g * C_spawns)
                / (n_s + C_spawns)
            )
            df.loc[mask_self, "_ks_a"] = (
                (row_slice["_ks_a_raw"] * n_s + avg_ks_a * C_spawns)
                / (n_s + C_spawns)
            )
            df.loc[mask_self, "_ks_n"] = (
                (row_slice["_ks_n_raw"] * n_s + avg_ks_n * C_spawns)
                / (n_s + C_spawns)
            )
            df.loc[mask_self, "_surv"] = (
                (row_slice["_surv_raw"] * n_s + avg_surv * C_spawns)
                / (n_s + C_spawns)
            )

    for k in metric_keys:
        df[f"z{k}"] = 0.0

    for br in unique_brs:
        for tg in type_groups:
            mask_peer = (
                (df["BR"] >= br - mm_window) &
                (df["BR"] <= br + mm_window) &
                (df["_type_group"] == tg)
            )
            mask_self = (df["BR"] == br) & (df["_type_group"] == tg)
            peers = df.loc[mask_peer]

            for m_col in metric_keys:
                p_vals = peers[m_col]
                mu     = p_vals.mean()
                sigma  = p_vals.std()
                if pd.isna(sigma) or sigma < 1e-9:
                    sigma = 1.0
                df.loc[mask_self, f"z{m_col}"] = (
                    (df.loc[mask_self, m_col] - mu) / sigma
                ).clip(-z_clip, z_clip)

    def _sigmoid(z_col: str) -> pd.Series:
        return 100.0 / (1.0 + np.exp(-sig_scale * df[z_col]))

    s_wr   = _sigmoid("z_wr")
    s_kd   = _sigmoid("z_kd")
    s_ks_g = _sigmoid("z_ks_g")
    s_ks_a = _sigmoid("z_ks_a")
    s_ks_n = _sigmoid("z_ks_n")
    s_surv = _sigmoid("z_surv")

    df["META_SCORE"] = 0.0

    for idx, row in df.iterrows():
        vtype   = row["Type"]
        weights = ROLE_WEIGHTS.get(vtype, ROLE_WEIGHTS["_default"]).copy()

        if vtype == "spaa" and row["_ks_g"] > row["_ks_a"] * 1.5:
            weights = ROLE_WEIGHTS["tank_destroyer"].copy()

        w_sum = sum(weights.values())
        if w_sum > 1e-9:
            for k in weights:
                weights[k] /= w_sum

        base_score = (
            weights.get("wr",   0) * s_wr[idx]   +
            weights.get("kd",   0) * s_kd[idx]   +
            weights.get("ks_g", 0) * s_ks_g[idx] +
            weights.get("ks_a", 0) * s_ks_a[idx] +
            weights.get("ks_n", 0) * s_ks_n[idx] +
            weights.get("surv", 0) * s_surv[idx]
        )

        battles     = float(row["Сыграно игр"])
        confidence  = battles / (battles + _C_CONF)
        final_score = 50.0 + (base_score - 50.0) * confidence

        df.at[idx, "META_SCORE"] = final_score

    df["META_SCORE"] = df["META_SCORE"].clip(0.0, 100.0)

    if "vdb_repair_cost_realistic" in df.columns:
        repair  = df["vdb_repair_cost_realistic"].fillna(0).astype(float)
        has_vdb = df.get("vdb_match_score", pd.Series(0.0, index=df.index)) > 0
        net_sl  = df["SL за игру"].where(~has_vdb, df["SL за игру"] - repair)
    else:
        net_sl = df["SL за игру"]

    df["_sl_eff"]       = net_sl.clip(lower=0) * (df["_wr"] / 50.0).clip(lower=0.5)
    df["Net SL за игру"] = net_sl.round(0).astype(int)
    df["_z_sl"]         = 0.0

    for br in unique_brs:
        for tg in type_groups:
            mask_peer = (
                (df["BR"] >= br - mm_window) &
                (df["BR"] <= br + mm_window) &
                (df["_type_group"] == tg)
            )
            mask_self = (df["BR"] == br) & (df["_type_group"] == tg)
            peers_sl  = df.loc[mask_peer, "_sl_eff"]
            if peers_sl.empty:
                continue
            mu_sl    = peers_sl.mean()
            sigma_sl = peers_sl.std()
            if pd.isna(sigma_sl) or sigma_sl < 1e-9:
                sigma_sl = 1.0
            df.loc[mask_self, "_z_sl"] = (
                (df.loc[mask_self, "_sl_eff"] - mu_sl) / sigma_sl
            ).clip(-z_clip, z_clip)

    df["FARM_SCORE"] = (
        100.0 / (1.0 + np.exp(-sig_scale * df["_z_sl"]))
    ).clip(0, 100)

    drop_cols = [
        c for c in df.columns
        if (c.startswith("_") or c.startswith("z_")) and c != "Net SL за игру"
    ]
    df.drop(columns=drop_cols, inplace=True, errors="ignore")

    return df
