"""
Колбэки сайдбара: предупреждения, поиск техники, карточка.
"""
import json
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from dash import dcc

from ui.helpers import generate_card_html


def register(app, core) -> None:

    # ── Предупреждение при конфликте типов ───────────────────────────────
    @app.callback(
        Output("sb-type-warning", "children"),
        Input("sb-ground",      "value"),
        Input("sb-air",         "value"),
        Input("sb-large-fleet", "value"),
        Input("sb-small-fleet", "value"),
    )
    def type_warning(ground, air, lf, sf):
        has_ground_air = bool(ground or air)
        has_fleet      = bool(lf or sf)
        none_selected  = not any([ground, air, lf, sf])

        if none_selected:
            return dbc.Alert("⚠️ Не выбран ни один класс техники",
                             color="warning", className="mt-1 p-1",
                             style={"fontSize": "0.72rem"})
        if has_ground_air and has_fleet:
            return dbc.Alert("⚠️ Смешение: флот + наземка/авиация",
                             color="warning", className="mt-1 p-1",
                             style={"fontSize": "0.72rem"})
        return ""

    # ── Результаты поиска ─────────────────────────────────────────────────
    @app.callback(
        Output("sb-search-results", "children"),
        Input("sb-search", "value"),
    )
    def search_results(query):
        if not query or len(query) < 2 or core.full_df.empty:
            return ""

        hits = core.full_df[
            core.full_df["Name"].str.contains(query, case=False, na=False)
        ]
        if hits.empty:
            return html.P("Ничего не найдено.", className="text-muted-sm mt-1")

        if "Nation" in hits.columns:
            hits = hits.drop_duplicates(subset=["Name", "Nation"]).head(20)
            opts = [
                {"label": f"{r['Name']} ({r['Nation']})",
                 "value": f"{r['Name']}||{r['Nation']}"}
                for _, r in hits.iterrows()
            ]
        else:
            hits = hits.drop_duplicates(subset=["Name"]).head(20)
            opts = [
                {"label": r["Name"], "value": f"{r['Name']}||"}
                for _, r in hits.iterrows()
            ]

        return html.Div([
            dcc.Dropdown(
                id="sb-pick", options=opts,
                placeholder="Выбери технику…", clearable=True,
                style={"fontSize": "0.75rem"},
            ),
            dbc.Button(
                "📋 Показать карточку", id="sb-show-card",
                size="sm", color="outline-success",
                style={"width": "100%", "marginTop": "6px", "fontSize": "0.72rem"},
            ),
        ])

    # ── Отображение карточки из сайдбара ──────────────────────────────────
    @app.callback(
        Output("sb-card-display", "children"),
        Input("sb-show-card", "n_clicks"),
        State("sb-pick", "value"),
        prevent_initial_call=True,
    )
    def show_card(n, pick_val):
        if not pick_val:
            return ""

        parts  = pick_val.split("||", 1)
        name   = parts[0]
        nation = parts[1] if len(parts) > 1 else ""

        # Приоритет: текущий display_df (отфильтрованный), затем full_df.
        row = core.get_vehicle_row(name, nation)
        if row is None and not core.full_df.empty:
            # Техника есть в базе, но не попала в текущий фильтр — берём из full_df.
            mask = core.full_df["Name"] == name
            if nation and "Nation" in core.full_df.columns:
                mask &= core.full_df["Nation"] == nation
            sub = core.full_df[mask]
            row = sub.iloc[0].to_dict() if not sub.empty else None

        if row is None:
            return dbc.Alert("Техника не найдена.", color="warning",
                             style={"fontSize": "0.8rem"})

        return html.Div([
            html.Hr(),
            generate_vehicle_card(row),
        ])
