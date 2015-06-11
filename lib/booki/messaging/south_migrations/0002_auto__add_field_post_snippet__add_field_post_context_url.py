# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding field 'Post.snippet'
        db.add_column('messaging_post', 'snippet', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)

        # Adding field 'Post.context_url'
        db.add_column('messaging_post', 'context_url', self.gf('django.db.models.fields.TextField')(default=''), keep_default=False)


    def backwards(self, orm):
        
        # Deleting field 'Post.snippet'
        db.delete_column('messaging_post', 'snippet')

        # Deleting field 'Post.context_url'
        db.delete_column('messaging_post', 'context_url')


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
            'context_url': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'sender': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['messaging.Endpoint']"}),
            'snippet': ('django.db.models.fields.TextField', [], {}),
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
