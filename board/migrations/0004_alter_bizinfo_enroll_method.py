# Generated by Django 5.0.2 on 2025-05-12 11:11

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("board", "0003_alter_bizinfo_application_form_path"),
    ]

    operations = [
        migrations.AlterField(
            model_name="bizinfo",
            name="enroll_method",
            field=models.CharField(max_length=500),
        ),
    ]
