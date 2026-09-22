import base64
import io
import json
import requests

from PIL import Image
import imagehash

from app.ai.client import client, MODEL_DEPLOYMENT


def download_thumbnail(url: str) -> bytes:
    response = requests.get(url, timeout=10)
    response.raise_for_status()

    return response.content


def thumbnail_hash(image_bytes: bytes):
    image = Image.open(io.BytesIO(image_bytes))
    return imagehash.phash(image)


def thumbnail_similarity(hash1, hash2):
    distance = hash1 - hash2

    similarity = 1 - (distance / 64)

    return round(max(0, similarity), 3)


def analyze_thumbnail(image_bytes: bytes):
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")

    response = client.responses.create(
        model=MODEL_DEPLOYMENT,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_text",
                        "text": """
Analyze this YouTube thumbnail for a growth-analysis system.

Return ONLY valid JSON with these fields:

{
    "has_face": true,
    "face_count": 0,
    "expression": "none",
    "has_text": true,
    "text_amount": "low",
    "subject_position": "center",
    "shot_type": "close_up",
    "high_contrast": true,
    "arrows_or_circles": false,
    "visual_complexity": "medium",
    "branding_elements": true,
    "main_subject": "description"
}

Rules:
- Only describe what is visually observable.
- Do not infer anything about the video's success.
- Do not infer audience reaction.
- Do not infer why the thumbnail performed well.
- If something is unclear, use "unclear".
- Return JSON only.
"""
                    },
                    {
                        "type": "input_image",
                        "image_url": (
                            f"data:image/jpeg;base64,{image_base64}"
                        ),
                        "detail": "auto"
                    }
                ]
            }
        ]
    )

    text = response.output_text.strip()

    try:
        return json.loads(text)

    except json.JSONDecodeError:
        raise ValueError(
            f"Model returned invalid JSON:\n{text}"
        )