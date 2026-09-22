import json
import time
import traceback
from datetime import datetime
from urllib.parse import urlparse

from app.youtube.client import (
    get_channel,
    get_video_ids,
    get_videos,
)

from app.youtube.comments import (
    fetch_all_comments,
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

from app.analysis.episodes import (
    analyze_all_growth_events,
    select_important_growth_events,
)

from app.analysis.related import (
    find_related_videos,
)

from app.analysis.audience_timing import (
    detect_peak_interaction_year,
)

from app.analysis.cross_year import (
    find_cross_year_candidates,
)

from app.research.agent import (
    research_event,
)


# ============================================================
# CONFIGURATION
# ============================================================
#
# These are ALGORITHM SETTINGS, not hardcoded data.
#
# No creator name.
# No channel ID.
# No video ID.
# No video title.
# No views.
# No dates.
# No related scores.
# No candidate scores.
#
# All of those come from the YouTube API / Python analysis.
# ============================================================

BEFORE_COUNT = 5
SHORT_COUNT = 5
LONG_COUNT = 10

ROLLING_WINDOW = 10

MIN_SPIKE_RATIO = 3.0
MIN_ROBUST_Z = 2.5

RETENTION_THRESHOLD = 1.5

RELATED_LIMIT = 20
CROSS_YEAR_LIMIT = 5

COMMENT_SAMPLE_SIZE = 100

MONTHS_BEFORE = 6
MONTHS_AFTER = 3


# ============================================================
# HELPERS
# ============================================================

def json_safe_value(value):
    """
    Convert Python values into JSON-safe values.
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
    return json_safe_value(dict(video))


def print_separator(title):
    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


def extract_channel_id(user_input):
    """
    Accept either:

        UCxxxxxxxxxxxxxxxxxxxxxx

    or a YouTube channel URL such as:

        https://www.youtube.com/channel/UCxxxxxxxx

    For @handles, this function returns None because the current
    get_channel() implementation expects a channel ID.
    """

    value = user_input.strip()

    if not value:
        raise ValueError(
            "Channel URL or channel ID cannot be empty."
        )

    # Direct channel ID
    if value.startswith("UC") and "/" not in value:
        return value

    parsed = urlparse(value)

    if parsed.netloc.lower() not in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
    }:
        raise ValueError(
            "Please provide a valid YouTube channel URL or channel ID."
        )

    path_parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    if (
        len(path_parts) >= 2
        and path_parts[0] == "channel"
    ):
        return path_parts[1]

    raise ValueError(
        "The supplied URL does not contain a /channel/CHANNEL_ID path.\n"
        "Please provide the channel URL in channel-ID form or the channel ID."
    )


def find_video_by_id(videos, video_id):
    for video in videos:
        if video.get("id") == video_id:
            return video

    return None


def build_before_videos(
    analyzed_videos,
    target_index,
):
    start = max(
        0,
        target_index - BEFORE_COUNT,
    )

    return analyzed_videos[
        start:target_index
    ]


def build_short_videos(
    analyzed_videos,
    target_index,
):
    start = target_index + 1

    return analyzed_videos[
        start:start + SHORT_COUNT
    ]


def build_long_videos(
    analyzed_videos,
    target_index,
):
    start = target_index + 1 + SHORT_COUNT

    return analyzed_videos[
        start:start + LONG_COUNT
    ]


def build_period_spike_analysis(
    important_events,
    spikes,
):
    """
    Build the period spike data entirely from the actual
    deterministic growth-event calculations.

    Nothing is manually supplied here.
    """

    rows = []

    spike_by_video_id = {
        spike.get("video_id"): spike
        for spike in spikes
    }

    for event in important_events:

        published_at = event.get(
            "published_at"
        )

        if isinstance(
            published_at,
            datetime,
        ):
            period = published_at.year
            published_at_value = (
                published_at.isoformat()
            )

        else:
            try:
                parsed = datetime.fromisoformat(
                    str(published_at).replace(
                        "Z",
                        "+00:00",
                    )
                )

                period = parsed.year
                published_at_value = (
                    parsed.isoformat()
                )

            except (
                ValueError,
                TypeError,
            ):
                period = None
                published_at_value = str(
                    published_at
                )

        source_spike = (
            spike_by_video_id.get(
                event.get("video_id"),
                {},
            )
        )

        rows.append(
            {
                "period": period,

                "event_role": event.get(
                    "event_role"
                ),

                "event_type": event.get(
                    "event_type"
                ),

                "progressive": event.get(
                    "progressive_trajectory",
                    False,
                ),

                "video_id": event.get(
                    "video_id",
                    "",
                ),

                "title": event.get(
                    "title",
                    "",
                ),

                "published_at":
                    published_at_value,

                "views": event.get(
                    "spike_views",
                    source_spike.get(
                        "views",
                        0,
                    ),
                ),

                "baseline_views":
                    source_spike.get(
                        "baseline_views",
                        event.get(
                            "before_baseline",
                            0,
                        ),
                    ),

                "spike_ratio": event.get(
                    "spike_ratio",
                    source_spike.get(
                        "spike_ratio",
                        0,
                    ),
                ),

                "robust_z":
                    source_spike.get(
                        "robust_z"
                    ),

                "signal":
                    source_spike.get(
                        "signal"
                    ),

                "before_baseline":
                    event.get(
                        "before_baseline"
                    ),

                "short_term_baseline":
                    event.get(
                        "short_term_baseline"
                    ),

                "long_term_baseline":
                    event.get(
                        "long_term_baseline"
                    ),

                "short_term_change":
                    event.get(
                        "short_term_change"
                    ),

                "long_term_change":
                    event.get(
                        "long_term_change"
                    ),

                "short_term_retained":
                    event.get(
                        "short_term_retained"
                    ),

                "long_term_retained":
                    event.get(
                        "long_term_retained"
                    ),
            }
        )

    return rows


# ============================================================
# MAIN PIPELINE
# ============================================================

def main():

    try:

        # ====================================================
        # 0. USER INPUT
        # ====================================================

        print_separator(
            "YouTube Growth & Spike Analyzer"
        )

        channel_input = input(
            "\nEnter YouTube channel URL or channel ID: "
        ).strip()

        channel_id = extract_channel_id(
            channel_input
        )

        print()
        print(
            f"Resolved channel ID: {channel_id}"
        )


        # ====================================================
        # 1. LOAD CHANNEL
        # ====================================================

        print_separator(
            "[1] Loading channel"
        )

        channel = get_channel(
            channel_id
        )

        creator_name = channel.get(
            "title",
            "Unknown Creator",
        )

        uploads_playlist_id = channel.get(
            "uploads_playlist_id"
        )

        if not uploads_playlist_id:
            raise RuntimeError(
                "YouTube channel did not provide "
                "an uploads playlist ID."
            )

        print(
            f"Creator: {creator_name}"
        )

        print(
            f"Channel ID: {channel.get('id')}"
        )

        print(
            f"Uploads playlist: "
            f"{uploads_playlist_id}"
        )


        # ====================================================
        # 2. LOAD ALL VIDEOS
        # ====================================================

        print_separator(
            "[2] Loading YouTube videos"
        )

        video_ids = get_video_ids(
            uploads_playlist_id
        )

        print(
            f"Video IDs found: "
            f"{len(video_ids)}"
        )

        if not video_ids:
            raise RuntimeError(
                "No videos were found for this channel."
            )

        videos = get_videos(
            video_ids
        )

        print(
            f"Videos loaded: "
            f"{len(videos)}"
        )

        if not videos:
            raise RuntimeError(
                "YouTube returned no video data."
            )


        # ====================================================
        # 3. PREPARE METRICS
        # ====================================================

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


        # ====================================================
        # 4. ROLLING BASELINE
        # ====================================================

        print_separator(
            "[4] Calculating rolling baselines"
        )

        analyzed_videos = rolling_baseline(
            prepared_videos,
            window=ROLLING_WINDOW,
        )

        print(
            f"Videos analyzed: "
            f"{len(analyzed_videos)}"
        )


        # ====================================================
        # 5. DETECT SPIKES
        # ====================================================

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
            f"Spikes detected: "
            f"{len(spikes)}"
        )

        if not ranked_spikes:
            raise RuntimeError(
                "No spikes were detected."
            )

        print("\nTop calculated spikes:")

        for spike in ranked_spikes[:10]:

            print()

            print(
                spike.get(
                    "title",
                    "",
                )
            )

            print(
                f"  views: "
                f"{spike.get('views', 0):,}"
            )

            print(
                f"  baseline: "
                f"{spike.get('baseline_views')}"
            )

            print(
                f"  ratio: "
                f"{spike.get('spike_ratio')}"
            )

            print(
                f"  robust_z: "
                f"{spike.get('robust_z')}"
            )

            print(
                f"  signal: "
                f"{spike.get('signal')}"
            )


        # ====================================================
        # 6. ANALYZE ALL GROWTH EVENTS
        # ====================================================

        print_separator(
            "[6] Analyzing growth events"
        )

        growth_events = (
            analyze_all_growth_events(
                videos=analyzed_videos,
                spikes=spikes,
                before_count=BEFORE_COUNT,
                short_count=SHORT_COUNT,
                long_count=LONG_COUNT,
                retention_threshold=RETENTION_THRESHOLD,
            )
        )

        print(
            f"Growth events calculated: "
            f"{len(growth_events)}"
        )


        # ====================================================
        # 7. SELECT IMPORTANT EVENTS
        # ====================================================

        print_separator(
            "[7] Selecting important events"
        )

        important_events = (
            select_important_growth_events(
                growth_events
            )
        )

        print(
            f"Important events: "
            f"{len(important_events)}"
        )

        for event in important_events:

            print()

            print(
                f"[{event.get('event_role')}] "
                f"{event.get('title')}"
            )

            print(
                f"  type: "
                f"{event.get('event_type')}"
            )

            print(
                f"  views: "
                f"{event.get('spike_views', 0):,}"
            )

            print(
                f"  ratio: "
                f"{event.get('spike_ratio')}"
            )

            print(
                f"  short retained: "
                f"{event.get('short_term_retained')}"
            )

            print(
                f"  long retained: "
                f"{event.get('long_term_retained')}"
            )

            print(
                f"  progressive: "
                f"{event.get('progressive_trajectory')}"
            )


        # ====================================================
        # 8. SELECT STRONGEST CALCULATED EVENT
        # ====================================================

        print_separator(
            "[8] Selecting target event"
        )

        target_spike = ranked_spikes[0]

        target_video_id = target_spike[
            "video_id"
        ]

        target = find_video_by_id(
            analyzed_videos,
            target_video_id,
        )

        if target is None:
            raise RuntimeError(
                "The detected spike could not "
                "be found in analyzed videos."
            )

        target_index = next(
            index
            for index, video
            in enumerate(analyzed_videos)
            if video.get("id")
            == target_video_id
        )

        print(
            f"Target: "
            f"{target.get('title')}"
        )

        print(
            f"Video ID: "
            f"{target.get('id')}"
        )

        print(
            f"Published: "
            f"{target.get('published_at')}"
        )

        print(
            f"Views: "
            f"{target.get('views', 0):,}"
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


        # ====================================================
        # 9. BUILD REAL BEFORE / SHORT / LONG WINDOWS
        # ====================================================

        print_separator(
            "[9] Building growth-event windows"
        )

        before_videos = build_before_videos(
            analyzed_videos,
            target_index,
        )

        short_videos = build_short_videos(
            analyzed_videos,
            target_index,
        )

        long_videos = build_long_videos(
            analyzed_videos,
            target_index,
        )

        print(
            f"Before videos: "
            f"{len(before_videos)}"
        )

        print(
            f"Short-term videos: "
            f"{len(short_videos)}"
        )

        print(
            f"Long-term videos: "
            f"{len(long_videos)}"
        )


        # ====================================================
        # 10. FIND REAL RELATED VIDEOS
        # ====================================================

        print_separator(
            "[10] Calculating related videos"
        )

        related_videos = find_related_videos(
            target_video=target,
            videos=analyzed_videos,
            threshold=0.20,
        )

        related_videos = related_videos[
            :RELATED_LIMIT
        ]

        print(
            f"Related videos: "
            f"{len(related_videos)}"
        )

        for video in related_videos[:10]:

            print()

            print(
                video.get(
                    "title",
                    "",
                )
            )

            print(
                f"  related_score: "
                f"{video.get('related_score')}"
            )

            print(
                f"  title_similarity: "
                f"{video.get('title_similarity')}"
            )

            print(
                f"  series_identity: "
                f"{video.get('series_identity')}"
            )

            print(
                f"  numbered_series_score: "
                f"{video.get('numbered_series_score')}"
            )

            print(
                f"  temporal_similarity: "
                f"{video.get('temporal_similarity')}"
            )

            print(
                f"  content_type_similarity: "
                f"{video.get('content_type_similarity')}"
            )


        # ====================================================
        # 11. LOAD REAL COMMENTS
        # ====================================================

        print_separator(
            "[11] Loading audience comments"
        )

        comments = fetch_all_comments(
            target_video_id,
            use_cache=True,
        )

        print(
            f"Comments retrieved: "
            f"{len(comments)}"
        )


        # ====================================================
        # 12. CALCULATE AUDIENCE TIMING
        # ====================================================

        print_separator(
            "[12] Calculating audience timing"
        )

        audience_timing = (
            detect_peak_interaction_year(
                comments,
                sample_size=COMMENT_SAMPLE_SIZE,
            )
        )

        print(
            json.dumps(
                json_safe_value(
                    audience_timing
                ),
                indent=2,
                ensure_ascii=False,
            )
        )

        audience_peak_year = (
            audience_timing.get(
                "peak_year"
            )
            if audience_timing
            else None
        )

        # If the comment sample cannot establish a peak year,
        # derive the fallback from the actual target video's
        # publication date.
        if audience_peak_year is None:

            published_at = target[
                "published_at"
            ]

            if isinstance(
                published_at,
                datetime,
            ):
                audience_peak_year = (
                    published_at.year
                )

            else:
                parsed = datetime.fromisoformat(
                    str(published_at).replace(
                        "Z",
                        "+00:00",
                    )
                )

                audience_peak_year = (
                    parsed.year
                )

        print(
            f"Audience peak year: "
            f"{audience_peak_year}"
        )


        # ====================================================
        # 13. CALCULATE CROSS-YEAR CANDIDATES
        # ====================================================

        print_separator(
            "[13] Calculating cross-year candidates"
        )

        cross_year_candidates = (
            find_cross_year_candidates(
                videos=analyzed_videos,
                spikes=spikes,
                related_videos=related_videos,
                target_video=target,
                audience_peak_year=(
                    audience_peak_year
                ),
                max_candidates=CROSS_YEAR_LIMIT,
            )
        )

        print(
            f"Cross-year candidates: "
            f"{len(cross_year_candidates)}"
        )

        for candidate in cross_year_candidates:

            print()

            print(
                candidate.get(
                    "title",
                    "",
                )
            )

            print(
                f"  candidate_score: "
                f"{candidate.get('candidate_score')}"
            )

            print(
                f"  related_score: "
                f"{candidate.get('related_score', candidate.get('existing_related_score'))}"
            )

            print(
                f"  relationship: "
                f"{candidate.get('relationship')}"
            )

            print(
                f"  performance_score: "
                f"{candidate.get('performance_score')}"
            )

            print(
                f"  series_identity: "
                f"{candidate.get('series_identity')}"
            )


        # ====================================================
        # 14. BUILD ACTUAL RESEARCH EVENT
        # ====================================================

        print_separator(
            "[14] Preparing research input"
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
            for video in short_videos
        ]

        research_event_data[
            "long_videos"
        ] = [
            json_safe_video(video)
            for video in long_videos
        ]

        # Add the actual growth-event calculation
        # corresponding to this target if available.

        matching_events = [
            event
            for event in growth_events
            if event.get("video_id")
            == target_video_id
        ]

        if matching_events:

            research_event_data[
                "growth_event"
            ] = json_safe_value(
                matching_events[0]
            )


        # ====================================================
        # 15. BUILD REAL SPIKE ANALYSIS
        # ====================================================

        period_spike_analysis = (
            build_period_spike_analysis(
                important_events,
                spikes,
            )
        )

        print(
            f"Important calculated event rows: "
            f"{len(period_spike_analysis)}"
        )


        # ====================================================
        # 16. CONVERT EVERYTHING TO JSON-SAFE DATA
        # ====================================================

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

        safe_growth_events = (
            json_safe_value(
                growth_events
            )
        )

        safe_important_events = (
            json_safe_value(
                important_events
            )
        )


        # ====================================================
        # 17. RESEARCH AGENT
        # ====================================================

        print_separator(
            "[15] Running research agent"
        )

        print(
            "Waiting before research request..."
        )

        # Keep this if you are hitting Foundry 429s.
        time.sleep(60)

        research_result = research_event(
            creator=creator_name,

            event=research_event_data,

            months_before=MONTHS_BEFORE,

            months_after=MONTHS_AFTER,

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
        )

        if not research_result:

            raise RuntimeError(
                "Research agent returned no result."
            )

        if not research_result.get(
            "success",
            False,
        ):

            raise RuntimeError(
                "Research agent failed:\n"
                + json.dumps(
                    research_result,
                    indent=2,
                    default=str,
                )
            )

        research = research_result.get(
            "research",
            {},
        )

        print(
            "Research agent completed."
        )


        # ====================================================
        # 18. PRINT FINAL RESEARCH RESULT
        # ====================================================

        print_separator(
            "[16] FINAL RESEARCH RESULT"
        )

        print(
            json.dumps(
                research,
                indent=2,
                ensure_ascii=False,
                default=str,
            )
        )


        # ====================================================
        # 19. SAVE COMPLETE DETERMINISTIC + AI RESULT
        # ====================================================

        print_separator(
            "[17] Saving result"
        )

        output = {

            # Actual YouTube API data
            "channel": json_safe_value(
                channel
            ),

            # Actual target selected from spike detector
            "target": json_safe_value(
                target
            ),

            # Actual spike detector output
            "target_spike": json_safe_value(
                target_spike
            ),

            # Actual Python spike calculations
            "spikes": safe_spikes,

            "ranked_spikes":
                safe_ranked_spikes,

            # Actual growth-event calculations
            "growth_events":
                safe_growth_events,

            "important_events":
                safe_important_events,

            # Actual related-video calculations
            "related_videos":
                safe_related_videos,

            # Actual comment-derived audience analysis
            "audience_timing":
                json_safe_value(
                    audience_timing
                ),

            # Actual cross-year deterministic analysis
            "cross_year_candidates":
                safe_cross_year_candidates,

            # Actual research-agent output
            "research":
                json_safe_value(
                    research_result
                ),
        }

        output_path = (
            "cache/full_pipeline_result.json"
        )

        with open(
            output_path,
            "w",
            encoding="utf-8",
        ) as file:

            json.dump(
                output,
                file,
                indent=2,
                ensure_ascii=False,
                default=str,
            )

        print(
            f"Saved: {output_path}"
        )


    except Exception:

        print_separator(
            "PIPELINE ERROR"
        )

        traceback.print_exc()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()