# Generated by Django 4.2.4 on 2023-12-07 21:34

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0022_alter_shift_rate_per_hour'),
    ]

    operations = [
        migrations.AddField(
            model_name='timelinebar',
            name='product',
            field=models.CharField(max_length=30, null=True),
        ),
    ]
