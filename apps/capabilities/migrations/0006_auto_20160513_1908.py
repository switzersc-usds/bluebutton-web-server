# -*- coding: utf-8 -*-
# Generated by Django 1.9.5 on 2016-05-13 19:08
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('capabilities', '0005_auto_20160330_1629'),
    ]

    operations = [
        migrations.AlterField(
            model_name='protectedcapability',
            name='description',
            field=models.TextField(blank=True, default='', max_length=10240),
        ),
        migrations.AlterField(
            model_name='protectedcapability',
            name='title',
            field=models.CharField(default='', max_length=256, unique=True),
        ),
    ]