import statistics


def _median(values):
    values = [
        value
        for value in values
        if value is not None
    ]

    if not values:
        return 0

    return statistics.median(values)


def calculate_period_baselines(
    videos,
    period="year"
):
    buckets = {}

    for video in videos:

        date = video["published_at"]

        if period == "year":
            key = date.year

        elif period == "quarter":
            key = (
                date.year,
                ((date.month - 1) // 3) + 1
            )

        elif period == "month":
            key = (
                date.year,
                date.month
            )

        else:
            raise ValueError(
                f"Unsupported period: {period}"
            )

        buckets.setdefault(
            key,
            []
        ).append(
            video["views"]
        )

    results = []

    for key, views in sorted(
        buckets.items()
    ):

        results.append({
            "period": key,
            "video_count": len(views),
            "median_views": round(
                _median(views)
            ),
            "mean_views": round(
                statistics.mean(views)
            ),
        })

    return results


def add_period_growth(results):

    previous = None

    for row in results:

        if (
            previous
            and previous["median_views"] > 0
        ):

            row["median_change_ratio"] = round(
                row["median_views"]
                / previous["median_views"],
                3
            )

        else:

            row["median_change_ratio"] = None

        previous = row

    return results