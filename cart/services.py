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
        
def send_email_to_owner(customer_email, customer_name, shipping_address, list_products, cart_uuid, total_articles, cgv_version, add_insurance, total_verified, order_id, add_shipping):
    # Vérification et conversion de list_products
    if isinstance(list_products, str):
        try:
            list_products = json.loads(list_products)
        except json.JSONDecodeError as e:
            logger.error(f"Erreur lors de la désérialisation de list_products: {e}")
            return  # Arrêt si la désérialisation échoue

    if not isinstance(list_products, list):
        logger.error("Erreur : list_products n'est pas une liste.")
        return  # Arrêt de l'exécution pour éviter des erreurs

    # Vérification et formatage de l'adresse
    shipping_address_line_2 = shipping_address.get('line2')
    if shipping_address_line_2 and shipping_address_line_2.lower() != "none":
        address = ', '.join(filter(None, [shipping_address.get('line1', 'Adresse inconnue'), shipping_address_line_2]))
    else:
        address = shipping_address.get('line1', 'Adresse inconnue')

    # Vérification et conversion de total_verified
    try:
        total_verified = round(float(total_verified) / 100, 2)  # Convertir en float avant de diviser
    except ValueError:
        logger.error(f"Erreur: total_verified contient une valeur non numérique ({total_verified}). Valeur par défaut utilisée.")
        total_verified = 0.00
    
    # Vérification si assurance supplémentaire ou assurance obligatoire (commande >= 50€)
    if add_insurance == 'True' or float(total_articles) >= 50:
        insurance = 'Oui'
    else:
        insurance = 'Non'
    if add_shipping == 'True':
        shipping = 'Oui'
    else:
        shipping = 'Non'
    shipping_cost = 10 if add_shipping == 'True' else 5
    insurance_cost = round(float(total_verified) - float(total_articles) - float(shipping_cost), 2)


    # Sujet de l'email
    subject = 'Nouvelle commande reçue'

    # Générer le message HTML
    message = f"""
    <html>
    <body>
    <p>Une nouvelle commande a été passée par {customer_name}.</p>
    <p>Numéro de commande : {order_id}</p>
    <h5>Condition générale de vente et UUID:</h5>
    <ul>
        <li>UUID : {cart_uuid}</li>
        <li>Version des Conditions Générales de vente acceptée : {cgv_version}</li>
    </ul>
    <h5>Détails du client :</h5>
    <ul>
        <li>Nom du client : {customer_name}</li>
        <li>Email client : {customer_email}</li>
        <li>Pays : {shipping_address.get('country', 'Pays inconnu')}</li>
        <li>Adresse de livraison : {address}</li>
        <li>Code postal : {shipping_address.get('postal_code', 'Code postal inconnu')}</li>
        <li>Ville : {shipping_address.get('city', 'Ville inconnue')}</li>
    </ul>
    <h5>Détails de la commande :</h5>
    <ul>
        <li>Assurance: {insurance}</li>
        <li>Livraison à domicile: {shipping}</li>
        <li>Frais de port : {shipping_cost} €</li>
        <li>Total des articles : {total_articles} €</li>
        <li>Assurance : {insurance_cost} €</li>
        <li><strong>Total de la commande frais de port et assurance inclus: {total_verified} €</strong></li>
        <li>
            <h5>Produits commandés :</h5>
            <ul>
    """

    # Ajouter chaque produit à l'email
    for product in list_products:
        if isinstance(product, dict):
            image_url = product.get("image_url", 'default-image-url')
            product_name = product.get("name", "Nom inconnu")
            message += f'<li><img src="{image_url}" alt="{product_name}" style="width:200px;" /> {product_name}</li>'
        else:
            logger.error(f"Produit invalide détecté : {product}")
            message += f'<li>Erreur avec le produit : {product}</li>'

    message += """
            </ul>
        </li>
    </ul>
    <br>
    <p>Merci de traiter la commande.</p>
    </body>
    </html>
    """

    # Envoi de l'email
    try:
        send_mail(
            subject,
            message,
            settings.EMAIL_HOST_USER,
            [settings.CLIENT_EMAIL],
            html_message=message,
        )
    except Exception as e:
        logger.error(f"Erreur lors de l'envoi de l'email : {e}")
