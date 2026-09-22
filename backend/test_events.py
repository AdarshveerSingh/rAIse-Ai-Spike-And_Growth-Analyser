from app.youtube.client import get_channel
from app.youtube.client import get_video_ids
from app.youtube.client import get_videos

from app.analysis.metrics import prepare_videos
from app.analysis.events import (
    detect_growth_events,
    get_event_summary
)


# --------------------------------------------------
# Fetch YouTube data
# --------------------------------------------------

channel = get_channel(
    "UC_x5XG1OV2P6uZZ5FSM9Ttw"
)

video_ids = get_video_ids(
    channel["uploads_playlist_id"]
)

videos = get_videos(video_ids)


# --------------------------------------------------
# Prepare metrics
# --------------------------------------------------

videos = prepare_videos(videos)


# --------------------------------------------------
# Detect growth events
# --------------------------------------------------

events = detect_growth_events(
    videos
)

summary = get_event_summary(events)


# --------------------------------------------------
# Print results
# --------------------------------------------------

print(
    "\nGrowth events found:",
    len(summary)
)


for event in summary:

    print(
        f"\n{event['published_at'].date()} | "
        f"{event['classification']}"
    )

    print(
        f"Title: {event['title']}"
    )

    print(
        f"Spike: "
        f"{event['spike_ratio']}x baseline"
    )

    # Before baseline
    if event["before_median"] is not None:
        print(
            f"Before: "
            f"{event['before_median']:,} views"
        )
    else:
        print(
            "Before: insufficient data"
        )

    # After baseline
    if event["after_median"] is not None:
        print(
            f"After: "
            f"{event['after_median']:,} views"
        )
    else:
        print(
            "After: insufficient data"
        )

    # Performance retention
    if event["performance_retention"] is not None:
        print(
            f"Performance retention: "
            f"{event['performance_retention']}x"
        )
    else:
        print(
            "Performance retention: "
            "insufficient data"
        )

    print(
        f"Elevated follow-ups: "
        f"{event['elevated_videos']}"
    )