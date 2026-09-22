from app.youtube.client import (
    get_channel,
    get_video_ids,
    get_videos
)

from app.analysis.metrics import prepare_videos
from app.analysis.rolling import rolling_baseline
from app.analysis.spikes import detect_spikes, rank_spikes


CHANNEL_ID = "UC7_YxT-KID8kRbqZo7MyscQ"


print("=" * 70)
print("1. FETCHING DATA")
print("=" * 70)

channel = get_channel(CHANNEL_ID)

video_ids = get_video_ids(
    channel["uploads_playlist_id"]
)

videos = get_videos(video_ids)

print("Videos:", len(videos))


print()
print("=" * 70)
print("2. PREPARING DATA")
print("=" * 70)

videos = prepare_videos(videos)

print("Prepared:", len(videos))


print()
print("=" * 70)
print("3. ROLLING BASELINE")
print("=" * 70)

videos = rolling_baseline(
    videos,
    window=10
)

print("Baseline calculated")


print()
print("=" * 70)
print("4. DETECTING SPIKES")
print("=" * 70)

spikes = detect_spikes(
    videos,
    min_ratio=3.0,
    min_robust_z=2.5
)

spikes = rank_spikes(spikes)

print("Total spikes:", len(spikes))


print()
print("=" * 70)
print("TOP 30 SPIKES")
print("=" * 70)

for i, spike in enumerate(spikes[:30], 1):

    print()
    print(f"#{i}")
    print("Title:", spike["title"])
    print("Date:", spike["published_at"])
    print("Views:", spike["views"])
    print("Baseline:", spike["baseline_views"])
    print("Spike ratio:", spike["spike_ratio"])
    print("Robust Z:", spike["robust_z"])
    print("Signal:", spike["signal"])


print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)