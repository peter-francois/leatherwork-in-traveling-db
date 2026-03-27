from django.core.management.base import BaseCommand
from django.utils import timezone
from page_vente.models import Cart, CartItem


class Command(BaseCommand):
    help = "Suprimmé les paniers de plus de 10 ans"

    def handle(self, *args, **kwargs):
        # Seuil de libération des paniers
        expiration_date = timezone.now()

        # Trouver les paniers expirés
        expired_carts = Cart.objects.filter(cart_expires_at__lt=expiration_date)

        if not expired_carts.exists():
            self.stdout.write("✅ Aucun panier expiré à supprimer.")
            return

        # Récupérer et supprimer les articles des paniers expirés
        carts_ids = list(expired_carts.values_list('id', flat=True))
        cart_items = CartItem.objects.filter(cart_id__in=carts_ids)

        total_carts_deleted = 0

        # Supprimer les paniers correspondants
        for cart in expired_carts:
            if cart_items:
                for cart_item in cart_items:
                    cart_item.delete()
            cart.delete()
            total_carts_deleted += 1

        self.stdout.write(f"✔️ {total_carts_deleted} panier(s) supprimé(s).")