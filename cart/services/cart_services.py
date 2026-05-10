from cart.constants import CART_EXPIRATION_DAYS, CGV_EXPIRATION_DAYS
from legal.choices import DocumentType
from legal.models import LegalDocument
from django.utils.timezone import now
from datetime import timedelta

def register_cgv_acceptance(cart) -> None:
    if not cart.cgv_accepted:
        latest_cgv = LegalDocument.objects.filter(
            document_type=DocumentType.TERMS
        ).latest('created_at')
        cart.cgv_accepted = latest_cgv
        cart.cgv_accepted_at = now()
        cart.cgv_expires_at = cart.cgv_accepted_at + timedelta(days=CGV_EXPIRATION_DAYS)
        cart.save()

def process_successful_payment(cart) -> None:
    """Mark cart as paid and update product availability"""
    if not cart.paid:
        cart.paid = True
        cart.paid_at = now()
        cart.cart_expires_at = cart.paid_at + timedelta(days=CART_EXPIRATION_DAYS)
        cart.save()

        for item in cart.cartitem_set.all():
            item.product.available = False
            item.product.pending_in_cart = False
            item.product.on_demand = True
            item.product.save()

def convert_centimes_to_euros(centimes):
    return round(float(centimes) / 100, 2)
