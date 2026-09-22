import math
import statistics


def median(values):
    values = [v for v in values if v is not None]

    if not values:
        return 0

    return statistics.median(values)


def mad(values):
    """
    Median Absolute Deviation.
    More robust than standard deviation when the channel contains
    viral outliers.
    """
    values = [v for v in values if v is not None]

    if not values:
        return 0

    m = statistics.median(values)

    deviations = [abs(v - m) for v in values]

    return statistics.median(deviations)


def rolling_baseline(
    videos,
    window=10,
):
    """
    Calculate a local rolling baseline using previous uploads only.

    Using previous uploads rather than future uploads prevents a later
    viral period from contaminating the baseline of an earlier video.
    """

    result = []

    log_views = [
        math.log1p(max(0, video["views"]))
        for video in videos
    ]

    for i, video in enumerate(videos):

        start = max(0, i - window)

        previous = videos[start:i]
        previous_logs = log_views[start:i]

        if len(previous) < 3:
            baseline = None
            log_baseline = None
            log_mad = None
        else:
            baseline = median(
                [video["views"] for video in previous]
            )

            log_baseline = median(previous_logs)
            log_mad = mad(previous_logs)

        current_views = video["views"]
        current_log = math.log1p(max(0, current_views))

        if baseline and baseline > 0:
            spike_ratio = current_views / baseline
        else:
            spike_ratio = None

        if log_baseline is not None and log_mad is not None:

            scale = 1.4826 * log_mad

            if scale > 0:
                robust_z = (
                    current_log - log_baseline
                ) / scale
            else:
                robust_z = 0

        else:
            robust_z = None

        result.append({
            **video,

            "rolling_window": len(previous),

            "rolling_baseline_views": (
                round(baseline)
                if baseline is not None
                else None
            ),

            "rolling_spike_ratio": (
                round(spike_ratio, 3)
                if spike_ratio is not None
                else None
            ),

            "rolling_log_median": (
                round(log_baseline, 4)
                if log_baseline is not None
                else None
            ),

            "rolling_log_mad": (
                round(log_mad, 4)
                if log_mad is not None
                else None
            ),

            "robust_z": (
                round(robust_z, 3)
                if robust_z is not None
                else None
            ),
        })

    return result