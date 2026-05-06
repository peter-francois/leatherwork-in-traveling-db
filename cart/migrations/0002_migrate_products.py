from django.db import migrations

def migrate_carts(apps, schema_editor):
    pass  # Already migrated, page_vente app removed

def migrate_cart_items(apps, shema_editor):
    pass  # Already migrated, page_vente app removed

class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_carts),
        migrations.RunPython(migrate_cart_items), 
    ]