# Generated by Django 4.2.4 on 2023-12-21 17:00

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0037_order_end_date_alter_order_end_alter_order_start_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='order',
            name='end_date',
            field=models.DateTimeField(null=True),
        ),
        migrations.AlterField(
            model_name='productioninfo',
            name='date',
            field=models.DateField(),
        ),
        migrations.AlterField(
            model_name='timelinebar',
            name='date',
            field=models.DateField(),
        ),
    ]