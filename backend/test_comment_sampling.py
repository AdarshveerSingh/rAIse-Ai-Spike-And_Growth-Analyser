import json
import math
from pathlib import Path
from collections import Counter


VIDEO_ID = "OzItHn9GSRE"

CACHE_DIR = (
    Path(__file__).resolve().parent
    / "cache"
    / "comments"
    / VIDEO_ID
)

ALL_COMMENTS_CACHE = CACHE_DIR / "all_comments.json"
RESULT_CACHE = CACHE_DIR / "sampling_test.json"

SAMPLE_SIZES = [
    50,
    100,
    250,
    500,
    1000,
    2000,
    5000,
    10000,
]


# ============================================================
# LOAD CACHE
# ============================================================

def load_comments():
    if not ALL_COMMENTS_CACHE.exists():
        raise FileNotFoundError(
            f"Could not find:\n{ALL_COMMENTS_CACHE}"
        )

    with open(
        ALL_COMMENTS_CACHE,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


# ============================================================
# YEAR
# ============================================================

def get_year(comment):
    timestamp = comment.get("published_at")

    if not timestamp:
        return None

    return timestamp[:4]


def year_distribution(comments):
    counts = Counter()

    for comment in comments:
        year = get_year(comment)

        if year:
            counts[year] += 1

    return dict(sorted(counts.items()))


def dominant_year(distribution):
    if not distribution:
        return None

    return max(
        distribution,
        key=distribution.get
    )


# ============================================================
# EVEN CHRONOLOGICAL SAMPLING
# ============================================================

def sample_evenly(comments, sample_size):
    """
    Select evenly spaced comments from the entire
    chronological comment stream.

    The input comments are already ordered by time.
    """

    if sample_size >= len(comments):
        return comments.copy()

    if sample_size <= 0:
        return []

    if sample_size == 1:
        return [comments[0]]

    samples = []

    for i in range(sample_size):

        position = round(
            i * (
                (len(comments) - 1)
                / (sample_size - 1)
            )
        )

        samples.append(
            comments[position]
        )

    return samples


# ============================================================
# DISTRIBUTION ERROR
# ============================================================

def distribution_error(
    ground_truth,
    sample
):
    """
    Mean absolute error between the percentage
    distribution of the sample and the true distribution.

    This is expressed as a percentage-point average.
    """

    years = set(
        ground_truth.keys()
    ) | set(
        sample.keys()
    )

    total_ground = sum(
        ground_truth.values()
    )

    total_sample = sum(
        sample.values()
    )

    if total_ground == 0 or total_sample == 0:
        return None

    total_error = 0

    for year in years:

        ground_share = (
            ground_truth.get(year, 0)
            / total_ground
        )

        sample_share = (
            sample.get(year, 0)
            / total_sample
        )

        total_error += abs(
            ground_share - sample_share
        )

    # Divide by number of years and convert
    # to percentage points.
    return (
        total_error
        / len(years)
        * 100
    )


# ============================================================
# DOMINANT YEAR SHARE ERROR
# ============================================================

def dominant_share_error(
    ground_distribution,
    sample_distribution
):
    ground_year = dominant_year(
        ground_distribution
    )

    if not ground_year:
        return None

    ground_total = sum(
        ground_distribution.values()
    )

    sample_total = sum(
        sample_distribution.values()
    )

    ground_share = (
        ground_distribution.get(
            ground_year,
            0
        ) / ground_total
    )

    sample_share = (
        sample_distribution.get(
            ground_year,
            0
        ) / sample_total
    )

    return round(
        abs(ground_share - sample_share)
        * 100,
        3
    )


# ============================================================
# TOP 3 YEAR OVERLAP
# ============================================================

def top_years(distribution, n=3):
    return [
        year
        for year, _ in sorted(
            distribution.items(),
            key=lambda x: x[1],
            reverse=True
        )[:n]
    ]


def top_three_overlap(
    ground_distribution,
    sample_distribution
):
    ground_top = set(
        top_years(ground_distribution)
    )

    sample_top = set(
        top_years(sample_distribution)
    )

    return len(
        ground_top & sample_top
    )


# ============================================================
# RUN TEST
# ============================================================

def run_test():

    comments = load_comments()

    print("=" * 75)
    print("CHRONOLOGICAL COMMENT SAMPLING TEST")
    print("=" * 75)

    print(
        f"\nTotal cached comments: "
        f"{len(comments)}"
    )

    # --------------------------------------------------------
    # Ground truth
    # --------------------------------------------------------

    ground_distribution = (
        year_distribution(comments)
    )

    ground_year = dominant_year(
        ground_distribution
    )

    ground_total = sum(
        ground_distribution.values()
    )

    ground_share = (
        ground_distribution[ground_year]
        / ground_total
    )

    print()
    print("GROUND TRUTH")
    print("-" * 75)

    print(
        f"Dominant year: {ground_year}"
    )

    print(
        f"Dominant count: "
        f"{ground_distribution[ground_year]}"
    )

    print(
        f"Dominant share: "
        f"{ground_share:.2%}"
    )

    print()
    print("Year distribution:")

    for year, count in ground_distribution.items():

        share = count / ground_total

        marker = (
            " <-- DOMINANT"
            if year == ground_year
            else ""
        )

        print(
            f"  {year}: "
            f"{count:5d} "
            f"({share:6.2%})"
            f"{marker}"
        )

    # --------------------------------------------------------
    # Test each sample size
    # --------------------------------------------------------

    results = []

    print()
    print("=" * 75)
    print("SAMPLE SIZE TEST")
    print("=" * 75)

    print()

    header = (
        f"{'Sample':>8} | "
        f"{'Peak':>6} | "
        f"{'Share':>8} | "
        f"{'Match':>6} | "
        f"{'Dist Err':>9} | "
        f"{'Peak Err':>9} | "
        f"{'Top-3':>5}"
    )

    print(header)
    print("-" * len(header))

    for sample_size in SAMPLE_SIZES:

        sample = sample_evenly(
            comments,
            sample_size
        )

        sample_distribution = (
            year_distribution(sample)
        )

        sample_year = dominant_year(
            sample_distribution
        )

        sample_total = sum(
            sample_distribution.values()
        )

        sample_share = (
            sample_distribution[
                sample_year
            ] / sample_total
            if sample_year
            else 0
        )

        dist_error = distribution_error(
            ground_distribution,
            sample_distribution
        )

        peak_error = dominant_share_error(
            ground_distribution,
            sample_distribution
        )

        top_overlap = top_three_overlap(
            ground_distribution,
            sample_distribution
        )

        matches = (
            sample_year == ground_year
        )

        print(
            f"{sample_size:8d} | "
            f"{sample_year or '-':>6} | "
            f"{sample_share:7.2%} | "
            f"{'YES' if matches else 'NO':>6} | "
            f"{dist_error:8.3f} | "
            f"{peak_error:8.3f} | "
            f"{top_overlap:5d}"
        )

        results.append({
            "sample_size": sample_size,
            "dominant_year": sample_year,
            "dominant_year_share": round(
                sample_share,
                6
            ),
            "matches_ground_truth": matches,
            "distribution_error_percentage_points": (
                round(dist_error, 4)
                if dist_error is not None
                else None
            ),
            "ground_truth_peak_share_error_percentage_points": (
                peak_error
            ),
            "top_3_year_overlap": top_overlap,
            "year_distribution": sample_distribution
        })

    # --------------------------------------------------------
    # Stability test
    # --------------------------------------------------------

    print()
    print("=" * 75)
    print("STABILITY")
    print("=" * 75)

    matching_sizes = [
        r["sample_size"]
        for r in results
        if r["matches_ground_truth"]
    ]

    if matching_sizes:

        print(
            "\nSample sizes matching ground truth:"
        )

        print(
            ", ".join(
                str(x)
                for x in matching_sizes
            )
        )

    else:

        print(
            "\nNo tested sample size matched "
            "the ground-truth dominant year."
        )

    # --------------------------------------------------------
    # Find smallest matching sample
    # --------------------------------------------------------

    smallest_reliable = None

    for result in results:

        if result["matches_ground_truth"]:

            smallest_reliable = (
                result["sample_size"]
            )

            break

    print()

    if smallest_reliable:

        print(
            f"Smallest tested sample matching "
            f"ground truth: "
            f"{smallest_reliable}"
        )

    else:

        print(
            "No reliable sample size found "
            "in the tested range."
        )

    # --------------------------------------------------------
    # Save
    # --------------------------------------------------------

    output = {
        "video_id": VIDEO_ID,
        "total_comments": len(comments),

        "ground_truth": {
            "dominant_year": ground_year,
            "dominant_year_share": round(
                ground_share,
                6
            ),
            "year_distribution": (
                ground_distribution
            )
        },

        "tests": results,

        "smallest_tested_sample_matching_ground_truth": (
            smallest_reliable
        )
    }

    with open(
        RESULT_CACHE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            output,
            f,
            indent=2,
            ensure_ascii=False
        )

    print()
    print(
        f"Results saved to:\n{RESULT_CACHE}"
    )


if __name__ == "__main__":
    run_test()

    ## ADD CODE FROM LATEST GPT RESPONSE