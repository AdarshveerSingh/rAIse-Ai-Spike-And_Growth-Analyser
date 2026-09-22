from app.analysis.spikes import detect_view_spikes
from app.analysis.retention import analyze_retention


def detect_growth_events(
    videos,
    spike_threshold=3.0,
    before_count=5,
    after_count=5,
    retention_threshold=1.5
):
    """
    Detect candidate growth events across the entire channel.

    A growth event starts with a significant video-performance spike,
    then checks whether performance remains elevated afterward.
    """

    spikes = detect_view_spikes(
        videos,
        before_count=before_count,
        threshold=spike_threshold
    )

    events = []

    for spike in spikes:

        retention = analyze_retention(
            videos,
            spike,
            before_count=before_count,
            after_count=after_count,
            retention_threshold=retention_threshold
        )

        if retention is None:
            continue

        event = {
            "video_id": spike["video_id"],
            "title": spike["title"],
            "published_at": spike["published_at"],

            "spike_views": spike["views"],
            "baseline_views": spike["baseline_views"],
            "spike_ratio": spike["spike_ratio"],

            # Performance retention
            "performance_retention":
                retention.get("retention_ratio"),

            "retained":
                retention.get("retained"),

            "elevated_videos":
                retention.get("elevated_videos", 0),

            # These may not exist when there is
            # insufficient surrounding data.
            "before_median":
                retention.get("before_median"),

            "after_median":
                retention.get("after_median"),

            "before":
                retention.get("before", []),

            "after":
                retention.get("after", []),

            "reason":
                retention.get("reason")
        }

        events.append(event)

    return events


def classify_growth_event(event):
    """
    Descriptive classification based only on
    post-spike performance.
    """

    if event["retained"] is None:
        return "INSUFFICIENT_DATA"

    if event["retained"]:
        return "SUSTAINED_PERFORMANCE"

    return "ONE_OFF_SPIKE"


def get_event_summary(events):
    """
    Produce a compact representation for the
    frontend and later AI analysis.
    """

    summary = []

    for event in events:

        summary.append({
            "video_id":
                event["video_id"],

            "title":
                event["title"],

            "published_at":
                event["published_at"],

            "spike_ratio":
                event["spike_ratio"],

            "spike_views":
                event["spike_views"],

            "baseline_views":
                event["baseline_views"],

            "before_median":
                event["before_median"],

            "after_median":
                event["after_median"],

            "performance_retention":
                event["performance_retention"],

            "retained":
                event["retained"],

            "elevated_videos":
                event["elevated_videos"],

            "classification":
                classify_growth_event(event)
        })

    return summary