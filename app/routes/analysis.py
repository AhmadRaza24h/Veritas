
"""
Analysis blueprint for event-based analysis pages.
"""
from app.models import AnalysisCache, Incident, IncidentNews, News
from flask import Blueprint, render_template, abort
from app.services import NewsService, AnalysisService
from app.extensions import db

analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/event/<int:group_id>')
def analysis_detail(group_id):
    """Analysis detail page for a real-world grouped news event."""

    # --------------------------------------------------
    # Get all articles belonging to this event
    # --------------------------------------------------
    group_articles = NewsService.get_news_by_group(group_id)

    incident_link = IncidentNews.query.filter_by(
            news_id=group_articles[0].news_id
        ).first()
    incident_id=incident_link.incident_id
    incident_data = NewsService.get_incident_by_id(incident_id)

    if not group_articles:
        abort(404)

    # Use first article for shared info
    primary_article = group_articles[0]
    
    incident_news=NewsService.get_incident_news(incident_id)

    simillar_incidents = AnalysisService.get_similar_incidents(incident_id, limit=5)

    # --------------------------------------------------
    # Get analysis (group-based)
    # --------------------------------------------------
    analysis = AnalysisService.get_or_create_analysis(group_id)

    scores = AnalysisService.get_credibility_scores(primary_article, group_articles)
           


    # --------------------------------------------------
    # Time-based insights
    # --------------------------------------------------
    time_data = AnalysisService.incidents_over_time(incident_id)

    # --------------------------------------------------
    # City / location insights
    # --------------------------------------------------
    city_data = AnalysisService.incidents_by_city(incident_id)

    return render_template (
        'analysis/detail.html',
        incident_news=incident_news,
        analysis=analysis,
        group_articles=group_articles,
        scores=scores,
        time_data=time_data,
        city_data=city_data,
        incident=incident_data,
        similar_incidents=simillar_incidents

    )
