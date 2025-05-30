# Generated by Django 5.0.2 on 2025-05-23 10:13

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("counsel", "0002_counsel_consent_counsel_consent2"),
    ]

    operations = [
        migrations.RenameField(
            model_name="counsel",
            old_name="sales_2024",
            new_name="sales",
        ),
        migrations.RemoveField(
            model_name="counsel",
            name="inquiry_type",
        ),
        migrations.RemoveField(
            model_name="counsel",
            name="sales_2025",
        ),
        migrations.AddField(
            model_name="counsel",
            name="industry_detail",
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name="counsel",
            name="start_date",
            field=models.CharField(max_length=50),
        ),
    ]
