# Generated by Django 4.2.4 on 2023-10-24 04:33

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0003_alter_scrap_shift'),
    ]

    operations = [
        migrations.AlterField(
            model_name='scrap',
            name='shift',
            field=models.ForeignKey(default=None, on_delete=django.db.models.deletion.CASCADE, related_name='scrap', to='api.shift'),
        ),
    ]
