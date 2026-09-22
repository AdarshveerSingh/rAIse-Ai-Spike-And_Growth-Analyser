from app.youtube.client import (
    get_channel,
    get_video_ids,
    get_videos
)

from app.analysis.metrics import prepare_videos
from app.analysis.rolling import rolling_baseline


CHANNEL_ID = "UC7_YxT-KID8kRbqZo7MyscQ"


print("=" * 70)
print("1. FETCHING CHANNEL")
print("=" * 70)

channel = get_channel(CHANNEL_ID)

print("Channel:", channel["title"])
print("Uploads playlist:", channel["uploads_playlist_id"])


print()
print("=" * 70)
print("2. FETCHING VIDEO IDS")
print("=" * 70)

video_ids = get_video_ids(
    channel["uploads_playlist_id"]
)

print("Video IDs:", len(video_ids))


print()
print("=" * 70)
print("3. FETCHING VIDEO METADATA")
print("=" * 70)

videos = get_videos(video_ids)

print("Videos:", len(videos))


print()
print("=" * 70)
print("4. PREPARING VIDEOS")
print("=" * 70)

prepared = prepare_videos(videos)

print("Prepared:", len(prepared))


print()
print("=" * 70)
print("5. CALCULATING ROLLING BASELINE")
print("=" * 70)

result = rolling_baseline(
    prepared,
    window=10
)

print("Rolling baseline complete:", len(result))


print()
print("=" * 70)
print("6. LAST 20 RESULTS")
print("=" * 70)

for video in result[-20:]:

    print()
    print(video["title"])
    print("Views:", video["views"])
    print("Baseline:", video["rolling_baseline_views"])
    print("Spike ratio:", video["rolling_spike_ratio"])
    print("Robust Z:", video["robust_z"])


print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)