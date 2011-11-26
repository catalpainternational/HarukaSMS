# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'ForwardingRule'
        db.create_table('groups_forwardingrule', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('keyword', self.gf('django.db.models.fields.CharField')(max_length=160)),
            ('source', self.gf('django.db.models.fields.related.ForeignKey')(related_name='source_rules', to=orm['groups.Group'])),
            ('dest', self.gf('django.db.models.fields.related.ForeignKey')(related_name='dest_rules', to=orm['groups.Group'])),
        ))
        db.send_create_signal('groups', ['ForwardingRule'])


    def backwards(self, orm):
        
        # Deleting model 'ForwardingRule'
        db.delete_table('groups_forwardingrule')


    models = {
        'groups.forwardingrule': {
            'Meta': {'object_name': 'ForwardingRule'},
            'dest': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'dest_rules'", 'to': "orm['groups.Group']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keyword': ('django.db.models.fields.CharField', [], {'max_length': '160'}),
            'source': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'source_rules'", 'to': "orm['groups.Group']"})
        },
        'groups.group': {
            'Meta': {'object_name': 'Group'},
            'contacts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'groups'", 'blank': 'True', 'to': "orm['rapidsms.Contact']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '64'})
        },
        'rapidsms.contact': {
            'Meta': {'object_name': 'Contact'},
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'language': ('django.db.models.fields.CharField', [], {'max_length': '6', 'blank': 'True'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'phone': ('django.db.models.fields.CharField', [], {'max_length': '32', 'blank': 'True'}),
            'pin': ('django.db.models.fields.CharField', [], {'max_length': '20', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '64', 'blank': 'True'})
        }
    }

    complete_apps = ['groups']
