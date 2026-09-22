from app.vision.thumbnails import (
    download_thumbnail,
    analyze_thumbnail,
    thumbnail_hash,
    thumbnail_similarity
)

from app.vision.cache import (
    get_cached_analysis,
    save_cached_analysis
)


def analyze_thumbnail_groups(thumbnail_set):

    results = []

    for group_name, group in thumbnail_set.items():

        videos = [group] if isinstance(group, dict) else group

        for video in videos:

            video_id = video["id"]

            # --------------------------------------------------
            # CACHE
            # --------------------------------------------------

            cached = get_cached_analysis(video_id)

            if cached is not None:

                results.append({
                    "video_id": video_id,
                    "title": video["title"],
                    "group": group_name,
                    "views": video["views"],
                    "published_at": video["published_at"],
                    "thumbnail_hash": cached["thumbnail_hash"],
                    "visual_analysis": cached["visual_analysis"],
                    "cached": True
                })

                continue

            # --------------------------------------------------
            # DOWNLOAD + ANALYZE
            # --------------------------------------------------

            try:

                image_bytes = download_thumbnail(
                    video["thumbnail_url"]
                )

                visual_analysis = analyze_thumbnail(
                    image_bytes
                )

                image_hash = thumbnail_hash(
                    image_bytes
                )

                # --------------------------------------------------
                # SAVE CACHE
                # --------------------------------------------------

                save_cached_analysis(
                    video_id,
                    {
                        "thumbnail_hash": str(image_hash),
                        "visual_analysis": visual_analysis
                    }
                )

                results.append({
                    "video_id": video_id,
                    "title": video["title"],
                    "group": group_name,
                    "views": video["views"],
                    "published_at": video["published_at"],
                    "thumbnail_hash": str(image_hash),
                    "visual_analysis": visual_analysis,
                    "cached": False
                })

            except Exception as e:

                results.append({
                    "video_id": video_id,
                    "title": video.get(
                        "title",
                        "Unknown"
                    ),
                    "group": group_name,
                    "views": video.get(
                        "views",
                        0
                    ),
                    "published_at": video.get(
                        "published_at"
                    ),
                    "error": str(e),
                    "cached": False
                })

    return results


def compare_thumbnail_results(results):
    """
    Compare thumbnails across groups.

    Expected groups can include:

        before
        target
        after
        related
        cross_year

    Returns structured comparisons without making
    causal claims about performance.
    """

    valid_results = [
        result
        for result in results
        if "error" not in result
        and result.get("thumbnail_hash")
    ]

    comparisons = []

    for i in range(len(valid_results)):

        first = valid_results[i]

        for j in range(i + 1, len(valid_results)):

            second = valid_results[j]

            try:

                hash1 = __import__(
                    "imagehash"
                ).hex_to_hash(
                    first["thumbnail_hash"]
                )

                hash2 = __import__(
                    "imagehash"
                ).hex_to_hash(
                    second["thumbnail_hash"]
                )

                similarity = thumbnail_similarity(
                    hash1,
                    hash2
                )

                comparisons.append({
                    "video_a": first["video_id"],
                    "video_b": second["video_id"],

                    "title_a": first["title"],
                    "title_b": second["title"],

                    "group_a": first["group"],
                    "group_b": second["group"],

                    "visual_similarity": similarity
                })

            except Exception:
                continue

    return comparisons


def build_thumbnail_summary(results, comparisons):
    """
    Build a compact structured object for the final
    analysis agent.
    """

    valid_results = [
        result
        for result in results
        if "error" not in result
    ]

    summary = {
        "thumbnail_count": len(valid_results),
        "analyses": valid_results,
        "comparisons": comparisons
    }

    return summary