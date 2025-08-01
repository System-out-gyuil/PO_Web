# Generated manually for emoji support

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('diary', '0028_kanbansettings'),
    ]

    operations = [
        migrations.RunSQL(
            "ALTER TABLE diary_alarm CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            reverse_sql="ALTER TABLE diary_alarm CONVERT TO CHARACTER SET utf8 COLLATE utf8_general_ci;"
        ),
        migrations.RunSQL(
            "ALTER TABLE diary_alarm MODIFY title VARCHAR(100) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;",
            reverse_sql="ALTER TABLE diary_alarm MODIFY title VARCHAR(100) CHARACTER SET utf8 COLLATE utf8_general_ci;"
        ),
    ] 