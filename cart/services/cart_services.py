import uuid
from datetime import timedelta

from django.utils.timezone import now

from cart.constants import CART_EXPIRATION_DAYS, CGV_EXPIRATION_DAYS
from cart.models import Cart, CartItem


def register_cgv_acceptance(cart, accepted_terms) -> str:

    if cart.cgv_accepted != accepted_terms:
        cart.cgv_accepted = accepted_terms
        cart.cgv_accepted_at = now()
        cart.cgv_expires_at = cart.cgv_accepted_at + timedelta(days=CGV_EXPIRATION_DAYS)

        cart.save()

    return str(cart.cgv_accepted.version)


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


def get_or_create_active_cart(request) -> Cart:
    if not request.session.session_key:
        request.session.create()

    session_id = request.session.session_key
    cart, created = Cart.objects.get_or_create(
        session_id=session_id, defaults={"uuid": uuid.uuid4()}
    )

    if cart.paid:
        request.session.create()
        session_id = request.session.session_key
        cart = Cart.objects.create(session_id=session_id, uuid=uuid.uuid4())

    return cart


def add_product_to_cart(cart, product) -> bool:
    if not product.available or product.on_demand or product.pending_in_cart:
        return False

    CartItem.objects.create(cart=cart, product=product, quantity=1)
    product.pending_in_cart = True
    product.save()
    return True


def empty_cart_and_release_products(cart) -> bool:
    cart_items = cart.cartitem_set.all()
    if not cart_items.exists():
        return False

    for item in cart_items:
        item.product.pending_in_cart = False
        item.product.save()
    cart.delete()
    return True


def remove_product_from_cart(cart, product_id) -> bool:
    cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
    if not cart_item:
        return False

    product = cart_item.product
    product.pending_in_cart = False
    product.save()
    cart_item.delete()
    return True
