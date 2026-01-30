"""
Main blueprint for home page and general routes.
"""
from flask import Blueprint, render_template
from app.services import NewsService, AnalysisService

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def home():
    """Home page with latest news and recommendations."""
    # Get latest news
    latest_news = NewsService.get_latest_news(limit=10)
    
    # Get recommendations (using user_id=1 as default for demo)
    # In production, this would use the logged-in user's ID
    recommendations = AnalysisService.get_user_recommendations(user_id=1, limit=5)
    
    return render_template(
        'pages/home.html',
        latest_news=latest_news,
        recommendations=recommendations
    )


@main_bp.route('/health')
def health():
    """Health check endpoint."""
    return {'status': 'ok'}, 200
