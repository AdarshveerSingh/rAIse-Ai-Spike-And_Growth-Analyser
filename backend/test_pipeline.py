import json

from app.youtube.client import (
    get_channel,
    get_video_ids,
    get_videos
)

from app.analysis.pipeline import run_analysis_pipeline


CHANNEL_ID = "UC7_YxT-KID8kRbqZo7MyscQ"


print("=" * 70)
print("1. FETCHING DATA")
print("=" * 70)

channel = get_channel(CHANNEL_ID)

video_ids = get_video_ids(
    channel["uploads_playlist_id"]
)

videos = get_videos(video_ids)

print("Channel:", channel["title"])
print("Videos:", len(videos))


print()
print("=" * 70)
print("2. RUNNING QUANTITATIVE PIPELINE")
print("=" * 70)

result = run_analysis_pipeline(videos)


print()
print("=" * 70)
print("FULL QUANTITATIVE PIPELINE")
print("=" * 70)

print()
print("Videos:", result["video_count"])
print("Spikes:", result["spike_count"])
print("Events:", result["event_count"])


print()
print("KEY EVENTS")
print("-" * 70)

for name, event in result["key_events"].items():

    if not event:
        print(name, "→ NONE")
        continue

    print(
        f'{name}: '
        f'{event["title"]} '
        f'({event["spike_ratio"]}x)'
    )


print()
print("CHANNEL GROWTH PERIODS")
print("-" * 70)

for row in result["channel_growth"]:

    print(
        row["period"],
        "| median:",
        row["median_views"],
        "| change:",
        row["median_change_ratio"]
    )


print()
print("PERIOD SPIKES")
print("-" * 70)

for row in result["period_spike_analysis"]:

    print(
        row["period"],
        "| spikes:",
        row["spike_count"],
        "| rate:",
        row["spike_rate"]
    )


with open(
    "cache/test_quantitative_pipeline.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        result,
        f,
        indent=2,
        default=str
    )


print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)

print(
    "Saved: cache/test_quantitative_pipeline.json"
)