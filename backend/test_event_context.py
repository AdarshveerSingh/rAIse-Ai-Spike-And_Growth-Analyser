import json

from app.youtube.client import (
    get_channel,
    get_video_ids,
    get_videos
)

from app.youtube.comments import (
    fetch_all_comments
)

from app.analysis.pipeline import (
    run_analysis_pipeline
)

from app.analysis.event_context import (
    build_event_context
)


CHANNEL_ID = "UC7_YxT-KID8kRbqZo7MyscQ"


print("=" * 70)
print("1. LOADING CHANNEL")
print("=" * 70)

channel = get_channel(
    CHANNEL_ID
)

video_ids = get_video_ids(
    channel["uploads_playlist_id"]
)

videos = get_videos(
    video_ids
)

print(
    "Channel:",
    channel["title"]
)

print(
    "Videos:",
    len(videos)
)


print()
print("=" * 70)
print("2. RUNNING PIPELINE")
print("=" * 70)

result = run_analysis_pipeline(
    videos
)

print(
    "Spikes:",
    result["spike_count"]
)

print(
    "Events:",
    result["event_count"]
)


print()
print("=" * 70)
print("3. SELECTING DRUNK MINECRAFT #1")
print("=" * 70)


event = None

for candidate in result["events"]:

    if candidate["video_id"] == "OzItHn9GSRE":

        event = candidate
        break


if event is None:

    raise ValueError(
        "Drunk Minecraft #1 event not found"
    )


print(
    "Title:",
    event["title"]
)

print(
    "Classification:",
    event["event_type"]
)

print(
    "Spike ratio:",
    event["spike_ratio"]
)


print()
print("=" * 70)
print("4. LOADING COMMENTS")
print("=" * 70)

comments = fetch_all_comments(
    event["video_id"]
)

print(
    "Comments:",
    len(comments)
)


print()
print("=" * 70)
print("5. BUILDING EVENT CONTEXT")
print("=" * 70)


context = build_event_context(
    event=event,
    videos=result["videos"],
    spikes=result["spikes"],
    period_spike_analysis=result["period_spike_analysis"],
    channel_growth=result["channel_growth"],
    comments=comments
)


print(
    json.dumps(
        context,
        indent=2,
        default=str
    )
)


print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)