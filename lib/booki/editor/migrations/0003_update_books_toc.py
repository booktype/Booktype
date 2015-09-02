# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def update_tocs(apps, schema_editor):
    # not using this because an error about missing get_toc method
    # BookVersion = apps.get_model('editor', 'BookVersion')  # noqa

    for book_version in apps.get_model('editor', 'BookVersion').objects.all():
        prev_section = None
        toc_items = apps.get_model('editor', 'BookToc').objects.filter(version=book_version).order_by("-weight")

        for toc_item in toc_items:
            # if item is section, the parent remains in None
            # but assign it as prev_section
            if toc_item.typeof == 0:
                prev_section = toc_item

            # if item is chapter, we assign prev_section as parent
            elif toc_item.typeof == 1:
                if prev_section:
                    toc_item.parent = prev_section
                    toc_item.save()


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0002_load_initial_data'),
    ]

    operations = [
        migrations.RunPython(update_tocs),
    ]
