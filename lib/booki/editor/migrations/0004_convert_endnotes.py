# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import lxml.html
from lxml import etree

from django.db import models, migrations

from booktype.importer.epub.epubimporter import EpubImporter


def convert_endnotes(apps, schema_editor):
    Chapter = apps.get_model('editor', 'Chapter')

    for chapter in Chapter.objects.all():
        tree = lxml.html.fragment_fromstring(chapter.content, create_parent=True,
                                             parser=lxml.html.HTMLParser(encoding='utf-8'))

        # converting
        tree, _ = EpubImporter.convert_endnotes(tree)

        content = unicode(etree.tostring(tree, pretty_print=True, encoding='utf-8',
                                         xml_declaration=False), 'utf-8')

        # remove redundant div wrapper
        a = len(u"<div>")
        b = content.rfind(u"</div>")
        chapter.content = content[a:b]

        chapter.save()


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0003_update_books_toc'),
    ]

    operations = [
        migrations.RunPython(convert_endnotes)
    ]
