from app.youtube.comments import (
    fetch_comments
)


def fetch_chronological_comments(
    video_id,
    total_comments=1000
):

    comments = fetch_comments(
        video_id,
        max_results=total_comments,
        order="time"
    )

    return comments


def evenly_sample_comments(
    comments,
    sample_size=100
):

    if not comments:
        return []

    comments = sorted(
        comments,
        key=lambda x: x["published_at"]
    )

    if len(comments) <= sample_size:
        return comments

    step = (
        (len(comments) - 1)
        / (sample_size - 1)
    )

    sampled = []

    for i in range(sample_size):

        index = round(
            i * step
        )

        sampled.append(
            comments[index]
        )

    return sampled