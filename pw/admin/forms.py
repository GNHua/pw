# -*- coding: utf-8 -*-
"""Admin forms."""
from flask_wtf import FlaskForm
from wtforms import TextAreaField, SubmitField, StringField, PasswordField, BooleanField
from wtforms.validators import DataRequired, Regexp, Email


class KeyPageEditForm(FlaskForm):
    textArea = TextAreaField('Edit')
    submit = SubmitField('Save Changes')


class NewUserForm(FlaskForm):
    username = StringField(
        'Username',
        validators=[
            DataRequired('Please enter a username.'),
            Regexp('^[\w ]+$', message='Username must contain only letters, '
                                       'numbers, underscore, or whitespace.')
        ]
    )
    email = StringField(
        'Email', 
        validators=[
            DataRequired('Please enter an email address.'), 
            Email()
        ]
    )
    password = PasswordField(
        'Password',
        validators=[DataRequired('Please enter a password.')]
    )
    is_admin = BooleanField('Admin')
    submit = SubmitField('Submit')


class ManageUserForm(NewUserForm):
    password = PasswordField('Password')
    remove = SubmitField('Remove')