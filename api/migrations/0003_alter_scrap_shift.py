# Generated by Django 4.2.4 on 2023-10-24 04:32

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_scrap_shift'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scrap',
            name='shift',
            field=models.ForeignKey(default='W1202310231', on_delete=django.db.models.deletion.CASCADE, related_name='scrap', to='api.shift'),
        ),
    ]
