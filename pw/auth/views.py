# -*- coding: utf-8 -*-
"""Auth section"""
from flask import Blueprint, redirect, url_for, g, session, request, render_template
from flask_login import current_user, login_user, logout_user
from werkzeug.urls import url_parse

from pw.blueprints import setup_blueprint
from pw.authentication import login_required
from pw.auth.forms import LoginForm, ChangePwdForm
from pw.models import WikiUser
from pw.utils import flash_errors, convert_user_ids_to_dict, convert_dict_to_user_ids
from pw.extensions import login_manager

blueprint = Blueprint('auth', __name__, static_folder='../static', url_prefix='/<wiki_group>')
setup_blueprint(blueprint)


@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('wiki.home'))

    form = LoginForm()
    if form.validate_on_submit():
        user = WikiUser.objects(name=form.username.data).first()
        if user is not None and user.verify_password(form.password.data):
            user_id_dict = convert_user_ids_to_dict(session.get['user_id'])
            user_id_dict[g.wiki_group] = user.id
            user.id = convert_dict_to_user_ids(user_id_dict)
            login_user(user, form.remember_me.data)
            WikiLoginRecord(
                username=form.username.data,
                browser=request.user_agent.browser, 
                platform=request.user_agent.platform, 
                details=request.user_agent.string, 
                ip=request.remote_addr
            ).save()

            # details on `url_parse` and `netloc`:
            # https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-v-user-logins
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('wiki.home')
            return redirect(next_page)
        flash('Invalid username or password.', 'warning')
    else:
        flash_errors(form)
    return render_template('auth/login.html', form=form)


@blueprint.route('/logout')
@login_required
def logout():
    user_id_dict = convert_user_ids_to_dict(session['user_id'])
    if len(user_id_dict) == 1:
        logout_user()
    else:
        user_id_dict.pop(g.wiki_group)
        session['user_id'] = convert_dict_to_user_ids(user_id_dict)
        # TODO: test whether the next line is needed
        login_manager._update_request_context_with_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('.login'))


@blueprint.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password(username):
    form = ChangePwdForm()
    if form.validate_on_submit():
        if not current_user.verify_password(form.old_password.data):
            flash('Password Verification Failed.')
        elif form.new_password.data != form.confirm_password.data:
            flash('Please confirm new password again.')
        else:
            current_user.set_password(form.new_password.data)
            (WikiUser
             .objects(name=current_user.name)
             .update_one(set__password_hash=current_user.password_hash))
            flash('Password changed.')
    else:
        flash_errors(form)

    return render_template(
        'auth/change_password.html',
        form=form
    )
