# Generated by Django 4.2.4 on 2023-12-04 21:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0012_alter_productioninfo_item_count'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='bars_scrap',
            field=models.IntegerField(default=0),
        ),
    ]
