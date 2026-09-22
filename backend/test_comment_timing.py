from app.youtube.comments import (
    fetch_all_comments
)

from app.analysis.audience_timing import (
    detect_peak_interaction_year
)


VIDEO_ID = "OzItHn9GSRE"


print("=" * 70)
print("FETCHING COMMENT HISTORY")
print("=" * 70)

comments = fetch_all_comments(
    VIDEO_ID
)

print()
print(
    "Total comments:",
    len(comments)
)


print()
print("=" * 70)
print("CHRONOLOGICAL SAMPLE")
print("=" * 70)

result = detect_peak_interaction_year(
    comments,
    sample_size=100
)

print(
    "Sample size:",
    result["sample_size"]
)

print(
    "Available comments:",
    result["total_available_comments"]
)

print(
    "Peak interaction year:",
    result["peak_year"]
)

print(
    "Peak share:",
    result["peak_share"]
)


print()
print("YEAR DISTRIBUTION")
print("-" * 70)

for row in result["distribution"]:

    print(
        row["year"],
        "|",
        row["count"],
        "|",
        row["share"]
    )


print()
print("=" * 70)
print("TEST COMPLETE")
print("=" * 70)