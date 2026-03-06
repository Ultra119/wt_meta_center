"""
WT META Center — Dash Edition
Entry point: инициализация приложения и регистрация колбэков.
"""

from dash import Dash
import dash_bootstrap_components as dbc

from analytics.core import AnalyticsCore
from analytics.constants import WT_BR_STEPS
from ui.type_filter import build_type_filter_data
from ui import layout
from ui.callbacks import meta, redbook, brackets, farm, sidebar, history

# ── Core (singleton) ──────────────────────────────────────────────────────────
core = AnalyticsCore()
core.load_data_recursive()

# ── Derived globals, shared across UI modules ─────────────────────────────────
from analytics.constants import WT_BR_STEPS

_WT_NATIONS = {
    "USA","Germany","USSR","Britain","Japan","Italy",
    "France","Sweden","Israel","China","Finland","Netherlands","Hungary",
}

if "Nation" in core.full_df.columns:
    _raw = core.full_df["Nation"].dropna().unique().tolist()
    all_nations = ["All"] + sorted(
        n for n in _raw if n.strip().title() in _WT_NATIONS or n in _WT_NATIONS
    )
else:
    all_nations = ["All"]

all_types = (
    sorted(core.full_df["Type"].dropna().unique().tolist())
    if "Type" in core.full_df.columns else []
)
tf_data = build_type_filter_data(all_types)

# ── App ────────────────────────────────────────────────────────────────────────
app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True,
    title="WT META Center",
)
server = app.server  # для деплоя (gunicorn)

app.layout = layout.build(all_nations, all_types, tf_data)

# Регистрация колбэков
meta.register(app, core, all_nations, all_types, tf_data)
redbook.register(app, core, all_types, tf_data)
brackets.register(app, core, all_types, tf_data)
farm.register(app, core, all_types, tf_data)
sidebar.register(app, core)
history.register(app, core)

if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0", port=8050)
