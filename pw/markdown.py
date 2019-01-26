from flask import g
import re
from mistune import Markdown, Renderer, InlineLexer
from mistune_contrib.toc import TocMixin
from flask_login import current_user

from pw.models import WikiPage, WikiFile, WikiUser


class WikiRenderer(TocMixin, Renderer):

    def wiki_page(self, title):
        wiki_page_title = title
        wiki_page = (WikiPage
                     .objects(title=wiki_page_title)
                     .only('title')
                     .first())
        if not wiki_page:
            wiki_page = WikiPage(
                title=wiki_page_title,
                modified_by=current_user.name
            ).save()
        g.wiki_page.refs.append(wiki_page)

        return render_wiki_page(wiki_page.id, wiki_page_title)

    def wiki_file(self, wiki_file_id, wiki_file_type, w, h):
        w = w or 0
        h = h or 0
        w, h = int(w), int(h)

        wiki_file = WikiFile.objects(id=wiki_file_id).first()
        if wiki_file:
            return render_wiki_file(
                wiki_file.id,
                wiki_file.name,
                wiki_file_type,
                w=w,
                h=h
            )

    def wiki_at(self, username):
        u = WikiUser.objects(name=username).first()
        if u is not None:
            g.users_to_email.append(u)
            return '<strong class="wiki-user-notification">[@{0}]</strong>'.format(username)


class WikiInlineLexer(InlineLexer):

    def enable_wiki_page(self):
        self.rules.wiki_page = re.compile(r'\[\[(.+?)\]\]')
        self.default_rules.insert(0, 'wiki_page')

    def output_wiki_page(self, m):
        return self.renderer.wiki_page(m.group(1))

    def enable_wiki_file(self):
        self.rules.wiki_file = re.compile(r'\[(file|image):(\d+)(@(\d+)x(\d+))?\]')
        self.default_rules.insert(1, 'wiki_file')

    def output_wiki_file(self, m):
        _, wiki_file_type, wiki_file_id, wh, w, h = [m.group(i) for i in range(6)]
        return self.renderer.wiki_file(wiki_file_id, wiki_file_type, w, h)

    def enable_wiki_at(self):
        self.rules.wiki_at = re.compile(r'\[@(.+?)\]')
        self.default_rules.insert(2, 'wiki_at')

    def output_wiki_at(self, m):
        username = m.group(2)
        return self.renderer.wiki_at(username)


class WikiMarkdown:
    def __init__(self):
        renderer = WikiRenderer()
        inline = WikiInlineLexer(renderer)
        # enable the feature
        inline.enable_wiki_page()
        inline.enable_wiki_file()
        self.markdown = Markdown(renderer, inline=inline)

    def __call__(self, wiki_page, markdown):
        g.wiki_page = wiki_page
        g.users_to_email = list()
        self.markdown.renderer.reset_toc()
        html = self.markdown.parse(markdown)

        # workaround for when there is no headings
        try:
            toc = self.markdown.renderer.render_toc(level=3)
        except TypeError:
            toc = ''
        return toc, html


def render_wiki_page(
    wiki_page_id,
    wiki_page_title
):
    return '<a class="wiki-page" href="/{0}/page/{1}">{2}</a>'.format(
        g.wiki_group,
        wiki_page_id,
        wiki_page_title
    )


def render_wiki_file(
    wiki_file_id,
    wiki_file_name,
    wiki_file_type,
    w=0,
    h=0
):
    link = '/{0}/file/{1}'.format(g.wiki_group, wiki_file_id)

    if wiki_file_type == 'image':
        temp = ['src={0}'.format(link)]
        if w:
            temp.append('width="{0}"'.format(w))
        if h:
            temp.append('height="{0}"'.format(h))
        return '<img class="wiki-file" {0} />'.format(' '.join(temp))
    elif wiki_file_type == 'file':
        return (
        '<a class="wiki-file" href="{0}">'
        '<img alt="file icon" height="20" src="/static/images/file-icon.png" width="20" />'
        '{1}</a>'.format(link, wiki_file_name)
        )
