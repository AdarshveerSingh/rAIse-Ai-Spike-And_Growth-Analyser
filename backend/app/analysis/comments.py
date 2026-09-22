import re
from collections import Counter


THEMES = {
    "creator": [
        "markiplier",
        "mark",
        "markus"
    ],
    "minecraft": [
        "minecraft",
        "mc",
        "creeper",
        "diamond",
        "craft"
    ],
    "collaboration": [
        "bob",
        "muyskerm",
        "wade",
        "lordminion",
        "friend",
        "friends",
        "collab"
    ],
    "series": [
        "part 2",
        "part 3",
        "part 4",
        "episode",
        "series",
        "more",
        "next one",
        "another"
    ],
    "discovery": [
        "found you",
        "discovered you",
        "first video",
        "first time",
        "new subscriber",
        "subscribed"
    ],
    "humor": [
        "funny",
        "laugh",
        "laughed",
        "hilarious",
        "lol",
        "lmao"
    ],
    "positive_reaction": [
        "love",
        "loved",
        "amazing",
        "great",
        "awesome",
        "best",
        "favorite",
        "favourite"
    ]
}


def _contains_phrase(text, phrase):
    text = text.lower()
    phrase = phrase.lower()

    if " " in phrase:
        return phrase in text

    return bool(
        re.search(
            rf"\b{re.escape(phrase)}\b",
            text
        )
    )


def analyze_comments(comments):
    """
    Produce compact audience signals.

    This is descriptive analysis, not causal inference.
    """

    if not comments:
        return {
            "comment_count": 0,
            "total_likes": 0,
            "average_likes": 0,
            "top_comments": [],
            "theme_counts": {},
            "recurring_requests": [],
            "collaborator_mentions": [],
            "discovery_signals": [],
            "audience_signals": []
        }

    total_likes = sum(
        comment["like_count"]
        for comment in comments
    )

    average_likes = (
        total_likes / len(comments)
    )

    theme_counts = Counter()

    for comment in comments:
        text = comment["text"].lower()

        for theme, keywords in THEMES.items():
            if any(
                _contains_phrase(text, keyword)
                for keyword in keywords
            ):
                theme_counts[theme] += 1

    # Highest-liked comments
    top_comments = sorted(
        comments,
        key=lambda x: x["like_count"],
        reverse=True
    )[:10]

    top_comment_data = [
        {
            "text": comment["text"],
            "likes": comment["like_count"],
            "replies":comment.get("reply_count", 0)
        }
        for comment in top_comments
    ]

    # Comments indicating continuation requests
    recurring_requests = []

    request_patterns = [
        "part 2",
        "part 3",
        "part 4",
        "make another",
        "do another",
        "more of this",
        "more drunk minecraft",
        "next episode",
        "another episode",
        "continue this"
    ]

    for comment in comments:
        text = comment["text"].lower()

        if any(
            pattern in text
            for pattern in request_patterns
        ):
            recurring_requests.append({
                "text": comment["text"],
                "likes": comment["like_count"]
            })

    # Collaborator mentions
    collaborator_mentions = []

    collaborator_patterns = [
        "bob",
        "muyskerm",
        "wade",
        "lordminion"
    ]

    for comment in comments:
        text = comment["text"].lower()

        matched = [
            name
            for name in collaborator_patterns
            if _contains_phrase(text, name)
        ]

        if matched:
            collaborator_mentions.append({
                "mentions": matched,
                "text": comment["text"],
                "likes": comment["like_count"]
            })

    # Discovery signals
    discovery_signals = []

    discovery_patterns = [
        "first video",
        "first time watching",
        "found you",
        "discovered you",
        "new subscriber",
        "just subscribed",
        "subscribed because"
    ]

    for comment in comments:
        text = comment["text"].lower()

        if any(
            pattern in text
            for pattern in discovery_patterns
        ):
            discovery_signals.append({
                "text": comment["text"],
                "likes": comment["like_count"]
            })

    audience_signals = []

    if theme_counts["series"] > 0:
        audience_signals.append(
            "Some sampled comments reference continuation, "
            "episodes, or requests for more content."
        )

    if theme_counts["collaboration"] > 0:
        audience_signals.append(
            "Some sampled comments mention collaborators."
        )

    if theme_counts["discovery"] > 0:
        audience_signals.append(
            "Some sampled comments contain creator-discovery "
            "or subscription language."
        )

    if theme_counts["humor"] > 0:
        audience_signals.append(
            "Some sampled comments explicitly reference "
            "humor or laughter."
        )

    return {
        "comment_count": len(comments),
        "total_likes": total_likes,
        "average_likes": round(
            average_likes,
            2
        ),
        "top_comments": top_comment_data,
        "theme_counts": dict(theme_counts),
        "recurring_requests": recurring_requests[:10],
        "collaborator_mentions": collaborator_mentions[:10],
        "discovery_signals": discovery_signals[:10],
        "audience_signals": audience_signals
    }