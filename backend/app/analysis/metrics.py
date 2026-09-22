from datetime import datetime


def prepare_videos(videos):
    prepared = []

    for video in videos:
        published_at = datetime.fromisoformat(
            video["published_at"].replace("Z", "+00:00")
        )

        views = video["views"]
        likes = video["likes"]
        comments = video["comments"]

        engagement_rate = 0

        if views > 0:
            engagement_rate = (
                (likes + comments) / views
            ) * 100

        prepared.append({
            **video,
            "published_at": published_at,
            "engagement_rate": round(
                engagement_rate, 3
            )
        })

    prepared.sort(
        key=lambda x: x["published_at"]
    )

    return prepared