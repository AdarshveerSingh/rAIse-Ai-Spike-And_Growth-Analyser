from collections import Counter


def calculate_thumbnail_stats(thumbnail_results):
    """
    Compare visual characteristics across thumbnail groups.

    Groups:
    - baseline
    - before
    - spike
    - after
    - high_performers
    """

    groups = {}

    for result in thumbnail_results:
        if "visual_analysis" not in result:
            continue

        group = result["group"]
        analysis = result["visual_analysis"]

        if group not in groups:
            groups[group] = []

        groups[group].append(analysis)

    features = [
        "has_face",
        "has_text",
        "high_contrast",
        "arrows_or_circles",
        "branding_elements"
    ]

    stats = {}

    for group, analyses in groups.items():

        group_stats = {
            "sample_size": len(analyses)
        }

        for feature in features:
            values = [
                analysis.get(feature)
                for analysis in analyses
                if isinstance(analysis.get(feature), bool)
            ]

            if values:
                count_true = sum(values)

                group_stats[feature] = {
                    "count": count_true,
                    "percentage": round(
                        (count_true / len(values)) * 100,
                        1
                    )
                }

        # Categorical features
        for feature in [
            "text_amount",
            "subject_position",
            "shot_type",
            "visual_complexity",
            "expression"
        ]:

            values = [
                analysis.get(feature)
                for analysis in analyses
                if analysis.get(feature) is not None
            ]

            if values:
                counts = Counter(values)

                group_stats[feature] = dict(
                    counts.most_common()
                )

        stats[group] = group_stats

    return stats