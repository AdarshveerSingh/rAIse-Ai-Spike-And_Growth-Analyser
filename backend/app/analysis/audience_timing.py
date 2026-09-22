from collections import Counter
from datetime import datetime


# ============================================================
# CHRONOLOGICAL DISTRIBUTED SAMPLE
# ============================================================

def chronological_sample(
    comments,
    sample_size=100
):
    """
    Select comments distributed across the entire available
    chronological history.

    Example:

        15,089 comments
              ↓
        sample_size=100
              ↓
        positions spread from oldest → newest
    """

    if not comments:
        return []

    comments = sorted(
        comments,
        key=lambda x: x.get(
            "published_at",
            ""
        )
    )

    sample_size = min(
        sample_size,
        len(comments)
    )

    if sample_size == 1:

        return [
            comments[0]
        ]

    sampled = []

    for i in range(
        sample_size
    ):

        position = round(
            i
            * (len(comments) - 1)
            / (sample_size - 1)
        )

        sampled.append(
            comments[position]
        )

    return sampled


# ============================================================
# COMMENT YEAR
# ============================================================

def get_comment_year(comment):
    published_at = comment.get(
        "published_at"
    )

    if not published_at:
        return None

    try:

        return datetime.fromisoformat(
            published_at.replace(
                "Z",
                "+00:00"
            )
        ).year

    except (
        ValueError,
        TypeError
    ):

        return None


# ============================================================
# YEAR DISTRIBUTION
# ============================================================

def year_distribution(
    comments
):
    """
    Calculate the distribution of sampled comments by year.
    """

    counts = Counter()

    for comment in comments:

        year = get_comment_year(
            comment
        )

        if year is not None:

            counts[year] += 1

    total = sum(
        counts.values()
    )

    result = []

    for year, count in sorted(
        counts.items()
    ):

        result.append(
            {
                "year": year,
                "count": count,
                "share": round(
                    count / total,
                    4
                ) if total else 0,
            }
        )

    return result


# ============================================================
# PEAK INTERACTION YEAR
# ============================================================

def detect_peak_interaction_year(
    comments,
    sample_size=100
):
    """
    Detect the year with the highest concentration of
    comments in the supplied sample.

    IMPORTANT:

    This is an audience-timing signal.

    It does NOT prove that the video became popular because
    of activity in that year.
    """

    if not comments:
        return None

    sampled = chronological_sample(
        comments,
        sample_size=sample_size
    )

    distribution = year_distribution(
        sampled
    )

    if not distribution:
        return None

    peak = max(
        distribution,
        key=lambda x: x["count"]
    )

    return {
        "sample_size": len(
            sampled
        ),
        "total_available_comments": len(
            comments
        ),
        "peak_year": peak["year"],
        "peak_count": peak["count"],
        "peak_share": peak["share"],
        "distribution": distribution,
    }