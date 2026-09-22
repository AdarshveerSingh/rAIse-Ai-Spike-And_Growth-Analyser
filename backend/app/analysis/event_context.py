from app.analysis.audience_timing import detect_peak_interaction_year
from app.analysis.correlation import correlate_audience_period
from app.analysis.related import find_related_videos


def build_event_context(
    event,
    videos,
    spikes,
    period_spike_analysis,
    channel_growth,
    comments=None
):
    context = {
        "target_video": {
            "video_id": event["video_id"],
            "title": event["title"],
            "published_at": event["published_at"],
            "classification": event["event_type"],
            "spike_ratio": event["spike_ratio"],
            "spike_views": event["spike_views"]
        },
        "audience_signal": None,
        "channel_signal": None,
        "related_videos": [],
        "period_spikes": []
    }

    # --------------------------------------------------
    # AUDIENCE COMMENT SIGNAL
    # --------------------------------------------------

    interaction_peak = None

    if comments:
        interaction_peak = detect_peak_interaction_year(
            comments,
            sample_size=100
        )

    context["audience_signal"] = interaction_peak

    # --------------------------------------------------
    # CHANNEL CORRELATION
    # --------------------------------------------------

    if interaction_peak:
        channel_signal = correlate_audience_period(
            interaction_peak,
            period_spike_analysis,
            channel_growth
        )

        context["channel_signal"] = channel_signal

    # --------------------------------------------------
    # RELATED VIDEOS
    # --------------------------------------------------

    target_video = next(
        (
            video
            for video in videos
            if video["id"] == event["video_id"]
        ),
        None
    )

    if target_video:
        related = find_related_videos(
            target_video,
            videos,
            threshold=0.15
        )

        context["related_videos"] = related[:20]

    # --------------------------------------------------
    # SPIKES DURING AUDIENCE PEAK PERIOD
    # --------------------------------------------------

    if interaction_peak:
        peak_year = interaction_peak["peak_year"]

        context["period_spikes"] = [
            row
            for row in period_spike_analysis
            if row["period"] == peak_year
        ]

    return context