import os

import pandas as pd

from analytics.config    import load_settings
from analytics.loader    import load_json_files, clean_dataframe
from analytics.scorer    import score
from vehicle_db          import VehicleDB


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

    def load_data_recursive(self) -> bool:
        raw_records = load_json_files(os.path.join(self._project_dir, "dataset", "stats"))
        if not raw_records:
            return False

        raw_df       = pd.DataFrame(raw_records)
        self.full_df = clean_dataframe(raw_df, self.vehicle_db)
        return True

    def aggregate_all_periods(self, df: pd.DataFrame) -> pd.DataFrame:
        if df.empty:
            return df.copy()

        df = df.copy()

        group_cols = [c for c in [
            "Name", "Mode", "Nation", "Type", "BR", "VehicleClass",
        ] if c in df.columns]

        if not group_cols:
            return df

        sum_cols = [c for c in [
            "Сыграно игр", "Победы", "Возрождения", "Смерти",
            "Наземные убийства", "Воздушные убийства", "Морские убийства",
        ] if c in df.columns]

        wavg_cols = [c for c in ["SL за игру", "RP за игру"] if c in df.columns]

        vdb_cols = [c for c in df.columns if c.startswith("vdb_")]

        battles_col = "Сыграно игр"

        for col in wavg_cols:
            df[f"__w_{col}"] = df[col] * df[battles_col].clip(lower=0)

        agg: dict = {}
        for c in sum_cols:
            agg[c] = "sum"
        for c in wavg_cols:
            agg[f"__w_{c}"] = "sum"
        for c in vdb_cols:
            agg[c] = "first"

        grouped = df.groupby(group_cols, as_index=False, sort=False).agg(agg)

        battles = grouped[battles_col].clip(lower=1)
        for col in wavg_cols:
            grouped[col] = grouped[f"__w_{col}"] / battles
            grouped.drop(columns=[f"__w_{col}"], inplace=True)

        if "Победы" in grouped.columns:
            grouped["WR"] = (grouped["Победы"] / battles) * 100.0
        else:
            grouped["WR"] = 0.0

        kills = pd.Series(0.0, index=grouped.index)
        for kill_col in ("Наземные убийства", "Воздушные убийства", "Морские убийства"):
            if kill_col in grouped.columns:
                kills = kills + grouped[kill_col]
        if "Смерти" in grouped.columns:
            grouped["KD"] = kills / grouped["Смерти"].clip(lower=1)
        else:
            grouped["KD"] = 0.0

        grouped["Period"] = "All"

        return grouped.reset_index(drop=True)

    def calculate_meta(self, filters: dict) -> pd.DataFrame:
        """
          type        — тип техники ("All" = без фильтра)
          mode        — игровой режим ("Realistic" / "Arcade" / "Simulator")
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
        if filters["mode"]:
            df = df[df["Mode"] == filters["mode"]]
        if filters["search"]:
            df = df[df["Name"].str.contains(filters["search"], case=False, na=False)]

        vehicle_classes = filters.get("vehicle_classes", [])
        if vehicle_classes and "VehicleClass" in df.columns:
            df = df[df["VehicleClass"].isin(vehicle_classes)]

        if df.empty:
            return pd.DataFrame()

        df_grouped = df.copy()

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
        return self.display_df
