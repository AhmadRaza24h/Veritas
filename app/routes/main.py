"""
Main routes with optional authentication.
"""
from flask import Blueprint, render_template
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import News
from app.utils.recommendations import get_recommendations
from sqlalchemy import text

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
@jwt_required(optional=True)  # ⭐ ADD optional=True (login NOT required but works if logged in)
def home():
    """Home page with optional authentication."""
    latest_news = News.query.order_by(News.published_date.desc()).limit(10).all()
    
    current_user_id = get_jwt_identity()  # None if not logged in, user_id if logged in
    
    if current_user_id:
        # Logged in user gets personalized recommendations
        from app.utils import get_recommendations
        recommendations = get_recommendations(user_id=current_user_id, limit=5)
    else:
        # Guest user gets latest news
        recommendations = News.query.order_by(News.published_date.desc()).limit(5).all()
    
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
        db.session.execute(text('SELECT 1'))
        return {'status': 'ok', 'database': 'connected'}, 200
    except Exception as e:
        return {'status': 'error', 'database': 'disconnected', 'error': str(e)}, 500