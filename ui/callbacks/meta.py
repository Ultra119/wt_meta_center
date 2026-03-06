"""
Колбэки вкладки 🏆 META Рейтинг.
"""
import json
import pandas as pd
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from dash import dash_table

from ui.helpers import add_name_display, generate_card_html, fmt_type
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


# Колонки, которые сохраняем в Store для карточки
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
        # Колонка с иконкой + конкретным типом вместо категории
        df["Type_Display"] = df["Type"].apply(fmt_type)
        cols_avail = [c for c in _META_COLS if c in df.columns]

        mode_note = " · данные из Realistic Battles" if mode == "All/Mixed" else ""
        info = html.Span([
            html.B(f"{len(df)} машин"),
            f"  ·  БР {filters['min_br']} – {filters['max_br']}",
            f"  ·  {mode or 'All/Mixed'}{mode_note}  ·  ",
            html.I("Кликните строку для карточки", style={"color": "#64748b"}),
        ], style={"fontSize": "0.75rem", "color": "#94a3b8"})

        table = dash_table.DataTable(
            id="meta-table",
            data=df[cols_avail].round(2).to_dict("records"),
            columns=[
                {"name": _META_COL_NAMES.get(c, c), "id": c,
                 "type": "numeric" if c not in ("Name_Display", "Nation", "Type_Display") else "text"}
                for c in cols_avail
            ],
            style_table={"overflowX": "auto", "minWidth": "100%",
                         "height": "600px", "overflowY": "auto"},
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
            },
            style_cell_conditional=[
                {"if": {"column_id": "Name_Display"},   "fontWeight": "600", "minWidth": "140px", "maxWidth": "200px", "textAlign": "left", "paddingLeft": "10px"},
                {"if": {"column_id": "META_SCORE"},     "color": "#34d399", "fontWeight": "700"},
                {"if": {"column_id": "FARM_SCORE"},     "color": "#a78bfa", "fontWeight": "700"},
                {"if": {"column_id": "Type_Display"},   "color": "#94a3b8", "fontSize": "11px", "minWidth": "110px", "maxWidth": "140px"},
            ],
            style_data_conditional=[
                {"if": {"state": "selected"},
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
            row_selectable="single",
            selected_rows=[],
            page_action="none",
        )

        # Store: только нужные колонки + vdb_*
        vdb_cols = [c for c in df.columns if c.startswith("vdb_")]
        keep     = [c for c in _STORE_KEEP + vdb_cols if c in df.columns]
        store    = df[keep].to_json(orient="records")

        return table, info, store, json.dumps(filters)

    # ── Карточка по выбору строки ─────────────────────────────────────────
    @app.callback(
        Output("meta-card-container",    "children"),
        Output("store-selected-vehicle", "data"),
        Input("meta-table",    "selected_rows"),
        Input("meta-table",    "derived_virtual_data"),
        State("store-meta-df", "data"),
        prevent_initial_call=True,
    )
    def show_card(sel_rows, virtual_data, store_json):
        if not sel_rows or not store_json:
            return "", None
        try:
            idx      = sel_rows[0]
            row_dict = (virtual_data or [])[idx] if virtual_data else None
            if row_dict is None:
                return "", None

            # Обогащаем vdb_ полями из store
            store_df = pd.DataFrame(json.loads(store_json))
            match    = store_df[store_df["Name"] == row_dict.get("Name", "")]
            if not match.empty:
                merged = {**row_dict, **match.iloc[0].to_dict()}
            else:
                merged = row_dict

            card_html = generate_card_html(merged)
            return html.Div(dangerouslySetInnerHTML={"__html": card_html}), json.dumps(merged)
        except Exception as e:
            return dbc.Alert(f"Ошибка карточки: {e}", color="danger"), None
