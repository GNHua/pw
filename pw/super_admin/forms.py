# -*- coding: utf-8 -*-
"""Super admin forms."""
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Regexp, Email


class AddWikiGroupForm(FlaskForm):
    wiki_group_name = StringField(
        'Wiki Group Name',
        validators=[
            DataRequired('Please enter a group name.'),
            Regexp('^[\w+ ]+$', message='Group name must contain only letters, '
                                        'numbers, underscore, and whitespace.')
        ]
    )
    username = StringField(
        'Username',
        validators=[
            DataRequired('Please enter a username.'),
            Regexp('^[\w+ ]+$', message='Username must contain only letters, '
                                        'numbers, and underscore.')
        ]
    )
    email = StringField(
        'Email address', 
        validators=[
            DataRequired('Please enter an email address.'), 
            Email()
        ]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired('Please enter a password.')]
    )
    submit = SubmitField('Submit')