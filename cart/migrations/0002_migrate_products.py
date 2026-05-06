from django.db import migrations

def migrate_carts(apps, schema_editor):
    OldCart  = apps.get_model('page_vente', 'Cart')
    NewCart  = apps.get_model('cart', 'Cart')

    for obj in OldCart.objects.all():
        NewCart.objects.create(
            id=obj.id,
            session_id=obj.session_id,
            uuid=obj.uuid,
            cgv_accepted=obj.cgv_accepted,
            cgv_accepted_at=obj.cgv_accepted_at,
            cgv_expires_at=obj.cgv_expires_at,
            created_at=obj.created_at,
            cart_expires_at=obj.cart_expires_at,
            paid=obj.paid,
            paid_at=obj.paid_at,
        )

def migrate_cart_items(apps, shema_editor):
    OldCartItem = apps.get_model('page_vente', 'CartItem')
    NewCartItem = apps.get_model('cart', 'CartItem')

    for obj in OldCartItem.objects.all():
        NewCartItem.objects.create(
            id = obj.id,
            cart_id = obj.cart_id,
            product_id = obj.product_id,
            quantity = obj.quantity
        )

class Migration(migrations.Migration):

    dependencies = [
        ('cart', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(migrate_carts),
        migrations.RunPython(migrate_cart_items), 
    ]