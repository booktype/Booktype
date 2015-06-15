# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0003_update_books_toc'),
        ('export', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ExportSettings',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('typeof', models.CharField(max_length=20, verbose_name='Export type')),
                ('data', models.TextField(default=b'{}', verbose_name='Data')),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='Created')),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book')),
            ],
            options={
                'verbose_name': 'Export Settings',
                'verbose_name_plural': 'Export Settings',
            },
            bases=(models.Model,),
        ),
    ]
