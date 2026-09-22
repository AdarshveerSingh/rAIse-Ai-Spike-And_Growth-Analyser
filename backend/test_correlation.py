from app.youtube.client import get_videos
from app.analysis.metrics import prepare_videos
from app.analysis.rolling import rolling_baseline
from app.analysis.spikes import detect_spikes
from app.analysis.correlation import analyze_period_spikes


CHANNEL_ID = "YOUR_CHANNEL_ID"

videos = get_videos(CHANNEL_ID)

videos = prepare_videos(videos)

videos = rolling_baseline(
    videos,
    window=10
)

spikes = detect_spikes(
    videos
)

periods = analyze_period_spikes(
    videos,
    spikes,
    period="year"
)

print("=" * 70)
print("PERIOD SPIKE CORRELATION")
print("=" * 70)

for period in periods:

    print(
        f'{period["period"]}: '
        f'{period["video_count"]} videos | '
        f'{period["spike_count"]} spikes | '
        f'rate={period["spike_rate"]}'
    )

    if period["spike_titles"]:

        for title in period["spike_titles"]:

            print("   -", title)