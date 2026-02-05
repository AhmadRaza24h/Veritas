"""
API blueprint for JSON endpoints.
"""
from flask import Blueprint, jsonify, request, abort
from app.services import NewsService, AnalysisService

api_bp = Blueprint('api', __name__)


@api_bp.route('/news')
def api_news_list():
    """API endpoint for news list."""
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)  # Max 100 items per page
    
    pagination = NewsService.get_news_paginated(page=page, per_page=per_page)
    
    return jsonify({
        'news': [
            {
                'news_id': news.news_id,
                'title': news.title,
                'summary': news.summary,
                'location': news.location,
                'incident_type': news.incident_type,
                'published_date': news.published_date.isoformat() if news.published_date else None,
                'source': {
                    'source_id': news.source.source_id,
                    'name': news.source.source_name,
                    'category': news.source.category
                } if news.source else None
            }
            for news in pagination.items
        ],
        'pagination': {
            'page': pagination.page,
            'per_page': pagination.per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@api_bp.route('/analysis/<int:incident_id>')
def api_analysis_detail(incident_id):
    """API endpoint for analysis detail."""
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
    
    return jsonify({
        'incident': {
            'incident_id': incident.incident_id,
            'incident_type': incident.incident_type,
            'location': incident.location,
            'first_reported': incident.first_reported.isoformat() if incident.first_reported else None,
            'last_reported': incident.last_reported.isoformat() if incident.last_reported else None
        },
        'analysis': analysis,
        'news_count': len(incident_news),
        'similar_incidents': [
            {
                'incident_id': sim.incident_id,
                'incident_type': sim.incident_type,
                'location': sim.location,
                'first_reported': sim.first_reported.isoformat() if sim.first_reported else None
            }
            for sim in similar_incidents
        ]
    })


@api_bp.route('/recommendations')
def api_recommendations():
    """API endpoint for recommendations."""
    user_id = request.args.get('user_id', 1, type=int)
    limit = min(request.args.get('limit', 10, type=int), 50)  # Max 50 recommendations
    
    recommendations = AnalysisService.get_user_recommendations(user_id, limit=limit)
    
    return jsonify({
        'recommendations': [
            {
                'news_id': news.news_id,
                'title': news.title,
                'summary': news.summary,
                'location': news.location,
                'incident_type': news.incident_type,
                'published_date': news.published_date.isoformat() if news.published_date else None
            }
            for news in recommendations
        ]
    })
@api_bp.route('/scheduler/jobs')
def get_scheduler_jobs():
    """Get list of scheduled jobs and their status."""
    from app.services.scheduler_service import scheduler_service
    
    jobs = scheduler_service.get_jobs()
    
    return jsonify({
        'success': True,
        'data': {
            'jobs': jobs,
            'scheduler_running': scheduler_service.scheduler.running,
            'total_jobs': len(jobs)
        }
    })


@api_bp.route('/scheduler/stats')
def get_scheduler_stats():
    """Get data ingestion statistics."""
    from app.models import Source
    
    # Count news by source
    sources = Source.query.all()
    stats = []
    
    for source in sources:
        stats.append({
            'source_name': source.source_name,
            'category': source.category,
            'news_count': len(source.news)
        })
    
    total_news = News.query.count()
    
    return jsonify({
        'success': True,
        'data': {
            'total_news': total_news,
            'sources': stats
        }
    })