# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_mongoengine import MongoEngine
from flask_login import LoginManager
from flask_mail import Mail


csrf_protect = CSRFProtect()
bcrypt = Bcrypt()
db = MongoEngine()
login_manager = LoginManager()
mail = Mail()


from pw.markdown import WikiMarkdown

markdown = WikiMarkdown()
