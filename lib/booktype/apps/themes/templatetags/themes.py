import os

from django import template
from django.template.base import Template
from django.conf import settings

from ..utils import read_theme_info

register = template.Library()


@register.inclusion_tag('themes/list.html')
def list_themes():
    themes = []

    for theme in os.listdir('{}/themes/'.format(settings.BOOKTYPE_ROOT)):
        if os.path.isdir('{}/themes/{}/'.format(settings.BOOKTYPE_ROOT, theme)):
            if os.path.exists('{}/themes/{}/info.json'.format(settings.BOOKTYPE_ROOT, theme)):
                info = read_theme_info('{}/themes/{}/info.json'.format(settings.BOOKTYPE_ROOT, theme))
                themes.append((theme, info.get('name', '')))

    themes.sort()

    return {'themes': themes}


@register.inclusion_tag('themes/options.html', takes_context=True)
def list_theme_options(context):
    options = []

    for theme in os.listdir('{}/themes/'.format(settings.BOOKTYPE_ROOT)):
        if os.path.isdir('{}/themes/{}/'.format(settings.BOOKTYPE_ROOT, theme)):
            if os.path.exists('{}/themes/{}/panel.html'.format(settings.BOOKTYPE_ROOT, theme)):
                f = open('{}/themes/{}/panel.html'.format(settings.BOOKTYPE_ROOT, theme), 'rt')
                s = f.read()
                f.close()

                t = Template(unicode(s, 'utf8'))
                content = t.render(context)

                options.append({'name': theme, 'content': content})

    return {'options': options}


@register.inclusion_tag('themes/preloads.html')
def list_theme_preloads():
    from django.contrib.staticfiles.templatetags.staticfiles import static

    options = []

    for theme in os.listdir('{}/themes/'.format(settings.BOOKTYPE_ROOT)):
        if os.path.isdir('{}/themes/{}/'.format(settings.BOOKTYPE_ROOT, theme)):
            if os.path.exists('{}/themes/{}/static/preload.css'.format(settings.BOOKTYPE_ROOT, theme)):
                options.append(static('themes/{}/preload.css'.format(theme)))

    return {'preloads': options, 'DATA_URL': settings.DATA_URL}
