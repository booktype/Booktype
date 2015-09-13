# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0005_bookversion_track_changes'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='publishwizzard',
            options={'verbose_name': 'Publish Wizard', 'verbose_name_plural': 'Publish Wizard'},
        ),
        migrations.AlterField(
            model_name='language',
            name='abbrevation',
            field=models.CharField(max_length=10, verbose_name='abbreviation'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='license',
            name='abbrevation',
            field=models.CharField(max_length=30, verbose_name='abbreviation'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='publishwizzard',
            name='wizz_options',
            field=models.TextField(default=b'', verbose_name='wizard options'),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='publishwizzard',
            name='wizz_type',
            field=models.CharField(max_length=20, verbose_name='wizard type'),
            preserve_default=True,
        ),
    ]
