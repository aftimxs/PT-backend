# Generated by Django 4.2.4 on 2023-11-26 23:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0010_remove_timelinebar_time_length'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timelinebar',
            name='parts_made',
            field=models.FloatField(),
        ),
    ]
