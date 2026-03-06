"""
Колбэки вкладки 📊 БР Кронштейны.
"""
import json
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from dash import dash_table

from ui.helpers import pivot_table
from ui.callbacks.common import (
    init, get_types, apply_type_filter, filters_from_meta_store,
    BR_MIN, BR_MAX,
)


def register(app, core, all_types, tf_data) -> None:
    init(all_types, tf_data)

    # ── Инфо-подпись ──────────────────────────────────────────────────────
    @app.callback(
        Output("brackets-info", "children"),
        Input("store-meta-filters", "data"),
    )
    def info(meta_f_json):
        if not meta_f_json:
            return ""
        try:
            f = json.loads(meta_f_json)
            return html.Span([
                "📡 Активный диапазон: ",
                html.B(f"{f.get('min_br','?')} – {f.get('max_br','?')}"),
                f" · режим {f.get('mode', '?')}. ",
                "Изменить — на вкладке ", html.B("🏆 META Рейтинг"), ".",
            ], style={"fontSize": "0.75rem", "color": "#94a3b8"})
        except Exception:
            return ""

    # ── META pivot ────────────────────────────────────────────────────────
    @app.callback(
        Output("br-pivot-meta", "children"),
        Input("br-calc-meta", "n_clicks"),
        State("br-step-meta",  "value"),
        State("br-topn-meta",  "value"),
        State("br-all-meta",   "value"),
        State("sb-mode",        "value"),
        State("sb-battles",     "value"),
        State("sb-classes",     "value"),
        State("sb-ground",      "value"),
        State("sb-air",         "value"),
        State("sb-large-fleet", "value"),
        State("sb-small-fleet", "value"),
        State("store-meta-filters", "data"),
        prevent_initial_call=True,
    )
    def pivot_meta(_, step, topn, all_veh, mode, battles, classes, ground, air, lf, sf, meta_f_json):
        return _compute_pivot(
            core, "meta", step, topn, all_veh,
            mode, battles, classes, ground, air, lf, sf, meta_f_json,
        )

    # ── MM pivot ──────────────────────────────────────────────────────────
    @app.callback(
        Output("br-pivot-mm", "children"),
        Input("br-calc-mm", "n_clicks"),
        State("br-step-mm",    "value"),
        State("br-topn-mm",    "value"),
        State("br-all-mm",     "value"),
        State("sb-mode",        "value"),
        State("sb-battles",     "value"),
        State("sb-classes",     "value"),
        State("sb-ground",      "value"),
        State("sb-air",         "value"),
        State("sb-large-fleet", "value"),
        State("sb-small-fleet", "value"),
        State("store-meta-filters", "data"),
        prevent_initial_call=True,
    )
    def pivot_mm(_, step, topn, all_veh, mode, battles, classes, ground, air, lf, sf, meta_f_json):
        return _compute_pivot(
            core, "mm", step, topn, all_veh,
            mode, battles, classes, ground, air, lf, sf, meta_f_json,
        )

    # ── Nations table ─────────────────────────────────────────────────────
    @app.callback(
        Output("br-nations-table", "children"),
        Input("br-calc-nat", "n_clicks"),
        State("br-topn-nat",   "value"),
        State("br-all-nat",    "value"),
        State("sb-mode",        "value"),
        State("sb-battles",     "value"),
        State("sb-classes",     "value"),
        State("sb-ground",      "value"),
        State("sb-air",         "value"),
        State("sb-large-fleet", "value"),
        State("sb-small-fleet", "value"),
        State("store-meta-filters", "data"),
        prevent_initial_call=True,
    )
    def nations(_, topn, all_veh, mode, battles, classes, ground, air, lf, sf, meta_f_json):
        types_list = get_types(ground, air, lf, sf)
        filters    = filters_from_meta_store(meta_f_json, mode, battles, classes)
        df         = core.calculate_meta(filters)
        df         = apply_type_filter(df, types_list)
        if df.empty:
            return dbc.Alert("Нет данных.", color="info")

        top_n = None if all_veh else int(topn or 5)
        core.display_df = df
        core.settings["top_nations_vehicles"] = 9999 if top_n is None else top_n
        core._calculate_nation_dominance()
        stats = core.nation_stats
        if stats.empty:
            return dbc.Alert("Нет данных.", color="info")

        return dash_table.DataTable(
            data=stats.round(2).to_dict("records"),
            columns=[
                {"name": "Нация",       "id": "Nation"},
                {"name": "Машин в пуле","id": "Vehicles_Count", "type": "numeric"},
                {"name": "Лидер нации", "id": "Best_Vehicle"},
                {"name": "Power Score", "id": "Power_Score",    "type": "numeric"},
            ],
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
                "fontSize": "12px", "padding": "6px 12px",
            },
            style_data_conditional=[
                {"if": {"row_index": 0},
                 "backgroundColor": "rgba(16,185,129,0.1)",
                 "border": "1px solid #10b981", "fontWeight": "700"},
                {"if": {"column_id": "Power_Score"}, "color": "#34d399", "fontWeight": "700"},
            ],
            sort_action="native",
            sort_by=[{"column_id": "Power_Score", "direction": "desc"}],
        )


# ── Shared helper ─────────────────────────────────────────────────────────────
def _compute_pivot(core, kind, step, topn, all_veh,
                   mode, battles, classes, ground, air, lf, sf, meta_f_json):
    types_list = get_types(ground, air, lf, sf)
    filters    = filters_from_meta_store(meta_f_json, mode, battles, classes)
    df         = core.calculate_meta(filters)
    df         = apply_type_filter(df, types_list)

    if df.empty:
        return dbc.Alert("Нет данных.", color="info")

    top_n = None if all_veh else int(topn or 5)
    core.display_df = df

    if kind == "meta":
        result = core.get_bracket_stats(int(step or 1), top_n=top_n)
    else:
        result = core.get_mm_context(int(step or 1), top_n=top_n)

    return pivot_table(result)
