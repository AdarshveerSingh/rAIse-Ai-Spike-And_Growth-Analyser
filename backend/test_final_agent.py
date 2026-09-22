import json

from app.reporting.final_agent import generate_final_report


# ---------------------------------------------------------
# Target event
# ---------------------------------------------------------

target_event = {
    "video_id": "OzItHn9GSRE",
    "title": "Drunk Minecraft #1 | A NEW HOPE",
    "date": "2012-08-09T01:47:50Z",
    "views": 10617804,
    "spike_ratio": 168.513,
    "robust_z": 24.6,
    "event_type": "SUSTAINED_EVENTUAL",
}


# ---------------------------------------------------------
# Quantitative analysis
# ---------------------------------------------------------

quantitative_analysis = {
    "channel": "Markiplier",
    "total_videos": 5794,

    "target": {
        "title": target_event["title"],
        "views": target_event["views"],
        "spike_ratio": target_event["spike_ratio"],
        "robust_z": target_event["robust_z"],
    },

    "classification": "SUSTAINED_EVENTUAL",

    "before": [
        {
            "title": "Orcs Must Die 2 w/ MY BROTHER | Part 5 | TAR TRAPS FTW",
            "views": 49167,
        },
        {
            "title": "Orcs Must Die 2 w/ MY BROTHER | Part 6 | SPIKES WERE A BAD CHOICE",
            "views": 39915,
        },
        {
            "title": "The Corridor",
            "views": 1259341,
        },
    ],

    "after": [
        {
            "title": "Cry of Fear: Out of It | Part 1 | GOING OUT OF MY HEAD",
            "views": 107164,
        },
        {
            "title": "Orcs Must Die 2 w/ MY BROTHER | Part 7 | ORC DECIMATION",
            "views": 41277,
        },
        {
            "title": "Cry of Fear: Out of It | Part 2 | STRANGE HAPPENINGS",
            "views": 54222,
        },
    ],
}


# ---------------------------------------------------------
# Audience analysis
# ---------------------------------------------------------

audience_analysis = {
    "peak_interaction_year": 2013,
    "peak_comment_share": 0.17,
    "sample_size": 100,
    "total_available_comments": 15089,

    "comment_themes": [
        "nostalgia",
        "series references",
        "collaborator references",
        "recommendation/discovery language",
    ],

    "limitations": [
        "Comment sample is not necessarily representative of the entire audience.",
        "Public comments cannot establish private traffic sources."
    ],
}


# ---------------------------------------------------------
# Cross-year candidates
# ---------------------------------------------------------

cross_year_analysis = {
    "target_upload_year": 2012,
    "audience_peak_year": 2013,

    "candidates": [
        {
            "video_id": "candidate1",
            "title": "Drunk Minecraft #42",
            "views": 3609241,
            "candidate_score": 0.4213,
            "research_priority": "HIGH",
            "existing_related_score": 0.8567,
            "performance_score": 1.0,
        },
        {
            "video_id": "candidate2",
            "title": "Drunk Minecraft #60",
            "views": 2656723,
            "candidate_score": 0.3587,
            "research_priority": "MEDIUM",
            "existing_related_score": 0.7933,
            "performance_score": 0.8,
        },
        {
            "video_id": "candidate3",
            "title": "Drunk Minecraft #56",
            "views": 2519206,
            "candidate_score": 0.315,
            "research_priority": "LOW",
            "existing_related_score": 0.8251,
            "performance_score": 0.6,
        },
        {
            "video_id": "candidate4",
            "title": "Drunk Minecraft #52",
            "views": 2166009,
            "candidate_score": 0.2578,
            "research_priority": "LOW",
            "existing_related_score": 0.7891,
            "performance_score": 0.4,
        },
        {
            "video_id": "candidate5",
            "title": "Drunk Minecraft #59",
            "views": 1990143,
            "candidate_score": 0.2025,
            "research_priority": "LOW",
            "existing_related_score": 0.7623,
            "performance_score": 0.2,
        },
    ],

    "causal_evidence_found": False,

    "limitations": [
        "Cross-year candidates identify related high-performing videos.",
        "They do not establish that these videos caused the original growth."
    ],
}


# ---------------------------------------------------------
# Thumbnail analysis
# ---------------------------------------------------------

thumbnail_analysis = {
    "target": {
        "title": "Drunk Minecraft #1 | A NEW HOPE",
        "visual_analysis": {
            "has_face": True,
            "face_count": 1,
            "expression": "smiling",
            "has_text": True,
            "text_amount": "medium",
            "subject_position": "right",
            "shot_type": "medium_shot",
            "high_contrast": True,
            "arrows_or_circles": False,
            "visual_complexity": "medium",
            "branding_elements": True,
            "main_subject": (
                "Minecraft avatar on the right, grassy terrain, "
                "left-side DRUNK MINECRAFT PART 1 text"
            ),
        },
    },

    "before": [
        {
            "title": "Orcs Must Die 2 Part 5",
            "views": 49167,
            "visual_analysis": {
                "has_face": True,
                "expression": "shouting",
                "text_amount": "medium",
                "subject_position": "center",
                "shot_type": "medium_shot",
                "high_contrast": True,
                "visual_complexity": "high",
                "branding_elements": True,
            },
        },
        {
            "title": "Orcs Must Die 2 Part 6",
            "views": 39915,
            "visual_analysis": {
                "has_face": True,
                "expression": "shouting/excited",
                "text_amount": "high",
                "subject_position": "center",
                "shot_type": "medium_shot",
                "high_contrast": True,
                "visual_complexity": "high",
                "branding_elements": True,
            },
        },
        {
            "title": "The Corridor",
            "views": 1259341,
            "visual_analysis": {
                "has_face": True,
                "expression": "screaming",
                "text_amount": "low",
                "subject_position": "center",
                "shot_type": "close_up",
                "high_contrast": True,
                "visual_complexity": "medium",
                "branding_elements": False,
            },
        },
    ],

    "after": [
        {
            "title": "Cry of Fear Part 1",
            "views": 107164,
        },
        {
            "title": "Orcs Must Die 2 Part 7",
            "views": 41277,
        },
        {
            "title": "Cry of Fear Part 2",
            "views": 54222,
        },
    ],

    "phash_similarities": {
        "Orcs Must Die 2 Part 5": 0.531,
        "Orcs Must Die 2 Part 6": 0.531,
        "The Corridor": 0.469,
        "Cry of Fear Part 1": 0.500,
        "Orcs Must Die 2 Part 7": 0.531,
        "Cry of Fear Part 2": 0.500,
    },

    "observations": [
        "The target thumbnail was visually distinct from the immediately preceding thumbnails.",
        "The target moved the main subject toward the right.",
        "The target used medium rather than high text density.",
        "The target used a smiling expression rather than the shouting/screaming expressions in several preceding thumbnails.",
        "The target retained high contrast."
    ],
}


# ---------------------------------------------------------
# Research
# ---------------------------------------------------------

research = {
    "event_type": "SUSTAINED_EVENTUAL",

    "research_window": {
        "start": "2012-02-09",
        "event": "2012-08-09",
        "end": "2012-11-09",
    },

    "summary": (
        "The event corresponds to the beginning of the recurring "
        "Drunk Minecraft series. The video involved collaborators "
        "and was followed by additional episodes."
    ),

    "direct_findings": [
        "Drunk Minecraft became a recurring series.",
        "The target involved collaborators.",
        "Additional episodes followed the target.",
        "The video description contained references to the server/promotion."
    ],

    "audience_findings": [
        "Sampled comments contained nostalgia.",
        "Comments referenced the series and collaborators.",
        "Some comments contained recommendation/discovery language."
    ],

    "cross_year_analysis": {
        "target_upload_year": 2012,
        "audience_peak_year": 2013,
        "peak_comment_share": 0.17,
        "causal_evidence_found": False,
    },

    "limitations": [
        "No private creator analytics.",
        "No verified contemporaneous paid promotion records.",
        "No verified contemporaneous social promotion evidence.",
        "Comment sample is limited and may not be representative.",
        "Public data does not establish private traffic sources."
    ],

    "sources": []
}


# ---------------------------------------------------------
# Generate report
# ---------------------------------------------------------

print("\nGenerating final report...\n")

report = generate_final_report(
    creator="Markiplier",
    event=target_event,
    quantitative_analysis=quantitative_analysis,
    research=research,
    audience_analysis=audience_analysis,
    cross_year_analysis=cross_year_analysis,
    thumbnail_analysis=thumbnail_analysis,
)


# ---------------------------------------------------------
# Print result
# ---------------------------------------------------------

print(json.dumps(
    report,
    indent=2,
    ensure_ascii=False
))