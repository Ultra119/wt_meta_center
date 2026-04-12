from __future__ import annotations

import json
import os
from typing import Optional

import pandas as pd

from analytics.units_csv import UnitsCsvTranslator


def _parse_json_field(raw, default):
    if isinstance(raw, (dict, list)):
        return raw
    if not raw or raw in ("{}", "[]", "null", None):
        return default
    try:
        return json.loads(str(raw))
    except Exception:
        return default


def _extract_engine_stats(raw) -> dict:
    eng = _parse_json_field(raw, {})
    return {
        "vdb_engine_hp_ab":        float(eng.get("horse_power_ab",          0) or 0),
        "vdb_engine_hp_rb":        float(eng.get("horse_power_rb_sb",       0) or 0),
        "vdb_engine_max_speed_ab": float(eng.get("max_speed_ab",            0) or 0),
        "vdb_engine_max_speed_rb": float(eng.get("max_speed_rb_sb",         0) or 0),
        "vdb_engine_reverse_ab":   float(eng.get("max_reverse_speed_ab",    0) or 0),
        "vdb_engine_reverse_rb":   float(eng.get("max_reverse_speed_rb_sb", 0) or 0),
        "vdb_engine_max_rpm":      float(eng.get("max_rpm",                 0) or 0),
    }


def _extract_armor(raw) -> tuple[float, float, float]:
    lst = _parse_json_field(raw, [])
    if isinstance(lst, list) and len(lst) >= 3:
        try:
            return float(lst[0]), float(lst[1]), float(lst[2])
        except (ValueError, TypeError):
            pass
    return 0.0, 0.0, 0.0


def _extract_weapon_summary(raw) -> dict:
    weapons = _parse_json_field(raw, [])
    if not isinstance(weapons, list) or not weapons:
        return {
            "vdb_main_caliber_mm": 0.0,
            "vdb_main_gun_speed":  0.0,
            "vdb_ammo_types":      [],
            "vdb_has_atgm":        False,
            "vdb_has_heat":        False,
            "vdb_has_aphe":        False,
        }

    max_caliber = 0.0
    max_speed   = 0.0
    ammo_types: set[str] = set()

    for w in weapons:
        if not isinstance(w, dict):
            continue
        for ammo in w.get("ammos", []):
            if not isinstance(ammo, dict):
                continue
            cal   = float(ammo.get("caliber", 0) or 0) * 1000
            spd   = float(ammo.get("speed",   0) or 0)
            atype = str(ammo.get("type",      "") or "")
            if cal > max_caliber:
                max_caliber = cal
            if spd > max_speed:
                max_speed = spd
            if atype:
                ammo_types.add(atype)

    return {
        "vdb_main_caliber_mm": round(max_caliber, 1),
        "vdb_main_gun_speed":  round(max_speed,   1),
        "vdb_ammo_types":      sorted(ammo_types),
        "vdb_has_atgm":        any("atgm" in t or "guided" in t for t in ammo_types),
        "vdb_has_heat":        any("heat" in t for t in ammo_types),
        "vdb_has_aphe":        any("aphe" in t for t in ammo_types),
    }


def _extract_modifications_summary(raw) -> dict:
    mods = _parse_json_field(raw, [])
    if not isinstance(mods, list):
        return {"vdb_mod_count": 0, "vdb_mod_max_tier": 0, "vdb_mod_classes": []}

    classes: set[str] = set()
    max_tier = 0
    for m in mods:
        if not isinstance(m, dict):
            continue
        cls  = m.get("mod_class", "")
        tier = int(m.get("tier", 0) or 0)
        if cls:
            classes.add(cls)
        if tier > max_tier:
            max_tier = tier

    return {
        "vdb_mod_count":    len(mods),
        "vdb_mod_max_tier": max_tier,
        "vdb_mod_classes":  sorted(classes),
    }


def _build_vdb_row(v: dict) -> dict:
    row: dict = {}

    row.update(_extract_engine_stats(v.get("engine")))

    hf, hs, hr = _extract_armor(v.get("hull_armor",   "[]"))
    tf, ts, tr = _extract_armor(v.get("turret_armor", "[]"))
    row.update({
        "vdb_hull_front":   hf, "vdb_hull_side":   hs, "vdb_hull_rear":   hr,
        "vdb_turret_front": tf, "vdb_turret_side": ts, "vdb_turret_rear": tr,
    })

    row.update(_extract_weapon_summary(v.get("weapons")))
    row.update(_extract_modifications_summary(v.get("modifications")))

    thermal = _parse_json_field(v.get("thermal_devices"), {})
    row["vdb_has_thermal"] = isinstance(thermal, dict) and len(thermal) > 0

    _NUM_FIELDS: list[tuple[str, type, object]] = [
        ("arcade_br",                           float, 0.0),
        ("realistic_br",                        float, 0.0),
        ("simulator_br",                        float, 0.0),
        ("realistic_ground_br",                 float, 0.0),
        ("simulator_ground_br",                 float, 0.0),
        ("era",                                 int,   0  ),
        ("exp_mul",                             float, 1.0),
        ("ge_cost",                             int,   0  ),
        ("is_premium",                          int,   0  ),
        ("is_pack",                             int,   0  ),
        ("squadron_vehicle",                    int,   0  ),
        ("on_marketplace",                      int,   0  ),
        ("has_customizable_weapons",            int,   0  ),
        ("mass",                                float, 0.0),
        ("crew_total_count",                    int,   0  ),
        ("visibility",                          float, 0.0),
        ("req_exp",                             int,   0  ),
        ("value",                               int,   0  ),
        ("train1_cost",                         int,   0  ),
        ("train2_cost",                         int,   0  ),
        ("train3_cost_exp",                     int,   0  ),
        ("train3_cost_gold",                    int,   0  ),
        ("repair_cost_arcade",                  int,   0  ),
        ("repair_cost_realistic",               int,   0  ),
        ("repair_cost_simulator",               int,   0  ),
        ("repair_cost_full_upgraded_arcade",    int,   0  ),
        ("repair_cost_full_upgraded_realistic", int,   0  ),
        ("repair_cost_full_upgraded_simulator", int,   0  ),
        ("repair_cost_per_min_arcade",          int,   0  ),
        ("repair_cost_per_min_realistic",       int,   0  ),
        ("repair_cost_per_min_simulator",       int,   0  ),
        ("repair_time_arcade",                  float, 0.0),
        ("repair_time_realistic",               float, 0.0),
        ("repair_time_simulator",               float, 0.0),
        ("repair_time_no_crew_arcade",          float, 0.0),
        ("repair_time_no_crew_realistic",       float, 0.0),
        ("repair_time_no_crew_simulator",       float, 0.0),
        ("sl_mul_arcade",                       float, 1.0),
        ("sl_mul_realistic",                    float, 1.0),
        ("sl_mul_simulator",                    float, 1.0),
    ]
    for field, cast, default in _NUM_FIELDS:
        raw_val = v.get(field, default)
        try:
            row[f"vdb_{field}"] = cast(raw_val) if raw_val is not None else default
        except (ValueError, TypeError):
            row[f"vdb_{field}"] = default

    row["vdb_identifier"]       = str(v.get("identifier",       "") or "")
    row["vdb_country"]          = str(v.get("country",          "") or "")
    row["vdb_vehicle_type"]     = str(v.get("vehicle_type",     "") or "")
    row["vdb_release_date"]     = str(v.get("release_date",     "") or "")
    row["vdb_required_vehicle"] = str(v.get("required_vehicle", "") or "")
    row["vdb_version"]          = str(v.get("version",          "") or "")

    row["vdb_display_name"] = ""

    row["vdb_shop_column"] = -1
    row["vdb_shop_row"]    = -1
    row["vdb_shop_rank"]   = 0
    row["vdb_shop_group"]  = ""
    row["vdb_shop_nation"] = ""
    row["vdb_shop_branch"] = ""
    row["vdb_shop_order"]  = 99999
    row["vdb_shop_is_gift"]  = False
    row["vdb_shop_is_event"] = False

    return row




class VehicleDB:
    def __init__(self, vehicles_json_path: str) -> None:
        self._index: dict[str, dict] = {}
        self._shop_index: dict[str, dict] = {}

        dataset_dir = (
            os.path.dirname(os.path.abspath(vehicles_json_path))
            if vehicles_json_path else ""
        )

        self._units: UnitsCsvTranslator = UnitsCsvTranslator(dataset_dir)

        self._load(vehicles_json_path)

        if vehicles_json_path:
            shop_path = os.path.join(dataset_dir, "shop.blkx")
            self._load_shop(shop_path)

        self._apply_display_names()

    def _apply_display_names(self) -> None:
        if not self._units.loaded:
            return

        enriched = 0
        for identifier, row in self._index.items():
            name = self._units.find_name(identifier)
            if name:
                row["vdb_display_name"] = name
                enriched += 1

        print(
            f"[VehicleDB] 📛 Display names from units.csv: "
            f"{enriched}/{len(self._index)} matches"
        )

    def _load_shop(self, path: str) -> None:
        try:
            from analytics.shop_parser import parse_shop_file
        except ImportError:
            try:
                from shop_parser import parse_shop_file
            except ImportError:
                print("[VehicleDB] ⚠️  shop_parser not found - skipping")
                return

        shop = parse_shop_file(path)
        if not shop:
            return

        self._shop_index = shop

        updated = 0
        for vid, sdata in shop.items():
            if vid in self._index:
                self._index[vid]["vdb_shop_column"] = sdata["shop_column"]
                self._index[vid]["vdb_shop_row"]    = sdata["shop_row"]
                self._index[vid]["vdb_shop_rank"]   = sdata["shop_rank"]
                self._index[vid]["vdb_shop_group"]  = sdata["shop_group"]
                self._index[vid]["vdb_shop_nation"] = sdata["shop_nation"]
                self._index[vid]["vdb_shop_branch"] = sdata["shop_branch"]
                self._index[vid]["vdb_shop_order"]  = sdata["shop_order"]
                self._index[vid]["vdb_shop_is_gift"]  = sdata.get("shop_is_gift",  False)
                self._index[vid]["vdb_shop_is_event"] = sdata.get("shop_is_event", False)
                updated += 1

        print(
            f"[VehicleDB] 🗺️  Shop-positions: "
            f"updated {updated}/{len(shop)} entries in index"
        )


    def _load(self, path: str) -> None:
        if not os.path.exists(path):
            print(f"[VehicleDB] ⚠️  vehicles.json not found: {path}")
            return

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"[VehicleDB] ❌ Error reading vehicles.json: {e}")
            return

        if isinstance(data, dict):
            data = list(data.values())

        if not isinstance(data, list):
            print("[VehicleDB] ❌ Unexpected format from vehicles.json (not list/dict)")
            return

        for v in data:
            if not isinstance(v, dict):
                continue
            identifier = str(v.get("identifier", "") or "").strip()
            if not identifier:
                continue
            self._index[identifier] = _build_vdb_row(v)

        print(f"[VehicleDB] ✅ Downloaded {len(self._index)} entries from vehicles.json")

    def find_by_id(self, identifier: str) -> Optional[dict]:
        return self._index.get(identifier)

    def enrich_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty or "id" not in df.columns:
            df["vdb_match_score"] = 0.0
            return df

        df = df.copy()

        ids = df["id"].fillna("").astype(str)
        unique_ids = ids.unique()
        cache: dict[str, Optional[dict]] = {
            uid: self.find_by_id(uid) for uid in unique_ids
        }

        sample = next((r for r in cache.values() if r is not None), None)
        if sample is None:
            print("[VehicleDB] ⚠️  No single match — check field 'id' in dataset")
            df["vdb_match_score"] = 0.0
            return df

        for k, val in sample.items():
            if k == "vdb_display_name":
                continue
            if isinstance(val, bool):    df[k] = False
            elif isinstance(val, int):   df[k] = 0
            elif isinstance(val, float): df[k] = 0.0
            elif isinstance(val, list):  df[k] = [[] for _ in range(len(df))]
            else:                        df[k] = None

        df["vdb_match_score"] = 0.0

        matched_mask = ids.map(lambda uid: cache.get(uid) is not None)
        matched_indices = df.index[matched_mask]

        if matched_indices.any():
            vdb_records = {idx: cache[ids[idx]] for idx in matched_indices}
            vdb_df = pd.DataFrame.from_dict(vdb_records, orient="index")

            if "vdb_display_name" in vdb_df.columns and "Name" in df.columns:
                good_names = vdb_df["vdb_display_name"] != ""
                df.loc[vdb_df.index[good_names], "Name"] = (
                    vdb_df.loc[good_names, "vdb_display_name"]
                )
                vdb_df = vdb_df.drop(columns=["vdb_display_name"])

            df.update(vdb_df)
            df.loc[matched_indices, "vdb_match_score"] = 1.0

        matched = int((df["vdb_match_score"] > 0).sum())
        total   = len(df)
        pct     = 100.0 * matched / total if total else 0.0
        print(f"[VehicleDB] 🔗 Compared {matched}/{total} ({pct:.1f}%) by id-match")

        if matched < total:
            unmatched_mask = df["vdb_match_score"] == 0
            unmatched_ids  = ids[unmatched_mask]

            sample_missing = unmatched_ids[unmatched_ids != ""].head(10).tolist()
            if sample_missing:
                print(
                    f"[VehicleDB] ⚠️  Not found {total - matched} entries, "
                    f"first 10: {sample_missing}"
                )

            if self._units.loaded and "Name" in df.columns:
                name_series = unmatched_ids.map(
                    lambda uid: self._units.find_name(uid) or ""
                )
                valid_names = name_series[name_series != ""]
                if not valid_names.empty:
                    df.loc[valid_names.index, "Name"] = valid_names
                    print(
                        f"[VehicleDB] 📛 Names from units.csv "
                        f"for {len(valid_names)} unmatched entries"
                    )

            if self._shop_index:
                shop_rows: dict[int, dict] = {}
                for idx, uid in unmatched_ids.items():
                    sdata = self._shop_index.get(uid)
                    if not sdata:
                        continue
                    shop_rows[idx] = {
                        "vdb_shop_column":   sdata["shop_column"],
                        "vdb_shop_row":      sdata["shop_row"],
                        "vdb_shop_rank":     sdata["shop_rank"],
                        "vdb_shop_group":    sdata["shop_group"],
                        "vdb_shop_nation":   sdata["shop_nation"],
                        "vdb_shop_branch":   sdata["shop_branch"],
                        "vdb_shop_order":    sdata["shop_order"],
                        "vdb_shop_is_gift":  sdata.get("shop_is_gift",  False),
                        "vdb_shop_is_event": sdata.get("shop_is_event", False),
                        "vdb_identifier":    uid,
                    }

                if shop_rows:
                    shop_df = pd.DataFrame.from_dict(shop_rows, orient="index")
                    df.update(shop_df)
                    print(
                        f"[VehicleDB] 🗺️  Shop-data applied "
                        f"for {len(shop_rows)} unmatched entries"
                    )

        return df

    @property
    def loaded(self) -> bool:
        return len(self._index) > 0

    def get_by_identifier(self, identifier: str) -> Optional[dict]:
        return self._index.get(identifier)

    def stats(self) -> dict:
        return {"total": len(self._index)}

    def __len__(self) -> int:
        return len(self._index)

    def __repr__(self) -> str:
        return f"VehicleDB({len(self)} vehicles)"
