"""
API blueprint for JSON endpoints.
Enhanced version with better error handling and validation.
"""
from flask import Blueprint, jsonify, request, abort
from app.services import NewsService, AnalysisService

api_bp = Blueprint('api', __name__)


@api_bp.route('/news')
def api_news_list():
    """API endpoint for news list with pagination."""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        
        pagination = NewsService.get_news_paginated(page=page, per_page=per_page)
        
        return jsonify({
            'success': True,
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
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch news',
            'message': str(e)
        }), 500


@api_bp.route('/analysis/<int:incident_id>')
def api_analysis_detail(incident_id):
    """API endpoint for analysis detail."""
    try:
        # Get incident
        incident = NewsService.get_incident_by_id(incident_id)
        
        if not incident:
            return jsonify({
                'success': False,
                'error': 'Incident not found'
            }), 404
        
        # Get analysis
        analysis = AnalysisService.get_or_create_analysis(incident_id)
        
        if not analysis:
            return jsonify({
                'success': False,
                'error': 'Failed to generate analysis'
            }), 500
        
        # Get news for this incident
        incident_news = NewsService.get_incident_news(incident_id)
        
        # Get similar incidents
        similar_incidents = AnalysisService.get_similar_incidents(incident_id, limit=5)
        
        return jsonify({
            'success': True,
            'incident': {
                'incident_id': incident.incident_id,
                'incident_type': incident.incident_type,
                'location': incident.location,
                'first_reported': incident.first_reported.isoformat() if incident.first_reported else None,
                'last_reported': incident.last_reported.isoformat() if incident.last_reported else None
            },
            'analysis': analysis,
            'news_count': len(incident_news),
            'news': [
                {
                    'news_id': news.news_id,
                    'title': news.title,
                    'summary': news.summary,
                    'source_name': news.source.source_name if news.source else None
                }
                for news in incident_news
            ],
            'similar_incidents': [
                {
                    'incident_id': sim.incident_id,
                    'incident_type': sim.incident_type,
                    'location': sim.location,
                    'first_reported': sim.first_reported.isoformat() if sim.first_reported else None
                }
                for sim in similar_incidents
            ]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Internal server error',
            'message': str(e)
        }), 500


@api_bp.route('/analysis/<int:incident_id>/refresh', methods=['POST'])
def api_refresh_analysis(incident_id):
    """Force refresh analysis for an incident."""
    try:
        # Check if incident exists
        incident = NewsService.get_incident_by_id(incident_id)
        if not incident:
            return jsonify({
                'success': False,
                'error': 'Incident not found'
            }), 404
        
        # Refresh analysis
        analysis = AnalysisService.refresh_analysis_cache(incident_id)
        
        if not analysis:
            return jsonify({
                'success': False,
                'error': 'Failed to refresh analysis'
            }), 500
        
        return jsonify({
            'success': True,
            'message': 'Analysis refreshed successfully',
            'analysis': analysis
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to refresh analysis',
            'message': str(e)
        }), 500


@api_bp.route('/recommendations')
def api_recommendations():
    """API endpoint for recommendations."""
    try:
        user_id = request.args.get('user_id', None, type=int)
        limit = min(request.args.get('limit', 10, type=int), 50)
        
        recommendations = AnalysisService.get_user_recommendations(user_id, limit=limit)
        
        return jsonify({
            'success': True,
            'user_id': user_id,
            'personalized': user_id is not None,
            'recommendations': [
                {
                    'news_id': news.news_id,
                    'title': news.title,
                    'summary': news.summary,
                    'location': news.location,
                    'incident_type': news.incident_type,
                    'published_date': news.published_date.isoformat() if news.published_date else None,
                    'source': {
                        'name': news.source.source_name,
                        'category': news.source.category
                    } if news.source else None
                }
                for news in recommendations
            ]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch recommendations',
            'message': str(e)
        }), 500


@api_bp.route('/analysis/stats')
def api_analysis_stats():
    """Get overall analysis statistics."""
    try:
        stats = AnalysisService.get_analysis_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': 'Failed to fetch statistics',
            'message': str(e)
        }), 500


# Health check endpoint
@api_bp.route('/health')
def api_health():
    """API health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'Veritas Analysis API',
        'version': '1.0.0'
    }), 200