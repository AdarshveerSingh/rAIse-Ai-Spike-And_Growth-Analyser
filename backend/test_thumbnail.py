from app.youtube.client import get_channel
from app.youtube.client import get_video_ids
from app.youtube.client import get_videos

from app.vision.thumbnails import (
    download_thumbnail,
    analyze_thumbnail
)


# ============================================================
# GET CHANNEL
# ============================================================

channel = get_channel(
    "UC_x5XG1OV2P6uZZ5FSM9Ttw"
)


# ============================================================
# GET LATEST VIDEO
# ============================================================

video_ids = get_video_ids(
    channel["uploads_playlist_id"],
    max_results=1
)

videos = get_videos(video_ids)


# ============================================================
# DOWNLOAD THUMBNAIL
# ============================================================

thumbnail = download_thumbnail(
    videos[0]["thumbnail_url"]
)


# ============================================================
# ANALYZE THUMBNAIL
# ============================================================

analysis = analyze_thumbnail(
    thumbnail
)


# ============================================================
# OUTPUT
# ============================================================

print("\n" + "=" * 80)
print("VIDEO")
print("=" * 80)

print(videos[0]["title"])


print("\n" + "=" * 80)
print("THUMBNAIL ANALYSIS")
print("=" * 80)

print(analysis)