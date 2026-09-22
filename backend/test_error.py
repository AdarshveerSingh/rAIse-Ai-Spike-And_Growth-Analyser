import json
import os
import traceback
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from app.research.prompts import (
    RESEARCH_AGENT_INSTRUCTIONS,
)

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

from app.analysis.related import (
    find_related_videos,
)

from app.analysis.audience_timing import (
    detect_peak_interaction_year,
)

from app.analysis.cross_year import (
    find_cross_year_candidates,
)

from app.analysis.episodes import (
    analyze_all_growth_events,
    select_important_growth_events,
)


# ============================================================
# ENVIRONMENT
# ============================================================

load_dotenv()

PROJECT_ENDPOINT = os.getenv(
    "PROJECT_ENDPOINT"
)

MODEL_DEPLOYMENT = os.getenv(
    "MODEL_DEPLOYMENT"
)

if not PROJECT_ENDPOINT:
    raise ValueError(
        "PROJECT_ENDPOINT is not set in .env"
    )

if not MODEL_DEPLOYMENT:
    raise ValueError(
        "MODEL_DEPLOYMENT is not set in .env"
    )


# ============================================================
# CONFIG
# ============================================================

CREATOR_NAME = "Markiplier"

CHANNEL_ID = (
    "UC7_YxT-KID8kRbqZo7MyscQ"
)

BEFORE_COUNT = 3
AFTER_COUNT = 3

RELATED_LIMIT = 20
CROSS_YEAR_LIMIT = 5

COMMENT_SAMPLE_SIZE = 100

ROLLING_WINDOW = 10

MIN_SPIKE_RATIO = 3.0
MIN_ROBUST_Z = 2.5


# ============================================================
# AZURE CLIENT
# ============================================================

credential = DefaultAzureCredential()

project = AIProjectClient(
    endpoint=PROJECT_ENDPOINT,
    credential=credential,
)

client = project.get_openai_client()


# ============================================================
# LLM CALL
# ============================================================

def ask_llm_fresh(
    instructions,
    prompt,
):
    """
    Make exactly one fresh LLM request.

    IMPORTANT:
    - No response cache
    - No retry
    - No sleep
    - No automatic retry
    """

    return client.responses.create(
        model=MODEL_DEPLOYMENT,
        instructions=instructions,
        tools=[
            {
                "type": "web_search"
            }
        ],
        input=prompt,
    )


# ============================================================
# JSON HELPERS
# ============================================================

def json_safe_value(value):

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


def json_text(value):

    return json.dumps(
        json_safe_value(value),
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def compact_video(video):

    return {
        "video_id": (
            video.get("id")
            or video.get("video_id")
        ),
        "title": video.get(
            "title"
        ),
        "published_at": video.get(
            "published_at"
        ),
        "views": video.get(
            "views"
        ),
        "likes": video.get(
            "likes"
        ),
        "comments": video.get(
            "comments"
        ),
        "engagement_rate": video.get(
            "engagement_rate"
        ),
        "rolling_baseline_views": video.get(
            "rolling_baseline_views"
        ),
        "rolling_spike_ratio": video.get(
            "rolling_spike_ratio"
        ),
        "robust_z": video.get(
            "robust_z"
        ),
    }


# ============================================================
# DISPLAY
# ============================================================

def separator(title):

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


# ============================================================
# BUILD IMPORTANT EVENTS
# ============================================================

def build_important_events(
    analyzed_videos,
    spikes,
):
    """
    Run the existing growth-event logic.

    Then restore the original spike metrics into the
    growth-event objects.

    This fixes the issue discovered by the previous
    diagnostic where important_events contained:

        views = None
        robust_z = None

    even though the original spike contained them.
    """

    growth_events = (
        analyze_all_growth_events(
            videos=analyzed_videos,
            spikes=spikes,
            before_count=5,
            short_count=5,
            long_count=10,
            retention_threshold=1.5,
        )
    )

    # --------------------------------------------------------
    # Original spike lookup
    # --------------------------------------------------------

    spike_by_video_id = {
        spike["video_id"]: spike
        for spike in spikes
    }

    # --------------------------------------------------------
    # Restore original spike metrics
    # --------------------------------------------------------

    for event in growth_events:

        video_id = event.get(
            "video_id"
        )

        spike = spike_by_video_id.get(
            video_id,
            {},
        )

        if event.get("views") is None:
            event["views"] = spike.get(
                "views"
            )

        if event.get("spike_ratio") is None:
            event["spike_ratio"] = spike.get(
                "spike_ratio"
            )

        if event.get("robust_z") is None:
            event["robust_z"] = spike.get(
                "robust_z"
            )

        if event.get("signal") is None:
            event["signal"] = spike.get(
                "signal"
            )

        if event.get("baseline_views") is None:
            event["baseline_views"] = spike.get(
                "baseline_views"
            )

    # --------------------------------------------------------
    # Select important events
    # --------------------------------------------------------

    important_events = (
        select_important_growth_events(
            growth_events
        )
    )

    return (
        growth_events,
        important_events,
    )


# ============================================================
# BUILD REAL PIPELINE DATA
# ============================================================

def build_pipeline_data():

    separator(
        "[SETUP] Building real pipeline data"
    )

    print(
        "No LLM request is made while building data."
    )

    # ========================================================
    # CHANNEL
    # ========================================================

    print()
    print("Loading channel...")

    channel = get_channel(
        CHANNEL_ID
    )

    uploads_playlist_id = (
        channel[
            "uploads_playlist_id"
        ]
    )

    print(
        f"Channel: "
        f"{channel.get('title', CREATOR_NAME)}"
    )

    # ========================================================
    # VIDEOS
    # ========================================================

    print()
    print("Loading videos...")

    video_ids = get_video_ids(
        uploads_playlist_id
    )

    videos = get_videos(
        video_ids
    )

    print(
        f"Videos loaded: "
        f"{len(videos)}"
    )

    # ========================================================
    # METRICS
    # ========================================================

    prepared_videos = prepare_videos(
        videos
    )

    analyzed_videos = rolling_baseline(
        prepared_videos,
        window=ROLLING_WINDOW,
    )

    # ========================================================
    # SPIKES
    # ========================================================

    spikes = detect_spikes(
        analyzed_videos,
        min_ratio=MIN_SPIKE_RATIO,
        min_robust_z=MIN_ROBUST_Z,
    )

    ranked_spikes = rank_spikes(
        spikes
    )

    if not ranked_spikes:

        raise RuntimeError(
            "No spikes detected."
        )

    print(
        f"Detected spikes: "
        f"{len(spikes)}"
    )

    # ========================================================
    # GROWTH EVENTS
    # ========================================================

    (
        growth_events,
        important_events,
    ) = build_important_events(
        analyzed_videos,
        spikes,
    )

    print(
        f"Growth events: "
        f"{len(growth_events)}"
    )

    print(
        f"Important events: "
        f"{len(important_events)}"
    )

    # ========================================================
    # IMPORTANT EVENTS DEBUG
    # ========================================================

    print()
    print(
        "Important events:"
    )

    for event in important_events:

        print(
            f"  "
            f"{event.get('event_role')} | "
            f"{event.get('event_type')} | "
            f"{event.get('title')} | "
            f"views={event.get('views')} | "
            f"ratio={event.get('spike_ratio')} | "
            f"z={event.get('robust_z')}"
        )

    # ========================================================
    # TARGET
    # ========================================================

    #
    # For this diagnostic we continue using the existing
    # production definition of target:
    #
    #     ranked_spikes[0]
    #
    # We will explicitly check whether that target also
    # exists inside important_events.
    #

    target_spike = (
        ranked_spikes[0]
    )

    target_video_id = (
        target_spike["video_id"]
    )

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
            "Target video not found."
        )

    # ========================================================
    # TARGET EVENT MATCH
    # ========================================================

    target_event = None

    for event in important_events:

        if event.get(
            "video_id"
        ) == target_video_id:

            target_event = event

            break

    if target_event:

        print()
        print(
            "Target event FOUND in important_events."
        )

    else:

        print()
        print(
            "WARNING:"
        )

        print(
            "Target statistical spike is NOT "
            "inside important_events."
        )

        print(
            f"Target video: "
            f"{target.get('title')}"
        )

        print(
            f"Target video ID: "
            f"{target_video_id}"
        )

        print(
            "This is a data-selection inconsistency "
            "we are intentionally measuring."
        )

    # ========================================================
    # BEFORE / AFTER
    # ========================================================

    before_start = max(
        0,
        target_index - BEFORE_COUNT,
    )

    before_videos = analyzed_videos[
        before_start:target_index
    ]

    after_videos = analyzed_videos[
        target_index + 1:
        target_index + 1 + AFTER_COUNT
    ]

    # ========================================================
    # RELATED
    # ========================================================

    print()
    print(
        "Finding related videos..."
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

    # ========================================================
    # COMMENTS
    # ========================================================

    print()
    print(
        "Loading comments..."
    )

    comments = fetch_all_comments(
        target_video_id,
        use_cache=True,
    )

    print(
        f"Comments retrieved: "
        f"{len(comments)}"
    )

    # ========================================================
    # COMMENT ANALYSIS
    #
    # We keep this intentionally lightweight here.
    # The actual research agent independently performs its
    # qualitative comment analysis.
    # ========================================================

    comment_analysis = {
        "comment_count": len(
            comments
        ),
        "sample_size": COMMENT_SAMPLE_SIZE,
        "comments_used_for_analysis": min(
            len(comments),
            COMMENT_SAMPLE_SIZE,
        ),
    }

    # ========================================================
    # COMMENT TRAFFIC
    # ========================================================

    audience_timing = (
        detect_peak_interaction_year(
            comments,
            sample_size=COMMENT_SAMPLE_SIZE,
        )
    )

    # ========================================================
    # AUDIENCE PEAK YEAR
    # ========================================================

    audience_peak_year = None

    if audience_timing:

        audience_peak_year = (
            audience_timing.get(
                "peak_year"
            )
        )

    # ========================================================
    # CROSS YEAR
    # ========================================================

    print()
    print(
        "Finding cross-year candidates..."
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

    # ========================================================
    # PERIOD SPIKE ANALYSIS
    #
    # IMPORTANT:
    # Only important events are included.
    # The original 750 spikes are NOT passed to the LLM.
    # ========================================================

    period_spike_analysis = []

    for event in important_events:

        published_at = event.get(
            "published_at"
        )

        if hasattr(
            published_at,
            "isoformat",
        ):

            published_at_value = (
                published_at.isoformat()
            )

        else:

            published_at_value = (
                published_at
            )

        period = None

        if published_at_value:

            period = str(
                published_at_value
            )[:4]

        period_spike_analysis.append(
            {
                "period": period,

                "event_role": event.get(
                    "event_role"
                ),

                "event_type": event.get(
                    "event_type"
                ),

                "progressive": event.get(
                    "progressive_trajectory"
                ),

                "video_id": event.get(
                    "video_id"
                ),

                "title": event.get(
                    "title"
                ),

                "published_at": (
                    published_at_value
                ),

                "views": event.get(
                    "views"
                ),

                "baseline_views": event.get(
                    "baseline_views"
                ),

                "spike_ratio": event.get(
                    "spike_ratio"
                ),

                "robust_z": event.get(
                    "robust_z"
                ),

                "signal": event.get(
                    "signal"
                ),

                "before_baseline": event.get(
                    "before_baseline"
                ),

                "short_term_baseline": event.get(
                    "short_term_baseline"
                ),

                "long_term_baseline": event.get(
                    "long_term_baseline"
                ),

                "short_term_change": event.get(
                    "short_term_change"
                ),

                "long_term_change": event.get(
                    "long_term_change"
                ),

                "short_term_retained": event.get(
                    "short_term_retained"
                ),

                "long_term_retained": event.get(
                    "long_term_retained"
                ),
            }
        )

    # ========================================================
    # TARGET EVENT DATA
    # ========================================================

    target_event_data = {
        "video_id": target["id"],
        "title": target["title"],
        "published_at": target[
            "published_at"
        ],
        "views": target["views"],
        "likes": target["likes"],
        "comments": target["comments"],
        "engagement_rate": target.get(
            "engagement_rate"
        ),

        "spike_ratio": target_spike.get(
            "spike_ratio"
        ),

        "robust_z": target_spike.get(
            "robust_z"
        ),

        "baseline_views": target_spike.get(
            "baseline_views"
        ),

        "signal": target_spike.get(
            "signal"
        ),
    }

    # Add event classification if available.

    if target_event:

        target_event_data.update(
            {
                "event_role": target_event.get(
                    "event_role"
                ),

                "event_type": target_event.get(
                    "event_type"
                ),

                "progressive_trajectory": (
                    target_event.get(
                        "progressive_trajectory"
                    )
                ),

                "before_baseline": (
                    target_event.get(
                        "before_baseline"
                    )
                ),

                "short_term_baseline": (
                    target_event.get(
                        "short_term_baseline"
                    )
                ),

                "long_term_baseline": (
                    target_event.get(
                        "long_term_baseline"
                    )
                ),

                "short_term_change": (
                    target_event.get(
                        "short_term_change"
                    )
                ),

                "long_term_change": (
                    target_event.get(
                        "long_term_change"
                    )
                ),

                "short_term_retained": (
                    target_event.get(
                        "short_term_retained"
                    )
                ),

                "long_term_retained": (
                    target_event.get(
                        "long_term_retained"
                    )
                ),
            }
        )

    # ========================================================
    # BEFORE / AFTER DATA
    # ========================================================

    before_after_data = {

        "target": compact_video(
            target
        ),

        "target_spike": {
            "video_id": target_spike.get(
                "video_id"
            ),

            "views": target_spike.get(
                "views"
            ),

            "baseline_views": target_spike.get(
                "baseline_views"
            ),

            "spike_ratio": target_spike.get(
                "spike_ratio"
            ),

            "robust_z": target_spike.get(
                "robust_z"
            ),

            "signal": target_spike.get(
                "signal"
            ),
        },

        "before": [
            compact_video(video)
            for video in before_videos
        ],

        "after": [
            compact_video(video)
            for video in after_videos
        ],

        "target_event": (
            target_event_data
        ),
    }

    # ========================================================
    # IMPORTANT EVENTS DATA
    # ========================================================

    important_events_data = []

    for event in important_events:

        important_events_data.append(
            {
                "event_role": event.get(
                    "event_role"
                ),

                "event_type": event.get(
                    "event_type"
                ),

                "progressive_trajectory": (
                    event.get(
                        "progressive_trajectory"
                    )
                ),

                "video_id": event.get(
                    "video_id"
                ),

                "title": event.get(
                    "title"
                ),

                "published_at": event.get(
                    "published_at"
                ),

                "views": event.get(
                    "views"
                ),

                "spike_ratio": event.get(
                    "spike_ratio"
                ),

                "robust_z": event.get(
                    "robust_z"
                ),

                "signal": event.get(
                    "signal"
                ),

                "before_baseline": (
                    event.get(
                        "before_baseline"
                    )
                ),

                "short_term_baseline": (
                    event.get(
                        "short_term_baseline"
                    )
                ),

                "long_term_baseline": (
                    event.get(
                        "long_term_baseline"
                    )
                ),

                "short_term_change": (
                    event.get(
                        "short_term_change"
                    )
                ),

                "long_term_change": (
                    event.get(
                        "long_term_change"
                    )
                ),

                "short_term_retained": (
                    event.get(
                        "short_term_retained"
                    )
                ),

                "long_term_retained": (
                    event.get(
                        "long_term_retained"
                    )
                ),
            }
        )

    # ========================================================
    # RELATED DATA
    # ========================================================

    related_data = []

    for video in related_videos:

        related_data.append(
            compact_video(video)
        )

    # ========================================================
    # CROSS YEAR
    # ========================================================

    cross_year_data = (
        json_safe_value(
            cross_year_candidates
        )
    )

    # ========================================================
    # RETURN
    # ========================================================

    return {

        "creator": CREATOR_NAME,

        "channel": {
            "title": channel.get(
                "title"
            ),
            "channel_id": CHANNEL_ID,
        },

        "target": target_event_data,

        "important_events": {
            "events": important_events_data,
            "count": len(
                important_events_data
            ),
        },

        "before_after": (
            before_after_data
        ),

        "comment_analysis": (
            comment_analysis
        ),

        "comment_traffic": (
            audience_timing
        ),

        "related_videos": (
            related_data
        ),

        "cross_year": (
            cross_year_data
        ),

        "period_spike_analysis": (
            period_spike_analysis
        ),

        "target_event_found": (
            target_event is not None
        ),
    }


# ============================================================
# BUILD ACTUAL RESEARCH PROMPT
# ============================================================

def build_research_prompt(
    data,
    included_components,
):
    """
    Reconstruct the same general prompt structure used by
    the real research agent.

    We intentionally don't call research_event() because that
    would itself perform comment analysis and make the real
    LLM request.
    """

    creator = data[
        "creator"
    ]

    target = data[
        "target"
    ]

    # --------------------------------------------------------
    # Research window
    # --------------------------------------------------------

    published_at = target.get(
        "published_at"
    )

    if isinstance(
        published_at,
        str,
    ):

        try:

            event_date = (
                datetime.fromisoformat(
                    published_at.replace(
                        "Z",
                        "+00:00",
                    )
                )
            )

        except Exception:

            event_date = None

    else:

        event_date = published_at

    if event_date:

        research_window = {
            "start": (
                event_date.replace(
                    year=event_date.year - 1
                ).isoformat()
            ),
            "event": (
                event_date.isoformat()
            ),
            "months_before": 6,
            "months_after": 3,
        }

    else:

        research_window = {
            "months_before": 6,
            "months_after": 3,
        }

    # --------------------------------------------------------
    # Base prompt
    # --------------------------------------------------------

    prompt = f"""
You are researching one major growth event for a
YouTube creator.

Your job is to gather and organize evidence.

You are NOT writing a final polished growth report.

Do not invent sources.

Do not invent dates, views, relationships,
collaborations, causes, or events.

Every factual claim obtained through web research
should have a source.

Internal quantitative analysis supplied in this
prompt is NOT an external source.

============================================================
CREATOR
============================================================

{json_text(creator)}

============================================================
TARGET EVENT
============================================================

{json_text(target)}

============================================================
RESEARCH WINDOW
============================================================

{json_text(research_window)}
"""

    # --------------------------------------------------------
    # Before / after
    # --------------------------------------------------------

    if (
        "before_after"
        in included_components
    ):

        before_after = data[
            "before_after"
        ]

        prompt += f"""

============================================================
VIDEOS BEFORE EVENT
============================================================

{json_text(before_after["before"])}

============================================================
SHORT-TERM FOLLOW-UP VIDEOS
============================================================

{json_text(before_after["after"])}
"""

    # --------------------------------------------------------
    # Important events
    # --------------------------------------------------------

    if (
        "important_events"
        in included_components
    ):

        prompt += f"""

============================================================
IMPORTANT GROWTH EVENTS
============================================================

{json_text(data["important_events"])}
"""

    # --------------------------------------------------------
    # Comment analysis
    # --------------------------------------------------------

    if (
        "comment_analysis"
        in included_components
    ):

        prompt += f"""

============================================================
AUDIENCE COMMENT ANALYSIS
============================================================

{json_text(data["comment_analysis"])}
"""

    # --------------------------------------------------------
    # Comment traffic
    # --------------------------------------------------------

    if (
        "comment_traffic"
        in included_components
    ):

        prompt += f"""

============================================================
AUDIENCE COMMENT TIMING
============================================================

{json_text(data["comment_traffic"])}
"""

    # --------------------------------------------------------
    # Related videos
    # --------------------------------------------------------

    if (
        "related_videos"
        in included_components
    ):

        prompt += f"""

============================================================
RELATED VIDEOS
============================================================

{json_text(data["related_videos"])}
"""

    # --------------------------------------------------------
    # Cross year
    # --------------------------------------------------------

    if (
        "cross_year"
        in included_components
    ):

        prompt += f"""

============================================================
CROSS-YEAR CANDIDATES
============================================================

{json_text(data["cross_year"])}
"""

    # --------------------------------------------------------
    # Period spike analysis
    # --------------------------------------------------------

    if (
        "period_spike_analysis"
        in included_components
    ):

        prompt += f"""

============================================================
IMPORTANT PERIOD SPIKE ANALYSIS
============================================================

{json_text(data["period_spike_analysis"])}
"""

    # --------------------------------------------------------
    # Thumbnails
    #
    # There is intentionally no thumbnail component here yet
    # unless actual cached thumbnail analysis is available.
    # --------------------------------------------------------

    if (
        "thumbnails"
        in included_components
    ):

        prompt += """

============================================================
THUMBNAIL ANALYSIS
============================================================

No thumbnail analysis was included in this
incremental research-agent test.
"""

    # --------------------------------------------------------
    # Research task
    # --------------------------------------------------------

    prompt += """

============================================================
RESEARCH TASK
============================================================

Research this growth event using web search.

Investigate:

1. What happened around the target event.
2. What changed in the content.
3. What changed in the creator's strategy.
4. Whether collaborations or promotion were involved.
5. Whether there was unusual external exposure.
6. Audience reaction where reliable evidence exists.
7. What factors are directly supported by evidence.
8. What factors are only hypotheses.
9. What changed after the event.
10. What did not change.
11. Alternative explanations.
12. Longer-term effects where evidence supports them.

Do not treat internal quantitative analysis as
external evidence.

Do not claim causation without supporting evidence.

Return a concise research result.

Return ONLY valid JSON.
"""

    return prompt


# ============================================================
# TEST ONE STAGE
# ============================================================

def run_stage(
    stage_number,
    stage_name,
    data,
    components,
):
    """
    Send one fresh request.

    Returns True on success.
    Returns False on failure.

    No retry.
    """

    separator(
        f"[TEST {stage_number}] {stage_name}"
    )

    prompt = build_research_prompt(
        data,
        components,
    )

    instructions = (
        RESEARCH_AGENT_INSTRUCTIONS
    )

    instruction_chars = len(
        instructions
    )

    prompt_chars = len(
        prompt
    )

    total_chars = (
        instruction_chars
        + prompt_chars
    )

    # Rough diagnostic estimate.
    estimated_tokens = (
        total_chars // 4
    )

    print(
        f"Components: "
        f"{', '.join(components)}"
    )

    print()
    print(
        "REQUEST SIZE"
    )

    print(
        f"Prompt characters: "
        f"{prompt_chars:,}"
    )

    print(
        f"Instructions characters: "
        f"{instruction_chars:,}"
    )

    print(
        f"Total characters: "
        f"{total_chars:,}"
    )

    print(
        f"Estimated input tokens: "
        f"{estimated_tokens:,}"
    )

    print()
    print(
        "Sending FRESH LLM request..."
    )

    try:

        response = ask_llm_fresh(
            instructions=instructions,
            prompt=prompt,
        )

        output_text = (
            response.output_text
        )

        print()
        print(
            "RESULT: SUCCESS"
        )

        print(
            f"Output characters: "
            f"{len(output_text):,}"
        )

        print()
        print(
            "First 1,000 output characters:"
        )

        print(
            output_text[:1000]
        )

        return {
            "stage": stage_name,
            "success": True,
            "components": components,
            "prompt_characters": prompt_chars,
            "instruction_characters": (
                instruction_chars
            ),
            "total_characters": total_chars,
            "estimated_input_tokens": (
                estimated_tokens
            ),
        }

    except Exception as e:

        error_text = str(e)

        print()
        print(
            "RESULT: FAILED"
        )

        print()
        print(
            error_text
        )

        return {
            "stage": stage_name,
            "success": False,
            "components": components,
            "prompt_characters": prompt_chars,
            "instruction_characters": (
                instruction_chars
            ),
            "total_characters": total_chars,
            "estimated_input_tokens": (
                estimated_tokens
            ),
            "error": error_text,
        }


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        separator(
            "rAIse AI GROWTH ANALYSER"
        )

        print(
            "INCREMENTAL RESEARCH AGENT "
            "RATE-LIMIT TEST"
        )

        print()
        print(
            f"Creator: "
            f"{CREATOR_NAME}"
        )

        print(
            f"Model: "
            f"{MODEL_DEPLOYMENT}"
        )

        print()
        print(
            "LLM responses are NOT cached."
        )

        print(
            "YouTube/data caches ARE allowed."
        )

        print(
            "No retries are performed."
        )

        print(
            "The test stops at the first failed stage."
        )

        # ====================================================
        # BUILD DATA
        # ====================================================

        data = build_pipeline_data()

        # ====================================================
        # DATA SUMMARY
        # ====================================================

        separator(
            "[DATA SUMMARY]"
        )

        components = [
            "target",
            "important_events",
            "before_after",
            "comment_analysis",
            "comment_traffic",
            "related_videos",
            "cross_year",
            "period_spike_analysis",
        ]

        for component in components:

            payload = json_text(
                data[component]
            )

            print(
                f"{component:28}"
                f"{len(payload):>10,} chars"
            )

        # ====================================================
        # VERIFY TARGET / EVENT CONSISTENCY
        # ====================================================

        separator(
            "[CONSISTENCY CHECK]"
        )

        print(
            f"Target event found: "
            f"{data['target_event_found']}"
        )

        print(
            f"Important events: "
            f"{data['important_events']['count']}"
        )

        print(
            f"Period spike rows: "
            f"{len(data['period_spike_analysis'])}"
        )

        # ====================================================
        # INCREMENTAL TESTS
        # ====================================================

        stages = [

            (
                "INSTRUCTIONS ONLY",
                [],
            ),

            (
                "TARGET",
                [
                    "target",
                ],
            ),

            (
                "TARGET + IMPORTANT EVENTS",
                [
                    "target",
                    "important_events",
                ],
            ),

            (
                "TARGET + EVENTS + BEFORE/AFTER",
                [
                    "target",
                    "important_events",
                    "before_after",
                ],
            ),

            (
                "TARGET + EVENTS + BEFORE/AFTER + COMMENTS",
                [
                    "target",
                    "important_events",
                    "before_after",
                    "comment_analysis",
                ],
            ),

            (
                "TARGET + EVENTS + BEFORE/AFTER + COMMENT TRAFFIC",
                [
                    "target",
                    "important_events",
                    "before_after",
                    "comment_analysis",
                    "comment_traffic",
                ],
            ),

            (
                "ADD RELATED VIDEOS",
                [
                    "target",
                    "important_events",
                    "before_after",
                    "comment_analysis",
                    "comment_traffic",
                    "related_videos",
                ],
            ),

            (
                "ADD CROSS-YEAR",
                [
                    "target",
                    "important_events",
                    "before_after",
                    "comment_analysis",
                    "comment_traffic",
                    "related_videos",
                    "cross_year",
                ],
            ),

            (
                "ADD PERIOD SPIKE ANALYSIS",
                [
                    "target",
                    "important_events",
                    "before_after",
                    "comment_analysis",
                    "comment_traffic",
                    "related_videos",
                    "cross_year",
                    "period_spike_analysis",
                ],
            ),

        ]

        results = []

        for index, (
            stage_name,
            stage_components,
        ) in enumerate(
            stages,
            start=1,
        ):

            result = run_stage(
                stage_number=index,
                stage_name=stage_name,
                data=data,
                components=stage_components,
            )

            results.append(
                result
            )

            if not result["success"]:

                print()
                print(
                    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                )

                print(
                    "FIRST FAILURE DETECTED"
                )

                print(
                    "!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!"
                )

                print(
                    f"Stage: "
                    f"{stage_name}"
                )

                print(
                    f"Total characters: "
                    f"{result['total_characters']:,}"
                )

                print()
                print(
                    "Stopping here."
                )

                break

        # ====================================================
        # FINAL SUMMARY
        # ====================================================

        separator(
            "INCREMENTAL TEST SUMMARY"
        )

        for result in results:

            status = (
                "PASS"
                if result["success"]
                else "FAIL"
            )

            print(
                f"{status:4} | "
                f"{result['stage']:<55} | "
                f"{result['total_characters']:>10,} chars | "
                f"{result['estimated_input_tokens']:>8,} tokens"
            )

        # ====================================================
        # FIND FIRST FAILURE
        # ====================================================

        failures = [
            result
            for result in results
            if not result["success"]
        ]

        print()

        if failures:

            first_failure = failures[0]

            print(
                "FIRST FAILURE:"
            )

            print(
                first_failure["stage"]
            )

            print()
            print(
                "This is the component combination "
                "where the actual research-agent "
                "request stopped succeeding."
            )

        else:

            print(
                "ALL INCREMENTAL TESTS SUCCEEDED."
            )

            print()
            print(
                "If the full pipeline still gets "
                "429, the next comparison should "
                "be between this reconstructed "
                "request and the exact production "
                "research_event() request."
            )

        # ====================================================
        # SAVE METADATA ONLY
        # ====================================================

        output_dir = Path(
            "cache"
        )

        output_dir.mkdir(
            parents=True,
            exist_ok=True,
        )

        output_file = (
            output_dir
            / "incremental_research_test.json"
        )

        with open(
            output_file,
            "w",
            encoding="utf-8",
        ) as f:

            json.dump(
                results,
                f,
                indent=2,
                ensure_ascii=False,
            )

        print()
        print(
            f"Test metadata saved to:"
        )

        print(
            output_file
        )

        print()
        print(
            "LLM responses were NOT saved."
        )

    except Exception as e:

        separator(
            "DIAGNOSTIC TEST FAILED"
        )

        print(
            str(e)
        )

        print()

        traceback.print_exc()


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()