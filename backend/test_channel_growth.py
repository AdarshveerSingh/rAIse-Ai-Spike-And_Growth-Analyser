from app.youtube.client import get_videos
from app.analysis.metrics import prepare_videos
from app.analysis.channel_growth import (
    calculate_period_baselines,
    add_period_growth,
)


CHANNEL_ID = "YOUR_CHANNEL_ID"

videos = get_videos(CHANNEL_ID)

videos = prepare_videos(videos)

growth = calculate_period_baselines(
    videos,
    period="year"
)

growth = add_period_growth(growth)

print("=" * 70)
print("CHANNEL GROWTH")
print("=" * 70)

for row in growth:

    print(
        f'{row["period"]}: '
        f'{row["video_count"]} videos | '
        f'median={row["median_views"]:,} | '
        f'change={row["median_change_ratio"]}'
    )