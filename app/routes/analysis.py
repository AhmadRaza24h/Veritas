"""
Analysis blueprint for analysis pages.
"""
from flask import Blueprint, render_template, abort
from app.services import NewsService, AnalysisService

analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/<int:incident_id>')
def analysis_detail(incident_id):
    """Analysis detail page for an incident."""
    # Get incident
    incident = NewsService.get_incident_by_id(incident_id)
    
    if not incident:
        abort(404)
    
    # Get analysis
    analysis = AnalysisService.get_or_create_analysis(incident_id)
    
    # Get news for this incident
    incident_news = NewsService.get_incident_news(incident_id)
    
    # Get similar incidents
    similar_incidents = AnalysisService.get_similar_incidents(incident_id, limit=5)

    #Get incidents over time
    time_data = AnalysisService.incidents_over_time(incident_id)
    #Get incidents by city
    city_data = AnalysisService.incidents_by_city(incident_id)

    
    return render_template(
    'analysis/detail.html',
    incident=incident,
    analysis=analysis,
    time_data=time_data,
    city_data=city_data,
    similar_incidents=similar_incidents
)
