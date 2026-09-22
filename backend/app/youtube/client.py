import os
import requests
from dotenv import load_dotenv

from app.youtube.cache import (
    load_cache,
    save_cache
)

load_dotenv()

API_KEY = os.getenv("YOUTUBE_API_KEY")

BASE_URL = "https://www.googleapis.com/youtube/v3"


def classify_video(video):
    snippet = video.get("snippet", {})
    live_details = video.get("liveStreamingDetails")

    title = snippet.get("title", "").lower()

    # YouTube explicitly provides live-streaming metadata
    if live_details is not None:
        return "LIVE_VOD"

    # Conservative Shorts detection for now
    if "#shorts" in title:
        return "SHORT"

    return "REGULAR"


def get_channel(channel_id: str):
    cache_name = f"channel_{channel_id}"

    cached = load_cache(cache_name)

    if cached is not None:
        if (
            "profile_picture" in cached
            and "banner_url" in cached
        ):
            print("YouTube cache hit: channel")
            return cached

        print(
            "YouTube channel cache is outdated — refreshing"
        )

    print("YouTube API: fetching channel")

    url = f"{BASE_URL}/channels"

    params = {
        "part": "snippet,statistics,contentDetails,brandingSettings",
        "id": channel_id,
        "key": API_KEY
    }

    response = requests.get(
        url,
        params=params
    )

    response.raise_for_status()

    data = response.json()

    if not data.get("items"):
        raise ValueError("Channel not found")

    channel = data["items"][0]

    result = {
        "id": channel["id"],
        "title": channel["snippet"]["title"],
        "description": channel["snippet"]["description"],
        "published_at": channel["snippet"]["publishedAt"],

        "profile_picture":
            channel["snippet"]
            ["thumbnails"]
            ["high"]
            ["url"],

        "banner_url":
            channel
            .get("brandingSettings", {})
            .get("image", {})
            .get("bannerExternalUrl"),

        "subscribers": int(
            channel["statistics"].get(
                "subscriberCount", 0
            )
        ),

        "views": int(
            channel["statistics"].get(
                "viewCount", 0
            )
        ),

        "video_count": int(
            channel["statistics"].get(
                "videoCount", 0
            )
        ),

        "uploads_playlist_id":
            channel["contentDetails"]
            ["relatedPlaylists"]
            ["uploads"]
    }

    save_cache(
        cache_name,
        result
    )

    return result

def get_video_ids(uploads_playlist_id: str, max_results=None):
    cache_name = f"video_ids_{uploads_playlist_id}"

    cached = load_cache(cache_name)

    if cached is not None:
        print("YouTube cache hit: video IDs")

        if max_results:
            return cached[:max_results]

        return cached

    print("YouTube API: fetching video IDs")

    video_ids = []
    next_page_token = None

    while True:
        params = {
            "part": "contentDetails",
            "playlistId": uploads_playlist_id,
            "maxResults": 50,
            "key": API_KEY
        }

        if next_page_token:
            params["pageToken"] = next_page_token

        response = requests.get(
            f"{BASE_URL}/playlistItems",
            params=params
        )

        response.raise_for_status()

        data = response.json()

        for item in data.get("items", []):
            video_ids.append(
                item["contentDetails"]["videoId"]
            )

        if max_results and len(video_ids) >= max_results:
            video_ids = video_ids[:max_results]
            break

        next_page_token = data.get("nextPageToken")

        if not next_page_token:
            break

    save_cache(
        cache_name,
        video_ids
    )

    return video_ids


def get_videos(video_ids):
    if not video_ids:
        return []

    # Use a stable cache name based on the first/last IDs
    # so the same channel's video metadata can be reused.
    cache_name = f"videos_{video_ids[0]}_{video_ids[-1]}"

    cached = load_cache(cache_name)

    if cached is not None:
        print("YouTube cache hit: videos")

        # --------------------------------------------------
        # CACHE MIGRATION
        # --------------------------------------------------
        # Older cached videos may not have content_type
        # because this field was added later.
        updated = False

        for video in cached:
            if "content_type" not in video:
                video["content_type"] = classify_video(video)
                updated = True

        # Save the upgraded cache so this only happens once.
        if updated:
            save_cache(
                cache_name,
                cached
            )

            print(
                "YouTube cache updated: added content_type"
            )

        return cached

    print("YouTube API: fetching video metadata")

    videos = []

    # YouTube allows up to 50 IDs per videos.list request
    for i in range(0, len(video_ids), 50):
        batch = video_ids[i:i + 50]

        params = {
            "part": "snippet,statistics,contentDetails,liveStreamingDetails",
            "id": ",".join(batch),
            "key": API_KEY
        }

        response = requests.get(
            f"{BASE_URL}/videos",
            params=params
        )

        response.raise_for_status()

        data = response.json()

        for video in data.get("items", []):

            statistics = video.get(
                "statistics",
                {}
            )

            videos.append({
                "id": video["id"],

                "title":
                    video["snippet"]["title"],

                "description":
                    video["snippet"]["description"],

                "published_at":
                    video["snippet"]["publishedAt"],

                "thumbnail_url":
                    video["snippet"]["thumbnails"]["high"]["url"],

                "duration":
                    video["contentDetails"]["duration"],

                "views": int(
                    statistics.get(
                        "viewCount",
                        0
                    )
                ),

                "likes": int(
                    statistics.get(
                        "likeCount",
                        0
                    )
                ),

                "comments": int(
                    statistics.get(
                        "commentCount",
                        0
                    )
                ),

                "content_type":
                    classify_video(video)
            })

    save_cache(
        cache_name,
        videos
    )

    return videos