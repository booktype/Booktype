import os

from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings

from booktype.apps.themes.utils import read_theme_info


class ThemeList(APIView):
    """
    API endpoint that lists all themes.
    """

    def get(self, request, *args, **kwargs):
        # TODO think about permissions here

        themes = []

        for theme in os.listdir('{}/themes/'.format(settings.BOOKTYPE_ROOT)):
            if os.path.isdir(
                    '{}/themes/{}/'.format(settings.BOOKTYPE_ROOT, theme)):

                theme_serialized = {
                    'name': theme,
                    'info': None,
                    'fonts': {},
                }
                # info
                if os.path.exists('{}/themes/{}/info.json'.format(
                        settings.BOOKTYPE_ROOT, theme)):
                    info = read_theme_info(
                        '{}/themes/{}/info.json'.format(settings.BOOKTYPE_ROOT,
                                                        theme))
                    theme_serialized['info'] = info.get('name', '')

                themes.append(theme_serialized)

                # fonts
                if os.path.isdir(
                        '{}/themes/{}/static/fonts/'.format(
                            settings.BOOKTYPE_ROOT, theme)
                ):
                    for font in os.listdir(
                            '{}/themes/{}/static/fonts/'.format(
                                settings.BOOKTYPE_ROOT, theme)):
                        if font.endswith('.ttf'):

                            font_key = font.split('-', 1)[0]
                            font_value = {
                                'name': font.split('.')[0].replace('-', ' '),
                                'file': font
                            }

                            if font_key not in theme_serialized['fonts']:
                                theme_serialized['fonts'][font_key] = [
                                    font_value
                                ]
                            else:
                                theme_serialized['fonts'][font_key].append(
                                    font_value
                                )

        themes.sort()

        return Response(themes)
