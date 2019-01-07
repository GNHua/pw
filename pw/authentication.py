# -*- coding: utf-8 -*-
from flask import redirect, url_for, request, g
from functools import wraps
from mongoengine.connection import DEFAULT_CONNECTION_NAME
from flask_login import current_user


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.blueprint == 'super_admin':
            redirect_blueprint = request.blueprint
        else:
            redirect_blueprint = 'auth'
        if not current_user.is_authenticated:
            return redirect(url_for('{0}.login'.format(redirect_blueprint), next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    @wraps(f)
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin:
            abort(401)
        return f(*args, **kwargs)

    return decorated_function
