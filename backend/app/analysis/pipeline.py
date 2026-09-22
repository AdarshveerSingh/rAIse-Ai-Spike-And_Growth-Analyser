from app.analysis.metrics import prepare_videos
from app.analysis.rolling import rolling_baseline
from app.analysis.spikes import detect_spikes, rank_spikes
from app.analysis.episodes import analyze_growth_event
from app.analysis.channel_growth import (
    calculate_period_baselines,
    add_period_growth,
)
from app.analysis.correlation import (
    analyze_period_spikes,
)
from app.analysis.related import (
    find_related_videos,
)


def run_analysis_pipeline(videos):

    # --------------------------------------------------
    # 1. Basic metrics
    # --------------------------------------------------

    prepared = prepare_videos(videos)

    # --------------------------------------------------
    # 2. Rolling baselines
    # --------------------------------------------------

    enriched = rolling_baseline(
        prepared,
        window=10,
    )

    # --------------------------------------------------
    # 3. Spike detection
    # --------------------------------------------------

    spikes = detect_spikes(
        enriched,
        min_ratio=3.0,
        min_robust_z=2.5,
    )

    ranked_spikes = rank_spikes(
        spikes
    )

    # --------------------------------------------------
    # 4. Growth periods
    # --------------------------------------------------

    yearly_growth = calculate_period_baselines(
        enriched,
        period="year",
    )

    yearly_growth = add_period_growth(
        yearly_growth
    )

    # --------------------------------------------------
    # 5. Channel-wide spike clustering
    # --------------------------------------------------

    yearly_spikes = analyze_period_spikes(
        enriched,
        spikes,
        period="year",
    )

    # --------------------------------------------------
    # 6. Growth events
    # --------------------------------------------------

    events = []

    for spike in spikes:

        event = analyze_growth_event(
            enriched,
            spike,
        )

        if event:
            events.append(event)

    # --------------------------------------------------
    # 7. Key events
    # --------------------------------------------------

    earliest = (
        min(
            events,
            key=lambda x: x["published_at"]
        )
        if events
        else None
    )

    strongest = (
        max(
            events,
            key=lambda x: x["spike_ratio"]
        )
        if events
        else None
    )

    sustained = [
        event
        for event in events
        if event["event_type"]
        == "SUSTAINED_THROUGHOUT"
    ]

    temporary = [
        event
        for event in events
        if event["event_type"]
        == "TEMPORARY"
    ]

    eventual = [
        event
        for event in events
        if event["event_type"]
        == "SUSTAINED_EVENTUAL"
    ]

    one_off = [
        event
        for event in events
        if event["event_type"]
        == "ONE_OFF"
    ]

    return {
        "videos": enriched,

        "spikes": ranked_spikes,

        "events": events,

        "key_events": {
            "earliest": earliest,

            "strongest": strongest,

            "one_off": (
                max(
                    one_off,
                    key=lambda x: x["spike_ratio"]
                )
                if one_off
                else None
            ),

            "temporary": (
                max(
                    temporary,
                    key=lambda x: x["spike_ratio"]
                )
                if temporary
                else None
            ),

            "sustained_throughout": (
                max(
                    sustained,
                    key=lambda x: x["spike_ratio"]
                )
                if sustained
                else None
            ),

            "sustained_eventual": (
                max(
                    eventual,
                    key=lambda x: x["spike_ratio"]
                )
                if eventual
                else None
            ),
        },

        "channel_growth": yearly_growth,

        "period_spike_analysis": yearly_spikes,

        "video_count": len(enriched),

        "spike_count": len(spikes),

        "event_count": len(events),
    }