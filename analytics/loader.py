import json
import os
import re

import pandas as pd

from logger import log_debug
from analytics.constants import VEHICLE_TYPE_CATEGORY, snap_to_wt_br

_PERIOD_RE = re.compile(r'^\d{1,2}-\d{4}$')


def load_json_files(script_dir: str) -> list:
    with open("debug_log.txt", "w", encoding="utf-8") as f:
        f.write("=== ЗАПУСК WT META CENTER v5.0 ===\n")

    all_data: list = []
    skip_files = {"settings.json", "vehicles.json"}

    for root, _dirs, files in os.walk(script_dir):
        for filename in files:
            if not filename.endswith(".json") or filename in skip_files:
                continue

            rel_path  = os.path.relpath(root, script_dir)
            first_sub = rel_path.split(os.sep)[0] if rel_path != "." else ""

            dir_category = first_sub if first_sub else "Uncategorized"

            period = first_sub if _PERIOD_RE.match(first_sub) else "All"

            name_parts = filename.replace(".json", "").split("_")
            nation = name_parts[0] if name_parts else "Unknown"
            _raw_mode = name_parts[1] if len(name_parts) > 1 else "Unknown"
            _MODE_NORM = {
                "rb": "Realistic", "realistic": "Realistic",
                "ab": "Arcade",    "arcade":    "Arcade",
                "sim": "Simulator","sb":        "Simulator", "simulator": "Simulator",
            }
            mode = _MODE_NORM.get(_raw_mode.lower(), _raw_mode.capitalize())

            try:
                with open(os.path.join(root, filename), "r", encoding="utf-8") as f:
                    data = json.load(f)
                for entry in data:
                    entry["_dir_category"] = dir_category
                    entry["Nation"]        = nation
                    entry["Mode"]          = mode
                    entry["Period"]        = period
                all_data.extend(data)
            except Exception as e:
                log_debug(f"Ошибка файла {filename}: {e}")

    return all_data


def extract_br(raw: str) -> float:
    s = str(raw)
    if "БР" in s:
        try:
            parts = s.split()
            idx   = parts.index("БР")
            if idx + 1 < len(parts):
                return float(parts[idx + 1])
        except Exception:
            pass
    match = re.search(r"\b(\d+\.\d+)\b", s)
    return float(match.group(1)) if match else 0.0


def clean_dataframe(df: pd.DataFrame, vehicle_db) -> pd.DataFrame:
    if "vehicle_type" in df.columns:
        vt = df["vehicle_type"].astype(str).str.strip()
        vt = vt.replace({"nan": "", "None": "", "none": ""})
        fallback = df["_dir_category"] if "_dir_category" in df.columns else "Uncategorized"
        df["Type"] = vt.where(vt != "", fallback)
    else:
        df["Type"] = df["_dir_category"] if "_dir_category" in df.columns else "Uncategorized"

    if "Name" in df.columns:
        df["Name"] = df["Name"].astype(str)
    else:
        df["Name"] = ""

    df["Category"] = df["Type"].map(VEHICLE_TYPE_CATEGORY).fillna("Uncategorized")

    if "vehicle_sub_types" in df.columns:
        df["vehicle_sub_types"] = df["vehicle_sub_types"].apply(_parse_json_list)
    else:
        df["vehicle_sub_types"] = [[] for _ in range(len(df))]

    for col in ("value", "train1_cost", "train2_cost",
                "train3_cost_exp", "train3_cost_gold"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)
        else:
            df[col] = 0

    if "visibility" in df.columns:
        df["visibility"] = pd.to_numeric(df["visibility"], errors="coerce").fillna(0)
    else:
        df["visibility"] = 0

    if "version" not in df.columns:
        df["version"] = ""
    else:
        df["version"] = df["version"].fillna("").astype(str)

    if "thermal_devices" in df.columns:
        df["thermal_devices"] = df["thermal_devices"].apply(_parse_json_dict)
    else:
        df["thermal_devices"] = [{} for _ in range(len(df))]

    if "turret_armor" in df.columns:
        df["turret_armor"] = df["turret_armor"].apply(_parse_json_list)
    else:
        df["turret_armor"] = [[] for _ in range(len(df))]

    if "weapons" in df.columns:
        df["weapons"] = df["weapons"].apply(_parse_json_list)
        df["weapons_count"] = df["weapons"].apply(
            lambda ws: sum(w.get("count", 1) for w in ws)
        )
        df["weapon_types"] = df["weapons"].apply(
            lambda ws: list({w.get("weapon_type", "unknown") for w in ws})
        )
    else:
        df["weapons"]       = [[] for _ in range(len(df))]
        df["weapons_count"] = 0
        df["weapon_types"]  = [[] for _ in range(len(df))]

    int_cols = [
        "Сыграно игр", "Победы", "Возрождения", "Смерти",
        "Наземные убийства", "Воздушные убийства", "Морские убийства",
        "Убийств за возрождение",
    ]

    if "Морские убийства" not in df.columns:
        df["Морские убийства"] = 0
    for col in int_cols:
        if col in df.columns:
            s = df[col].astype(str).str.replace(",", "", regex=False)
            s = s.map(lambda v: "0" if v.strip() in ("N/A", "None", "nan", "") else v)
            df[col] = pd.to_numeric(s, errors="coerce").fillna(0)

    for col in ("SL за игру", "RP за игру"):
        if col in df.columns:
            s = (
                df[col].astype(str)
                       .str.replace(",", "", regex=False)
                       .str.replace(" ", "", regex=False)
            )
            s = s.map(lambda v: "0" if v.strip() in ("N/A", "None", "nan", "") else v)
            df[col] = pd.to_numeric(s, errors="coerce").fillna(0)
        else:
            df[col] = 0.0

    if "Убийств за смерть" in df.columns:
        s = df["Убийств за смерть"].astype(str).str.replace(",", ".", regex=False)
        s = s.map(lambda v: "0" if v.strip() in ("N/A", "None", "nan", "") else v)
        df["KD"] = pd.to_numeric(s, errors="coerce").fillna(0)
    else:
        df["KD"] = 0.0

    if "Процент побед" in df.columns:
        s = df["Процент побед"].astype(str).str.replace("%", "", regex=False)
        s = s.map(lambda v: "0" if v.strip() in ("N/A", "None", "nan", "") else v)
        df["WR"] = pd.to_numeric(s, errors="coerce").fillna(0)
    else:
        df["WR"] = 0.0

    raw_br = (
        df["Rank_Info"].apply(extract_br)
        if "Rank_Info" in df.columns
        else pd.Series(0.0, index=df.index)
    )
    df["BR"] = raw_br.apply(snap_to_wt_br)

    df.drop(columns=["_dir_category"], errors="ignore", inplace=True)

    if vehicle_db is not None and vehicle_db.loaded:
        df = vehicle_db.enrich_dataframe(df)
        df = df.copy()

        matched = int((df.get("vdb_match_score", 0) > 0).sum())
        log_debug(
            f"[VehicleDB] vdb_ матч завершён. "
            f"Сопоставлено: {matched}/{len(df)}"
        )

        if "vdb_vehicle_type" in df.columns:
            good_match = df.get("vdb_match_score", pd.Series(0.0, index=df.index)) > 0
            vdb_vt = df["vdb_vehicle_type"].astype(str).str.strip()
            valid  = good_match & vdb_vt.isin(["", "nan"]).eq(False)
            df.loc[valid, "Type"] = df.loc[valid, "vdb_vehicle_type"]
            log_debug(
                f"[VehicleDB] Type уточнён для {int(valid.sum())} строк "
                f"из {len(df)} (через vdb_vehicle_type)"
            )

    def _derive_class(row) -> str:
        if int(row.get("vdb_is_pack",          0) or 0): return "Pack"
        if int(row.get("vdb_on_marketplace",   0) or 0): return "Marketplace"
        if int(row.get("vdb_squadron_vehicle", 0) or 0): return "Squadron"
        if     row.get("vdb_shop_is_event", False):      return "Event"
        if     row.get("vdb_shop_is_gift",  False):      return "Gift"
        if int(row.get("vdb_is_premium",       0) or 0): return "Premium"
        return "Standard"

    _vdb_flag_cols = [
        "vdb_is_premium", "vdb_is_pack", "vdb_squadron_vehicle",
        "vdb_on_marketplace", "vdb_shop_is_gift", "vdb_shop_is_event",
    ]
    if all(c in df.columns for c in _vdb_flag_cols):
        df["VehicleClass"] = df.apply(_derive_class, axis=1)
    else:
        df["VehicleClass"] = "Standard"

    return df


def _parse_json_list(raw) -> list:
    if isinstance(raw, list):
        return raw
    try:
        return json.loads(str(raw)) if raw not in (None, "", "[]") else []
    except Exception:
        return []


def _parse_json_dict(raw) -> dict:
    if isinstance(raw, dict):
        return raw
    try:
        parsed = json.loads(str(raw)) if raw not in (None, "", "{}") else {}
        return parsed if isinstance(parsed, dict) else {}
    except Exception:
        return {}
