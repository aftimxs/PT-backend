# Generated by Django 4.2.4 on 2023-11-25 21:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0007_timelinebar_loss'),
    ]

    operations = [
        migrations.AlterField(
            model_name='timelinebar',
            name='loss',
            field=models.FloatField(default=0),
        ),
    ]