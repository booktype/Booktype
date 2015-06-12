# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'BookExport'
        db.create_table(u'export_bookexport', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.BookVersion'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('task_id', self.gf('django.db.models.fields.CharField')(unique=True, max_length=64, db_index=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('published', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
        ))
        db.send_create_signal(u'export', ['BookExport'])

        # Adding model 'ExportFile'
        db.create_table(u'export_exportfile', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('export', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['export.BookExport'])),
            ('typeof', self.gf('django.db.models.fields.CharField')(max_length=20)),
            ('filesize', self.gf('django.db.models.fields.IntegerField')(default=0, null=True)),
            ('pages', self.gf('django.db.models.fields.IntegerField')(default=0, null=True)),
            ('status', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('filename', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal(u'export', ['ExportFile'])

        # Adding model 'ExportComment'
        db.create_table(u'export_exportcomment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('export', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['export.BookExport'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('content', self.gf('django.db.models.fields.TextField')(default='')),
        ))
        db.send_create_signal(u'export', ['ExportComment'])


    def backwards(self, orm):
        # Deleting model 'BookExport'
        db.delete_table(u'export_bookexport')

        # Deleting model 'ExportFile'
        db.delete_table(u'export_exportfile')

        # Deleting model 'ExportComment'
        db.delete_table(u'export_exportcomment')


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'editor.book': {
            'Meta': {'object_name': 'Book'},
            'cover': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.BookiGroup']", 'null': 'True'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Language']", 'null': 'True'}),
            'license': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.License']", 'null': 'True', 'blank': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'permission': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'status'", 'null': 'True', 'to': u"orm['editor.BookStatus']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'url_title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2500'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'version'", 'null': 'True', 'to': u"orm['editor.BookVersion']"})
        },
        u'editor.bookigroup': {
            'Meta': {'object_name': 'BookiGroup'},
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'members'", 'blank': 'True', 'to': u"orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'url_name': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        u'editor.bookstatus': {
            'Meta': {'object_name': 'BookStatus'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'weight': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'editor.bookversion': {
            'Meta': {'object_name': 'BookVersion'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'major': ('django.db.models.fields.IntegerField', [], {}),
            'minor': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        u'editor.language': {
            'Meta': {'object_name': 'Language'},
            'abbrevation': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'editor.license': {
            'Meta': {'object_name': 'License'},
            'abbrevation': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        },
        u'export.bookexport': {
            'Meta': {'object_name': 'BookExport'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'published': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'task_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64', 'db_index': 'True'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.BookVersion']"})
        },
        u'export.exportcomment': {
            'Meta': {'object_name': 'ExportComment'},
            'content': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'export': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['export.BookExport']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'export.exportfile': {
            'Meta': {'object_name': 'ExportFile'},
            'description': ('django.db.models.fields.TextField', [], {}),
            'export': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['export.BookExport']"}),
            'filename': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'filesize': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pages': ('django.db.models.fields.IntegerField', [], {'default': '0', 'null': 'True'}),
            'status': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'typeof': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['export']