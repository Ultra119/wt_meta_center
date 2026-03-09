import os

import pandas as pd

from analytics.config    import load_settings
from analytics.loader    import load_json_files, clean_dataframe
from analytics.scorer    import aggregate_modes, score
from vehicle_db          import VehicleDB
from logic.logic_nations  import calculate_nation_dominance
from logic.logic_farm     import get_farm_set      as _get_farm_set
from logic.logic_brackets import get_bracket_stats as _get_bracket_stats


class AnalyticsCore:
    def __init__(self) -> None:
        self._project_dir: str = os.path.dirname(
            os.path.dirname(os.path.abspath(__file__))
        )

        self.settings:     dict         = load_settings(self._project_dir)
        self.full_df:      pd.DataFrame = pd.DataFrame()
        self.display_df:   pd.DataFrame = pd.DataFrame()
        self.nation_stats: pd.DataFrame = pd.DataFrame()

        _vehicles_path      = os.path.join(self._project_dir, "dataset", "vehicles.json")
        self.vehicle_db: VehicleDB = VehicleDB(_vehicles_path)

    def reload_settings(self) -> None:
        """Перечитать settings.json без перезагрузки данных (вызывается из GUI)."""
        self.settings = load_settings(self._project_dir)

    def load_data_recursive(self) -> bool:
        raw_records = load_json_files(os.path.join(self._project_dir, "dataset", "stats"))
        if not raw_records:
            return False

        raw_df       = pd.DataFrame(raw_records)
        self.full_df = clean_dataframe(raw_df, self.vehicle_db)
        return True

    def calculate_meta(self, filters: dict) -> pd.DataFrame:
        """
          type        — тип техники ("All" = без фильтра)
          mode        — игровой режим ("All/Mixed" = без фильтра)
          search      — строка поиска по Name (пустая строка = без фильтра)
          nation      — нация ("All" = без фильтра)
          min_br      — минимальный BR
          max_br      — максимальный BR
          min_battles — минимальное число сыгранных боёв
        """
        df = self.full_df.copy()
        if df.empty:
            return df

        if filters["type"] != "All":
            df = df[df["Type"] == filters["type"]]
        if filters["mode"] != "All/Mixed":
            df = df[df["Mode"] == filters["mode"]]
        if filters["search"]:
            df = df[df["Name"].str.contains(filters["search"], case=False, na=False)]

        vehicle_classes = filters.get("vehicle_classes", [])
        if vehicle_classes and "VehicleClass" in df.columns:
            df = df[df["VehicleClass"].isin(vehicle_classes)]

        if df.empty:
            return pd.DataFrame()

        group_cols    = ["Name", "Nation", "BR", "Type"]
        existing_cols = [c for c in group_cols if c in df.columns]

        df_grouped = (
            df.groupby(existing_cols, group_keys=True)
              .apply(aggregate_modes, include_groups=False)
              .reset_index()
        )

        df_grouped = df_grouped[
            (df_grouped["BR"]          >= filters["min_br"])   &
            (df_grouped["BR"]          <= filters["max_br"])   &
            (df_grouped["Сыграно игр"] >= filters["min_battles"])
        ]

        if filters["nation"] != "All":
            df_grouped = df_grouped[df_grouped["Nation"] == filters["nation"]]

        if not df_grouped.empty:
            df_grouped = score(df_grouped, self.settings)

        self.display_df   = df_grouped.round(2)
        self.nation_stats = calculate_nation_dominance(self.display_df, self.settings)
        return self.display_df

    def _calculate_nation_dominance(self) -> None:
        self.nation_stats = calculate_nation_dominance(self.display_df, self.settings)

    def get_farm_set(
        self,
        target_br: float,
        nation: str = "All",
        vehicle_type: str = "All",
    ) -> dict:
        return _get_farm_set(self.display_df, target_br, nation, vehicle_type)

    def get_bracket_stats(
        self,
        step: int = 3,
        top_n: "int | None" = None,
        exclude_spaa: bool = False,
    ) -> pd.DataFrame:
        return _get_bracket_stats(self.display_df, step, top_n, exclude_spaa)

    def get_progression_data(self, nation: str, mode: str = "All/Mixed") -> "pd.DataFrame":
        """
        Возвращает scored DataFrame для одной нации.
        """
        _MODE_PRIORITY = ["Realistic", "Simulator", "Arcade"]

        df = self.full_df.copy()
        if df.empty:
            return pd.DataFrame()

        # ── Фильтр/дедупликация по режиму ────────────────────────────────
        if "Mode" in df.columns:
            if mode != "All/Mixed":
                df = df[df["Mode"] == mode]
            else:
                key_cols = [c for c in ["Name", "Nation"] if c in df.columns]
                chosen_parts = []
                for _, grp in df.groupby(key_cols, sort=False):
                    for preferred in _MODE_PRIORITY:
                        subset = grp[grp["Mode"] == preferred]
                        if not subset.empty:
                            chosen_parts.append(subset)
                            break
                    else:
                        chosen_parts.append(grp)
                df = pd.concat(chosen_parts, ignore_index=True) if chosen_parts else df

        if df.empty:
            return pd.DataFrame()

        group_cols = [c for c in ["Name", "Nation", "BR", "Type"] if c in df.columns]
        try:
            df_grouped = (
                df.groupby(group_cols, group_keys=True)
                  .apply(aggregate_modes, include_groups=False)
                  .reset_index()
            )
        except TypeError:
            df_grouped = (
                df.groupby(group_cols, group_keys=True)
                  .apply(aggregate_modes)
                  .reset_index()
            )

        if df_grouped.empty:
            return pd.DataFrame()

        # Переносим VehicleClass и vdb_* из full_df (они теряются при groupby)
        aux_cols = ["VehicleClass"] + [c for c in df.columns if c.startswith("vdb_")]
        aux_cols = [c for c in aux_cols if c in df.columns and c not in df_grouped.columns]
        if aux_cols:
            key_cols = [c for c in ["Name", "Nation"] if c in df.columns and c in df_grouped.columns]
            aux = df.drop_duplicates(subset=key_cols)[key_cols + aux_cols]
            df_grouped = df_grouped.merge(aux, on=key_cols, how="left")

        if "VehicleClass" not in df_grouped.columns:
            df_grouped["VehicleClass"] = "Standard"
        else:
            df_grouped["VehicleClass"] = df_grouped["VehicleClass"].fillna("Standard")

        df_scored = score(df_grouped, self.settings)

        if nation != "All":
            df_scored = df_scored[df_scored["Nation"] == nation]

        return df_scored.round(2)

    def get_vehicle_row(self, name: str, nation: str = "") -> dict | None:
        """
        Ищет строку техники в display_df (текущий результат calculate_meta).
        Возвращает dict со всеми колонками, включая vdb_*.
        Возвращает None, если техника не найдена или display_df пуст.
        """
        df = self.display_df
        if df.empty or "Name" not in df.columns:
            return None
        mask = df["Name"] == name
        if nation and "Nation" in df.columns:
            mask &= df["Nation"] == nation
        sub = df[mask]
        return sub.iloc[0].to_dict() if not sub.empty else None
