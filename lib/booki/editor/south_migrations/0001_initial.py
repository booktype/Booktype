# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'License'
        db.create_table('editor_license', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('abbrevation', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('editor', ['License'])

        # Adding model 'Language'
        db.create_table('editor_language', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50)),
            ('abbrevation', self.gf('django.db.models.fields.CharField')(max_length=10)),
        ))
        db.send_create_signal('editor', ['Language'])

        # Adding model 'BookStatus'
        db.create_table('editor_bookstatus', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Book'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=30)),
            ('weight', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal('editor', ['BookStatus'])

        # Adding model 'BookNotes'
        db.create_table('editor_booknotes', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Book'])),
            ('notes', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('editor', ['BookNotes'])

        # Adding model 'BookiGroup'
        db.create_table('editor_bookigroup', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('url_name', self.gf('django.db.models.fields.CharField')(max_length=300)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('editor', ['BookiGroup'])

        # Adding M2M table for field members on 'BookiGroup'
        db.create_table('editor_bookigroup_members', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bookigroup', models.ForeignKey(orm['editor.bookigroup'], null=False)),
            ('user', models.ForeignKey(orm['auth.user'], null=False))
        ))
        db.create_unique('editor_bookigroup_members', ['bookigroup_id', 'user_id'])

        # Adding model 'Book'
        db.create_table('editor_book', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('url_title', self.gf('django.db.models.fields.CharField')(unique=True, max_length=2500)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=2500)),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(related_name='status', null=True, to=orm['editor.BookStatus'])),
            ('language', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Language'], null=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(related_name='version', null=True, to=orm['editor.BookVersion'])),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.BookiGroup'], null=True)),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('license', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.License'], null=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('published', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('editor', ['Book'])

        # Adding model 'BookHistory'
        db.create_table('editor_bookhistory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Book'])),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.BookVersion'], null=True)),
            ('chapter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Chapter'], null=True)),
            ('chapter_history', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.ChapterHistory'], null=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('args', self.gf('django.db.models.fields.CharField')(max_length=2500)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('kind', self.gf('django.db.models.fields.SmallIntegerField')(default=0)),
        ))
        db.send_create_signal('editor', ['BookHistory'])

        # Adding model 'Info'
        db.create_table('editor_info', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Book'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=2500, db_index=True)),
            ('kind', self.gf('django.db.models.fields.SmallIntegerField')()),
            ('value_string', self.gf('django.db.models.fields.CharField')(max_length=2500, null=True)),
            ('value_integer', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('value_text', self.gf('django.db.models.fields.TextField')(null=True)),
            ('value_date', self.gf('django.db.models.fields.DateTimeField')(null=True)),
        ))
        db.send_create_signal('editor', ['Info'])

        # Adding model 'BookVersion'
        db.create_table('editor_bookversion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Book'])),
            ('major', self.gf('django.db.models.fields.IntegerField')()),
            ('minor', self.gf('django.db.models.fields.IntegerField')()),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=250, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('editor', ['BookVersion'])

        # Adding model 'Chapter'
        db.create_table('editor_chapter', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.BookVersion'])),
            ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Book'])),
            ('url_title', self.gf('django.db.models.fields.CharField')(max_length=2500)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=2500)),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.BookStatus'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, blank=True)),
            ('revision', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('content', self.gf('django.db.models.fields.TextField')()),
        ))
        db.send_create_signal('editor', ['Chapter'])

        # Adding model 'ChapterHistory'
        db.create_table('editor_chapterhistory', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('chapter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Chapter'])),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('revision', self.gf('django.db.models.fields.IntegerField')(default=1)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=2500, blank=True)),
        ))
        db.send_create_signal('editor', ['ChapterHistory'])

        # Adding model 'Attachment'
        db.create_table('editor_attachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.BookVersion'])),
            ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Book'])),
            ('attachment', self.gf('django.db.models.fields.files.FileField')(max_length=2500)),
            ('status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.BookStatus'])),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('editor', ['Attachment'])

        # Adding model 'BookToc'
        db.create_table('editor_booktoc', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('version', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.BookVersion'])),
            ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Book'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=2500, blank=True)),
            ('chapter', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Chapter'], null=True, blank=True)),
            ('weight', self.gf('django.db.models.fields.IntegerField')()),
            ('typeof', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal('editor', ['BookToc'])

        # Adding model 'BookiPermission'
        db.create_table('editor_bookipermission', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'])),
            ('book', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.Book'], null=True)),
            ('group', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['editor.BookiGroup'], null=True)),
            ('permission', self.gf('django.db.models.fields.SmallIntegerField')()),
        ))
        db.send_create_signal('editor', ['BookiPermission'])


    def backwards(self, orm):
        
        # Deleting model 'License'
        db.delete_table('editor_license')

        # Deleting model 'Language'
        db.delete_table('editor_language')

        # Deleting model 'BookStatus'
        db.delete_table('editor_bookstatus')

        # Deleting model 'BookNotes'
        db.delete_table('editor_booknotes')

        # Deleting model 'BookiGroup'
        db.delete_table('editor_bookigroup')

        # Removing M2M table for field members on 'BookiGroup'
        db.delete_table('editor_bookigroup_members')

        # Deleting model 'Book'
        db.delete_table('editor_book')

        # Deleting model 'BookHistory'
        db.delete_table('editor_bookhistory')

        # Deleting model 'Info'
        db.delete_table('editor_info')

        # Deleting model 'BookVersion'
        db.delete_table('editor_bookversion')

        # Deleting model 'Chapter'
        db.delete_table('editor_chapter')

        # Deleting model 'ChapterHistory'
        db.delete_table('editor_chapterhistory')

        # Deleting model 'Attachment'
        db.delete_table('editor_attachment')

        # Deleting model 'BookToc'
        db.delete_table('editor_booktoc')

        # Deleting model 'BookiPermission'
        db.delete_table('editor_bookipermission')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'editor.attachment': {
            'Meta': {'object_name': 'Attachment'},
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '2500'}),
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Book']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.BookStatus']"}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.BookVersion']"})
        },
        'editor.book': {
            'Meta': {'object_name': 'Book'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.BookiGroup']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Language']", 'null': 'True'}),
            'license': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.License']", 'null': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'published': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'status'", 'null': 'True', 'to': "orm['editor.BookStatus']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'url_title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2500'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'version'", 'null': 'True', 'to': "orm['editor.BookVersion']"})
        },
        'editor.bookhistory': {
            'Meta': {'object_name': 'BookHistory'},
            'args': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Book']"}),
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Chapter']", 'null': 'True'}),
            'chapter_history': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.ChapterHistory']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.SmallIntegerField', [], {'default': '0'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.BookVersion']", 'null': 'True'})
        },
        'editor.bookigroup': {
            'Meta': {'object_name': 'BookiGroup'},
            'created': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'members': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'members'", 'blank': 'True', 'to': "orm['auth.User']"}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '300'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"}),
            'url_name': ('django.db.models.fields.CharField', [], {'max_length': '300'})
        },
        'editor.bookipermission': {
            'Meta': {'object_name': 'BookiPermission'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Book']", 'null': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.BookiGroup']", 'null': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'permission': ('django.db.models.fields.SmallIntegerField', [], {}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'editor.booknotes': {
            'Meta': {'object_name': 'BookNotes'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Book']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notes': ('django.db.models.fields.TextField', [], {})
        },
        'editor.bookstatus': {
            'Meta': {'object_name': 'BookStatus'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Book']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'weight': ('django.db.models.fields.SmallIntegerField', [], {})
        },
        'editor.booktoc': {
            'Meta': {'object_name': 'BookToc'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Book']"}),
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Chapter']", 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'blank': 'True'}),
            'typeof': ('django.db.models.fields.SmallIntegerField', [], {}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.BookVersion']"}),
            'weight': ('django.db.models.fields.IntegerField', [], {})
        },
        'editor.bookversion': {
            'Meta': {'object_name': 'BookVersion'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Book']"}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '250', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'major': ('django.db.models.fields.IntegerField', [], {}),
            'minor': ('django.db.models.fields.IntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'editor.chapter': {
            'Meta': {'object_name': 'Chapter'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Book']"}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'blank': 'True'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.BookStatus']"}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'url_title': ('django.db.models.fields.CharField', [], {'max_length': '2500'}),
            'version': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.BookVersion']"})
        },
        'editor.chapterhistory': {
            'Meta': {'object_name': 'ChapterHistory'},
            'chapter': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Chapter']"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'blank': 'True'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'revision': ('django.db.models.fields.IntegerField', [], {'default': '1'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']"})
        },
        'editor.info': {
            'Meta': {'object_name': 'Info'},
            'book': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['editor.Book']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.SmallIntegerField', [], {}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'db_index': 'True'}),
            'value_date': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'value_integer': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'value_string': ('django.db.models.fields.CharField', [], {'max_length': '2500', 'null': 'True'}),
            'value_text': ('django.db.models.fields.TextField', [], {'null': 'True'})
        },
        'editor.language': {
            'Meta': {'object_name': 'Language'},
            'abbrevation': ('django.db.models.fields.CharField', [], {'max_length': '10'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'editor.license': {
            'Meta': {'object_name': 'License'},
            'abbrevation': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['editor']
