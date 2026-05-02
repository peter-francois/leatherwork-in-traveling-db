from django.http import JsonResponse
import json
import logging
from django.core.mail import send_mail
from django.conf import settings
from cart.models import Cart
import stripe

logger = logging.getLogger(__name__)

def create_stripe_session(cart, add_insurance, add_shipping, accept_cgv, front_total, success_url, cancel_url):

    total_articles = float(Cart.get_total(cart))

    # Calcul du total en centimes
    total_centimes = get_total_centimes(total_articles, add_insurance, add_shipping)

    # Convertir le montant du front-end en centimes pour la comparaison
    front_total_centimes = int(round(front_total * 100))

    # Comparaison en centimes
    if front_total_centimes != total_centimes:
        return JsonResponse({'error': 'Problème de cohérence des montants', 'total': total_centimes / 100, 'front_total': front_total}, status=400)

    # Créer la session de paiement Stripe
    list_products = []
    for item in cart.cartitem_set.all():

        image_url = None
        if item.product.image1.url:
            image_url = item.product.image1.url
        elif item.product.image2.url:
            image_url = item.product.image2.url
        elif item.product.image3.url:
            image_url = item.product.image3.url
        elif item.product.image4.url:
            image_url = item.product.image4.url

        list_products.append({
            'name': item.product.name,
            'image_url': image_url if image_url else 'default-image-url',
        })
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'eur',
                    'product_data': {
                        'name': f"Commande de {cart.cartitem_set.count()} article{'s' if cart.cartitem_set.count() > 1 else ''}",
                    },
                    'unit_amount': total_centimes,
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={
                            'cart_uuid': str(cart.uuid),
                            'acceptCGV': str(accept_cgv),
                            'cgv_version': str(cart.cgv_accepted.version),
                            'add_insurance': str(add_insurance),
                            'add_shipping': str(add_shipping),
                            'total_articles': float(total_articles),
                            'total_verified': int(total_centimes),
                            'list_products': json.dumps(list_products),
                        },
            shipping_address_collection={
                'allowed_countries': ['FR','DE','AT','BE','ES','IT','LU','NL','PT'],
            },
            custom_text={
                "shipping_address": {
                    "message": f"If your country is not listed, please contact us by email {settings.CLIENT_EMAIL}. We have a solution to ship your order to any part of Europe."
                }
            },
        )
        return checkout_session.url
    
    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe : {e}")
        return JsonResponse({'error': 'Erreur de paiement, veuillez réessayer.'}, status=500)
    
    except Exception as e:
        logger.exception("Erreur inattendue lors de la création de la session Stripe.")
        return JsonResponse({'error': 'Une erreur est survenue.'}, status=500)

def get_total_centimes(total_articles, add_insurance, add_shipping):

    # Calculer le total en centimes
    total_centimes = int(round(total_articles * 100))

    # Ajouter l'assurance en centimes si nécessaire
    if total_centimes > 5000:
        if total_centimes > 37500:
            total_centimes += 800
        elif total_centimes > 25000:
            total_centimes += 650
        elif total_centimes > 12500:
            total_centimes += 500
        else:
            total_centimes += 350
    elif 2500 < total_centimes <= 5000:
        if add_insurance:
            total_centimes += 200

    # Ajouter les frais de port en centimes
    if add_shipping:
        total_centimes += 1000
    else:
        total_centimes += 500

    # Vérification du total
    if total_centimes <= 0:
        return JsonResponse({'error': 'Montant invalide.'}, status=400)

    return total_centimes  # Total en centimes

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
