from app.youtube.client import get_channel
from app.youtube.client import get_video_ids
from app.youtube.client import get_videos

from app.vision.thumbnails import (
    download_thumbnail,
    thumbnail_hash,
    thumbnail_similarity
)


channel = get_channel(
    "UC_x5XG1OV2P6uZZ5FSM9Ttw"
)

video_ids = get_video_ids(
    channel["uploads_playlist_id"],
    max_results=5
)

videos = get_videos(video_ids)

hashes = []

for video in videos:
    image = download_thumbnail(
        video["thumbnail_url"]
    )

    h = thumbnail_hash(image)
    hashes.append(h)

    print(
        video["title"],
        "→",
        h
    )


print("\nSimilarity between thumbnails:\n")

for i in range(len(hashes)):
    for j in range(i + 1, len(hashes)):
        similarity = thumbnail_similarity(
            hashes[i],
            hashes[j]
        )

        print(
            f"{i} vs {j}: {similarity}"
        )