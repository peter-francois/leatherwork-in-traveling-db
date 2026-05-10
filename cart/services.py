import json
import logging
from django.conf import settings
import stripe
from django.utils.timezone import now
from datetime import timedelta
from legal.choices import DocumentType
from legal.models import LegalDocument
import uuid
from cart.constants import (
    ALLOWED_COUNTRIES, CART_EXPIRATION_DAYS, CGV_EXPIRATION_DAYS, EXPRESS_SHIPPING_COST, STANDARD_SHIPPING_COST,
    INSURANCE_OPTIONAL_MIN, INSURANCE_OPTIONAL_MAX, INSURANCE_OPTIONAL_COST,
    INSURANCE_MANDATORY_MIN,INSURANCE_THRESHOLD_1,
    INSURANCE_THRESHOLD_2,INSURANCE_THRESHOLD_3,INSURANCE_COST_50_TO_125,
    INSURANCE_COST_125_TO_250,INSURANCE_COST_250_TO_375,
    INSURANCE_COST_ABOVE_375,
)

stripe.api_key = settings.STRIPE_SECRET_KEY
logger = logging.getLogger(__name__)

class AmountMismatchError(Exception):
    pass


class StripeSessionError(Exception):
    pass


def _build_product_list(cart):
    """Build product list for Stripe metadata"""
    products = []
    for item in cart.cartitem_set.all():
        image_url = next(
            (getattr(item.product, f'image{i}').url
             for i in range(1, 5)
             if getattr(item.product, f'image{i}')
             ),
            'default-image-url'
        )
        products.append({
            'name': item.product.name,
            'image_url': image_url,
        })
    return products

def create_stripe_session(cart, metadata, success_url, cancel_url, total_centimes) -> str:
    item_count = cart.cartitem_set.count()

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f"Commande de {item_count} article{'s' if item_count > 1 else ''}",
                    },
                    'unit_amount': total_centimes,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata = metadata,
            shipping_address_collection={
                'allowed_countries': list(ALLOWED_COUNTRIES),
            },
            custom_text={
                "shipping_address": {
                    "message": f"If your country is not listed, please contact us by email {settings.CLIENT_EMAIL}. We have a solution to ship your order to any part of Europe."
                }
            },
        )
        session_url = checkout_session.url
        if session_url is None:
            raise ValueError("Stripe checkout session URL is missing")

        return session_url

    except stripe.StripeError as e:
        logger.error(f"Stripe error: {e}")
        raise StripeSessionError("Stripe payment error")

    except Exception as e:
        logger.exception(f"Unexpected error creating Stripe session: {e}")
        raise StripeSessionError("Unexpected error")
    
def build_metadata(cart, add_insurance, add_shipping, total_centimes, total_articles):
    return {
        "cart_uuid": str(cart.uuid),
        "add_insurance": str(add_insurance),
        "add_shipping": str(add_shipping),
        'total_articles': str(total_articles),
        "total_verified": str(total_centimes),
        "cgv_version": str(cart.cgv_accepted.version),
        "list_products": json.dumps(_build_product_list(cart)),
    }

def get_total_centimes(total_articles, add_insurance, add_shipping) -> int:
    total_centimes = int(round(total_articles * 100))

    if total_centimes > INSURANCE_MANDATORY_MIN:
        if total_centimes > INSURANCE_THRESHOLD_3:
            total_centimes += INSURANCE_COST_ABOVE_375
        elif total_centimes > INSURANCE_THRESHOLD_2:
            total_centimes += INSURANCE_COST_250_TO_375
        elif total_centimes > INSURANCE_THRESHOLD_1:
            total_centimes += INSURANCE_COST_125_TO_250
        else:
            total_centimes += INSURANCE_COST_50_TO_125
    elif INSURANCE_OPTIONAL_MIN < total_centimes <= INSURANCE_OPTIONAL_MAX:
        if add_insurance:
            total_centimes += INSURANCE_OPTIONAL_COST

    total_centimes += EXPRESS_SHIPPING_COST if add_shipping else STANDARD_SHIPPING_COST

    if total_centimes <= 0:
        raise ValueError("Invalid total amount")

    return total_centimes

def verify_total(total_articles, add_insurance, add_shipping, front_total) -> int:
    
    total_centimes = get_total_centimes(total_articles, add_insurance, add_shipping)
    front_total_centimes = int(round(front_total * 100))
    
    if front_total_centimes != total_centimes:
        raise AmountMismatchError(f"Front: {front_total_centimes}, Back: {total_centimes}")
    
    return total_centimes

def register_cgv_acceptance(cart) -> None:
    if not cart.cgv_accepted:
        latest_cgv = LegalDocument.objects.filter(
            document_type=DocumentType.TERMS
        ).latest('created_at')
        cart.cgv_accepted = latest_cgv
        cart.cgv_accepted_at = now()
        cart.cgv_expires_at = cart.cgv_accepted_at + timedelta(days=CGV_EXPIRATION_DAYS)
        cart.save()

def convert_centimes_to_euros(centimes):
    return round(float(centimes) / 100, 2)

def get_stripe_session(session_id: str):
    session = stripe.checkout.Session.retrieve(session_id)
    
    if session.payment_status != 'paid':
        raise ValueError("Payment not completed")
    
    metadata = getattr(session, "metadata", {})
    if not isinstance(metadata, dict) or "cart_uuid" not in metadata:
        raise ValueError("Invalid metadata or missing cart_uuid")
    
    try:
        cart_uuid = uuid.UUID(metadata["cart_uuid"])
    except ValueError:
        raise ValueError("Invalid cart UUID")
    
    if session.amount_total is None:
        raise ValueError("Total verified is missing")
    
    return session, cart_uuid

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
            item.product.save()

def extract_session_data(session, metadata) -> dict:
    """Extract and prepare data from Stripe session"""
    shipping_address = session.get('collected_information', {}).get('shipping_details', {}).get('address', {})
    _format_shipping_address(shipping_address)
    
    list_products = _parse_list_products(metadata.get('list_products'))
    
    return {
        'customer_email': session.get('customer_details', {}).get('email', 'Unknown'),
        'customer_name': session.get('customer_details', {}).get('name', 'Unknown'),
        'shipping_address': shipping_address,
        'list_products': list_products,
        'cart_uuid': metadata.get('cart_uuid'),
        'total_articles': metadata.get('total_articles'),
        'cgv_version': metadata.get('cgv_version'),
        'add_insurance': metadata.get('add_insurance'),
        'add_shipping': metadata.get('add_shipping'),
        'total_verified': metadata.get('total_verified'),
    }

def _parse_list_products(list_products: str | list) -> list | None:
    """Parse and validate list_products from string or list"""
    if isinstance(list_products, str):
        try:
            list_products = json.loads(list_products)
        except json.JSONDecodeError as e:
            logger.error(f"Failed to deserialize list_products: {e}")
            return None

    if not isinstance(list_products, list):
        logger.error("list_products is not a list")
        return None

    return list_products


def _format_shipping_address(shipping_address: dict) -> dict:
    """Format shipping address for email"""
    line2 = shipping_address.get('line2')
    if line2 and line2.lower() != "none":
        shipping_address['formatted'] = ', '.join(filter(None, [shipping_address.get('line1', 'Unknown'), line2]))
    else:
        shipping_address['formatted'] = shipping_address.get('line1', 'Unknown')
    return shipping_address
