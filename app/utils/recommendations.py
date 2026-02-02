"""
Recommendation utility with optional authentication.
"""
from collections import Counter
from datetime import datetime, timedelta
from sqlalchemy import or_
from app.models import UserHistory, News
from app.extensions import db


def get_recommendations(user_id=None, limit=10):
    """
    Get personalized news recommendations.
    
    Args:
        user_id: User ID (None for guest users)
        limit: Number of recommendations
    
    Returns:
        list: List of recommended News objects
    """
    if not user_id:
        # Guest user: return recent news
        return News.query.order_by(News.published_date.desc()).limit(limit).all()
    
    # Logged in user: personalized recommendations
    thirty_days_ago = datetime.utcnow() - timedelta(days=30)
    
    history = db.session.query(UserHistory).filter(
        UserHistory.user_id == user_id,
        UserHistory.viewed_at >= thirty_days_ago
    ).all()
    
    if not history:
        return News.query.order_by(News.published_date.desc()).limit(limit).all()
    
    viewed_news_ids = [h.news_id for h in history]
    
    viewed_news = db.session.query(News).filter(
        News.news_id.in_(viewed_news_ids)
    ).all()
    
    category_counter = Counter()
    location_counter = Counter()
    
    for news in viewed_news:
        if news.incident_type:
            category_counter[news.incident_type] += 1
        if news.location:
            location_counter[news.location] += 1
    
    top_categories = [cat for cat, _ in category_counter.most_common(3)]
    top_locations = [loc for loc, _ in location_counter.most_common(3)]
    
    query = db.session.query(News).filter(
        News.news_id.not_in(viewed_news_ids)
    )
    
    if top_categories or top_locations:
        filters = []
        if top_categories:
            filters.append(News.incident_type.in_(top_categories))
        if top_locations:
            filters.append(News.location.in_(top_locations))
        query = query.filter(or_(*filters))
    
    recommendations = query.order_by(News.published_date.desc()).limit(limit).all()
    
    if len(recommendations) < limit:
        recent = News.query.filter(
            News.news_id.not_in(viewed_news_ids + [n.news_id for n in recommendations])
        ).order_by(News.published_date.desc()).limit(limit - len(recommendations)).all()
        recommendations.extend(recent)
    
    return recommendations