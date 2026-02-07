"""
Analysis service for orchestrating analysis operations.
"""
from datetime import datetime
from app.models import AnalysisCache, Incident, IncidentNews, News
from app.extensions import db
from app.utils import (
    calculate_credibility_score,
    calculate_perspective_distribution,
    find_similar_incidents,
    get_recommendations
)


class AnalysisService:
    """Service class for analysis operations."""
    
    @staticmethod
    def get_or_create_analysis(incident_id, force_refresh=False):
        """
        Get cached analysis or create new one.
        
        Args:
            incident_id: The incident ID to analyze
            force_refresh: Force regeneration of analysis
            
        Returns:
            dict: Analysis results
        """
        # Check for cached analysis
        if not force_refresh:
            cached = AnalysisCache.query.filter_by(incident_id=incident_id).first()
            if cached:
                return AnalysisService._format_analysis(cached)
        
        # Get incident and related news
        incident = Incident.query.get(incident_id)
        if not incident:
            return None
        
        # Get all news for this incident
        incident_news_links = IncidentNews.query.filter_by(incident_id=incident_id).all()
        news_ids = [link.news_id for link in incident_news_links]
        news_list = News.query.filter(News.news_id.in_(news_ids)).all()
        
        # Calculate credibility score
        credibility = calculate_credibility_score(news_list)
        
        # Calculate perspective distribution
        perspective = calculate_perspective_distribution(news_list)
        
        # Save or update cache
        cached = AnalysisCache.query.filter_by(incident_id=incident_id).first()
        if cached:
            cached.credibility_score = credibility
            cached.public_pct = perspective['public_pct']
            cached.neutral_pct = perspective['neutral_pct']
            cached.political_pct = perspective['political_pct']
            cached.perspective_summary = perspective['summary']
            cached.generated_at = datetime.utcnow()
        else:
            cached = AnalysisCache(
                incident_id=incident_id,
                credibility_score=credibility,
                public_pct=perspective['public_pct'],
                neutral_pct=perspective['neutral_pct'],
                political_pct=perspective['political_pct'],
                perspective_summary=perspective['summary']
            )
            db.session.add(cached)
        
        db.session.commit()
        
        return AnalysisService._format_analysis(cached)
    
    @staticmethod
    def _format_analysis(analysis_cache):
        """Format analysis cache for response."""
        return {
            'incident_id': analysis_cache.incident_id,
            'credibility_score': analysis_cache.credibility_score,
            'perspective': {
                'public_pct': analysis_cache.public_pct,
                'neutral_pct': analysis_cache.neutral_pct,
                'political_pct': analysis_cache.political_pct,
                'summary': analysis_cache.perspective_summary
            },
            'generated_at': analysis_cache.generated_at.isoformat() if analysis_cache.generated_at else None
        }
    
    @staticmethod
    def get_similar_incidents(incident_id, limit=5):
        """Get similar incidents for an incident."""
        incident = Incident.query.get(incident_id)
        if not incident:
            return []
        
        return find_similar_incidents(incident, limit=limit)
    
    @staticmethod
    def get_user_recommendations(user_id, limit=10):
        """Get personalized recommendations for a user."""
        return get_recommendations(user_id, limit=limit)