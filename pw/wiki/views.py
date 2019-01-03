# -*- coding: utf-8 -*-
"""Wiki section, including wiki pages for each group."""
from flask import (Blueprint, g, request, redirect, url_for, render_template,
                   flash)
import os
from datetime import date, datetime, timedelta
from flask_login import login_required, current_user
import difflib

from pw.decorators import decorate_blueprint
from pw.extensions import db, markdown
from pw.wiki.forms import (SearchForm, CommentForm, WikiEditForm, UploadForm,
                           RenameForm, HistoryRecoverForm)
from pw.models import WikiPage, WikiPageVersion, WikiFile
from pw.settings import UPLOAD_PATH
from pw.markdown import render_wiki_page, render_wiki_file
from pw.utils import flash_errors, get_pagination_kwargs
from pw.diff import make_patch, apply_patches

blueprint = Blueprint('wiki', __name__, static_folder='../static', url_prefix='/<wiki_group>')
decorate_blueprint(blueprint)


@blueprint.route('/home')
@login_required
def home():
    """Home page."""
    wiki_page = WikiPage.objects(title='Home').only('id').first()
    return redirect(url_for('.page', wiki_page_id=wiki_page.id))


@blueprint.route('/page/<wiki_page_id>')
@login_required
def page(wiki_page_id):
    comment_form = CommentForm()
    wiki_page = (WikiPage
                 .objects
                 .excluede('versions', 'refs')
                 .get_or_404(id=wiki_page_id))

    if form.validate_on_submit():
        g.wiki_page = wiki_page
        _, comment_html = markdown(form.textArea.data)
        new_comment = WikiComment(
            author=current_user.name,
            html=comment_html,
            md=form.textArea.data
        )

        (WikiPage
         .objects(id=wiki_page_id)
         .update_one(push__comments=new_comment))

        # TODO: add user emailing
        # user_emails = [u.email for u in g.users_to_notify]
        # send_email(user_emails, 'You are mentioned', 
        #             '{} ({}) mentioned you at <a href="{}#wiki-comment-box">{}</a>'.\
        #             format(current_user.name, 
        #                     current_user.email, 
        #                     request.base_url, 
        #                     page.title))
        return redirect(url_for(
            '.page', 
            wiki_page_id=wiki_page_id, 
            _anchor='wiki-comment-box'
        ))

    return render_template(
        'wiki/page.html',
        wiki_page=wiki_page
    )


# @blueprint.route('/handle-comment', methods=['POST'])
# def handle_comment():
#     form = request.form


@blueprint.route('/edit/<wiki_page_id>', methods=['GET', 'POST'])
@login_required
def edit(wiki_page_id):
    fields = ['title', 'md', 'current_version',
              'modified_on', 'modified_by']
    wiki_page = (WikiPage.objects
                 .no_dereference()
                 .only(*fields)
                 .get_or_404(id=wiki_page_id))
    edit_form = WikiEditForm()
    upload_form = UploadForm()

    if edit_form.validate_on_submit():
        if edit_form.current_version.data == wiki_page.current_version:
            diff = make_patch(wiki_page.md, edit_form.textArea.data)
            if diff:
                g.wiki_page = wiki_page
                toc, html = markdown(edit_form.textArea.data)
                md = edit_form.textArea.data
                wiki_page.update_db(diff, md, html, toc=toc)

            return redirect(url_for('.page', wiki_page_id=wiki_page.id))
        else:
            flash('Other changes have been made to this '
                  'wiki page since you started editing it.')

    return render_template(
        'wiki/edit.html',
        wiki_page=wiki_page,
        edit_form=edit_form,
        upload_form=upload_form
    )


@blueprint.route('/upload/<wiki_page_id>')
@login_required
def upload(wiki_page_id):
    form = UploadForm()
    return render_template(
        'wiki/upload.html', 
        wiki_page_id=wiki_page_id,
        form=form
    )


@blueprint.route('/handle-upload', methods=['POST'])
@login_required
def handle_upload():
    form = request.form
    wiki_page_id = form.get('wiki_page_id', None)
    upload_from_upload_page = form.get('upload_page', None)

    file_markdown, file_html = '', ''
    wiki_files = list()
    for i, file in enumerate(request.files.getlist('wiki_file')):
        # TODO: add uploaded_by
        wiki_file = WikiFile(name=file.filename, mime_type=file.mime_type)
        file.save(os.path.join(UPLOAD_PATH, g.wiki_group, str(wiki_file.id)))
        # Use the position of file pointer to get file size
        wiki_file.size = file.tell()
        wiki_file.save()

        if 'image' in wiki_file.mime_type:
            file_type = 'image'
        else:
            file_type = 'file'
        file_markdown += '\n\n[{}:{}]'.format(file_type, wiki_file.id)
        file_html += '<p>{}</p>'.format(render_wiki_file(
            wiki_file.id,
            wiki_file.name,
            file_type,
            tostring=True
        ))

    if upload_from_upload_page:
        fields = ['md', 'html', 'current_version',
                  'modified_on', 'modified_by']
        wiki_page = (WikiPage
                     .objects
                     .only(*fields)
                     .get_or_404(id=wiki_page_id))

        diff = make_patch(wiki_page.md, wiki_page.md+file_markdown)
        wiki_page.update_db(
            diff,
            wiki_page.md+file_markdown,
            wiki_page.html+file_html,
            update_refs=False
        )

        return ''

    return file_markdown


@blueprint.route('/reference/<wiki_page_id>')
@login_required
def reference(wiki_page_id):
    wiki_page = WikiPage.objects.only('title').get_or_404(id=wiki_page_id)
    wiki_referencing_pages = (WikiPage
                              .objects(refs__contains=wiki_page_id)
                              .only('title')
                              .all())

    return render_template(
        'wiki/reference.html',
        wiki_page=wiki_page,
        wiki_referencing_pages=wiki_referencing_pages
    )


@blueprint.route('/rename/<wiki_page_id>', methods=['GET', 'POST'])
@login_required
def rename(wiki_page_id):
    wiki_page = WikiPage.objects.only('title').get_or_404(id=wiki_page_id)
    if wiki_page.title == 'Home':
        return redirect(url_for('.home'))

    form = RenameForm(new_title=wiki_page.title)

    if form.validate_on_submit():
        new_title = form.new_title.data
        if wiki_page.title == new_title:
            flash('The page name is not changed.', 'warning')
        elif WikiPage.objects(title=new_title).count() > 0:
            flash('The new page title has already been taken.', 'warning')
        else:
            old_md = '[[{}]]'.format(wiki_page.title)
            new_md = '[[{}]]'.format(new_title)

            old_html = render_wiki_page(wiki_page.id, wiki_page.title, tostring=True)
            new_html = render_wiki_page(wiki_page.id, new_title, tostring=True)

            # update the markdown of referencing wiki page 
            wiki_referencing_pages = (
                WikiPage
                .objects(refs__contains=wiki_page_id)
                .only('md', 'html')
                .all()
            )

            for ref in wiki_referencing_pages:
                new_md_content = ref.md.replace(old_md, new_md)
                new_html_content = ref.html.replace(old_html, new_html)

                (WikiPage
                 .objects(id=ref.id)
                 .update_one(
                     set__md=new_md_content,
                     set__html=new_html_content))

            # update the diff of related wiki page versions
            for pv in WikiPageVersion.objects.search_text(old_md).all():
                pv.diff = pv.diff.replace(old_md, new_md)
                pv.save()

            (WikiPage
             .objects(id=wiki_page.id)
             .update_one(set__title=new_title))

            return redirect(url_for('.page', wiki_page_id=wiki_page.id))
    else:
        flash_errors(form)

    return render_template(
        'wiki/rename.html',
        wiki_page=wiki_page,
        form=form
    )


@blueprint.route('/file/<int:wiki_file_id>')
@login_required
def file(wiki_file_id):
    fn = request.args.get('filename')
    if not fn:
        wiki_file = WikiFile.objects.only('name').get_or_404(id=wiki_file_id)
        fn = wiki_file.name

    return send_from_directory(
        os.path.join(UPLOAD_PATH, g.wiki_group),
        str(wiki_file_id),
        as_attachment=True,
        attachment_filename=fn
    )


@blueprint.route('/history/<wiki_page_id>', methods=['GET', 'POST'])
@login_required
def history(wiki_page_id):
    fields = ['title', 'md', 'current_version',
              'modified_on', 'modified_by', 'versions']
    wiki_page = (WikiPage
                 .objects
                 .only(*fields)
                 .get_or_404(id=wiki_page_id))

    if wiki_page.current_version == 1:
        return redirect(url_for('.page', wiki_page_id=wiki_page_id))

    form = HistoryRecoverForm()
    if form.validate_on_submit():
        if form.version.data >= wiki_page.current_version:
            flash('Please enter an old version number.')
        else:
            old_to_current = wiki_page.versions[(form.version.data-1):]
            old_to_current_patches = [pv.diff for pv in old_to_current[::-1]]
            recovered_content = apply_patches(
                wiki_page.md,
                old_to_current_patches,
                revert=True
            )

            g.wiki_page = wiki_page
            diff = make_patch(wiki_page.md, recovered_content)
            if diff:
                toc, html = markdown(recovered_content)
                wiki_page.update_db(diff, recovered_content, html, toc=toc)
            return redirect(url_for('.page', wiki_page_id=wiki_page.id))
    else:
        flash_errors(form)

    old_ver_num = request.args.get(
        'version',
        default=wiki_page.current_version-1,
        type=int
    )
    new_ver_num = old_ver_num + 1
    if new_ver_num > wiki_page.current_version:
        return redirect(url_for(
            '.history',
            wiki_page_id=wiki_page_id,
            version=wiki_page.current_version-1
        ))

    old_to_current = wiki_page.versions[old_ver_num-1:]
    old_to_current_patches = [pv.diff for pv in old_to_current[::-1]]
    new_markdown = apply_patches(wiki_page.md, old_to_current_patches[:-1], revert=True)
    old_markdown = apply_patches(new_markdown, [old_to_current_patches[-1]], revert=True)

    diff = difflib.HtmlDiff()
    diff_table = diff.make_table(old_markdown.splitlines(), new_markdown.splitlines())
    diff_table = diff_table.replace('&nbsp;', ' ').replace(' nowrap="nowrap"', '')

    kwargs = dict()
    get_pagination_kwargs(kwargs, old_ver_num, wiki_page.current_version-1)

    return render_template(
        'wiki/history.html',
        wiki_page=wiki_page,
        form=form,
        wiki_page_versions=wiki_page_versions,
        old_ver_num=old_ver_num,
        new_ver_num=new_ver_num,
        diff_table=diff_table,
        **kwargs
    )


@blueprint.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    # TODO: add filter by user
    keyword = request.args.get('keyword')
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    current_page_number = request.args.get('page', default=1, type=int)
    number_per_page = 100
    kwargs = dict()
    form = SearchForm(search=keyword, start_date=start_date, end_date=end_date)

    if keyword and not keyword.isspace():
        filter = dict()
        if start_date:
            start_date = datetime.strptime(start_date, '%m/%d/%Y')
            filter['modified_on__gte'] = temp
        if end_date:
            end_date = datetime.strptime(end_date, '%m/%d/%Y')+timedelta(days=1)
            filter['modified_on__lte'] = temp
        results = (WikiPage
                   .objects(**filter)
                   .search_text(keyword)
                   .only('title', 'modified_on', 'modified_by')
                   .order_by('$text_score', '-modified_on')
                   .paginate(page=result_page, per_page=number_per_page))

        kwargs['data'] = results
        kwargs['number_per_page'] = number_per_page
        total_page_number = results.pages
        get_pagination_kwargs(kwargs, current_page_number, total_page_number)

    if form.validate_on_submit():
        return redirect(url_for(
            '.search',
            keyword=form.search.data,
            start=form.start_date.data,
            end=form.end_date.data
        ))

    return render_template(
        'wiki/search.html',
        form=form,
        **kwargs
    )


# TODO: add filters, such as user
@blueprint.route('/changes')
@login_required
def changes():
    current_page_number=request.args.get('page', default=1, type=int)
    number_per_page = 100
    results = (WikiPage
               .objects
               .only('title', 'modified_on', 'modified_by')
               .order_by('-modified_on')
               .paginate(current_page_number, paginate_by=number_per_page))
    total_page_number = results.pages
    kwargs = dict(data=results, number_per_page=number_per_page)
    get_pagination_kwargs(kwargs, current_page_number, total_page_number)

    return render_template(
        'wiki/changes.html',
        **kwargs
    )


@blueprint.route('/markdown')
@login_required
def markdown_instructions():
    return render_template('wiki/markdown.html')
