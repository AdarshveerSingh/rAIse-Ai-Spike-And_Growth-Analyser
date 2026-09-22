import statistics


def _median_views(videos):
    if not videos:
        return 0

    return statistics.median(
        video["views"]
        for video in videos
    )


def _add_video_metrics(videos, baseline):
    result = []

    for video in videos:
        views = video["views"]

        if baseline > 0:
            ratio = views / baseline
        else:
            ratio = 0

        result.append({
            "video_id": video["id"],
            "title": video["title"],
            "published_at": video["published_at"],
            "views": views,
            "vs_baseline": round(ratio, 2)
        })

    return result


def classify_growth_event(
    short_term_retained,
    long_term_retained
):
    """
    Classify an event based on short-term and long-term
    baseline retention.

    ONE_OFF:
        ST = False
        LT = False

    TEMPORARY:
        ST = True
        LT = False

    SUSTAINED_THROUGHOUT:
        ST = True
        LT = True

    SUSTAINED_EVENTUAL:
        ST = False
        LT = True

    INSUFFICIENT_DATA:
        Either retention value is None.
    """

    if (
        short_term_retained is None
        or long_term_retained is None
    ):
        return "INSUFFICIENT_DATA"

    if not short_term_retained and not long_term_retained:
        return "ONE_OFF"

    if short_term_retained and not long_term_retained:
        return "TEMPORARY"

    if short_term_retained and long_term_retained:
        return "SUSTAINED_THROUGHOUT"

    if not short_term_retained and long_term_retained:
        return "SUSTAINED_EVENTUAL"

    return "UNKNOWN"


def detect_progressive_trajectory(
    before_baseline,
    short_term_baseline,
    long_term_baseline
):
    """
    Initial progressive-growth check.

    A trajectory is considered progressive when:

        before < short term < long term

    This is intentionally a simple first version.
    We will later determine whether the increases
    are large enough to be considered meaningful.
    """

    if (
        before_baseline <= 0
        or short_term_baseline <= 0
        or long_term_baseline <= 0
    ):
        return False

    return (
        before_baseline
        < short_term_baseline
        < long_term_baseline
    )


def analyze_growth_event(
    videos,
    spike,
    before_count=5,
    short_count=5,
    long_count=10,
    retention_threshold=1.5
):
    """
    Analyze what happened before and after a candidate spike.

    Windows:

        BEFORE      = previous 5 videos
        SPIKE       = candidate spike
        SHORT TERM  = next 5 videos
        LONG TERM   = following 10 videos

    The spike itself is excluded from all baselines.
    """

    spike_index = None

    for i, video in enumerate(videos):
        if video["id"] == spike["video_id"]:
            spike_index = i
            break

    if spike_index is None:
        return None

    # --------------------------------------------------
    # BEFORE SPIKE
    # --------------------------------------------------

    before_start = max(
        0,
        spike_index - before_count
    )

    before = videos[
        before_start:spike_index
    ]

    # --------------------------------------------------
    # SHORT TERM AFTER SPIKE
    # --------------------------------------------------

    short_start = spike_index + 1

    short_end = min(
        len(videos),
        short_start + short_count
    )

    short_term = videos[
        short_start:short_end
    ]

    # --------------------------------------------------
    # LONG TERM AFTER SPIKE
    # --------------------------------------------------

    long_start = short_end

    long_end = min(
        len(videos),
        long_start + long_count
    )

    long_term = videos[
        long_start:long_end
    ]

    # --------------------------------------------------
    # NEED ENOUGH BEFORE DATA
    # --------------------------------------------------

    if len(before) < 3:
        return None

    before_baseline = _median_views(before)

    if before_baseline <= 0:
        return None

    short_baseline = _median_views(short_term)
    long_baseline = _median_views(long_term)

    # --------------------------------------------------
    # CHANGE FROM PRE-SPIKE BASELINE
    # --------------------------------------------------

    short_term_change = (
        short_baseline / before_baseline
        if short_baseline > 0
        else 0
    )

    long_term_change = (
        long_baseline / before_baseline
        if long_baseline > 0
        else 0
    )

    # --------------------------------------------------
    # RETENTION
    # --------------------------------------------------

    short_retained = (
        short_term_change >= retention_threshold
        if short_term
        else None
    )

    long_retained = (
        long_term_change >= retention_threshold
        if long_term
        else None
    )

    # --------------------------------------------------
    # CORE EVENT CLASSIFICATION
    # --------------------------------------------------

    event_type = classify_growth_event(
        short_retained,
        long_retained
    )

    # --------------------------------------------------
    # PROGRESSIVE TRAJECTORY
    # --------------------------------------------------

    progressive_trajectory = detect_progressive_trajectory(
        before_baseline,
        short_baseline,
        long_baseline
    )

    # --------------------------------------------------
    # PER-VIDEO METRICS
    # --------------------------------------------------

    before_metrics = _add_video_metrics(
        before,
        before_baseline
    )

    short_metrics = _add_video_metrics(
        short_term,
        before_baseline
    )

    long_metrics = _add_video_metrics(
        long_term,
        before_baseline
    )

    # --------------------------------------------------
    # RESULT
    # --------------------------------------------------

    return {
        "video_id": spike["video_id"],
        "title": spike["title"],
        "published_at": spike["published_at"],

        "spike_views": spike["views"],
        "spike_ratio": spike["spike_ratio"],

        # ----------------------------------------------
        # BASELINES
        # ----------------------------------------------

        "before_baseline": round(
            before_baseline
        ),

        "short_term_baseline": round(
            short_baseline
        ),

        "long_term_baseline": round(
            long_baseline
        ),

        # ----------------------------------------------
        # BASELINE CHANGES
        # ----------------------------------------------

        "short_term_change": round(
            short_term_change,
            2
        ),

        "long_term_change": round(
            long_term_change,
            2
        ),

        # ----------------------------------------------
        # RETENTION
        # ----------------------------------------------

        "short_term_retained": short_retained,

        "long_term_retained": long_retained,

        # ----------------------------------------------
        # CORE CLASSIFICATION
        # ----------------------------------------------

        "event_type": event_type,

        # ----------------------------------------------
        # PROGRESSIVE TRAJECTORY
        # ----------------------------------------------

        "progressive_trajectory": progressive_trajectory,

        # ----------------------------------------------
        # VIDEO WINDOWS
        # ----------------------------------------------

        "before": before_metrics,

        "short_term": short_metrics,

        "long_term": long_metrics,

        # ----------------------------------------------
        # COUNTS
        # ----------------------------------------------

        "before_count": len(before),

        "short_term_count": len(short_term),

        "long_term_count": len(long_term)
    }


def analyze_all_growth_events(
    videos,
    spikes,
    before_count=5,
    short_count=5,
    long_count=10,
    retention_threshold=1.5
):
    events = []

    for spike in spikes:

        event = analyze_growth_event(
            videos,
            spike,

            before_count=before_count,
            short_count=short_count,
            long_count=long_count,

            retention_threshold=retention_threshold
        )

        if event is not None:
            events.append(event)

    return events

def select_important_growth_events(events):
    """
    Reduce all detected growth events to the small set that
    should be sent to the AI research agent.

    Selected:
        1. Earliest event
        2. Strongest event
        3. First ONE_OFF event
        4. First TEMPORARY event
        5. First SUSTAINED_THROUGHOUT event
        6. First SUSTAINED_EVENTUAL event
        7. First PROGRESSIVE event

    Duplicate videos are removed while preserving priority.
    """

    if not events:
        return []

    selected = []

    def add_event(event, role):
        if event is None:
            return

        selected.append({
            **event,
            "event_role": role
        })

    # --------------------------------------------------
    # 1. EARLIEST
    # --------------------------------------------------

    earliest = min(
        events,
        key=lambda event: event["published_at"]
    )

    add_event(
        earliest,
        "EARLIEST"
    )

    # --------------------------------------------------
    # 2. STRONGEST
    # --------------------------------------------------

    strongest = max(
        events,
        key=lambda event: (
            event.get("spike_ratio", 0)
        )
    )

    add_event(
        strongest,
        "STRONGEST"
    )

    # --------------------------------------------------
    # 3–6. ONE EVENT PER RETENTION CLASS
    # --------------------------------------------------

    retention_types = [
        "ONE_OFF",
        "TEMPORARY",
        "SUSTAINED_THROUGHOUT",
        "SUSTAINED_EVENTUAL",
    ]

    for event_type in retention_types:

        matching = [
            event
            for event in events
            if event.get("event_type") == event_type
        ]

        if not matching:
            continue

        # Use the earliest occurrence of each type.
        representative = min(
            matching,
            key=lambda event: event["published_at"]
        )

        add_event(
            representative,
            event_type
        )

    # --------------------------------------------------
    # 7. PROGRESSIVE
    # --------------------------------------------------

    progressive_events = [
        event
        for event in events
        if event.get("progressive_trajectory") is True
    ]

    if progressive_events:

        representative = min(
            progressive_events,
            key=lambda event: event["published_at"]
        )

        add_event(
            representative,
            "PROGRESSIVE"
        )

    # --------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------

    unique = []
    seen = set()

    for event in selected:

        video_id = event["video_id"]

        if video_id in seen:
            continue

        seen.add(video_id)
        unique.append(event)

    return unique

def print_growth_event(event):

    print("\n" + "=" * 80)

    print(
        f"SPIKE: {event['title']}"
    )

    print(
        f"Date: {event['published_at']}"
    )

    print(
        f"Spike views: "
        f"{event['spike_views']:,}"
    )

    print(
        f"Spike ratio: "
        f"{event['spike_ratio']}x"
    )

    # --------------------------------------------------
    # CLASSIFICATION
    # --------------------------------------------------

    print("\n" + "-" * 80)
    print("CLASSIFICATION")
    print("-" * 80)

    print(
        f"Event type          : "
        f"{event['event_type']}"
    )

    print(
        f"Progressive         : "
        f"{event['progressive_trajectory']}"
    )

    # --------------------------------------------------
    # BASELINES
    # --------------------------------------------------

    print("\n" + "-" * 80)
    print("BASELINES")
    print("-" * 80)

    print(
        f"Before baseline : "
        f"{event['before_baseline']:,}"
    )

    print(
        f"Short baseline  : "
        f"{event['short_term_baseline']:,} "
        f"({event['short_term_change']}x)"
    )

    print(
        f"Long baseline   : "
        f"{event['long_term_baseline']:,} "
        f"({event['long_term_change']}x)"
    )

    print(
        f"\nShort-term retained: "
        f"{event['short_term_retained']}"
    )

    print(
        f"Long-term retained : "
        f"{event['long_term_retained']}"
    )

    # --------------------------------------------------
    # VIDEO PRINTING
    # --------------------------------------------------

    def print_videos(label, videos):

        print("\n" + "-" * 80)
        print(label)
        print("-" * 80)

        for video in videos:

            print(
                f"{video['published_at'].date()} | "
                f"{video['views']:>10,} views | "
                f"{video['vs_baseline']:>7.2f}x | "
                f"{video['title']}"
            )

    print_videos(
        "BEFORE",
        event["before"]
    )

    print_videos(
        "SHORT TERM",
        event["short_term"]
    )

    print_videos(
        "LONG TERM",
        event["long_term"]
    )