from django.db import migrations, models


def rename_start_time_to_appointment_time(apps, schema_editor):
    # Rename the column in the database
    if schema_editor.connection.vendor == 'postgresql':
        schema_editor.execute(
            'ALTER TABLE appointments_appointment RENAME COLUMN start_time TO appointment_time;'
        )
    else:
        # For SQLite, MySQL, etc.
        with schema_editor.connection.cursor() as cursor:
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND name='appointments_appointment';"
            )
            result = cursor.fetchone()
            if result and 'start_time' in result[0]:
                # This is a simplified approach and may need adjustment based on your database
                # For production, you might want to use a more robust solution like django-rename-field
                cursor.execute(
                    'ALTER TABLE appointments_appointment RENAME COLUMN start_time TO appointment_time;'
                )


class Migration(migrations.Migration):

    dependencies = [
        ('appointments', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='appointment',
            old_name='start_time',
            new_name='appointment_time',
        ),
        migrations.RunPython(rename_start_time_to_appointment_time, reverse_code=migrations.RunPython.noop),
    ]
