# Generated by Django 2.1.3 on 2019-07-16 15:17

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('darwin', '0004_blacklistwhitelist'),
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
