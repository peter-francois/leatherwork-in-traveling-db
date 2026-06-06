from cart.constants import CART_EXPIRATION_DAYS, CGV_EXPIRATION_DAYS
from cart.models import Cart, CartItem
from django.utils.timezone import now
from datetime import timedelta
import uuid

def register_cgv_acceptance(cart, accepted_terms) -> str:

    if cart.cgv_accepted != accepted_terms:
        cart.cgv_accepted = accepted_terms
        cart.cgv_accepted_at = now()
        cart.cgv_expires_at = (
            cart.cgv_accepted_at
            + timedelta(days=CGV_EXPIRATION_DAYS)
        )

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

def empty_cart_and_release_products(cart) -> None:

    for item in cart.cartitem_set.all():
        item.product.pending_in_cart = False
        item.product.save()
    cart.cartitem_set.all().delete()
    cart.delete()

def get_cart_items_data(cart) -> list:
    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    return [
        {
            'name': item.product.name,
            'price': item.product.price,
            'quantity': item.quantity,
            'id': item.product.id,
            'discount': item.product.discount,
            **{f'image{i}': getattr(item.product, f'image{i}').url 
               if getattr(item.product, f'image{i}') else None 
               for i in range(1, 7)}
        }
        for item in cart_items
    ]

def remove_product_from_cart(cart, product_id) -> bool:
    cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
    if not cart_item:
        return False

    product = cart_item.product
    product.pending_in_cart = False
    product.save()
    cart_item.delete()
    return True