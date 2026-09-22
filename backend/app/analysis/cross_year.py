from datetime import datetime
from typing import Any


# ============================================================
# HELPERS
# ============================================================


def _get_year(published_at):
    """
    Extract the calendar year from a video's published_at value.
    """

    if not published_at:
        return None

    if isinstance(published_at, datetime):
        return published_at.year

    try:
        return datetime.fromisoformat(
            str(published_at).replace("Z", "+00:00")
        ).year

    except (ValueError, TypeError):
        return None


def _safe_float(value, default=0.0):
    """
    Safely convert a value to float.
    """

    try:
        return float(value)

    except (TypeError, ValueError):
        return default


def _safe_int(value, default=0):
    """
    Safely convert a value to int.
    """

    try:
        return int(value)

    except (TypeError, ValueError):
        return default


def _get_spike_video_id(spike):
    """
    Extract the video ID from a spike record.
    """

    return (
        spike.get("video_id")
        or spike.get("id")
        or spike.get("videoId")
    )


def _get_related_video_id(related):
    """
    Extract the video ID from a related-video record.
    """

    return (
        related.get("video_id")
        or related.get("id")
        or related.get("videoId")
    )


def _get_related_score(related):
    """
    Extract the existing related-video score.
    """

    return _safe_float(
        related.get(
            "related_score",
            related.get(
                "score",
                0.0
            )
        )
    )


def _get_series_identity(related):
    """
    Extract exact series identity score.
    """

    return _safe_float(
        related.get(
            "series_identity",
            0.0
        )
    )


def _get_numbered_series_score(related):
    """
    Extract numbered-series relationship score.
    """

    return _safe_float(
        related.get(
            "numbered_series_score",
            related.get(
                "numbered_score",
                related.get(
                    "numbered",
                    0.0
                )
            )
        )
    )


def _get_title_similarity(related):
    """
    Extract title similarity.
    """

    return _safe_float(
        related.get(
            "title_similarity",
            0.0
        )
    )


def _get_content_type_score(related):
    """
    Extract content-type similarity.
    """

    return _safe_float(
        related.get(
            "content_type_similarity",
            related.get(
                "content_type_score",
                0.0
            )
        )
    )


def _get_temporal_score(related):
    """
    Extract temporal similarity from related.py.
    """

    return _safe_float(
        related.get(
            "temporal_similarity",
            related.get(
                "temporal_score",
                0.0
            )
        )
    )

# ============================================================
# SPIKE INDEX
# ============================================================


def _build_spike_index(spikes):
    """
    Build:

        video_id -> spike record

    Missing entries simply mean the video was not detected
    as an individual spike.
    """

    index = {}

    for spike in spikes or []:

        video_id = _get_spike_video_id(spike)

        if video_id:
            index[video_id] = spike

    return index


# ============================================================
# RELATED INDEX
# ============================================================


def _build_related_index(related_videos):
    """
    Build:

        video_id -> related-video record
    """

    index = {}

    for related in related_videos or []:

        video_id = _get_related_video_id(related)

        if video_id:
            index[video_id] = related

    return index


# ============================================================
# PERFORMANCE SCORE
# ============================================================


def _calculate_performance_score(
    video,
    year_videos,
):
    """
    Calculate a within-year performance percentile.

    This is NOT a spike detector.

    It answers:

        "How popular was this video compared with other
         videos uploaded during the audience-peak year?"
    """

    if not year_videos:
        return 0.0

    views = _safe_int(
        video.get(
            "views",
            0
        )
    )

    all_views = sorted(
        [
            _safe_int(
                item.get(
                    "views",
                    0
                )
            )
            for item in year_videos
        ]
    )

    if not all_views:
        return 0.0

    below_or_equal = sum(
        1
        for value in all_views
        if value <= views
    )

    percentile = (
        below_or_equal
        / len(all_views)
    )

    return round(
        percentile,
        4
    )


# ============================================================
# TEMPORAL SCORE
# ============================================================


def _calculate_temporal_score(
    target_video,
    candidate_video,
    audience_peak_year,
):
    """
    Measure how relevant the candidate's timing is.

    This is deliberately a weak contextual signal.

    It is NOT causal evidence.
    """

    target_date = target_video.get(
        "published_at"
    )

    candidate_date = candidate_video.get(
        "published_at"
    )

    if not target_date or not candidate_date:
        return 0.0

    try:

        target_dt = datetime.fromisoformat(
            str(target_date).replace(
                "Z",
                "+00:00"
            )
        )

        candidate_dt = datetime.fromisoformat(
            str(candidate_date).replace(
                "Z",
                "+00:00"
            )
        )

    except (ValueError, TypeError):

        return 0.0

    days_from_target = abs(
        (
            candidate_dt
            - target_dt
        ).days
    )

    score = 1.0 / (
        1.0
        + (days_from_target / 365.0)
    )

    return round(
        max(
            0.0,
            min(
                1.0,
                score
            )
        ),
        4
    )


# ============================================================
# RELATIONSHIP LABEL
# ============================================================


def _relationship_label(
    series_identity,
    numbered_series_score,
    related_score,
    spike,
):
    """
    Produce a human-readable description of the candidate.
    """

    if (
        series_identity >= 1.0
        and numbered_series_score >= 0.75
    ):
        return (
            "Later episode in the same series."
        )

    if series_identity >= 1.0:
        return (
            "Same recurring series or format."
        )

    if spike:
        return (
            "High-performing channel activity "
            "during the audience-peak year."
        )

    if related_score >= 0.65:
        return (
            "Strongly related channel content."
        )

    if related_score >= 0.50:
        return (
            "Related channel content."
        )

    return (
        "Potentially relevant channel activity."
    )


# ============================================================
# EVIDENCE
# ============================================================


def _build_evidence(
    series_identity,
    numbered_series_score,
    performance_score,
    spike,
    temporal_score,
):
    """
    Build structured observations explaining why a candidate
    matters.

    These are signals, NOT causal conclusions.
    """

    evidence = []

    # --------------------------------------------------------
    # SERIES
    # --------------------------------------------------------

    if series_identity >= 1.0:

        evidence.append({
            "type": "series_evidence",
            "label": "SAME_SERIES",
            "description": (
                "The candidate belongs to the same recurring "
                "series or format as the target video."
            ),
            "evidence_level": "INDIRECT",
        })

    # --------------------------------------------------------
    # NUMBERED SERIES
    # --------------------------------------------------------

    if numbered_series_score >= 0.75:

        evidence.append({
            "type": "series_evidence",
            "label": "LATER_EPISODE",
            "description": (
                "The candidate appears to be a later episode "
                "of the same numbered series."
            ),
            "evidence_level": "INDIRECT",
        })

    # --------------------------------------------------------
    # PERFORMANCE
    # --------------------------------------------------------

    if performance_score >= 0.90:

        evidence.append({
            "type": "performance_evidence",
            "label": "TOP_10_PERCENT",
            "description": (
                "The candidate was among the higher-viewed "
                "videos in the audience-peak year."
            ),
            "evidence_level": "DIRECT"}
        )

    elif performance_score >= 0.75:

        evidence.append({
            "type": "performance_evidence",
            "label": "ABOVE_AVERAGE",
            "description": (
                "The candidate performed above most videos "
                "uploaded during the audience-peak year."
            ),
            "evidence_level": "DIRECT",
        })

    # --------------------------------------------------------
    # SPIKE
    # --------------------------------------------------------

    if spike:

        spike_ratio = _safe_float(
            spike.get(
                "spike_ratio",
                0.0
            )
        )

        evidence.append({
            "type": "spike_evidence",
            "label": "CHANNEL_SPIKE",
            "description": (
                "The candidate itself was detected as an "
                "individual performance spike."
            ),
            "spike_ratio": spike_ratio,
            "robust_z": _safe_float(
                spike.get(
                    "robust_z",
                    0.0
                )
            ),
            "evidence_level": "DIRECT",
        })

    # --------------------------------------------------------
    # TEMPORAL
    # --------------------------------------------------------

    if temporal_score >= 0.50:

        evidence.append({
            "type": "temporal_evidence",
            "label": "TEMPORALLY_RELEVANT",
            "description": (
                "The candidate occurs within a relatively "
                "relevant period for the cross-year analysis."
            ),
            "evidence_level": "INDIRECT",
        })

    return evidence


# ============================================================
# RESEARCH PRIORITY
# ============================================================


def _research_priority(
    series_identity,
    numbered_series_score,
    performance_score,
    spike,
):
    """
    Determine how useful the candidate is for downstream
    research.

    This is NOT a causal probability.

    It simply tells the research agent which candidates have
    the strongest observable evidence to investigate first.
    """

    priority = "LOW"

    if (
        series_identity >= 1.0
        and performance_score >= 0.75
    ):
        priority = "HIGH"

    elif (
        performance_score >= 0.90
        or (
            series_identity >= 1.0
            and numbered_series_score >= 0.75
        )
    ):
        priority = "HIGH"

    elif (
        series_identity >= 1.0
        or performance_score >= 0.75
        or spike
    ):
        priority = "MEDIUM"

    return priority


# ============================================================
# MAIN FUNCTION
# ============================================================


def find_cross_year_candidates(
    target_video,
    audience_peak_year,
    videos,
    spikes,
    related_videos,
    max_candidates=20,
):
    """
    Find channel activity during an audience peak year that
    may help explain renewed attention around an older video.

    IMPORTANT:

    This function does NOT claim that these candidates caused
    the audience peak or caused traffic to the target video.

    It produces structured evidence candidates for the
    downstream Research Agent.

    A candidate can be useful even if it is NOT an individual
    spike.
    """

    if not target_video:
        return []

    if not videos:
        return []

    if audience_peak_year is None:
        return []

    # --------------------------------------------------------
    # BUILD LOOKUPS
    # --------------------------------------------------------

    spike_index = _build_spike_index(
        spikes
    )

    related_index = _build_related_index(
        related_videos
    )

    # --------------------------------------------------------
    # FILTER TO AUDIENCE PEAK YEAR
    # --------------------------------------------------------

    year_videos = []

    for video in videos:

        year = _get_year(
            video.get(
                "published_at"
            )
        )

        if year == audience_peak_year:

            year_videos.append(
                video
            )

    if not year_videos:
        return []

    # --------------------------------------------------------
    # CANDIDATE GENERATION
    # --------------------------------------------------------

    candidates = []

    target_id = (
        target_video.get("id")
        or target_video.get("video_id")
    )

    target_year = _get_year(
        target_video.get(
            "published_at"
        )
    )

    for video in year_videos:

        video_id = (
            video.get("id")
            or video.get("video_id")
        )

        if not video_id:
            continue

        # ----------------------------------------------------
        # Never include the target itself.
        # ----------------------------------------------------

        if video_id == target_id:
            continue

        related = related_index.get(
            video_id
        )

        # ----------------------------------------------------
        # Existing relationship signals
        # ----------------------------------------------------

        if related:

            related_score = _get_related_score(
                related
            )

            series_identity = _get_series_identity(
                related
            )

            numbered_series_score = (
                _get_numbered_series_score(
                    related
                )
            )

            title_similarity = (
                _get_title_similarity(
                    related
                )
            )

            content_type_score = (
                _get_content_type_score(
                    related
                )
            )

            related_temporal_score = (
                _get_temporal_score(
                    related
                )
            )

        else:

            related_score = 0.0
            series_identity = 0.0
            numbered_series_score = 0.0
            title_similarity = 0.0
            content_type_score = 0.0
            related_temporal_score = 0.0

        # ----------------------------------------------------
        # Actual spike information
        # ----------------------------------------------------

        spike = spike_index.get(
            video_id
        )

        if spike:

            spike_ratio = _safe_float(
                spike.get(
                    "spike_ratio",
                    0.0
                )
            )

            robust_z = _safe_float(
                spike.get(
                    "robust_z",
                    0.0
                )
            )

            spike_signal = spike.get(
                "signal"
            )

        else:

            spike_ratio = 0.0
            robust_z = 0.0
            spike_signal = None

        # ----------------------------------------------------
        # Performance within audience-peak year
        # ----------------------------------------------------

        performance_score = (
            _calculate_performance_score(
                video,
                year_videos
            )
        )

        # ----------------------------------------------------
        # Temporal relevance
        # ----------------------------------------------------

        temporal_score = (
            related_temporal_score
            if related
            else _calculate_temporal_score(
                target_video,
                video,
                audience_peak_year
            )
        )

        # ----------------------------------------------------
        # Candidate score
        #
        # This ranks research candidates.
        # It is NOT a causal score.
        # ----------------------------------------------------

        candidate_score = (
            series_identity * 0.25
            + numbered_series_score * 0.10
            + related_score * 0.20
            + performance_score * 0.25
            + temporal_score * 0.10
            + content_type_score * 0.05
            + (
                min(
                    spike_ratio / 10.0,
                    1.0
                )
                * 0.05
            )
        )

        candidate_score = round(
            candidate_score,
            4
        )

        # ----------------------------------------------------
        # Relationship
        # ----------------------------------------------------

        relationship = _relationship_label(
            series_identity=series_identity,
            numbered_series_score=numbered_series_score,
            related_score=related_score,
            spike=spike,
        )

        # ----------------------------------------------------
        # Structured evidence
        # ----------------------------------------------------

        evidence = _build_evidence(
            series_identity=series_identity,
            numbered_series_score=numbered_series_score,
            performance_score=performance_score,
            spike=spike,
            temporal_score=temporal_score,
        )

        # ----------------------------------------------------
        # Research priority
        # ----------------------------------------------------

        research_priority = _research_priority(
            series_identity=series_identity,
            numbered_series_score=numbered_series_score,
            performance_score=performance_score,
            spike=spike,
        )

        # ----------------------------------------------------
        # Why this candidate exists
        # ----------------------------------------------------

        reasons = []

        if series_identity >= 1.0:

            reasons.append(
                "same series continued during "
                "the audience-peak year"
            )

        if numbered_series_score >= 0.75:

            reasons.append(
                "appears to be a later episode "
                "in the same numbered series"
            )

        if performance_score >= 0.90:

            reasons.append(
                "among the highest-viewed videos "
                "in the audience-peak year"
            )

        elif performance_score >= 0.75:

            reasons.append(
                "above-average performance during "
                "the audience-peak year"
            )

        if spike:

            reasons.append(
                "itself detected as a performance spike"
            )

        if not reasons:

            reasons.append(
                "potentially relevant channel activity "
                "during the audience-peak year"
            )

        # ----------------------------------------------------
        # Research hypothesis
        # ----------------------------------------------------

        if (
            series_identity >= 1.0
            and numbered_series_score >= 0.75
        ):

            possible_mechanism = (
                "Viewers discovering or watching the later "
                "episode may have explored earlier episodes "
                "of the same series."
            )

        elif series_identity >= 1.0:

            possible_mechanism = (
                "Later activity in the same recurring series "
                "may have renewed interest in older content."
            )

        elif performance_score >= 0.90:

            possible_mechanism = (
                "High-performing channel activity during the "
                "audience-peak year may have increased broader "
                "channel attention, potentially creating an "
                "opportunity for older videos to be rediscovered."
            )

        else:

            possible_mechanism = (
                "The candidate represents channel activity "
                "that coincided with the audience-peak year "
                "and may warrant further investigation."
            )

        # ----------------------------------------------------
        # Final candidate object
        # ----------------------------------------------------

        candidates.append({

            "video_id": video_id,

            "title": video.get(
                "title",
                ""
            ),

            "date": video.get(
                "published_at"
            ),

            "views": _safe_int(
                video.get(
                    "views",
                    0
                )
            ),

            "relationship": relationship,

            # Ranking for research ordering.
            # NOT causal probability.
            "candidate_score": candidate_score,

            "research_priority": research_priority,

            # ------------------------------------------------
            # Relationship signals
            # ------------------------------------------------

            "title_similarity": round(
                title_similarity,
                4
            ),

            "series_identity": round(
                series_identity,
                4
            ),

            "numbered_series_score": round(
                numbered_series_score,
                4
            ),

            "existing_related_score": round(
                related_score,
                4
            ),

            "temporal_score": round(
                temporal_score,
                4
            ),

            "content_type_score": round(
                content_type_score,
                4
            ),

            # ------------------------------------------------
            # Performance signals
            # ------------------------------------------------

            "performance_score": round(
                performance_score,
                4
            ),

            "spike_ratio": round(
                spike_ratio,
                4
            ),

            "robust_z": round(
                robust_z,
                4
            ),

            "spike_signal": spike_signal,

            "is_spike": spike is not None,

            # ------------------------------------------------
            # Cross-year context
            # ------------------------------------------------

            "target_upload_year": target_year,

            "audience_peak_year": (
                audience_peak_year
            ),

            "year_gap": (
                audience_peak_year - target_year
                if (
                    audience_peak_year is not None
                    and target_year is not None
                )
                else None
            ),

            # ------------------------------------------------
            # Human-readable reasoning
            # ------------------------------------------------

            "reasons": reasons,

            "possible_mechanism": possible_mechanism,

            # ------------------------------------------------
            # Structured evidence
            # ------------------------------------------------

            "evidence": evidence,

            # ------------------------------------------------
            # Causality
            # ------------------------------------------------

            "causal_claim": None,

            "causal_evidence_found": False,

            # Explicitly tells downstream research that this
            # needs investigation rather than being treated
            # as established causality.
            "requires_external_validation": True,

        })

    # --------------------------------------------------------
    # RANK
    # --------------------------------------------------------

    candidates.sort(
        key=lambda candidate: (
            candidate["candidate_score"],
            candidate["performance_score"],
            candidate["views"],
        ),
        reverse=True,
    )

    return candidates[
        :max_candidates
    ]