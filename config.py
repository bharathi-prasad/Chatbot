import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    DATABASE_URL = os.environ.get('DATABASE_URL') or 'postgresql://postgres:Lms@123$@183.82.119.245:5432/postgres'
    
    # Database configuration - Updated with new database details
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', '183.82.119.245'),
        'database': os.environ.get('DB_NAME', 'postgres'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'Lms@123$'),
        'port': int(os.environ.get('DB_PORT', 5432))
    }
    
    # Schema configuration
    DB_SCHEMA = os.environ.get('DB_SCHEMA', 'loancraft')
    
    # Flask configuration
    DEBUG = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    FLASK_ENV = os.environ.get('FLASK_ENV', 'development')
    
    # CORS configuration
    CORS_ORIGINS = os.environ.get('CORS_ORIGINS', 'http://localhost:3000').split(',')
    
    # API configuration
    API_VERSION = 'v1'
    API_PREFIX = f'/api/{API_VERSION}'
    
    # Chatbot configuration
    MAX_MESSAGE_LENGTH = 1000
    SESSION_TIMEOUT = 3600  # 1 hour in seconds
    INTENT_CONFIDENCE_THRESHOLD = 0.3
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'chatbot.log')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Development database configuration
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', '183.82.119.245'),
        'database': os.environ.get('DB_NAME', 'postgres'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'Lms@123$'),
        'port': int(os.environ.get('DB_PORT', 5432))
    }

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    TESTING = False
    
    # Production database configuration
    DB_CONFIG = {
        'host': os.environ.get('DB_HOST', '183.82.119.245'),
        'database': os.environ.get('DB_NAME', 'postgres'),
        'user': os.environ.get('DB_USER', 'postgres'),
        'password': os.environ.get('DB_PASSWORD', 'Lms@123$'),
        'port': int(os.environ.get('DB_PORT', 5432)),
        'sslmode': os.environ.get('DB_SSLMODE', 'prefer')
    }

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    
    # Test database configuration - using same database but different schema/approach
    DB_CONFIG = {
        'host': '183.82.119.245',
        'database': 'postgres',
        'user': 'postgres',
        'password': 'Lms@123$',
        'port': 5432
    }

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}