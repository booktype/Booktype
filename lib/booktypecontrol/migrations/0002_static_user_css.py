# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

class Migration(DataMigration):
    
    def forwards(self, orm):
        "Write your forwards methods here."
        from django.conf import settings
        try:
            f = open('%s/css/_user.css' % settings.STATIC_ROOT, 'w')
            f.write(' ')
            f.close()
        except IOError:
            raise RuntimeError("Can not create the file.")
                
    def backwards(self, orm):
        "Write your backwards methods here."
    
    models = {
        
    }
    
    complete_apps = ['booktypecontrol']
