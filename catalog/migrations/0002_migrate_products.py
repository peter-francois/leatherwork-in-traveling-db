from django.db import migrations

def migrate_products(apps, schema_editor):
    AllProducts = apps.get_model('page_vente', 'AllProducts')
    Product = apps.get_model('catalog', 'Product')

    for obj in AllProducts.objects.all():
        Product.objects.create(
            id=obj.id,
            nom=obj.nom,
            categorie=obj.categorie,
            type=obj.type,
            description=obj.description,
            prix=obj.prix,
            discount=obj.discount,
            image1=obj.image1,
            image2=obj.image2,
            image3=obj.image3,
            image4=obj.image4,
            image5=obj.image5,
            image6=obj.image6,
            disponible=obj.disponible,
            en_attente_dans_panier=obj.en_attente_dans_panier,
            sur_commande=obj.sur_commande,
            updated_at=obj.updated_at,
        )

class Migration(migrations.Migration):

    dependencies = [
        ('catalog', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_products),
    ]