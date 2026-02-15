"""
News service for managing news articles and incidents.
"""
from sqlalchemy import or_
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
                or_(
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
    
    @staticmethod
    def get_news_by_group(group_id):
        """Get all news articles by group_id."""
        return News.query.filter_by(group_id=group_id).order_by(News.published_date.desc()).all()

    @staticmethod
    def create_or_link_incident(news_article):
        """
        Auto-create or link incident when news is added.
        Called automatically by scheduler/API.
        """
        from datetime import timedelta, datetime
        
        if not news_article.published_date:
            news_article.published_date = datetime.utcnow().date()
        
        # Find matching incident (7-day window)
        time_start = news_article.published_date - timedelta(days=7)
        time_end = news_article.published_date + timedelta(days=7)
        
        incident = Incident.query.filter(
            Incident.location == news_article.location,
            Incident.incident_type == news_article.incident_type,
            Incident.first_reported >= time_start,
            Incident.last_reported <= time_end
        ).first()
        
        if incident:
            # Update existing incident dates
            if news_article.published_date < incident.first_reported:
                incident.first_reported = news_article.published_date
            if news_article.published_date > incident.last_reported:
                incident.last_reported = news_article.published_date
        else:
            # Create new incident
            incident = Incident(
                incident_type=news_article.incident_type,
                location=news_article.location,
                first_reported=news_article.published_date,
                last_reported=news_article.published_date
            )
            db.session.add(incident)
            db.session.flush()
        
        # Link news to incident
        link = IncidentNews.query.filter_by(
            incident_id=incident.incident_id,
            news_id=news_article.news_id
        ).first()
        
        if not link:
            link = IncidentNews(
                incident_id=incident.incident_id,
                news_id=news_article.news_id
            )
            db.session.add(link)
        
        db.session.commit()
        return incident
    
    @staticmethod
    def add_news_with_incident(title, content='', summary='', location='', 
                               incident_type='', source_id=None, published_date=None):
        """
        Add news from API/scheduler and auto-create incident.
        
        USE THIS in your scheduler instead of directly creating News.
        """
        from datetime import datetime
        
        if not published_date:
            published_date = datetime.utcnow().date()
        elif isinstance(published_date, str):
            try:
                published_date = datetime.strptime(published_date, '%Y-%m-%d').date()
            except:
                published_date = datetime.utcnow().date()
        
        # Check duplicate
        existing = News.query.filter_by(title=title, published_date=published_date).first()
        if existing:
            return existing, None
        
        # Create news
        news = News(
            source_id=source_id,
            title=title,
            summary=summary,
            content=content,
            location=location or 'Unknown',
            incident_type=incident_type or 'General',
            published_date=published_date
        )
        db.session.add(news)
        db.session.flush()
        
        # Auto-create incident
        incident = NewsService.create_or_link_incident(news)
        return news, incident
    
    @staticmethod
    def fix_existing_ungrouped_news():
        """
        ONE-TIME FIX: Group all existing news into incidents.
        Run this once to fix existing data.
        """
        all_news = News.query.all()
        fixed = 0
        
        for news in all_news:
            existing = IncidentNews.query.filter_by(news_id=news.news_id).first()
            if not existing:
                NewsService.create_or_link_incident(news)
                fixed += 1
        
        return fixed
    
    