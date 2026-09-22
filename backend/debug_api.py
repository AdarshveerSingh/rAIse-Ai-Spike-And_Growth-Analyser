from collections import Counter
import os
from urllib.parse import urlparse

import json

from datetime import datetime
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from googleapiclient.discovery import build

from app.youtube.client import (
    get_channel,
    get_video_ids,
    get_videos,
)

from app.analysis.metrics import prepare_videos
from app.analysis.rolling import rolling_baseline
from app.analysis.spikes import detect_spikes, rank_spikes
from app.analysis.episodes import analyze_all_growth_events
from app.pipeline.growth_pipeline import run_growth_pipeline


# ============================================================
# APP
# ============================================================

app = FastAPI(
    title="rAIse Analysis API",
    version="1.0.0",
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# LEGACY CHANNELS
#
# Kept so the old endpoints continue to work.
# The new frontend does NOT depend on these.
# ============================================================

CHANNELS = {
    "google": {
        "name": "Google for Developers",
        "id": "UC_x5XG1OV2P6uZZ5FSM9Ttw",
    },
    "markiplier": {
        "name": "Markiplier",
        "id": "UC7_YxT-KID8kRbqZo7MyscQ",
    },
    "dynamo": {
        "name": "Dynamo Gaming",
        "id": "UCqNH56x9g4QYVpzmWTzqVYg",
    },
}


# ============================================================
# ANALYSIS SETTINGS
# ============================================================

BEFORE_COUNT = 5
SHORT_COUNT = 5
LONG_COUNT = 10

ROLLING_WINDOW = 10

MIN_SPIKE_RATIO = 3.0
MIN_ROBUST_Z = 2.5

RETENTION_THRESHOLD = 1.5


# ============================================================
# REQUEST MODELS
# ============================================================

class ResearchRequest(BaseModel):
    event: dict


# ============================================================
# YOUTUBE CHANNEL RESOLUTION
# ============================================================

def _youtube_service():
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        raise HTTPException(
            status_code=500,
            detail="YOUTUBE_API_KEY is not configured.",
        )

    return build(
        "youtube",
        "v3",
        developerKey=api_key,
    )


def resolve_youtube_channel(channel_url: str):
    """
    Resolve a YouTube channel URL to:
        {
            "id": channel_id,
            "name": channel_name
        }

    Supported:
      /channel/UC...
      /@handle
      /c/legacy-name
      /user/username
    """

    if not channel_url:
        raise HTTPException(
            status_code=400,
            detail="No YouTube channel URL supplied.",
        )

    channel_url = channel_url.strip()

    try:
        parsed = urlparse(channel_url)
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Invalid YouTube channel URL.",
        )

    host = parsed.netloc.lower()

    # Also accept a URL without https://
    if not host and channel_url.startswith("youtube.com"):
        parsed = urlparse("https://" + channel_url)
        host = parsed.netloc.lower()

    if host not in {
        "youtube.com",
        "www.youtube.com",
        "m.youtube.com",
    }:
        raise HTTPException(
            status_code=400,
            detail="Please provide a valid YouTube channel URL.",
        )

    path = parsed.path.rstrip("/")

    # --------------------------------------------------------
    # Direct channel ID
    # --------------------------------------------------------

    if path.startswith("/channel/"):
        channel_id = path[len("/channel/"):]

        if not channel_id:
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube channel ID.",
            )

        try:
            channel = get_channel(channel_id)
        except Exception as exc:
            raise HTTPException(
                status_code=404,
                detail=f"Could not find YouTube channel: {exc}",
            )

        return {
            "id": channel["id"],
            "name": channel["title"],
        }

    youtube = _youtube_service()

    # --------------------------------------------------------
    # @handle
    # --------------------------------------------------------

    if path.startswith("/@"):
        handle = path[2:]

        if not handle:
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube handle.",
            )

        try:
            response = (
                youtube.channels()
                .list(
                    part="snippet,contentDetails,statistics",
                    forHandle=handle,
                )
                .execute()
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"YouTube API error: {exc}",
            )

        items = response.get("items", [])

        if not items:
            raise HTTPException(
                status_code=404,
                detail=f"YouTube channel @{handle} was not found.",
            )

        item = items[0]

        return {
            "id": item["id"],
            "name": item["snippet"]["title"],
        }

    # --------------------------------------------------------
    # /user/username
    # --------------------------------------------------------

    if path.startswith("/user/"):
        username = path[len("/user/"):]

        if not username:
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube username.",
            )

        try:
            response = (
                youtube.channels()
                .list(
                    part="snippet,contentDetails,statistics",
                    forUsername=username,
                )
                .execute()
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"YouTube API error: {exc}",
            )

        items = response.get("items", [])

        if not items:
            raise HTTPException(
                status_code=404,
                detail=f"YouTube user '{username}' was not found.",
            )

        item = items[0]

        return {
            "id": item["id"],
            "name": item["snippet"]["title"],
        }

    # --------------------------------------------------------
    # /c/legacy-name
    # --------------------------------------------------------

    if path.startswith("/c/"):
        channel_name = path[len("/c/"):]

        if not channel_name:
            raise HTTPException(
                status_code=400,
                detail="Invalid YouTube channel URL.",
            )

        try:
            response = (
                youtube.search()
                .list(
                    part="snippet",
                    q=channel_name,
                    type="channel",
                    maxResults=5,
                )
                .execute()
            )
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"YouTube API error: {exc}",
            )

        items = response.get("items", [])

        if not items:
            raise HTTPException(
                status_code=404,
                detail=f"YouTube channel '{channel_name}' was not found.",
            )

        item = items[0]

        return {
            "id": item["snippet"]["channelId"],
            "name": item["snippet"]["channelTitle"],
        }

    raise HTTPException(
        status_code=400,
        detail=(
            "Unsupported YouTube URL. Use a channel URL such as "
            "https://youtube.com/@creator"
        ),
    )


# ============================================================
# HELPERS
# ============================================================

def normalize_datetime(value):
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def build_analysis(channel_info):
    """
    Runs the existing deterministic analysis pipeline.
    """

    print()
    print("=" * 80)
    print(f"ANALYZING: {channel_info['name']}")
    print(f"CHANNEL ID: {channel_info['id']}")
    print("=" * 80)

    # --------------------------------------------------------
    # GET CHANNEL
    # --------------------------------------------------------

    channel = get_channel(
        channel_info["id"]
    )

    # --------------------------------------------------------
    # GET VIDEO IDS
    # --------------------------------------------------------

    video_ids = get_video_ids(
        channel["uploads_playlist_id"]
    )

    print(f"Found {len(video_ids)} videos")

    # --------------------------------------------------------
    # GET VIDEO DATA
    # --------------------------------------------------------

    videos = get_videos(video_ids)

    print(f"Loaded {len(videos)} videos")

    # --------------------------------------------------------
    # CONTENT TYPES
    # --------------------------------------------------------

    content_types = Counter(
        video["content_type"]
        for video in videos
    )

    # --------------------------------------------------------
    # REGULAR VIDEOS ONLY
    # --------------------------------------------------------

    analysis_videos = [
        video
        for video in videos
        if video["content_type"] == "REGULAR"
    ]

    print(
        f"Regular videos: {len(analysis_videos)}"
    )

    # --------------------------------------------------------
    # PREPARE METRICS
    # --------------------------------------------------------

    prepared_videos = prepare_videos(
        analysis_videos
    )

    # --------------------------------------------------------
    # ROLLING BASELINE
    # --------------------------------------------------------

    baseline_videos = rolling_baseline(
        prepared_videos,
        window=ROLLING_WINDOW,
    )

    # --------------------------------------------------------
    # DETECT SPIKES
    # --------------------------------------------------------

    spikes = detect_spikes(
        baseline_videos,
        min_ratio=MIN_SPIKE_RATIO,
        min_robust_z=MIN_ROBUST_Z,
    )

    # --------------------------------------------------------
    # RANK SPIKES
    # --------------------------------------------------------

    ranked_spikes = rank_spikes(spikes)

    print(
        f"Detected spikes: {len(spikes)}"
    )

    # --------------------------------------------------------
    # GROWTH EVENTS
    # --------------------------------------------------------

    events = analyze_all_growth_events(
        prepared_videos,
        spikes,
        before_count=BEFORE_COUNT,
        short_count=SHORT_COUNT,
        long_count=LONG_COUNT,
        retention_threshold=RETENTION_THRESHOLD,
    )

    print(
        f"Growth events: {len(events)}"
    )

    # --------------------------------------------------------
    # CLASSIFICATION COUNTS
    # --------------------------------------------------------

    classification_counts = Counter(
        event["event_type"]
        for event in events
    )

    progressive_count = sum(
        1
        for event in events
        if event.get(
            "progressive_trajectory",
            False,
        )
    )

    # --------------------------------------------------------
    # SPIKE IDS
    # --------------------------------------------------------

    spike_ids = {
        spike["video_id"]
        for spike in spikes
    }

    # --------------------------------------------------------
    # TIMELINE
    # --------------------------------------------------------

    timeline = []

    for video in prepared_videos:
        timeline.append(
            {
                "video_id": video["id"],
                "title": video["title"],
                "published_at": normalize_datetime(
                    video["published_at"]
                ),
                "views": video["views"],
                "engagement_rate": video[
                    "engagement_rate"
                ],
                "is_spike": (
                    video["id"] in spike_ids
                ),
                "thumbnail_url": video["thumbnail_url"],
            }
        )
    thumbnail_map = {
        video["id"]: video.get("thumbnail_url")
        for video in videos
    }
    # --------------------------------------------------------
    # NORMALIZE EVENTS
    # --------------------------------------------------------

    thumbnail_map = {
        video["id"]: video.get("thumbnail_url")
        for video in videos
    }

    normalized_events = []

    for event in events:
        video_id = event.get("video_id")

        normalized_event = {
            **event,
            "published_at": normalize_datetime(
                event["published_at"]
            ),
            "thumbnail_url": thumbnail_map.get(video_id),
        }

        normalized_events.append(
            normalized_event
        )

    normalized_events.sort(
        key=lambda event:
        event["published_at"]
    )
    # --------------------------------------------------------
    # RETURN
    # --------------------------------------------------------

    return {
"channel": {
    "id": channel["id"],
    "name": channel["title"],
    "description": channel["description"],
    "published_at": normalize_datetime(
        channel["published_at"]
    ),

    "profile_picture": channel.get("profile_picture"),
    "banner_url": channel.get("banner_url"),

    "subscribers": channel["subscribers"],
    "views": channel["views"],
    "video_count": channel["video_count"],
},

        "settings": {
            "before_count": BEFORE_COUNT,
            "short_count": SHORT_COUNT,
            "long_count": LONG_COUNT,
            "rolling_window": ROLLING_WINDOW,
            "spike_threshold": MIN_SPIKE_RATIO,
            "robust_z_threshold": MIN_ROBUST_Z,
            "retention_threshold": RETENTION_THRESHOLD,
        },

        "analysis": {
            "total_videos": len(videos),
            "regular_videos": len(analysis_videos),
            "spike_candidates": len(spikes),
            "events": len(normalized_events),
            "content_types": dict(content_types),
            "classification_counts": dict(
                classification_counts
            ),
            "progressive_count": progressive_count,
        },

        "spikes": spikes,
        "ranked_spikes": ranked_spikes,
        "timeline": timeline,
        "events": normalized_events,
    }


def build_research(channel_info, event):
    """
    Runs the existing research pipeline.
    """

    if not event:
        raise HTTPException(
            status_code=400,
            detail="No event supplied.",
        )

    video_id = event.get("video_id")

    if not video_id:
        video_id = event.get("id")

    if not video_id:
        raise HTTPException(
            status_code=400,
            detail="Event does not contain a video_id.",
        )

    channel_id = channel_info["id"]
    creator_name = channel_info["name"]

    print("=" * 70)
    print("RESEARCH REQUEST")
    print("=" * 70)
    print("Channel:", creator_name)
    print("Channel ID:", channel_id)
    print("Video ID:", video_id)
    print("Title:", event.get("title"))
    print("=" * 70)

    try:
        pipeline_result = run_growth_pipeline(
            channel_id=channel_id,
            creator_name=creator_name,
            target_video_id=video_id,
            save_output=False,
        )
    except Exception as exc:
        print(
            "Research pipeline exception:",
            exc,
        )

        raise HTTPException(
            status_code=500,
            detail=f"Research pipeline failed: {exc}",
        )

    if not pipeline_result:
        raise HTTPException(
            status_code=500,
            detail="Research pipeline returned no result.",
        )

    pipeline_research = pipeline_result.get(
        "research"
    )

    if not pipeline_research:
        response = {
            "success": False,
            "error": (
                "Research pipeline returned "
                "no research report."
            ),
            "creator": creator_name,
            "channel": channel_info,
            "target": event,
            "growth_event": pipeline_result.get(
                "growth_event"
            ),
            "spikes": pipeline_result.get(
                "spikes",
                [],
            ),
            "ranked_spikes": pipeline_result.get(
                "ranked_spikes",
                [],
            ),
            "related_videos": pipeline_result.get(
                "related_videos",
                [],
            ),
            "audience_timing": pipeline_result.get(
                "audience_signal"
            ),
            "cross_year_candidates": pipeline_result.get(
                "cross_year_candidates",
                [],
            ),
            "research": None,
        }

        return response

    if isinstance(pipeline_research, dict):
        if (
            "research" in pipeline_research
            and isinstance(
                pipeline_research["research"],
                dict,
            )
        ):
            research = pipeline_research[
                "research"
            ]
        else:
            research = pipeline_research
    else:
        research = None

    if research is None:
        response = {
            "success": False,
            "error": "Research report was empty.",
            "creator": creator_name,
            "channel": channel_info,
            "target": event,
            "research": None,
        }

        return response

    # ============================================================
    # FINAL RESPONSE
    # ============================================================

    response = {
        "success": True,
        "creator": creator_name,
        "channel": channel_info,
        "target": event,
        "growth_event": pipeline_result.get(
            "growth_event"
        ),
        "spikes": pipeline_result.get(
            "spikes",
            [],
        ),
        "ranked_spikes": pipeline_result.get(
            "ranked_spikes",
            [],
        ),
        "related_videos": pipeline_result.get(
            "related_videos",
            [],
        ),
        "audience_timing": pipeline_result.get(
            "audience_signal"
        ),
        "cross_year_candidates": pipeline_result.get(
            "cross_year_candidates",
            [],
        ),
        "research": research,
    }

    # ============================================================
    # SAVE FINAL RESPONSE JSON
    # ============================================================

    from pathlib import Path
    from datetime import datetime
    import json

    output_dir = (
        Path(__file__).resolve().parent
        / "research_outputs"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True,
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    output_file = (
        output_dir
        / f"research_response_{timestamp}.json"
    )

    with open(
        output_file,
        "w",
        encoding="utf-8",
    ) as f:
        json.dump(
            response,
            f,
            indent=2,
            ensure_ascii=False,
            default=str,
        )

    print(
        "\n"
        + "=" * 80
        + "\n"
        + "FINAL RESPONSE JSON SAVED"
        + "\n"
        + "=" * 80
    )

    print(
        f"File: {output_file}"
    )

    print(
        f"Size: {output_file.stat().st_size:,} bytes"
    )

    print("=" * 80)

    return response

# ============================================================
# HEALTH
# ============================================================

@app.get("/")
def root():
    return {
        "name": "rAIse Analysis API",
        "status": "running",
    }


@app.get("/api/health")
def health():
    return {
        "status": "ok",
    }


# ============================================================
# AVAILABLE LEGACY CHANNELS
# ============================================================

@app.get("/api/channels")
def get_available_channels():
    return {
        key: {
            "name": value["name"],
            "id": value["id"],
        }
        for key, value in CHANNELS.items()
    }


# ============================================================
# NEW: ANALYZE FROM YOUTUBE URL
# ============================================================

@app.get("/api/analyze")
def analyze_channel_url(channel_url: str):
    channel_info = resolve_youtube_channel(
        channel_url
    )

    return build_analysis(channel_info)


# ============================================================
# LEGACY: ANALYZE BY CHANNEL KEY
# ============================================================

@app.get("/api/analyze/{channel_key}")
def analyze_channel(channel_key: str):

    if channel_key not in CHANNELS:
        raise HTTPException(
            status_code=404,
            detail="Unknown channel",
        )

    channel_info = CHANNELS[channel_key]

    return build_analysis(channel_info)


# ============================================================
# NEW: RESEARCH FROM YOUTUBE URL
# ============================================================

@app.post("/api/research")
def run_research_from_url(
    channel_url: str,
    request: ResearchRequest,
):
    channel_info = resolve_youtube_channel(
        channel_url
    )

    return build_research(
        channel_info,
        request.event,
    )


# ============================================================
# LEGACY: RESEARCH BY CHANNEL KEY
# ============================================================

@app.post("/api/research/{channel_key}")
def run_research(
    channel_key: str,
    request: ResearchRequest,
):

    if channel_key not in CHANNELS:
        raise HTTPException(
            status_code=404,
            detail="Unknown channel",
        )

    channel_info = CHANNELS[channel_key]

    return build_research(
        channel_info,
        request.event,
    )
