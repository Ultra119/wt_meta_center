"""
Общие функции для колбэков: построение фильтров, применение типов.
"""
import json
import pandas as pd

from analytics.constants import WT_BR_STEPS
from ui.type_filter import TypeFilterData, get_types_from_checkboxes

BR_MIN = float(min(WT_BR_STEPS))
BR_MAX = float(max(WT_BR_STEPS))

# Глобальные ссылки, заполняются при регистрации колбэков
_all_types: list = []
_tf_data:   TypeFilterData | None = None


def init(all_types: list, tf_data: TypeFilterData) -> None:
    global _all_types, _tf_data
    _all_types = all_types
    _tf_data   = tf_data


def get_types(ground, air, lf, sf) -> list:
    return get_types_from_checkboxes(
        ground=bool(ground), aviation=bool(air),
        large_fleet=bool(lf), small_fleet=bool(sf),
        all_types=_all_types,
        type_to_cat=_tf_data.type_to_cat if _tf_data else {},
    )


def apply_type_filter(df: pd.DataFrame, types_list: list) -> pd.DataFrame:
    if not types_list or df.empty:
        return pd.DataFrame()
    return df[df["Type"].isin(types_list)]


def build_filters(
    mode, battles, classes,
    nation="All",
    br_range=None,
) -> dict:
    return {
        "type":            "All",
        "mode":            mode or "All/Mixed",
        "search":          "",
        "nation":          nation or "All",
        "min_br":          float(br_range[0]) if br_range else BR_MIN,
        "max_br":          float(br_range[1]) if br_range else BR_MAX,
        "min_battles":     int(battles or 50),
        "vehicle_classes": classes or ["Standard", "Premium", "Pack", "Squadron", "Marketplace"],
    }


def filters_from_meta_store(meta_f_json: str | None, mode, battles, classes) -> dict:
    """Берёт диапазон BR из сохранённых meta-фильтров, остальное из сайдбара."""
    base = build_filters(mode, battles, classes)
    if meta_f_json:
        try:
            f = json.loads(meta_f_json)
            base["min_br"] = f.get("min_br", BR_MIN)
            base["max_br"] = f.get("max_br", BR_MAX)
        except Exception:
            pass
    return base
