import json

from dash import Input, Output, State, ALL, ctx, html, no_update
import dash_bootstrap_components as dbc

from ui.helpers import generate_card, CLASS_PREFIX, fmt_type, _NATION_FLAG

_MAX_HISTORY = 15


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _vehicle_key(item: dict) -> str:
    """Уникальный ключ записи для дедупликации."""
    return f"{item.get('name', '')}||{item.get('nation', '')}"


def _item_from_selected(data: dict) -> dict | None:
    """Конвертирует данные из store-selected-vehicle в компактную запись истории."""
    name = data.get("Name") or data.get("name")
    if not name or str(name).strip() in ("", "nan", "None"):
        return None
    return {
        "name":   str(name),
        "nation": str(data.get("Nation", data.get("nation", ""))),
        "br":     float(data.get("BR",   data.get("br",    0)) or 0),
        "type":   str(data.get("Type",   data.get("type",  ""))),
        "vclass": str(data.get("VehicleClass", data.get("vclass", "Standard"))),
    }


def _history_item_ui(h: dict, index: int, is_first: bool) -> dbc.DropdownMenuItem:
    """Строит один элемент выпадающего списка."""
    flag   = _NATION_FLAG.get(h["nation"].lower(), "🏴")
    prefix = CLASS_PREFIX.get(h["vclass"], "")

    return dbc.DropdownMenuItem(
        html.Div([
            html.Span(
                f"{prefix}{h['name']}",
                style={"fontWeight": "600", "color": "#e2e8f0", "fontSize": "12px"},
            ),
            html.Span(
                f"  {flag} {h['nation'].title()}  ·  {h['br']:.1f}  ·  {fmt_type(h['type'])}",
                style={"color": "#64748b", "fontSize": "10px", "marginLeft": "8px"},
            ),
        ], style={"display": "flex", "alignItems": "center", "flexWrap": "wrap"}),
        id={"type": "history-item", "index": index},
        n_clicks=0,
        style={
            "backgroundColor": "#0a2540" if is_first else "#1e293b",
            "borderBottom": "1px solid #0f172a",
            "padding": "7px 14px",
            "cursor": "pointer",
        },
    )


# ── Регистрация колбэков ──────────────────────────────────────────────────────

def register(app, core) -> None:

    # ── 1. Обновление истории при выборе любой техники ────────────────────
    @app.callback(
        Output("store-history", "data"),
        Input("store-selected-vehicle", "data"),
        State("store-history", "data"),
        prevent_initial_call=True,
    )
    def update_history(selected_json, history_json):
        if not selected_json:
            return no_update
        try:
            data = (
                json.loads(selected_json)
                if isinstance(selected_json, str)
                else selected_json
            )
            item = _item_from_selected(data)
            if not item:
                return no_update

            history = list(history_json or [])
            key = _vehicle_key(item)
            history = [h for h in history if _vehicle_key(h) != key]
            history.insert(0, item)
            return history[:_MAX_HISTORY]
        except Exception:
            return no_update

    # ── 2. Рендер виджета в топбаре ───────────────────────────────────────
    @app.callback(
        Output("history-widget", "children"),
        Input("store-history", "data"),
    )
    def render_widget(history_json):
        history = history_json or []

        if not history:
            return html.Div(
                "🕐 Нет истории",
                style={
                    "color": "#334155",
                    "fontSize": "11px",
                    "padding": "6px 10px",
                    "border": "1px solid #1e293b",
                    "borderRadius": "6px",
                    "fontFamily": "'JetBrains Mono', monospace",
                    "whiteSpace": "nowrap",
                },
            )

        last   = history[0]
        flag   = _NATION_FLAG.get(last["nation"].lower(), "🏴")
        prefix = CLASS_PREFIX.get(last["vclass"], "")
        label  = f"{prefix}{last['name']}"

        items = [
            dbc.DropdownMenuItem(
                html.Div([
                    html.Span("🕐 ИСТОРИЯ ПРОСМОТРОВ",
                              style={"color": "#475569", "fontSize": "10px",
                                     "letterSpacing": "0.1em"}),
                    html.Span(f" ({len(history)})",
                              style={"color": "#334155", "fontSize": "10px"}),
                ]),
                header=True,
                style={"backgroundColor": "#0f172a", "padding": "6px 14px"},
            ),
        ]
        for i, h in enumerate(history):
            items.append(_history_item_ui(h, i, i == 0))

        toggle_label = html.Span([
            html.Span("🕐 ", style={"fontSize": "13px"}),
            html.Span(
                label,
                style={
                    "fontWeight": "600",
                    "maxWidth": "160px",
                    "overflow": "hidden",
                    "textOverflow": "ellipsis",
                    "whiteSpace": "nowrap",
                    "display": "inline-block",
                    "verticalAlign": "middle",
                    "fontSize": "12px",
                },
            ),
            html.Span(
                f"  {flag} {last['br']:.1f}",
                style={"color": "#94a3b8", "fontSize": "11px", "marginLeft": "6px"},
            ),
        ], style={"display": "flex", "alignItems": "center", "gap": "0px"})

        return dbc.DropdownMenu(
            label=toggle_label,
            children=items,
            color="dark",
            size="sm",
            menu_variant="dark",
            align_end=True,
            toggle_style={
                "backgroundColor": "#1e293b",
                "border": "1px solid #334155",
                "borderRadius": "6px",
                "color": "#e2e8f0",
                "padding": "5px 12px",
                "fontFamily": "'JetBrains Mono', monospace",
                "display": "flex",
                "alignItems": "center",
                "gap": "4px",
            },
            style={"fontFamily": "'JetBrains Mono', monospace"},
        )

    # ── 3. Клик по записи истории → открыть карточку в модальном окне ─────
    @app.callback(
        Output("vehicle-modal",          "is_open",  allow_duplicate=True),
        Output("vehicle-modal-body",     "children", allow_duplicate=True),
        Output("store-history",          "data",     allow_duplicate=True),
        Input({"type": "history-item", "index": ALL}, "n_clicks"),
        State("store-history", "data"),
        prevent_initial_call=True,
    )
    def open_from_history(n_clicks_list, history_json):
        if not any(n for n in (n_clicks_list or []) if n):
            return no_update, no_update, no_update

        triggered = ctx.triggered_id
        if not triggered or not isinstance(triggered, dict):
            return no_update, no_update, no_update

        idx     = triggered.get("index", 0)
        history = list(history_json or [])
        if idx >= len(history):
            return no_update, no_update, no_update

        item   = history[idx]
        name   = item["name"]
        nation = item["nation"]

        # Ищем технику: сначала в текущем display_df, потом в full_df
        row = core.get_vehicle_row(name, nation)
        if row is None and not core.full_df.empty:
            mask = core.full_df["Name"] == name
            if nation and "Nation" in core.full_df.columns:
                mask &= core.full_df["Nation"] == nation
            sub = core.full_df[mask]
            row = sub.iloc[0].to_dict() if not sub.empty else None

        if row is None:
            err = dbc.Alert(
                [html.B("Техника не найдена: "), f"«{name}»"],
                color="warning",
                style={"margin": "16px"},
            )
            return True, err, no_update

        # Перемещаем кликнутый элемент в начало истории
        key     = _vehicle_key(item)
        history = [h for h in history if _vehicle_key(h) != key]
        history.insert(0, item)

        return True, generate_card(row), history[:_MAX_HISTORY]
