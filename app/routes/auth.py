"""
Authentication routes for login, register, logout.
"""
from flask import Blueprint, request, jsonify, render_template, redirect, url_for, make_response
from flask_jwt_extended import (
    create_access_token, create_refresh_token,
    jwt_required, get_jwt_identity, set_access_cookies, unset_jwt_cookies
)
from datetime import datetime
from app.extensions import db
from app.models import User

auth_bp = Blueprint('auth', __name__)


# ============================================
# HTML Routes (Pages)
# ============================================

@auth_bp.route('/login')
def login_page():
    """Show login page."""
    return render_template('auth/login.html')


@auth_bp.route('/register')
def register_page():
    """Show registration page."""
    return render_template('auth/register.html')


@auth_bp.route('/profile')
@jwt_required(optional=True)
def profile():
    """User profile page."""
    current_user_id = get_jwt_identity()
    
    if not current_user_id:
        return redirect(url_for('auth.login_page'))
    
    user = User.query.get(current_user_id)
    if not user:
        return redirect(url_for('auth.login_page'))
    
    # Get user's history
    history = user.history.order_by(db.desc('viewed_at')).limit(20).all()
    
    return render_template('user/profile.html', user=user, history=history)


# ============================================
# API Routes (JSON)
# ============================================

@auth_bp.route('/api/register', methods=['POST'])
def register():
    """Register new user."""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Username, email, and password are required'}), 400
    
    if len(data['password']) < 6:
        return jsonify({'error': 'Password must be at least 6 characters'}), 400
    
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'Username already exists'}), 400
    
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 400
    
    user = User(
        username=data['username'],
        email=data['email']
    )
    user.set_password(data['password'])
    
    db.session.add(user)
    db.session.commit()
    
    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)
    
    return jsonify({
        'message': 'User registered successfully',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    }), 201


@auth_bp.route('/api/login', methods=['POST'])
def login():
    """Login user."""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username and password are required'}), 400
    
    user = User.query.filter_by(username=data['username']).first()
    
    if not user or not user.check_password(data['password']):
        return jsonify({'error': 'Invalid username or password'}), 401
    
    access_token = create_access_token(identity=user.user_id)
    refresh_token = create_refresh_token(identity=user.user_id)
    
    response = jsonify({
        'message': 'Login successful',
        'user': user.to_dict(),
        'access_token': access_token,
        'refresh_token': refresh_token
    })
    
    set_access_cookies(response, access_token)
    
    return response, 200


@auth_bp.route('/api/logout', methods=['POST'])
@jwt_required()
def logout():
    """Logout user."""
    response = jsonify({'message': 'Logout successful'})
    unset_jwt_cookies(response)
    return response, 200


@auth_bp.route('/api/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """Refresh access token."""
    current_user_id = get_jwt_identity()
    new_access_token = create_access_token(identity=current_user_id)
    
    return jsonify({'access_token': new_access_token}), 200


@auth_bp.route('/api/me', methods=['GET'])
@jwt_required()
def get_current_user():
    """Get current logged-in user."""
    current_user_id = get_jwt_identity()
    user = User.query.get(current_user_id)
    
    if not user:
        return jsonify({'error': 'User not found'}), 404
    
    return jsonify({'user': user.to_dict()}), 200


@auth_bp.route('/api/check-auth', methods=['GET'])
@jwt_required(optional=True)
def check_auth():
    """Check if user is authenticated."""
    current_user_id = get_jwt_identity()
    
    if current_user_id:
        user = User.query.get(current_user_id)
        return jsonify({
            'authenticated': True,
            'user': user.to_dict() if user else None
        }), 200
    else:
        return jsonify({
            'authenticated': False,
            'user': None
        }), 200