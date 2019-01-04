# -*- coding: utf-8 -*-
from flask import g, request, abort
import sys
import inspect
from mongoengine.connection import DEFAULT_CONNECTION_NAME
from datetime import date

from pw.extensions import db
from pw.wiki.forms import SearchForm
from pw.models import WikiPage


def setup_blueprint(blueprint):

    @blueprint.url_defaults
    def add_wiki_group_code(endpoint, values):
        if 'wiki_group' in values:
            return
        values.setdefault('wiki_group', g.wiki_group)

    @blueprint.url_value_preprocessor
    def pull_wiki_group_code(endpoint, values):
        g.wiki_group = values.pop('wiki_group')
        if g.wiki_group not in db.connection.database_names():
            abort(404)

    @blueprint.before_request
    def open_database_connection():
        for name, obj in inspect.getmembers(sys.modules['pw.models']):
            if inspect.isclass(obj) and inspect.getmro(obj)[1] == db.Document:
                if not obj._meta.get('db_alias'):
                    obj._get_collection()
                obj._meta['db_alias'] = g.wiki_group
                obj._collection = None

    @blueprint.after_request
    def close_database_connection(response):
        for name, obj in inspect.getmembers(sys.modules['pw.models']):
            if inspect.isclass(obj) and inspect.getmro(obj)[1] == db.Document:
                obj._meta['db_alias'] = DEFAULT_CONNECTION_NAME
                obj._collection = None
        return response

    # Docs: http://flask.pocoo.org/docs/1.0/templating/#context-processors
    @blueprint.context_processor
    def inject_wiki_group_data():
        if g.wiki_group not in db.connection.database_names():
            return dict()

        if request.endpoint in [
            'wiki.edit', 'wiki.upload', 'wiki.handle_upload', 'wiki.file'
            'auth.login', 'auth.logout',
        ]:
            return dict(wiki_group=g.wiki_group)

        search_form = SearchForm()

        wiki_keypages = (WikiPage
                         .objects(keypage__exists=True)
                         .only('title')
                         .all())

        # TODO: enhancement - this might be a performance bottleneck in the future.
        wiki_changes = (WikiPage
                        .objects
                        .only('title', 'modified_on')
                        .order_by('-modified_on')[:5])

        latest_change_time = wiki_changes[0].modified_on
        if latest_change_time.date() == date.today():
            latest_change_time = latest_change_time.strftime('[%H:%M]')
        else:
            latest_change_time = latest_change_time.strftime('[%b %d]')

        return dict(
            wiki_group=g.wiki_group,
            search_form=search_form,
            wiki_keypages=wiki_keypages,
            wiki_changes=wiki_changes,
            latest_change_time=latest_change_time
        )
