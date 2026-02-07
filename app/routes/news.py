"""
News routes.
"""
from flask import Blueprint, render_template, request, jsonify
from app.models import News
from app.extensions import db
from flask_jwt_extended import jwt_required, get_jwt_identity
from app.models import News, UserHistory,Incident
from datetime import datetime

news_bp = Blueprint('news', __name__)


@news_bp.route('/')
def news_list():
    """Display paginated list of news articles."""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Get paginated news
    pagination = News.query.order_by(News.published_date.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    # Calculate total
    total = News.query.count()
    
    return render_template(
        'news/list.html',
        news_list=pagination.items,  # Changed from 'news' to 'news_list'
        pagination=pagination,
        page=page,
        per_page=per_page,
        total=total
    )


@news_bp.route('/<int:news_id>')
@jwt_required(optional=True)
def news_detail(news_id):
    """Display individual news article."""
    news = News.query.get_or_404(news_id)
    incident = Incident.query.filter_by(
    incident_type=news.incident_type,
    location=news.location).first()
    
    # Track user history if logged in
    current_user_id = get_jwt_identity()
    if current_user_id:
        # Check if already viewed
        existing = UserHistory.query.filter_by(
            user_id=current_user_id,
            news_id=news_id
        ).first()
        
        if not existing:
            history = UserHistory(
                user_id=current_user_id,
                news_id=news_id,
                viewed_at=datetime.utcnow()
            )
            db.session.add(history)
            db.session.commit()
    
    return render_template('news/detail.html', news=news, incident=incident )


@news_bp.route('/search')
def search_news():
    """Search news articles."""
    query = request.args.get('q', '')
    category = request.args.get('category', '')
    location = request.args.get('location', '')
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    # Build query
    news_query = News.query
    
    if query:
        news_query = news_query.filter(
            db.or_(
                News.title.ilike(f'%{query}%'),
                News.summary.ilike(f'%{query}%'),
                News.content.ilike(f'%{query}%')
            )
        )
    
    if category:
        news_query = news_query.filter(News.incident_type == category)
    
    if location:
        news_query = news_query.filter(News.location.ilike(f'%{location}%'))
    
    # Paginate
    pagination = news_query.order_by(News.published_date.desc()).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    
    total = news_query.count()
    
    return render_template(
        'news/list.html',
        news_list=pagination.items,
        pagination=pagination,
        page=page,
        per_page=per_page,
        total=total,
        search_query=query,
        search_category=category,
        search_location=location
    )