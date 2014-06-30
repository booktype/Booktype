import re
import cgi
import json

from django import template
from django.contrib.auth import models as auth_models
from django.core.urlresolvers import reverse
from django.conf import settings

from booki.editor import models
from booktype.utils import config


register = template.Library()


@register.simple_tag
def username(user):
    """Returns full name of the user.

    Args:
        user: User object

    Returns:
        Returns Full name of the user if possible. If user is not authenticated it will return "Anonymous"
        value. If user is authenticated and does not have defined Full name it will return username.
    """

    name = user.username
    if user.is_authenticated():
        if user.first_name.strip() != '':
            name = user.first_name
    else:
        name = 'Anonymous'

    return name

###############################################################################################################


class FormatGroupsNode(template.Node):
    def render(self, context):
        t = template.loader.get_template('core/booktype_groups.html')

        return t.render(template.Context({
            'groups': models.BookiGroup.objects.all().order_by("name"),
            'books': models.Book.objects.filter(hidden=False)}, autoescape=context.autoescape))


@register.tag(name="booktype_groups")
def booktype_groups(parser, token):
    return FormatGroupsNode()

###############################################################################################################


class FormatBooktypeNode(template.Node):
    def __init__(self, booktype_data):
        self.booktype_data = template.Variable(booktype_data)

    def render(self, context):
        chapter = self.booktype_data.resolve(context)

        if chapter.content.find('##') == -1:
            return chapter.content

        lns = []

        for ln in chapter.content.split("\n"):
            macro_re = re.compile(r'##([\w\_]+)(\{[^\}]*\})?##')

            while True:
                mtch = macro_re.search(ln)

                if mtch:
                    try:
                        t = template.loader.get_template_from_string('{%% load booktype_tags %%} {%% booktype_%s book args %%}' % (mtch.group(1).lower(),))
                        con = t.render(template.Context({"content": chapter,
                                                         "book": chapter.version.book,
                                                         "args": mtch.group(2)}))
                    except template.TemplateSyntaxError:
                        con = '<span style="background-color: red; color: white; font-weight: bold">ERROR WITH MACRO %s</span>' % (mtch.group(1).lower(), )

                    ln = ln[:mtch.start()] + con + ln[mtch.end():]
                else:
                    break

            lns.append(ln)

        return "\n".join(lns)


@register.tag(name="booktype_format")
def booktype_format(parser, token):
    try:
        tag_name, booktype_data = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly one argument" % token.contents.split()[0]

    return FormatBooktypeNode(booktype_data)


###############################################################################################################

class FormatAuthorsNode(template.Node):
    def __init__(self, book, args):
        self.book = template.Variable(book)
        self.args = template.Variable(args)

    def render(self, context):
        book = self.book.resolve(context)

        t = template.loader.get_template('core/authors.html')

        chapters = []

        excluded_users = [ae.user for ae in models.AttributionExclude.objects.filter(book=book)]

        # this should be book version, not book

        for chapter in models.BookToc.objects.filter(book=book).order_by("-weight"):
            if not chapter:
                continue
            if not chapter.chapter:
                continue

            authors = {}

            for us_id in models.ChapterHistory.objects.filter(chapter=chapter.chapter).distinct():
                if not us_id:
                    continue

                usr = auth_models.User.objects.get(id=us_id.user.id)

                if usr in excluded_users:
                    continue

                modified_year = us_id.modified.strftime('%Y')

                if usr.username in authors:
                    _years = authors[usr.username][1]

                    if modified_year not in _years:
                        authors[usr.username][1].append(modified_year)

                else:
                    authors[usr.username] = [usr, [modified_year]]

            chapters.append({"authors": authors.values(),
                             "name": chapter.chapter.title})

        copyright_description = self.args.resolve(context) or ''

        return t.render(template.Context({'chapters': chapters,
                                          "copyright": copyright_description[1:-1]},
                                         autoescape=context.autoescape))


@register.tag(name="booktype_authors")
def booktype_authors(parser, token):
    """
    Django Tag. Shows list of authors for this book. Accepts one argument, book. Reads template authors.html.
    Needs a lot of work.

        {% load booktype_tags %}
        {% booktype_authors book %}
    """

    try:
        tag_name, book, args = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError, "%r tag requires exactly two argument" % token.contents.split()[0]

    return FormatAuthorsNode(book, args)


@register.filter
def jsonlookup(d, key):
    d2 = json.loads(d)

    return d2[key]


@register.simple_tag
def booktype_site_metadata():
    s = ''

    # probably should add namespace to html tag
    name = config.get_configuration('BOOKTYPE_SITE_NAME', None)
    if name:
        s += '<meta property="og:site_name" content="%s"/>' % cgi.escape(name, True)

    tagline = config.get_configuration('BOOKTYPE_SITE_TAGLINE', None)
    if tagline:
        s += '<meta name="description" content="%s"/>' % cgi.escape(tagline, True)

    return s


@register.simple_tag
def booktype_site_name():
    frontpage_url = reverse('portal:frontpage')

    name = config.get_configuration('BOOKTYPE_SITE_NAME', None)
    if name:
        s = '<div class="logotext"><a href="%s%s">%s</a> </div>' % (settings.BOOKTYPE_URL, frontpage_url, name)
    else:
        s = '<div class="logo"><a href="%s%s"></a></div>' % (settings.BOOKTYPE_URL, frontpage_url)

    return s


@register.simple_tag
def booktype_site_favicon():
    favicon = config.get_configuration('BOOKTYPE_SITE_FAVICON', None)
    if favicon:
        s = '<link rel="SHORTCUT ICON" href="%s" type="image/x-icon">' % cgi.escape(favicon, True)
    else:
        s = '<link rel="SHORTCUT ICON" href="%score/img/favicon.ico" type="image/x-icon">' % settings.STATIC_URL

    return s


@register.filter
def booktype_anyone_register(object):
    return config.get_configuration('FREE_REGISTRATION', True)    