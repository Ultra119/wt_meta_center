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

    # ── Блокировка Топ-N при «Все машины» ─────────────────────────────────
    for _sfx in ("meta", "nat"):
        @app.callback(
            Output(f"br-topn-{_sfx}", "disabled"),
            Input(f"br-all-{_sfx}",   "value"),
        )
        def _toggle_topn(all_checked):
            return bool(all_checked)

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
        State("br-step-meta",    "value"),
        State("br-topn-meta",    "value"),
        State("br-all-meta",     "value"),
        State("br-excl-spaa",    "value"),
        State("sb-mode",          "value"),
        State("sb-battles",       "value"),
        State("sb-classes",       "value"),
        State("sb-ground",        "value"),
        State("sb-air",           "value"),
        State("sb-large-fleet",   "value"),
        State("sb-small-fleet",   "value"),
        State("store-meta-filters", "data"),
        prevent_initial_call=True,
    )
    def pivot_meta(_, step, topn, all_veh, excl_spaa,
                   mode, battles, classes, ground, air, lf, sf, meta_f_json):
        return _compute_pivot(
            core, step, topn, all_veh, bool(excl_spaa),
            mode, battles, classes, ground, air, lf, sf, meta_f_json,
        )

    # ── Nations table ─────────────────────────────────────────────────────
    @app.callback(
        Output("br-nations-table", "children"),
        Input("br-calc-nat", "n_clicks"),
        State("br-topn-nat",     "value"),
        State("br-all-nat",      "value"),
        State("br-excl-spaa",    "value"),
        State("sb-mode",          "value"),
        State("sb-battles",       "value"),
        State("sb-classes",       "value"),
        State("sb-ground",        "value"),
        State("sb-air",           "value"),
        State("sb-large-fleet",   "value"),
        State("sb-small-fleet",   "value"),
        State("store-meta-filters", "data"),
        prevent_initial_call=True,
    )
    def nations(_, topn, all_veh, excl_spaa,
                mode, battles, classes, ground, air, lf, sf, meta_f_json):
        types_list = get_types(ground, air, lf, sf)
        filters    = filters_from_meta_store(meta_f_json, mode, battles, classes)
        df         = core.calculate_meta(filters)
        df         = apply_type_filter(df, types_list)
        if df.empty:
            return dbc.Alert("Нет данных.", color="info")

        if excl_spaa and "Type" in df.columns:
            df_for_nations = df[df["Type"] != "spaa"]
        else:
            df_for_nations = df

        if df_for_nations.empty:
            return dbc.Alert("Нет данных после фильтрации ЗСУ.", color="info")

        top_n = None if all_veh else int(topn or 5)
        core.display_df = df_for_nations
        core.settings["top_nations_vehicles"] = 9999 if top_n is None else top_n
        core._calculate_nation_dominance()
        stats = core.nation_stats
        if stats.empty:
            return dbc.Alert("Нет данных.", color="info")

        # Подпись: информируем пользователя об активном фильтре
        spaa_note = (
            html.Div(
                "⚡ ЗСУ исключены из расчёта Power Score",
                style={"fontSize": "0.72rem", "color": "#64748b",
                       "marginBottom": "6px"},
            )
            if excl_spaa else None
        )

        table = dash_table.DataTable(
            data=stats.round(2).to_dict("records"),
            columns=[
                {"name": "Нация",       "id": "Nation"},
                {"name": "Машин в пуле","id": "Vehicles_Count", "type": "numeric"},
                {"name": "Лидер нации", "id": "Best_Vehicle"},
                {"name": "Power Score", "id": "Power_Score",    "type": "numeric"},
            ],
            style_table={
                "overflowX": "auto", "maxHeight": "600px", "overflowY": "auto",
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
                "fontSize": "12px", "padding": "6px 12px",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "whiteSpace": "nowrap",
            },
            style_cell_conditional=[
                {"if": {"column_id": "Nation"},
                 "width": "100px", "minWidth": "100px", "maxWidth": "100px"},
                {"if": {"column_id": "Vehicles_Count"},
                 "width": "100px", "minWidth": "100px", "maxWidth": "100px"},
                {"if": {"column_id": "Best_Vehicle"},
                 "width": "220px", "minWidth": "220px", "maxWidth": "220px"},
                {"if": {"column_id": "Power_Score"},
                 "width": "100px", "minWidth": "100px", "maxWidth": "100px",
                 "color": "#34d399", "fontWeight": "700"},
            ],
            style_data_conditional=[
                {"if": {"row_index": 0},
                 "backgroundColor": "rgba(16,185,129,0.1)",
                 "border": "1px solid #10b981", "fontWeight": "700"},
            ],
            sort_action="native",
            sort_by=[{"column_id": "Power_Score", "direction": "desc"}],
        )

        return html.Div([spaa_note, table] if spaa_note else [table])

# ── Shared helper ─────────────────────────────────────────────────────────────
def _compute_pivot(core, step, topn, all_veh, exclude_spaa,
                   mode, battles, classes, ground, air, lf, sf, meta_f_json):
    types_list = get_types(ground, air, lf, sf)
    filters    = filters_from_meta_store(meta_f_json, mode, battles, classes)
    df         = core.calculate_meta(filters)
    df         = apply_type_filter(df, types_list)

    if df.empty:
        return dbc.Alert("Нет данных.", color="info")

    top_n = None if all_veh else int(topn or 5)
    core.display_df = df

    result = core.get_bracket_stats(
        int(step or 1),
        top_n=top_n,
        exclude_spaa=exclude_spaa,
    )
    return pivot_table(result)
