# -*- coding: utf-8 -*-
# Generated by Django 1.11.18 on 2019-03-08 19:29
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('signup', '0004_0_2_6'),
    ]

    operations = [
        migrations.AddField(
            model_name='contact',
            name='mfa_backend',
            field=models.PositiveSmallIntegerField(choices=[(0, 'password only'), (1, 'send one-time authentication code through email')], default=0, help_text='Backend to use for multi-factor authentication'),
        ),
        migrations.AddField(
            model_name='contact',
            name='mfa_nb_attempts',
            field=models.IntegerField(default=0, verbose_name='Number of attempts to pass the MFA code'),
        ),
        migrations.AddField(
            model_name='contact',
            name='mfa_priv_key',
            field=models.IntegerField(null=True, verbose_name='One-time authentication code'),
        ),
    ]