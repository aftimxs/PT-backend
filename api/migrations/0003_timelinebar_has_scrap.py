# Generated by Django 4.2.4 on 2023-11-12 03:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_alter_shift_options_shift_total_parts_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='timelinebar',
            name='has_scrap',
            field=models.BooleanField(default=False),
        ),
    ]