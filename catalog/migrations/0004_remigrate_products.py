from django.db import migrations

def remigrate_products(apps, schema_editor):
    pass  # Already migrated, page_vente app removed

class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_alter_product_options_remove_product_categorie_and_more'),
    ]

    operations = [
        migrations.RunPython(remigrate_products),
    ]