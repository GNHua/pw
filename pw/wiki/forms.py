# -*- coding: utf-8 -*-
"""Wiki forms."""
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, IntegerField, FileField, StringField
from wtforms.validators import DataRequired


class WikiEditForm(FlaskForm):
    textArea = TextAreaField('Edit')
    submit = SubmitField('Save Changes')
    current_version = IntegerField('Current version')


class CommentForm(FlaskForm):
    textArea = TextAreaField('Edit', 
        validators=[DataRequired()]
        )
    submit = SubmitField('Submit')


class UploadForm(FlaskForm):
    file = FileField('File')
    upload = SubmitField('Upload')


class RenameForm(FlaskForm):
    new_title = StringField(
        'New page title',
        validators=[
            DataRequired('Enter a new title.')
        ]
    )
    submit = SubmitField('Rename')


class SearchForm(FlaskForm):
    search = StringField('Search')
    start_date = StringField()
    end_date = StringField()
    submit = SubmitField('Search')


class HistoryRecoverForm(FlaskForm):
    version = IntegerField(
        'Recover history',
        validators=[DataRequired('Please enter a version number.')]
    )
    submit = SubmitField('Submit')
