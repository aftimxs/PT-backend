# Generated by Django 4.2.4 on 2023-10-23 20:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_barcomments'),
    ]

    operations = [
        migrations.RenameField(
            model_name='scrap',
            old_name='timeline_bar',
            new_name='bar',
        ),
        migrations.RemoveField(
            model_name='scrap',
            name='minute',
        ),
        migrations.RemoveField(
            model_name='scrap',
            name='shift',
        ),
    ]
