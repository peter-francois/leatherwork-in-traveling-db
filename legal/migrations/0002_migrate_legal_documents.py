from django.db import migrations

def migrate_legal_data(apps, schema_editor):
    pass  # Already migrated, page_vente app removed

class Migration(migrations.Migration):

    dependencies = [
        ('legal', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_legal_data),
    ]