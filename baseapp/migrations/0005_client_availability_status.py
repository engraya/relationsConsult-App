# Generated by Django 3.0.5 on 2023-09-05 07:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('baseapp', '0004_auto_20230905_0701'),
    ]

    operations = [
        migrations.AddField(
            model_name='client',
            name='availability_status',
            field=models.BooleanField(default=False),
        ),
    ]
