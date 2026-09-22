import json
from pathlib import Path


CACHE_DIR = Path("cache/thumbnails")
CACHE_DIR.mkdir(parents=True, exist_ok=True)


def get_cached_analysis(video_id):
    cache_file = CACHE_DIR / f"{video_id}.json"

    if not cache_file.exists():
        return None

    with open(cache_file, "r", encoding="utf-8") as f:
        return json.load(f)


def save_cached_analysis(video_id, analysis):
    cache_file = CACHE_DIR / f"{video_id}.json"

    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(
            analysis,
            f,
            indent=2,
            ensure_ascii=False
        )