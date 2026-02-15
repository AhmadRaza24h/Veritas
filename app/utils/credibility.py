"""
Article-level credibility scoring utility.

Credibility Score Calculation (0–100)

Evaluates structural credibility of a news article
based on cross-source validation within same group_id.
"""

from datetime import timedelta

SOURCE_WEIGHT = {
    "neutral": 1.0,
    "public": 0.8,
    "political": 0.6
}


def calculate_credibility_score(article, group_articles):
    """
    Calculate credibility score for a single article using group validation.

    Args:
        article: current article object
        group_articles: list of all articles with same group_id

    Returns:
        int: credibility score (0–100)
    """

    if not group_articles:
        return 0

    # --------------------------------------------------
    # 1️⃣ Cross-Source Confirmation (50%)
    # --------------------------------------------------

    unique_sources = {
        a.source_id for a in group_articles
        if a.source_id is not None
    }

    source_count = len(unique_sources)

    cross_source_score = min(source_count / 3.0, 1.0) * 50


    # --------------------------------------------------
    # 2️⃣ Source Reliability Tier (30%)
    # --------------------------------------------------

    category = (
        article.source.category.lower()
        if article.source and article.source.category
        else "public"
    )

    reliability_score = SOURCE_WEIGHT.get(category, 0.8) * 30

    # --------------------------------------------------
    # 3️⃣ Time Convergence (20%)
    # --------------------------------------------------

    close_reports = 0

    for other in group_articles:
        if other.news_id == article.news_id:
            continue

        if not other.published_date or not article.published_date:
            continue

        time_diff = abs(
            (other.published_date - article.published_date).total_seconds()
        )

        # Within 1 hour window
        if time_diff <= 6 * 3600:  # 6 hours

            close_reports += 1

    time_convergence_score = min(close_reports / 5.0, 1.0) * 20

    # --------------------------------------------------
    # Final Score
    # --------------------------------------------------

    total_score = cross_source_score + reliability_score + time_convergence_score

    return  max(0, min(100, int(round(total_score))))
