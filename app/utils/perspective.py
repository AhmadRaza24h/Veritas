"""
Perspective distribution utility.

Perspective Distribution:
- Count articles by source type: public, neutral, political
- Calculate percentage distribution
"""


def calculate_perspective_distribution(incident_news_list):
    """
    Calculate perspective distribution for an incident.
    
    Args:
        incident_news_list: List of news articles with sources
        
    Returns:
        dict: Distribution with keys 'public_pct', 'neutral_pct', 'political_pct', 'summary'
    """
    if not incident_news_list:
        return {
            'public_pct': 0,
            'neutral_pct': 0,
            'political_pct': 0,
            'summary': 'No perspective data available'
        }
    
    # Count by source type
    counts = {
        'public': 0,
        'neutral': 0,
        'political': 0
    }
    
    total = 0
    for news in incident_news_list:
        if news.source and news.source.category:
            category = news.source.category.lower()
            if category in counts:
                counts[category] += 1
                total += 1
    
    # Calculate percentages
    if total == 0:
        return {
            'public_pct': 0,
            'neutral_pct': 0,
            'political_pct': 0,
            'summary': 'No categorized sources'
        }
    
    public_pct = int(round((counts['public'] / total) * 100))
    neutral_pct = int(round((counts['neutral'] / total) * 100))
    political_pct = int(round((counts['political'] / total) * 100))
    
    # Generate summary
    dominant = max(counts.items(), key=lambda x: x[1])
    summary = f"Coverage is primarily {dominant[0]} ({dominant[1]}/{total} sources)"
    
    return {
        'public_pct': public_pct,
        'neutral_pct': neutral_pct,
        'political_pct': political_pct,
        'summary': summary
    }
