from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from .models import *
from .forms import ProductFilterForm
from django.core.paginator import Paginator
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.csrf import csrf_protect, csrf_exempt
from django.utils.timezone import now
from .utils.sessions import get_session_expiration
import stripe
import json
import logging
from django.conf import settings
# pour résoudre le problème de CSRF token
from django.views.decorators.csrf import ensure_csrf_cookie
from datetime import timedelta
from django.urls import reverse
from django.core.mail import send_mail
from django.utils import translation
from django.contrib.sitemaps.views import sitemap as django_sitemap
from urllib.parse import urlencode


stripe.api_key = settings.STRIPE_SECRET_KEY
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET


logger = logging.getLogger(__name__)

def produits(request):
    all_products = AllProducts.objects.all()

    all_products = [product for product in all_products if product.disponible]

    all_products.sort(key=lambda product: (product.en_attente_dans_panier, -product.id))

    all_products, form, number_of_products_in_filter, filter_used = use_filter(request, all_products, is_all_products=True )

    page_obj = pagination(request,all_products)

    context = {
        'products': page_obj,
        'form': form,
        'number_of_products_in_filter': number_of_products_in_filter,
        'filter_used': filter_used,
    }

    return render(request, 'page_vente/produits.html', context)

def maroquinerie(request):
    all_leather_products = AllProducts.objects.all().filter(categorie='Maroquinerie')
    all_leather_products = [product for product in all_leather_products if product.disponible]

    all_leather_products.sort(key=lambda product: (product.en_attente_dans_panier, -product.id))

    all_leather_products, form, number_of_products_in_filter, filter_used = use_filter(request, all_leather_products, is_all_products=False)

    page_obj = pagination(request,all_leather_products)

    context = {
        'products': page_obj,
        'form': form,
        'number_of_products_in_filter': number_of_products_in_filter,
        'filter_used': filter_used,
    }

    return render(request, 'page_vente/maroquinerie.html', context)

def macrames(request):

    all_macrame_products = AllProducts.objects.all().filter(categorie='Macrame')
    all_macrame_products = [product for product in all_macrame_products if product.disponible]

    all_macrame_products.sort(key=lambda product: (product.en_attente_dans_panier, -product.id))

    all_macrame_products, form, number_of_products_in_filter, filter_used = use_filter(request, all_macrame_products, is_all_products=False)

    page_obj = pagination(request,all_macrame_products)

    context = {
        'products': page_obj,
        'form': form,
        'number_of_products_in_filter': number_of_products_in_filter,
        'filter_used': filter_used,
    }

    return render(request, 'page_vente/macrames.html', context)

def hybride(request):
    all_hybride_products = AllProducts.objects.all().filter(categorie='Hybride')
    all_hybride_products = [product for product in all_hybride_products if product.disponible]

    all_hybride_products.sort(key=lambda product: (product.en_attente_dans_panier, -product.id))

    all_hybride_products, form, number_of_products_in_filter, filter_used = use_filter(request, all_hybride_products, is_all_products=False)

    page_obj = pagination(request,all_hybride_products)

    context = {
        'products': page_obj,
        'form': form,
        'number_of_products_in_filter': number_of_products_in_filter,
        'filter_used': filter_used,
    }

    return render(request, 'page_vente/hybride.html', context)

def creation_sur_mesure(request):
    return render(request, 'page_vente/creation_sur_mesure.html')

def panier(request):
    session_key = request.session.session_key
    latest_cgv = CGV.objects.latest('created_at')
    cart = Cart.objects.filter(session_id=session_key, paid=False).first()
    items = CartItem.objects.filter(cart=cart)
    total = sum((item.product.prix - item.product.discount) * item.quantity for item in items)
    expiration_date = get_session_expiration(request)

    return render(request, "page_vente/panier.html", {
        "expiration_date": expiration_date,
        "items": items,
        "total": total,
        "latest_cgv": latest_cgv,
    })
def add_to_cart(request, product_id):
    product = get_object_or_404(AllProducts, id=product_id)

    if not product.disponible or product.en_attente_dans_panier:
        return JsonResponse({'success': False, 'message': 'Produit déjà pris'}, status=400)

    if not request.session.session_key:
        request.session.create()
    session_id = request.session.session_key

    # Vérifier si un panier existe pour cette session
    cart, created = Cart.objects.get_or_create(session_id=session_id,defaults={'uuid': uuid.uuid4()})

    if cart.paid:
        request.session.create()
        session_id = request.session.session_key
        cart = Cart.objects.create(session_id=session_id, uuid=uuid.uuid4())

    # Récupérer l'expiration de la session
    expiration_date = get_session_expiration(request)


    # Ajouter le produit au panier
    cart_item, item_created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not item_created:
        cart_item.quantity += 1
        cart_item.save()

    # Marquer le produit comme en attente dans le panier
    product.en_attente_dans_panier = True
    product.save()

    return JsonResponse({
        'success': True,
        'message': f'{product.nom} ajouté au panier',
        'cart_uuid': str(cart.uuid),
        "session_expiration": expiration_date.strftime('%Y-%m-%d %H:%M:%S') if expiration_date else None,
    })

def cart_detail(request):
    session_id = request.session.session_key
    if not session_id:
        return JsonResponse({'cart': []})

    cart = Cart.objects.filter(session_id=session_id, paid=False).first()
    if not cart:
        return JsonResponse({'cart': []})

    cart_items = CartItem.objects.filter(cart=cart).select_related('product')
    data = []

    for item in cart_items:
        product = item.product
        
        data.append({
            'nom': product.nom,
            'prix': product.prix,
            'quantity': item.quantity,
            'image1': product.image1.url if product.image1 else None,
            'image2': product.image2.url if product.image2 else None,
            'image3': product.image3.url if product.image3 else None,
            'image4': product.image4.url if product.image4 else None,
            'image5': product.image5.url if product.image5 else None,
            'image6': product.image6.url if product.image6 else None,
            'id': product.id,
            'discount': product.discount
        })

    return JsonResponse({'cart': data})

def vider_panier(request):
    session_id = request.session.session_key
    if not session_id:
        return JsonResponse({'success': False, 'message': 'Aucun panier trouvé'})

    cart = Cart.objects.filter(session_id=session_id, paid=False).first()
    if not cart:
        return JsonResponse({'success': False, 'message': 'Le panier est déjà vide'})
    cart_items = CartItem.objects.filter(cart=cart)
    for item in cart_items:
        item.product.en_attente_dans_panier = False
        item.product.save()
        item.delete()

    cart.delete()  # Supprimer le panier après suppression des articles

    return JsonResponse({'success': True, 'message': 'Le panier a été vide'})

def remove_from_cart(request, product_id):
    session_id = request.session.session_key
    if not session_id:
        return JsonResponse({'success': False, 'message': 'Aucun panier trouvé'})
    cart = Cart.objects.filter(session_id=session_id, paid=False).first()
    cart_item = CartItem.objects.filter(cart=cart, product_id=product_id).first()
    if cart_item:
        cart_item.product.en_attente_dans_panier = False
        cart_item.product.save()
        cart_item.delete()
        return JsonResponse({'success': True, 'message': 'Article retiré du panier', 'article': {"id": cart_item.product.id, "prix": cart_item.product.prix}})
    else:
        return JsonResponse({'success': False, 'message': 'Article non trouvé dans le panier'})

def get_product_images(request, article_id):
    try:
        product = AllProducts.objects.get(id=article_id)
        images = [
            product.image1.url if product.image1 else None,
            product.image2.url if product.image2 else None,
            product.image3.url if product.image3 else None,
            product.image4.url if product.image4 else None,
            product.image5.url if product.image5 else None,
            product.image6.url if product.image6 else None,
            ]
        images = [image for image in images if image]
        return JsonResponse({'images': images, 'nom': product.nom, 'description': product.description if product.description else None, 'discount': product.discount,'prix': product.prix, 'en_attente_dans_panier': product.en_attente_dans_panier, 'sur_commande': product.sur_commande})
    except AllProducts.DoesNotExist:
        return JsonResponse({'error': 'Product not found'}, status=404)


def use_filter(request, product_views, is_all_products):
    
    filter_used = False
    if not product_views:
        return product_views, None, 0, filter_used

    if is_all_products:
        form = ProductFilterForm(request.GET, categorie=None)

    else:
        categorie = product_views[0].categorie if hasattr(product_views[0], 'categorie') else None
        if not categorie:
            return product_views, None , 0, filter_used

        form = ProductFilterForm(request.GET, categorie=categorie)  

    if form.is_valid():
        search = form.cleaned_data.get('search')
        type = form.cleaned_data.get('type')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        sort_by_price = form.cleaned_data.get('sort_by_price')


        if search:
            product_views = [product for product in product_views if search.lower() in product.nom.lower()]
            filter_used = True
        if type:
            if type == '---':
                type = None
            else:
                product_views = [product for product in product_views if product.type == type]
                filter_used = True
        if min_price is not None:
            product_views = [product for product in product_views if product.prix >= min_price]
            filter_used = True
        if max_price is not None:
            product_views = [product for product in product_views if product.prix <= max_price]
            filter_used = True
        if sort_by_price:
            if sort_by_price == 'price':
                product_views = sorted(product_views, key=lambda x: x.prix)
                filter_used = True
            elif sort_by_price == '-price':
                product_views = sorted(product_views, key=lambda x: x.prix, reverse=True)
                filter_used = True
        number_of_products_in_filter = len(product_views)

    return product_views, form, number_of_products_in_filter, filter_used

def pagination(request, product_views):

    paginator = Paginator(product_views, 24)
    page_number = request.GET.get('page', 1)
    return paginator.get_page(page_number)

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

def checkout(request):
    success_url_build = request.build_absolute_uri(reverse('boutique:paiement_reussi'))
    cancel_url_build = request.build_absolute_uri(reverse('boutique:paiement_annule'))
    cart_uuid = request.GET.get('cart_uuid')
    cart = Cart.objects.filter(uuid=cart_uuid, paid=False).first()
    front_total = float(request.GET.get('front_total'))

    if not cart:
        return JsonResponse({'error': 'Panier invalide ou expiré.'}, status=400)

    # Récupérer les paramètres envoyés par le front
    add_insurance = request.GET.get('insurance') == '1'
    add_shipping = request.GET.get('shipping') == '1'
    acceptCGV = request.GET.get('acceptCGV') == '1'
    if not acceptCGV:
        logger.error("L'utilisateur n'a pas accepté les conditions générales de vente.")
        return JsonResponse({'error': 'Vous devez accepter les conditions générales de vente'}, status=400)

    # Récupérer la dernière version des CGV
    latest_cgv = CGV.objects.latest('created_at')

    # Enregistrer l'acceptation des CGV
    if not cart.cgv_accepted:
        cart.cgv_accepted = latest_cgv
        cart.cgv_accepted_at = now()
        cart.cgv_expires_at = cart.cgv_accepted_at + timedelta(days=5*365)
        cart.save()

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
            'name': item.product.nom,
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
            success_url=success_url_build + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url_build,
            metadata={
                            'cart_uuid': str(cart_uuid),
                            'acceptCGV': str(acceptCGV),
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
        return redirect(checkout_session.url)
    except stripe.error.StripeError as e:
        logger.error(f"Erreur Stripe : {e}")
        return JsonResponse({'error': 'Erreur de paiement, veuillez réessayer.'}, status=500)
    except Exception as e:
        logger.exception("Erreur inattendue lors de la création de la session Stripe.")
        return JsonResponse({'error': 'Une erreur est survenue.'}, status=500)

def success_view(request):
    session_id = request.GET.get('session_id')
    if not session_id:
        logger.error("Session ID manquant.")
        return redirect('/')

    try:
        session = stripe.checkout.Session.retrieve(session_id)
        if session.payment_status != 'paid':
            return redirect('/')

# Vérifier si `metadata` est bien un dictionnaire
        metadata = getattr(session, "metadata", {})
        if not isinstance(metadata, dict) or "cart_uuid" not in metadata:
            logger.error("Métadonnées invalides ou cart_uuid manquant.")
            return redirect('/')

        cart_uuid = metadata["cart_uuid"]
        add_insurance = metadata.get('add_insurance', 'false').lower() == 'true'
        add_shipping = metadata.get('add_shipping', 'false').lower() == 'true'
        total_articles = float(metadata.get('total_articles', 0))

        # ✅ Convertir cart_uuid en format UUID
        try:
            cart_uuid = uuid.UUID(cart_uuid)  # Transforme la string en UUID valide
        except ValueError:
            logger.error("UUID du panier invalide.")
            return redirect('/')

        cart = get_object_or_404(Cart, uuid=cart_uuid)

        # Vérifier que le total correspond bien
        total_verified_centimes = session.amount_total
        total_cart = get_total_centimes(total_articles, add_insurance, add_shipping)

        if total_verified_centimes != total_cart:
            logger.error(f"Montant invalide. Total vérifié: {total_verified_centimes}, Total du panier: {total_cart}")
            return redirect('/')

        total_verified = round(total_verified_centimes / 100, 2)
        return render(request, 'page_vente/paiement_reussi.html', {
            'order_id': cart.id,
            'total_amount': total_verified,
            'payment_date': cart.paid_at if cart.paid_at else "Non disponible",
        })

    except stripe.error.StripeError:
        logger.error("Erreur Stripe lors de la récupération de la session.")
        return redirect('/')

def cancel_view(request):
    return render(request, 'page_vente/paiement_annule.html')

@csrf_exempt  # Désactive la protection CSRF pour recevoir les requêtes Stripe
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature', '')


    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse("Invalid payload", status=400)
    except stripe.error.SignatureVerificationError:
        return HttpResponse("Invalid signature", status=400)
    # 🎯 Si un paiement est réussi
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        if session.get("payment_link"):
            logger.warning("Paiement via Payment Link ignoré.")
            return JsonResponse({'status': 'ignored - payment link'}, status=200)
        # 🔹 Vérifier si `metadata` existe avant d'accéder à `cart_uuid`
        metadata = session.get("metadata", {})
        cart_uuid = metadata.get("cart_uuid")
        if not cart_uuid:
            logger.error("Cart UUID manquant.")
            return JsonResponse({'status': 'error - missing cart UUID'}, status=400)

        cart = get_object_or_404(Cart, uuid=cart_uuid)
        if not cart.paid:  # Vérifier que le panier n'a pas déjà été traité
            cart.paid = True
            cart.paid_at = now()
            cart.cart_expires_at = cart.paid_at + timedelta(days=10*365)
            cart.save()
        # 🔄 Mettre à jour la disponibilité des produits du panier
            for item in cart.cartitem_set.all():
                product = item.product
                product.disponible = False
                product.en_attente_dans_panier = False
                product.save()

        logger.info(f"✅ Paiement reçu pour le panier {cart_uuid}")

        # Récupérer les informations du client
        order_id = cart.id
        customer_email = session.get('customer_details', {}).get('email', 'Email inconnu')
        customer_name = session.get('customer_details', {}).get('name', 'Nom inconnu')
        shipping_address = session.get('collected_information', {}).get('shipping_details', {}).get('address', {})
        list_products = metadata.get('list_products')
        cart_uuid= metadata.get('cart_uuid')
        total_articles = metadata.get('total_articles')
        cgv_version= metadata.get('cgv_version')
        add_insurance= metadata.get('add_insurance')
        add_shipping= metadata.get('add_shipping')
        total_verified= metadata.get('total_verified')




        # Vous pouvez maintenant utiliser ces informations pour envoyer un email de confirmation
        send_email_to_owner(customer_email, customer_name, shipping_address, list_products, cart_uuid, total_articles, cgv_version, add_insurance, total_verified, order_id, add_shipping)

    return JsonResponse({'status': 'success'}, status=200)

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

def cgv_view(request):
    latest_cgv = CGV.objects.latest('created_at')
    return render(request, 'page_vente/cgv.html', {'cgv': latest_cgv})

def cookies_view(request):
    latest_cookies = CookiesPolicy.objects.latest('created_at')
    return render(request, 'page_vente/cookies.html', {'cookies': latest_cookies})

def legal_mentions_view(request):
    latest_legal_mentions = LegalMention.objects.latest('created_at')
    return render(request, 'page_vente/mentions-legales.html', {'legal_mentions': latest_legal_mentions})

def privacy_policy_view(request):
    latest_privacy_policy = PrivacyPolicy.objects.latest('created_at')
    return render(request, 'page_vente/politique-confidentialite.html', {'privacy_policy': latest_privacy_policy})

def get_number_of_products_in_cart(request):
    session_key = request.session.session_key

    # Vérifie si le session_key est valide
    if not session_key:
        return JsonResponse({'success': False, 'number_of_products': 0})

    try:
        # Récupère le panier lié à la session
        cart = Cart.objects.filter(session_id=session_key).first()

        # Si aucun panier n'est trouvé
        if not cart:
            return JsonResponse({'success': False, 'number_of_products': 0})
        if cart.paid:
            return JsonResponse({'success': False, 'number_of_products': 0})

        # Comptage des articles dans le panier
        cart_items = CartItem.objects.filter(cart=cart)
        cart_items_count = cart_items.count()
        return JsonResponse({'success': True, 'number_of_products': cart_items_count})

    except ObjectDoesNotExist:
        # Si une erreur se produit avec l'accès aux objets, retourner une réponse vide
        return JsonResponse({'success': False, 'number_of_products': 0})

def get_document_content(request, document_type, lang):
    try:
        if document_type == 'CGV':
            latest_cgv = CGV.objects.latest('created_at')
            content = latest_cgv.content_fr if lang == 'fr' else latest_cgv.content_en
            cookies_url = reverse('boutique:cookies')
            privacy_policy_url = reverse('boutique:privacy_policy')
            content = content.replace("cookies_url", cookies_url)
            content = content.replace("privacy_policy_url", privacy_policy_url)
        elif document_type == 'Cookies':
            latest_cookies = CookiesPolicy.objects.latest('created_at')
            content = latest_cookies.content_fr if lang == 'fr' else latest_cookies.content_en
        elif document_type == 'LegalMentions':
            latest_legal_mentions = LegalMention.objects.latest('created_at')
            content = latest_legal_mentions.content_fr if lang == 'fr' else latest_legal_mentions.content_en
            cookies_url = reverse('boutique:cookies')
            cgv_url = reverse('boutique:cgv')
            privacy_policy_url = reverse('boutique:privacy_policy')
            content = content.replace("cookies_url", cookies_url)
            content = content.replace("cgv_url", cgv_url)
            content = content.replace("privacy_policy_url", privacy_policy_url)

        elif document_type == 'PrivacyPolicy':
            latest_privacy_policy = PrivacyPolicy.objects.latest('created_at')
            content = latest_privacy_policy.content_fr if lang == 'fr' else latest_privacy_policy.content_en
        else:
            return JsonResponse({'error': 'Invalid document type'}, status=400)

        return HttpResponse(content, content_type="text/html")

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
