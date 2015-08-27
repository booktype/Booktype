# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0004_convert_endnotes'),
    ]

    operations = [
        migrations.AddField(
            model_name='bookversion',
            name='track_changes',
            field=models.BooleanField(default=False),
            preserve_default=True,
        ),
    ]
