# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.conf import settings
import booki.editor.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('attachment', models.FileField(upload_to=booki.editor.models.uploadAttachmentTo, max_length=2500, verbose_name='filename')),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='created')),
            ],
            options={
                'verbose_name': 'Attachment',
                'verbose_name_plural': 'Attachments',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='AttributionExclude',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
            ],
            options={
                'verbose_name': 'Attribution Exclude',
                'verbose_name_plural': 'Attribution Exclude',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Book',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url_title', models.CharField(unique=True, max_length=2500, verbose_name='url title')),
                ('title', models.CharField(max_length=2500, verbose_name='title')),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='created')),
                ('published', models.DateTimeField(null=True, verbose_name='published')),
                ('hidden', models.BooleanField(default=False, verbose_name='hidden')),
                ('permission', models.SmallIntegerField(default=0, verbose_name='permission')),
                ('description', models.TextField(default=b'', verbose_name='description')),
                ('cover', models.ImageField(upload_to=b'cover_images/', null=True, verbose_name='cover')),
            ],
            options={
                'verbose_name': 'Book',
                'verbose_name_plural': 'Books',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookCover',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('cid', models.CharField(default=b'', unique=True, max_length=40, verbose_name=b'cid')),
                ('attachment', models.FileField(upload_to=booki.editor.models.uploadCoverTo, max_length=2500, verbose_name='filename')),
                ('filename', models.CharField(default=b'', max_length=250, verbose_name=b'file name')),
                ('title', models.CharField(max_length=250, verbose_name='Cover title')),
                ('width', models.IntegerField(verbose_name='Width', blank=True)),
                ('height', models.IntegerField(verbose_name='Height', blank=True)),
                ('unit', models.CharField(max_length=20, verbose_name='Unit', blank=True)),
                ('booksize', models.CharField(max_length=30, verbose_name='Booksize', blank=True)),
                ('is_book', models.BooleanField(default=False, verbose_name='Book cover')),
                ('is_ebook', models.BooleanField(default=False, verbose_name='E-book cover')),
                ('is_pdf', models.BooleanField(default=False, verbose_name='PDF cover')),
                ('cover_type', models.CharField(max_length=20, verbose_name='Cover type', blank=True)),
                ('creator', models.CharField(max_length=40, verbose_name='Cover', blank=True)),
                ('notes', models.TextField(verbose_name='notes')),
                ('approved', models.BooleanField(default=False, verbose_name='Approved')),
                ('created', models.DateTimeField(verbose_name='created')),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book', null=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('args', models.CharField(max_length=2500, verbose_name='args')),
                ('kind', models.SmallIntegerField(default=0, verbose_name='kind')),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookiGroup',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=300, verbose_name='name')),
                ('url_name', models.CharField(max_length=300, verbose_name='url name')),
                ('description', models.TextField(verbose_name='description')),
                ('created', models.DateTimeField(null=True, verbose_name='created')),
                ('members', models.ManyToManyField(related_name=b'members', verbose_name='members', to=settings.AUTH_USER_MODEL, blank=True)),
                ('owner', models.ForeignKey(verbose_name='owner', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Booktype group',
                'verbose_name_plural': 'Booktype groups',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookiPermission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('permission', models.SmallIntegerField(verbose_name='permission')),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book', null=True)),
                ('group', models.ForeignKey(verbose_name='group', to='editor.BookiGroup', null=True)),
                ('user', models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookNotes',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('notes', models.TextField(verbose_name='notes')),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book')),
            ],
            options={
                'verbose_name': 'Book note',
                'verbose_name_plural': 'Book notes',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookSetting',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=2500, verbose_name='name', db_index=True)),
                ('kind', models.SmallIntegerField(verbose_name='kind', choices=[(0, b'string'), (1, b'integer'), (2, b'text'), (3, b'date')])),
                ('value_string', models.CharField(max_length=2500, null=True, verbose_name='value string')),
                ('value_integer', models.IntegerField(null=True, verbose_name='value integer')),
                ('value_text', models.TextField(null=True, verbose_name='value text')),
                ('value_date', models.DateTimeField(null=True, verbose_name='value date')),
                ('book', models.ForeignKey(related_name=b'settings', verbose_name='book', to='editor.Book')),
            ],
            options={
                'verbose_name': 'Book setting',
                'verbose_name_plural': 'Book settings',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookStatus',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=30, verbose_name='name')),
                ('weight', models.SmallIntegerField(verbose_name='weight')),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book')),
            ],
            options={
                'verbose_name': 'Book status',
                'verbose_name_plural': 'Book status',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookToc',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=2500, verbose_name='name', blank=True)),
                ('weight', models.IntegerField(verbose_name='weight')),
                ('typeof', models.SmallIntegerField(verbose_name='typeof', choices=[(0, 'section name'), (1, 'chapter name'), (2, 'line')])),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book')),
            ],
            options={
                'verbose_name': 'Book TOC',
                'verbose_name_plural': 'Book TOCs',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BookVersion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('major', models.IntegerField(verbose_name='major')),
                ('minor', models.IntegerField(verbose_name='minor')),
                ('name', models.CharField(max_length=50, verbose_name='name', blank=True)),
                ('description', models.CharField(max_length=250, verbose_name='description', blank=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='created')),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Chapter',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('url_title', models.CharField(max_length=2500, verbose_name='url title')),
                ('title', models.CharField(max_length=2500, verbose_name='title')),
                ('created', models.DateTimeField(default=datetime.datetime.now, verbose_name='created')),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified', null=True)),
                ('revision', models.IntegerField(default=1, verbose_name='revision')),
                ('content', models.TextField(verbose_name='content')),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book')),
                ('status', models.ForeignKey(verbose_name='status', to='editor.BookStatus')),
                ('version', models.ForeignKey(verbose_name='version', to='editor.BookVersion')),
            ],
            options={
                'verbose_name': 'Chapter',
                'verbose_name_plural': 'Chapters',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChapterHistory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('content', models.TextField()),
                ('modified', models.DateTimeField(auto_now=True, verbose_name='modified')),
                ('revision', models.IntegerField(default=1, verbose_name='revision')),
                ('comment', models.CharField(max_length=2500, verbose_name='comment', blank=True)),
                ('chapter', models.ForeignKey(verbose_name='chapter', to='editor.Chapter')),
                ('user', models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Chapter history',
                'verbose_name_plural': 'Chapters history',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ChapterLock',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('type', models.IntegerField(default=2, choices=[(1, b'Lock everyone'), (2, b'Lock to people without permissions')])),
                ('created', models.DateTimeField(auto_now_add=True, verbose_name='created')),
                ('chapter', models.OneToOneField(related_name=b'lock', to='editor.Chapter')),
                ('user', models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ('created',),
                'verbose_name': 'Chapter Lock',
                'verbose_name_plural': 'Chapters Locks',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Info',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=2500, verbose_name='name', db_index=True)),
                ('kind', models.SmallIntegerField(verbose_name='kind', choices=[(0, b'string'), (1, b'integer'), (2, b'text'), (3, b'date')])),
                ('value_string', models.CharField(max_length=2500, null=True, verbose_name='value string')),
                ('value_integer', models.IntegerField(null=True, verbose_name='value integer')),
                ('value_text', models.TextField(null=True, verbose_name='value text')),
                ('value_date', models.DateTimeField(null=True, verbose_name='value date')),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book')),
            ],
            options={
                'verbose_name': 'Metadata',
                'verbose_name_plural': 'Metadata',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=50, verbose_name='name')),
                ('abbrevation', models.CharField(max_length=10, verbose_name='abbrevation')),
            ],
            options={
                'verbose_name': 'Language',
                'verbose_name_plural': 'Languages',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='License',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('abbrevation', models.CharField(max_length=30, verbose_name='abbrevation')),
                ('url', models.URLField(null=True, verbose_name='url', blank=True)),
            ],
            options={
                'verbose_name': 'License',
                'verbose_name_plural': 'Licenses',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PublishWizzard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('wizz_type', models.CharField(max_length=20, verbose_name='wizzard type')),
                ('wizz_options', models.TextField(default=b'', verbose_name='wizzard options')),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book', null=True)),
                ('user', models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Publish Wizzard',
                'verbose_name_plural': 'Publish Wizzard',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='publishwizzard',
            unique_together=set([('book', 'user', 'wizz_type')]),
        ),
        migrations.AddField(
            model_name='booktoc',
            name='chapter',
            field=models.ForeignKey(verbose_name='chapter', blank=True, to='editor.Chapter', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='booktoc',
            name='parent',
            field=models.ForeignKey(verbose_name='parent', blank=True, to='editor.BookToc', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='booktoc',
            name='version',
            field=models.ForeignKey(verbose_name='version', to='editor.BookVersion'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bookhistory',
            name='chapter',
            field=models.ForeignKey(verbose_name='chapter', to='editor.Chapter', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bookhistory',
            name='chapter_history',
            field=models.ForeignKey(verbose_name='chapter history', to='editor.ChapterHistory', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bookhistory',
            name='user',
            field=models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bookhistory',
            name='version',
            field=models.ForeignKey(verbose_name='version', to='editor.BookVersion', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bookcover',
            name='license',
            field=models.ForeignKey(verbose_name='license', to='editor.License', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bookcover',
            name='user',
            field=models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='group',
            field=models.ForeignKey(verbose_name='group', to='editor.BookiGroup', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='language',
            field=models.ForeignKey(verbose_name='language', to='editor.Language', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='license',
            field=models.ForeignKey(verbose_name='license', blank=True, to='editor.License', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='owner',
            field=models.ForeignKey(verbose_name='owner', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='status',
            field=models.ForeignKey(related_name=b'status', verbose_name='status', to='editor.BookStatus', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='book',
            name='version',
            field=models.ForeignKey(related_name=b'version', verbose_name='version', to='editor.BookVersion', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attributionexclude',
            name='book',
            field=models.ForeignKey(verbose_name='book', to='editor.Book', null=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attributionexclude',
            name='user',
            field=models.ForeignKey(verbose_name='user', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attachment',
            name='book',
            field=models.ForeignKey(verbose_name='book', to='editor.Book'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attachment',
            name='status',
            field=models.ForeignKey(verbose_name='status', to='editor.BookStatus'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attachment',
            name='version',
            field=models.ForeignKey(verbose_name='version', to='editor.BookVersion'),
            preserve_default=True,
        ),
    ]
