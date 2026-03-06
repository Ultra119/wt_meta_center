"""
Колбэки сайдбара: предупреждения, поиск техники, карточка.
"""
import json
import pandas as pd
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
        State("sb-pick",        "value"),
        State("store-meta-df",  "data"),
        prevent_initial_call=True,
    )
    def show_card(n, pick_val, meta_df_json):
        if not pick_val:
            return ""

        parts  = pick_val.split("||", 1)
        name   = parts[0]
        nation = parts[1] if len(parts) > 1 else ""

        row = _find_row(core, name, nation, meta_df_json)
        if row is None:
            return dbc.Alert("Техника не найдена.", color="warning",
                             style={"fontSize": "0.8rem"})

        return html.Div([
            html.Hr(),
            html.Div(dangerouslySetInnerHTML={"__html": generate_card_html(row)}),
        ])


# ── Private helpers ───────────────────────────────────────────────────────────
def _find_row(core, name: str, nation: str, meta_df_json) -> dict | None:
    """Ищет строку в порядке: display_df → store → full_df."""
    def _match(df: pd.DataFrame):
        mask = df["Name"] == name
        if nation and "Nation" in df.columns:
            mask &= df["Nation"] == nation
        sub = df[mask]
        return sub.iloc[0].to_dict() if not sub.empty else None

    if not core.display_df.empty:
        row = _match(core.display_df)
        if row:
            return row

    if meta_df_json:
        try:
            df = pd.DataFrame(json.loads(meta_df_json))
            row = _match(df)
            if row:
                return row
        except Exception:
            pass

    return _match(core.full_df)
