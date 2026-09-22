import json
from pathlib import Path
from collections import Counter
from datetime import datetime

from app.youtube.comments import fetch_comment_timing_sample
from app.analysis.audience_timing import chronological_sample


VIDEO_ID = "OzItHn9GSRE"

CACHE_FILE = (
    Path(__file__).resolve().parent
    / "cache"
    / "comments"
    / VIDEO_ID
    / "all_comments.json"
)

def get_year(comment):
    published_at = comment.get("published_at")

    if not published_at:
        return None

    return datetime.fromisoformat(
        published_at.replace("Z", "+00:00")
    ).year


def get_distribution(comments):
    counts = Counter()

    for comment in comments:
        year = get_year(comment)

        if year is not None:
            counts[year] += 1

    total = sum(counts.values())

    return {
        year: {
            "count": count,
            "share": round(count / total, 4)
        }
        for year, count in sorted(counts.items())
    }


def get_peak_year(comments):
    distribution = get_distribution(comments)

    if not distribution:
        return None

    return max(
        distribution,
        key=lambda year: distribution[year]["count"]
    )


def print_result(label, comments):

    distribution = get_distribution(comments)
    peak_year = get_peak_year(comments)

    print()
    print("=" * 70)
    print(label)
    print("=" * 70)

    print("Sample size:", len(comments))
    print("Peak year:", peak_year)

    print()
    print("Distribution:")

    for year, data in distribution.items():
        print(
            f"  {year}: "
            f"{data['count']} "
            f"({data['share'] * 100:.2f}%)"
        )


def main():

    # ---------------------------------------------------------
    # A. FULL HISTORY GROUND TRUTH
    # ---------------------------------------------------------

    print("Loading cached full comment history...")

    with open(CACHE_FILE, "r", encoding="utf-8") as f:
        full_comments = json.load(f)

    print("Full comments:", len(full_comments))

    full_peak = get_peak_year(full_comments)

    print("Ground-truth peak year:", full_peak)

    # ---------------------------------------------------------
    # B. PREVIOUSLY VALIDATED CHRONOLOGICAL SAMPLE
    # ---------------------------------------------------------

    validated_sample = chronological_sample(
        full_comments,
        sample_size=100
    )

    print_result(
        "B. VALIDATED 100-COMMENT SAMPLE",
        validated_sample
    )

    validated_peak = get_peak_year(validated_sample)

    # ---------------------------------------------------------
    # C. NEW PRODUCTION SAMPLER
    # ---------------------------------------------------------

    print()
    print("Calling production timing sampler...")

    production_sample = fetch_comment_timing_sample(
        VIDEO_ID,
        sample_size=100
    )

    print_result(
        "C. PRODUCTION TIMING SAMPLER",
        production_sample
    )

    production_peak = get_peak_year(production_sample)

    # ---------------------------------------------------------
    # FINAL COMPARISON
    # ---------------------------------------------------------

    print()
    print("=" * 70)
    print("FINAL COMPARISON")
    print("=" * 70)

    print("Full-history peak:       ", full_peak)
    print("Validated sample peak:   ", validated_peak)
    print("Production sample peak:  ", production_peak)

    print()

    print(
        "Validated sample matches ground truth:",
        validated_peak == full_peak
    )

    print(
        "Production sampler matches ground truth:",
        production_peak == full_peak
    )

    print()

    if production_peak == full_peak:
        print("PASS: Production sampler matches ground truth.")
    else:
        print("FAIL: Production sampler does NOT match ground truth.")


if __name__ == "__main__":
    main()