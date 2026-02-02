"""
Main routes with optional authentication.
"""
from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import News
from app.utils.recommendations import get_recommendations

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@jwt_required(optional=True)
def home():
    """Home page with optional authentication."""
    # Use published_date instead of created_at
    latest_news = News.query.order_by(News.published_date.desc()).limit(10).all()
    
    current_user_id = get_jwt_identity()
    recommendations = get_recommendations(user_id=current_user_id, limit=5)
    
    return render_template(
        'pages/home.html',
        latest_news=latest_news,
        recommendations=recommendations,
        is_logged_in=(current_user_id is not None)
    )


@main_bp.route('/health')
def health():
    """Health check endpoint."""
    from app.extensions import db
    try:
        db.session.execute('SELECT 1')
        return {'status': 'ok', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'error', 'database': 'disconnected', 'error': str(e)}, 500