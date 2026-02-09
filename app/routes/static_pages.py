# app/routes/static_pages.py
from flask import Blueprint, render_template

static_bp = Blueprint('static_pages', __name__, template_folder='templates')

@static_bp.route('/about')
def about():
    return render_template('static_pages/about.html')

@static_bp.route('/methodology')
def methodology():
    return render_template('static_pages/methodology.html')

@static_bp.route('/privacy')
def privacy():
    return render_template('static_pages/privacy.html')

@static_bp.route('/terms')
def terms():
    return render_template('static_pages/terms.html')
