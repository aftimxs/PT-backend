# Generated by Django 4.2.4 on 2023-12-06 22:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0019_order_end_order_made_order_scrap_order_start_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='shift',
            name='items',
            field=models.CharField(max_length=200, null=True),
        ),
        migrations.AddField(
            model_name='shift',
            name='quantity',
            field=models.IntegerField(default=0),
        ),
    ]
