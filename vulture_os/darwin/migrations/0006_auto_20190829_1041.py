# Generated by Django 2.1.3 on 2019-08-29 10:41

import bson.objectid
from django.db import migrations, models
import django.db.models.deletion
import djongo.models.fields
from toolkit.mongodb.mongo_base import MongoBase

def update_conf_path(apps, schema_editor):
    FilterPolicy = apps.get_model('darwin', 'FilterPolicy')

    filters = FilterPolicy.objects.all()

    for filter in filters:
        filter.conf_path = "/home/darwin/conf/f{name}/f{name}_{id}.conf".format(
            name=filter.policy.name,
            id=filter.policy.id
        )
        filter.save()


def remove_session_and_logs_filters(apps, schema_editor):
    DarwinFilter = apps.get_model('darwin', 'DarwinFilter')
    FilterPolicy = apps.get_model('darwin', 'FilterPolicy')

    # Manually set config attribute, due to a migration bug
    m = MongoBase()
    m.connect_primary()
    coll = m.db['vulture']['darwin_filterpolicy']
    coll.update_many({}, {"$set": {"config": {}}})

    for filter_obj in DarwinFilter.objects.filter(name__in=['session', 'logs']):
        FilterPolicy.objects.filter(filter=filter_obj).delete()


def initial_access_control(apps, schema_editor):
    AccessControl = apps.get_model('darwin', 'AccessControl')

    acls = [
        {
            "enabled": False,
            "name": "Example_Source_IP_Verification",
            "rules": [
                {
                    "pk": "2hd780o",
                    "lines": [
                        {
                            "acl_name": "8hdk79h",
                            "criterion": "src",
                            "criterion_name": "",
                            "converter": "ip",
                            "dns": True,
                            "case": False,
                            "operator": "",
                            "pattern": "192.168.1.1"
                        },
                        {
                            "acl_name": "8hdk79i",
                            "criterion": "method",
                            "criterion_name": "",
                            "converter": "str",
                            "dns": False,
                            "case": False,
                            "operator": "",
                            "pattern": "GET"
                        }
                    ]
                }
            ]
        },
        {
            "enabled": False,
            "name": "Example_User_Agent_Verification",
            "rules": [
                {
                    "pk": "2hd780a",
                    "lines": [
                        {
                            "acl_name": "8hdk79p",
                            "criterion": "hdr",
                            "criterion_name": "User-Agent",
                            "converter": "sub",
                            "dns": False,
                            "case": False,
                            "operator": "",
                            "pattern": "Firefox"
                        }
                    ]
                },
                {
                    "pk": "2hd780q",
                    "lines": [
                        {
                            "acl_name": "9hdk79h",
                            "criterion": "hdr",
                            "criterion_name": "User-Agent",
                            "converter": "sub",
                            "dns": False,
                            "case": False,
                            "operator": "",
                            "pattern": "Chrome"
                        }
                    ]
                }
            ]
        }
    ]

    for acl in acls:
        print(acl)
        AccessControl.objects.create(
            name=acl['name'],
            enabled=acl['enabled'],
            rules=acl['rules']
        )


class Migration(migrations.Migration):

    dependencies = [
        ('darwin', '0005_auto_20190716_1517'),
    ]

    operations = [
        migrations.CreateModel(
            name='AccessControl',
            fields=[
                ('_id', djongo.models.fields.ObjectIdField(auto_created=True, default=bson.objectid.ObjectId, primary_key=True, serialize=False)),
                ('name', models.SlugField(help_text='Friendly name', max_length=255, unique=True, verbose_name='Friendly name')),
                ('enabled', models.BooleanField(default=True)),
                ('acls', models.TextField(default='')),
                ('rules', djongo.models.fields.ListField(default=[])),
            ],
        ),
        migrations.RunPython(initial_access_control),
        migrations.CreateModel(
            name='DefenderPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(default='Default defender policy', unique=True)),
                ('request_body_limit', models.PositiveIntegerField(default=8388608)),
                ('enable_libinjection_sql', models.BooleanField(default=True)),
                ('enable_libinjection_xss', models.BooleanField(default=True)),
                ('defender_ruleset', models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='darwin.DefenderRuleset')),
            ],
        ),
        migrations.CreateModel(
            name='DefenderProcessRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_id', models.TextField()),
                ('expiration_date', models.DateTimeField(auto_now_add=True)),
                ('rule_id', models.IntegerField()),
                ('rule_key', models.TextField(default='')),
                ('data', djongo.models.fields.DictField(default={})),
            ],
        ),
        migrations.CreateModel(
            name='DefenderProcessRuleJob',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('job_id', models.TextField(unique=True)),
                ('is_done', models.BooleanField(default=False)),
                ('expiration_date', models.DateTimeField(auto_now_add=True)),
            ],
        ),
        migrations.CreateModel(
            name='InspectionPolicy',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(default='Inspection_policy_name', help_text='Friendly name for the inspection policy', unique=True)),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('techno', models.TextField(choices=[('yara', 'yara')], default='yara', help_text='Technology used to inspect')),
                ('description', models.TextField(default='', help_text='Give your policy a description')),
                ('compilable', models.TextField(default='UNKNOWN')),
                ('compile_status', models.TextField(default='', help_text="yara compilation's result of this policy")),
            ],
        ),
        migrations.CreateModel(
            name='InspectionRule',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.TextField(default='Rule_name', help_text='Friendly name for the inspection rule')),
                ('last_update', models.DateTimeField(auto_now=True)),
                ('techno', models.TextField(choices=[('yara', 'yara')], default='yara', help_text='Technology used to inspect')),
                ('category', models.TextField(default='', help_text='Category of the rule')),
                ('source', models.TextField(default='custom', help_text='Source of the rule')),
                ('content', models.TextField(default='', help_text='Content of the rule')),
            ],
        ),
        migrations.RemoveField(
            model_name='darwinfilter',
            name='conf_path',
        ),
        migrations.RemoveField(
            model_name='darwinpolicy',
            name='defender_ruleset',
        ),
        migrations.AddField(
            model_name='darwinfilter',
            name='is_internal',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='filterpolicy',
            name='conf_path',
            field=models.TextField(default=''),
            preserve_default=False,
        ),
        migrations.RunPython(update_conf_path),
        migrations.AddField(
            model_name='filterpolicy',
            name='config',
            field=djongo.models.fields.DictField(default={}),
        ),
        migrations.AddField(
            model_name='filterpolicy',
            name='mmdarwin_enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='filterpolicy',
            name='mmdarwin_parameters',
            field=djongo.models.fields.ListField(default=[]),
        ),
        migrations.AddField(
            model_name='filterpolicy',
            name='next_filter',
            field=models.ForeignKey(default=None, null=True, on_delete=django.db.models.deletion.SET_NULL, to='darwin.FilterPolicy'),
        ),
        migrations.AddField(
            model_name='filterpolicy',
            name='output',
            field=models.TextField(choices=[('NONE', 'Do not send any data to next filter'), ('LOG', 'Send filters alerts to next filter'), ('RAW', 'Send initial body to next filter'), ('PARSED', 'Send parsed body to next filter')], default='NONE'),
        ),
        migrations.AlterField(
            model_name='filterpolicy',
            name='enabled',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='filterpolicy',
            name='threshold',
            field=models.PositiveIntegerField(default=80),
        ),
        migrations.AddField(
            model_name='inspectionpolicy',
            name='rules',
            field=djongo.models.fields.ArrayReferenceField(help_text='rules in policy', null=True, on_delete=django.db.models.deletion.CASCADE, to='darwin.InspectionRule'),
        ),
        migrations.RunPython(remove_session_and_logs_filters)
    ]
