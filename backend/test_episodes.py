from collections import Counter

from app.youtube.client import (
    get_channel,
    get_video_ids,
    get_videos
)

from app.analysis.metrics import prepare_videos
from app.analysis.spikes import detect_view_spikes

from app.analysis.episodes import (
    analyze_growth_event,
    print_growth_event
)


# ==========================================================
# CHANNELS
# ==========================================================

CHANNELS = {
    "Google for Developers": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
    "Markiplier": "UC7_YxT-KID8kRbqZo7MyscQ",
    "Dynamo Gaming": "UCqNH56x9g4QYVpzmWTzqVYg"
}


# ==========================================================
# SETTINGS
# ==========================================================

BEFORE_COUNT = 5
SHORT_COUNT = 5
LONG_COUNT = 10

SPIKE_THRESHOLD = 3.0
RETENTION_THRESHOLD = 1.5


# ==========================================================
# PROCESS CHANNEL
# ==========================================================

def process_channel(channel_name, channel_id):

    print("\n\n")
    print("#" * 100)
    print(channel_name.upper())
    print("#" * 100)

    # ------------------------------------------------------
    # CHANNEL
    # ------------------------------------------------------

    channel = get_channel(channel_id)

    video_ids = get_video_ids(
        channel["uploads_playlist_id"]
    )

    videos = get_videos(video_ids)

    # ------------------------------------------------------
    # CONTENT TYPES
    # ------------------------------------------------------

    content_types = Counter(
        video["content_type"]
        for video in videos
    )

    print("\nContent types:")

    for content_type, count in content_types.items():
        print(
            f"{content_type}: {count}"
        )

    # ------------------------------------------------------
    # REGULAR VIDEOS ONLY
    # ------------------------------------------------------

    analysis_videos = [
        video
        for video in videos
        if video["content_type"] == "REGULAR"
    ]

    print(
        f"\nVideos used for growth analysis: "
        f"{len(analysis_videos)}"
    )

    if len(analysis_videos) < BEFORE_COUNT + 1:
        print(
            "Not enough regular videos."
        )
        return

    # ------------------------------------------------------
    # PREPARE
    # ------------------------------------------------------

    videos = prepare_videos(
        analysis_videos
    )

    # ------------------------------------------------------
    # SPIKES
    # ------------------------------------------------------

    spikes = detect_view_spikes(
        videos,
        before_count=BEFORE_COUNT,
        threshold=SPIKE_THRESHOLD
    )

    print(
        f"Spike candidates: "
        f"{len(spikes)}"
    )

    if not spikes:
        print("No spike candidates found.")
        return

    # ------------------------------------------------------
    # ANALYZE ALL EVENTS
    # ------------------------------------------------------

    events = []

    for spike in spikes:

        event = analyze_growth_event(
            videos,
            spike,

            before_count=BEFORE_COUNT,
            short_count=SHORT_COUNT,
            long_count=LONG_COUNT,

            retention_threshold=RETENTION_THRESHOLD
        )

        if event is not None:
            events.append(event)

    print(
        f"Events with sufficient data: "
        f"{len(events)}"
    )

    if not events:
        return

    # ======================================================
    # CLASSIFICATION SUMMARY
    # ======================================================

    classifications = Counter(
        event["event_type"]
        for event in events
    )

    progressive_count = sum(
        event["progressive_trajectory"]
        for event in events
    )

    print("\n")
    print("-" * 80)
    print("EVENT CLASSIFICATION SUMMARY")
    print("-" * 80)

    for event_type, count in classifications.items():

        print(
            f"{event_type:<25} : {count}"
        )

    print(
        f"{'PROGRESSIVE TRAJECTORY':<25} : "
        f"{progressive_count}"
    )

    # ======================================================
    # SELECT REPRESENTATIVE EVENTS
    # ======================================================

    selected = []

    # ------------------------------------------------------
    # EARLIEST
    # ------------------------------------------------------

    earliest = min(
        events,
        key=lambda x: x["published_at"]
    )

    selected.append(
        ("EARLIEST", earliest)
    )

    # ------------------------------------------------------
    # STRONGEST
    # ------------------------------------------------------

    strongest = max(
        events,
        key=lambda x: x["spike_ratio"]
    )

    if strongest["video_id"] != earliest["video_id"]:
        selected.append(
            ("STRONGEST", strongest)
        )

    # ------------------------------------------------------
    # ONE OF EACH CLASSIFICATION
    # ------------------------------------------------------

    seen_types = set()

    for event in events:

        event_type = event["event_type"]

        if event_type in seen_types:
            continue

        if event["video_id"] == earliest["video_id"]:
            continue

        if event["video_id"] == strongest["video_id"]:
            continue

        selected.append(
            (event_type, event)
        )

        seen_types.add(event_type)

    # ======================================================
    # PRINT REPRESENTATIVE EVENTS
    # ======================================================

    for label, event in selected:

        print("\n\n")
        print("#" * 100)
        print(
            f"{channel_name} — {label}"
        )
        print("#" * 100)

        print_growth_event(
            event
        )


# ==========================================================
# RUN ALL CHANNELS
# ==========================================================

for channel_name, channel_id in CHANNELS.items():

    process_channel(
        channel_name,
        channel_id
    )