# -*- coding: utf-8 -*-
"""Admin section"""
from flask import Blueprint, render_template, request

from pw.decorators import decorate_blueprint, admin_required
from pw.models import WikiPage, WikiFile, WikiUser, WikiLoginRecord
from pw.utils import flash_errors, paginate
from pw.admin.forms import KeyPageEditForm, NewUserForm, ManageUserForm

blueprint = Blueprint('admin', __name__, static_folder='../static', url_prefix='/<wiki_group>')
decorate_blueprint(blueprint)


@blueprint.route('/keypage-edit', methods=['GET', 'POST'])
@admin_required
def keypage_edit():
    wiki_keypages = (WikiPage
                     .objects(keypage__exists=True)
                     .only('title')
                     .order_by('+keypage'))
    keypage_titles = [
        wiki_keypage.title for wiki_keypage in wiki_keypages
    ]
    form = KeyPageEditForm(textArea='\n'.join(keypage_titles))

    if form.validate_on_submit():
        (WikiPage
         .objects(keypage__exists=True)
         .update(unset__keypage=0))

        new_titles = form.textArea.data.splitlines()
        for i, new_title in enumerate(new_titles):
            (WikiPage
             .objects(title=new_title)
             .update_one(set__keypage=i+1))

        return redirect(url_for('.home'))
    else:
        flash_errors(form)

    return render_template(
        'admin/keypage_edit.html',
        form=form
    )


@blueprint.route('/admin')
@admin_required
def group_admin():
    wiki_page_num = WikiPage.objects.count()
    wiki_file_num = WikiFile.objects.count()
    wiki_user_num = WikiUser.objects.count()
    return render_template(
        'admin/group_admin.html',
        wiki_page_num=wiki_page_num,
        wiki_file_num=wiki_file_num,
        wiki_user_num=wiki_user_num
    )


@blueprint.route('/all-pages')
@admin_required
def all_pages():
    fields = ['title', 'modified_on', 'modified_by']
    query_set = WikiPage.objects.only(*fields).order_by('+id')
    kwargs = paginate(query_set)
    return render_template(
        'admin/all_pages.html',
        **kwargs
    )


@blueprint.route('/all-files')
@admin_required
def all_files():
    query_set = WikiFile.objects.order_by('+id')
    kwargs = paginate(query_set)
    return render_template(
        'admin/all_files.html',
        **kwargs
    )


@blueprint.route('/all-users', methods=['GET', 'POST'])
@admin_required
def all_users():
    form = NewUserForm()

    if form.validate_on_submit():
        user = WikiUser.objects(name=form.username.data).first()
        if not user:
            new_user = WikiUser(
                name=form.username.data,
                email=form.email.data,
                is_admin=form.is_admin.data
            )
            new_user.set_password(form.password.data)
            new_user.save()
            flash('New user added')
            return redirect(url_for('.all_users'))
        else:
            flash('User already exists.')
    else:
        flash_errors(form)

    all_wiki_users = WikiUser.objects.order_by('+id').all()
    return render_template(
        'admin/all_users.html',
        form=form,
        all_wiki_users=all_wiki_users
    )


@blueprint.route('/manage-user/<wiki_user_id>', methods=['GET', 'POST'])
@admin_required
def manage_user():
    user = WikiUser.objects(id=wiki_user_id).first()
    if user is None:
        return redirect(url_for('.all_user'))

    form = ManageUserForm(
        username=user.name,
        email=user.email,
        is_admin=user.is_admin
    )

    if form.validate_on_submit():
        if form.remove.data:
            user.delete()
            flash('User removed.', 'warning')
        else:
            user.username = form.username.data
            user.email = form.email.data
            user.is_admin = form.is_admin.data
            if not form.password.data:
                user.set_password(form.password.data)
            user.save()
            flash('User updated.', 'info')
        return redirect(url_for('.all_user'))
    else:
        flash_errors(form)

    return render_template(
        'admin/manage_user.html',
        form=form
    )


# TODO: add filters, such as date, user
@blueprint.route('/login-record')
@admin_required
def login_record():
    query_set = WikiLoginRecord.objects
    kwargs = paginate(query_set)
    return render_template(
        'admin/login_record.html',
        **kwargs
    )

# TODO: delete page
# TODO: delete file