from django.core.management.base import BaseCommand
from django.utils import timezone
from page_vente.models import Cart


class Command(BaseCommand):
    help = "Libère les acceptations des CGV après 5 ans"

    def handle(self, *args, **kwargs):
        # Seuil de libération des cgv_Acceptation
        expiration_date = timezone.now()

        # Trouver les paniers dont les CGV ont expiré
        expired_cgv_cart = Cart.objects.filter(cgv_expires_at__lt=expiration_date)

        if not expired_cgv_cart.exists():
            self.stdout.write("✅ Aucun CGV expiré à libérer.")
            return

        # Réinitialiser les preuves d'acceptation des CGV pour les paniers expirés
        for cart in expired_cgv_cart:
            cart.cgv_accepted = None  # Supprimer la référence à CGV
            cart.cgv_accepted_at = None  # Réinitialiser la date d'acceptation
            cart.cgv_expires_at = None  # Réinitialiser la date d'expiration
            cart.save()

        self.stdout.write(f"✔️ Preuves d'acceptation des CGV supprimées pour {expired_cgv_cart.count()} panier(s).")