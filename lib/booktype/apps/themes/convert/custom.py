# -*- coding: utf-8 -*-
from booktype.apps.convert import plugin


class CustomPDF(plugin.MPDFPlugin):
    def get_mpdf_config(self):
        return {
            'mirrorMargins': True,
            'useSubstitutions': False
        }


__convert__ = {
    'mpdf': CustomPDF,
    'screenpdf': CustomPDF
}
