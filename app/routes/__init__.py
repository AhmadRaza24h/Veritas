"""
Route blueprints initialization.
"""
from app.routes.main import main_bp
from app.routes.news import news_bp
from app.routes.analysis import analysis_bp
from app.routes.api import api_bp

__all__ = [
    'main_bp',
    'news_bp',
    'analysis_bp',
    'api_bp'
]
