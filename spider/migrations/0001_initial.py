# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-07-05 10:11
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileLinks',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('parent', models.CharField(default='', max_length=255)),
                ('url', models.CharField(max_length=255)),
                ('hash', models.CharField(max_length=32)),
                ('type', models.CharField(default='', max_length=16)),
                ('data_update', models.DateTimeField(auto_now=True, null=True)),
            ],
        ),
        migrations.CreateModel(
            name='Scans',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('data_finish', models.DateTimeField(blank=True, default=None, null=True)),
                ('deep_level', models.IntegerField(default=9)),
                ('celery_task_id', models.CharField(default='', max_length=36)),
                ('count_vised_pages', models.IntegerField(default=0)),
                ('count_file_links_total', models.IntegerField(default=0)),
                ('count_file_links_new', models.IntegerField(default=0)),
                ('is_deleted', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='Websites',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('url', models.CharField(max_length=255, unique=True)),
                ('hash_domain', models.CharField(max_length=32, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='scans',
            name='website',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spider.Websites'),
        ),
        migrations.AddField(
            model_name='filelinks',
            name='scan',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='spider.Scans'),
        ),
        migrations.AddField(
            model_name='filelinks',
            name='website',
            field=models.ForeignKey(default=0, null=True, on_delete=django.db.models.deletion.CASCADE, to='spider.Websites'),
        ),
    ]
