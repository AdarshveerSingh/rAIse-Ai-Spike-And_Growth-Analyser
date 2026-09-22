def get_spike_context(videos, spike, window=3):
    """
    Get videos surrounding a potential spike.
    """

    spike_index = None

    for i, video in enumerate(videos):
        if video["id"] == spike["video_id"]:
            spike_index = i
            break

    if spike_index is None:
        return None

    start = max(0, spike_index - window)
    end = min(len(videos), spike_index + window + 1)

    return {
        "before": videos[start:spike_index],
        "spike": {
            **videos[spike_index],
            "spike_ratio": spike["spike_ratio"]
        },
        "after": videos[spike_index + 1:end],
    }