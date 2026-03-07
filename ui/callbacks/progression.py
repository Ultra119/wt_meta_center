from dash import Input, Output, html
import dash_bootstrap_components as dbc
from dash import dcc

from ui.helpers import fmt_type, CLASS_PREFIX, _NATION_FLAG, _TYPE_ICON
from logic.logic_progression import (
    build_progression_data,
    ROMAN,
    VERDICT_MUST, VERDICT_PASS, VERDICT_SKIP, VERDICT_PREM,
)

# ── Цветовая схема вердиктов ──────────────────────────────────────────────────
_VC = {
    VERDICT_MUST: {"border": "#10b981", "bg": "rgba(16,185,129,0.12)", "icon": "🟢", "label": "Must Play"},
    VERDICT_PASS: {"border": "#fbbf24", "bg": "rgba(251,191,36,0.09)",  "icon": "🟡", "label": "Passable"},
    VERDICT_SKIP: {"border": "#f87171", "bg": "rgba(248,113,113,0.10)", "icon": "🔴", "label": "Hard Skip"},
    VERDICT_PREM: {"border": "#a78bfa", "bg": "rgba(167,139,250,0.11)", "icon": "👑", "label": "Premium Fix"},
}

# ── Типы техники по веткам ────────────────────────────────────────────────────
_BRANCH_TYPES: dict[str, list[str]] = {
    "Ground":   ["medium_tank", "light_tank", "heavy_tank", "tank_destroyer", "spaa"],
    "Aviation": ["fighter", "bomber", "assault", "attack_helicopter", "utility_helicopter"],
    "Fleet":    [
        "destroyer", "heavy_cruiser", "light_cruiser",
        "battleship", "battlecruiser",
        "boat", "heavy_boat", "frigate", "barge",
    ],
}

_PREM_CLASSES = {"Premium", "Pack", "Squadron", "Marketplace"}

def _verdict_badge(verdict: str) -> html.Span:
    c = _VC.get(verdict, _VC[VERDICT_PASS])
    return html.Span(
        c["icon"],
        title=c["label"],
        style={"fontSize": "9px", "flexShrink": "0"},
    )


def _vehicle_card(row: dict, card_id: str) -> html.Div:
    verdict    = row.get("Verdict", VERDICT_PASS)
    c          = _VC.get(verdict, _VC[VERDICT_PASS])
    name       = str(row.get("Name", ""))
    br         = float(row.get("BR", 0))
    wr         = float(row.get("WR", 0))
    kd         = float(row.get("KD", 0))
    loc_s      = float(row.get("Local_Score", 0))
    reason     = str(row.get("Skip_Reason", ""))
    vclass     = str(row.get("VehicleClass", "Standard"))
    prefix     = CLASS_PREFIX.get(vclass, "")
    prem_boost = float(row.get("Prem_Boost", 0) or 0)
    pain_fix   = bool(row.get("Prem_Pain_Fix", False))

    br_color = {
        "Premium": "#fbbf24", "Pack": "#60a5fa",
        "Squadron": "#34d399", "Marketplace": "#a78bfa",
    }.get(vclass, "#64748b")

    children = [
        html.Div([
            _verdict_badge(verdict),
            html.Span(
                f"{prefix}{name}",
                style={
                    "fontSize": "11px", "fontWeight": "600",
                    "color": "#e2e8f0", "flex": "1",
                    "overflow": "hidden", "textOverflow": "ellipsis",
                    "whiteSpace": "nowrap",
                },
            ),
            html.Span(
                f"{br:.1f}",
                style={
                    "fontSize": "10px", "color": br_color,
                    "flexShrink": "0", "fontFamily": "JetBrains Mono, monospace",
                },
            ),
        ], style={"display": "flex", "alignItems": "center", "gap": "4px", "marginBottom": "2px"}),

        html.Div(
            f"WR {wr:.1f}%  K/D {kd:.1f}  LS {loc_s:.0f}",
            style={
                "fontSize": "10px", "color": "#64748b",
                "fontFamily": "JetBrains Mono, monospace",
            },
        ),
    ]

    if verdict == VERDICT_SKIP and reason:
        children.append(html.Div(
            f"⚠ {reason}",
            style={
                "fontSize": "9px", "color": "#fca5a5",
                "marginTop": "3px", "fontStyle": "italic",
                "lineHeight": "1.3",
            },
        ))

    if verdict == VERDICT_PREM:
        prem_lines = []

        if pain_fix:
            prem_lines.append(html.Div(
                "👑 Поможет обойти боль ранга",
                style={"fontSize": "9px", "color": "#c4b5fd", "marginTop": "3px"},
            ))

        if prem_boost > 0:
            if prem_boost >= 1.05:
                boost_color = "#34d399"
                boost_label = f"⚡ Грайнд ×{prem_boost:.1f} быстрее бесплатного"
            elif prem_boost >= 0.95:
                boost_color = "#94a3b8"
                boost_label = f"≈ Паритет с бесплатным (×{prem_boost:.1f})"
            else:
                boost_color = "#f87171"
                boost_label = f"↓ Слабее бесплатного (×{prem_boost:.1f})"

            prem_lines.append(html.Div(
                boost_label,
                style={
                    "fontSize": "9px", "color": boost_color,
                    "marginTop": "2px", "fontWeight": "600",
                    "fontFamily": "JetBrains Mono, monospace",
                },
            ))

        if not prem_lines:
            prem_lines.append(html.Div(
                "★ Премиум",
                style={"fontSize": "9px", "color": "#c4b5fd", "marginTop": "3px"},
            ))

        children.extend(prem_lines)

    return html.Div(
        children,
        id=card_id,
        style={
            "border": f"1px solid {c['border']}",
            "backgroundColor": c["bg"],
            "borderRadius": "5px",
            "padding": "5px 7px",
            "marginBottom": "4px",
            "boxSizing": "border-box",
        },
    )


def _column_header(vtype: str) -> html.Div:
    icon = _TYPE_ICON.get(vtype, "🔧")
    return html.Div(
        [
            html.Div(icon, style={"fontSize": "16px"}),
            html.Div(
                fmt_type(vtype),
                style={
                    "fontSize": "10px", "color": "#94a3b8",
                    "marginTop": "2px", "lineHeight": "1.2",
                    "textAlign": "center",
                },
            ),
        ],
        style={
            "backgroundColor": "#1e293b",
            "borderRadius": "4px",
            "padding": "6px 4px",
            "textAlign": "center",
            "minHeight": "52px",
            "display": "flex",
            "flexDirection": "column",
            "alignItems": "center",
            "justifyContent": "center",
        },
    )


def _rank_label(era: int) -> html.Div:
    return html.Div(
        [
            html.Span(
                ROMAN.get(era, str(era)),
                style={"fontSize": "22px", "fontWeight": "800", "color": "#a7f3d0"},
            ),
        ],
        style={
            "backgroundColor": "#162032",
            "borderRadius": "4px",
            "padding": "8px 4px",
            "textAlign": "center",
            "display": "flex",
            "alignItems": "center",
            "justifyContent": "center",
            "minHeight": "52px",
        },
    )


def _empty_cell() -> html.Div:
    return html.Div(style={
        "backgroundColor": "rgba(15,23,42,0.4)",
        "borderRadius": "4px",
        "border": "1px dashed #1e293b",
        "minHeight": "52px",
    })


def _build_grid(prog_df: "pd.DataFrame", types_ordered: list) -> html.Div:
    import pandas as pd

    if prog_df.empty:
        return dbc.Alert("Нет данных для выбранной нации.", color="info")

    eras = sorted(e for e in prog_df["_era_int"].unique() if 1 <= e <= 8)
    if not eras:
        return dbc.Alert("Не удалось определить ранги техники.", color="warning")

    n_cols = len(types_ordered) + 1
    counter = [0]

    # ── Заголовки столбцов ────────────────────────────────────────────────
    cells = [
        html.Div(
            "РАНГ",
            style={
                "backgroundColor": "#1e293b", "borderRadius": "4px",
                "padding": "6px 4px", "textAlign": "center",
                "fontSize": "9px", "fontWeight": "700",
                "color": "#475569", "letterSpacing": "0.1em",
                "display": "flex", "alignItems": "center",
                "justifyContent": "center", "minHeight": "52px",
            },
        )
    ]
    for vtype in types_ordered:
        cells.append(_column_header(vtype))

    # ── Строки: Ранг × Тип ───────────────────────────────────────────────
    _has_shop = "vdb_shop_order" in prog_df.columns

    for era in eras:
        era_df = prog_df[prog_df["_era_int"] == era]
        cells.append(_rank_label(era))

        for vtype in types_ordered:
            cell_df = era_df[era_df["_branch"] == vtype]

            # Сортировка: по shop_order если есть, иначе по BR
            if _has_shop:
                sort_key = pd.to_numeric(
                    cell_df["vdb_shop_order"], errors="coerce"
                ).fillna(99999)
                # Для техники без позиции — по BR
                fallback = cell_df["BR"] * 10000
                effective = sort_key.where(sort_key < 99999, fallback)
                cell_df = cell_df.loc[effective.sort_values().index]
            else:
                cell_df = cell_df.sort_values("BR")

            if cell_df.empty:
                cells.append(_empty_cell())
                continue

            cards = []
            for _, row in cell_df.iterrows():
                cid = f"pgc-{counter[0]}"
                counter[0] += 1
                cards.append(_vehicle_card(row.to_dict(), cid))

            cells.append(html.Div(cards, style={"padding": "3px"}))

    return html.Div(
        cells,
        style={
            "display": "grid",
            "gridTemplateColumns": f"52px repeat({len(types_ordered)}, 1fr)",
            "gap": "4px",
            "alignItems": "start",
        },
    )


def _build_premium_panel(prem_df: "pd.DataFrame") -> html.Div:
    import pandas as pd

    if prem_df.empty:
        return html.Div()

    _has_shop = "vdb_shop_order" in prem_df.columns

    eras = sorted(e for e in prem_df["_era_int"].unique() if 1 <= e <= 8)

    counter = [9000]
    sections = [
        html.Div(
            "👑 ОСОБАЯ",
            style={
                "backgroundColor": "#1e293b",
                "borderRadius": "4px",
                "padding": "6px 4px",
                "textAlign": "center",
                "fontSize": "9px", "fontWeight": "700",
                "color": "#a78bfa",
                "letterSpacing": "0.1em",
                "minHeight": "52px",
                "display": "flex", "alignItems": "center",
                "justifyContent": "center",
            },
        )
    ]

    for era in eras:
        era_df = prem_df[prem_df["_era_int"] == era]

        # Сортировка по shop_order
        if _has_shop:
            sort_key = pd.to_numeric(
                era_df["vdb_shop_order"], errors="coerce"
            ).fillna(99999)
            fallback = era_df["BR"] * 10000
            effective = sort_key.where(sort_key < 99999, fallback)
            era_df = era_df.loc[effective.sort_values().index]
        else:
            era_df = era_df.sort_values("BR")

        cards = []
        for _, row in era_df.iterrows():
            cid = f"pgp-{counter[0]}"
            counter[0] += 1
            cards.append(_vehicle_card(row.to_dict(), cid))

        # Ранг-метка + карточки премиума
        sections.append(
            html.Div([
                _rank_label(era),
                html.Div(cards, style={"padding": "3px"}),
            ], style={"marginBottom": "4px"})
        )

    return html.Div(
        sections,
        style={
            "display": "flex",
            "flexDirection": "column",
            "gap": "4px",
            "minWidth": "160px",
            "maxWidth": "200px",
        },
    )


def _legend() -> html.Div:
    items = [
        (VERDICT_MUST, "Must Play — лидер ветки, сажать экспертов"),
        (VERDICT_PASS, "Passable — проходная, не задерживаться"),
        (VERDICT_SKIP, "Hard Skip — НЕ сажать экипаж, грайндить предыдущей"),
        (VERDICT_PREM, "Premium Fix — решение для болезненного ранга"),
    ]
    return html.Div([
        html.Span([
            html.Span(_VC[v]["icon"], style={"marginRight": "3px"}),
            html.Span(lbl, style={"color": "#64748b"}),
        ], style={"marginRight": "18px", "fontSize": "11px", "display": "inline-block"})
        for v, lbl in items
    ], style={"padding": "6px 0 10px 0"})

def register(app, core, all_nations, all_types, tf_data) -> None:

    @app.callback(
        Output("prog-grid",   "children"),
        Output("prog-info",   "children"),
        Input("prog-nation",  "value"),
        Input("prog-branch",  "value"),
        Input("sb-classes",   "value"),
        Input("sb-mode",      "value"),
    )
    def update_grid(nation, branch, classes, mode):
        if not nation or nation == "All":
            return (
                dbc.Alert("⬅️ Выберите нацию для построения дерева.", color="info"),
                "",
            )

        df = core.get_progression_data(nation, mode=mode or "All/Mixed")
        if df.empty:
            return dbc.Alert(f"Нет данных для нации «{nation}».", color="info"), ""

        if classes and "VehicleClass" in df.columns:
            df = df[df["VehicleClass"].isin(classes)]

        prog_df = build_progression_data(df, nation)
        if prog_df.empty:
            return dbc.Alert("Нет данных после расчёта.", color="warning"), ""

        branch_types = _BRANCH_TYPES.get(branch, [])
        present = [t for t in branch_types if t in prog_df["_branch"].values]
        if not present:
            return dbc.Alert("В этой ветке нет техники данной нации.", color="warning"), ""

        prog_df = prog_df[prog_df["_branch"].isin(present)]

        _is_prem = prog_df["VehicleClass"].isin(_PREM_CLASSES)
        std_df   = prog_df[~_is_prem]
        prem_df  = prog_df[_is_prem]

        n_must = int((prog_df["Verdict"] == VERDICT_MUST).sum())
        n_skip = int((prog_df["Verdict"] == VERDICT_SKIP).sum())
        n_prem = int((prog_df["Verdict"] == VERDICT_PREM).sum())
        total  = len(prog_df)

        flag = _NATION_FLAG.get(nation.lower(), "🏴")
        info = html.Span([
            html.B(f"{flag} {nation.title()}"),
            f"  ·  {branch}  ·  всего {total} машин  ·  ",
            html.Span(f"🟢 {n_must} Must  ", style={"color": "#10b981"}),
            html.Span(f"🔴 {n_skip} Skip  ", style={"color": "#f87171"}),
            html.Span(f"👑 {n_prem} Prem",   style={"color": "#a78bfa"}),
        ], style={"fontSize": "0.75rem", "color": "#94a3b8"})

        regular_grid  = _build_grid(std_df, present)
        premium_panel = _build_premium_panel(prem_df)

        layout = html.Div(
            [
                # Основное дерево
                html.Div(regular_grid, style={"flex": "1 1 0", "minWidth": "0"}),
                # Разделитель
                html.Div(style={
                    "width": "1px",
                    "backgroundColor": "#334155",
                    "margin": "0 8px",
                    "alignSelf": "stretch",
                }),
                # Панель особой техники
                html.Div(premium_panel, style={"flex": "0 0 auto"}),
            ],
            style={
                "display": "flex",
                "alignItems": "flex-start",
                "gap": "0",
            },
        )

        return layout, info
