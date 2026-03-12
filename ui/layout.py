from dash import dcc, html
import dash_bootstrap_components as dbc

from analytics.constants import WT_BR_STEPS
from ui.type_filter import TypeFilterData

BR_MIN = float(min(WT_BR_STEPS))
BR_MAX = float(max(WT_BR_STEPS))

BR_MARKS = {
    v: {"label": str(int(v)), "style": {"color": "#e2e8f0", "fontSize": "12px", "fontWeight": "600"}}
    if v == int(v) else {"label": ""}
    for v in WT_BR_STEPS
}

_STEP_OPTS = [
    {"label": "Каждый WT BR (0.3)", "value": 1},
    {"label": "По 1 BR-пункту",     "value": 3},
    {"label": "Широкие (3 пункта)", "value": 9},
]


# ─────────────────────────────────────────────────────────────────────────────
def _sidebar(all_nations: list, tf_data: TypeFilterData) -> html.Div:
    class_opts = [
        {"label": "🔓 Стандартная",  "value": "Standard"},
        {"label": "★ Премиум",       "value": "Premium"},
        {"label": "📦 Пак",          "value": "Pack"},
        {"label": "✦ Эскадрилья",   "value": "Squadron"},
        {"label": "🏪 Маркетплейс",  "value": "Marketplace"},
        {"label": "🎁 Подарок",      "value": "Gift"},
        {"label": "🎪 Ивент",        "value": "Event"},
    ]
    return html.Div(id="sidebar", children=[
        html.H5("🎛️ НАСТРОЙКИ"),

        html.Div("Режим игры", className="section-label"),
        dcc.Dropdown(
            id="sb-mode",
            options=[{"label": m, "value": m} for m in ["Realistic", "Arcade", "Simulator"]],
            value="Realistic", clearable=False, searchable=False,
        ),
        html.Hr(),

        html.Div("🏷️ Классы техники", className="section-label"),
        dbc.Checklist(
            id="sb-ground",
            options=[{"label": "🚜 Наземка",       "value": "ground"}],
            value=["ground"], switch=True,
        ),
        dbc.Checklist(
            id="sb-air",
            options=[{"label": "✈️ Авиация",       "value": "air"}],
            value=[], switch=True,
        ),
        html.Div("— флот —", className="text-muted-sm", style={"margin": "4px 0"}),
        dbc.Checklist(
            id="sb-large-fleet",
            options=[{"label": "🚢 Большой флот", "value": "lf"}],
            value=[], switch=True,
        ),
        dbc.Checklist(
            id="sb-small-fleet",
            options=[{"label": "⛵ Малый флот",  "value": "sf"}],
            value=[], switch=True,
        ),
        html.Div(id="sb-type-warning"),
        html.Hr(),

        html.Div("Мин. боёв", className="section-label"),
        dbc.Input(id="sb-battles", type="number", value=50, step=10, min=0),
        html.Hr(),

        html.Div("💎 Тип техники", className="section-label"),
        dcc.Dropdown(
            id="sb-classes",
            options=class_opts,
            value=["Standard", "Premium", "Pack", "Squadron", "Marketplace", "Gift", "Event"],
            multi=True, clearable=False, searchable=False, placeholder="Все классы",
        ),
        html.Hr(),

        html.Div("🔍 Карточка техники", className="section-label"),
        dbc.Input(id="sb-search", type="text", placeholder="Tiger, T-34, F-16…", debounce=True),
        html.Div(id="sb-search-results", style={"marginTop": "6px"}),
        html.Div(id="sb-card-display",   style={"marginTop": "8px"}),
    ])


# ─────────────────────────────────────────────────────────────────────────────
def _tab_meta(all_nations: list) -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div("Нация", className="section-label"),
                dcc.Dropdown(
                    id="meta-nation",
                    options=[{"label": n, "value": n} for n in all_nations],
                    value="All", clearable=False, searchable=False,
                ),
            ], width=2),
            dbc.Col([
                html.Div("Диапазон БР", className="section-label"),
                dcc.RangeSlider(
                    id="meta-br", min=BR_MIN, max=BR_MAX,
                    marks=BR_MARKS, value=[BR_MIN, BR_MAX], step=None,
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ], width=10),
        ], className="panel mb-3"),
        html.Div(id="meta-info", className="caption-text"),
        dcc.Loading(
            id="loading-meta",
            type="dot",
            color="#10b981",
            children=html.Div(id="meta-table-container"),
        ),
    ], style={"padding": "4px"})


def _tab_redbook(all_nations: list) -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div("Нация", className="section-label"),
                dcc.Dropdown(
                    id="rb-nation",
                    options=[{"label": n, "value": n} for n in all_nations],
                    value="All", clearable=False, searchable=False,
                ),
            ], width=2),
            dbc.Col([
                html.Div("Диапазон БР", className="section-label"),
                dcc.RangeSlider(
                    id="rb-br", min=BR_MIN, max=BR_MAX,
                    marks=BR_MARKS, value=[BR_MIN, BR_MAX], step=None,
                    tooltip={"placement": "bottom", "always_visible": False},
                ),
            ], width=10),
        ], className="panel mb-3"),
        html.P("💀 Техника с наименьшим числом боёв — «вымирающие» машины.", className="caption-text"),
        dcc.Loading(
            id="loading-rb",
            type="dot",
            color="#10b981",
            children=html.Div(id="rb-table-container"),
        ),
    ], style={"padding": "4px"})


def _tab_brackets() -> html.Div:
    def _br_controls(sfx: str, with_step: bool = True) -> dbc.Row:
        cols = []
        if with_step:
            cols.append(dbc.Col([
                html.Div("Детализация", className="section-label"),
                dcc.Dropdown(
                    id=f"br-step-{sfx}", options=_STEP_OPTS,
                    value=1, clearable=False, searchable=False,
                ),
            ], width=3))
        cols.append(
            dbc.Col([
                html.Div("Топ-N машин нации", className="section-label"),
                html.Div([
                    dbc.Input(
                        id=f"br-topn-{sfx}",
                        type="number", value=5, min=1, max=50,
                        style={
                            "width": "68px", "flexShrink": "0",
                            "border": "none", "backgroundColor": "transparent",
                            "color": "#e2e8f0", "padding": "4px 8px",
                            "boxShadow": "none",
                        },
                    ),
                    html.Div(style={
                        "width": "1px", "alignSelf": "stretch",
                        "background": "#334155", "margin": "4px 0",
                    }),
                    html.Div([
                        dbc.Switch(
                            id=f"br-all-{sfx}",
                            value=False,
                            style={"margin": "0"},
                        ),
                        html.Span("Все", style={
                            "fontSize": "12px", "color": "#94a3b8",
                            "userSelect": "none",
                        }),
                    ], style={
                        "display": "flex", "alignItems": "center",
                        "gap": "6px", "padding": "0 10px",
                    }),
                ], style={
                    "display": "inline-flex",
                    "alignItems": "center",
                    "border": "1px solid #334155",
                    "borderRadius": "6px",
                    "backgroundColor": "#1e293b",
                    "overflow": "hidden",
                }),
            ], width="auto"),
        )
        return dbc.Row(cols, className="mb-3")

    options_panel = dbc.Row([
        dbc.Col([
            html.Div("⚙️ Опции расчёта", className="section-label"),
            html.Div([
                html.Div([
                    dbc.Switch(
                        id="br-excl-spaa",
                        value=True,
                        style={"margin": "0"},
                    ),
                    html.Span(
                        "Исключить ЗСУ из скора наций",
                        style={"fontSize": "12px", "color": "#e2e8f0",
                               "userSelect": "none"},
                    ),
                    html.Span(
                        " ⓘ",
                        id="br-spaa-tooltip-target",
                        style={"fontSize": "11px", "color": "#64748b",
                               "cursor": "help"},
                    ),
                    dbc.Tooltip(
                        "ЗСУ — поддерживающий класс. Её META_SCORE отражает "
                        "эффективность против воздуха, а не вклад в наземный бой. "
                        "Включение ЗСУ завышает скор наций с большим зенитным парком.",
                        target="br-spaa-tooltip-target",
                        placement="right",
                    ),
                ], style={
                    "display": "flex", "alignItems": "center",
                    "gap": "8px",
                    "padding": "6px 12px",
                    "border": "1px solid #334155",
                    "borderRadius": "6px",
                    "backgroundColor": "#1e293b",
                    "width": "fit-content",
                }),
            ]),
        ], width="auto"),
    ], className="panel mb-3", align="center")

    return html.Div([
        html.Div(id="brackets-info", className="caption-text"),

        options_panel,

        dbc.Tabs(id="brackets-sub", active_tab="br-meta", children=[

            dbc.Tab(label="📊 META Score", tab_id="br-meta", children=[
                _br_controls("meta"),
                html.P(
                    "Взвешенный META_SCORE топ-N машин нации в кронштейне. "
                    "Золото = лучшая нация. Нормализация — внутри типовой категории.",
                    className="caption-text",
                ),
                dbc.Button("🔄 Пересчитать", id="br-calc-meta",
                           color="success", size="sm", className="mb-2"),
                dcc.Loading(id="loading-br-meta", type="dot", color="#10b981",
                            children=html.Div(id="br-pivot-meta")),
            ]),

            dbc.Tab(label="🌍 Топ Наций", tab_id="br-nations", children=[
                _br_controls("nat", with_step=False),
                html.P(
                    "Power Score наций — взвешенное среднее META топ-N машин. "
                    "ЗСУ исключается если включён переключатель выше.",
                    className="caption-text",
                ),
                dbc.Button("🔄 Пересчитать", id="br-calc-nat",
                           color="success", size="sm", className="mb-2"),
                dcc.Loading(id="loading-br-nat", type="dot", color="#10b981",
                            children=html.Div(id="br-nations-table")),
            ]),
        ]),
    ], style={"padding": "4px"})


def _tab_farm(all_nations: list, tf_data: TypeFilterData) -> html.Div:
    return html.Div([
        html.H5("⚙️ Конструктор Сетапа",
                style={"fontFamily": "Rajdhani", "color": "#a7f3d0", "letterSpacing": "0.1em"}),
        dbc.Row([
            dbc.Col([
                html.Div("Целевой БР", className="section-label"),
                dcc.Dropdown(
                    id="farm-br",
                    options=[{"label": str(v), "value": v} for v in WT_BR_STEPS],
                    value=7.0, clearable=False, searchable=False,
                ),
            ], width=3),
            dbc.Col([
                html.Div("Нация", className="section-label"),
                dcc.Dropdown(
                    id="farm-nation",
                    options=[{"label": n, "value": n} for n in all_nations],
                    value="All", clearable=False, searchable=False,
                ),
            ], width=3),
            dbc.Col([
                html.Div("Тип техники", className="section-label"),
                dcc.Dropdown(
                    id="farm-type",
                    options=[{"label": o, "value": o} for o in tf_data.farm_type_opts],
                    value="All", clearable=False, searchable=False,
                ),
            ], width=3),
            dbc.Col([
                html.Div("Цель", className="section-label"),
                dcc.Dropdown(
                    id="farm-goal",
                    options=[{"label": "💰 SL (Фарм)", "value": "SL"},
                             {"label": "📚 RP (Грайнд)", "value": "RP"}],
                    value="SL", clearable=False, searchable=False,
                ),
            ], width=3),
        ], className="panel mb-3"),
        dbc.Button(
            "🚀 Подобрать сетап", id="farm-calc", color="success", size="lg",
            style={"width": "100%", "fontFamily": "Rajdhani", "fontWeight": "700",
                   "letterSpacing": "0.15em", "fontSize": "1rem"},
        ),
        dcc.Loading(
            id="loading-farm",
            type="dot",
            color="#10b981",
            children=html.Div(id="farm-result", style={"marginTop": "20px"}),
        ),
    ], style={"padding": "4px"})


def _tab_progression(all_nations: list) -> html.Div:
    nations_no_all = [n for n in all_nations if n != "All"]

    _sep = html.Div(style={
        "width": "1px", "alignSelf": "stretch",
        "background": "#1e293b", "margin": "0 16px", "flexShrink": "0",
    })

    return html.Div([
        html.Div([

            html.Div([
                html.Div("Нация", className="section-label"),
                dcc.Dropdown(
                    id="prog-nation",
                    options=[{"label": n, "value": n} for n in nations_no_all],
                    value=nations_no_all[0] if nations_no_all else None,
                    clearable=False, searchable=False,
                    style={"minWidth": "140px"},
                ),
            ], style={"flexShrink": "0", "width": "155px"}),

            _sep,

            html.Div([
                html.Div([
                    html.Div("Ветка", className="section-label"),
                    dbc.RadioItems(
                        id="prog-branch",
                        options=[
                            {"label": "🚜 Наземка",  "value": "Ground"},
                            {"label": "✈️ Авиация",  "value": "Aviation"},
                            {"label": "⚓ Флот",     "value": "Fleet"},
                        ],
                        value="Ground",
                        inline=True,
                        inputStyle={"marginRight": "4px", "marginLeft": "12px"},
                        labelStyle={"color": "#e2e8f0", "fontSize": "13px"},
                    ),
                ]),
                html.Div([
                    html.Div("Типы", className="section-label",
                             style={"marginTop": "7px"}),
                    dbc.Checklist(
                        id="prog-type-toggles",
                        options=[],
                        value=[],
                        inline=True,
                        inputStyle={"marginRight": "3px", "marginLeft": "10px"},
                        labelStyle={"color": "#94a3b8", "fontSize": "11px"},
                    ),
                ]),
            ], style={"flex": "1", "minWidth": "0"}),

            _sep,

            html.Div([
                html.Div([
                    html.Div("Слоты", className="section-label"),
                    dbc.RadioItems(
                        id="prog-slots",
                        options=[
                            {"label": "3", "value": 3},
                            {"label": "4", "value": 4},
                            {"label": "5", "value": 5},
                        ],
                        value=4,
                        inline=True,
                        inputStyle={"marginRight": "4px", "marginLeft": "10px"},
                        labelStyle={"color": "#e2e8f0", "fontSize": "13px"},
                    ),
                ]),
                html.Div(id="prog-info", style={"marginTop": "8px"}),
            ], style={"flexShrink": "0"}),

        ], className="panel mb-2", style={
            "display":    "flex",
            "alignItems": "flex-start",
            "padding":    "10px 14px",
        }),

        html.Div([
            html.Span([html.Span("🟢", style={"marginRight": "3px"}),
                       html.Span("Must Play",     style={"color": "#94a3b8"})],
                      style={"marginRight": "14px", "fontSize": "11px"}),
            html.Span([html.Span("🔵", style={"marginRight": "3px"}),
                       html.Span("Lineup Filler", style={"color": "#94a3b8"})],
                      style={"marginRight": "14px", "fontSize": "11px"}),
            html.Span([html.Span("🟡", style={"marginRight": "3px"}),
                       html.Span("Passable",      style={"color": "#94a3b8"})],
                      style={"marginRight": "14px", "fontSize": "11px"}),
            html.Span([html.Span("🔴", style={"marginRight": "3px"}),
                       html.Span("Hard Skip",     style={"color": "#94a3b8"})],
                      style={"marginRight": "14px", "fontSize": "11px"}),
            html.Span([html.Span("👑", style={"marginRight": "3px"}),
                       html.Span("Premium Fix",   style={"color": "#94a3b8"})],
                      style={"fontSize": "11px"}),
        ], style={"marginBottom": "10px", "padding": "0 2px"}),

        dcc.Loading(
            id="loading-prog",
            type="dot", color="#10b981",
            children=html.Div(id="prog-grid"),
        ),
    ], style={"padding": "4px"})

def build(all_nations: list, all_types: list, tf_data: TypeFilterData) -> html.Div:
    vehicle_modal = dbc.Modal(
        id="vehicle-modal",
        is_open=False,
        size="lg",
        centered=True,
        scrollable=True,
        children=[
            dbc.ModalHeader(
                dbc.Button(
                    "✕",
                    id="vehicle-modal-close",
                    color="link",
                    style={
                        "color": "#94a3b8", "fontSize": "1.2rem",
                        "padding": "0 4px", "lineHeight": "1",
                        "marginLeft": "auto",
                    },
                ),
                style={
                    "backgroundColor": "#0a1628",
                    "borderBottom": "1px solid #1e3a5f",
                    "padding": "8px 16px",
                },
                close_button=False,
            ),
            dbc.ModalBody(
                id="vehicle-modal-body",
                style={"backgroundColor": "#0f172a", "padding": "0"},
            ),
        ],
        style={"--bs-modal-bg": "#0f172a"},
        backdrop=True,
        keyboard=True,
    )

    return html.Div([
        dcc.Store(id="store-meta-df"),
        dcc.Store(id="store-meta-filters"),
        dcc.Store(id="store-selected-vehicle"),
        dcc.Store(id="store-history", data=[]),

        vehicle_modal,

        html.Div(id="topbar", children=[
            html.Span("🛡️", style={"fontSize": "1.5rem"}),
            html.H3("WT META CENTER"),
            html.Span("Dash Edition", className="topbar-badge"),
            html.Div(id="history-widget", style={"marginLeft": "auto"}),
        ]),

        dbc.Row([
            dbc.Col(_sidebar(all_nations, tf_data), width=3, xl=2, style={"padding": 0}),
            dbc.Col([
                dbc.Tabs(id="main-tabs", active_tab="tab-meta", children=[
                    dbc.Tab(_tab_meta(all_nations),          label="🏆 META Рейтинг",      tab_id="tab-meta"),
                    dbc.Tab(_tab_redbook(all_nations),       label="💀 Красная Книга",      tab_id="tab-redbook"),
                    dbc.Tab(_tab_brackets(),                 label="📊 БР Кронштейны",      tab_id="tab-brackets"),
                    dbc.Tab(_tab_farm(all_nations, tf_data), label="⚙️ Конструктор Сетапа", tab_id="tab-farm"),
                    dbc.Tab(_tab_progression(all_nations),   label="🗺 Прогрессия",          tab_id="tab-progression"),
                ], style={"marginTop": "6px"}),
            ], width=9, xl=10, style={"padding": "8px 16px"}),
        ], style={"margin": 0, "flexWrap": "nowrap"}),
    ], style={"backgroundColor": "#0f172a", "minHeight": "100vh"})
