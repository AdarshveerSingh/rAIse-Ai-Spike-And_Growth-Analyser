import json
import os
import re
from pathlib import Path

import requests
from dotenv import load_dotenv


load_dotenv()


YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")

BASE_URL = "https://www.googleapis.com/youtube/v3/commentThreads"

MAX_RESULTS_PER_REQUEST = 100

CACHE_DIR = (
    Path(__file__).resolve().parents[2]
    / "cache"
    / "comments"
)


# ============================================================
# TEXT CLEANING
# ============================================================

def _clean_text(text):
    if not text:
        return ""

    text = re.sub(r"\s+", " ", text)

    return text.strip()


# ============================================================
# COMMENT PARSING
# ============================================================

def _parse_comment(item):
    snippet = item["snippet"]["topLevelComment"]["snippet"]

    return {
        "id": item["id"],
        "text": _clean_text(
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
        "author": snippet.get(
            "authorDisplayName",
            ""
        ),
        "reply_count": int(
            item["snippet"].get(
                "totalReplyCount",
                0
            )
        ),
    }


# ============================================================
# API
# ============================================================

def fetch_comment_page(
    video_id,
    page_token=None,
    order="time"
):
    """
    Fetch one page of YouTube comments.

    order="time" gives us chronological API ordering,
    which is useful when building the cached history.
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
        timeout=30,
    )

    response.raise_for_status()

    return response.json()


# ============================================================
# CACHE HELPERS
# ============================================================

def _get_cache_dir(video_id):
    return CACHE_DIR / video_id


def _get_cache_file(video_id):
    return _get_cache_dir(video_id) / "all_comments.json"


def _normalise_cached_comment(comment):
    """
    Older cached comments may not contain fields that were added
    later. Add safe defaults for backwards compatibility.
    """

    comment.setdefault("like_count", 0)
    comment.setdefault("reply_count", 0)
    comment.setdefault("updated_at", None)
    comment.setdefault("author", "")

    if "text" not in comment:
        comment["text"] = ""

    return comment


# ============================================================
# FULL COMMENT HISTORY
# ============================================================

def fetch_all_comments(
    video_id,
    use_cache=True
):
    """
    Fetch the complete top-level comment history.

    For the MVP this is intentionally cached.

    IMPORTANT:
    The complete history is NOT sent to the AI model.

    Downstream analysis takes a small sample from this cached
    history.
    """

    cache_file = _get_cache_file(video_id)

    # --------------------------------------------------------
    # CACHE HIT
    # --------------------------------------------------------

    if use_cache and cache_file.exists():

        print(
            f"YouTube comment cache hit: {video_id}"
        )

        with open(
            cache_file,
            "r",
            encoding="utf-8"
        ) as f:

            comments = json.load(f)

        comments = [
            _normalise_cached_comment(comment)
            for comment in comments
        ]

        print(
            f"Comments retrieved: {len(comments)}"
        )

        return comments

    # --------------------------------------------------------
    # API FETCH
    # --------------------------------------------------------

    print(
        f"Fetching comments from YouTube: {video_id}"
    )

    comments = []

    page_token = None

    while True:

        data = fetch_comment_page(
            video_id,
            page_token=page_token,
            order="time",
        )

        items = data.get(
            "items",
            []
        )

        if not items:
            break

        for item in items:

            try:
                comments.append(
                    _parse_comment(item)
                )

            except (
                KeyError,
                TypeError,
                ValueError
            ):
                continue

        page_token = data.get(
            "nextPageToken"
        )

        if not page_token:
            break

    # --------------------------------------------------------
    # CACHE
    # --------------------------------------------------------

    cache_file.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    with open(
        cache_file,
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
        f"Comments fetched and cached: {len(comments)}"
    )

    return comments

# ============================================================
# RELEVANT COMMENT HISTORY
# ============================================================

def fetch_relevant_comments(
    video_id,
    max_comments=25000,
):
    """
    Fetch up to max_comments top-level comments using
    YouTube's relevance ordering.

    Used for high-engagement videos.
    """

    if not YOUTUBE_API_KEY:
        raise ValueError(
            "YOUTUBE_API_KEY is not set in .env"
        )

    comments = []
    page_token = None

    print(
        f"Fetching up to {max_comments:,} relevant comments: "
        f"{video_id}"
    )

    while len(comments) < max_comments:

        remaining = max_comments - len(comments)

        page_size = min(
            MAX_RESULTS_PER_REQUEST,
            remaining
        )

        data = fetch_comment_page(
            video_id,
            page_token=page_token,
            order="relevance",
        )

        items = data.get("items", [])

        if not items:
            break

        for item in items:

            try:
                comments.append(
                    _parse_comment(item)
                )
            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            if len(comments) >= max_comments:
                break

        page_token = data.get("nextPageToken")

        if not page_token:
            break

    print(
        f"Relevant comments retrieved: "
        f"{len(comments):,}"
    )

    return comments
# ============================================================
# QUALITATIVE COMMENT SAMPLE
# ============================================================

def fetch_comment_sample(
    video_id,
    relevant_count=50,
    recent_count=50
):
    """
    Build a small qualitative sample.

    MVP implementation:
    uses the cached full history and selects:
      - distributed comments across the history
      - recent comments

    The complete history is never sent to the AI model.
    """

    comments = fetch_all_comments(
        video_id
    )

    if not comments:
        return []

    comments = sorted(
        comments,
        key=lambda x: x.get(
            "published_at",
            ""
        )
    )

    total = len(comments)

    # --------------------------------------------------------
    # DISTRIBUTED SAMPLE
    # --------------------------------------------------------

    relevant_count = min(
        relevant_count,
        total
    )

    distributed = []

    if relevant_count == 1:

        distributed = [
            comments[0]
        ]

    elif relevant_count > 1:

        for i in range(
            relevant_count
        ):

            index = round(
                i
                * (total - 1)
                / (relevant_count - 1)
            )

            distributed.append(
                comments[index]
            )

    # --------------------------------------------------------
    # RECENT SAMPLE
    # --------------------------------------------------------

    recent_count = min(
        recent_count,
        total
    )

    recent = comments[
        -recent_count:
    ]

    # --------------------------------------------------------
    # COMBINE WITHOUT DUPLICATES
    # --------------------------------------------------------

    result = []

    seen = set()

    for comment in distributed + recent:

        comment_id = comment.get(
            "id"
        )

        if comment_id in seen:
            continue

        seen.add(comment_id)

        result.append(comment)

    return result


# ============================================================
# TIMING SAMPLE
# ============================================================

def fetch_comment_timing_sample(
    video_id,
    sample_size=100
):
    """
    MVP audience-timing sampler.

    IMPORTANT:

    This deliberately uses the FULL CACHED COMMENT HISTORY
    and then creates a chronological distributed sample.

    This is the validated method we tested against:

        15,089 comments
              ↓
        100 distributed samples
              ↓
        dominant year = 2013

    We are NOT using the previous API-only implementation
    that fetched only the newest 100 comments.

    A more API-efficient historical sampling strategy will
    be investigated after the MVP.
    """

    comments = fetch_all_comments(
        video_id
    )

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

        index = round(
            i
            * (len(comments) - 1)
            / (sample_size - 1)
        )

        sampled.append(
            comments[index]
        )

    return sampled