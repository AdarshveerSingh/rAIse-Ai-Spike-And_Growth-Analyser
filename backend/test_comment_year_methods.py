import json
import os
from collections import Counter
from datetime import datetime
from pathlib import Path

import requests
from dotenv import load_dotenv


# ============================================================
# CONFIG
# ============================================================

load_dotenv()

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

VIDEO_ID = "OzItHn9GSRE"
VIDEO_TITLE = "Drunk Minecraft #1 | A NEW HOPE"

MAX_RESULTS_PER_REQUEST = 100

# Top comments retrieved from YouTube relevance ranking
TOP_COMMENT_COUNT = 100

# Number of chronological samples to compare.
# These are positions through the complete comment stream.
CHRONOLOGICAL_SAMPLE_COUNT = 100

BASE_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

CACHE_DIR = (
    Path(__file__).resolve().parent
    / "cache"
    / "comments"
    / VIDEO_ID
)

ALL_COMMENTS_CACHE = CACHE_DIR / "all_comments.json"
TOP_COMMENTS_CACHE = CACHE_DIR / "top_comments.json"
COMPARISON_CACHE = CACHE_DIR / "comparison.json"


# ============================================================
# HELPERS
# ============================================================

def clean_text(text):
    return " ".join(text.split()).strip()


def parse_comment(item):
    """
    Extract only top-level comment information.

    Replies are intentionally ignored.
    """

    snippet = item["snippet"]["topLevelComment"]["snippet"]

    return {
        "id": item["id"],
        "text": clean_text(
            snippet.get("textDisplay", "")
        ),
        "like_count": int(
            snippet.get("likeCount", 0)
        ),
        "published_at": snippet.get(
            "publishedAt"
        ),
        "updated_at": snippet.get(
            "updatedAt"
        ),
    }


def get_comment_year(comment):
    published_at = comment.get("published_at")

    if not published_at:
        return None

    try:
        return datetime.fromisoformat(
            published_at.replace("Z", "+00:00")
        ).year
    except ValueError:
        return None


# ============================================================
# YOUTUBE API
# ============================================================

def fetch_comment_page(video_id, page_token=None, order="time"):
    """
    Fetch one page of top-level comments.

    One API request = up to 100 comment threads.
    """

    if not YOUTUBE_API_KEY:
        raise ValueError(
            "YOUTUBE_API_KEY is not set in .env"
        )

    params = {
        "part": "snippet",
        "videoId": video_id,
        "maxResults": MAX_RESULTS_PER_REQUEST,
        "order": order,
        "textFormat": "plainText",
        "key": YOUTUBE_API_KEY,
    }

    if page_token:
        params["pageToken"] = page_token

    response = requests.get(
        BASE_URL,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# ALL COMMENTS
# ============================================================

def fetch_all_comments(video_id):
    """
    Fetch every available top-level comment.

    ONLY used for this experiment.

    Production code should NOT do this.
    """

    if ALL_COMMENTS_CACHE.exists():
        print(
            f"\nUsing cached comments:"
            f"\n{ALL_COMMENTS_CACHE}"
        )

        with open(
            ALL_COMMENTS_CACHE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    print("\nFetching ALL comments...")
    print("This is only for the testing experiment.")
    print()

    comments = []
    page_token = None
    page_number = 0

    while True:

        page_number += 1

        print(
            f"Fetching page {page_number}..."
        )

        data = fetch_comment_page(
            video_id,
            page_token=page_token,
            order="time"
        )

        items = data.get("items", [])

        for item in items:
            comments.append(
                parse_comment(item)
            )

        print(
            f"  Retrieved this page: {len(items)}"
        )
        print(
            f"  Total comments: {len(comments)}"
        )

        page_token = data.get(
            "nextPageToken"
        )

        if not page_token:
            break

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        ALL_COMMENTS_CACHE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            comments,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"\nCached {len(comments)} comments:"
        f"\n{ALL_COMMENTS_CACHE}"
    )

    return comments


# ============================================================
# TOP / RELEVANCE COMMENTS
# ============================================================

def fetch_top_comments(video_id):
    """
    Fetch YouTube's relevance-ranked comments.

    Only the first 100 are needed for this experiment.
    """

    if TOP_COMMENTS_CACHE.exists():
        print(
            f"\nUsing cached top comments:"
            f"\n{TOP_COMMENTS_CACHE}"
        )

        with open(
            TOP_COMMENTS_CACHE,
            "r",
            encoding="utf-8"
        ) as f:
            return json.load(f)

    print(
        "\nFetching top/relevance comments..."
    )

    data = fetch_comment_page(
        video_id,
        order="relevance"
    )

    comments = [
        parse_comment(item)
        for item in data.get("items", [])
    ]

    comments = comments[:TOP_COMMENT_COUNT]

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        TOP_COMMENTS_CACHE,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            comments,
            f,
            indent=2,
            ensure_ascii=False
        )

    print(
        f"Cached {len(comments)} top comments:"
        f"\n{TOP_COMMENTS_CACHE}"
    )

    return comments


# ============================================================
# YEAR ANALYSIS
# ============================================================

def calculate_year_distribution(comments):
    """
    Count comments by publication year.
    """

    counts = Counter()

    for comment in comments:

        year = get_comment_year(comment)

        if year is not None:
            counts[str(year)] += 1

    return dict(
        sorted(counts.items())
    )


def calculate_like_distribution(comments):
    """
    Calculate total comment likes by year.
    """

    likes = Counter()

    for comment in comments:

        year = get_comment_year(comment)

        if year is not None:
            likes[str(year)] += comment.get(
                "like_count",
                0
            )

    return dict(
        sorted(likes.items())
    )


def get_dominant_year(year_distribution):
    """
    Return the year with the most comments.

    Returns None if there is no data.
    """

    if not year_distribution:
        return None

    return max(
        year_distribution,
        key=year_distribution.get
    )


def calculate_share(
    year_distribution,
    year
):
    if not year:
        return 0

    total = sum(
        year_distribution.values()
    )

    if total == 0:
        return 0

    return round(
        year_distribution.get(
            year,
            0
        ) / total,
        4
    )


# ============================================================
# CHRONOLOGICAL SAMPLING
# ============================================================

def create_chronological_samples(
    all_comments,
    sample_count=100
):
    """
    Select evenly distributed comments from the
    complete chronological comment stream.

    This simulates the production strategy without
    using the complete dataset as the estimate.

    Example:

        20,000 comments
        100 samples

        positions roughly:
        0
        200
        400
        ...
        19,800
    """

    if not all_comments:
        return []

    sample_count = min(
        sample_count,
        len(all_comments)
    )

    if sample_count == 1:
        return [all_comments[0]]

    samples = []

    for i in range(sample_count):

        position = round(
            i * (
                (len(all_comments) - 1)
                / (sample_count - 1)
            )
        )

        samples.append(
            all_comments[position]
        )

    return samples


# ============================================================
# CHRONOLOGICAL WINDOW SAMPLING
# ============================================================

def create_chronological_window_samples(
    all_comments,
    window_size=100
):
    """
    Divide the complete chronological comment stream
    into equally sized windows.

    This is useful for seeing how the comment stream
    changes over time.

    Example:

        20,000 comments
        window_size=100

        Window 1 → comments 1-100
        Window 2 → comments 101-200
        ...
    """

    windows = []

    for start in range(
        0,
        len(all_comments),
        window_size
    ):

        window = all_comments[
            start:start + window_size
        ]

        if not window:
            continue

        years = calculate_year_distribution(
            window
        )

        dominant_year = get_dominant_year(
            years
        )

        windows.append({
            "start_position": start + 1,
            "end_position": (
                start + len(window)
            ),
            "size": len(window),
            "dominant_year": dominant_year,
            "year_distribution": years
        })

    return windows


# ============================================================
# COMPARISON
# ============================================================

def compare_methods(
    all_comments,
    top_comments
):

    # --------------------------------------------------------
    # GROUND TRUTH
    # --------------------------------------------------------

    ground_truth_years = (
        calculate_year_distribution(
            all_comments
        )
    )

    ground_truth_year = (
        get_dominant_year(
            ground_truth_years
        )
    )

    ground_truth_share = calculate_share(
        ground_truth_years,
        ground_truth_year
    )

    # --------------------------------------------------------
    # TOP COMMENTS
    # --------------------------------------------------------

    top_years = (
        calculate_year_distribution(
            top_comments
        )
    )

    top_year = get_dominant_year(
        top_years
    )

    top_share = calculate_share(
        top_years,
        top_year
    )

    # --------------------------------------------------------
    # CHRONOLOGICAL SAMPLE
    # --------------------------------------------------------

    chronological_samples = (
        create_chronological_samples(
            all_comments,
            CHRONOLOGICAL_SAMPLE_COUNT
        )
    )

    chronological_years = (
        calculate_year_distribution(
            chronological_samples
        )
    )

    chronological_year = (
        get_dominant_year(
            chronological_years
        )
    )

    chronological_share = calculate_share(
        chronological_years,
        chronological_year
    )

    # --------------------------------------------------------
    # WINDOW ANALYSIS
    # --------------------------------------------------------

    windows = (
        create_chronological_window_samples(
            all_comments,
            window_size=100
        )
    )

    # --------------------------------------------------------
    # RESULT
    # --------------------------------------------------------

    return {
        "video": {
            "id": VIDEO_ID,
            "title": VIDEO_TITLE
        },

        "ground_truth": {
            "total_comments": len(
                all_comments
            ),
            "year_distribution": (
                ground_truth_years
            ),
            "dominant_year": (
                ground_truth_year
            ),
            "dominant_year_share": (
                ground_truth_share
            )
        },

        "top_comments_method": {
            "sample_size": len(
                top_comments
            ),
            "year_distribution": top_years,
            "dominant_year": top_year,
            "dominant_year_share": top_share,
            "matches_ground_truth": (
                top_year == ground_truth_year
            )
        },

        "chronological_sample_method": {
            "sample_size": len(
                chronological_samples
            ),
            "year_distribution": (
                chronological_years
            ),
            "dominant_year": (
                chronological_year
            ),
            "dominant_year_share": (
                chronological_share
            ),
            "matches_ground_truth": (
                chronological_year
                == ground_truth_year
            )
        },

        "chronological_windows": windows
    }


# ============================================================
# PRINT RESULTS
# ============================================================

def print_distribution(
    distribution,
    dominant_year=None
):

    for year, count in distribution.items():

        marker = ""

        if year == dominant_year:
            marker = "  <-- DOMINANT"

        print(
            f"  {year}: {count}{marker}"
        )


def print_results(result):

    print()
    print("=" * 70)
    print("COMMENT YEAR ANALYSIS TEST")
    print("=" * 70)

    print(
        f"\nVideo: {result['video']['title']}"
    )

    print(
        f"ID: {result['video']['id']}"
    )

    # --------------------------------------------------------
    # GROUND TRUTH
    # --------------------------------------------------------

    ground = result["ground_truth"]

    print()
    print("GROUND TRUTH — ALL COMMENTS")
    print("-" * 40)

    print(
        f"Total comments: "
        f"{ground['total_comments']}"
    )

    print()

    print_distribution(
        ground["year_distribution"],
        ground["dominant_year"]
    )

    print()

    print(
        f"Dominant year: "
        f"{ground['dominant_year']}"
    )

    print(
        f"Dominant share: "
        f"{ground['dominant_year_share']:.2%}"
    )

    # --------------------------------------------------------
    # TOP COMMENTS
    # --------------------------------------------------------

    top = result["top_comments_method"]

    print()
    print("METHOD 1 — TOP / RELEVANCE COMMENTS")
    print("-" * 40)

    print(
        f"Sample size: "
        f"{top['sample_size']}"
    )

    print()

    print_distribution(
        top["year_distribution"],
        top["dominant_year"]
    )

    print()

    print(
        f"Dominant year: "
        f"{top['dominant_year']}"
    )

    print(
        f"Dominant share: "
        f"{top['dominant_year_share']:.2%}"
    )

    print(
        f"Matches ground truth: "
        f"{'YES' if top['matches_ground_truth'] else 'NO'}"
    )

    # --------------------------------------------------------
    # CHRONOLOGICAL SAMPLE
    # --------------------------------------------------------

    chrono = result[
        "chronological_sample_method"
    ]

    print()
    print("METHOD 2 — CHRONOLOGICAL SAMPLE")
    print("-" * 40)

    print(
        f"Sample size: "
        f"{chrono['sample_size']}"
    )

    print()

    print_distribution(
        chrono["year_distribution"],
        chrono["dominant_year"]
    )

    print()

    print(
        f"Dominant year: "
        f"{chrono['dominant_year']}"
    )

    print(
        f"Dominant share: "
        f"{chrono['dominant_year_share']:.2%}"
    )

    print(
        f"Matches ground truth: "
        f"{'YES' if chrono['matches_ground_truth'] else 'NO'}"
    )

    # --------------------------------------------------------
    # FINAL
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("COMPARISON")
    print("=" * 70)

    print(
        f"\nGround truth:       "
        f"{ground['dominant_year']}"
    )

    print(
        f"Top comments:       "
        f"{top['dominant_year']} "
        f"{'✓' if top['matches_ground_truth'] else '✗'}"
    )

    print(
        f"Chronological:      "
        f"{chrono['dominant_year']} "
        f"{'✓' if chrono['matches_ground_truth'] else '✗'}"
    )

    print()

    print(
        f"Full comparison saved to:\n"
        f"{COMPARISON_CACHE}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print(
        "\nStarting comment analysis experiment..."
    )

    # --------------------------------------------------------
    # 1. ALL COMMENTS
    # --------------------------------------------------------

    all_comments = fetch_all_comments(
        VIDEO_ID
    )

    # --------------------------------------------------------
    # 2. TOP COMMENTS
    # --------------------------------------------------------

    top_comments = fetch_top_comments(
        VIDEO_ID
    )

    # --------------------------------------------------------
    # 3. COMPARE
    # --------------------------------------------------------

    result = compare_methods(
        all_comments,
        top_comments
    )

    # --------------------------------------------------------
    # 4. CACHE RESULT
    # --------------------------------------------------------

    CACHE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        COMPARISON_CACHE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            result,
            f,
            indent=2,
            ensure_ascii=False
        )

    # --------------------------------------------------------
    # 5. PRINT
    # --------------------------------------------------------

    print_results(result)


if __name__ == "__main__":
    main()