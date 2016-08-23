# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0006_auto_20150913_1528'),
    ]

    operations = [
        migrations.AddField(
            model_name='booktoc',
            name='settings',
            field=models.TextField(verbose_name='settings', blank=True),
            preserve_default=True,
        ),
    ]
