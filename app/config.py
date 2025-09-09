"""
Configuration settings for the BBQ app
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    
    # Flask Configuration
    SECRET_KEY = os.getenv('SECRET_KEY')
    SESSION_LIFETIME = int(os.getenv('SESSION_LIFETIME', 1800))
    
    # Database Configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'bbq.db')
    
    # Email Configuration
    SMTP_SERVER = os.getenv('SMTP_SERVER')
    SMTP_PORT = int(os.getenv('SMTP_PORT', 587))
    SMTP_USERNAME = os.getenv('SMTP_USERNAME')
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD')
    ORGANIZER_EMAIL = os.getenv('ORGANIZER_EMAIL')
    
    # Admin Configuration
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')
    
    # BBQ Event Configuration
    BBQ_DETAILS = {
        "price_per_adult": float(os.getenv('BBQ_PRICE_PER_ADULT', 28.50)),
        "date": os.getenv('BBQ_DATE', "zaterdag 6 september"),
        "location": os.getenv('BBQ_LOCATION', "familie Smit aan de Kamperweg 46"),
        "deadline": os.getenv('BBQ_DEADLINE', "22 augustus"),
        "contact_kay_phone": os.getenv('BBQ_CONTACT_PHONE', "06-83699549")
    }
    
    # Bunq.me Configuration
    BUNQ_ME_BASE_URL = os.getenv('BUNQ_ME_BASE_URL', "https://bunq.me/kamperwegBBQ")

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    FLASK_ENV = 'production'

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}


