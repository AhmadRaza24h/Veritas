"""
Flask Application Factory with Scheduler.
"""
from flask import Flask
from app.config import config
from app.extensions import db, migrate, jwt, bcrypt


def create_app(config_name='development'):
    """Create and configure Flask app."""
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    bcrypt.init_app(app)
    
    # Initialize scheduler
    from app.services.scheduler_service import scheduler_service
    scheduler_service.init_app(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # JWT callbacks
    register_jwt_callbacks(app)
    
    return app


def register_blueprints(app):
    """Register Flask blueprints."""
    from app.routes.main import main_bp
    from app.routes.news import news_bp
    from app.routes.analysis import analysis_bp
    from app.routes.api import api_bp
    from app.routes.auth import auth_bp
    from app.routes.static_pages import static_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(news_bp, url_prefix='/news')
    app.register_blueprint(analysis_bp, url_prefix='/analysis') 
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(static_bp)


def register_error_handlers(app):
    """Register error handlers."""
    from flask import render_template, jsonify, request
    
    @app.errorhandler(404)
    def not_found(error):
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Not found'}), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        if request.path.startswith('/api/'):
            return jsonify({'error': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500


def register_jwt_callbacks(app):
    """Register JWT callbacks."""
    from flask import jsonify
    
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            'error': 'Token has expired',
            'message': 'Please login again'
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            'error': 'Invalid token',
            'message': 'Please login again'
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            'error': 'No token provided',
            'message': 'Login required for this action'
        }), 401