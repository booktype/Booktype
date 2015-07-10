# -*- coding: utf-8 -*-

import uuid
from ebooklib.epub import EpubBook


class ExportEpubBook(EpubBook):

    def set_title(self, title, _type='main'):
        """
        Overrides EpubBook set_title method in order to set
        dc.title tag with the specified type to title. Default is main.

        :Args:
          - title: String of the title to be set
          - _type: String of type of title. Available: main, short, subtitle

        """

        title_id = '%s_%s' % (_type, str(uuid.uuid4())[:8])
        if _type == 'main':
            self.title = title

        # add dc.title tag
        self.add_metadata('DC', 'title', title, {'id': title_id})

        # add refines meta tag
        self.add_metadata(
            None, 'meta', _type, {
                'refines': '#%s' % title_id,
                'property': 'title-type'
            }
        )
