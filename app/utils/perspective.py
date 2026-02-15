"""
Perspective distribution utility (Group-Based).

Calculates perspective diversity for a single group_id.
Uses UNIQUE sources only.
"""


def calculate_perspective_distribution(group_articles):

    if not group_articles:
        return {
            "public": 0,
            "neutral": 0,
            "political": 0,
            "public_pct": 0,
            "neutral_pct": 0,
            "political_pct": 0,
            "summary": "No perspective data available"
        }

    # UNIQUE sources only
    unique_sources = {}

    for news in group_articles:
        if news.source and news.source.category:
            if news.source_id not in unique_sources:
                unique_sources[news.source_id] = news.source.category.lower()

    counts = {
        "public": 0,
        "neutral": 0,
        "political": 0
    }

    for category in unique_sources.values():
        if category in counts:
            counts[category] += 1

    total = sum(counts.values())

    if total == 0:
        return {
            **counts,
            "public_pct": 0,
            "neutral_pct": 0,
            "political_pct": 0,
            "summary": "No categorized sources"
        }

    public_pct = int(round((counts["public"] / total) * 100))
    neutral_pct = int(round((counts["neutral"] / total) * 100))
    political_pct = int(round((counts["political"] / total) * 100))

    dominant = max(counts.items(), key=lambda x: x[1])

    if dominant[1] == total:
        summary = f"Coverage is entirely {dominant[0]}"
    elif dominant[1] >= total * 0.6:
        summary = f"Coverage is primarily {dominant[0]}"
    elif all(counts[c] > 0 for c in counts):
        summary = "Coverage includes multiple perspectives"
    else:
        summary = "Coverage shows mixed perspectives"

    # 🔥 ADD SOURCE COUNT
    summary = f"{summary} ({total} unique source{'s' if total > 1 else ''})"

    return {
        **counts,
        "public_pct": public_pct,
        "neutral_pct": neutral_pct,
        "political_pct": political_pct,
        "summary": summary,
        "total_sources": total  # optional extra field if you want to show separately
    }
