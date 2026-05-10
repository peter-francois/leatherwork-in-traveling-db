from cart.constants import CART_EXPIRATION_DAYS, CGV_EXPIRATION_DAYS
from cart.models import Cart, CartItem
from legal.choices import DocumentType
from legal.models import LegalDocument
from django.utils.timezone import now
from datetime import timedelta
import uuid

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

def get_or_create_active_cart(request) -> Cart:
    if not request.session.session_key:
        request.session.create()
    
    session_id = request.session.session_key
    cart, created = Cart.objects.get_or_create(
        session_id=session_id,
        defaults={'uuid': uuid.uuid4()}
    )

    if cart.paid:
        request.session.create()
        session_id = request.session.session_key
        cart = Cart.objects.create(session_id=session_id, uuid=uuid.uuid4())

    return cart

def add_product_to_cart(cart, product) -> None:
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    product.pending_in_cart = True
    product.save()

