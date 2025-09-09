"""
Main routes (public pages)
"""

from flask import Blueprint, render_template
from app.config import Config

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page with registration form"""
    return render_template('index.html', bbq_details=Config.BBQ_DETAILS)

@main_bp.route('/success')
def success_page():
    """Success page after registration"""
    return render_template('success.html')


