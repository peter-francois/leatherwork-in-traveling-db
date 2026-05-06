from django.db import migrations

def migrate_products(apps, schema_editor):
    pass  # Already migrated, page_vente app removed

class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_products),
    ]