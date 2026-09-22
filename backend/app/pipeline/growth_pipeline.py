import json
from datetime import datetime
from typing import Optional


from app.youtube.client import (
    get_channel,
    get_video_ids,
    get_videos,
)

from app.youtube.comments import (
    fetch_all_comments,
    fetch_relevant_comments,
)

from app.analysis.metrics import (
    prepare_videos,
)

from app.analysis.rolling import (
    rolling_baseline,
)

from app.analysis.spikes import (
    detect_spikes,
    rank_spikes,
)

from app.analysis.related import (
    find_related_videos,
)

from app.analysis.audience_timing import (
    detect_peak_interaction_year,
)

from app.analysis.comments import (
    analyze_comments,
)

from app.analysis.cross_year import (
    find_cross_year_candidates,
)

from app.research.agent import (
    research_event,
)

from app.reporting.final_agent import (
    generate_final_report,
)

from app.vision.compare import (
    analyze_thumbnail_groups,
)


# ============================================================
# CONFIG
# ============================================================

BEFORE_COUNT = 3
AFTER_COUNT = 3

RELATED_LIMIT = 20
CROSS_YEAR_LIMIT = 5

COMMENT_SAMPLE_SIZE = 100

ROLLING_WINDOW = 10

MIN_SPIKE_RATIO = 3.0
MIN_ROBUST_Z = 2.5


# ============================================================
# HELPERS
# ============================================================

def json_safe_value(value):
    """
    Recursively convert Python values into JSON-safe values.

    datetime -> ISO string
    dict/list/tuple -> recursively converted
    """

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, dict):
        return {
            key: json_safe_value(val)
            for key, val in value.items()
        }

    if isinstance(value, list):
        return [
            json_safe_value(item)
            for item in value
        ]

    if isinstance(value, tuple):
        return [
            json_safe_value(item)
            for item in value
        ]

    return value


def json_safe_video(video):
    """
    Make a JSON-safe copy of a video.
    """

    return json_safe_value(
        dict(video)
    )


def print_separator(title):
    """
    Print a readable pipeline section header.
    """

    print()
    print("=" * 70)
    print(title)
    print("=" * 70)


# ============================================================
# MAIN PIPELINE
# ============================================================

def run_growth_pipeline(
    channel_id: str,
    creator_name: str,
    target_video_id: Optional[str] = None,
    save_output: bool = False,
    output_path: str = "cache/full_pipeline_result.json",
):
    """
    Run the complete YouTube growth analysis pipeline.

    Parameters
    ----------
    channel_id:
        YouTube channel ID.

    creator_name:
        Creator/channel name.

    target_video_id:
        Optional video ID selected by the user.

        If provided, the pipeline will research this detected
        spike instead of automatically selecting the strongest
        spike.

        If None, the strongest detected spike is selected.
        This preserves the original test_full_pipeline.py
        behavior.

    save_output:
        Whether to save the complete pipeline result to disk.

    output_path:
        Path used when save_output=True.

    Returns
    -------
    dict
        Complete pipeline result.
    """

    # ========================================================
    # 1. LOAD CHANNEL
    # ========================================================

    print_separator(
        "[1] Loading channel"
    )

    channel = get_channel(
        channel_id
    )

    print(
        f"Channel: "
        f"{channel.get('title', creator_name)}"
    )

    print(
        f"Channel ID: "
        f"{channel['id']}"
    )

    # uploads_playlist_id is obtained automatically
    # from get_channel().

    uploads_playlist_id = (
        channel["uploads_playlist_id"]
    )

    print(
        f"Uploads playlist: "
        f"{uploads_playlist_id}"
    )


    # ========================================================
    # 2. LOAD VIDEOS
    # ========================================================

    print_separator(
        "[2] Loading YouTube videos"
    )

    video_ids = get_video_ids(
        uploads_playlist_id
    )

    print(
        f"Video IDs: "
        f"{len(video_ids)}"
    )

    videos = get_videos(
        video_ids
    )

    print(
        f"Loaded videos: "
        f"{len(videos)}"
    )


    # ========================================================
    # 3. PREPARE QUANTITATIVE METRICS
    # ========================================================

    print_separator(
        "[3] Preparing quantitative metrics"
    )

    prepared_videos = prepare_videos(
        videos
    )

    print(
        f"Prepared videos: "
        f"{len(prepared_videos)}"
    )


    # ========================================================
    # 4. CALCULATE ROLLING BASELINE + SPIKE METRICS
    # ========================================================

    print_separator(
        "[4] Calculating rolling spike metrics"
    )

    analyzed_videos = rolling_baseline(
        prepared_videos,
        window=ROLLING_WINDOW,
    )

    print(
        f"Videos analyzed: "
        f"{len(analyzed_videos)}"
    )

    # --------------------------------------------------------
    # Sanity check
    # --------------------------------------------------------

    eligible_spike_metrics = sum(
        1
        for video in analyzed_videos
        if video.get(
            "rolling_spike_ratio"
        ) is not None
    )

    print(
        f"Videos with valid rolling baseline: "
        f"{eligible_spike_metrics}"
    )

    # --------------------------------------------------------
    # Show one example of generated metrics
    # --------------------------------------------------------

    if eligible_spike_metrics > 0:

        example = next(
            video
            for video in analyzed_videos
            if video.get(
                "rolling_spike_ratio"
            ) is not None
        )

        print()
        print(
            "Example rolling metrics:"
        )

        print(
            f"  {example['title']}"
        )

        print(
            f"  baseline="
            f"{example['rolling_baseline_views']}"
        )

        print(
            f"  spike_ratio="
            f"{example['rolling_spike_ratio']}"
        )

        print(
            f"  robust_z="
            f"{example['robust_z']}"
        )


    # ========================================================
    # 5. DETECT SPIKES
    # ========================================================

    print_separator(
        "[5] Detecting spikes"
    )

    spikes = detect_spikes(
        analyzed_videos,
        min_ratio=MIN_SPIKE_RATIO,
        min_robust_z=MIN_ROBUST_Z,
    )

    ranked_spikes = rank_spikes(
        spikes
    )

    print(
        f"Detected spikes: "
        f"{len(spikes)}"
    )

    print()
    print("Top spikes:")

    for spike in ranked_spikes[:10]:

        robust_z = spike.get(
            "robust_z"
        )

        if robust_z is None:
            robust_z_text = "N/A"
        else:
            robust_z_text = (
                f"{robust_z:.3f}"
            )

        print(
            f"  {spike['title']}"
        )

        print(
            f"    ratio="
            f"{spike['spike_ratio']:.3f} "
            f"robust_z="
            f"{robust_z_text} "
            f"signal="
            f"{spike['signal']}"
        )


    # ========================================================
    # 6. SELECT TARGET EVENT
    # ========================================================

    print_separator(
        "[6] Selecting target event"
    )

    if not ranked_spikes:
        raise RuntimeError(
            "No spikes were detected. "
            "Cannot continue to event analysis."
        )

    # --------------------------------------------------------
    # USER-SELECTED EVENT
    # --------------------------------------------------------
    #
    # If the frontend supplied a target_video_id,
    # use that spike.
    #
    # Otherwise preserve the original behavior and
    # automatically select the strongest spike.
    # --------------------------------------------------------

    if target_video_id:

        target_spike = next(
            (
                spike
                for spike in ranked_spikes
                if spike["video_id"] == target_video_id
            ),
            None,
        )

        if target_spike is None:
            raise ValueError(
                f"Selected video "
                f"{target_video_id} was not detected "
                f"as a spike."
            )

    else:

        target_spike = (
            ranked_spikes[0]
        )

        target_video_id = (
            target_spike["video_id"]
        )

    # --------------------------------------------------------
    # Find target video in analyzed videos
    # --------------------------------------------------------

    target = None
    target_index = None

    for index, video in enumerate(
        analyzed_videos
    ):

        if video["id"] == target_video_id:

            target = video
            target_index = index

            break

    if target is None:
        raise RuntimeError(
            "Detected spike video was not "
            "found in analyzed videos."
        )

    print(
        f"Selected event: "
        f"{target['title']}"
    )

    print(
        f"Video ID: "
        f"{target['id']}"
    )

    print(
        f"Date: "
        f"{target['published_at']}"
    )

    print(
        f"Views: "
        f"{target['views']:,}"
    )

    print(
        f"Index: "
        f"{target_index}"
    )

    print(
        f"Baseline: "
        f"{target.get('rolling_baseline_views')}"
    )

    print(
        f"Spike ratio: "
        f"{target.get('rolling_spike_ratio')}"
    )

    print(
        f"Robust Z: "
        f"{target.get('robust_z')}"
    )


    # ========================================================
    # 7. BUILD BEFORE / AFTER CONTEXT
    # ========================================================

    print_separator(
        "[7] Building before/after context"
    )

    before_start = max(
        0,
        target_index - BEFORE_COUNT
    )

    before_videos = (
        analyzed_videos[
            before_start:target_index
        ]
    )

    after_videos = (
        analyzed_videos[
            target_index + 1:
            target_index + 1 + AFTER_COUNT
        ]
    )

    print()
    print("BEFORE:")

    for video in before_videos:

        print(
            f"  {video['title']} "
            f"({video['views']:,} views)"
        )

    print()
    print("TARGET:")

    print(
        f"  {target['title']} "
        f"({target['views']:,} views)"
    )

    print()
    print("AFTER:")

    for video in after_videos:

        print(
            f"  {video['title']} "
            f"({video['views']:,} views)"
        )


    # ========================================================
    # 8. FIND RELATED VIDEOS
    # ========================================================

    print_separator(
        "[8] Finding related videos"
    )

    related_videos = find_related_videos(
        target_video=target,
        videos=analyzed_videos,
        threshold=0.20,
    )

    related_videos = (
        related_videos[
            :RELATED_LIMIT
        ]
    )

    print(
        f"Related videos found: "
        f"{len(related_videos)}"
    )

    for video in related_videos[:10]:

        print(
            f"  {video['title']} "
            f"score="
            f"{video.get('score', 0)}"
        )


    # ========================================================
    # 9. LOAD AUDIENCE COMMENTS
    # ========================================================

    print_separator(
        "[9] Loading audience comments"
    )

    total_comment_count = int(
        target.get(
            "comments",
            0
        )
    )

    print(
        f"Total YouTube comments: "
        f"{total_comment_count:,}"
    )

    # --------------------------------------------------------
    # HIGH-ENGAGEMENT THRESHOLD
    # --------------------------------------------------------

    HIGH_ENGAGEMENT_COMMENT_THRESHOLD = 25000

    if (
        total_comment_count
        > HIGH_ENGAGEMENT_COMMENT_THRESHOLD
    ):

        # ====================================================
        # HIGH-ENGAGEMENT MODE
        # ====================================================

        audience_mode = (
            "high_engagement"
        )

        print(
            "High-engagement video detected."
        )

        print(
            f"Comment count exceeds "
            f"{HIGH_ENGAGEMENT_COMMENT_THRESHOLD:,}."
        )

        print(
            "Using YouTube relevance ordering."
        )

        comments = fetch_relevant_comments(
            target_video_id,
            max_comments=25000,
        )

    else:

        # ====================================================
        # HISTORICAL MODE
        # ====================================================

        audience_mode = (
            "historical"
        )

        print(
            "Historical audience mode."
        )

        print(
            f"Comment count is at or below "
            f"{HIGH_ENGAGEMENT_COMMENT_THRESHOLD:,}."
        )

        comments = fetch_all_comments(
            target_video_id,
            use_cache=True,
        )
        

    print(
        f"Comments retrieved: "
        f"{len(comments):,}"
    )

    print(
        f"Audience analysis mode: "
        f"{audience_mode}"
    )
    # ========================================================
    # 9B. ANALYZE COMMENTS
    # ========================================================

    comment_analysis = analyze_comments(
        comments
    )

    print(
        "Comment analysis completed."
    )

    print(
        f"  Themes: "
        f"{len(comment_analysis.get('theme_counts', {}))}"
    )

    print(
        f"  Audience signals: "
        f"{len(comment_analysis.get('audience_signals', []))}"
    )

    print(
        f"  Recurring requests: "
        f"{len(comment_analysis.get('recurring_requests', []))}"
    )

    print(
        f"  Collaborator mentions: "
        f"{len(comment_analysis.get('collaborator_mentions', []))}"
    )

    print(
        f"  Discovery signals: "
        f"{len(comment_analysis.get('discovery_signals', []))}"
    )
    # ========================================================
    # 10. ANALYZE AUDIENCE TIMING
    # ========================================================

    print_separator(
        "[10] Analyzing audience timing"
    )

    if audience_mode == "high_engagement":

        # ----------------------------------------------------
        # HIGH-ENGAGEMENT MODE
        # ----------------------------------------------------
        #
        # We intentionally do NOT determine which year had
        # the most comments.
        #
        # The comments were selected using YouTube relevance
        # ordering because this video already has substantial
        # audience discussion.
        # ----------------------------------------------------

        audience_timing = None

        print(
            "High-engagement mode:"
        )

        print(
            "Skipping audience peak-year analysis."
        )

        print(
            "Comments will instead be used to identify "
            "audience discussion themes."
        )

    else:

        # ----------------------------------------------------
        # HISTORICAL MODE
        # ----------------------------------------------------

        audience_timing = (
            detect_peak_interaction_year(
                comments,
                sample_size=COMMENT_SAMPLE_SIZE,
            )
        )

        print(
            json.dumps(
                audience_timing,
                indent=2,
                default=str,
            )
        )

    # ========================================================
    # 11. FIND CROSS-YEAR CANDIDATES
    # ========================================================

    print_separator(
        "[11] Finding cross-year candidates"
    )

    if audience_mode == "high_engagement":

        # ----------------------------------------------------
        # HIGH-ENGAGEMENT MODE
        # ----------------------------------------------------
        #
        # Cross-year research is intentionally skipped.
        # The target video already has substantial audience
        # discussion, so we analyze what those viewers are
        # talking about instead.
        # ----------------------------------------------------

        audience_peak_year = None

        cross_year_candidates = []

        print(
            "High-engagement mode active."
        )

        print(
            "Skipping audience peak-year detection."
        )

        print(
            "Skipping cross-year candidate search."
        )

    else:

        # ----------------------------------------------------
        # HISTORICAL MODE
        # ----------------------------------------------------

        audience_peak_year = None

        if audience_timing:

            audience_peak_year = (
                audience_timing.get(
                    "peak_year"
                )
            )

        # ----------------------------------------------------
        # Fallback to target upload year
        # ----------------------------------------------------

        if audience_peak_year is None:

            published_at = (
                target["published_at"]
            )

            if isinstance(
                published_at,
                datetime,
            ):

                audience_peak_year = (
                    published_at.year
                )

            else:

                audience_peak_year = (
                    datetime.fromisoformat(
                        str(published_at)
                        .replace(
                            "Z",
                            "+00:00",
                        )
                    ).year
                )

        print(
            f"Audience peak year: "
            f"{audience_peak_year}"
        )

        # ----------------------------------------------------
        # Determine target upload year
        # ----------------------------------------------------

        target_published_at = (
            target["published_at"]
        )

        if isinstance(
            target_published_at,
            datetime,
        ):

            target_upload_year = (
                target_published_at.year
            )

        else:

            target_upload_year = (
                datetime.fromisoformat(
                    str(target_published_at)
                    .replace(
                        "Z",
                        "+00:00",
                    )
                ).year
            )

        if (
            audience_peak_year
            == target_upload_year
        ):

            cross_year_candidates = []

            print(
                "Target upload year matches "
                "audience peak year. "
                "Skipping cross-year candidate search."
            )

        else:

            cross_year_candidates = (
                find_cross_year_candidates(

                    videos=analyzed_videos,

                    spikes=spikes,

                    related_videos=related_videos,

                    target_video=target,

                    audience_peak_year=(
                        audience_peak_year
                    ),

                    max_candidates=(
                        CROSS_YEAR_LIMIT
                    ),
                )
            )

    print(
        f"Cross-year candidates: "
        f"{len(cross_year_candidates)}"
    )

    for candidate in (
        cross_year_candidates
    ):

        print(
            f"  {candidate['title']} "
            f"score="
            f"{candidate.get('candidate_score', 0):.4f}"
        )

        print(
            f"    relationship="
            f"{candidate.get('relationship')} "
            f"performance="
            f"{candidate.get('performance_score', 0):.3f} "
            f"spike="
            f"{candidate.get('spike_ratio', 0):.3f}"
        )
    # ========================================================
    # 12. PREPARE RESEARCH AGENT INPUT
    # ========================================================

    print_separator(
        "[12] Preparing research agent input"
    )

    research_event_data = (
        json_safe_video(target)
    )

    research_event_data[
        "video_id"
    ] = target["id"]

    research_event_data[
        "before_videos"
    ] = [

        json_safe_video(video)

        for video in before_videos

    ]

    research_event_data[
        "short_videos"
    ] = [

        json_safe_video(video)

        for video in after_videos

    ]

    # Preserve the existing pipeline behavior:
    # the research agent receives related videos
    # in the long_videos field.

    research_event_data[
        "long_videos"
    ] = [

        json_safe_video(video)

        for video in related_videos

    ]

    safe_spikes = (
        json_safe_value(
            spikes
        )
    )

    safe_ranked_spikes = (
        json_safe_value(
            ranked_spikes
        )
    )

    safe_related_videos = (
        json_safe_value(
            related_videos
        )
    )

    safe_cross_year_candidates = (
        json_safe_value(
            cross_year_candidates
        )
    )

    # --------------------------------------------------------
    # Sanity checks
    # --------------------------------------------------------

    json.dumps(
        research_event_data
    )

    json.dumps(
        safe_spikes
    )

    json.dumps(
        safe_cross_year_candidates
    )

    print(
        "Research input is JSON serializable."
    )


    # ========================================================
    # 13. PREPARE SPIKE ANALYSIS
    # ========================================================

    print_separator(
        "[13] Preparing spike analysis"
    )

    # --------------------------------------------------------
    # IMPORTANT:
    #
    # research/agent.py expects period_spike_analysis
    # to be a LIST of dictionaries.
    #
    # _format_cross_year_context() does:
    #
    #     for row in period_spike_analysis:
    #         if row.get("period") == peak_year:
    #
    # Therefore DO NOT pass a summary dictionary here.
    # --------------------------------------------------------

    period_spike_analysis = []

    for spike in spikes:

        published_at = spike.get(
            "published_at"
        )

        # -----------------------------------------------
        # Determine year
        # -----------------------------------------------

        if isinstance(
            published_at,
            datetime,
        ):

            period = published_at.year

        else:

            try:

                period = datetime.fromisoformat(
                    str(published_at)
                    .replace(
                        "Z",
                        "+00:00",
                    )
                ).year

            except (
                ValueError,
                TypeError,
            ):

                continue

        # -----------------------------------------------
        # Create one structured row per spike
        # -----------------------------------------------

        period_spike_analysis.append({

            "period": period,

            "video_id": spike.get(
                "video_id",
                "",
            ),

            "title": spike.get(
                "title",
                "",
            ),

            "published_at": (
                published_at.isoformat()
                if isinstance(
                    published_at,
                    datetime,
                )
                else str(published_at)
            ),

            "views": spike.get(
                "views",
                0,
            ),

            "baseline_views": spike.get(
                "baseline_views",
                0,
            ),

            "spike_ratio": spike.get(
                "spike_ratio",
                0,
            ),

            "robust_z": spike.get(
                "robust_z",
                0,
            ),

            "signal": spike.get(
                "signal"
            ),

            "engagement_rate": spike.get(
                "engagement_rate",
                0,
            ),

        })

    print(
        f"Period spike rows: "
        f"{len(period_spike_analysis)}"
    )

    print()

    print(
        "Sample period spike rows:"
    )

    for row in period_spike_analysis[:5]:

        print(
            f"  {row['period']} | "
            f"{row['title']} | "
            f"ratio={row['spike_ratio']}"
        )


    # ========================================================
    # 14. RUN RESEARCH AGENT
    # ========================================================

    print_separator(
        "[14] Running research agent"
    )

    research_result = research_event(

        creator=creator_name,

        event=research_event_data,

        months_before=6,

        months_after=3,

        channel_growth=None,

        period_spike_analysis=(
            period_spike_analysis
        ),

        related_videos=(
            safe_related_videos
        ),

        cross_year_candidates=(
            safe_cross_year_candidates
        ),

        comment_analysis=(
            comment_analysis
        ),

        audience_mode=(
            audience_mode
        ),

    )

    if not research_result:

        raise RuntimeError(
            "Research agent returned "
            "no result."
        )

    if not research_result.get(
        "success",
        False,
    ):

        raise RuntimeError(
            "Research agent failed:\n"
            +
            json.dumps(
                research_result,
                indent=2,
                default=str,
            )
        )

    print(
        "Research agent completed successfully."
    )

    research = (
        research_result.get(
            "research",
            {},
        )
    )

    print()

    print(
        "Event type:",
        research.get(
            "event_type"
        ),
    )

    print(
        "Spike ratio:",
        research.get(
            "spike_signal",
            {}
        ).get(
            "spike_ratio"
        ),
    )

    print(
        "Causal evidence found:",
        research.get(
            "causal_evidence_found"
        ),
    )


    # ========================================================
    # 15. ANALYZE THUMBNAILS
    # ========================================================

    print_separator(
        "[15] Analyzing thumbnails"
    )

    thumbnail_set = {

        "before":
            before_videos,

        "target":
            target,

        "after":
            after_videos,

    }

    thumbnail_analysis = (
        analyze_thumbnail_groups(
            thumbnail_set
        )
    )

    print(
        f"Thumbnail analyses: "
        f"{len(thumbnail_analysis)}"
    )


    # ========================================================
    # 16. BUILD QUANTITATIVE ANALYSIS
    # ========================================================

    print_separator(
        "[16] Preparing final quantitative analysis"
    )

    quantitative_analysis = {

        "target":
            json_safe_value(
                target
            ),

        "before":
            json_safe_value(
                before_videos
            ),

        "after":
            json_safe_value(
                after_videos
            ),

        "related_videos":
            safe_related_videos,

        "spikes":
            safe_spikes,

        "target_spike":
            json_safe_value(
                target_spike
            ),

        "period_spike_analysis":
            json_safe_value(
                period_spike_analysis
            ),

        "audience_timing":
            json_safe_value(
                audience_timing
            ),

        "cross_year_candidates":
            safe_cross_year_candidates,

    }


    # ========================================================
    # 17. RUN FINAL REPORT AGENT
    # ========================================================

    print_separator(
        "[17] Running final report agent"
    )

    final_report = (
        generate_final_report(

            creator=creator_name,

            event=json_safe_value(
                research_event_data
            ),

            quantitative_analysis=(
                quantitative_analysis
            ),

            research=research,

            audience_analysis=(
                json_safe_value(
                    audience_timing
                )
            ),

            cross_year_analysis=(
                safe_cross_year_candidates
            ),

            thumbnail_analysis=(
                json_safe_value(
                    thumbnail_analysis
                )
            ),

        )
    )


    # ========================================================
    # 18. BUILD COMPLETE RESULT
    # ========================================================

    print_separator(
        "[18] Building complete pipeline result"
    )

    output = {

        "creator":
            creator_name,

        "channel":
            json_safe_value(
                channel
            ),

        "target":
            json_safe_value(
                target
            ),

        "target_spike":
            json_safe_value(
                target_spike
            ),

        "spikes":
            safe_spikes,

        "ranked_spikes":
            safe_ranked_spikes,

        "audience_timing":
            json_safe_value(
                audience_timing
            ),

        "related_videos":
            safe_related_videos,

        "cross_year_candidates":
            safe_cross_year_candidates,

        "research":
            json_safe_value(
                research_result
            ),

        "thumbnail_analysis":
            json_safe_value(
                thumbnail_analysis
            ),

        "quantitative_analysis":
            json_safe_value(
                quantitative_analysis
            ),

        "final_report":
            json_safe_value(
                final_report
            ),

    }


    # ========================================================
    # 19. OPTIONAL SAVE
    # ========================================================

    if save_output:

        print_separator(
            "[19] Saving pipeline output"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                output,
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(
            f"Pipeline output saved to: "
            f"{output_path}"
        )


    # ========================================================
    # DONE
    # ========================================================

    print()

    print("=" * 70)

    print(
        "PIPELINE COMPLETED SUCCESSFULLY"
    )

    print("=" * 70)

    return output


# ============================================================
# OPTIONAL STANDALONE TEST
# ============================================================

if __name__ == "__main__":

    try:

        result = run_growth_pipeline(

            channel_id=(
                "UC7_YxT-KID8kRbqZo7MyscQ"
            ),

            creator_name="Markiplier",

            # Leave None to preserve the original
            # strongest-spike behavior.
            target_video_id=None,

            save_output=True,

        )

    except Exception as e:

        print()

        print("=" * 70)

        print(
            "PIPELINE FAILED"
        )

        print("=" * 70)

        print()

        print(
            f"Error: {e}"
        )

        print()

        print(
            "Full traceback:"
        )

        import traceback

        traceback.print_exc()