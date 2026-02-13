# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def create_user_css(apps, schema_editor):
    from django.conf import settings
    import os

    try:
        if not os.path.exists('%s/css/' % settings.STATIC_ROOT):
            try:
                os.mkdir('%s/css/' % settings.STATIC_ROOT)
            except OSError as err:
                print(err)
                raise RuntimeError('Can not create css directory.')

        f = open('%s/css/_user.css' % settings.STATIC_ROOT, 'w')
        f.write(' ')
        f.close()
    except IOError as err:
        print(err)
        raise RuntimeError('Can not create the file.')


class Migration(migrations.Migration):

    dependencies = [
        ('booktypecontrol', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_user_css)
    ]
