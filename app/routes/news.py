"""
News routes with optional authentication.
"""
from flask import Blueprint, render_template, request, abort
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import News, UserHistory
from app.extensions import db

news_bp = Blueprint('news', __name__)


@news_bp.route('/')
def news_list():
    """News listing page (no login required)."""
    page = request.args.get('page', 1, type=int)
    category = request.args.get('category')
    location = request.args.get('location')
    
    query = News.query
    
    if category:
        query = query.filter_by(incident_type=category)
    if location:
        query = query.filter(News.location.ilike(f'%{location}%'))
    
    pagination = query.order_by(News.published_date.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('news/list.html', news=pagination.items, pagination=pagination)


@news_bp.route('/<int:news_id>')
@jwt_required(optional=True)
def news_detail(news_id):
    """Single news detail page. Saves to history if logged in."""
    news = News.query.get_or_404(news_id)
    
    current_user_id = get_jwt_identity()
    
    if current_user_id:
        history = UserHistory(user_id=current_user_id, news_id=news_id)
        db.session.add(history)
        db.session.commit()
    
    return render_template('news/detail.html', news=news)