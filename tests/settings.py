"""Settings module for test app."""
import os


ENV = 'development'
TESTING = True
SECRET_KEY = 'not-so-secret-in-tests'
DEBUG_TB_ENABLED = False
CACHE_TYPE = 'simple'  # Can be "memcached", "redis", etc.
WTF_CSRF_ENABLED = False  # Allows form testing
MONGODB_SETTINGS = {
    'db': 'mongoenginetest',
    'host': 'mongomock://localhost'
}
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), 'data'))
DB_PATH = os.path.join(DATA_PATH, 'db')
UPLOAD_PATH = os.path.join(DATA_PATH, 'upload')

ADMIN_USERNAME = 'ADMIN_USERNAME'
ADMIN_EMAIL = 'ADMIN_EMAIL'
ADMIN_PASSWORD = 'ADMIN_PASSWORD'