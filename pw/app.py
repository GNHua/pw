# -*- coding: utf-8 -*-
"""The app module, containing the app factory function."""
from flask import Flask, render_template
from werkzeug.contrib.fixers import ProxyFix
from datetime import timedelta

from pw import commands, wiki, super_admin, admin, auth
from pw.extensions import csrf_protect, bcrypt, db, login_manager
from pw.models import WikiGroup, WikiPage


def create_app(config_object='pw.settings'):
    """An application factory, as explained here: http://flask.pocoo.org/docs/patterns/appfactories/.

    :param config_object: The configuration object to use.
    """
    app = Flask(__name__.split('.')[0])
    app.config.from_object(config_object)
    # TODO: check if this can be put in settings.py
    app.permanent_session_lifetime = timedelta(days=1)
    app.wsgi_app = ProxyFix(app.wsgi_app)
    register_extensions(app)
    register_blueprints(app)
    register_errorhandlers(app)
    register_shellcontext(app)
    register_commands(app)
    register_database(app)
    return app


def register_extensions(app):
    """Register Flask extensions."""
    csrf_protect.init_app(app)
    bcrypt.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    return None


def register_blueprints(app):
    """Register Flask blueprints."""
    app.register_blueprint(super_admin.views.blueprint)
    app.register_blueprint(admin.views.blueprint)
    app.register_blueprint(auth.views.blueprint)
    app.register_blueprint(wiki.views.blueprint)
    return None


def register_errorhandlers(app):
    """Register error handlers."""
    def render_error(error):
        """Render error template."""
        # If a HTTPException, pull the `code` attribute; default to 500
        error_code = getattr(error, 'code', 500)
        return render_template('{0}.html'.format(error_code)), error_code
    for errcode in [401, 404, 500]:
        app.errorhandler(errcode)(render_error)
    return None


def register_shellcontext(app):
    """Register shell context objects."""
    def shell_context():
        """Shell context objects."""
        return {
            'db': db,
            'WikiPage': WikiPage}

    app.shell_context_processor(shell_context)


def register_commands(app):
    """Register Click commands."""
    app.cli.add_command(commands.test)
    app.cli.add_command(commands.lint)
    app.cli.add_command(commands.clean)
    app.cli.add_command(commands.urls)


def register_database(app):
    for wiki_group in WikiGroup.objects(active=True).all():
        db.register_connection(
            alias=wiki_group.db_name, 
            name=wiki_group.db_name,
            host=app.config['MONGODB_SETTINGS']['host'],
            port=app.config['MONGODB_SETTINGS']['port']
        )