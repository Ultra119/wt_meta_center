"""
Колбэки вкладки ⚙️ Конструктор Сетапа.
"""
from dash import Input, Output, State, html
import dash_bootstrap_components as dbc
from dash import dash_table

from analytics.constants import WT_BR_STEPS
from ui.helpers import CLASS_PREFIX
from ui.callbacks.common import init, get_types, apply_type_filter, build_filters

BR_MIN = float(min(WT_BR_STEPS))
BR_MAX = float(max(WT_BR_STEPS))


def register(app, core, all_types, tf_data) -> None:
    init(all_types, tf_data)

    @app.callback(
        Output("farm-result", "children"),
        Input("farm-calc", "n_clicks"),
        State("farm-br",     "value"),
        State("farm-nation", "value"),
        State("farm-type",   "value"),
        State("farm-goal",   "value"),
        State("sb-mode",        "value"),
        State("sb-battles",     "value"),
        State("sb-classes",     "value"),
        State("sb-ground",      "value"),
        State("sb-air",         "value"),
        State("sb-large-fleet", "value"),
        State("sb-small-fleet", "value"),
        prevent_initial_call=True,
    )
    def compute(n_clicks, target_br, nation, ftype, goal,
                mode, battles, classes, ground, air, lf, sf):

        types_list = get_types(ground, air, lf, sf)
        target_br  = float(target_br or 7.0)

        filters = build_filters(
            mode, battles, classes,
            br_range=[max(BR_MIN, target_br - 2.5), min(BR_MAX, target_br + 1.0)],
        )

        df = core.calculate_meta(filters)

        # Применяем фильтр по типу из конструктора
        farm_types = tf_data.ui_type_cats.get(ftype) if ftype != "All" else None
        if farm_types:
            df = df[df["Type"].isin(farm_types)]
        else:
            df = apply_type_filter(df, types_list)

        core.display_df = df
        res = core.get_farm_set(target_br, nation or "All", "All")

        if res["anchor"].empty:
            return dbc.Alert("❌ Не найдена якорная техника на этом БР.", color="danger")

        anchor      = res["anchor"].iloc[0]
        anchor_name = CLASS_PREFIX.get(anchor.get("VehicleClass", "Standard"), "") + str(anchor["Name"])
        anchor_farm = float(anchor.get("FARM_SCORE", 0))

        _sl_col = "Net SL за игру" if "Net SL за игру" in res["main_set"].columns else "SL за игру"
        _sl_lbl = "Net SL/игру" if _sl_col == "Net SL за игру" else "SL/игру"

        def _farm_table(df_in, show_role: bool) -> html.Div:
            if df_in.empty:
                return html.P("Нет данных.", className="text-muted-sm")
            df_in = df_in.copy()
            df_in["Техника"] = df_in.apply(
                lambda r: CLASS_PREFIX.get(r.get("VehicleClass", "Standard"), "") + str(r["Name"]),
                axis=1,
            )
            cols = (["Роль"] if show_role else []) + [
                "Техника", "Nation", "BR", "Сыграно игр", "WR", "KD", "FARM_SCORE",
            ] + ([_sl_col] if _sl_col in df_in.columns else [])
            cols = [c for c in cols if c in df_in.columns]

            cond_styles = [
                {"if": {"state": "selected"},
                 "backgroundColor": "rgba(16,185,129,0.12)", "border": "1px solid #10b981"},
                {"if": {"column_id": "FARM_SCORE"}, "color": "#a78bfa", "fontWeight": "700"},
                {"if": {"column_id": _sl_col},      "color": "#34d399"},
            ]
            if show_role:
                cond_styles += [
                    {"if": {"filter_query": '{Роль} = "⚓ Якорь"'},
                     "backgroundColor": "rgba(147,197,253,0.08)", "fontWeight": "700"},
                    {"if": {"filter_query": '{Роль} = "💰 Топ-фармер"'}, "color": "#fbbf24"},
                ]

            _farm_col_names = {"Nation": "Нация", "BR": "БР", "Сыграно игр": "Бои",
                               "WR": "WR%", "KD": "K/D", "FARM_SCORE": "Farm",
                               "Техника": "Техника", "Роль": "Роль",
                               _sl_col: _sl_lbl}

            def _farm_col(c):
                from dash.dash_table.Format import Format, Scheme
                col = {"name": _farm_col_names.get(c, c), "id": c}
                if c == "BR":
                    col["type"] = "numeric"
                    col["format"] = Format(precision=1, scheme=Scheme.fixed)
                return col

            return dash_table.DataTable(
                data=df_in[cols].round(2).to_dict("records"),
                columns=[_farm_col(c) for c in cols],
                style_table={"overflowX": "auto"},
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
                style_data_conditional=cond_styles,
                sort_action="native",
            )

        return html.Div([
            dbc.Alert([
                html.B("⚓ ЯКОРЬ: "), f"{anchor_name} ",
                html.Span(f"({anchor['BR']:.1f})", style={"color": "#94a3b8"}),
                " · Farm Score: ",
                html.B(f"{anchor_farm:.1f}", style={"color": "#a78bfa"}),
            ], color="success", style={"fontSize": "0.9rem"}),

            html.H6("🛠️ Основной состав",
                    style={"color": "#a7f3d0", "fontFamily": "Rajdhani", "letterSpacing": "0.08em"}),
            _farm_table(res["main_set"], show_role=True),

            html.Div(style={"height": "16px"}),
            html.H6("💎 Жемчужины (Low BR / High Efficiency)",
                    style={"color": "#a78bfa", "fontFamily": "Rajdhani", "letterSpacing": "0.08em"}),
            _farm_table(res["gems"], show_role=False) if not res["gems"].empty
            else html.P("Нет жемчужин в диапазоне -2.0 BR с Farm Score выше якоря.",
                        className="text-muted-sm"),
        ])
