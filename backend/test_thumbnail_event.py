import json

from app.youtube.client import (
    get_videos,
)

from app.vision.thumbnails import (
    download_thumbnail,
    analyze_thumbnail,
    thumbnail_hash,
    thumbnail_similarity,
)


# ============================================================
# CONFIG
# ============================================================

TARGET_VIDEO_ID = "OzItHn9GSRE"

# Number of videos before/after the target to analyze
BEFORE_COUNT = 3
AFTER_COUNT = 3


# ============================================================
# HELPERS
# ============================================================

def analyze_video_thumbnail(video):
    """
    Download and analyze one video's thumbnail.
    """

    print(
        f"Analyzing thumbnail: {video['title']}"
    )

    image_bytes = download_thumbnail(
        video["thumbnail_url"]
    )

    visual_analysis = analyze_thumbnail(
        image_bytes
    )

    image_hash = thumbnail_hash(
        image_bytes
    )

    return {
        "video_id": video["id"],
        "title": video["title"],
        "published_at": video["published_at"],
        "views": video["views"],
        "thumbnail_url": video["thumbnail_url"],
        "thumbnail_hash": str(image_hash),
        "visual_analysis": visual_analysis,
    }


def compare_two_thumbnails(first, second):
    """
    Compare two thumbnail hashes.
    """

    hash1 = thumbnail_hash_from_string(
        first["thumbnail_hash"]
    )

    hash2 = thumbnail_hash_from_string(
        second["thumbnail_hash"]
    )

    return {
        "video_a": first["video_id"],
        "video_b": second["video_id"],
        "title_a": first["title"],
        "title_b": second["title"],
        "visual_similarity": thumbnail_similarity(
            hash1,
            hash2
        ),
    }


def thumbnail_hash_from_string(hash_string):
    """
    Convert cached/string pHash back into an imagehash object.
    """

    import imagehash

    return imagehash.hex_to_hash(
        hash_string
    )


def compare_visual_features(first, second):
    """
    Identify observable differences between two
    thumbnail analyses.

    This does NOT make performance or causal claims.
    """

    a = first["visual_analysis"]
    b = second["visual_analysis"]

    differences = []

    fields = [
        "has_face",
        "face_count",
        "expression",
        "has_text",
        "text_amount",
        "subject_position",
        "shot_type",
        "high_contrast",
        "arrows_or_circles",
        "visual_complexity",
        "branding_elements",
        "main_subject",
    ]

    for field in fields:

        value_a = a.get(field)
        value_b = b.get(field)

        if value_a != value_b:

            differences.append({
                "feature": field,
                "before": value_a,
                "after": value_b,
            })

    return differences


# ============================================================
# LOAD TARGET
# ============================================================

print("\n")
print("=" * 80)
print("LOADING TARGET VIDEO")
print("=" * 80)


target_video = get_videos(
    [TARGET_VIDEO_ID]
)[0]


print(
    "\nTarget:",
    target_video["title"]
)

print(
    "Published:",
    target_video["published_at"]
)

print(
    "Views:",
    f"{target_video['views']:,}"
)


# ============================================================
# LOAD CHANNEL VIDEOS
# ============================================================

print("\n")
print("=" * 80)
print("LOADING CHANNEL VIDEOS")
print("=" * 80)


# Markiplier channel
CHANNEL_ID = "UC7_YxT-KID8kRbqZo7MyscQ"


from app.youtube.client import (
    get_channel,
    get_video_ids,
)


channel = get_channel(
    CHANNEL_ID
)


video_ids = get_video_ids(
    channel["uploads_playlist_id"],
    max_results=5794
)


all_videos = get_videos(
    video_ids
)


print(
    "\nTotal videos:",
    len(all_videos)
)


# ============================================================
# SORT CHRONOLOGICALLY
# ============================================================

all_videos.sort(
    key=lambda video: video["published_at"]
)


target_index = None

for index, video in enumerate(all_videos):

    if video["id"] == TARGET_VIDEO_ID:

        target_index = index
        break


if target_index is None:

    raise ValueError(
        "Target video was not found in channel videos."
    )


print(
    "Target index:",
    target_index
)


# ============================================================
# BEFORE / TARGET / AFTER
# ============================================================

before_videos = all_videos[
    max(0, target_index - BEFORE_COUNT):
    target_index
]

after_videos = all_videos[
    target_index + 1:
    target_index + 1 + AFTER_COUNT
]


print("\n")
print("=" * 80)
print("EVENT WINDOW")
print("=" * 80)


print("\nBEFORE:")

for video in before_videos:

    print(
        "-",
        video["title"],
        "|",
        video["published_at"],
        "|",
        f"{video['views']:,}",
    )


print("\nTARGET:")

print(
    "-",
    target_video["title"],
    "|",
    target_video["published_at"],
    "|",
    f"{target_video['views']:,}",
)


print("\nAFTER:")

for video in after_videos:

    print(
        "-",
        video["title"],
        "|",
        video["published_at"],
        "|",
        f"{video['views']:,}",
    )


# ============================================================
# ANALYZE THUMBNAILS
# ============================================================

print("\n")
print("=" * 80)
print("ANALYZING THUMBNAILS")
print("=" * 80)


thumbnail_results = []


# BEFORE

for video in before_videos:

    result = analyze_video_thumbnail(
        video
    )

    result["group"] = "before"

    thumbnail_results.append(
        result
    )


# TARGET

target_result = analyze_video_thumbnail(
    target_video
)

target_result["group"] = "target"

thumbnail_results.append(
    target_result
)


# AFTER

for video in after_videos:

    result = analyze_video_thumbnail(
        video
    )

    result["group"] = "after"

    thumbnail_results.append(
        result
    )


# ============================================================
# PRINT INDIVIDUAL ANALYSES
# ============================================================

print("\n")
print("=" * 80)
print("INDIVIDUAL THUMBNAIL ANALYSIS")
print("=" * 80)


for result in thumbnail_results:

    print("\n")

    print(
        "VIDEO:",
        result["title"]
    )

    print(
        "GROUP:",
        result["group"]
    )

    print(
        "VIEWS:",
        f"{result['views']:,}"
    )

    print(
        "ANALYSIS:"
    )

    print(
        json.dumps(
            result["visual_analysis"],
            indent=2,
            ensure_ascii=False
        )
    )


# ============================================================
# TARGET VS BEFORE
# ============================================================

print("\n")
print("=" * 80)
print("TARGET VS BEFORE")
print("=" * 80)


target_before_comparisons = []


for result in thumbnail_results:

    if result["group"] != "before":
        continue

    hash1 = thumbnail_hash_from_string(
        result["thumbnail_hash"]
    )

    hash2 = thumbnail_hash_from_string(
        target_result["thumbnail_hash"]
    )

    similarity = thumbnail_similarity(
        hash1,
        hash2
    )

    differences = compare_visual_features(
        result,
        target_result
    )

    comparison = {
        "before_video": result["title"],
        "target_video": target_result["title"],
        "visual_similarity": similarity,
        "feature_changes": differences,
    }

    target_before_comparisons.append(
        comparison
    )

    print("\n")
    print(
        "BEFORE:",
        result["title"]
    )

    print(
        "SIMILARITY:",
        similarity
    )

    print(
        "CHANGES:"
    )

    print(
        json.dumps(
            differences,
            indent=2,
            ensure_ascii=False
        )
    )


# ============================================================
# TARGET VS AFTER
# ============================================================

print("\n")
print("=" * 80)
print("TARGET VS AFTER")
print("=" * 80)


target_after_comparisons = []


for result in thumbnail_results:

    if result["group"] != "after":
        continue

    hash1 = thumbnail_hash_from_string(
        target_result["thumbnail_hash"]
    )

    hash2 = thumbnail_hash_from_string(
        result["thumbnail_hash"]
    )

    similarity = thumbnail_similarity(
        hash1,
        hash2
    )

    differences = compare_visual_features(
        target_result,
        result
    )

    comparison = {
        "target_video": target_result["title"],
        "after_video": result["title"],
        "visual_similarity": similarity,
        "feature_changes": differences,
    }

    target_after_comparisons.append(
        comparison
    )

    print("\n")
    print(
        "AFTER:",
        result["title"]
    )

    print(
        "SIMILARITY:",
        similarity
    )

    print(
        "CHANGES:"
    )

    print(
        json.dumps(
            differences,
            indent=2,
            ensure_ascii=False
        )
    )


# ============================================================
# FINAL STRUCTURED OUTPUT
# ============================================================

thumbnail_event_analysis = {

    "target_event": {
        "video_id": target_video["id"],
        "title": target_video["title"],
        "published_at": target_video["published_at"],
        "views": target_video["views"],
    },

    "thumbnail_results": thumbnail_results,

    "target_vs_before": target_before_comparisons,

    "target_vs_after": target_after_comparisons,
}


# ============================================================
# PRINT FINAL JSON
# ============================================================

print("\n")
print("=" * 80)
print("FINAL THUMBNAIL EVENT ANALYSIS")
print("=" * 80)


print(
    json.dumps(
        thumbnail_event_analysis,
        indent=2,
        ensure_ascii=False
    )
)