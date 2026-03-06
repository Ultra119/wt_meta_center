"""
Общие утилиты UI: форматирование, фабрики таблиц, генерация HTML карточки.
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
    "Premium":    "★ ",
    "Pack":       "📦 ",
    "Squadron":   "✦ ",
    "Marketplace": "🏪 ",
    "Standard":   "",
}

# ── Formatting ────────────────────────────────────────────────────────────────
def fmt_num(n: int, suffix: str = "", signed: bool = False) -> str:
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
}
_SEL_STYLE = [
    {"if": {"state": "selected"},
     "backgroundColor": "rgba(16,185,129,0.12)",
     "border": "1px solid #10b981"},
]


def dark_table(
    df: pd.DataFrame,
    columns: list[str],
    col_names: dict[str, str],
    *,
    sort_by: list | None = None,
    selectable: bool = False,
    extra_cond_styles: list | None = None,
    table_id: str | None = None,
    page_size: int = 100,
    max_height: str = "520px",
) -> dash_table.DataTable:
    cols_avail = [c for c in columns if c in df.columns]
    kwargs: dict = dict(
        data=df[cols_avail].round(2).to_dict("records"),
        columns=[
            {
                "name": col_names.get(c, c),
                "id": c,
                "type": "numeric" if c not in ("Name_Display", "Name", "Nation", "Type", "Роль") else "text",
            }
            for c in cols_avail
        ],
        style_table={"overflowX": "auto", "minWidth": "100%", "maxHeight": max_height, "overflowY": "auto"},
        style_header=_HEADER_STYLE,
        style_cell=_CELL_STYLE,
        style_data_conditional=_SEL_STYLE + (extra_cond_styles or []),
        fixed_rows={"headers": True},
        sort_action="native",
        sort_by=sort_by or [],
        filter_action="native",
        filter_options={"case": "insensitive"},
        page_size=page_size,
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

    styles = [{"if": {"state": "selected"}, "backgroundColor": "rgba(16,185,129,0.1)"}]
    for row_i, row in enumerate(records):
        vals = {c: float(row.get(c, 0) or 0) for c in nation_cols}
        row_max = max(vals.values()) if vals else 0
        for col, val in vals.items():
            if row_max <= 0:
                continue
            if val == row_max:
                s = {"backgroundColor": "#854d0e", "color": "#fef08a", "fontWeight": "bold"}
            elif val >= row_max * 0.90:
                s = {"color": "#a7f3d0"}
            elif val >= row_max * 0.75:
                s = {"color": "#fcd34d"}
            elif val > 0:
                s = {"color": "#f87171"}
            else:
                s = {"color": "#475569"}
            styles.append({"if": {"row_index": row_i, "column_id": col}, **s})

    return dash_table.DataTable(
        data=records,
        columns=[{"name": c, "id": c} for c in pivot.columns],
        style_table={"overflowX": "auto", "minWidth": "100%", "maxHeight": "520px", "overflowY": "auto"},
        style_header=_HEADER_STYLE,
        style_cell={**_CELL_STYLE, "minWidth": "60px"},
        style_cell_conditional=[
            {"if": {"column_id": idx_col}, "color": "#94a3b8", "fontSize": "11px", "minWidth": "80px"}
        ],
        style_data_conditional=styles,
        fixed_rows={"headers": True},
        sort_action="native",
        page_size=200,
    )


# ── Vehicle Card HTML ─────────────────────────────────────────────────────────
# ── Type display ─────────────────────────────────────────────────────────────
# Ключи: snake_case типы из vehicle_type + категории-фолбэки (имя папки)
TYPE_DISPLAY: dict[str, str] = {
    # Наземка
    "medium_tank":        "Средний танк",
    "light_tank":         "Лёгкий танк",
    "heavy_tank":         "Тяжёлый танк",
    "tank_destroyer":     "Противотанковая САУ",
    "spaa":               "ЗСУ",
    # Авиация
    "fighter":            "Истребитель",
    "bomber":             "Бомбардировщик",
    "assault":            "Штурмовик",
    "attack_helicopter":  "Ударный вертолёт",
    "utility_helicopter": "Вертолёт",
    # Большой флот
    "destroyer":          "Эсминец",
    "battleship":         "Линкор",
    "light_cruiser":      "Лёгкий крейсер",
    "heavy_cruiser":      "Тяжёлый крейсер",
    "battlecruiser":      "Линейный крейсер",
    # Малый флот
    "boat":               "Катер",
    "heavy_boat":         "Тяжёлый катер",
    "frigate":            "Фрегат",
    "barge":              "Баржа",
    # Фолбэки (имя папки, когда vehicle_type пустой)
    "Ground":             "Наземка",
    "Aviation":           "Авиация",
    "LargeFleet":         "Большой флот",
    "SmallFleet":         "Малый флот",
    "Uncategorized":      "—",
}


def fmt_type(raw_type: str) -> str:
    """Возвращает читаемое русское название типа техники."""
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


def _armor_bar(label: str, value: float) -> str:
    pct = min(100.0, (value / 500.0) * 100.0) if value > 0 else 0.0
    if value >= 300:   color = "#ef4444"
    elif value >= 150: color = "#f97316"
    elif value >= 60:  color = "#fbbf24"
    elif value > 0:    color = "#34d399"
    else:              color = "#1e293b"
    num = "—" if value == 0 else f"{value:.0f} мм"
    return (
        f'<div class="vc-armor-bar">'
        f'<span class="vc-armor-label">{label}</span>'
        f'<div class="vc-armor-track"><div class="vc-armor-fill" style="width:{pct:.0f}%;background:{color}"></div></div>'
        f'<span class="vc-armor-num">{num}</span>'
        f'</div>'
    )


def _ammo_chip(atype: str) -> str:
    t = str(atype).lower()
    if "aphe" in t:                           cls, lbl = "chip-aphe",  "APHE"
    elif "heat" in t or "hesh" in t:          cls, lbl = "chip-heat",  "HEAT/HESH"
    elif "atgm" in t or "guided" in t:        cls, lbl = "chip-atgm",  "ATGM"
    elif "apds" in t or "apfs" in t or "apcr" in t: cls, lbl = "chip-apds", t.upper()[:6]
    elif "he_frag" in t or t == "he":         cls, lbl = "chip-he",    "HE"
    elif "smoke" in t:                        cls, lbl = "chip-smoke", "Smoke"
    else:                                     cls, lbl = "chip-other", t[:8].upper()
    return f'<span class="vc-ammo-chip {cls}">{lbl}</span>'


def _stat_row(label: str, value: str, cls: str = "vc-value") -> str:
    return (
        f'<div class="vc-row">'
        f'<span class="vc-label">{label}</span>'
        f'<span class="{cls}">{value}</span>'
        f'</div>'
    )


def _score_col(v: float) -> str:
    if v >= 70: return "#34d399"
    if v >= 45: return "#fbbf24"
    return "#f87171"


def generate_card_html(row: dict) -> str:
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

    meta_col = _score_col(meta)
    farm_col = _score_col(farm)
    wr_cls   = "vc-value-green" if wr >= 55 else "vc-value-yellow" if wr >= 48 else "vc-value-red"

    badges = ""
    if is_prem:  badges += '<span class="vc-badge vc-badge-prem">★ Premium</span>'
    if is_pack:  badges += '<span class="vc-badge vc-badge-pack">📦 Pack</span>'
    if is_squad: badges += '<span class="vc-badge vc-badge-squad">✦ Squadron</span>'
    if on_mkt:   badges += '<span class="vc-badge vc-badge-mkt">🏪 Marketplace</span>'

    rep_cls    = "vc-value-red" if rep_rb > 5000 else "vc-value-yellow" if rep_rb > 2000 else "vc-value-green"
    sl_mul_cls = "vc-value-green" if sl_mul_rb >= 1.5 else "vc-value-yellow" if sl_mul_rb >= 1.0 else "vc-value-red"
    net_sl     = sl_pg - rep_rb if sl_pg > 0 and rep_rb > 0 else 0
    net_cls    = "vc-value-green" if net_sl > 0 else "vc-value-red"

    econ = ""
    if sl_pg > 0:     econ += _stat_row("SL / игру",        fmt_num(sl_pg),              "vc-value-yellow")
    if rp_pg > 0:     econ += _stat_row("RP / игру",        fmt_num(rp_pg),              "vc-value-blue")
    if net_sl != 0:   econ += _stat_row("Чистый SL / игру", fmt_num(net_sl, signed=True), net_cls)
    if rep_rb > 0:    econ += _stat_row("Ремонт RB",        fmt_num(rep_rb, " SL"),      rep_cls)
    if rep_fu > 0:    econ += _stat_row("Полный ремонт",    fmt_num(rep_fu, " SL"),      "vc-value")
    if sl_mul_rb > 0: econ += _stat_row("SL-множитель RB",  f"×{sl_mul_rb:.2f}",         sl_mul_cls)
    if sl_mul_ab > 0: econ += _stat_row("SL-множитель AB",  f"×{sl_mul_ab:.2f}",         "vc-value")
    if req_exp > 0:   econ += _stat_row("Нужно RP",         fmt_num(req_exp),            "vc-value-blue")
    if val_sl > 0:    econ += _stat_row("Стоимость",        fmt_num(val_sl, " SL"),      "vc-value")
    econ_section = f'<div class="vc-section-title">💰 Экономика</div>{econ}' if econ else ""

    armor_html = ""
    if any([hull_f, hull_s, hull_r, turt_f, turt_s, turt_r]):
        armor_html = (
            '<div class="vc-section-title">🛡️ Бронирование</div>'
            + _armor_bar("Корпус: перед", hull_f)
            + _armor_bar("Корпус: борт",  hull_s)
            + _armor_bar("Корпус: корма", hull_r)
            + _armor_bar("Башня: перед",  turt_f)
            + _armor_bar("Башня: борт",   turt_s)
            + _armor_bar("Башня: корма",  turt_r)
        )

    weapon_rows = ""
    if caliber:  weapon_rows += _stat_row("Калибр",        f"{caliber:.0f} мм")
    if gun_spd:  weapon_rows += _stat_row("Нач. скорость", f"{gun_spd:.0f} м/с")
    perks = []
    if has_atgm:  perks.append("🚀 ATGM")
    if has_therm: perks.append("🌡️ Термооптика")
    if has_heat:  perks.append("🔥 HEAT/HESH")
    if has_aphe:  perks.append("💥 APHE")
    ammo_chips = ("".join(_ammo_chip(t) for t in ammo_types[:12])
                  if ammo_types else '<span style="color:#475569;font-size:.7rem">нет данных</span>')
    perks_html = (f'<div style="margin-top:6px;font-size:.72rem;color:#a7f3d0">{" &nbsp;|&nbsp; ".join(perks)}</div>'
                  if perks else "")
    weapon_section = (
        f'<div class="vc-section-title">🔫 Вооружение</div>'
        f'{weapon_rows}<div style="margin-top:6px">{ammo_chips}</div>{perks_html}'
    ) if (weapon_rows or ammo_types or perks) else ""

    mobility_html = ""
    if spd_rb > 0 or hp_rb > 0:
        pw = (hp_rb / (mass / 1000)) if mass > 0 and hp_rb > 0 else 0
        pw_cls = "vc-value-green" if pw >= 20 else "vc-value-yellow" if pw >= 12 else "vc-value-red"
        parts = []
        if spd_rb: parts.append(f"Скорость {spd_rb} км/ч")
        if pw:     parts.append(f"Уд. мощность <span class='{pw_cls}'>{pw:.1f} л.с./т</span>")
        if crew:   parts.append(f"Экипаж {crew} чел.")
        mobility_html = (
            '<div class="vc-section-title">⚡ Подвижность</div>'
            '<div style="font-size:.78rem;color:#e2e8f0;display:flex;gap:20px;flex-wrap:wrap">'
            + "".join(f"<span>{p}</span>" for p in parts) + "</div>"
        )

    footer_match = f"✅ match {match_sc:.0%}" if match_sc > 0 else "⚠️ vdb нет данных"
    footer_extra = ""
    if rel_date: footer_extra += f"Добавлено: {rel_date}"
    if ver:      footer_extra += f"&nbsp;|&nbsp;{ver}"

    return f"""
<div class="vc-card">
  <div class="vc-header">
    <div class="vc-title">{flag} {name}</div>
    <div class="vc-subtitle">
      {type_icon} {vtype.replace("_", " ").title()}
      &nbsp;·&nbsp; {nation.title()}
      &nbsp;·&nbsp; БР {br:.1f}
      &nbsp;·&nbsp; Ранг {era_str}
    </div>
    <div style="margin-top:8px">{badges}</div>
  </div>
  <div class="vc-body">
    <div style="display:flex;align-items:center;gap:20px;margin-bottom:12px">
      <div style="display:inline-flex;flex-direction:column;align-items:center;justify-content:center;
                  width:66px;height:66px;border-radius:50%;border:3px solid {meta_col};
                  background:radial-gradient(circle,#064e3b 0%,#0f172a 100%);
                  box-shadow:0 0 14px {meta_col}44;flex-shrink:0">
        <span style="font-family:Rajdhani,sans-serif;font-size:1.3rem;font-weight:700;color:{meta_col};line-height:1">{meta:.0f}</span>
        <span style="font-size:.5rem;color:#6ee7b7;letter-spacing:.1em;text-transform:uppercase">META</span>
      </div>
      <div style="display:inline-flex;flex-direction:column;align-items:center;justify-content:center;
                  width:66px;height:66px;border-radius:50%;border:3px solid {farm_col};
                  background:radial-gradient(circle,#1c1917 0%,#0f172a 100%);
                  box-shadow:0 0 14px {farm_col}44;flex-shrink:0">
        <span style="font-family:Rajdhani,sans-serif;font-size:1.3rem;font-weight:700;color:{farm_col};line-height:1">{farm:.0f}</span>
        <span style="font-size:.5rem;color:#a78bfa;letter-spacing:.1em;text-transform:uppercase">FARM</span>
      </div>
      <div style="display:flex;flex-direction:column;gap:3px;font-size:.78rem">
        {_stat_row("WinRate", f"{wr:.1f}%", wr_cls)}
        {_stat_row("K/D",     f"{kd:.2f}")}
        {_stat_row("Боёв",    fmt_num(battles))}
      </div>
    </div>
    {econ_section}
    {armor_html}
    {weapon_section}
    {mobility_html}
  </div>
  <div class="vc-footer">
    <span>{identifier or "—"}</span>
    <span>{footer_extra}</span>
    <span>{footer_match}</span>
  </div>
</div>"""
