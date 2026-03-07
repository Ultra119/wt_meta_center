"""
Колбэки вкладки 🏆 META Рейтинг.
"""
import json
import pandas as pd
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from dash import dash_table
from dash.dash_table.Format import Format, Scheme

from ui.helpers import add_name_display, generate_card, fmt_type
from ui.callbacks.common import init, get_types, apply_type_filter, build_filters

_META_COLS = [
    "Name_Display", "Nation", "BR", "Type_Display",
    "Сыграно игр", "WR", "KD", "META_SCORE",
    "FARM_SCORE", "Net SL за игру",
]
_META_COL_NAMES = {
    "Name_Display":   "Техника",
    "Nation":         "Нация",
    "BR":             "БР",
    "Type_Display":   "Тип",
    "Сыграно игр":    "Бои",
    "WR":             "WR%",
    "KD":             "K/D",
    "META_SCORE":     "META",
    "FARM_SCORE":     "FARM",
    "Net SL за игру": "Net SL/игру",
}

_STORE_KEEP = [
    "Name", "Nation", "BR", "Type", "WR", "KD",
    "META_SCORE", "FARM_SCORE", "Сыграно игр",
    "SL за игру", "RP за игру", "Net SL за игру", "VehicleClass",
]


def register(app, core, all_nations, all_types, tf_data) -> None:
    init(all_types, tf_data)

    # ── Основная таблица ──────────────────────────────────────────────────
    @app.callback(
        Output("meta-table-container", "children"),
        Output("meta-info",            "children"),
        Output("store-meta-df",        "data"),
        Output("store-meta-filters",   "data"),
        Input("sb-mode",        "value"),
        Input("sb-battles",     "value"),
        Input("sb-classes",     "value"),
        Input("sb-ground",      "value"),
        Input("sb-air",         "value"),
        Input("sb-large-fleet", "value"),
        Input("sb-small-fleet", "value"),
        Input("meta-nation",    "value"),
        Input("meta-br",        "value"),
    )
    def update_table(mode, battles, classes, ground, air, lf, sf, nation, br_range):
        types_list = get_types(ground, air, lf, sf)
        filters = build_filters(mode, battles, classes, nation, br_range)

        if not types_list:
            return (
                dbc.Alert("⚠️ Выберите хотя бы один класс техники.", color="warning"),
                "", None, json.dumps(filters),
            )

        df = core.calculate_meta(filters)
        df = apply_type_filter(df, types_list)

        if df.empty:
            return (
                dbc.Alert("Нет данных по заданным критериям.", color="info"),
                "", None, json.dumps(filters),
            )

        df = add_name_display(df)
        df["Type_Display"] = df["Type"].apply(fmt_type)
        cols_avail = [c for c in _META_COLS if c in df.columns]

        mode_note = " · данные из Realistic Battles" if mode == "All/Mixed" else ""
        info = html.Span([
            html.B(f"{len(df)} машин"),
            f"  ·  БР {filters['min_br']} – {filters['max_br']}",
            f"  ·  {mode or 'All/Mixed'}{mode_note}  ·  ",
            html.I("Кликните строку для карточки", style={"color": "#64748b"}),
        ], style={"fontSize": "0.75rem", "color": "#94a3b8"})

        # Поле "id" в каждой записи = row_id для active_cell
        table_records = df[cols_avail + ["Name"]].round(2).to_dict("records")
        for rec in table_records:
            rec["id"] = rec["Name"]

        def _col_def(c):
            if c in ("Name_Display", "Nation", "Type_Display"):
                return {"name": _META_COL_NAMES.get(c, c), "id": c, "type": "text"}
            col = {"name": _META_COL_NAMES.get(c, c), "id": c, "type": "numeric"}
            if c == "BR":
                from dash.dash_table.Format import Format, Scheme
                col["format"] = Format(precision=1, scheme=Scheme.fixed)
            return col

        table = dash_table.DataTable(
            id="meta-table",
            data=table_records,
            columns=[_col_def(c) for c in cols_avail],
            virtualization=True,
            style_table={
                "overflowX": "auto", "minWidth": "100%",
                "height": "600px", "overflowY": "auto",
                "tableLayout": "fixed",
            },
            style_header={
                "backgroundColor": "#1e293b", "color": "#a7f3d0",
                "fontWeight": "600", "fontSize": "11px",
                "letterSpacing": "0.1em", "textTransform": "uppercase",
                "border": "1px solid #1e3a5f",
            },
            style_cell={
                "backgroundColor": "#0f172a", "color": "#e2e8f0",
                "border": "1px solid #1e293b",
                "fontFamily": "'JetBrains Mono', monospace",
                "fontSize": "12px", "padding": "6px 10px",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
                "whiteSpace": "nowrap",
                "cursor": "pointer",
            },
            style_cell_conditional=[
                {"if": {"column_id": "Name_Display"},
                 "width": "180px", "minWidth": "180px", "maxWidth": "180px",
                 "fontWeight": "600", "textAlign": "left", "paddingLeft": "10px"},
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
                {"if": {"column_id": "META_SCORE"},
                 "width": "68px", "minWidth": "68px", "maxWidth": "68px",
                 "color": "#34d399", "fontWeight": "700"},
                {"if": {"column_id": "FARM_SCORE"},
                 "width": "68px", "minWidth": "68px", "maxWidth": "68px",
                 "color": "#a78bfa", "fontWeight": "700"},
                {"if": {"column_id": "Net SL за игру"},
                 "width": "96px", "minWidth": "96px", "maxWidth": "96px"},
            ],
            style_data_conditional=[
                {"if": {"state": "active"},
                 "backgroundColor": "rgba(16,185,129,0.12)", "border": "1px solid #10b981"},
                {"if": {"filter_query": "{META_SCORE} >= 70", "column_id": "META_SCORE"}, "color": "#34d399"},
                {"if": {"filter_query": "{META_SCORE} >= 45 && {META_SCORE} < 70", "column_id": "META_SCORE"}, "color": "#fbbf24"},
                {"if": {"filter_query": "{META_SCORE} < 45", "column_id": "META_SCORE"}, "color": "#f87171"},
                {"if": {"filter_query": "{WR} >= 55", "column_id": "WR"}, "color": "#34d399"},
                {"if": {"filter_query": "{WR} < 48",  "column_id": "WR"}, "color": "#f87171"},
            ],
            sort_action="native",
            sort_by=[{"column_id": "META_SCORE", "direction": "desc"}],
            fixed_rows={"headers": True},
            page_action="none",
        )

        vdb_cols = [c for c in df.columns if c.startswith("vdb_")]
        keep     = [c for c in _STORE_KEEP + vdb_cols if c in df.columns]
        store    = df[keep].to_json(orient="records")

        return table, info, store, json.dumps(filters)

    @app.callback(
        Output("vehicle-modal",      "is_open"),
        Output("vehicle-modal-body", "children"),
        Output("store-selected-vehicle", "data"),
        Input("meta-table",    "active_cell"),
        State("meta-table",    "derived_virtual_data"),
        State("store-meta-df", "data"),
        prevent_initial_call=True,
    )
    def open_modal(active_cell, virtual_data, store_json):
        if not active_cell or not store_json:
            return False, None, None
        try:
            row_idx  = active_cell["row"]
            vd       = virtual_data or []
            if row_idx >= len(vd):
                return False, None, None

            name = vd[row_idx].get("Name") or vd[row_idx].get("id")
            if not name:
                return False, None, None

            store_df = pd.DataFrame(json.loads(store_json))
            match    = store_df[store_df["Name"] == name]
            if match.empty:
                return False, None, None

            merged = {**vd[row_idx], **match.iloc[0].to_dict()}
            card   = generate_card(merged)
            return True, card, json.dumps(merged)
        except Exception as e:
            err = dbc.Alert(f"Ошибка карточки: {e}", color="danger")
            return True, err, None

    # ── Закрытие модального окна ─────────────────────────────────────────
    @app.callback(
        Output("vehicle-modal", "is_open", allow_duplicate=True),
        Input("vehicle-modal-close", "n_clicks"),
        prevent_initial_call=True,
    )
    def close_modal(_):
        return False
