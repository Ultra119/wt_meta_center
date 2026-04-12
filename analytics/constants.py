WT_BR_STEPS: list = [
    1.0, 1.3, 1.7,
    2.0, 2.3, 2.7,
    3.0, 3.3, 3.7,
    4.0, 4.3, 4.7,
    5.0, 5.3, 5.7,
    6.0, 6.3, 6.7,
    7.0, 7.3, 7.7,
    8.0, 8.3, 8.7,
    9.0, 9.3, 9.7,
    10.0, 10.3, 10.7,
    11.0, 11.3, 11.7,
    12.0, 12.3, 12.7,
    13.0,
]

VEHICLE_TYPE_CATEGORY: dict = {
    "fighter":            "Aviation",
    "bomber":             "Aviation",
    "assault":            "Aviation",

    "utility_helicopter": "Helicopter",
    "attack_helicopter":  "Helicopter",

    "medium_tank":        "Ground",
    "light_tank":         "Ground",
    "spaa":               "Ground",
    "heavy_tank":         "Ground",
    "tank_destroyer":     "Ground",

    "destroyer":          "LargeFleet",
    "heavy_cruiser":      "LargeFleet",
    "light_cruiser":      "LargeFleet",
    "battleship":         "LargeFleet",
    "battlecruiser":      "LargeFleet",

    "boat":               "SmallFleet",
    "heavy_boat":         "SmallFleet",
    "frigate":            "SmallFleet",
    "barge":              "SmallFleet",
}

#   wr    — процент побед
#   ks_g  — наземные убийства / возрождение
#   ks_a  — воздушные убийства / возрождение
#   kd    — K/D ratio
#   ks_n  — морские убийства / возрождение
#   surv  — выживаемость (1 - смерти/возрождения)

ROLE_WEIGHTS: dict = {
    "medium_tank":        {"wr": 0.35, "ks_g": 0.35, "ks_a": 0.00, "kd": 0.20, "ks_n": 0.00, "surv": 0.10},
    "light_tank":         {"wr": 0.45, "ks_g": 0.20, "ks_a": 0.00, "kd": 0.10, "ks_n": 0.00, "surv": 0.25},
    "heavy_tank":         {"wr": 0.25, "ks_g": 0.30, "ks_a": 0.00, "kd": 0.35, "ks_n": 0.00, "surv": 0.10},
    "tank_destroyer":     {"wr": 0.25, "ks_g": 0.45, "ks_a": 0.00, "kd": 0.20, "ks_n": 0.00, "surv": 0.10},
    "spaa":               {"wr": 0.25, "ks_g": 0.05, "ks_a": 0.55, "kd": 0.10, "ks_n": 0.00, "surv": 0.05},
    "fighter":            {"wr": 0.30, "ks_g": 0.00, "ks_a": 0.50, "kd": 0.20, "ks_n": 0.00, "surv": 0.00},
    "bomber":             {"wr": 0.40, "ks_g": 0.30, "ks_a": 0.05, "kd": 0.15, "ks_n": 0.00, "surv": 0.10},
    "assault":            {"wr": 0.35, "ks_g": 0.35, "ks_a": 0.10, "kd": 0.15, "ks_n": 0.00, "surv": 0.05},
    "attack_helicopter":  {"wr": 0.30, "ks_g": 0.45, "ks_a": 0.05, "kd": 0.15, "ks_n": 0.00, "surv": 0.05},
    "utility_helicopter": {"wr": 0.40, "ks_g": 0.15, "ks_a": 0.20, "kd": 0.15, "ks_n": 0.00, "surv": 0.10},
    "destroyer":          {"wr": 0.35, "ks_g": 0.00, "ks_a": 0.10, "kd": 0.20, "ks_n": 0.35, "surv": 0.00},
    "heavy_cruiser":      {"wr": 0.35, "ks_g": 0.00, "ks_a": 0.10, "kd": 0.25, "ks_n": 0.30, "surv": 0.00},
    "light_cruiser":      {"wr": 0.35, "ks_g": 0.00, "ks_a": 0.15, "kd": 0.20, "ks_n": 0.30, "surv": 0.00},
    "battleship":         {"wr": 0.30, "ks_g": 0.00, "ks_a": 0.05, "kd": 0.35, "ks_n": 0.30, "surv": 0.00},
    "battlecruiser":      {"wr": 0.30, "ks_g": 0.00, "ks_a": 0.10, "kd": 0.30, "ks_n": 0.30, "surv": 0.00},
    "boat":               {"wr": 0.35, "ks_g": 0.00, "ks_a": 0.15, "kd": 0.15, "ks_n": 0.35, "surv": 0.00},
    "heavy_boat":         {"wr": 0.35, "ks_g": 0.00, "ks_a": 0.10, "kd": 0.20, "ks_n": 0.35, "surv": 0.00},
    "frigate":            {"wr": 0.35, "ks_g": 0.00, "ks_a": 0.15, "kd": 0.20, "ks_n": 0.30, "surv": 0.00},
    "barge":              {"wr": 0.30, "ks_g": 0.00, "ks_a": 0.10, "kd": 0.20, "ks_n": 0.40, "surv": 0.00},
    "_default":           {"wr": 0.35, "ks_g": 0.20, "ks_a": 0.10, "kd": 0.20, "ks_n": 0.05, "surv": 0.10},
}

DEFAULT_SETTINGS: dict = {
    "mm_window":     1.0,
    "sigmoid_scale": 1.5,
    "z_clip":        3.0,
    "wilson_z":      1.96,
    "c_battles":     5000,
    "c_spawns":      7500,
    "c_deaths":      3000,
}

def snap_to_wt_br(br: float) -> float:
    return min(WT_BR_STEPS, key=lambda x: abs(x - br))
