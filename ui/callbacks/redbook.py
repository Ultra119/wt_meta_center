"""
Колбэки вкладки 💀 Красная Книга.
"""
from dash import Input, Output
import dash_bootstrap_components as dbc
from dash import dash_table

from ui.helpers import add_name_display
from ui.callbacks.common import init, get_types, apply_type_filter, build_filters

_RB_COLS = ["Name_Display", "Nation", "BR", "Type", "Сыграно игр", "WR", "KD"]
_RB_NAMES = {
    "Name_Display": "Техника", "Nation": "Нация", "BR": "БР",
    "Type": "Тип", "Сыграно игр": "Бои", "WR": "WR%", "KD": "K/D",
}


def register(app, core, all_types, tf_data) -> None:
    init(all_types, tf_data)

    @app.callback(
        Output("rb-table-container", "children"),
        Input("sb-mode",        "value"),
        Input("sb-battles",     "value"),
        Input("sb-classes",     "value"),
        Input("sb-ground",      "value"),
        Input("sb-air",         "value"),
        Input("sb-large-fleet", "value"),
        Input("sb-small-fleet", "value"),
        Input("rb-nation",      "value"),
        Input("rb-br",          "value"),
    )
    def update(mode, battles, classes, ground, air, lf, sf, nation, br_range):
        types_list = get_types(ground, air, lf, sf)
        filters    = build_filters(mode, battles, classes, nation, br_range)

        df = core.calculate_meta(filters)
        df = apply_type_filter(df, types_list)

        if df.empty:
            return dbc.Alert("Нет данных.", color="info")

        df = (df[df["Сыграно игр"] > 0]
              .sort_values("Сыграно игр", ascending=True)
              .head(100))
        df = add_name_display(df)
        cols = [c for c in _RB_COLS if c in df.columns]

        return dash_table.DataTable(
            data=df[cols].round(2).to_dict("records"),
            columns=[{"name": _RB_NAMES.get(c, c), "id": c} for c in cols],
            style_table={"overflowX": "auto", "maxHeight": "600px", "overflowY": "auto"},
            style_header={
                "backgroundColor": "#1e293b", "color": "#a7f3d0",
                "fontWeight": "600", "fontSize": "11px",
                "letterSpacing": "0.1em", "border": "1px solid #1e3a5f",
            },
            style_cell={
                "backgroundColor": "#0f172a", "color": "#e2e8f0",
                "border": "1px solid #1e293b",
                "fontFamily": "'JetBrains Mono', monospace",
                "fontSize": "12px", "padding": "6px 10px",
            },
            style_data_conditional=[
                {"if": {"filter_query": "{Сыграно игр} < 100"}, "color": "#f87171"},
                {"if": {"state": "selected"}, "backgroundColor": "rgba(16,185,129,0.12)"},
            ],
            sort_action="native",
            sort_by=[{"column_id": "Сыграно игр", "direction": "asc"}],
            filter_action="native",
            filter_options={"case": "insensitive"},
            fixed_rows={"headers": True},
            page_size=100,
        )
