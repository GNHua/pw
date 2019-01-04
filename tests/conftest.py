# -*- coding: utf-8 -*-
"""Defines fixtures available to all tests."""

import pytest
from webtest import TestApp
from mongoengine.connection import get_db

from pw.app import create_app
from pw.extensions import db as _db
from pw.models import *


@pytest.fixture
def app():
    """An application for the tests."""
    _app = create_app('tests.settings')
    ctx = _app.test_request_context()
    ctx.push()

    yield _app

    ctx.pop()


@pytest.fixture
def testapp(app):
    """A Webtest app."""
    return TestApp(app)


@pytest.fixture
def db():
    """A test database for the tests."""

    yield _db

    __db = get_db()
    for collection in __db.collection_names():
        if 'system.' in collection:
            continue
        __db.drop_collection(collection)


@pytest.fixture
def wiki_group(db):
    """A wiki group for the tests."""
    _wiki_group = WikiGroupFactory.create()
    return _wiki_group
