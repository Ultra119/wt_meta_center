"""
Общие утилиты UI: форматирование, фабрики таблиц, карточка техники на Dash-компонентах.
"""
import math
import pandas as pd
from dash import dash_table, html
import dash_bootstrap_components as dbc

from analytics.constants import WT_BR_STEPS

BR_MIN = float(min(WT_BR_STEPS))
BR_MAX = float(max(WT_BR_STEPS))

# ── Prefixes ──────────────────────────────────────────────────────────────────
CLASS_PREFIX: dict[str, str] = {
    "Premium":     "★ ",
    "Pack":        "📦 ",
    "Squadron":    "✦ ",
    "Marketplace": "🏪 ",
    "Standard":    "",
}

# ── Formatting ────────────────────────────────────────────────────────────────
def fmt_num(n, suffix: str = "", signed: bool = False) -> str:
    try:
        n = int(n)
        s = f"{abs(n):,}".replace(",", "\u202f")
        sign = "-" if n < 0 else ("+" if signed and n > 0 else "")
        return f"{sign}{s}{suffix}"
    except Exception:
        return str(n)


def add_name_display(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    df = df.copy()
    if "VehicleClass" in df.columns:
        df["Name_Display"] = df.apply(
            lambda r: CLASS_PREFIX.get(r["VehicleClass"], "") + str(r["Name"]),
            axis=1,
        )
    else:
        df["Name_Display"] = df["Name"]
    return df


# ── Dark DataTable factory ────────────────────────────────────────────────────
_HEADER_STYLE = {
    "backgroundColor": "#1e293b",
    "color": "#a7f3d0",
    "fontWeight": "600",
    "fontSize": "11px",
    "letterSpacing": "0.1em",
    "textTransform": "uppercase",
    "border": "1px solid #1e3a5f",
}
_CELL_STYLE = {
    "backgroundColor": "#0f172a",
    "color": "#e2e8f0",
    "border": "1px solid #1e293b",
    "fontFamily": "'JetBrains Mono', monospace",
    "fontSize": "12px",
    "padding": "6px 10px",
    "overflow": "hidden",
    "textOverflow": "ellipsis",
    "whiteSpace": "nowrap",
}
_SEL_STYLE = [
    {"if": {"state": "active"},
     "backgroundColor": "rgba(16,185,129,0.12)",
     "border": "1px solid #10b981"},
]

COL_WIDTHS: dict[str, int] = {
    "Name_Display":   180,
    "Name":           180,
    "Nation":          80,
    "BR":              54,
    "Type":           120,
    "Type_Display":   120,
    "Роль":            90,
    "Техника":        180,
    "Сыграно игр":     80,
    "WR":              58,
    "KD":              54,
    "META_SCORE":      62,
    "FARM_SCORE":      62,
    "Net SL за игру":  90,
    "SL за игру":      80,
    "RP за игру":      70,
    "FARM_SCORE":      62,
}

def _col_width_styles(cols: list[str]) -> list[dict]:
    styles = []
    for c in cols:
        w = COL_WIDTHS.get(c)
        if w:
            styles.append({
                "if": {"column_id": c},
                "width":    f"{w}px",
                "minWidth": f"{w}px",
                "maxWidth": f"{w}px",
            })
    return styles


def dark_table(
    df: pd.DataFrame,
    columns: list[str],
    col_names: dict[str, str],
    *,
    sort_by: list | None = None,
    selectable: bool = False,
    extra_cond_styles: list | None = None,
    extra_cell_cond: list | None = None,
    table_id: str | None = None,
    max_height: str = "520px",
    virtualize: bool = True,
) -> dash_table.DataTable:
    cols_avail = [c for c in columns if c in df.columns]
    kwargs: dict = dict(
        data=df[cols_avail].round(2).to_dict("records"),
        columns=[
            {
                "name": col_names.get(c, c),
                "id": c,
                "type": "numeric" if c not in ("Name_Display", "Name", "Nation", "Type", "Type_Display", "Роль", "Техника") else "text",
            }
            for c in cols_avail
        ],
        virtualization=virtualize,
        style_table={
            "overflowX": "auto",
            "minWidth": "100%",
            "height": max_height,
            "overflowY": "auto",
            "tableLayout": "fixed",   # ← фиксирует ширины, без него браузер пересчитывает
        },
        style_header=_HEADER_STYLE,
        style_cell=_CELL_STYLE,
        style_cell_conditional=_col_width_styles(cols_avail) + (extra_cell_cond or []),
        style_data_conditional=_SEL_STYLE + (extra_cond_styles or []),
        fixed_rows={"headers": True},
        sort_action="native",
        sort_by=sort_by or [],
        page_action="none",
        style_as_list_view=False,
    )
    if selectable:
        kwargs["row_selectable"] = "single"
        kwargs["selected_rows"] = []
    if table_id:
        kwargs["id"] = table_id

    return dash_table.DataTable(**kwargs)


def pivot_table(pivot: pd.DataFrame) -> html.Div | dash_table.DataTable:
    """Pivot-таблица кронштейнов с подсветкой максимума по строке."""
    if pivot.empty:
        return html.Div("Нет данных", style={"color": "#475569", "padding": "12px"})

    pivot = pivot.reset_index()
    idx_col = pivot.columns[0]
    nation_cols = [c for c in pivot.columns if c != idx_col]
    records = pivot.to_dict("records")

    styles = [{"if": {"state": "active"}, "backgroundColor": "rgba(16,185,129,0.15)"}]
    for row_i, row in enumerate(records):
        vals = {c: float(row.get(c, 0) or 0) for c in nation_cols}
        row_max = max(vals.values()) if vals else 0
        for col, val in vals.items():
            if row_max <= 0:
                continue
            if val == row_max:
                s = {"backgroundColor": "#b45309", "color": "#fef3c7", "fontWeight": "800"}
            elif val >= row_max * 0.90:
                s = {"backgroundColor": "rgba(16,185,129,0.18)", "color": "#a7f3d0", "fontWeight": "600"}
            elif val >= row_max * 0.75:
                s = {"backgroundColor": "rgba(251,191,36,0.10)", "color": "#fcd34d"}
            elif val > 0:
                s = {"color": "#f87171"}
            else:
                s = {"color": "#475569"}
            styles.append({"if": {"row_index": row_i, "column_id": col}, **s})

    _pivot_cell = {k: v for k, v in _CELL_STYLE.items() if k != "backgroundColor"}
    return dash_table.DataTable(
        data=records,
        columns=[{"name": c, "id": c} for c in pivot.columns],
        virtualization=True,
        style_table={
            "overflowX": "auto", "minWidth": "100%",
            "height": "520px", "overflowY": "auto",
            "tableLayout": "fixed",
        },
        style_header=_HEADER_STYLE,
        style_cell={**_pivot_cell, "width": "80px", "minWidth": "80px", "maxWidth": "80px"},
        style_data={"backgroundColor": "#0f172a"},
        style_cell_conditional=[
            {"if": {"column_id": idx_col},
             "color": "#94a3b8", "fontSize": "11px",
             "width": "100px", "minWidth": "100px", "maxWidth": "100px"},
        ],
        style_data_conditional=styles,
        fixed_rows={"headers": True},
        sort_action="native",
        page_action="none",
    )


# ── Type display ──────────────────────────────────────────────────────────────
TYPE_DISPLAY: dict[str, str] = {
    "medium_tank":        "Средний танк",
    "light_tank":         "Лёгкий танк",
    "heavy_tank":         "Тяжёлый танк",
    "tank_destroyer":     "Противотанковая САУ",
    "spaa":               "ЗСУ",
    "fighter":            "Истребитель",
    "bomber":             "Бомбардировщик",
    "assault":            "Штурмовик",
    "attack_helicopter":  "Ударный вертолёт",
    "utility_helicopter": "Вертолёт",
    "destroyer":          "Эсминец",
    "battleship":         "Линкор",
    "light_cruiser":      "Лёгкий крейсер",
    "heavy_cruiser":      "Тяжёлый крейсер",
    "battlecruiser":      "Линейный крейсер",
    "boat":               "Катер",
    "heavy_boat":         "Тяжёлый катер",
    "frigate":            "Фрегат",
    "barge":              "Баржа",
    "Ground":             "Наземка",
    "Aviation":           "Авиация",
    "LargeFleet":         "Большой флот",
    "SmallFleet":         "Малый флот",
    "Uncategorized":      "—",
}


def fmt_type(raw_type: str) -> str:
    return TYPE_DISPLAY.get(str(raw_type), str(raw_type))


_NATION_FLAG: dict = {
    "usa": "🇺🇸", "germany": "🇩🇪", "ussr": "🇷🇺", "britain": "🇬🇧",
    "japan": "🇯🇵", "italy": "🇮🇹", "france": "🇫🇷", "sweden": "🇸🇪",
    "israel": "🇮🇱", "china": "🇨🇳", "finland": "🇫🇮",
    "netherlands": "🇳🇱", "hungary": "🇭🇺",
}
_TYPE_ICON: dict = {
    "medium_tank": "🛡️", "heavy_tank": "⚔️", "light_tank": "💨",
    "tank_destroyer": "🎯", "spaa": "🌀",
    "fighter": "✈️", "bomber": "💣", "assault": "🔥",
    "attack_helicopter": "🚁", "utility_helicopter": "🚁",
    "destroyer": "🚢", "battleship": "⚓", "light_cruiser": "🛳️",
    "heavy_cruiser": "🛳️", "battlecruiser": "⚓",
    "boat": "⛵", "heavy_boat": "🚤", "frigate": "🛥️",
}


def _g(row: dict, col, default=None):
    v = row.get(col, default)
    if v is None:
        return default
    if isinstance(v, float) and math.isnan(v):
        return default
    if isinstance(v, str) and not v.strip():
        return default
    return v


# ── Dash-компонент карточки техники ──────────────────────────────────────────

def _score_color(v: float) -> str:
    if v >= 70: return "#34d399"
    if v >= 45: return "#fbbf24"
    return "#f87171"


def _stat_row_dash(label: str, value: str, color: str = "#e2e8f0") -> html.Div:
    return html.Div([
        html.Span(label, style={
            "color": "#64748b", "fontSize": "11px",
            "minWidth": "140px", "display": "inline-block",
        }),
        html.Span(value, style={
            "color": color, "fontWeight": "600",
            "fontFamily": "'JetBrains Mono', monospace", "fontSize": "12px",
        }),
    ], style={"display": "flex", "alignItems": "center", "padding": "2px 0"})


def _score_circle(value: float, label: str, bg: str) -> html.Div:
    color = _score_color(value)
    return html.Div([
        html.Span(f"{value:.0f}", style={
            "fontFamily": "Rajdhani, sans-serif",
            "fontSize": "1.3rem", "fontWeight": "700",
            "color": color, "lineHeight": "1",
        }),
        html.Span(label, style={
            "fontSize": "0.5rem", "color": color,
            "letterSpacing": "0.1em", "textTransform": "uppercase",
        }),
    ], style={
        "display": "inline-flex", "flexDirection": "column",
        "alignItems": "center", "justifyContent": "center",
        "width": "66px", "height": "66px", "borderRadius": "50%",
        "border": f"3px solid {color}",
        "background": f"radial-gradient(circle, {bg} 0%, #0f172a 100%)",
        "boxShadow": f"0 0 14px {color}44", "flexShrink": "0",
    })


def _ammo_badge(atype: str) -> dbc.Badge:
    t = str(atype).lower()
    if "aphe" in t:
        label, color = "APHE", "danger"
    elif "heat" in t or "hesh" in t:
        label, color = "HEAT/HESH", "warning"
    elif "atgm" in t or "guided" in t:
        label, color = "ATGM", "primary"
    elif "apds" in t or "apfs" in t or "apcr" in t:
        label, color = t.upper()[:6], "secondary"
    elif "he_frag" in t or t == "he":
        label, color = "HE", "success"
    elif "smoke" in t:
        label, color = "Smoke", "light"
    else:
        label, color = t[:8].upper(), "dark"
    return dbc.Badge(label, color=color, className="me-1",
                     style={"fontSize": "10px", "fontFamily": "'JetBrains Mono', monospace"})


def _section_title(text: str) -> html.Div:
    return html.Div(text, style={
        "color": "#a7f3d0", "fontSize": "11px", "fontWeight": "700",
        "letterSpacing": "0.12em", "textTransform": "uppercase",
        "borderBottom": "1px solid #1e3a5f",
        "paddingBottom": "4px", "marginTop": "12px", "marginBottom": "6px",
    })


def generate_card(row: dict) -> html.Div:
    """Карточка техники — чистые Dash-компоненты, без HTML-строк."""
    name    = _g(row, "Name",    "—")
    nation  = str(_g(row, "Nation", "")).lower()
    br      = float(_g(row, "BR",  0))
    vtype   = str(_g(row, "Type", "—"))
    wr      = float(_g(row, "WR",  0))
    kd      = float(_g(row, "KD",  0))
    battles = int(_g(row, "Сыграно игр", 0))
    meta    = float(_g(row, "META_SCORE", 0))
    farm    = float(_g(row, "FARM_SCORE", 0))
    sl_pg   = int(_g(row, "SL за игру",  0))
    rp_pg   = int(_g(row, "RP за игру",  0))

    flag      = _NATION_FLAG.get(nation, "🏴")
    type_icon = _TYPE_ICON.get(vtype, "🔧")

    era       = int(_g(row, "vdb_era", 0))
    crew      = int(_g(row, "vdb_crew_total_count", 0))
    rep_rb    = int(_g(row, "vdb_repair_cost_realistic", 0))
    rep_fu    = int(_g(row, "vdb_repair_cost_full_upgraded_realistic", 0))
    sl_mul_rb = float(_g(row, "vdb_sl_mul_realistic", 0))
    sl_mul_ab = float(_g(row, "vdb_sl_mul_arcade", 0))
    req_exp   = int(_g(row, "vdb_req_exp", 0))
    val_sl    = int(_g(row, "vdb_value", 0))

    hull_f    = float(_g(row, "vdb_hull_front",   0))
    hull_s    = float(_g(row, "vdb_hull_side",    0))
    hull_r    = float(_g(row, "vdb_hull_rear",    0))
    turt_f    = float(_g(row, "vdb_turret_front", 0))
    turt_s    = float(_g(row, "vdb_turret_side",  0))
    turt_r    = float(_g(row, "vdb_turret_rear",  0))

    caliber   = float(_g(row, "vdb_main_caliber_mm", 0))
    gun_spd   = float(_g(row, "vdb_main_gun_speed",  0))
    ammo_types = _g(row, "vdb_ammo_types", []) or []
    has_atgm  = bool(_g(row, "vdb_has_atgm",    False))
    has_heat  = bool(_g(row, "vdb_has_heat",    False))
    has_aphe  = bool(_g(row, "vdb_has_aphe",    False))
    has_therm = bool(_g(row, "vdb_has_thermal", False))

    spd_rb    = int(_g(row, "vdb_engine_max_speed_rb", 0))
    hp_rb     = int(_g(row, "vdb_engine_hp_rb",        0))
    mass      = float(_g(row, "vdb_mass", 0))

    is_prem   = int(_g(row, "vdb_is_premium",       0))
    is_pack   = int(_g(row, "vdb_is_pack",          0))
    is_squad  = int(_g(row, "vdb_squadron_vehicle", 0))
    on_mkt    = int(_g(row, "vdb_on_marketplace",   0))
    identifier = str(_g(row, "vdb_identifier", ""))
    match_sc   = float(_g(row, "vdb_match_score", 0.0))
    rel_date   = str(_g(row, "vdb_release_date", ""))
    ver        = str(_g(row, "vdb_version", ""))

    era_roman = ["", "I", "II", "III", "IV", "V", "VI", "VII", "VIII"]
    era_str   = era_roman[era] if 0 < era < len(era_roman) else (str(era) if era else "—")

    wr_color  = "#34d399" if wr >= 55 else "#fbbf24" if wr >= 48 else "#f87171"
    net_sl    = sl_pg - rep_rb if sl_pg > 0 and rep_rb > 0 else 0

    # ── Badges ────────────────────────────────────────────────────────────
    badges = []
    if is_prem:  badges.append(dbc.Badge("★ Premium",    color="warning", className="me-1"))
    if is_pack:  badges.append(dbc.Badge("📦 Pack",      color="primary", className="me-1"))
    if is_squad: badges.append(dbc.Badge("✦ Squadron",   color="info",    className="me-1"))
    if on_mkt:   badges.append(dbc.Badge("🏪 Marketplace", color="secondary", className="me-1"))

    # ── Header ────────────────────────────────────────────────────────────
    header = html.Div([
        html.Div(f"{flag} {name}", style={
            "fontFamily": "Rajdhani, sans-serif",
            "fontSize": "1.4rem", "fontWeight": "700", "color": "#e2e8f0",
        }),
        html.Div(
            f"{type_icon} {fmt_type(vtype)}  ·  {nation.title()}  ·  БР {br:.1f}  ·  Ранг {era_str}",
            style={"color": "#94a3b8", "fontSize": "12px", "marginTop": "2px"},
        ),
        html.Div(badges, style={"marginTop": "6px"}),
    ], style={
        "background": "linear-gradient(90deg, #0a2540 0%, #0f172a 100%)",
        "borderBottom": "1px solid #1e3a5f",
        "padding": "12px 16px",
    })

    # ── Score circles + base stats ────────────────────────────────────────
    scores = html.Div([
        _score_circle(meta, "META", "#064e3b"),
        _score_circle(farm, "FARM", "#1c1917"),
        html.Div([
            _stat_row_dash("WinRate", f"{wr:.1f}%", wr_color),
            _stat_row_dash("K/D",     f"{kd:.2f}"),
            _stat_row_dash("Боёв",    fmt_num(battles)),
        ], style={"display": "flex", "flexDirection": "column", "gap": "2px"}),
    ], style={"display": "flex", "alignItems": "center", "gap": "20px",
              "marginBottom": "12px"})

    # ── Экономика ─────────────────────────────────────────────────────────
    econ_rows = []
    rep_color    = "#f87171" if rep_rb > 5000 else "#fbbf24" if rep_rb > 2000 else "#34d399"
    sl_mul_color = "#34d399" if sl_mul_rb >= 1.5 else "#fbbf24" if sl_mul_rb >= 1.0 else "#f87171"
    net_color    = "#34d399" if net_sl > 0 else "#f87171"
    if sl_pg:   econ_rows.append(_stat_row_dash("SL / игру",        fmt_num(sl_pg),              "#fbbf24"))
    if rp_pg:   econ_rows.append(_stat_row_dash("RP / игру",        fmt_num(rp_pg),              "#60a5fa"))
    if net_sl:  econ_rows.append(_stat_row_dash("Чистый SL / игру", fmt_num(net_sl, signed=True), net_color))
    if rep_rb:  econ_rows.append(_stat_row_dash("Ремонт RB",        fmt_num(rep_rb, " SL"),      rep_color))
    if rep_fu:  econ_rows.append(_stat_row_dash("Полный ремонт",    fmt_num(rep_fu, " SL")))
    if sl_mul_rb: econ_rows.append(_stat_row_dash("SL × RB",        f"×{sl_mul_rb:.2f}",         sl_mul_color))
    if sl_mul_ab: econ_rows.append(_stat_row_dash("SL × AB",        f"×{sl_mul_ab:.2f}"))
    if req_exp: econ_rows.append(_stat_row_dash("Нужно RP",         fmt_num(req_exp),             "#60a5fa"))
    if val_sl:  econ_rows.append(_stat_row_dash("Стоимость",        fmt_num(val_sl, " SL")))
    econ_section = [_section_title("💰 Экономика")] + econ_rows if econ_rows else []

    # ── Бронирование — простой текст ──────────────────────────────────────
    armor_rows = []
    armor_pairs = [
        ("Корпус: перед", hull_f), ("Корпус: борт", hull_s), ("Корпус: корма", hull_r),
        ("Башня: перед",  turt_f), ("Башня: борт",  turt_s), ("Башня: корма",  turt_r),
    ]
    for lbl, val in armor_pairs:
        if val:
            armor_rows.append(_stat_row_dash(lbl, f"{val:.0f} мм"))
    armor_section = [_section_title("🛡️ Бронирование")] + armor_rows if armor_rows else []

    # ── Вооружение ────────────────────────────────────────────────────────
    weapon_rows = []
    if caliber: weapon_rows.append(_stat_row_dash("Калибр",        f"{caliber:.0f} мм"))
    if gun_spd: weapon_rows.append(_stat_row_dash("Нач. скорость", f"{gun_spd:.0f} м/с"))
    perks = []
    if has_atgm:  perks.append("🚀 ATGM")
    if has_therm: perks.append("🌡️ Термооптика")
    if has_heat:  perks.append("🔥 HEAT/HESH")
    if has_aphe:  perks.append("💥 APHE")
    ammo_badges = [_ammo_badge(t) for t in (ammo_types or [])[:12]]
    weapon_extras = []
    if ammo_badges:
        weapon_extras.append(html.Div(ammo_badges, style={"marginTop": "6px"}))
    if perks:
        weapon_extras.append(html.Div(
            "  |  ".join(perks),
            style={"marginTop": "4px", "fontSize": "11px", "color": "#a7f3d0"},
        ))
    weapon_section = (
        [_section_title("🔫 Вооружение")] + weapon_rows + weapon_extras
        if (weapon_rows or ammo_badges or perks) else []
    )

    # ── Подвижность ───────────────────────────────────────────────────────
    mobility_section = []
    if spd_rb or hp_rb:
        pw = (hp_rb / (mass / 1000)) if mass > 0 and hp_rb > 0 else 0
        pw_color = "#34d399" if pw >= 20 else "#fbbf24" if pw >= 12 else "#f87171"
        mob_rows = []
        if spd_rb: mob_rows.append(_stat_row_dash("Скорость",     f"{spd_rb} км/ч"))
        if pw:     mob_rows.append(_stat_row_dash("Уд. мощность", f"{pw:.1f} л.с./т", pw_color))
        if crew:   mob_rows.append(_stat_row_dash("Экипаж",       f"{crew} чел."))
        mobility_section = [_section_title("⚡ Подвижность")] + mob_rows

    # ── Footer ────────────────────────────────────────────────────────────
    footer_parts = []
    if identifier: footer_parts.append(identifier)
    if rel_date:   footer_parts.append(f"Добавлено: {rel_date}")
    if ver:        footer_parts.append(ver)
    match_txt = f"✅ match {match_sc:.0%}" if match_sc > 0 else "⚠️ vdb нет данных"
    footer_parts.append(match_txt)

    footer = html.Div(
        "  ·  ".join(footer_parts),
        style={
            "borderTop": "1px solid #1e3a5f", "marginTop": "12px",
            "paddingTop": "8px", "color": "#475569", "fontSize": "10px",
        },
    )

    body_children = [scores] + econ_section + armor_section + weapon_section + mobility_section + [footer]

    return html.Div([
        header,
        html.Div(body_children, style={"padding": "12px 16px"}),
    ], style={
        "background": "#0f172a",
        "border": "1px solid #1e3a5f",
        "borderRadius": "8px",
        "overflow": "hidden",
    })


# Обратная совместимость для sidebar.py и других мест
generate_card_html = generate_card
