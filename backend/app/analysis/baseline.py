def get_thumbnail_analysis_set(
    videos,
    spike,
    window=4,
    baseline_count=8
):
    """
    Select thumbnails around a specific growth event.

    Groups:
    - baseline: typical videos from the local time period
    - before: videos immediately before the spike
    - spike: the spike video
    - after: videos immediately after the spike
    - high_performers: other strong videos from the same local period
    """

    spike_index = None

    for i, video in enumerate(videos):
        if video["id"] == spike["video_id"]:
            spike_index = i
            break

    if spike_index is None:
        return None

    # Videos immediately before the spike
    before = videos[
        max(0, spike_index - window):spike_index
    ]

    # Videos immediately after the spike
    after = videos[
        spike_index + 1:
        min(len(videos), spike_index + window + 1)
    ]

    spike_video = {
        **videos[spike_index],
        "spike_ratio": spike["spike_ratio"]
    }

    # --------------------------------------------------
    # LOCAL COMPARISON WINDOW
    # --------------------------------------------------
    #
    # Use a much larger window around the event so that
    # baseline videos come from the same era of the channel.
    #

    local_window = max(40, window * 10)

    local_start = max(
        0,
        spike_index - local_window
    )

    local_end = min(
        len(videos),
        spike_index + local_window + 1
    )

    local_videos = videos[
        local_start:local_end
    ]

    # Remove the immediate context and spike itself
    excluded_ids = {
        video["id"]
        for video in before + after + [spike_video]
    }

    local_candidates = [
        video
        for video in local_videos
        if video["id"] not in excluded_ids
    ]

    if not local_candidates:
        return {
            "baseline": [],
            "before": before,
            "spike": spike_video,
            "after": after,
            "high_performers": []
        }

    # --------------------------------------------------
    # LOCAL PERFORMANCE BASELINE
    # --------------------------------------------------

    sorted_local = sorted(
        local_candidates,
        key=lambda x: x["views"]
    )

    # Remove the lowest and highest thirds.
    # This gives us videos that represent
    # normal performance rather than extremes.
    third = len(sorted_local) // 3

    if third > 0:
        middle = sorted_local[
            third:len(sorted_local) - third
        ]
    else:
        middle = sorted_local

    baseline = middle[:baseline_count]

    # --------------------------------------------------
    # LOCAL HIGH PERFORMERS
    # --------------------------------------------------

    high_performers = sorted(
        local_candidates,
        key=lambda x: x["views"],
        reverse=True
    )[:5]

    return {
        "baseline": baseline,
        "before": before,
        "spike": spike_video,
        "after": after,
        "high_performers": high_performers
    }