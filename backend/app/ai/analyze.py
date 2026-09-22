from app.ai.client import ask_ai


def analyze_spike(context):
    spike = context["spike"]

    before = context["before"]
    after = context["after"]

    prompt = f"""
You are analyzing a YouTube creator's growth pattern.

Analyze the following potential growth spike.

SPIKE VIDEO:
Title: {spike["title"]}
Published: {spike["published_at"]}
Views: {spike["views"]}
Views relative to channel median: {spike["spike_ratio"]}x
Engagement rate: {spike["engagement_rate"]}%

VIDEOS BEFORE THE SPIKE:
"""

    for video in before:
        prompt += f"""
- {video["published_at"].date()} | {video["views"]} views | {video["title"]}
"""

    prompt += """

VIDEOS AFTER THE SPIKE:
"""

    for video in after:
        prompt += f"""
- {video["published_at"].date()} | {video["views"]} views | {video["title"]}
"""

    prompt += """

Answer using the following structure:

1. Observed pattern
2. What changed around the spike
3. What did not appear to change
4. Possible explanations
5. Evidence supporting each explanation
6. Evidence that is missing
7. Confidence level

Important:
- Do not claim causation from this data alone.
- Clearly distinguish observations from hypotheses.
- Do not invent external events or facts.
- If the available data is insufficient, explicitly say so.
"""

    return ask_ai(prompt)