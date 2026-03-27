import json
import os

from logger import log_debug
from analytics.constants import DEFAULT_SETTINGS


def load_settings(script_dir: str) -> dict:
    settings_path = os.path.join(script_dir, "settings.json")

    if not os.path.exists(settings_path):
        try:
            with open(settings_path, "w", encoding="utf-8") as f:
                json.dump(DEFAULT_SETTINGS, f, ensure_ascii=False, indent=4)
            log_debug("settings.json создан с дефолтными значениями.")
        except Exception as e:
            log_debug(f"Не удалось создать settings.json: {e}")
        return dict(DEFAULT_SETTINGS)

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        merged = dict(DEFAULT_SETTINGS)
        merged.update(loaded)
        merged["meta_weights"] = {
            **DEFAULT_SETTINGS["meta_weights"],
            **loaded.get("meta_weights", {}),
        }
        log_debug(f"settings.json загружен: {merged}")
        return merged

    except Exception as e:
        log_debug(f"Ошибка чтения settings.json, используются дефолты: {e}")
        return dict(DEFAULT_SETTINGS)
