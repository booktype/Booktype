# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'EndpointConfig'
        db.create_table('messaging_endpointconfig', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('notification_filter', self.gf('django.db.models.fields.CharField')(max_length=2500)),
        ))
        db.send_create_signal('messaging', ['EndpointConfig'])

        # Adding field 'Endpoint.config'
        db.add_column('messaging_endpoint', 'config', self.gf('django.db.models.fields.related.OneToOneField')(to=orm['messaging.EndpointConfig'], unique=True, null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Deleting model 'EndpointConfig'
        db.delete_table('messaging_endpointconfig')

        # Deleting field 'Endpoint.config'
        db.delete_column('messaging_endpoint', 'config_id')


    models = {
        'messaging.endpoint': {
            'Meta': {'object_name': 'Endpoint'},
            'config': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['messaging.EndpointConfig']", 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'syntax': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '2500'})
        },
        'messaging.endpointconfig': {
            'Meta': {'object_name': 'EndpointConfig'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'notification_filter': ('django.db.models.fields.CharField', [], {'max_length': '2500'})
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
