from __future__ import annotations

import csv
import os
import re
import urllib.request
from typing import Optional

_SUFFIX_RE = re.compile(r"(_shop|_\d+)$")

_BADGE_PREFIX_RE = re.compile(r"^[^\w(\[{\"']+", re.UNICODE)

def _strip_badge_prefix(name: str) -> str:
    return _BADGE_PREFIX_RE.sub("", name).strip()


UNITS_CSV_URL: str = (
    "https://github.com/gszabi99/War-Thunder-Datamine"
    "/raw/master/lang.vromfs.bin_u/lang/units.csv"
)
UNITS_CSV_FILENAME: str = "units.csv"
_DOWNLOAD_TIMEOUT: int = 20


class UnitsCsvTranslator:
    def __init__(self, dataset_dir: str) -> None:
        self._en_to_id: dict[str, str] = {}   # "t-34 (1940)"    → "ussr_t_34_1940"
        self._id_to_en: dict[str, str] = {}   # "ussr_t_34_1940" → "T-34 (1940)"
        self.loaded: bool = False

        local_path = os.path.join(dataset_dir, UNITS_CSV_FILENAME)
        self._load(local_path)


    def find_id(self, display_name: str) -> Optional[str]:
        if not display_name:
            return None
        return self._en_to_id.get(display_name.strip().lower())

    def find_name(self, identifier: str) -> Optional[str]:
        if not identifier:
            return None
        return self._id_to_en.get(identifier)

    def coverage_report(self, identifiers: list[str]) -> dict:
        covered = [i for i in identifiers if i in self._id_to_en]
        missing = [i for i in identifiers if i not in self._id_to_en]
        pct = 100.0 * len(covered) / max(len(identifiers), 1)
        return {
            "total":   len(identifiers),
            "covered": len(covered),
            "missing": missing,
            "pct":     round(pct, 1),
        }

    def __len__(self) -> int:
        return len(self._en_to_id)

    def __repr__(self) -> str:
        status = "loaded" if self.loaded else "not loaded"
        return f"UnitsCsvTranslator({len(self._en_to_id)} names, {status})"


    def _load(self, path: str) -> None:
        if not os.path.exists(path):
            self._try_download(path)
        if not os.path.exists(path):
            print(
                "[UnitsCsv] ⚠️  units.csv is unavailable — equipment names will be "
                "taken from the source data without normalization"
            )
            return
        self._parse(path)

    def _try_download(self, dest: str) -> None:
        try:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            print("[UnitsCsv] 📥 Download units.csv from War-Thunder-Datamine …")
            req = urllib.request.Request(
                UNITS_CSV_URL,
                headers={"User-Agent": "WTMetaCenter/1.0"},
            )
            with urllib.request.urlopen(req, timeout=_DOWNLOAD_TIMEOUT) as resp, \
                    open(dest, "wb") as out_f:
                out_f.write(resp.read())
            print(f"[UnitsCsv] ✅ Downloaded and saved → {dest}")
        except Exception as e:
            print(f"[UnitsCsv] ❌ Unable to download units.csv: {e}")
            print( "[UnitsCsv]    Upload the file manually: dataset/units.csv")
            print(f"[UnitsCsv]    URL: {UNITS_CSV_URL}")

    def _parse(self, path: str) -> None:
        count_parsed  = 0
        count_skipped = 0
        try:
            with open(path, encoding="utf-8", errors="replace", newline="") as f:
                reader = csv.reader(f, delimiter=";", quotechar='"')
                for i, row in enumerate(reader):
                    if i == 0:
                        continue
                    if len(row) < 2:
                        count_skipped += 1
                        continue

                    raw_id  = row[0].strip().strip('"')
                    english = row[1].strip()

                    if len(english) >= 2 and english[0] == '"' and english[-1] == '"':
                        english = english[1:-1].replace('""', '"')

                    english = _strip_badge_prefix(english)

                    if not raw_id or not english:
                        count_skipped += 1
                        continue
                    if english.startswith("<") and english.endswith(">"):
                        count_skipped += 1
                        continue
                    if english in ("-", "—", " "):
                        count_skipped += 1
                        continue

                    # «units/ussr_t_34_1940_shop» → «ussr_t_34_1940»
                    identifier = raw_id.split("/", 1)[-1] if "/" in raw_id else raw_id
                    base_id    = _SUFFIX_RE.sub("", identifier)
                    en_key     = english.lower()
                    is_shop    = identifier.endswith("_shop")

                    if en_key not in self._en_to_id or is_shop:
                        self._en_to_id[en_key] = base_id
                    if base_id not in self._id_to_en or is_shop:
                        self._id_to_en[base_id] = english

                    count_parsed += 1

        except Exception as e:
            print(f"[UnitsCsv] ❌ Error parsing units.csv: {e}")
            return

        self.loaded = True
        print(
            f"[UnitsCsv] ✅ {count_parsed} records loaded "
            f"({len(self._en_to_id)} (unique names) from units.csv"
        )
