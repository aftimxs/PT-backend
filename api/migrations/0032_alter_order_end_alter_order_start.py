# Generated by Django 4.2.4 on 2023-12-19 19:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0031_alter_order_end_alter_order_start'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='end',
            field=models.TimeField(null=True),
        ),
        migrations.AlterField(
            model_name='order',
            name='start',
            field=models.TimeField(null=True),
        ),
    ]
