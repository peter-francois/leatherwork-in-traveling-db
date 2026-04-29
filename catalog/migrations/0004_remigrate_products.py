from django.db import migrations

def remigrate_products(apps, schema_editor):
    AllProducts = apps.get_model('page_vente', 'AllProducts')
    Product = apps.get_model('catalog', 'Product')

    Product.objects.all().delete()

    for obj in AllProducts.objects.all():
        Product.objects.create(
            id=obj.id,
            name=obj.nom,
            category=obj.categorie,
            product_type=obj.type,
            description=obj.description,
            price=obj.prix,
            discount=obj.discount,
            image1=obj.image1,
            image2=obj.image2,
            image3=obj.image3,
            image4=obj.image4,
            image5=obj.image5,
            image6=obj.image6,
            available=obj.disponible,
            pending_in_cart=obj.en_attente_dans_panier,
            on_demand=obj.sur_commande,
            updated_at=obj.updated_at,
        )

class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0003_alter_product_options_remove_product_categorie_and_more'),
        ('page_vente', '0048_alter_cart_cgv_accepted'),
    ]

    operations = [
        migrations.RunPython(remigrate_products),
    ]