# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('editor', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BookRole',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('book', models.ForeignKey(verbose_name='book', to='editor.Book')),
                ('members', models.ManyToManyField(related_name='roles', null=True, verbose_name='users', to=settings.AUTH_USER_MODEL, blank=True)),
            ],
            options={
                'verbose_name': 'Book Role',
                'verbose_name_plural': 'Book Roles',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Permission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('app_name', models.CharField(max_length=40, verbose_name='app name')),
                ('name', models.CharField(max_length=60, verbose_name='name')),
                ('description', models.CharField(max_length=255, verbose_name='description')),
            ],
            options={
                'verbose_name': 'Permission',
                'verbose_name_plural': 'Permissions',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=60, verbose_name='name')),
                ('description', models.CharField(max_length=255, verbose_name='description', blank=True)),
                ('permissions', models.ManyToManyField(to='core.Permission', null=True, verbose_name='permissions', blank=True)),
            ],
            options={
                'verbose_name': 'Role',
                'verbose_name_plural': 'Roles',
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='permission',
            unique_together=set([('app_name', 'name')]),
        ),
        migrations.AddField(
            model_name='bookrole',
            name='role',
            field=models.ForeignKey(verbose_name='role', to='core.Role'),
            preserve_default=True,
        ),
    ]
