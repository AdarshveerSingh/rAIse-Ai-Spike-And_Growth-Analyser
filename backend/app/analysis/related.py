import re
from datetime import datetime


# ============================================================
# STOPWORDS
# ============================================================

STOPWORDS = {
    "the",
    "a",
    "an",
    "and",
    "or",
    "of",
    "to",
    "in",
    "on",
    "with",
    "for",
    "my",
    "is",
    "this",
    "that",
    "new",
    "part",
    "episode",
    "ep",
    "full",
    "complete",
    "official",
}


# ============================================================
# TOKENIZATION
# ============================================================

def tokenize(text):
    if not text:
        return set()

    text = text.lower()

    tokens = re.findall(
        r"[a-z0-9]+",
        text
    )

    return {
        token
        for token in tokens
        if token not in STOPWORDS
    }


# ============================================================
# TITLE SIMILARITY
# ============================================================

def title_similarity(
    title_a,
    title_b
):
    tokens_a = tokenize(title_a)
    tokens_b = tokenize(title_b)

    if not tokens_a or not tokens_b:
        return 0.0

    intersection = tokens_a & tokens_b
    union = tokens_a | tokens_b

    if not union:
        return 0.0

    return len(intersection) / len(union)


# ============================================================
# EXTRACT EPISODE NUMBER
# ============================================================

def extract_episode_number(title):

    if not title:
        return None

    patterns = [
        # #1
        r"#\s*(\d+)",

        # Part 1
        r"\bpart\s+(\d+)\b",

        # Episode 1
        r"\bepisode\s+(\d+)\b",

        # Ep 1
        r"\bep\s+(\d+)\b",
    ]

    title_lower = title.lower()

    for pattern in patterns:

        match = re.search(
            pattern,
            title_lower
        )

        if match:

            return int(
                match.group(1)
            )

    return None


# ============================================================
# EXTRACT SERIES IDENTITY
# ============================================================

def extract_series_identity(title):
    """
    Extract the recurring series portion of a title.

    Examples:

        Drunk Minecraft #1 | A NEW HOPE
            -> drunk minecraft

        Drunk Minecraft #42 | TO THE MOON!!
            -> drunk minecraft

        Cry of Fear: Out of It | Part 1 | GOING OUT OF MY HEAD
            -> cry fear out

    The first title section is treated as the primary
    series identifier.
    """

    if not title:
        return ""

    text = title.lower().strip()

    # --------------------------------------------------------
    # Split on title separators FIRST
    # --------------------------------------------------------

    sections = re.split(
        r"\s*\|\s*",
        text
    )

    primary = sections[0]

    # --------------------------------------------------------
    # Remove episode number
    # --------------------------------------------------------

    primary = re.sub(
        r"#\s*\d+",
        " ",
        primary
    )

    primary = re.sub(
        r"\bpart\s+\d+\b",
        " ",
        primary
    )

    primary = re.sub(
        r"\bepisode\s+\d+\b",
        " ",
        primary
    )

    primary = re.sub(
        r"\bep\s+\d+\b",
        " ",
        primary
    )

    # --------------------------------------------------------
    # Remove punctuation
    # --------------------------------------------------------

    primary = re.sub(
        r"[^a-z0-9\s]",
        " ",
        primary
    )

    # --------------------------------------------------------
    # Normalize whitespace
    # --------------------------------------------------------

    primary = re.sub(
        r"\s+",
        " ",
        primary
    ).strip()

    # --------------------------------------------------------
    # Remove stopwords
    # --------------------------------------------------------

    tokens = [
        token
        for token in primary.split()
        if token not in STOPWORDS
    ]

    return " ".join(tokens)


# ============================================================
# SERIES IDENTITY MATCH
# ============================================================

def series_identity_match(
    title_a,
    title_b
):
    """
    Exact recurring-series identity.

    Example:

        Drunk Minecraft #1
        Drunk Minecraft #42

        -> 1.0
    """

    series_a = extract_series_identity(
        title_a
    )

    series_b = extract_series_identity(
        title_b
    )

    if not series_a or not series_b:
        return 0.0

    if series_a == series_b:
        return 1.0

    return 0.0


# ============================================================
# SERIES TOKEN SIMILARITY
# ============================================================

def series_similarity(
    title_a,
    title_b
):
    """
    Softer similarity between extracted series names.
    """

    series_a = set(
        extract_series_identity(
            title_a
        ).split()
    )

    series_b = set(
        extract_series_identity(
            title_b
        ).split()
    )

    if not series_a or not series_b:
        return 0.0

    intersection = series_a & series_b
    union = series_a | series_b

    if not union:
        return 0.0

    return len(
        intersection
    ) / len(
        union
    )


# ============================================================
# NUMBERED SERIES RELATIONSHIP
# ============================================================

def numbered_series_match(
    title_a,
    title_b
):
    """
    Score proximity between episodes in the same series.
    """

    episode_a = extract_episode_number(
        title_a
    )

    episode_b = extract_episode_number(
        title_b
    )

    if (
        episode_a is None
        or episode_b is None
    ):
        return 0.0

    # They must belong to the same explicit series.
    if series_identity_match(
        title_a,
        title_b
    ) != 1.0:

        return 0.0

    difference = abs(
        episode_a - episode_b
    )

    if difference == 0:
        return 1.0

    if difference == 1:
        return 1.0

    if difference <= 5:
        return 0.75

    if difference <= 15:
        return 0.5

    return 0.25


# ============================================================
# TEMPORAL SIMILARITY
# ============================================================

def temporal_similarity(
    date_a,
    date_b,
    max_days=365
):

    if not date_a or not date_b:
        return 0.0

    if isinstance(
        date_a,
        str
    ):

        date_a = datetime.fromisoformat(
            date_a.replace(
                "Z",
                "+00:00"
            )
        )

    if isinstance(
        date_b,
        str
    ):

        date_b = datetime.fromisoformat(
            date_b.replace(
                "Z",
                "+00:00"
            )
        )

    # Handle naive vs aware datetime safely.
    if (
        date_a.tzinfo is not None
        and date_b.tzinfo is None
    ):

        date_b = date_b.replace(
            tzinfo=date_a.tzinfo
        )

    elif (
        date_b.tzinfo is not None
        and date_a.tzinfo is None
    ):

        date_a = date_a.replace(
            tzinfo=date_b.tzinfo
        )

    days = abs(
        (
            date_a - date_b
        ).total_seconds()
    ) / 86400

    if days > max_days:
        return 0.0

    return max(
        0.0,
        1.0 - (
            days / max_days
        )
    )


# ============================================================
# CONTENT TYPE
# ============================================================

def content_type_similarity(
    type_a,
    type_b
):

    if not type_a or not type_b:
        return 0.0

    if type_a == type_b:
        return 1.0

    return 0.0


# ============================================================
# RELATED VIDEO SCORE
# ============================================================

def calculate_related_score(
    target,
    candidate
):

    title_score = title_similarity(
        target.get(
            "title",
            ""
        ),
        candidate.get(
            "title",
            ""
        )
    )

    series_identity_score = (
        series_identity_match(
            target.get(
                "title",
                ""
            ),
            candidate.get(
                "title",
                ""
            )
        )
    )

    series_score = series_similarity(
        target.get(
            "title",
            ""
        ),
        candidate.get(
            "title",
            ""
        )
    )

    numbered_score = numbered_series_match(
        target.get(
            "title",
            ""
        ),
        candidate.get(
            "title",
            ""
        )
    )

    temporal_score = temporal_similarity(
        target.get(
            "published_at"
        ),
        candidate.get(
            "published_at"
        )
    )

    content_score = content_type_similarity(
        target.get(
            "content_type"
        ),
        candidate.get(
            "content_type"
        )
    )

    # ========================================================
    # WEIGHTED SCORE
    # ========================================================

    score = (
        title_score * 0.20
        + series_identity_score * 0.40
        + numbered_score * 0.25
        + temporal_score * 0.10
        + content_score * 0.05
    )

    return {

        "related_score": round(
            score,
            4
        ),

        "title_similarity": round(
            title_score,
            4
        ),

        "series_identity": round(
            series_identity_score,
            4
        ),

        "series_similarity": round(
            series_score,
            4
        ),

        "numbered_series_score": round(
            numbered_score,
            4
        ),

        "temporal_similarity": round(
            temporal_score,
            4
        ),

        "content_type_similarity": round(
            content_score,
            4
        )
    }


# ============================================================
# FIND RELATED VIDEOS
# ============================================================

def find_related_videos(
    target_video,
    videos,
    candidate_ids=None,
    threshold=0.20
):

    candidate_id_set = (
        set(candidate_ids)
        if candidate_ids
        else None
    )

    related = []

    for video in videos:

        if (
            video.get("id")
            == target_video.get("id")
        ):
            continue

        if (
            candidate_id_set is not None
            and video.get("id")
            not in candidate_id_set
        ):
            continue

        scores = calculate_related_score(
            target_video,
            video
        )

        if (
            scores["related_score"]
            < threshold
        ):
            continue

        related.append({

            "video_id": video.get(
                "id"
            ),

            "title": video.get(
                "title",
                ""
            ),

            "published_at": video.get(
                "published_at"
            ),

            "views": video.get(
                "views",
                0
            ),

            "content_type": video.get(
                "content_type"
            ),

            **scores
        })

    related.sort(
        key=lambda x: x[
            "related_score"
        ],
        reverse=True
    )

    return related

if __name__ == "__main__":

    target = {
        "id": "1",
        "title": "Drunk Minecraft #1 | A NEW HOPE",
        "published_at": "2012-08-09T00:00:00+00:00",
        "views": 10616588,
        "content_type": "gaming",
    }

    candidates = [
        {
            "id": "42",
            "title": "Drunk Minecraft #42 | TO THE MOON!!",
            "published_at": "2013-05-30T00:00:00+00:00",
            "views": 3609241,
            "content_type": "gaming",
        },
        {
            "id": "60",
            "title": "Drunk Minecraft #60 | PROP HUNT #2",
            "published_at": "2013-12-15T00:00:00+00:00",
            "views": 2656723,
            "content_type": "gaming",
        },
        {
            "id": "56",
            "title": "Drunk Minecraft #56 | PROP HUNT",
            "published_at": "2013-11-16T00:00:00+00:00",
            "views": 2519206,
            "content_type": "gaming",
        },
    ]

    for candidate in candidates:

        print()
        print("=" * 60)

        print(
            candidate["title"]
        )

        print(
            "Series A:",
            extract_series_identity(
                target["title"]
            )
        )

        print(
            "Series B:",
            extract_series_identity(
                candidate["title"]
            )
        )

        print(
            "Episode A:",
            extract_episode_number(
                target["title"]
            )
        )

        print(
            "Episode B:",
            extract_episode_number(
                candidate["title"]
            )
        )

        print(
            "Scores:"
        )

        print(
            calculate_related_score(
                target,
                candidate
            )
        )