# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BookExport',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='Name')),
                ('task_id', models.CharField(unique=True, max_length=64, verbose_name='Task ID', db_index=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='Created')),
                ('published', models.DateTimeField(null=True, verbose_name='Published')),
                ('status', models.SmallIntegerField(default=0, verbose_name='Status')),
                ('user', models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL, null=True)),
                ('version', models.ForeignKey(verbose_name='export', to='editor.BookVersion')),
            ],
            options={
                'verbose_name': 'Book Export',
                'verbose_name_plural': 'Book Exports',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExportComment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='Created')),
                ('content', models.TextField(default=b'', verbose_name='Content')),
                ('export', models.ForeignKey(verbose_name='version', to='export.BookExport')),
                ('user', models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Export Comment',
                'verbose_name_plural': 'Export Comments',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ExportFile',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('typeof', models.CharField(max_length=20, verbose_name='Export type')),
                ('filesize', models.IntegerField(default=0, null=True, verbose_name='File size')),
                ('pages', models.IntegerField(default=0, null=True, verbose_name='Number of pages')),
                ('status', models.SmallIntegerField(default=0, verbose_name='Status')),
                ('description', models.TextField(verbose_name='Description')),
                ('filename', models.CharField(max_length=200, null=True, verbose_name='File name', blank=True)),
                ('export', models.ForeignKey(verbose_name='export', to='export.BookExport')),
            ],
            options={
                'verbose_name': 'Export File',
                'verbose_name_plural': 'Export Files',
            },
            bases=(models.Model,),
        ),
    ]
