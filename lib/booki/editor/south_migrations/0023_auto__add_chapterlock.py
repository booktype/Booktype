# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'ChapterLock'
        db.create_table(u'editor_chapterlock', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('chapter', self.gf('django.db.models.fields.related.OneToOneField')(related_name='lock', unique=True, to=orm['editor.Chapter'])),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('type', self.gf('django.db.models.fields.IntegerField')(default=2)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
        ))
        db.send_create_signal(u'editor', ['ChapterLock'])


    def backwards(self, orm):
        # Deleting model 'ChapterLock'
        db.delete_table(u'editor_chapterlock')


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
        u'editor.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '2500'}),
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.BookStatus']"}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.BookVersion']"})
        },
        u'editor.attributionexclude': {
            'Meta': {'object_name': 'AttributionExclude'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
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
        u'editor.bookcover': {
            'Meta': {'object_name': 'BookCover'},
            'approved': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '2500'}),
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']", 'null': 'True'}),
            'booksize': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'cid': ('django.db.models.fields.CharField', [], {'default': "''", 'unique': 'True', 'max_length': '40'}),
            'cover_type': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {}),
            'creator': ('django.db.models.fields.CharField', [], {'max_length': '40', 'blank': 'True'}),
            'filename': ('django.db.models.fields.CharField', [], {'default': "''", 'max_length': '250'}),
            'height': ('django.db.models.fields.IntegerField', [], {'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_book': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_ebook': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_pdf': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'license': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.License']", 'null': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '250'}),
            'unit': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'width': ('django.db.models.fields.IntegerField', [], {'blank': 'True'})
        },
        u'editor.bookhistory': {
            'Meta': {'object_name': 'BookHistory'},
            'args': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']"}),
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Chapter']", 'null': 'True'}),
            'chapter_history': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.ChapterHistory']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.BookVersion']", 'null': 'True'})
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
        u'editor.bookipermission': {
            'Meta': {'object_name': 'BookiPermission'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']", 'null': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.BookiGroup']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permission': ('django.db.models.fields.SmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'editor.booknotes': {
            'Meta': {'object_name': 'BookNotes'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {})
        },
        u'editor.booksetting': {
            'Meta': {'object_name': 'BookSetting'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'settings'", 'to': u"orm['editor.Book']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.SmallIntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'db_index': 'True'}),
            'value_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'value_integer': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'value_string': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'null': 'True'}),
            'value_text': ('django.db.models.fields.TextField', [], {'null': 'True'})
        },
        u'editor.bookstatus': {
            'Meta': {'object_name': 'BookStatus'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'weight': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        u'editor.booktoc': {
            'Meta': {'object_name': 'BookToc'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']"}),
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Chapter']", 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.BookToc']", 'null': 'True', 'blank': 'True'}),
            'typeof': ('django.db.models.fields.SmallIntegerField', [], {}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.BookVersion']"}),
            'weight': ('django.db.models.fields.IntegerField', [], {})
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
        u'editor.chapter': {
            'Meta': {'object_name': 'Chapter'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.BookStatus']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'url_title': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.BookVersion']"})
        },
        u'editor.chapterhistory': {
            'Meta': {'object_name': 'ChapterHistory'},
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Chapter']"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'editor.chapterlock': {
            'Meta': {'ordering': "('created',)", 'object_name': 'ChapterLock'},
            'chapter': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'lock'", 'unique': 'True', 'to': u"orm['editor.Chapter']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'type': ('django.db.models.fields.IntegerField', [], {'default': '2'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"})
        },
        u'editor.info': {
            'Meta': {'object_name': 'Info'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.SmallIntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'db_index': 'True'}),
            'value_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'value_integer': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'value_string': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'null': 'True'}),
            'value_text': ('django.db.models.fields.TextField', [], {'null': 'True'})
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
        u'editor.publishwizzard': {
            'Meta': {'unique_together': "(('book', 'user', 'wizz_type'),)", 'object_name': 'PublishWizzard'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['editor.Book']", 'null': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['auth.User']"}),
            'wizz_options': ('django.db.models.fields.TextField', [], {'default': "''"}),
            'wizz_type': ('django.db.models.fields.CharField', [], {'max_length': '20'})
        }
    }

    complete_apps = ['editor']