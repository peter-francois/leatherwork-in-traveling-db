from django.db import migrations

def populate_french_translations(apps, schema_editor):
    Product = apps.get_model("catalog", "Product")
    for product in Product.objects.all():
        product.name_fr = product.name
        product.description_fr = product.description
        product.save()

class Migration(migrations.Migration):
    dependencies = [('catalog', '0007_product_description_en_product_description_fr_and_more'),]
    operations = [
        migrations.RunPython(populate_french_translations),
    ]