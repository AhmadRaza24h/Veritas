"""
Analysis service for orchestrating analysis operations.
"""
from datetime import datetime
from app.models import AnalysisCache, Incident, IncidentNews, News
from app.extensions import db
from sqlalchemy import func

from app.utils import (
    calculate_credibility_score,
    calculate_perspective_distribution,
    find_similar_incidents,
    get_recommendations
)


class AnalysisService:
    """Service class for analysis operations."""
    
    
    @staticmethod
    def get_or_create_analysis(group_id, force_refresh=False):
        """
        Get cached analysis or create new one
        based on group_id (same event articles),
        but still linked to incident_id.
        """

        if not group_id:
            return None

        # --------------------------------------------------
        # Fetch all articles of same event
        # --------------------------------------------------
        group_articles = News.query.filter_by(group_id=group_id).all()

        if not group_articles:
            return None

        # --------------------------------------------------
        # Get incident_id from first article in group
        # --------------------------------------------------
        first_article = group_articles[0]

        incident_link = IncidentNews.query.filter_by(
            news_id=first_article.news_id
        ).first()

        if not incident_link:
            return None

        incident_id = incident_link.incident_id

        # --------------------------------------------------
        # Try cache first (by group_id)
        # --------------------------------------------------
        if not force_refresh:
            cached = AnalysisCache.query.filter_by(group_id=group_id).first()
            if cached:
                return AnalysisService._format_analysis(cached)

        # --------------------------------------------------
        # Calculate perspective
        # --------------------------------------------------
        perspective = calculate_perspective_distribution(group_articles)

        # --------------------------------------------------
        # Calculate credibility
        # --------------------------------------------------
        credibility_scores = [
            calculate_credibility_score(article, group_articles)
            for article in group_articles
        ]

        final_credibility = (
            int(sum(credibility_scores) / len(credibility_scores))
            if credibility_scores else 0
        )

        # --------------------------------------------------
        # Save / Update Cache
        # --------------------------------------------------
        cached = AnalysisCache.query.filter_by(group_id=group_id).first()

        if cached:
            cached.credibility_score = final_credibility
            cached.public_pct = perspective['public_pct']
            cached.neutral_pct = perspective['neutral_pct']
            cached.political_pct = perspective['political_pct']
            cached.perspective_summary = perspective['summary']
            cached.generated_at = datetime.utcnow()
        else:
            cached = AnalysisCache(
                group_id=group_id,
                incident_id=incident_id,  # 👈 still storing category reference
                credibility_score=final_credibility,
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
            'group_id': analysis_cache.group_id,
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
    
    @staticmethod
    def incidents_over_time(incident_id):
        rows = (
            db.session.query(
                News.published_date.label('date'),
                func.count(News.news_id).label('count')
            )
            .join(IncidentNews, IncidentNews.news_id == News.news_id)
            .filter(IncidentNews.incident_id == incident_id)
            .group_by(News.published_date)
            .order_by(News.published_date)
            .all()
        )

        return [
            {
                'date': r.date.strftime('%Y-%m-%d'),
                'count': r.count
            }
            for r in rows
            if r.date
        ]



    @staticmethod
    def incidents_by_city(incident_id):
        # get incident first
        incident = Incident.query.get(incident_id)
        if not incident:
            return []

        rows = (
            db.session.query(
                News.location.label('city'),
                func.count(News.news_id).label('count')
            )
            .join(IncidentNews, IncidentNews.news_id == News.news_id)
            .join(Incident, Incident.incident_id == IncidentNews.incident_id)
            .filter(Incident.incident_type == incident.incident_type)
            .group_by(News.location)
            .order_by(func.count(News.news_id).desc())
            .all()
        )

        return [
            {'city': r.city, 'count': r.count}
            for r in rows if r.city
        ]
    
    @staticmethod
    def get_related_news(incident):
        """
        Fetch news related to an incident using incident_type + location
        """
        if not incident:
            return []

        return (
            News.query
            .filter(
                News.incident_type == incident.incident_type,
                News.location == incident.location
            )
            .order_by(News.published_date.desc())
            .all()
        )
    def get_credibility_scores(article, group_articles):

        SOURCE_WEIGHT = {
    "neutral": 1.0,
    "public": 0.8,
    "political": 0.6
    }

   

        if not group_articles:
            return {
                "total": 0,
                "cross_source": 0,
                "reliability": 0,
                "time_convergence": 0
            }

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

            if time_diff <= 6 * 3600:
                close_reports += 1

        time_convergence_score = min(close_reports / 5.0, 1.0) * 20

        # --------------------------------------------------
        # Final Score
        # --------------------------------------------------

        total_score = (
            cross_source_score +
            reliability_score +
            time_convergence_score
        )

        return {
            "total": max(0, min(100, int(round(total_score)))),
            "cross_source": int(round(cross_source_score)),
            "reliability": int(round(reliability_score)),
            "time_convergence": int(round(time_convergence_score))
        }


