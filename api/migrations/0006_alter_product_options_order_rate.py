# Generated by Django 4.2.4 on 2023-11-25 03:16

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_product_rate'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='product',
            options={'ordering': ['part_num']},
        ),
        migrations.AddField(
            model_name='order',
            name='rate',
            field=models.FloatField(null=True),
        ),
    ]
