from django.core.management.base import BaseCommand
from django.utils import timezone
from cart.models import Cart


class Command(BaseCommand):
    help = "Libère les acceptations des CGV après 5 ans"

    def handle(self, *args, **kwargs):
        expiration_date = timezone.now()
        expired_cgv_carts = Cart.objects.filter(cgv_expires_at__lt=expiration_date)

        if not expired_cgv_carts.exists():
            self.stdout.write("✅ Aucun CGV expiré à libérer.")
            return

        count = expired_cgv_carts.count()
        expired_cgv_carts.update(
            cgv_accepted=None,
            cgv_accepted_at=None,
            cgv_expires_at=None,
        )

        self.stdout.write(f"✔️ Preuves d'acceptation des CGV supprimées pour {count} panier(s).")