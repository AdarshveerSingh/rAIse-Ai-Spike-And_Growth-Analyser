import statistics


def period_key(
    video,
    period="year"
):

    date = video["published_at"]

    if period == "year":
        return date.year

    if period == "quarter":
        return (
            date.year,
            ((date.month - 1) // 3) + 1
        )

    if period == "month":
        return (
            date.year,
            date.month
        )

    raise ValueError(
        f"Unsupported period: {period}"
    )


def analyze_period_spikes(
    videos,
    spikes,
    period="year"
):

    spike_by_id = {
        spike["video_id"]: spike
        for spike in spikes
    }

    periods = {}

    for video in videos:

        key = period_key(
            video,
            period
        )

        if key not in periods:

            periods[key] = {
                "videos": [],
                "spikes": []
            }

        periods[key]["videos"].append(
            video
        )

        if video["id"] in spike_by_id:

            periods[key]["spikes"].append(
                spike_by_id[video["id"]]
            )

    results = []

    for key, data in sorted(
        periods.items()
    ):

        views = [
            video["views"]
            for video in data["videos"]
        ]

        spike_count = len(
            data["spikes"]
        )

        results.append({
            "period": key,
            "video_count": len(views),

            "spike_count": spike_count,

            "spike_rate": round(
                spike_count / len(views),
                4
            ) if views else 0,

            "median_views": round(
                statistics.median(views)
            ) if views else 0,

            "spike_titles": [
                spike["title"]
                for spike in data["spikes"][:10]
            ]
        })

    return results


def correlate_audience_period(
    interaction_peak,
    period_analysis,
    channel_growth=None
):

    if not interaction_peak:
        return None

    target_period = (
        interaction_peak["peak_year"]
    )

    matching = None

    for period in period_analysis:

        if period["period"] == target_period:

            matching = period
            break

    growth_matching = None

    if channel_growth:

        for period in channel_growth:

            if period["period"] == target_period:

                growth_matching = period
                break

    if matching is None:

        return {
            "interaction_peak_year": target_period,
            "channel_period_found": False
        }

    result = {
        "interaction_peak_year":
            target_period,

        "channel_period_found":
            True,

        "channel_video_count":
            matching["video_count"],

        "channel_spike_count":
            matching["spike_count"],

        "channel_spike_rate":
            matching["spike_rate"],

        "channel_median_views":
            matching["median_views"],

        "related_spike_titles":
            matching["spike_titles"]
    }

    if growth_matching:

        result["channel_median_views"] = (
            growth_matching["median_views"]
        )

        result["channel_video_count"] = (
            growth_matching["video_count"]
        )

        result["channel_median_change_ratio"] = (
            growth_matching[
                "median_change_ratio"
            ]
        )

    return result