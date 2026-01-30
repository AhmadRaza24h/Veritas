"""
News blueprint for news listing and detail pages.
"""
from flask import Blueprint, render_template, request, abort
from app.services import NewsService
from app.models import UserHistory
from app.extensions import db

news_bp = Blueprint('news', __name__)


@news_bp.route('/')
def news_list():
    """News listing page with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    
    # Get filters
    query = request.args.get('q')
    location = request.args.get('location')
    incident_type = request.args.get('type')
    
    # Get paginated news
    if query or location or incident_type:
        pagination = NewsService.search_news(
            query=query,
            location=location,
            incident_type=incident_type,
            page=page,
            per_page=per_page
        )
    else:
        pagination = NewsService.get_news_paginated(page=page, per_page=per_page)
    
    return render_template(
        'news/list.html',
        pagination=pagination,
        query=query,
        location=location,
        incident_type=incident_type
    )


@news_bp.route('/<int:news_id>')
def news_detail(news_id):
    """News detail page."""
    news = NewsService.get_news_by_id(news_id)
    
    if not news:
        abort(404)
    
    # Track user view (using user_id=1 as default for demo)
    # In production, this would use the logged-in user's ID
    history = UserHistory(user_id=1, news_id=news_id)
    db.session.add(history)
    db.session.commit()
    
    # Get associated incident
    incident = NewsService.get_incident_for_news(news_id)
    
    return render_template(
        'news/detail.html',
        news=news,
        incident=incident
    )
