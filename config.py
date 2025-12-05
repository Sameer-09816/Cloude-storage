# Production Configuration
import os
from datetime import timedelta

class Config:
    """Base configuration"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    
    # Session configuration
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # Set to True if using HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # File upload settings
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024 * 1024  # 5GB max file size
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or 'uploads'
    DOWNLOAD_FOLDER = os.environ.get('DOWNLOAD_FOLDER') or 'downloads'
    THUMBNAIL_FOLDER = 'static/thumbnails'
    
    # Login credentials (in production, use environment variables)
    VALID_EMAIL = os.environ.get('ADMIN_EMAIL') or 'Sameerkom16@gmail.com'
    VALID_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'Sameerkom16@123'
    
    # Server settings
    HOST = os.environ.get('HOST') or '0.0.0.0'
    PORT = int(os.environ.get('PORT') or 5000)
    DEBUG = os.environ.get('FLASK_ENV') == 'development'
    
    # Download optimization
    CHUNK_SIZE = 8 * 1024 * 1024  # 8MB chunks
    MAX_RETRIES = 5
    TIMEOUT = 60

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    
class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SESSION_COOKIE_SECURE = True  # Require HTTPS
    
# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
