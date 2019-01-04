# -*- coding: utf-8 -*-
from flask import g
from datetime import datetime
from mongoengine.connection import DEFAULT_CONNECTION_NAME
from mongoengine.context_managers import switch_db
from flask_login import current_user, UserMixin

from pw.extensions import db, bcrypt, login_manager
from pw.utils import convert_user_ids_to_dict


@login_manager.user_loader
def load_user(user_id):
    user_id_dict = convert_user_ids_to_dict(user_id)
    current_user_id = user_id_dict.get(DEFAULT_CONNECTION_NAME)
    if current_user_id is not None:
        with switch_db(WikiUser, DEFAULT_CONNECTION_NAME) as WU:
            return WU.objects(id=current_user_id).first()

    current_user_id = user_id_dict.get(g.wiki_group)
    if current_user_id is not None:
        return WikiUser.objects(id=current_user_id).first()
    return


class WikiGroup(db.Document):
    name = db.StringField(unique=True)
    db_name = db.StringField(unique=True)
    active = db.BooleanField()

    meta = {'collection': 'wiki_group'}


class WikiPageVersion(db.Document):
    diff = db.StringField()
    version = db.IntField()
    modified_on = db.DateTimeField()
    modified_by = db.StringField()

    meta = {
        'collection': 'wiki_page_version',
        'indexes': [{
            'fields': ['$diff'],
            'default_language': 'english'
        }]
    }


class WikiComment(db.EmbeddedDocument):
    # id = <epoch time>-<author id>
    # id = db.StringField(required=True)
    timestamp = db.DateTimeField(default=datetime.now)
    author = db.StringField()
    md = db.StringField()
    html = db.StringField()


class WikiPage(db.Document):
    title = db.StringField(required=True, unique=True)
    md = db.StringField(default='')
    html = db.StringField()
    toc = db.StringField()
    modified_on = db.DateTimeField(default=datetime.now)
    modified_by = db.StringField(default='system')
    comments = db.ListField(db.EmbeddedDocumentField(WikiComment))
    current_version = db.IntField(default=1)
    versions = db.ListField(db.ReferenceField(WikiPageVersion))
    refs = db.ListField(db.ReferenceField('self'))
    keypage = db.IntField()

    meta = {
        'collection': 'wiki_page',
        'indexes': [
            '#title', {
                'fields': ['$title', '$md', '$comments.md'],
                'default_language': 'english',
                'weights': {'title': 10, 'md': 2, 'comments.md': 1}
            }
        ]
    }

    def update_db(self, diff, md, html, toc=None, update_refs=True):
        wiki_page_version = WikiPageVersion(
            diff=diff,
            version=self.current_version,
            modified_on=self.modified_on,
            modified_by=self.modified_by
        ).save()

        updates = {
            'set__md': md,
            'set__html': html,
            'inc__current_version': 1,
            'set__modified_on': datetime.now(),
            'set__modified_by': current_user.name,
            'push__versions': wiki_page_version
        }
        if update_refss:
            updates['set__toc'] = toc
            updates['set__refs'] = self.refs

        self.__class__.objects(id=wiki_page.id).update_one(**updates)


class WikiFile(db.Document):
    id = db.SequenceField(primary_key=True)
    name = db.StringField(max_length=256, required=True)
    mime_type = db.StringField()
    size = db.IntField()  # in bytes
    uploaded_on = db.DateTimeField(default=datetime.now)
    uploaded_by = db.StringField()

    meta = {'collection': 'wiki_file'}


class WikiUser(db.Document, UserMixin):
    name = db.StringField(unique=True)
    email = db.StringField(required=True)
    password_hash = db.StringField()
    is_admin = db.BooleanField()

    meta = {'collection': 'wiki_user'}

    def __repr__(self):
        return '<User {}>'.format(self.name)

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password, 12)

    def verify_password(self, password):
        return bcrypt.check_password_hash(self.password_hash, password)


class WikiLoginRecord(db.Document):
    username = db.StringField()
    timestamp = db.DateTimeField(default=datetime.now)
    browser = db.StringField()
    platform = db.StringField()
    details = db.StringField()
    ip = db.StringField()

    meta = {
        'collection': 'wiki_login_record',
        'ordering': ['-timestamp']
    }
