# -*- coding: utf-8 -*-
# Generated by Django 1.11.8 on 2018-01-30 13:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('club_games', '0002_auto_20180127_0500'),
    ]

    operations = [
        migrations.AddField(
            model_name='clubrating',
            name='open_hand',
            field=models.DecimalField(decimal_places=2, default=0, max_digits=10),
            preserve_default=False,
        ),
    ]
