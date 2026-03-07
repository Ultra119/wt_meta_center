from __future__ import annotations

import json
import os
import urllib.request

SHOP_URL: str = (
    "https://github.com/gszabi99/War-Thunder-Datamine"
    "/raw/master/char.vromfs.bin_u/config/shop.blkx"
)
SHOP_FILENAME: str  = "shop.blkx"
_DOWNLOAD_TIMEOUT: int = 30

_META_KEYS = frozenset({
    "image", "reqAir", "futureReqAir", "slaveUnit",
    "gift", "marketplaceItemdefId", "isClanVehicle",
    "reqFeature", "showOnlyWhenBought", "showByPlatform",
    "beginPurchaseDate", "endPurchaseDate",
    "isCrossPromo", "crossPromoBanner", "hideFeature", "event",
})


def _try_download(dest: str) -> None:
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        print(f"[ShopParser] 📥 Скачиваем shop.blkx из War-Thunder-Datamine …")
        req = urllib.request.Request(
            SHOP_URL,
            headers={"User-Agent": "WTMetaCenter/1.0"},
        )
        with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT) as resp, \
             open(dest, "wb") as out_f:
            out_f.write(resp.read())
        print(f"[ShopParser] ✅ Скачан и сохранён → {dest}")
    except Exception as e:
        print(f"[ShopParser] ❌ Не удалось скачать shop.blkx: {e}")
        print( "[ShopParser]    Положите файл вручную: dataset/shop.blkx")
        print(f"[ShopParser]    URL: {SHOP_URL}")


def _iter_column(col_dict: dict):
    row = 0
    for key, val in col_dict.items():
        if key in _META_KEYS or not isinstance(val, dict):
            continue

        nested = [
            (k, v) for k, v in val.items()
            if k not in _META_KEYS and isinstance(v, dict) and "rank" in v
        ]

        if nested:
            for sub_key, sub_val in nested:
                yield sub_key, int(sub_val.get("rank", 0) or 0), key, row
                row += 1
        elif "rank" in val:
            yield key, int(val.get("rank", 0) or 0), "", row
            row += 1


def parse_shop_file(path: str) -> dict[str, dict]:
    if not os.path.exists(path):
        _try_download(path)

    if not os.path.exists(path):
        print("[ShopParser] ⚠️  shop.blkx недоступен — порядок дерева отключён")
        return {}

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ShopParser] ❌ Ошибка чтения shop.blkx: {e}")
        return {}

    result: dict[str, dict] = {}

    for nation_key, nation_data in data.items():
        if not isinstance(nation_data, dict):
            continue
        nation = nation_key.replace("country_", "")

        for branch, branch_data in nation_data.items():
            if not isinstance(branch_data, dict):
                continue
            columns = branch_data.get("range", [])
            if not isinstance(columns, list):
                continue

            for col_idx, col_dict in enumerate(columns):
                if not isinstance(col_dict, dict):
                    continue
                for vid, rank, group, row_idx in _iter_column(col_dict):
                    result[vid] = {
                        "shop_column": col_idx,
                        "shop_row":    row_idx,
                        "shop_rank":   rank,
                        "shop_group":  group,
                        "shop_nation": nation,
                        "shop_branch": branch,
                        "shop_order":  col_idx * 10000 + row_idx,
                    }

    print(f"[ShopParser] ✅ Распарсено {len(result)} позиций из shop.blkx")
    return result
