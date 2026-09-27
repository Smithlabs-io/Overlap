"""Timezone reference data (region -> IANA names), shipped inside the package."""
import json
from functools import lru_cache
from pathlib import Path
from typing import Dict, List

_DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "timezone_data.json"


@lru_cache(maxsize=1)
def load_timezone_reference() -> Dict[str, List[str]]:
    with open(_DATA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)
