"""
Recommendation utility.

Recommendations:
- Based on user viewing history
- Tracks category preferences
- Returns recent news from preferred categories
"""
from collections import Counter
from datetime import datetime, timedelta
from app.models import UserHistory, News
from app.extensions import db


def get_recommendations(user_id, limit=10):
    """
    Get personalized news recommendations for a user.
    
    Args:
        user_id: The user ID to generate recommendations for
        limit: Maximum number of recommendations to return
        
    Returns:
        list: List of recommended News objects
    """
    if not user_id:
        # Return recent news if no user specified
        return News.query.order_by(News.published_date.desc()).limit(limit).all()
    
    # Get user's viewing history (last 30 days)
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    history = db.session.query(UserHistory).filter(
        UserHistory.user_id == user_id,
        UserHistory.viewed_at >= thirty_days_ago
    ).all()
    
    if not history:
        # Return recent news if no history
        return News.query.order_by(News.published_date.desc()).limit(limit).all()
    
    # Get news IDs from history
    viewed_news_ids = [h.news_id for h in history]
    
    # Get news articles from history
    viewed_news = db.session.query(News).filter(
        News.news_id.in_(viewed_news_ids)
    ).all()
    
    # Count incident types (categories) from viewed news
    category_counter = Counter()
    location_counter = Counter()
    
    for news in viewed_news:
        if news.incident_type:
            category_counter[news.incident_type] += 1
        if news.location:
            location_counter[news.location] += 1
    
    # Get top categories and locations
    top_categories = [cat for cat, _ in category_counter.most_common(3)]
    top_locations = [loc for loc, _ in location_counter.most_common(3)]
    
    # Build recommendation query
    query = db.session.query(News).filter(
        News.news_id.notin_(viewed_news_ids)  # Exclude already viewed
    )
    
    # Filter by preferred categories or locations
    if top_categories or top_locations:
        filters = []
        if top_categories:
            filters.append(News.incident_type.in_(top_categories))
        if top_locations:
            filters.append(News.location.in_(top_locations))
        query = query.filter(db.or_(*filters))
    
    # Order by recent and limit
    recommendations = query.order_by(News.published_date.desc()).limit(limit).all()
    
    # If not enough recommendations, fill with recent news
    if len(recommendations) < limit:
        recent_news = News.query.filter(
            News.news_id.notin_(viewed_news_ids + [n.news_id for n in recommendations])
        ).order_by(News.published_date.desc()).limit(limit - len(recommendations)).all()
        recommendations.extend(recent_news)
    
    return recommendations
