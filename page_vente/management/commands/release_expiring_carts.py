from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from page_vente.models import Cart, CartItem
from datetime import timedelta
from django.conf import settings

class Command(BaseCommand):
    help = "Libère les articles des paniers qui vont expirer bientôt"

    def handle(self, *args, **kwargs):
        # Seuil de libération des articles (ex: 1 heure avant expiration)
        expiration_threshold = now() + timedelta(hours=1)

        # Trouver les sessions qui vont expirer bientôt
        expiring_sessions = Session.objects.filter(expire_date__lte=expiration_threshold)

        if not expiring_sessions.exists():
            self.stdout.write("✅ Aucun panier expiré à libérer.")
            return

        # Récupérer et supprimer les paniers correspondants
        expired_session_keys = list(expiring_sessions.values_list('session_key', flat=True))

        # Récupérer les paniers correspondants avec prefetch_related() pour minimiser les requêtes en base (récupère tous les articles liés en une seule requête)
        expired_carts = Cart.objects.filter(session_id__in=expired_session_keys).prefetch_related('cartitem_set__product')
        
        if not expired_carts.exists():
            self.stdout.write("✅ Aucun panier à libérer.")
            return
        # Si tous les paniers sont payés
        if all(cart.paid for cart in expired_carts):
            self.stdout.write("✅ Aucun panier à libérer.")
            return

        # On ne garde que ceux à libérer (paid=False)
        expired_carts = expired_carts.filter(paid=False)

        total_products_liberated = 0
        total_carts_deleted = 0
        # Libérer les produits de ces paniers
        for cart in expired_carts:
            # Libérer les produits
            for item in cart.cartitem_set.all():
                product = item.product
                # Si le produit était en attente dans un panier, on le libère
                if product.en_attente_dans_panier:
                    product.en_attente_dans_panier = False
                    product.save(update_fields=["en_attente_dans_panier"])
                    total_products_liberated += 1

            # Supprimer le panier après avoir libéré les produits
            cart.delete()
            total_carts_deleted += 1

        # Nettoyer les sessions expirées en une seule requête
        expiring_sessions.delete()

        self.stdout.write(f"✔️ {total_products_liberated} produit(s) libéré(s) et {total_carts_deleted} panier(s) supprimé(s).")