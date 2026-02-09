"""
Main routes with optional authentication.
"""
from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import News
from app.utils.recommendations import get_recommendations

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
@jwt_required(optional=True)  # ✅ IMPORTANT: optional=True
def home():
    """Home page - accessible without login."""
    try:
        # Get latest news (no authentication needed)
        latest_news = News.query.order_by(News.published_date.desc()).limit(10).all()
    except Exception as e:
        print(f"Error fetching news: {e}")
        latest_news = []
    
    # Get user ID if logged in (optional)
    current_user_id = None
    try:
        current_user_id = get_jwt_identity()
    except:
        pass  # No problem if not logged in
    
    # Get recommendations only if user is logged in
    recommendations = []
    if current_user_id:
        try:
            recommendations = get_recommendations(user_id=current_user_id, limit=5)
        except:
            recommendations = []
    
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