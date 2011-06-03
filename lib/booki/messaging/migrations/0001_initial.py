# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Post'
        db.create_table('messaging_post', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('sender', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['messaging.Endpoint'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('attachment', self.gf('django.db.models.fields.files.FileField')(max_length=2500)),
        ))
        db.send_create_signal('messaging', ['Post'])

        # Adding model 'PostAppearance'
        db.create_table('messaging_postappearance', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('post', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['messaging.Post'])),
            ('timestamp', self.gf('django.db.models.fields.DateTimeField')()),
            ('endpoint', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['messaging.Endpoint'])),
        ))
        db.send_create_signal('messaging', ['PostAppearance'])

        # Adding model 'Endpoint'
        db.create_table('messaging_endpoint', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('syntax', self.gf('django.db.models.fields.CharField')(unique=True, max_length=2500)),
        ))
        db.send_create_signal('messaging', ['Endpoint'])

        # Adding model 'Following'
        db.create_table('messaging_following', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('follower', self.gf('django.db.models.fields.related.ForeignKey')(related_name='follower', to=orm['messaging.Endpoint'])),
            ('target', self.gf('django.db.models.fields.related.ForeignKey')(related_name='target', to=orm['messaging.Endpoint'])),
        ))
        db.send_create_signal('messaging', ['Following'])


    def backwards(self, orm):
        
        # Deleting model 'Post'
        db.delete_table('messaging_post')

        # Deleting model 'PostAppearance'
        db.delete_table('messaging_postappearance')

        # Deleting model 'Endpoint'
        db.delete_table('messaging_endpoint')

        # Deleting model 'Following'
        db.delete_table('messaging_following')


    models = {
        'messaging.endpoint': {
            'Meta': {'object_name': 'Endpoint'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'syntax': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2500'})
        },
        'messaging.following': {
            'Meta': {'object_name': 'Following'},
            'follower': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'follower'", 'to': "orm['messaging.Endpoint']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'target': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'target'", 'to': "orm['messaging.Endpoint']"})
        },
        'messaging.post': {
            'Meta': {'object_name': 'Post'},
            'attachment': ('django.db.models.fields.files.FileField', [], {'max_length': '2500'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['messaging.Endpoint']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        'messaging.postappearance': {
            'Meta': {'object_name': 'PostAppearance'},
            'endpoint': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['messaging.Endpoint']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['messaging.Post']"}),
            'timestamp': ('django.db.models.fields.DateTimeField', [], {})
        }
    }

    complete_apps = ['messaging']
