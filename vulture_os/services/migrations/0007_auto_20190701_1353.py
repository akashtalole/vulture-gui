# Generated by Django 2.1.3 on 2019-07-01 13:53

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('services', '0006_auto_20190625_1517'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='blacklistwhitelist',
            name='frontend',
        ),
        migrations.DeleteModel(
            name='BlacklistWhitelist',
        ),
    ]
