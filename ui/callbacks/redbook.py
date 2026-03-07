"""
Колбэки вкладки 💀 Красная Книга.
"""
from dash import Input, Output
import dash_bootstrap_components as dbc
from dash import dash_table

from ui.helpers import add_name_display, fmt_type
from ui.callbacks.common import init, get_types, apply_type_filter, build_filters

_RB_COLS = ["Name_Display", "Nation", "BR", "Type_Display", "Сыграно игр", "WR", "KD"]
_RB_NAMES = {
    "Name_Display": "Техника", "Nation": "Нация", "BR": "БР",
    "Type_Display": "Тип", "Сыграно игр": "Бои", "WR": "WR%", "KD": "K/D",
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
        df["Type_Display"] = df["Type"].apply(fmt_type)
        cols = [c for c in _RB_COLS if c in df.columns]

        def _rb_col(c):
            col = {"name": _RB_NAMES.get(c, c), "id": c}
            if c == "BR":
                col["type"] = "numeric"
                from dash.dash_table.Format import Format, Scheme
                col["format"] = Format(precision=1, scheme=Scheme.fixed)
            return col

        return dash_table.DataTable(
            data=df[cols].round(2).to_dict("records"),
            columns=[_rb_col(c) for c in cols],
            virtualization=True,
            style_table={
                "overflowX": "auto", "height": "600px", "overflowY": "auto",
                "tableLayout": "fixed",
            },
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
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "whiteSpace": "nowrap",
            },
            style_cell_conditional=[
                {"if": {"column_id": "Name_Display"},
                 "width": "180px", "minWidth": "180px", "maxWidth": "180px",
                 "fontWeight": "600", "textAlign": "left"},
                {"if": {"column_id": "Nation"},
                 "width": "80px", "minWidth": "80px", "maxWidth": "80px"},
                {"if": {"column_id": "BR"},
                 "width": "54px", "minWidth": "54px", "maxWidth": "54px"},
                {"if": {"column_id": "Type_Display"},
                 "width": "130px", "minWidth": "130px", "maxWidth": "130px",
                 "color": "#94a3b8", "fontSize": "11px"},
                {"if": {"column_id": "Сыграно игр"},
                 "width": "80px", "minWidth": "80px", "maxWidth": "80px"},
                {"if": {"column_id": "WR"},
                 "width": "58px", "minWidth": "58px", "maxWidth": "58px"},
                {"if": {"column_id": "KD"},
                 "width": "54px", "minWidth": "54px", "maxWidth": "54px"},
            ],
            style_data_conditional=[
                {"if": {"filter_query": "{Сыграно игр} < 100"}, "color": "#f87171"},
                {"if": {"state": "selected"}, "backgroundColor": "rgba(16,185,129,0.12)"},
            ],
            fixed_rows={"headers": True},
            sort_action="native",
            sort_by=[{"column_id": "Сыграно игр", "direction": "asc"}],
            page_action="none",
        )
