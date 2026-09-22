from app.youtube.client import get_channel
from app.youtube.client import get_video_ids
from app.youtube.client import get_videos

from app.analysis.metrics import prepare_videos
from app.analysis.spikes import (
    detect_view_spikes,
    get_top_spikes
)

from app.analysis.context import get_spike_context
from app.ai.analyze import analyze_spike

from app.analysis.baseline import get_thumbnail_analysis_set

from app.vision.compare import analyze_thumbnail_groups

from app.analysis.thumbnail_stats import calculate_thumbnail_stats

from app.progress import ProgressTracker


# --------------------------------------------------
# Progress tracker
# --------------------------------------------------

tracker = ProgressTracker()


# --------------------------------------------------
# 1. Fetch channel
# --------------------------------------------------

tracker.update(
    "FETCHING_CHANNEL",
    "Fetching channel information...",
    10
)

channel = get_channel(
    "UC_x5XG1OV2P6uZZ5FSM9Ttw"
)


# --------------------------------------------------
# 2. Fetch videos
# --------------------------------------------------

tracker.update(
    "FETCHING_VIDEOS",
    "Fetching video history...",
    20
)

video_ids = get_video_ids(
    channel["uploads_playlist_id"]
)
print("Total videos found:", len(video_ids))
videos = get_videos(video_ids)

print("Channel:", channel["title"])
print("Videos:", len(videos))


# --------------------------------------------------
# 3. Calculate metrics
# --------------------------------------------------

tracker.update(
    "CALCULATING_METRICS",
    "Calculating performance metrics...",
    35
)

videos = prepare_videos(videos)


# --------------------------------------------------
# 4. Detect spikes
# --------------------------------------------------

tracker.update(
    "DETECTING_SPIKES",
    "Detecting potential growth spikes...",
    45
)

spikes = detect_view_spikes(videos)

top_spikes = get_top_spikes(
    spikes,
    5
)


# --------------------------------------------------
# Check that we found a spike
# --------------------------------------------------

if not top_spikes:
    tracker.update(
        "COMPLETE",
        "Analysis complete — no significant spikes found.",
        100
    )

    print("\nNo significant spikes found.")
    exit()


# --------------------------------------------------
# 5. Prepare thumbnail comparison groups
# --------------------------------------------------

tracker.update(
    "PREPARING_THUMBNAILS",
    "Selecting thumbnails for comparison...",
    55
)

thumbnail_set = get_thumbnail_analysis_set(
    videos,
    top_spikes[0]
)


# --------------------------------------------------
# 6. Analyze thumbnails
# --------------------------------------------------

tracker.update(
    "ANALYZING_THUMBNAILS",
    "Analyzing thumbnail visual patterns...",
    65
)

thumbnail_results = analyze_thumbnail_groups(
    thumbnail_set
)


# --------------------------------------------------
# 7. Compare thumbnail characteristics
# --------------------------------------------------

tracker.update(
    "COMPARING_THUMBNAILS",
    "Comparing thumbnail characteristics...",
    80
)

thumbnail_stats = calculate_thumbnail_stats(
    thumbnail_results
)


# --------------------------------------------------
# Print thumbnail statistics
# --------------------------------------------------

print("\n\nThumbnail statistics:\n")

for group, stats in thumbnail_stats.items():

    print(f"\n[{group.upper()}]")

    print(
        f"Sample size: {stats['sample_size']}"
    )

    for feature, values in stats.items():

        if feature == "sample_size":
            continue

        print(
            f"{feature}: {values}"
        )


# --------------------------------------------------
# Print thumbnail visual analysis
# --------------------------------------------------

print("\nThumbnail visual analysis:\n")

for result in thumbnail_results:

    print(
        f"\n[{result['group'].upper()}]"
    )

    print(
        result["title"]
    )

    if "error" in result:

        print(
            "ERROR:",
            result["error"]
        )

        continue
    print(
        "CACHE:",
        "HIT" if result.get("cached") else "MISS"
    )

    print(
        result["visual_analysis"]
    )


# --------------------------------------------------
# Print thumbnail analysis groups
# --------------------------------------------------

print("\nThumbnail analysis groups:")

for group_name, group in thumbnail_set.items():

    if isinstance(group, dict):

        video = group

        print(
            f"\n{group_name.upper()}: "
            f"{video['title']}"
        )

    else:

        print(
            f"\n{group_name.upper()}:"
        )

        for video in group:

            print(
                f"- {video['published_at'].date()} | "
                f"{video['views']:,} views | "
                f"{video['title']}"
            )


# --------------------------------------------------
# 8. Build spike context
# --------------------------------------------------

tracker.update(
    "BUILDING_CONTEXT",
    "Building context around the detected spike...",
    85
)

context = get_spike_context(
    videos,
    top_spikes[0],
    window=3
)


# --------------------------------------------------
# 9. AI spike analysis
# --------------------------------------------------

tracker.update(
    "ANALYZING_SPIKE",
    "Analyzing the growth spike with AI...",
    90
)

analysis = analyze_spike(
    context
)


# --------------------------------------------------
# Print AI analysis
# --------------------------------------------------

print("\nAI SPIKE ANALYSIS:\n")

print(
    analysis
)


# --------------------------------------------------
# 10. Complete
# --------------------------------------------------

tracker.update(
    "COMPLETE",
    "Analysis complete.",
    100
)


# --------------------------------------------------
# Print top spikes
# --------------------------------------------------

print("\nTop potential spikes:\n")

for spike in top_spikes:

    print(
        f"{spike['published_at'].date()} | "
        f"{spike['spike_ratio']}x median | "
        f"{spike['views']:,} views | "
        f"{spike['title']}"
    )


# --------------------------------------------------
# Final progress status
# --------------------------------------------------

print("\nAnalysis status:")

print(
    tracker.get_status()
)