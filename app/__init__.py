"""
BBQ Registration App
A Flask application for managing neighborhood BBQ event registrations.
"""

import os
import secrets
import logging
from flask import Flask
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    """Application factory pattern"""
    app = Flask(__name__, static_folder='../static', template_folder='../templates')
    
    # Initialize CSRF protection
    csrf = CSRFProtect(app)
    
    # Generate a secure secret key if not provided
    secret_key = os.getenv('SECRET_KEY')
    if not secret_key or secret_key == 'your_very_secure_secret_key_here_change_this_in_production':
        secret_key = secrets.token_hex(32)
        print("WARNING: Using generated secret key. Set SECRET_KEY in .env for production!")
    
    app.config['SECRET_KEY'] = secret_key
    app.config['PERMANENT_SESSION_LIFETIME'] = int(os.getenv('SESSION_LIFETIME', 1800))
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('../bbq_app.log'),
            logging.StreamHandler()
        ]
    )
    
    # Register blueprints
    from app.routes.main import main_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api')
    
    # Initialize database
    from app.models.database import init_db
    with app.app_context():
        init_db()
    
    return app
