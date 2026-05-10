import json
import logging
from django.core.mail import send_mail
from django.conf import settings
from cart.constants import EXPRESS_SHIPPING_COST, STANDARD_SHIPPING_COST
from cart.services import convert_centimes_to_euros

logger = logging.getLogger(__name__)

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
    total_verified_euros = convert_centimes_to_euros(total_verified)
    total_articles_euros = convert_centimes_to_euros(total_articles)
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