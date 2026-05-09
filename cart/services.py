import json
import logging
from django.core.mail import send_mail
from django.conf import settings
import stripe
from django.utils.timezone import now
from datetime import timedelta
from legal.choices import DocumentType
from legal.models import LegalDocument
from .constants import (
    ALLOWED_COUNTRIES, CGV_EXPIRATION_DAYS, STANDARD_SHIPPING_COST, EXPRESS_SHIPPING_COST,
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


def _build_email_message(customer_name, customer_email, order_id, cart_uuid, cgv_version,
                          shipping_address, insurance, home_delivery, shipping_cost,
                          total_articles, insurance_cost, total_verified, list_products) -> str:
    """Build HTML email message"""
    message = f"""
    <html><body>
    <p>Une nouvelle commande a été passée par {customer_name}.</p>
    <p>Numéro de commande : {order_id}</p>
    <h5>Condition générale de vente et UUID:</h5>
    <ul>
        <li>UUID: {cart_uuid}</li>
        <li>ersion des Conditions Générales de vente acceptée : {cgv_version}</li>
    </ul>
    <h5>Détails du client :</h5>
    <ul>
        <li>Nom: {customer_name}</li>
        <li>Email: {customer_email}</li>
        <li>Pays: {shipping_address.get('country', 'Unknown')}</li>
        <li>Addresse : {shipping_address.get('formatted', 'Unknown')}</li>
        <li>Code postal : {shipping_address.get('postal_code', 'Unknown')}</li>
        <li>Ville: {shipping_address.get('city', 'Unknown')}</li>
    </ul>
    <h5>Détails de la commande:</h5>
    <ul>
        <li>Assurance: {insurance}</li>
        <li>Livraison à domicile: {home_delivery}</li>
        <li>Frais de port : {shipping_cost}€</li>
        <li>Total des articles : {total_articles}€</li>
        <li>Coût de l'assurance: {insurance_cost}€</li>
        <li><strong>Total de la commande frais de port et assurance inclus : {total_verified}€</strong></li>
        <li><h5>Produits commandés :</h5><ul>
    """

    for product in list_products:
        if isinstance(product, dict):
            image_url = product.get("image_url", 'default-image-url')
            product_name = product.get("name", "Unknown")
            message += f'<li><img src="{image_url}" alt="{product_name}" style="width:200px;" /> {product_name}</li>'
        else:
            logger.error(f"Invalid product detected: {product}")
            message += f'<li>Error with product: {product}</li>'

    message += """
        </ul></li>
    </ul>
    <p>Merci de traiter la commande.</p>
    </body></html>
    """
    return message


def send_email_to_owner(customer_email, customer_name, shipping_address, list_products,
                         cart_uuid, total_articles, cgv_version, add_insurance,
                         total_verified, order_id, add_shipping):
    total_verified_euros = round(float(total_verified) / 100, 2)
    total_articles_euros = round(float(total_articles) / 100, 2)
    shipping_cost_euros = EXPRESS_SHIPPING_COST / 100 if add_shipping == 'True' else STANDARD_SHIPPING_COST / 100
    insurance_cost_euros = round(total_verified_euros - total_articles_euros - shipping_cost_euros, 2)
    insurance = 'Oui' if add_insurance == 'True' or total_articles_euros >= 50 else 'Non'
    home_delivery = 'Oui' if add_shipping == 'True' else 'Non'
    list_products = _parse_list_products(list_products)
    if list_products is None:
        return

    shipping_address = _format_shipping_address(shipping_address)

    message = _build_email_message(
        customer_name, customer_email, order_id, cart_uuid, cgv_version,
        shipping_address, insurance, home_delivery, shipping_cost_euros,
        total_articles_euros, insurance_cost_euros, total_verified_euros, list_products
    )

    try:
        send_mail(
            'Nouvelle commande reçue depuis leatherworkintravelingdb.com',
            message,
            settings.EMAIL_HOST_USER,
            [settings.CLIENT_EMAIL],
            html_message=message,
        )
    except Exception as e:
        logger.error(f"Error sending email: {e}")