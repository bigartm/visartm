# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-01-26 11:15
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('models', '0023_documentintopic_weight'),
    ]

    operations = [
        migrations.RenameField(
            model_name='topic',
            old_name='id_model',
            new_name='index_id',
        ),
    ]
