from app.youtube.client import (
    get_channel,
    get_video_ids,
    get_videos,
)

from app.analysis.metrics import (
    prepare_videos,
)

from app.analysis.rolling import (
    rolling_baseline,
)

from app.analysis.related import (
    find_related_videos,
)

from app.analysis.spikes import (
    detect_spikes,
    rank_spikes,
)

from app.analysis.cross_year import (
    find_cross_year_candidates,
)


# ============================================================
# CONFIG
# ============================================================

CHANNEL_ID = "UC7_YxT-KID8kRbqZo7MyscQ"

TARGET_VIDEO_ID = "OzItHn9GSRE"

AUDIENCE_PEAK_YEAR = 2013

MAX_CANDIDATES = 20

ROLLING_WINDOW = 10

MIN_SPIKE_RATIO = 3.0

MIN_ROBUST_Z = 2.5


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 80)
    print("LOADING CHANNEL")
    print("=" * 80)

    # --------------------------------------------------------
    # CHANNEL
    # --------------------------------------------------------

    channel = get_channel(
        CHANNEL_ID
    )

    print(
        "Channel:",
        channel.get(
            "title",
            "Unknown"
        )
    )

    uploads_playlist_id = channel[
        "uploads_playlist_id"
    ]

    print(
        "Uploads playlist:",
        uploads_playlist_id
    )

    # --------------------------------------------------------
    # VIDEO IDS
    # --------------------------------------------------------

    print()
    print(
        "Loading video IDs..."
    )

    video_ids = get_video_ids(
        uploads_playlist_id
    )

    print(
        "Video IDs:",
        len(video_ids)
    )

    # --------------------------------------------------------
    # VIDEOS
    # --------------------------------------------------------

    print()
    print(
        "Loading videos..."
    )

    videos = get_videos(
        video_ids
    )

    print(
        "Videos loaded:",
        len(videos)
    )

    # --------------------------------------------------------
    # TARGET VIDEO
    # --------------------------------------------------------

    target_video = next(
        (
            video
            for video in videos
            if video.get("id")
            == TARGET_VIDEO_ID
        ),
        None
    )

    if not target_video:

        print()
        print(
            "ERROR: Target video was not found."
        )

        return

    print()
    print("=" * 80)
    print("TARGET VIDEO")
    print("=" * 80)

    print(
        "Title:",
        target_video.get(
            "title"
        )
    )

    print(
        "Video ID:",
        target_video.get(
            "id"
        )
    )

    print(
        "Published:",
        target_video.get(
            "published_at"
        )
    )

    print(
        "Views:",
        f"{target_video.get('views', 0):,}"
    )

    # --------------------------------------------------------
    # PREPARE VIDEO METRICS
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("PREPARING VIDEO METRICS")
    print("=" * 80)

    prepared_videos = prepare_videos(
        videos
    )

    print(
        "Prepared:",
        len(prepared_videos)
    )

    # --------------------------------------------------------
    # ROLLING BASELINE
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("CALCULATING ROLLING BASELINE")
    print("=" * 80)

    prepared_videos = rolling_baseline(
        prepared_videos,
        window=ROLLING_WINDOW
    )

    print(
        "Rolling baseline calculated."
    )

    # --------------------------------------------------------
    # SPIKES
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("DETECTING SPIKES")
    print("=" * 80)

    spikes = detect_spikes(
        prepared_videos,
        min_ratio=MIN_SPIKE_RATIO,
        min_robust_z=MIN_ROBUST_Z
    )

    spikes = rank_spikes(
        spikes
    )

    print(
        "Total spikes:",
        len(spikes)
    )

    # --------------------------------------------------------
    # RELATED VIDEOS
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("FINDING RELATED VIDEOS")
    print("=" * 80)

    related_videos = find_related_videos(
        target_video,
        prepared_videos,
        threshold=0.15
    )

    print(
        "Related videos:",
        len(related_videos)
    )

    # --------------------------------------------------------
    # CROSS-YEAR CANDIDATES
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("GENERATING CROSS-YEAR CANDIDATES")
    print("=" * 80)

    print(
        "Target upload year:",
        target_video[
            "published_at"
        ][:4]
    )

    print(
        "Audience peak year:",
        AUDIENCE_PEAK_YEAR
    )

    candidates = find_cross_year_candidates(
        target_video=target_video,
        audience_peak_year=AUDIENCE_PEAK_YEAR,
        videos=prepared_videos,
        spikes=spikes,
        related_videos=related_videos,
        max_candidates=MAX_CANDIDATES,
    )

    # --------------------------------------------------------
    # RESULTS
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("CROSS-YEAR CANDIDATES")
    print("=" * 80)

    if not candidates:

        print(
            "No candidates found."
        )

        return

    for index, candidate in enumerate(
        candidates,
        start=1
    ):

        print()
        print(
            f"{index}. {candidate['title']}"
        )

        print(
            "   Video ID:",
            candidate["video_id"]
        )

        print(
            "   Date:",
            candidate["date"]
        )

        print(
            "   Views:",
            f"{candidate['views']:,}"
        )

        print(
            "   Relationship:",
            candidate["relationship"]
        )

        print(
            "   Candidate score:",
            candidate["candidate_score"]
        )

        print(
            "   Title similarity:",
            candidate["title_similarity"]
        )

        print(
            "   Series identity:",
            candidate["series_identity"]
        )

        print(
            "   Numbered series:",
            candidate[
                "numbered_series_score"
            ]
        )

        print(
            "   Existing related score:",
            candidate[
                "existing_related_score"
            ]
        )

        print(
            "   Temporal score:",
            candidate["temporal_score"]
        )

        print(
            "   Content type score:",
            candidate[
                "content_type_score"
            ]
        )

        print(
            "   Spike ratio:",
            candidate["spike_ratio"]
        )

        print(
            "   Robust Z:",
            candidate["robust_z"]
        )

        print(
            "   Spike signal:",
            candidate["spike_signal"]
        )

        print(
            "   Is spike:",
            candidate["is_spike"]
        )

        print(
            "   Performance score:",
            candidate["performance_score"]
        )
        
        print(
            "   Reasons:",
            ", ".join(candidate["reasons"])
        )
    # --------------------------------------------------------
    # SUMMARY
    # --------------------------------------------------------

    print()
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)

    print(
        "Target:",
        target_video["title"]
    )

    print(
        "Target upload year:",
        target_video[
            "published_at"
        ][:4]
    )

    print(
        "Audience peak year:",
        AUDIENCE_PEAK_YEAR
    )

    print(
        "Total channel videos:",
        len(prepared_videos)
    )

    print(
        "Total channel spikes:",
        len(spikes)
    )

    print(
        "Related videos:",
        len(related_videos)
    )

    print(
        "Candidates found:",
        len(candidates)
    )

    print()

    for index, candidate in enumerate(
        candidates[:10],
        start=1
    ):

        print(
            f"{index}. "
            f"{candidate['title']} "
            f"({candidate['candidate_score']})"
        )


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()