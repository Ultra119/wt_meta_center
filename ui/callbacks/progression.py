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
    VERDICT_MUST: {"border": "#10b981", "bg": "rgba(16,185,129,0.08)",  "icon": "🟢", "label": "Must Play"},
    VERDICT_PASS: {"border": "#fbbf24", "bg": "rgba(251,191,36,0.06)",  "icon": "🟡", "label": "Passable"},
    VERDICT_SKIP: {"border": "#f87171", "bg": "rgba(248,113,113,0.08)", "icon": "🔴", "label": "Hard Skip"},
    VERDICT_PREM: {"border": "#a78bfa", "bg": "rgba(167,139,250,0.09)", "icon": "👑", "label": "Premium Fix"},
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

# Все не-Standard классы → колонка «ОСОБАЯ»
_STD_CLASS = "Standard"


def _verdict_badge(verdict: str) -> html.Span:
    c = _VC.get(verdict, _VC[VERDICT_PASS])
    return html.Span(
        c["icon"],
        title=c["label"],
        style={"fontSize": "9px", "flexShrink": "0"},
    )


def _type_dot(vtype: str) -> html.Span:
    icon = _TYPE_ICON.get(vtype, "🔧")
    return html.Span(
        icon,
        title=fmt_type(vtype),
        style={"fontSize": "9px", "flexShrink": "0", "opacity": "0.6"},
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
    vtype      = str(row.get("_branch", ""))
    prefix     = CLASS_PREFIX.get(vclass, "")
    prem_boost = float(row.get("Prem_Boost", 0) or 0)
    pain_fix   = bool(row.get("Prem_Pain_Fix", False))

    br_color = {
        "Premium":     "#fbbf24",
        "Pack":        "#60a5fa",
        "Squadron":    "#34d399",
        "Marketplace": "#a78bfa",
        "Gift":        "#f472b6",
        "Event":       "#fb923c",
    }.get(vclass, "#64748b")

    border_color = c["border"]

    # ── Название + BR ─────────────────────────────────────────────────────────
    header_row = html.Div([
        _type_dot(vtype),
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
    ], style={"display": "flex", "alignItems": "center", "gap": "4px", "marginBottom": "3px"})

    # ── Статистика: три отдельных блока ───────────────────────────────────────
    def _stat_chip(label: str, value: str) -> html.Span:
        return html.Span([
            html.Span(label, style={"color": "#475569", "fontSize": "9px"}),
            html.Span(value, style={
                "color": "#94a3b8", "fontSize": "10px",
                "fontFamily": "JetBrains Mono, monospace", "marginLeft": "2px",
            }),
        ])

    stats_row = html.Div([
        _stat_chip("WR", f"{wr:.1f}%"),
        _stat_chip("K/D", f"{kd:.1f}"),
        _stat_chip("META", f"{loc_s:.0f}"),
    ], style={"display": "flex", "gap": "8px"})

    cross_hint   = str(row.get("Cross_Hint",   "") or "")
    forward_hint = str(row.get("Forward_Hint", "") or "")

    children = [header_row, stats_row]

    # ── Взгляд вперёд: сильная машина впереди в ветке ────────────────────────
    if forward_hint:
        children.append(html.Div(
            forward_hint,
            style={
                "fontSize": "9px",
                "fontWeight": "normal",
                "color": "#86efac",        # зеленоватый — «впереди хорошее»
                "marginTop": "5px",
                "paddingTop": "5px",
                "borderTop": "1px solid rgba(134,239,172,0.20)",
                "lineHeight": "1.4",
            },
        ))

    # ── Кросс-хинт: лучшая техника из соседней ветки ─────────────────────────
    if cross_hint:
        children.append(html.Div(
            cross_hint,
            style={
                "fontSize": "9px",
                "fontWeight": "normal",
                "color": "#7dd3fc",        # голубой — отличается от красного SKIP
                "marginTop": "5px",
                "paddingTop": "5px",
                "borderTop": "1px solid rgba(125,211,252,0.20)",
                "lineHeight": "1.4",
            },
        ))

    # ── Причина скипа: вынесена в "подвал" без курсива ────────────────────────
    if verdict == VERDICT_SKIP and reason:
        children.append(html.Div(
            reason,
            style={
                "fontSize": "9px",
                "fontWeight": "normal",
                "color": "#fecaca",
                "marginTop": "5px",
                "paddingTop": "5px",
                "borderTop": f"1px solid rgba(248,113,113,0.25)",
                "lineHeight": "1.4",
            },
        ))

    # ── Премиум: буст и боль-ранг ─────────────────────────────────────────────
    if verdict == VERDICT_PREM:
        prem_lines = []

        if pain_fix:
            prem_lines.append(html.Div(
                "👑 Поможет обойти боль ранга",
                style={
                    "fontSize": "9px", "color": "#c4b5fd",
                    "marginTop": "5px", "paddingTop": "5px",
                    "borderTop": f"1px solid rgba(167,139,250,0.25)",
                },
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

            sep_style = {} if pain_fix else {
                "marginTop": "5px", "paddingTop": "5px",
                "borderTop": f"1px solid rgba(167,139,250,0.25)",
            }
            prem_lines.append(html.Div(
                boost_label,
                style={
                    "fontSize": "9px", "color": boost_color,
                    "fontWeight": "600",
                    "fontFamily": "JetBrains Mono, monospace",
                    **sep_style,
                },
            ))

        if not prem_lines:
            prem_lines.append(html.Div(
                "★ Премиум",
                style={
                    "fontSize": "9px", "color": "#c4b5fd",
                    "marginTop": "5px", "paddingTop": "5px",
                    "borderTop": f"1px solid rgba(167,139,250,0.25)",
                },
            ))

        children.extend(prem_lines)

    # ── Стиль карточки: полоса слева + лёгкий тинт ────────────────────────────
    return html.Div(
        children,
        id=card_id,
        style={
            "borderTop":    f"1px solid {border_color}22",
            "borderRight":  f"1px solid {border_color}22",
            "borderBottom": f"1px solid {border_color}22",
            "borderLeft":   f"4px solid {border_color}",
            "borderRadius": "0 5px 5px 0",
            "backgroundColor": c["bg"],
            "padding": "5px 7px",
            "marginBottom": "4px",
            "boxSizing": "border-box",
        },
    )


def _rank_label(era: int) -> html.Div:
    return html.Div(
        html.Span(
            ROMAN.get(era, str(era)),
            style={"fontSize": "22px", "fontWeight": "800", "color": "#a7f3d0"},
        ),
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


def _group_bracket(cards: list, group_name: str = "", first_vehicle_name: str = "") -> html.Div:
    label = first_vehicle_name.strip() if first_vehicle_name else group_name.replace("_", " ").strip()

    header = []
    if label:
        header = [html.Div(
            f"📁 {label}",
            style={
                "fontSize": "8px",
                "color": "#475569",
                "letterSpacing": "0.05em",
                "marginBottom": "2px",
                "paddingLeft": "4px",
                "textTransform": "uppercase",
                "whiteSpace": "nowrap",
                "overflow": "hidden",
                "textOverflow": "ellipsis",
            },
        )]

    # Карточки без нижнего отступа у последней — скоб "склеивает" их
    styled_cards = []
    for i, card in enumerate(cards):
        is_last = i == len(cards) - 1
        extra_style = {}
        if len(cards) > 1:
            if i == 0:
                extra_style = {
                    "borderBottomLeftRadius":  "0",
                    "borderBottomRightRadius": "0",
                    "marginBottom":            "1px",
                }
            elif is_last:
                extra_style = {
                    "borderTopLeftRadius":  "0",
                    "borderTopRightRadius": "0",
                    "marginBottom":         "0",
                }
            else:
                extra_style = {
                    "borderRadius":  "0",
                    "marginBottom":  "1px",
                }
        # Клонируем card, докидывая стили
        orig_style = card.style or {}
        new_style  = {**orig_style, **extra_style}
        styled_cards.append(html.Div(
            card.children,
            id=card.id,
            style=new_style,
        ))

    return html.Div(
        header + styled_cards,
        style={
            "borderLeft":        "2px solid #334155",
            "borderBottom":      "1px solid #1e293b",
            "borderTop":         "1px solid #1e293b",
            "borderRight":       "1px solid #1e293b",
            "borderRadius":      "0 4px 4px 0",
            "paddingTop":        "4px",
            "paddingBottom":     "4px",
            "paddingLeft":       "0",
            "paddingRight":      "0",
            "marginBottom":      "4px",
            "backgroundColor":   "rgba(30,41,59,0.35)",
        },
    )


def _render_cell_cards(cell_df: "pd.DataFrame", prefix: str, counter: list) -> list:
    """Рендерит карточки ячейки, группируя технику из одной папки (vdb_shop_group)."""
    import pandas as pd

    result = []

    has_groups = "vdb_shop_group" in cell_df.columns

    if has_groups:
        # Разбиваем на группы, сохраняя порядок строк
        seen_groups: dict = {}        # group_name → list of cards
        seen_groups_names: dict = {}  # group_name → display name of first vehicle
        ungrouped:   list = []

        for _, r in cell_df.iterrows():
            g = str(r.get("vdb_shop_group", "") or "").strip()
            cid = f"{prefix}-{counter[0]}"
            counter[0] += 1
            card = _vehicle_card(r.to_dict(), cid)

            if g:
                if g not in seen_groups:
                    seen_groups[g] = []
                    seen_groups_names[g] = str(r.get("Name", "") or "").strip()
                seen_groups[g].append(card)
            else:
                ungrouped.append((card, g))

        ordered: list = []
        seen_groups_added: set = set()

        # Перебираем заново, чтобы сохранить позицию группы
        for row_pos, (_, r) in enumerate(cell_df.iterrows()):
            g = str(r.get("vdb_shop_group", "") or "").strip()
            if g:
                if g not in seen_groups_added:
                    seen_groups_added.add(g)
                    grp_cards = seen_groups[g]
                    if len(grp_cards) > 1:
                        first_name = seen_groups_names.get(g, "")
                        ordered.append(_group_bracket(grp_cards, g, first_name))
                    else:
                        ordered.extend(grp_cards)
            else:
                # ungrouped: берём следующую карточку из ungrouped
                ordered.append(ungrouped.pop(0)[0])

        result = ordered
    else:
        for _, r in cell_df.iterrows():
            cid = f"{prefix}-{counter[0]}"
            counter[0] += 1
            result.append(_vehicle_card(r.to_dict(), cid))

    return result



def _build_unified_grid(
    std_df:  "pd.DataFrame",
    prem_df: "pd.DataFrame",
) -> html.Div:
    import pandas as pd

    if std_df.empty and prem_df.empty:
        return dbc.Alert("Нет данных для выбранной нации.", color="info")

    all_era_sets = []
    for _df in (std_df, prem_df):
        if not _df.empty:
            all_era_sets += [e for e in _df["_era_int"].unique() if 1 <= e <= 8]
    eras = sorted(set(all_era_sets))

    if not eras:
        return dbc.Alert("Не удалось определить ранги техники.", color="warning")

    # ── Колонки std_df (shop или fallback) ───────────────────────────────────
    has_shop = (
        not std_df.empty
        and "vdb_shop_column" in std_df.columns
        and (pd.to_numeric(std_df["vdb_shop_column"], errors="coerce").fillna(-1) >= 0).any()
    )

    _UNPLACED_COL = -1
    if has_shop:
        shop_col_num = pd.to_numeric(std_df["vdb_shop_column"], errors="coerce").fillna(-1)
        raw_cols     = sorted(shop_col_num[shop_col_num >= 0].unique().astype(int))
        col_remap    = {old: new for new, old in enumerate(raw_cols)}
        shop_col_num = shop_col_num.map(lambda x: col_remap.get(int(x), -1) if x >= 0 else -1)
        std_df       = std_df.copy()
        std_df["_shop_col_norm"] = shop_col_num
        valid_cols   = list(range(len(raw_cols)))
        has_unplaced = (shop_col_num < 0).any()
        types_in_df  = []
    elif not std_df.empty:
        types_in_df  = std_df["_branch"].dropna().unique().tolist()
        valid_cols   = list(range(len(types_in_df)))
        has_unplaced = False
    else:
        types_in_df  = []
        valid_cols   = []
        has_unplaced = False

    all_std_cols = valid_cols + ([_UNPLACED_COL] if has_unplaced else [])
    n_data_cols  = len(all_std_cols)
    counter      = [0]

    # ── Заголовок: РАНГ + пустые ячейки std + «ОСОБАЯ» ──────────────────────
    cells: list = [
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
    for col in all_std_cols:
        label = "?" if col == _UNPLACED_COL and has_shop else ""
        cells.append(html.Div(label, style={"backgroundColor": "transparent", "minHeight": "4px"}))

    cells.append(html.Div(
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
    ))

    # ── Строки: одна на ранг ──────────────────────────────────────────────────
    for era in eras:
        # Ранг-метка (крайняя левая)
        cells.append(_rank_label(era))

        # Ячейки std_df по колонкам
        if not std_df.empty:
            era_df = std_df[std_df["_era_int"] == era].copy()
        else:
            era_df = pd.DataFrame()

        for col in all_std_cols:
            if std_df.empty:
                cells.append(_empty_cell())
                continue

            if has_shop:
                col_src = "_shop_col_norm" if "_shop_col_norm" in era_df.columns else "vdb_shop_column"
                col_num = pd.to_numeric(era_df[col_src], errors="coerce").fillna(-1).astype(int)
                cell_df = era_df[col_num < 0].copy() if col == _UNPLACED_COL else era_df[col_num == col].copy()
                if not cell_df.empty and "vdb_shop_row" in cell_df.columns:
                    row_order = pd.to_numeric(cell_df["vdb_shop_row"], errors="coerce").fillna(99999)
                    cell_df   = cell_df.loc[row_order.sort_values().index]
                elif not cell_df.empty:
                    cell_df = cell_df.sort_values("BR")
            else:
                branch  = types_in_df[col] if col < len(types_in_df) else None
                cell_df = era_df[era_df["_branch"] == branch].sort_values("BR") if branch else pd.DataFrame()

            if cell_df.empty:
                cells.append(_empty_cell())
                continue

            cards = _render_cell_cards(cell_df, "pgc", counter)
            cells.append(html.Div(cards, style={"padding": "3px"}))

        # ── Ячейка «ОСОБАЯ» ──────────────────────────────────────────────────
        if not prem_df.empty:
            pera_df = prem_df[prem_df["_era_int"] == era].copy()
            if not pera_df.empty:
                if "vdb_shop_order" in pera_df.columns:
                    sort_key = pd.to_numeric(pera_df["vdb_shop_order"], errors="coerce").fillna(99999)
                    fallback = pera_df["BR"] * 10000
                    effective = sort_key.where(sort_key < 99999, fallback)
                    pera_df   = pera_df.loc[effective.sort_values().index]
                else:
                    pera_df = pera_df.sort_values("BR")

                cards = _render_cell_cards(pera_df, "pgp", counter)
                cells.append(html.Div(cards, style={"padding": "3px"}))
            else:
                cells.append(_empty_cell())
        else:
            cells.append(_empty_cell())

    # ── CSS grid: 52px ранг | std (1fr каждая) | 180px особая ───────────────
    grid_cols = f"52px repeat({n_data_cols}, 1fr) 180px"

    return html.Div(
        cells,
        style={
            "display": "grid",
            "gridTemplateColumns": grid_cols,
            "gap": "4px",
            "alignItems": "start",
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
        Input("sb-mode",      "value"),
    )
    def update_grid(nation, branch, mode):
        if not nation or nation == "All":
            return (
                dbc.Alert("⬅️ Выберите нацию для построения дерева.", color="info"),
                "",
            )

        df = core.get_progression_data(nation, mode=mode or "All/Mixed")
        if df.empty:
            return dbc.Alert(f"Нет данных для нации «{nation}».", color="info"), ""

        prog_df = build_progression_data(df, nation)
        if prog_df.empty:
            return dbc.Alert("Нет данных после расчёта.", color="warning"), ""

        # Фильтрация по ветке
        branch_types = _BRANCH_TYPES.get(branch, [])
        present = [t for t in branch_types if t in prog_df["_branch"].values]
        if not present:
            return dbc.Alert("В этой ветке нет техники данной нации.", color="warning"), ""

        prog_df = prog_df[prog_df["_branch"].isin(present)]

        _is_std  = prog_df["VehicleClass"] == _STD_CLASS
        std_df   = prog_df[_is_std]
        prem_df  = prog_df[~_is_std]

        n_must  = int((prog_df["Verdict"] == VERDICT_MUST).sum())
        n_skip  = int((prog_df["Verdict"] == VERDICT_SKIP).sum())
        n_prem  = int((prog_df["Verdict"] == VERDICT_PREM).sum())
        total   = len(prog_df)

        flag = _NATION_FLAG.get(nation.lower(), "🏴")
        info = html.Span([
            html.B(f"{flag} {nation.title()}"),
            f"  ·  {branch}  ·  всего {total} машин  ·  ",
            html.Span(f"🟢 {n_must} Must  ", style={"color": "#10b981"}),
            html.Span(f"🔴 {n_skip} Skip  ", style={"color": "#f87171"}),
            html.Span(f"👑 {n_prem} Prem",   style={"color": "#a78bfa"}),
        ], style={"fontSize": "0.75rem", "color": "#94a3b8"})

        # Единая сетка: std + premium + event в одном CSS grid
        grid = _build_unified_grid(std_df, prem_df)

        return grid, info
