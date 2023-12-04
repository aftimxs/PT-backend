# Generated by Django 4.2.4 on 2023-12-04 21:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0013_shift_bars_scrap'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='loss_slow',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='shift',
            name='loss_stopped',
            field=models.FloatField(default=0),
        ),
        migrations.AddField(
            model_name='shift',
            name='minutes_slow',
            field=models.IntegerField(default=0),
        ),
        migrations.AddField(
            model_name='shift',
            name='minutes_stopped',
            field=models.IntegerField(default=0),
        ),
    ]
