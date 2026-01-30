"""
News service for managing news articles and incidents.
"""
from app.models import News, Incident, IncidentNews, Source
from app.extensions import db


class NewsService:
    """Service class for news-related operations."""
    
    @staticmethod
    def get_latest_news(limit=20):
        """Get latest news articles."""
        return News.query.order_by(News.published_date.desc()).limit(limit).all()
    
    @staticmethod
    def get_news_by_id(news_id):
        """Get a single news article by ID."""
        return News.query.get(news_id)
    
    @staticmethod
    def get_news_paginated(page=1, per_page=20):
        """Get paginated news articles."""
        return News.query.order_by(News.published_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
    
    @staticmethod
    def get_incident_by_id(incident_id):
        """Get an incident by ID."""
        return Incident.query.get(incident_id)
    
    @staticmethod
    def get_incident_news(incident_id):
        """Get all news articles for an incident."""
        incident_news_links = IncidentNews.query.filter_by(incident_id=incident_id).all()
        news_ids = [link.news_id for link in incident_news_links]
        return News.query.filter(News.news_id.in_(news_ids)).all()
    
    @staticmethod
    def get_incident_for_news(news_id):
        """Get incident associated with a news article."""
        incident_news = IncidentNews.query.filter_by(news_id=news_id).first()
        if incident_news:
            return Incident.query.get(incident_news.incident_id)
        return None
    
    @staticmethod
    def search_news(query=None, location=None, incident_type=None, page=1, per_page=20):
        """Search news with filters."""
        news_query = News.query
        
        if query:
            search_filter = f'%{query}%'
            news_query = news_query.filter(
                db.or_(
                    News.title.ilike(search_filter),
                    News.summary.ilike(search_filter),
                    News.content.ilike(search_filter)
                )
            )
        
        if location:
            news_query = news_query.filter(News.location.ilike(f'%{location}%'))
        
        if incident_type:
            news_query = news_query.filter(News.incident_type == incident_type)
        
        return news_query.order_by(News.published_date.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
