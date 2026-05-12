import logging
from django.core.mail import send_mail
from django.conf import settings
from cart.services.pricing_services import calculate_insurance_cost_centimes, convert_centimes_to_euros
from ..constants import EXPRESS_SHIPPING_COST, INSURANCE_MANDATORY_MIN, STANDARD_SHIPPING_COST


logger = logging.getLogger(__name__)

def send_email_to_owner(customer_email, customer_name, shipping_address, list_products,
                         cart_uuid, total_articles_centimes, cgv_version, add_insurance,
                         total_verified_centimes, order_id, add_shipping):
    if list_products is None:
        logger.error("list_products is None, email not sent")
        return
    
    total_verified_euros = convert_centimes_to_euros(total_verified_centimes)
    total_articles_euros = convert_centimes_to_euros(total_articles_centimes)
    shipping_cost_centimes = calculate_insurance_cost_centimes(total_verified_centimes, add_insurance)
    shipping_cost_euros = convert_centimes_to_euros(shipping_cost_centimes)
    insurance_cost_euros = round(total_verified_euros - total_articles_euros - shipping_cost_euros, 2)
    insurance = 'Oui' if add_insurance == 'True' or total_articles_euros >= INSURANCE_MANDATORY_MIN else 'Non'
    home_delivery = 'Oui' if add_shipping == 'True' else 'Non'

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

def _build_email_message(customer_name, customer_email, order_id, cart_uuid, cgv_version,
                          shipping_address, insurance, home_delivery, shipping_cost,
                          total_articles_euros, insurance_cost, total_verified_euros, list_products) -> str:
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
        <li>Total des articles : {total_articles_euros}€</li>
        <li>Coût de l'assurance: {insurance_cost}€</li>
        <li><strong>Total de la commande frais de port et assurance inclus : {total_verified_euros}€</strong></li>
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
