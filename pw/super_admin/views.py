# -*- coding: utf-8 -*-
"""Admin section"""
from flask import (Blueprint, render_template, redirect, url_for, flash,
                   send_from_directory, current_app, session, g, request)
import os
import shutil
from mongoengine.connection import DEFAULT_CONNECTION_NAME
from mongoengine.connection import _connection_settings as db_connection_settings
from mongoengine.connection import disconnect
from flask_login import login_user, logout_user, current_user

from pw.extensions import db
from pw.authentication import admin_required
from pw.auth.forms import LoginForm
from pw.super_admin.forms import AddWikiGroupForm
from pw.models import WikiGroup, WikiUser, WikiLoginRecord, WikiPage
from pw.utils import flash_errors, convert_user_ids_to_dict, convert_dict_to_user_ids

blueprint = Blueprint('super_admin', __name__, static_folder='../static')

@blueprint.url_value_preprocessor
def pull_wiki_group_code(endpoint, values):
    g.wiki_group = DEFAULT_CONNECTION_NAME


@blueprint.route('/')
def cover():
    """Cover page."""
    active_wiki_groups = WikiGroup.objects(active=True).all()
    return render_template(
        'super_admin/cover.html',
        active_wiki_groups=active_wiki_groups
    )


@blueprint.route('/super-login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = WikiUser.objects(name=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            user_id_dict = {g.wiki_group: user.id}
            user.id = convert_dict_to_user_ids(user_id_dict)
            login_user(user, form.remember_me.data)
            WikiLoginRecord(
                username=form.username.data,
                browser=request.user_agent.browser, 
                platform=request.user_agent.platform, 
                details=request.user_agent.string, 
                ip=request.remote_addr
            ).save()

            return redirect(url_for('.home'))
        flash('Invalid username or password.', 'danger')
    else:
        flash_errors(form)
    return render_template('auth/login.html', form=form)


@blueprint.route('/super-logout')
@admin_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('.login'))


@blueprint.route('/super-admin', methods=['GET', 'POST'])
@admin_required
def home():
    """Manage wiki groups."""
    all_wiki_groups = WikiGroup.objects.all()
    form = AddWikiGroupForm()

    # Create a new wiki group with its own database and static file directory
    if form.validate_on_submit():
        new_wiki_group_name = form.wiki_group_name.data
        new_db_name = new_wiki_group_name.replace(' ', '')

        # Save the name of the new wiki group in database `_admin`
        # Remove whitespaces in the wiki group name.
        # Then use it to name the database which is about to be initialized.
        new_group = WikiGroup(
            name=new_wiki_group_name,
            db_name=new_db_name,
            active=True
        )

        # Initialize a new database for the just-created group
        # Make sure the new group name is not occupied.
        if new_group.db_name in db.connection.database_names():
            flash('Wiki group already exists', 'danger')
        else:
            try:
                os.mkdir(os.path.join(current_app.config['UPLOAD_PATH'], new_group.db_name))
                new_group.save()
                db.register_connection(
                    alias=new_group.db_name, 
                    name=new_group.db_name,
                    host=current_app.config['MONGODB_SETTINGS']['host'],
                    port=current_app.config['MONGODB_SETTINGS']['port']
                )

                new_user = WikiUser(
                    name=form.username.data,
                    email=form.email.data,
                    is_admin=True
                )
                new_user.set_password(form.password.data)
                new_user.switch_db(new_group.db_name).save()
                WikiPage(title='Home').switch_db(new_group.db_name).save()
                flash('New wiki group added', 'success')
                return redirect(url_for('.home'))
            except FileExistsError:
                flash('Upload directory already exists', 'danger')

    else:
        flash_errors(form)

    return render_template(
        'super_admin/home.html',
        form=form,
        all_wiki_groups=all_wiki_groups
    )


@blueprint.route('/activate/<wiki_group>')
@admin_required
def activate(wiki_group):
    wg = WikiGroup.objects(db_name=wiki_group).first()
    if wg is not None:
        if wg.active:
            wg.active = False
            db_connection_settings.pop(wg.db_name, None)
            disconnect(wg.db_name)
        else:
            wg.active = True
            db.register_connection(
                alias=wg.db_name,
                name=wg.db_name,
                host=current_app.config['MONGODB_SETTINGS']['host'],
                port=current_app.config['MONGODB_SETTINGS']['port'])
        wg.save()
    return redirect(url_for('.home'))


@blueprint.route('/delete-group/<wiki_group>')
@admin_required
def delete_group(wiki_group):
    wg = WikiGroup.objects(db_name=wiki_group).first()
    if wg is not None:
        if wg.active:
            db_connection_settings.pop(wg.db_name, None)
            disconnect(wg.db_name)
        db.connection.drop_database(wg.db_name)
        wg.delete()

        shutil.rmtree(os.path.join(current_app.config['UPLOAD_PATH'], wiki_group))

    return redirect(url_for('.home'))


# TODO: maybe move these routes to another blueprint
@blueprint.route('/favicon.ico')
def favicon():
    return send_from_directory(
        os.path.join(blueprint.static_folder, 'images'),
        'favicon.ico',
        mimetype='image/vnd.microsoft.icon'
    )
