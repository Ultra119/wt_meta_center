from __future__ import annotations

import numpy as np
import pandas as pd

from analytics.constants import ROLE_WEIGHTS, VEHICLE_TYPE_CATEGORY




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
    C_battles = float(settings.get("c_battles", 5000.0))
    C_spawns  = float(settings.get("c_spawns",  7500.0))
    C_deaths  = float(settings.get("c_deaths",  3000.0))

    spawns = df["Возрождения"].clip(lower=1)
    deaths = df["Смерти"].clip(lower=0)

    df["_ks_g_raw"] = df["Наземные убийства"]  / spawns
    df["_ks_a_raw"] = df["Воздушные убийства"] / spawns
    df["_ks_n_raw"] = df["Морские убийства"]   / spawns
    df["_kd_raw"]   = df["KD"]
    df["_surv_raw"] = (1.0 - (deaths / spawns)).clip(0.0, 1.0)
    df["_wr_raw"]   = (df["WR"] / 100.0).clip(0.0, 1.0)

    df["_total_kills"]      = (
        df["Наземные убийства"] +
        df["Воздушные убийства"] +
        df["Морские убийства"]
    )
    df["_survival_events"]  = (spawns - deaths).clip(lower=0)

    df["_type_group"] = df["Type"].map(VEHICLE_TYPE_CATEGORY).fillna("_other")

    metric_keys  = ["_wr", "_kd", "_ks_g", "_ks_a", "_ks_n", "_surv"]
    unique_brs   = df["BR"].unique()
    type_groups  = df["Type"].dropna().unique()
    unique_modes = df["Mode"].unique() if "Mode" in df.columns else [None]

    for k in metric_keys:
        df[k] = 0.0

    for mode in unique_modes:
        mask_mode = (df["Mode"] == mode) if mode is not None else pd.Series(True, index=df.index)
        for br in unique_brs:
            for tg in type_groups:
                mask_peer = (
                    (df["BR"] >= br - mm_window) &
                    (df["BR"] <= br + mm_window) &
                    (df["Type"] == tg) &
                    mask_mode
                )
                mask_self = (df["BR"] == br) & (df["Type"] == tg) & mask_mode

                peers = df.loc[mask_peer]
                if peers.empty:
                    continue

                peers_ext = df.loc[mask_peer & ~mask_self]
                if peers_ext.empty:
                    peers_ext = peers  # единственная техника в окне — fallback
                avg_wr   = _weighted_avg(peers_ext["_wr_raw"],   peers_ext["Сыграно игр"])
                avg_kd   = _weighted_avg(peers_ext["_kd_raw"],   peers_ext["Смерти"].clip(lower=1))
                avg_ks_g = _weighted_avg(peers_ext["_ks_g_raw"], peers_ext["Возрождения"])
                avg_ks_a = _weighted_avg(peers_ext["_ks_a_raw"], peers_ext["Возрождения"])
                avg_ks_n = _weighted_avg(peers_ext["_ks_n_raw"], peers_ext["Возрождения"])
                avg_surv = _weighted_avg(peers_ext["_surv_raw"], peers_ext["Возрождения"])

                row_slice = df.loc[mask_self]
                n_g = row_slice["Сыграно игр"]
                n_s = row_slice["Возрождения"]
                n_d = row_slice["Смерти"].clip(lower=0)

                df.loc[mask_self, "_wr"] = (
                    (row_slice["_wr_raw"] * n_g + avg_wr * C_battles)
                    / (n_g + C_battles)
                )

                df.loc[mask_self, "_kd"] = (
                    (row_slice["_total_kills"] + avg_kd * C_deaths)
                    / (n_d + C_deaths)
                )

                df.loc[mask_self, "_ks_g"] = (
                    (row_slice["Наземные убийства"] + avg_ks_g * C_spawns)
                    / (n_s + C_spawns)
                )
                df.loc[mask_self, "_ks_a"] = (
                    (row_slice["Воздушные убийства"] + avg_ks_a * C_spawns)
                    / (n_s + C_spawns)
                )
                df.loc[mask_self, "_ks_n"] = (
                    (row_slice["Морские убийства"] + avg_ks_n * C_spawns)
                    / (n_s + C_spawns)
                )
                df.loc[mask_self, "_surv"] = (
                    (row_slice["_survival_events"] + avg_surv * C_spawns)
                    / (n_s + C_spawns)
                )

    _RAW_COL: dict[str, str] = {
        "_wr":   "_wr_raw",
        "_kd":   "_kd_raw",
        "_ks_g": "_ks_g_raw",
        "_ks_a": "_ks_a_raw",
        "_ks_n": "_ks_n_raw",
        "_surv": "_surv_raw",
    }

    _global_sigma: dict[tuple, dict[str, float]] = {}
    for mode in unique_modes:
        mask_mode = (df["Mode"] == mode) if mode is not None else pd.Series(True, index=df.index)
        for tg in type_groups:
            mask_tg = (df["Type"] == tg) & mask_mode
            g = df.loc[mask_tg]
            sigs: dict[str, float] = {}
            for m_col, raw_col in _RAW_COL.items():
                vals  = g[raw_col]
                g_mu  = vals.median()
                g_mad = (vals - g_mu).abs().median()
                g_sig = g_mad * 1.4826
                sigs[m_col] = float(g_sig) if (not pd.isna(g_sig) and g_sig > 1e-9) else 0.0
            _global_sigma[(tg, mode)] = sigs

    for k in metric_keys:
        df[f"z{k}"] = 0.0

    for mode in unique_modes:
        mask_mode = (df["Mode"] == mode) if mode is not None else pd.Series(True, index=df.index)
        for br in unique_brs:
            for tg in type_groups:
                mask_peer = (
                    (df["BR"] >= br - mm_window) &
                    (df["BR"] <= br + mm_window) &
                    (df["Type"] == tg) &
                    mask_mode
                )
                mask_self = (df["BR"] == br) & (df["Type"] == tg) & mask_mode
                peers     = df.loc[mask_peer]
                g_sigs    = _global_sigma.get((tg, mode), {})

                peers_ext = df.loc[mask_peer & ~mask_self]
                if peers_ext.empty:
                    peers_ext = peers
                for m_col in metric_keys:
                    raw_col  = _RAW_COL[m_col]
                    p_raw    = peers_ext[raw_col]

                    mu    = p_raw.median()
                    mad   = (p_raw - mu).abs().median()
                    sigma = mad * 1.4826

                    if pd.isna(sigma) or sigma < 1e-9:
                        sigma = g_sigs.get(m_col, 0.0)

                    if sigma < 1e-9:
                        continue

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

        if vtype == "spaa":
            z_g    = float(row.get("z_ks_g", 0.0))
            t      = max(0.0, min(1.0, z_g / z_clip)) if z_clip > 1e-9 else 0.0
            w_spaa = ROLE_WEIGHTS["spaa"]
            w_td   = ROLE_WEIGHTS["tank_destroyer"]
            weights = {k: w_spaa[k] * (1.0 - t) + w_td[k] * t for k in w_spaa}

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

        df.at[idx, "META_SCORE"] = base_score

    df["META_SCORE"] = df["META_SCORE"].clip(0.0, 100.0)

    if "vdb_repair_cost_realistic" in df.columns:
        repair  = df["vdb_repair_cost_realistic"].fillna(0).astype(float)
        has_vdb = df.get("vdb_match_score", pd.Series(0.0, index=df.index)) > 0
        deaths_per_game = (
            df["Смерти"] / df["Сыграно игр"].clip(lower=1)
        )
        repair_per_game = repair * deaths_per_game

        net_sl = df["SL за игру"].where(~has_vdb, df["SL за игру"] - repair_per_game)
    else:
        net_sl = df["SL за игру"]

    df["_sl_eff"]        = net_sl
    df["Net SL за игру"] = net_sl.round(0).astype(int)
    df["_z_sl"]          = 0.0

    _global_sigma_sl: dict[tuple, float] = {}
    for mode in unique_modes:
        mask_mode = (df["Mode"] == mode) if mode is not None else pd.Series(True, index=df.index)
        for tg in type_groups:
            mask_tg  = (df["Type"] == tg) & mask_mode
            g_sl     = df.loc[mask_tg, "_sl_eff"]
            g_mu_sl  = g_sl.median()
            g_mad_sl = (g_sl - g_mu_sl).abs().median()
            g_sig_sl = g_mad_sl * 1.4826
            _global_sigma_sl[(tg, mode)] = (
                float(g_sig_sl) if (not pd.isna(g_sig_sl) and g_sig_sl > 1e-9) else 0.0
            )

    for mode in unique_modes:
        mask_mode = (df["Mode"] == mode) if mode is not None else pd.Series(True, index=df.index)
        for br in unique_brs:
            for tg in type_groups:
                mask_peer = (
                    (df["BR"] >= br - mm_window) &
                    (df["BR"] <= br + mm_window) &
                    (df["Type"] == tg) &
                    mask_mode
                )
                mask_self = (df["BR"] == br) & (df["Type"] == tg) & mask_mode

                peers_ext_sl = df.loc[mask_peer & ~mask_self, "_sl_eff"]
                if peers_ext_sl.empty:
                    peers_ext_sl = df.loc[mask_peer, "_sl_eff"]
                if peers_ext_sl.empty:
                    continue
                mu_sl    = peers_ext_sl.median()
                mad_sl   = (peers_ext_sl - mu_sl).abs().median()
                sigma_sl = mad_sl * 1.4826
                if pd.isna(sigma_sl) or sigma_sl < 1e-9:
                    sigma_sl = _global_sigma_sl.get((tg, mode), 0.0)
                if sigma_sl < 1e-9:
                    continue
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
