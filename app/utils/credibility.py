"""
Credibility scoring utility.

Credibility Score Calculation:
- Source diversity (40%): More diverse sources = higher score
- Location clarity (30%): Clear location information = higher score
- Completeness (30%): Complete information (title, content, summary) = higher score
"""


def calculate_credibility_score(incident_news_list):
    """
    Calculate credibility score for an incident.
    
    Args:
        incident_news_list: List of news articles linked to the incident
        
    Returns:
        int: Credibility score (0-100)
    """
    if not incident_news_list:
        return 0
    
    # Calculate source diversity (40%)
    unique_sources = set()
    for news in incident_news_list:
        if news.source_id:
            unique_sources.add(news.source_id)
    
    # Score based on number of unique sources (max 5 sources for 100%)
    source_diversity_score = min(len(unique_sources) / 5.0, 1.0) * 40
    
    # Calculate location clarity (30%)
    locations_with_clarity = sum(
        1 for news in incident_news_list 
        if news.location and len(news.location.strip()) > 0
    )
    location_clarity_score = (locations_with_clarity / len(incident_news_list)) * 30
    
    # Calculate completeness (30%)
    complete_articles = sum(
        1 for news in incident_news_list
        if news.title and news.content and news.summary
    )
    completeness_score = (complete_articles / len(incident_news_list)) * 30
    
    # Total credibility score
    total_score = source_diversity_score + location_clarity_score + completeness_score
    
    return int(round(total_score))
