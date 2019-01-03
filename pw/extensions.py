# -*- coding: utf-8 -*-
"""Extensions module. Each extension is initialized in the app factory located in app.py."""
from flask_wtf.csrf import CSRFProtect
from flask_bcrypt import Bcrypt
from flask_mongoengine import MongoEngine
from flask_login import LoginManager, set_login_view

from pw import auth, wiki


csrf_protect = CSRFProtect()
bcrypt = Bcrypt()
db = MongoEngine()
login_manager = LoginManager()
set_login_view('auth.login', auth.views.blueprint)
set_login_view('auth.login', wiki.views.blueprint)


from pw.markdown import WikiMarkdown

markdown = WikiMarkdown()
