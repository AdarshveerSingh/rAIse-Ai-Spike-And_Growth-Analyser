import json
from pathlib import Path
from datetime import datetime, timezone, timedelta


CACHE_DIR = Path("cache/youtube")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CACHE_TTL = timedelta(hours=24)


def get_cache_path(cache_name):
    return CACHE_DIR / f"{cache_name}.json"


def load_cache(cache_name):
    cache_file = get_cache_path(cache_name)

    if not cache_file.exists():
        return None

    with open(cache_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    fetched_at = datetime.fromisoformat(
        data["fetched_at"]
    )

    if datetime.now(timezone.utc) - fetched_at >= CACHE_TTL:
        return None

    return data["data"]


def save_cache(cache_name, data):
    cache_file = get_cache_path(cache_name)

    payload = {
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "data": data
    }

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(
            payload,
            f,
            indent=2,
            ensure_ascii=False
        )