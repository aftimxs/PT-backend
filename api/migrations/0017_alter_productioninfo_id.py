# Generated by Django 4.2.4 on 2023-12-05 17:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0016_alter_productioninfo_id_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productioninfo',
            name='id',
            field=models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID'),
        ),
    ]
