import json
import os
import traceback
from datetime import datetime

from dotenv import load_dotenv

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential

from app.research.prompts import RESEARCH_AGENT_INSTRUCTIONS

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

ROLLING_WINDOW = 10

MIN_SPIKE_RATIO = 3.0
MIN_ROBUST_Z = 2.5

BEFORE_COUNT = 3
AFTER_COUNT = 3

RELATED_LIMIT = 20
CROSS_YEAR_LIMIT = 5

COMMENT_SAMPLE_SIZE = 100


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
# HELPERS
# ============================================================

def safe_json(value):

    if isinstance(value, datetime):
        return value.isoformat()

    if isinstance(value, dict):

        return {
            key: safe_json(val)
            for key, val in value.items()
        }

    if isinstance(value, list):

        return [
            safe_json(item)
            for item in value
        ]

    if isinstance(value, tuple):

        return [
            safe_json(item)
            for item in value
        ]

    return value


def json_text(value):

    return json.dumps(
        safe_json(value),
        indent=2,
        ensure_ascii=False,
        default=str,
    )


def separator(title):

    print()
    print("=" * 80)
    print(title)
    print("=" * 80)


# ============================================================
# FORMAT VIDEO
# ============================================================

def format_video(video):

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

        "rolling_baseline_views": (
            video.get(
                "rolling_baseline_views"
            )
        ),

        "rolling_spike_ratio": (
            video.get(
                "rolling_spike_ratio"
            )
        ),

        "robust_z": video.get(
            "robust_z"
        ),

        "signal": video.get(
            "signal"
        ),
    }


# ============================================================
# BUILD GROWTH EVENTS
# ============================================================

def build_growth_events(
    analyzed_videos,
    spikes,
):

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

    spike_lookup = {
        spike["video_id"]: spike
        for spike in spikes
    }

    # --------------------------------------------------------
    # Restore original spike metrics.
    # --------------------------------------------------------

    for event in growth_events:

        video_id = event.get(
            "video_id"
        )

        spike = spike_lookup.get(
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

        if event.get("baseline_views") is None:
            event["baseline_views"] = spike.get(
                "baseline_views"
            )

        if event.get("signal") is None:
            event["signal"] = spike.get(
                "signal"
            )

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
# BUILD DATA
# ============================================================

def build_data():

    separator(
        "BUILDING REAL PRODUCTION DATA"
    )

    # --------------------------------------------------------
    # Channel
    # --------------------------------------------------------

    print(
        "Loading channel..."
    )

    channel = get_channel(
        CHANNEL_ID
    )

    uploads_playlist_id = (
        channel[
            "uploads_playlist_id"
        ]
    )

    # --------------------------------------------------------
    # Videos
    # --------------------------------------------------------

    print(
        "Loading videos..."
    )

    video_ids = get_video_ids(
        uploads_playlist_id
    )

    videos = get_videos(
        video_ids
    )

    print(
        f"Videos: {len(videos)}"
    )

    # --------------------------------------------------------
    # Metrics
    # --------------------------------------------------------

    prepared = prepare_videos(
        videos
    )

    analyzed = rolling_baseline(
        prepared,
        window=ROLLING_WINDOW,
    )

    # --------------------------------------------------------
    # Spikes
    # --------------------------------------------------------

    spikes = detect_spikes(
        analyzed,
        min_ratio=MIN_SPIKE_RATIO,
        min_robust_z=MIN_ROBUST_Z,
    )

    ranked_spikes = rank_spikes(
        spikes
    )

    print(
        f"Spikes: {len(spikes)}"
    )

    if not ranked_spikes:

        raise RuntimeError(
            "No spikes detected."
        )

    # --------------------------------------------------------
    # Growth events
    # --------------------------------------------------------

    (
        growth_events,
        important_events,
    ) = build_growth_events(
        analyzed,
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

    # --------------------------------------------------------
    # Production target
    #
    # This intentionally matches test_full_pipeline.py:
    #
    # ranked_spikes[0]
    # --------------------------------------------------------

    target_spike = (
        ranked_spikes[0]
    )

    target_video_id = (
        target_spike["video_id"]
    )

    target = None
    target_index = None

    for index, video in enumerate(
        analyzed
    ):

        if video["id"] == target_video_id:

            target = video
            target_index = index

            break

    if target is None:

        raise RuntimeError(
            "Target video not found."
        )

    print()
    print(
        "PRODUCTION TARGET"
    )

    print(
        f"Title: "
        f"{target['title']}"
    )

    print(
        f"Video ID: "
        f"{target_video_id}"
    )

    print(
        f"Views: "
        f"{target['views']:,}"
    )

    print(
        f"Spike ratio: "
        f"{target_spike.get('spike_ratio')}"
    )

    print(
        f"Robust Z: "
        f"{target_spike.get('robust_z')}"
    )

    # --------------------------------------------------------
    # Target growth event
    # --------------------------------------------------------

    target_growth_event = None

    for event in important_events:

        if (
            event.get("video_id")
            == target_video_id
        ):

            target_growth_event = event

            break

    print()

    if target_growth_event:

        print(
            "Target growth event FOUND."
        )

    else:

        print(
            "WARNING: Target growth event "
            "NOT FOUND in important events."
        )

    # --------------------------------------------------------
    # Before
    # --------------------------------------------------------

    before_start = max(
        0,
        target_index - BEFORE_COUNT,
    )

    before_videos = analyzed[
        before_start:target_index
    ]

    # --------------------------------------------------------
    # After
    # --------------------------------------------------------

    after_videos = analyzed[
        target_index + 1:
        target_index + 1 + AFTER_COUNT
    ]

    # --------------------------------------------------------
    # Related
    # --------------------------------------------------------

    print()
    print(
        "Finding related videos..."
    )

    related_videos = find_related_videos(
        target_video=target,
        videos=analyzed,
        threshold=0.20,
    )

    related_videos = related_videos[
        :RELATED_LIMIT
    ]

    print(
        f"Related videos: "
        f"{len(related_videos)}"
    )

    # --------------------------------------------------------
    # Comments
    # --------------------------------------------------------

    print()
    print(
        "Loading comments..."
    )

    comments = fetch_all_comments(
        target_video_id,
        use_cache=True,
    )

    print(
        f"Comments: "
        f"{len(comments)}"
    )

    # --------------------------------------------------------
    # Comment analysis
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Audience timing
    # --------------------------------------------------------

    audience_signal = (
        detect_peak_interaction_year(
            comments,
            sample_size=COMMENT_SAMPLE_SIZE,
        )
    )

    # --------------------------------------------------------
    # Audience peak year
    # --------------------------------------------------------

    audience_peak_year = None

    if audience_signal:

        audience_peak_year = (
            audience_signal.get(
                "peak_year"
            )
        )

    print(
        f"Audience peak year: "
        f"{audience_peak_year}"
    )

    # --------------------------------------------------------
    # Cross-year candidates
    # --------------------------------------------------------

    print()
    print(
        "Finding cross-year candidates..."
    )

    cross_year_candidates = (
        find_cross_year_candidates(
            videos=analyzed,
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

    # --------------------------------------------------------
    # Important period spike rows
    #
    # Same optimization as the current production
    # pipeline: 5 important events rather than all 750.
    # --------------------------------------------------------

    period_spike_analysis = []

    for event in important_events:

        published_at = event.get(
            "published_at"
        )

        if hasattr(
            published_at,
            "isoformat",
        ):

            published_at = (
                published_at.isoformat()
            )

        period = None

        if published_at:

            period = str(
                published_at
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

                "published_at": published_at,

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

    # --------------------------------------------------------
    # Target event object
    # --------------------------------------------------------

    target_event = {
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

    if target_growth_event:

        target_event.update(
            {
                "event_role": (
                    target_growth_event.get(
                        "event_role"
                    )
                ),

                "event_type": (
                    target_growth_event.get(
                        "event_type"
                    )
                ),

                "progressive_trajectory": (
                    target_growth_event.get(
                        "progressive_trajectory"
                    )
                ),

                "before_baseline": (
                    target_growth_event.get(
                        "before_baseline"
                    )
                ),

                "short_term_baseline": (
                    target_growth_event.get(
                        "short_term_baseline"
                    )
                ),

                "long_term_baseline": (
                    target_growth_event.get(
                        "long_term_baseline"
                    )
                ),

                "short_term_change": (
                    target_growth_event.get(
                        "short_term_change"
                    )
                ),

                "long_term_change": (
                    target_growth_event.get(
                        "long_term_change"
                    )
                ),

                "short_term_retained": (
                    target_growth_event.get(
                        "short_term_retained"
                    )
                ),

                "long_term_retained": (
                    target_growth_event.get(
                        "long_term_retained"
                    )
                ),
            }
        )

    # --------------------------------------------------------
    # Research event data
    #
    # This mirrors the object sent by test_full_pipeline.
    # --------------------------------------------------------

    research_event_data = {

        **target_event,

        "before_videos": [
            format_video(video)
            for video in before_videos
        ],

        "short_videos": [
            format_video(video)
            for video in after_videos
        ],

        "long_videos": [
            format_video(video)
            for video in related_videos
        ],
    }

    # --------------------------------------------------------
    # Important events
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Return
    # --------------------------------------------------------

    return {

        "creator": CREATOR_NAME,

        "target": target_event,

        "research_event": research_event_data,

        "important_events": (
            important_events_data
        ),

        "before_videos": [
            format_video(video)
            for video in before_videos
        ],

        "short_videos": [
            format_video(video)
            for video in after_videos
        ],

        "long_videos": [
            format_video(video)
            for video in related_videos
        ],

        "comment_analysis": (
            comment_analysis
        ),

        "audience_signal": (
            audience_signal
        ),

        "period_spike_analysis": (
            period_spike_analysis
        ),

        "related_videos": (
            related_videos
        ),

        "cross_year_candidates": (
            cross_year_candidates
        ),

        "channel_growth": [],
    }


# ============================================================
# FORMAT RESEARCH CONTEXT
# ============================================================

def format_research_context(
    data
):
    """
    This is deliberately close to the context passed into
    research_event():

        cross_year_context
        cross_year_candidates_context
        before_videos
        short_videos
        long_videos
    """

    before_videos = data[
        "before_videos"
    ]

    short_videos = data[
        "short_videos"
    ]

    long_videos = data[
        "long_videos"
    ]

    cross_year_context = {
        "audience_signal": (
            data["audience_signal"]
        ),

        "channel_growth": (
            data["channel_growth"]
        ),

        "period_spike_analysis": (
            data["period_spike_analysis"]
        ),

        "related_videos": (
            data["related_videos"]
        ),
    }

    cross_year_candidates_context = (
        data["cross_year_candidates"]
    )

    return {
        "before_videos": before_videos,
        "short_videos": short_videos,
        "long_videos": long_videos,
        "cross_year_context": (
            cross_year_context
        ),
        "cross_year_candidates_context": (
            cross_year_candidates_context
        ),
    }


# ============================================================
# BUILD EXACT PRODUCTION-STYLE PROMPT
# ============================================================

def build_exact_research_prompt(
    data
):

    event = data[
        "research_event"
    ]

    context = format_research_context(
        data
    )

    creator = data[
        "creator"
    ]

    # --------------------------------------------------------
    # Research window
    # --------------------------------------------------------

    published_at = event.get(
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

        # ----------------------------------------------------
        # Use month arithmetic approximately here.
        #
        # The important point for this diagnostic is that
        # the request structure matches production.
        # ----------------------------------------------------

        research_window = {
            "start": (
                event_date.isoformat()
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
    # EXACT PRODUCTION-STYLE PROMPT
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

Internal quantitative analysis supplied in this prompt
is NOT an external source.

============================================================
CREATOR
============================================================

{json_text(creator)}

============================================================
TARGET EVENT
============================================================

{json_text(event)}

============================================================
RESEARCH WINDOW
============================================================

{json_text(research_window)}

The research window is:

6 months before the target event
→ target event
→ 3 months after the target event.

Focus external research primarily on this period unless
later evidence is necessary to understand the event.

============================================================
VIDEOS BEFORE EVENT
============================================================

{json_text(context["before_videos"])}

============================================================
SHORT-TERM FOLLOW-UP VIDEOS
============================================================

{json_text(context["short_videos"])}

============================================================
LONG-TERM FOLLOW-UP VIDEOS
============================================================

{json_text(context["long_videos"])}

============================================================
AUDIENCE COMMENT SAMPLE
============================================================

The following is a small qualitative sample of comments.

It is NOT the entire audience.

Do not treat this sample as a representative census
of all viewers.

{json_text(data["comment_analysis"])}

============================================================
AUDIENCE TIMING SIGNAL
============================================================

{json_text(data["audience_signal"])}

============================================================
CROSS-YEAR CONTEXT
============================================================

{json_text(context["cross_year_context"])}

============================================================
CROSS-YEAR CANDIDATES
============================================================

{json_text(context["cross_year_candidates_context"])}

============================================================
IMPORTANT GROWTH EVENTS
============================================================

{json_text(data["important_events"])}

============================================================
RESEARCH OBJECTIVE
============================================================

Research this specific growth event.

Investigate:

1. What happened around the spike.

2. What changed in the content.

3. What changed in the creator's strategy.

4. Whether collaborations were involved.

5. Whether promotion or unusual exposure
   was involved.

6. What happened to the creator after the spike.

7. Audience reaction where reliable evidence exists.

8. What factors are directly supported by evidence.

9. What factors are only hypotheses.

10. What changed.

11. What did not change.

12. Alternative explanations.

13. Patterns across years where evidence
    supports further investigation.

IMPORTANT:

Do NOT rely only on the quantitative data supplied
in this prompt.

Use actual web research.

Do NOT invent sources.

Do NOT claim that comments, fan requests,
sharing, promotion, algorithmic exposure,
collaborations or audience sentiment existed
unless you found evidence for them.

Every factual research finding should have
a source attached.

The supplied quantitative analysis is
INTERNAL_ANALYSIS.

It is not an external web source.

If something is plausible but unsupported,
classify it as HYPOTHESIS.

Do not turn unsupported assumptions into
factual findings.

Keep the result concise.

Prefer 3-5 high-value findings.

Do not write a biography of the creator.

Focus on explaining this specific growth event.

Return ONLY valid JSON.
"""

    return prompt


# ============================================================
# REQUEST SIZE
# ============================================================

def print_request_size(
    mode,
    instructions,
    prompt,
):

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

    estimated_tokens = (
        total_chars // 4
    )

    print()
    print(
        "REQUEST SIZE"
    )

    print(
        f"Mode:                  {mode}"
    )

    print(
        f"Instructions:          "
        f"{instruction_chars:,} chars"
    )

    print(
        f"Input prompt:          "
        f"{prompt_chars:,} chars"
    )

    print(
        f"Total:                 "
        f"{total_chars:,} chars"
    )

    print(
        f"Estimated input:       "
        f"{estimated_tokens:,} tokens"
    )


# ============================================================
# RUN ONE REQUEST
# ============================================================

def run_request(
    mode,
    instructions,
    prompt,
    use_web_search,
):

    separator(
        f"REQUEST TEST: {mode}"
    )

    print_request_size(
        mode,
        instructions,
        prompt,
    )

    print()
    print(
        "Sending fresh request..."
    )

    try:

        if use_web_search:

            response = client.responses.create(
                model=MODEL_DEPLOYMENT,

                instructions=(
                    instructions
                ),

                tools=[
                    {
                        "type": "web_search"
                    }
                ],

                input=prompt,
            )

        else:

            response = client.responses.create(
                model=MODEL_DEPLOYMENT,

                instructions=(
                    instructions
                ),

                input=prompt,
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
            "First 1,500 output characters:"
        )

        print(
            output_text[:1500]
        )

        # ----------------------------------------------------
        # Inspect web-search calls if available.
        # ----------------------------------------------------

        if use_web_search:

            successful_searches = 0
            failed_searches = 0

            for item in response.output:

                item_type = getattr(
                    item,
                    "type",
                    None,
                )

                if (
                    item_type
                    != "web_search_call"
                ):
                    continue

                status = getattr(
                    item,
                    "status",
                    None,
                )

                if status == "completed":

                    successful_searches += 1

                elif status == "failed":

                    failed_searches += 1

            print()

            print(
                f"Web searches completed: "
                f"{successful_searches}"
            )

            print(
                f"Web searches failed: "
                f"{failed_searches}"
            )

        return True

    except Exception as e:

        print()
        print(
            "RESULT: FAILED"
        )

        print()
        print(
            "Exception:"
        )

        print(
            str(e)
        )

        print()
        print(
            "Exception type:"
        )

        print(
            type(e).__name__
        )

        return False


# ============================================================
# MAIN
# ============================================================

def main():

    try:

        separator(
            "rAIse AI GROWTH ANALYSER"
        )

        print(
            "EXACT RESEARCH REQUEST TEST"
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
            "Purpose:"
        )

        print(
            "Compare the production-style research "
            "request WITHOUT web_search against "
            "the same request WITH web_search."
        )

        print()
        print(
            "LLM responses are NOT cached."
        )

        print(
            "YouTube/data caches ARE allowed."
        )

        # ====================================================
        # BUILD DATA
        # ====================================================

        data = build_data()

        # ====================================================
        # BUILD EXACT PROMPT
        # ====================================================

        separator(
            "BUILDING EXACT RESEARCH PROMPT"
        )

        prompt = (
            build_exact_research_prompt(
                data
            )
        )

        instructions = (
            RESEARCH_AGENT_INSTRUCTIONS
        )

        print(
            "Prompt constructed."
        )

        # ====================================================
        # SHOW DATA COMPONENT SIZES
        # ====================================================

        print()
        print(
            "DATA COMPONENT SIZES"
        )

        components = {

            "target":
                data["target"],

            "research_event":
                data["research_event"],

            "important_events":
                data["important_events"],

            "before_videos":
                data["before_videos"],

            "short_videos":
                data["short_videos"],

            "long_videos":
                data["long_videos"],

            "comment_analysis":
                data["comment_analysis"],

            "audience_signal":
                data["audience_signal"],

            "period_spike_analysis":
                data[
                    "period_spike_analysis"
                ],

            "related_videos":
                data["related_videos"],

            "cross_year_candidates":
                data[
                    "cross_year_candidates"
                ],
        }

        for name, value in (
            components.items()
        ):

            size = len(
                json_text(value)
            )

            print(
                f"{name:28}"
                f"{size:>10,} chars"
            )

        # ====================================================
        # TEST 1
        # ====================================================

        no_web_success = run_request(
            mode="NO_WEB_SEARCH",
            instructions=instructions,
            prompt=prompt,
            use_web_search=False,
        )

        # ====================================================
        # STOP IF NO-WEB FAILED
        # ====================================================

        if not no_web_success:

            print()
            print(
                "NO_WEB_SEARCH FAILED."
            )

            print(
                "Therefore the issue is not specifically "
                "the web_search tool configuration."
            )

            return

        # ====================================================
        # TEST 2
        # ====================================================

        web_success = run_request(
            mode="WITH_WEB_SEARCH",
            instructions=instructions,
            prompt=prompt,
            use_web_search=True,
        )

        # ====================================================
        # FINAL DIAGNOSIS
        # ====================================================

        separator(
            "DIAGNOSIS"
        )

        if web_success:

            print(
                "BOTH REQUESTS SUCCEEDED."
            )

            print()
            print(
                "NO_WEB_SEARCH:      PASS"
            )

            print(
                "WITH_WEB_SEARCH:    PASS"
            )

            print()
            print(
                "This means the current production "
                "429 is not reproducible from the "
                "research prompt/data alone."
            )

            print()
            print(
                "Next step:"
            )

            print(
                "Compare the exact production "
                "research_event() execution against "
                "this request, including any calls "
                "made immediately before it."
            )

        else:

            print(
                "NO_WEB_SEARCH succeeded."
            )

            print(
                "WITH_WEB_SEARCH failed."
            )

            print()
            print(
                "This isolates the failure to the "
                "web-search-enabled request path."
            )

            print()
            print(
                "The next debugging target is the "
                "Foundry web_search configuration/request."
            )

    except Exception as e:

        separator(
            "TEST FAILED"
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