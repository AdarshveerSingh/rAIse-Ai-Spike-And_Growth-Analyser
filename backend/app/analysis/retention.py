import statistics


def analyze_retention(
    videos,
    spike,
    before_count=5,
    after_count=5,
    retention_threshold=1.5
):
    spike_index = None

    for i, video in enumerate(videos):
        if video["id"] == spike["video_id"]:
            spike_index = i
            break

    if spike_index is None:
        return None

    before = videos[
        max(0, spike_index - before_count):spike_index
    ]

    after = videos[
        spike_index + 1:
        min(len(videos), spike_index + after_count + 1)
    ]

    if len(before) < 3 or len(after) < 3:
        return {
            "video_id": spike["video_id"],
            "retained": None,
            "reason": "Insufficient surrounding videos",
            "before": before,
            "after": after
        }

    before_views = [
        video["views"] for video in before
    ]

    after_views = [
        video["views"] for video in after
    ]

    before_median = statistics.median(before_views)
    after_median = statistics.median(after_views)

    if before_median == 0:
        return {
            "video_id": spike["video_id"],
            "retained": None,
            "reason": "Pre-spike baseline is zero",
            "before": before,
            "after": after
        }

    retention_ratio = after_median / before_median

    retained = retention_ratio >= retention_threshold

    elevated_count = sum(
        1 for views in after_views
        if views >= before_median * retention_threshold
    )

    return {
        "video_id": spike["video_id"],
        "retained": retained,
        "before_median": round(before_median),
        "after_median": round(after_median),
        "retention_ratio": round(retention_ratio, 2),
        "elevated_videos": elevated_count,
        "after_video_count": len(after),
        "before": before,
        "after": after
    }