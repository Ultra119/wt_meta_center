"""
Полный layout приложения.
Собирает топ-бар, сайдбар и четыре вкладки.
"""
from dash import dcc, html
import dash_bootstrap_components as dbc

from analytics.constants import WT_BR_STEPS
from ui.type_filter import TypeFilterData

BR_MIN = float(min(WT_BR_STEPS))
BR_MAX = float(max(WT_BR_STEPS))

# Отметки на слайдере БР: только целые числа подписаны
BR_MARKS = {
    v: {"label": str(int(v)), "style": {"color": "#94a3b8", "fontSize": "10px"}}
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
    ]
    return html.Div(id="sidebar", children=[
        html.H5("🎛️ НАСТРОЙКИ"),

        html.Div("Режим игры", className="section-label"),
        dcc.Dropdown(
            id="sb-mode",
            options=[{"label": m, "value": m} for m in ["All/Mixed", "Realistic", "Arcade", "Sim"]],
            value="All/Mixed", clearable=False,
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
            value=["Standard", "Premium", "Pack", "Squadron", "Marketplace"],
            multi=True, clearable=False, placeholder="Все классы",
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
                    value="All", clearable=False,
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
        html.Div(id="meta-table-container"),
        html.Div(id="meta-card-container", style={"marginTop": "20px"}),
    ], style={"padding": "4px"})


def _tab_redbook(all_nations: list) -> html.Div:
    return html.Div([
        dbc.Row([
            dbc.Col([
                html.Div("Нация", className="section-label"),
                dcc.Dropdown(
                    id="rb-nation",
                    options=[{"label": n, "value": n} for n in all_nations],
                    value="All", clearable=False,
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
        html.Div(id="rb-table-container"),
    ], style={"padding": "4px"})


def _tab_brackets() -> html.Div:
    def _br_controls(sfx: str, with_step: bool = True) -> dbc.Row:
        cols = []
        if with_step:
            cols.append(dbc.Col([
                html.Div("Детализация", className="section-label"),
                dcc.Dropdown(id=f"br-step-{sfx}", options=_STEP_OPTS, value=1, clearable=False),
            ], width=3))
        cols += [
            dbc.Col([
                html.Div("Топ-N машин нации", className="section-label"),
                dbc.Input(id=f"br-topn-{sfx}", type="number", value=5, min=1, max=50),
            ], width=2),
            dbc.Col([
                html.Div("", className="section-label"),
                dbc.Checkbox(id=f"br-all-{sfx}", label="Все машины", value=False),
            ], width=2, style={"marginTop": "4px"}),
        ]
        return dbc.Row(cols, className="mb-3")

    return html.Div([
        html.Div(id="brackets-info", className="caption-text"),
        dbc.Tabs(id="brackets-sub", active_tab="br-meta", children=[

            dbc.Tab(label="📊 META Score", tab_id="br-meta", children=[
                _br_controls("meta"),
                html.P("Средний META_SCORE топ-N машин нации в кронштейне. Золото = лучшая нация.", className="caption-text"),
                dbc.Button("🔄 Пересчитать", id="br-calc-meta", color="success", size="sm", className="mb-2"),
                html.Div(id="br-pivot-meta"),
            ]),

            dbc.Tab(label="⚔️ MM-Контекст", tab_id="br-mm", children=[
                _br_controls("mm"),
                html.P("Скор с учётом позиции в окне MM (±1.0 BR). Высокий META при низком MM = сила только в топе.", className="caption-text"),
                dbc.Button("🔄 Пересчитать", id="br-calc-mm", color="success", size="sm", className="mb-2"),
                html.Div(id="br-pivot-mm"),
            ]),

            dbc.Tab(label="🌍 Топ Наций", tab_id="br-nations", children=[
                _br_controls("nat", with_step=False),
                html.P("Power Score наций по среднему META топ-N машин.", className="caption-text"),
                dbc.Button("🔄 Пересчитать", id="br-calc-nat", color="success", size="sm", className="mb-2"),
                html.Div(id="br-nations-table"),
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
                    value=7.0, clearable=False,
                ),
            ], width=3),
            dbc.Col([
                html.Div("Нация", className="section-label"),
                dcc.Dropdown(
                    id="farm-nation",
                    options=[{"label": n, "value": n} for n in all_nations],
                    value="All", clearable=False,
                ),
            ], width=3),
            dbc.Col([
                html.Div("Тип техники", className="section-label"),
                dcc.Dropdown(
                    id="farm-type",
                    options=[{"label": o, "value": o} for o in tf_data.farm_type_opts],
                    value="All", clearable=False,
                ),
            ], width=3),
            dbc.Col([
                html.Div("Цель", className="section-label"),
                dcc.Dropdown(
                    id="farm-goal",
                    options=[{"label": "💰 SL (Фарм)", "value": "SL"},
                             {"label": "📚 RP (Грайнд)", "value": "RP"}],
                    value="SL", clearable=False,
                ),
            ], width=3),
        ], className="panel mb-3"),
        dbc.Button(
            "🚀 Подобрать сетап", id="farm-calc", color="success", size="lg",
            style={"width": "100%", "fontFamily": "Rajdhani", "fontWeight": "700",
                   "letterSpacing": "0.15em", "fontSize": "1rem"},
        ),
        html.Div(id="farm-result", style={"marginTop": "20px"}),
    ], style={"padding": "4px"})


# ─────────────────────────────────────────────────────────────────────────────
def build(all_nations: list, all_types: list, tf_data: TypeFilterData) -> html.Div:
    return html.Div([
        # Shared stores
        dcc.Store(id="store-meta-df"),
        dcc.Store(id="store-meta-filters"),
        dcc.Store(id="store-selected-vehicle"),

        # Top bar
        html.Div(id="topbar", children=[
            html.Span("🛡️", style={"fontSize": "1.5rem"}),
            html.H3("WT META CENTER"),
            html.Span("Dash Edition", className="topbar-badge"),
        ]),

        # Two-column layout: sidebar + content
        dbc.Row([
            dbc.Col(_sidebar(all_nations, tf_data), width=3, xl=2, style={"padding": 0}),
            dbc.Col([
                dbc.Tabs(id="main-tabs", active_tab="tab-meta", children=[
                    dbc.Tab(_tab_meta(all_nations),       label="🏆 META Рейтинг",      tab_id="tab-meta"),
                    dbc.Tab(_tab_redbook(all_nations),    label="💀 Красная Книга",      tab_id="tab-redbook"),
                    dbc.Tab(_tab_brackets(),              label="📊 БР Кронштейны",      tab_id="tab-brackets"),
                    dbc.Tab(_tab_farm(all_nations, tf_data), label="⚙️ Конструктор Сетапа", tab_id="tab-farm"),
                ], style={"marginTop": "6px"}),
            ], width=9, xl=10, style={"padding": "8px 16px"}),
        ], style={"margin": 0, "flexWrap": "nowrap"}),
    ], style={"backgroundColor": "#0f172a", "minHeight": "100vh"})
