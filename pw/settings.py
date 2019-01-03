# -*- coding: utf-8 -*-
"""Application configuration.

Most configuration is set via environment variables.

For local development, use a .env file to set
environment variables.
"""
from environs import Env
import os
from datetime import timezone, timedelta

env = Env()
env.read_env()

ENV = env.str('FLASK_ENV', default='production')
DEBUG = ENV == 'development'
SECRET_KEY = env.str('SECRET_KEY')
WTF_CSRF_ENABLED = True
MONGODB_SETTINGS = {
    'db': env.str('DB_NAME', default='admin'),
    'host': env.str('DB_SERVICE', default='127.0.0.1'),
    'port': env.int('DB_PORT', default=27017),
    'username': env.str('DB_USER'),
    'password': env.str('DB_PASS')
}
DEBUG_TB_ENABLED = DEBUG
DEBUG_TB_INTERCEPT_REDIRECTS = False
WTF_CSRF_TIME_LIMIT = 100000000 # TODO: change
DATA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir, 'data'))
DB_PATH = os.path.join(DATA_PATH, 'db')
UPLOAD_PATH = os.path.join(DATA_PATH, 'upload')

# Email to send out notification to users
# Here Gmail is used as an example. 
# If you want to stay with Gmail, 
# you need to `Allow less secure apps to access accounts`.
# More info: https://support.google.com/a/answer/6260879?hl=en
# and https://github.com/miguelgrinberg/flasky/issues/65
MAIL_SERVER = 'smtp.googlemail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
MAIL_SENDER = 'Project Wiki <{}>'.format(os.environ.get('MAIL_USERNAME'))
MAIL_SUBJECT_PREFIX = '[Do-not-reply]'

# Super admin username, email, and password
# The email can be the same as the one above.
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME')
ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL')
ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD')
