import os

from django import template
from django.conf import settings

from ..utils import read_theme_info

register = template.Library()


@register.inclusion_tag('themes/list.html')
def list_themes():
    themes = []

    for theme in os.listdir('{}/themes/'.format(settings.DATA_ROOT)):
        if os.path.isdir('{}/themes/{}/'.format(settings.DATA_ROOT, theme)):
            if os.path.exists('{}/themes/{}/info.json'.format(settings.DATA_ROOT, theme)):
                info = read_theme_info('{}/themes/{}/info.json'.format(settings.DATA_ROOT, theme))
                themes.append((theme, info.get('name', '')))
    
    return {'themes': themes}


@register.inclusion_tag('themes/options.html')
def list_theme_options():
    options = []

    for theme in os.listdir('{}/themes/'.format(settings.DATA_ROOT)):
        if os.path.isdir('{}/themes/{}/'.format(settings.DATA_ROOT, theme)):
            if os.path.exists('{}/themes/{}/panel.html'.format(settings.DATA_ROOT, theme)):
                f = open('{}/themes/{}/panel.html'.format(settings.DATA_ROOT, theme), 'rt')
                s = f.read()
                f.close()
                
                t = template.Template(unicode(s, 'utf8'))
                c = template.Context({})

                content = t.render(c)

                options.append({'name': theme, 'content': content})
    
    return {'options': options}


@register.inclusion_tag('themes/preloads.html')
def list_theme_preloads():
    options = []

    for theme in os.listdir('{}/themes/'.format(settings.DATA_ROOT)):
        if os.path.isdir('{}/themes/{}/'.format(settings.DATA_ROOT, theme)):
            if os.path.exists('{}/themes/{}/preload.css'.format(settings.DATA_ROOT, theme)):
                options.append(theme)
    
    return {'options': options, 'DATA_URL': settings.DATA_URL}    