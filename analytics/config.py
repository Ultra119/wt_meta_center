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
            log_debug("settings.json has been created with default values.")
        except Exception as e:
            log_debug(f"Failed to create settings.json: {e}")
        return dict(DEFAULT_SETTINGS)

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)

        merged = dict(DEFAULT_SETTINGS)
        merged.update(loaded)
        log_debug(f"settings.json downloaded: {merged}")
        return merged

    except Exception as e:
        log_debug(f"Error reading settings.json; defaults are being used: {e}")
        return dict(DEFAULT_SETTINGS)
