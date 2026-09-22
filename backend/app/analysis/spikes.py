def detect_spikes(
    videos,
    min_ratio=3.0,
    min_robust_z=2.5,
):
    spikes = []

    for video in videos:

        ratio = video.get("rolling_spike_ratio")
        robust_z = video.get("robust_z")

        if ratio is None:
            continue

        ratio_trigger = ratio >= min_ratio

        z_trigger = (
            robust_z is not None
            and robust_z >= min_robust_z
        )

        if not ratio_trigger and not z_trigger:
            continue

        if ratio_trigger and z_trigger:
            signal = "STRONG"

        elif ratio_trigger:
            signal = "RATIO"

        else:
            signal = "ROBUST_Z"

        spikes.append({
            "video_id": video["id"],
            "title": video["title"],
            "published_at": video["published_at"],
            "views": video["views"],

            "baseline_views": video[
                "rolling_baseline_views"
            ],

            "spike_ratio": video[
                "rolling_spike_ratio"
            ],

            "robust_z": video[
                "robust_z"
            ],

            "signal": signal,

            "engagement_rate": video[
                "engagement_rate"
            ],
        })

    return spikes


def rank_spikes(spikes):

    return sorted(
        spikes,
        key=lambda x: (
            x["robust_z"]
            if x["robust_z"] is not None
            else 0
        ),
        reverse=True,
    )