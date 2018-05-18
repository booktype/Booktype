import re
import json
import logging
from lxml import etree
from ebooklib.utils import parse_html_string

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.template.context import Context
from django.template.smartif import Literal
from django.template.defaulttags import TemplateIfParser, IfNode

from django.contrib.auth import models as auth_models
from django.core.urlresolvers import reverse
from django.conf import settings

from booki.editor import models
from booktype.utils import config

register = template.Library()

logger = logging.getLogger('booktype')


def tag_username(user):
    """Returns full name of the user.

    Args:
        user: User object

    Returns:
        Returns Full name of the user if possible. If user is not authenticated
             it will return "Anonymous"
        value. If user is authenticated and does not have defined Full name
            it will return username.
    """

    name = user.username
    if user.is_authenticated():
        if user.first_name.strip() != '':
            name = user.first_name
    else:
        name = 'Anonymous'

    return name

register.simple_tag(func=tag_username, name='username')
register.filter(filter_func=tag_username, name='username')


###############################################################################
class FormatGroupsNode(template.Node):

    def render(self, context):
        t = template.loader.get_template('core/booktype_groups.html')

        return t.render({
            'groups': models.BookiGroup.objects.all().order_by("name"),
            'books': models.Book.objects.filter(hidden=False)
        })


@register.tag(name="booktype_groups")
def booktype_groups(parser, token):
    return FormatGroupsNode()


###############################################################################
class FormatBooktypeNode(template.Node):

    def __init__(self, booktype_data):
        self.booktype_data = template.Variable(booktype_data)

    @staticmethod
    def _reformat_endnotes(content):

        try:
            tree = parse_html_string(content.encode('utf-8'))
        except Exception as err:
            logger.error('Error parsing chapter content {err}'.format(err=err))
            return content

        for elem in tree.iter():
            # remove endnotes without reference
            if elem.tag == 'ol' and elem.get('class') == 'endnotes':
                for li in elem.xpath("//li[@class='orphan-endnote']"):
                    li.drop_tree()

            # insert internal link to endnote's body into the sup
            elif elem.tag == 'sup' and elem.get('data-id'):
                a = etree.Element("a")
                a.set('href', '#endnote-{0}'.format(elem.get('data-id')))
                a.text = elem.text
                elem.text = ''
                elem.insert(0, a)

        content = etree.tostring(tree, method='html', encoding='utf-8', xml_declaration=False)
        content = content.replace('<html><body>', '').replace('</body></html>', '')

        return content

    def render(self, context):
        chapter = self.booktype_data.resolve(context)

        if chapter is None:
            return ""

        chapter.content = self._reformat_endnotes(chapter.content)

        if chapter.content.find('##') == -1:
            return chapter.content

        lns = []

        for ln in chapter.content.split("\n"):
            macro_re = re.compile(r'##([\w\_]+)(\{[^\}]*\})?##')

            while True:
                mtch = macro_re.search(ln)

                if mtch:
                    try:
                        tag_text = '{%% load booktype_tags %%} \
                            {%% booktype_%s book args %%}'
                        t = template.loader.get_template_from_string(
                            tag_text % (mtch.group(1).lower(),))
                        con = t.render({
                            "content": chapter,
                            "book": chapter.version.book,
                            "args": mtch.group(2)
                        })
                    except template.TemplateSyntaxError:
                        con = '<span style="background-color: red; \
                            color: white; font-weight: bold">\
                            ERROR WITH MACRO %s</span>' %\
                            (mtch.group(1).lower(), )

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
        raise template.TemplateSyntaxError(
            "%r tag requires exactly one argument" %
            token.contents.split()[0])

    return FormatBooktypeNode(booktype_data)


##########################################################################

class FormatAuthorsNode(template.Node):

    def __init__(self, book, args):
        self.book = template.Variable(book)
        self.args = template.Variable(args)

    def render(self, context):
        book = self.book.resolve(context)

        t = template.loader.get_template('core/authors.html')

        chapters = []

        excluded_users = [
            ae.user for ae in models.AttributionExclude.objects.filter(
                book=book)]

        # this should be book version, not book

        for chapter in models.BookToc.objects.filter(
                book=book).order_by("-weight"):
            if not chapter:
                continue
            if not chapter.chapter:
                continue

            authors = {}

            for us_id in models.ChapterHistory.objects.filter(
                    chapter=chapter.chapter).distinct():
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

        return t.render({
            'chapters': chapters,
            "copyright": copyright_description[1:-1]
        })


@register.tag(name="booktype_authors")
def booktype_authors(parser, token):
    """
    Django Tag. Shows list of authors for this book. Accepts one argument, book
    Reads template authors.html. Needs a lot of work.

        {% load booktype_tags %}
        {% booktype_authors book %}
    """

    try:
        tag_name, book, args = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r tag requires exactly two argument" %
            token.contents.split()[0])

    return FormatAuthorsNode(book, args)


@register.filter
def jsonlookup(d, key):
    d2 = json.loads(d)

    return d2[key]


@register.simple_tag
def booktype_site_metadata():
    """Simple tag to load sitename and tagline from custom configuration"""

    meta_tags = ''

    name = config.get_configuration('BOOKTYPE_SITE_NAME', None)
    if name:
        meta_tags += '<meta property="og:site_name" content="%s" />' % escape(name)

    tagline = config.get_configuration('BOOKTYPE_SITE_TAGLINE', None)
    if tagline:
        meta_tags += '\n<meta name="description" content="%s" />' % escape(tagline)

    return mark_safe(meta_tags)


@register.simple_tag
def booktype_site_name():
    name = config.get_configuration('BOOKTYPE_SITE_NAME', None)
    default_url = '{0}{1}'.format(settings.BOOKTYPE_URL, reverse('portal:frontpage'))
    frontpage_url = config.get_configuration('BOOKTYPE_FRONTPAGE_URL', default_url)

    if name:
        markup = '<div class="logotext"><a href="%s">%s</a></div>' % (frontpage_url, name)
    else:
        markup = '<div class="logo"><a href="%s"></a></div>' % (frontpage_url)

    return mark_safe(markup)


@register.simple_tag
def booktype_site_favicon():
    """Simple tag to load default booktype favicon or custom one from settings"""

    from django.templatetags.static import static

    default = static('core/img/favicon.ico')
    favicon = config.get_configuration('BOOKTYPE_SITE_FAVICON', default)
    html = '<link rel="shortcut icon" href="%s" type="image/x-icon">' % escape(favicon)

    return mark_safe(html)


@register.filter
def booktype_anyone_register(object):
    return config.get_configuration('FREE_REGISTRATION', True)


@register.simple_tag
def role_ids_for(user, book):
    """
    Returns a list of ids of the roles for a given user and a book

    Arguments:
        - user: Django user instance
        - book: instance of the book to scope the roles of the user
    """

    return [r.role.id for r in user.roles.filter(book=book)]


@register.filter
def order_by(queryset, order_field):
    """Orders a given queryset with the desired order_field as param"""

    return queryset.order_by(order_field)


@register.assignment_tag(takes_context=True)
def has_perm(context, permission_string):
    """Checks if a given user has a specific permission.

    :Args:
      - context (:class:`dict`): Django template context
      - permission_string (:class:`str`): Concatenated string of app name and permission codename
                                          e.g. "editor.create_chapter"

    :Returns:
      Returns (:class:`bool`) True or False
    """

    return context['security'].has_perm(permission_string)


class PermissionLiteral(Literal):
    """
    This class just extends the basic Literal. We just override the eval method
    which checks if the user has the given permission
    """

    @property
    def perm_string(self):
        return template.Variable(self.value).resolve({})

    def eval(self, context):
        return context['security'].has_perm(self.perm_string)


class TemplateCheckPermParser(TemplateIfParser):

    def create_var(self, value):
        """
        This override checks if the value param has the permission nomenclature e.g:
        something like "app.perm_string"
        """
        try:
            if len(value.split('.')) == 2:
                return PermissionLiteral(value)
        except:
            return super(TemplateCheckPermParser, self).create_var(value)


def do_has_perm(parser, token):

    # {% check_perm ... %}
    bits = token.split_contents()[1:]
    condition = TemplateCheckPermParser(parser, bits).parse()
    nodelist = parser.parse(('else', 'endcheck_perm'))
    conditions_nodelists = [(condition, nodelist)]
    token = parser.next_token()

    # {% else %} (optional)
    if token.contents == 'else':
        nodelist = parser.parse(('endcheck_perm',))
        conditions_nodelists.append((None, nodelist))
        token = parser.next_token()

    # this tag should end in {% endcheck_perm %}
    assert token.contents == 'endcheck_perm'

    return IfNode(conditions_nodelists)

register.tag('check_perm', do_has_perm)


class AssignNode(template.Node):
    def __init__(self, name, value):
        self.name = name
        self.value = value

    def render(self, context):
        context[self.name] = self.value.resolve(context, True)
        return ''


@register.tag(name="assign")
def do_assign(parser, token):
    """
    Assign an expression to a variable in the current context.

    Syntax::
        {% assign [name] [value] %}
    Example::
        {% assign list entry.get_related %}

    """

    bits = token.contents.split()
    if len(bits) != 3:
        raise template.TemplateSyntaxError("'%s' tag takes two arguments" % bits[0])
    value = parser.compile_filter(bits[2])
    return AssignNode(bits[1], value)


@register.simple_tag
def add_url_query_param(request, key, value):
    key_value = request.GET.copy()
    key_value[key] = value

    return key_value.urlencode()


@register.inclusion_tag('templatetags/pagination.html', takes_context=True)
def booktype_pagination(context, page_object, pagination_class=None):
    """
    Render bootstrap based paginator.
    Usage: {% booktype_pagination page_obj 'right' %}

    :Args:
      - page_object (:class:`django.core.paginator.Page`): page object
      - size (:class:`str`): Use 'lg', 'sm' or leave empty

    :Returns:
      Returns rendered pagination html
    """
    page_range = list(page_object.paginator.page_range)
    page_count = len(page_object.paginator.page_range)
    page_object.paginator.page_range_cutted = page_range

    if page_count > 16:

        page_object.paginator.page_range_cutted = []

        if page_object.number <= 5:
            page_object.paginator.page_range_cutted += page_range[:page_object.number + 2]
        else:
            page_object.paginator.page_range_cutted.append(1)

        page_object.paginator.page_range_cutted.append('..')

        if page_object.number <= 5:
            page_object.paginator.page_range_cutted += page_range[page_count - 2:]
        else:
            if page_object.number + 4 < page_count:
                page_object.paginator.page_range_cutted += page_range[page_object.number - 3:page_object.number + 2]
                page_object.paginator.page_range_cutted.append('..')
                page_object.paginator.page_range_cutted.append(page_count)
            else:
                page_object.paginator.page_range_cutted += page_range[page_object.number - 3:]

    pagination_data = {'page_object': page_object, 'request': context['request']}

    if pagination_class:
        pagination_data['pagination_class'] = 'pagination-{0}'.format(pagination_class)

    return pagination_data


@register.inclusion_tag('templatetags/pager.html', takes_context=True)
def booktype_pager(context, page_object):
    """
    Render bootstrap based pager.
    Usage: {% booktype_pagination page_obj 'right' %}

    :Args:
      - page_object (:class:`django.core.paginator.Page`): page object
      - size (:class:`str`): Use 'lg', 'sm' or leave empty

    :Returns:
      Returns rendered pager html
    """

    pagination_data = {'page_object': page_object, 'request': context['request']}
    return pagination_data


@register.inclusion_tag('templatetags/google_analytics.html', takes_context=True)
def google_analytics(context):
    """
    Add google analytics async tracking code.
    Usage: {% google_analytics %}

    :Returns:
      Returns rendered java script code's block
    """
    data = {'USE_GOOGLE_ANALYTICS': config.get_configuration('USE_GOOGLE_ANALYTICS'),
            'GOOGLE_ANALYTICS_ID': config.get_configuration('GOOGLE_ANALYTICS_ID')}

    if context['request'].user.is_superuser:
        data['USE_GOOGLE_ANALYTICS'] = False

    return data


@register.simple_tag
def random_url(length=12):
    from random import randint
    return randint(10**(length - 1), (10**(length) - 1))
