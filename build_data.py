from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

import pandas as pd

PROJECT_DIR  = os.path.dirname(os.path.abspath(__file__))
FRONTEND_PUB = os.path.join(PROJECT_DIR, "frontend", "public")
OUT_MEGA     = os.path.join(FRONTEND_PUB, "mega_db.json")
OUT_META     = os.path.join(FRONTEND_PUB, "meta_info.json")

os.makedirs(FRONTEND_PUB, exist_ok=True)

sys.path.insert(0, os.path.join(PROJECT_DIR, "analytics"))
sys.path.insert(0, PROJECT_DIR)

from analytics.core    import AnalyticsCore
from analytics.constants import WT_BR_STEPS

_KEEP_COLS = [
    # Идентификаторы
    "Name", "Nation", "BR", "Type", "Mode", "VehicleClass",
    # Статистика игр
    "Сыграно игр", "WR", "KD",
    "SL за игру", "RP за игру", "Net SL за игру",
    # Скоры
    "META_SCORE", "FARM_SCORE",
    # VehicleDB — броня
    "vdb_hull_front",  "vdb_hull_side",  "vdb_hull_rear",
    "vdb_turret_front","vdb_turret_side","vdb_turret_rear",
    # VehicleDB — двигатель / скорость
    "vdb_engine_hp_rb",     "vdb_engine_hp_ab",
    "vdb_engine_max_speed_rb","vdb_engine_max_speed_ab",
    "vdb_engine_reverse_rb",
    # VehicleDB — вооружение
    "vdb_main_caliber_mm","vdb_main_gun_speed",
    "vdb_has_thermal","vdb_has_atgm","vdb_has_heat","vdb_has_aphe",
    "vdb_ammo_types",
    # VehicleDB — классификация и экономика
    "vdb_is_premium","vdb_is_pack","vdb_squadron_vehicle",
    "vdb_on_marketplace","vdb_shop_is_gift","vdb_shop_is_event",
    "vdb_shop_rank","vdb_era","vdb_country","vdb_identifier",
    "vdb_arcade_br","vdb_realistic_br","vdb_simulator_br",
    "vdb_repair_cost_realistic","vdb_repair_cost_arcade","vdb_repair_cost_simulator",
    "vdb_ge_cost","vdb_exp_mul","vdb_sl_mul_realistic","vdb_sl_mul_arcade",
    # Shop-дерево (для ProgressionTab)
    "vdb_shop_column","vdb_shop_row","vdb_shop_nation","vdb_shop_branch",
    "vdb_shop_order","vdb_req_exp","vdb_value","vdb_required_vehicle",
    "vdb_shop_group",
    "vdb_crew_total_count","vdb_visibility","vdb_mass",
    # Матч-скор
    "vdb_match_score",
]

_ALL_VEHICLE_CLASSES = [
    "Standard","Premium","Pack","Squadron","Marketplace","Gift","Event",
]

_MODES = ["Realistic", "Arcade", "Simulator"]


def _safe_val(v):
    import math
    import numpy as np
    if isinstance(v, (np.integer,)):     return int(v)
    if isinstance(v, (np.floating,)):    return None if math.isnan(v) else float(v)
    if isinstance(v, (np.bool_,)):       return bool(v)
    if isinstance(v, float) and math.isnan(v): return None
    return v


def _df_to_records(df: pd.DataFrame) -> list[dict]:
    records = []
    cols = [c for c in _KEEP_COLS if c in df.columns]
    for row in df[cols].itertuples(index=False):
        rec = {}
        for c, v in zip(cols, row):
            rec[c] = _safe_val(v)
        records.append(rec)
    return records


def main() -> None:
    t0 = time.perf_counter()
    print("=" * 60)
    print("  WT META Center — Data Pipeline")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    core = AnalyticsCore()
    ok   = core.load_data_recursive()
    if not ok or core.full_df.empty:
        print("❌  Данные не загружены. Проверьте папку dataset/stats/")
        sys.exit(1)

    print(f"✅  full_df: {len(core.full_df)} строк")

    all_records: list[dict] = []

    for mode in _MODES:
        has_mode = (
            "Mode" in core.full_df.columns
            and mode in core.full_df["Mode"].values
        )
        if not has_mode:
            print(f"⚠️   Режим {mode} не найден — пропуск")
            continue

        print(f"\n▶  Обрабатываем режим: {mode}")

        filters = {
            "type":            "All",
            "mode":            mode,
            "search":          "",
            "nation":          "All",
            "min_br":          float(min(WT_BR_STEPS)),
            "max_br":          float(max(WT_BR_STEPS)),
            "min_battles":     1,
            "vehicle_classes": _ALL_VEHICLE_CLASSES,
        }

        df_mode = core.calculate_meta(filters)
        if df_mode.empty:
            print(f"   ℹ️  Нет данных для режима {mode}")
            continue

        records = _df_to_records(df_mode)
        all_records.extend(records)
        print(f"   ✅  {len(records)} записей")

    if not all_records:
        print("\n❌  Итоговый список пуст — JSON не записан")
        sys.exit(1)

    _WT_NATIONS = {
        "USA","Germany","USSR","Britain","Japan","Italy",
        "France","Sweden","Israel","China","Finland","Netherlands","Hungary",
    }

    all_nations_raw = (
        core.full_df["Nation"].dropna().unique().tolist()
        if "Nation" in core.full_df.columns else []
    )
    nations_list = sorted(
        n for n in all_nations_raw
        if n.strip().title() in _WT_NATIONS or n in _WT_NATIONS
    )

    all_types = (
        sorted(core.full_df["Type"].dropna().unique().tolist())
        if "Type" in core.full_df.columns else []
    )

    meta_info = {
        "generated_at":   datetime.now(timezone.utc).isoformat(),
        "nations":        nations_list,
        "types":          all_types,
        "br_steps":       WT_BR_STEPS,
        "modes":          _MODES,
        "vehicle_classes": _ALL_VEHICLE_CLASSES,
        "total_records":  len(all_records),
    }

    print(f"\n💾  Запись {OUT_MEGA} …")
    with open(OUT_MEGA, "w", encoding="utf-8") as f:
        json.dump(all_records, f, ensure_ascii=False, separators=(",", ":"))
    size_mb = os.path.getsize(OUT_MEGA) / 1_048_576
    print(f"   ✅  {len(all_records)} записей · {size_mb:.2f} MB")

    print(f"💾  Запись {OUT_META} …")
    with open(OUT_META, "w", encoding="utf-8") as f:
        json.dump(meta_info, f, ensure_ascii=False, indent=2)
    print(f"   ✅  {len(nations_list)} наций · {len(all_types)} типов")

    elapsed = time.perf_counter() - t0
    print(f"\n✅  Готово за {elapsed:.1f}с")
    print("=" * 60)


if __name__ == "__main__":
    main()
