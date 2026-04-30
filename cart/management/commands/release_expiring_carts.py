from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from cart.models import Cart
from datetime import timedelta


class Command(BaseCommand):
    help = "Libère les articles des paniers qui vont expirer bientôt"

    def handle(self, *args, **kwargs):
        expiration_threshold = now() + timedelta(hours=1)

        expiring_sessions = Session.objects.filter(expire_date__lte=expiration_threshold)
        if not expiring_sessions.exists():
            self.stdout.write("✅ Aucun panier expiré à libérer.")
            return

        expired_session_keys = list(expiring_sessions.values_list('session_key', flat=True))
        expired_carts = Cart.objects.filter(
            session_id__in=expired_session_keys,
            paid=False,
        ).prefetch_related('cartitem_set__product')

        if not expired_carts.exists():
            self.stdout.write("✅ Aucun panier à libérer.")
            return

        total_products_liberated = 0
        total_carts_deleted = 0

        for cart in expired_carts:
            for item in cart.cartitem_set.all():
                product = item.product
                if product.pending_in_cart:
                    product.pending_in_cart = False
                    product.save(update_fields=["pending_in_cart"])
                    total_products_liberated += 1
            cart.delete()
            total_carts_deleted += 1

        expiring_sessions.delete()

        self.stdout.write(f"✔️ {total_products_liberated} produit(s) libéré(s) et {total_carts_deleted} panier(s) supprimé(s).")