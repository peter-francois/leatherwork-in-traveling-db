from django.core.management.base import BaseCommand
from django.utils import timezone

from cart.models import Cart


class Command(BaseCommand):
    help = "Supprime les paniers de plus de 10 ans"

    def handle(self, *args, **kwargs):
        expiration_date = timezone.now()
        expired_carts = Cart.objects.filter(cart_expires_at__lt=expiration_date)

        if not expired_carts.exists():
            self.stdout.write("✅ Aucun panier expiré à supprimer.")
            return

        count = expired_carts.count()
        expired_carts.delete()

        self.stdout.write(f"✔️ {count} panier(s) supprimé(s).")
