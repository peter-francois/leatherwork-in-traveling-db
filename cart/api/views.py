from django.shortcuts import get_object_or_404, redirect
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from cart.services.email_services import send_email_to_owner
from cart.services import build_metadata, create_stripe_session, extract_session_data, process_successful_payment, register_cgv_acceptance, verify_total
from cart.services.pricing_services import AmountMismatchError
from cart.services.stripe_services import StripeSessionError
from core.services import get_session_expiration
import stripe
from django.urls import reverse
from django.conf import settings
from catalog.models import Product
from ..models import Cart, CartItem
import logging
import uuid

logger = logging.getLogger(__name__)
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not product.available or product.pending_in_cart:
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
    product.pending_in_cart = True
    product.save()

    return JsonResponse({
        'success': True,
        'message': f'{product.name} ajouté au panier',
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
            'name': product.name,
            'price': product.price,
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

def empty_cart(request):
    session_id = request.session.session_key
    if not session_id:
        return JsonResponse({'success': False, 'message': 'Aucun panier trouvé'})

    cart = Cart.objects.filter(session_id=session_id, paid=False).first()
    if not cart:
        return JsonResponse({'success': False, 'message': 'Le panier est déjà vide'})
    cart_items = CartItem.objects.filter(cart=cart)
    for item in cart_items:
        item.product.pending_in_cart = False
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
        cart_item.product.pending_in_cart = False
        cart_item.product.save()
        cart_item.delete()
        return JsonResponse({'success': True, 'message': 'Article retiré du panier', 'article': {"id": cart_item.product.id, "price": cart_item.product.price}})
    else:
        return JsonResponse({'success': False, 'message': 'Article non trouvé dans le panier'})
    
def get_number_of_products(request):
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

def checkout(request):
    front_total = float(request.GET.get('front_total'))
    add_insurance = request.GET.get('insurance') == '1'
    add_shipping = request.GET.get('shipping') == '1'
    accept_cgv = request.GET.get('acceptCGV') == '1'
    success_url = request.build_absolute_uri(reverse('cart:success'))
    cancel_url = request.build_absolute_uri(reverse('cart:cancel'))
    cart_uuid = request.GET.get('cart_uuid')

    if not cart_uuid:
        return JsonResponse({'error': 'Cart UUID manquant'}, status=400)
    
    cart = Cart.objects.filter(uuid=cart_uuid, paid=False).first()
    if not cart:
        return JsonResponse({'error': 'Panier invalide ou expiré.'}, status=400)
    
    if not accept_cgv:
        logger.error("L'utilisateur n'a pas accepté les conditions générales de vente.")
        return JsonResponse({'error': 'Vous devez accepter les conditions générales de vente'}, status=400)
    
    register_cgv_acceptance(cart)

    total_articles = float(Cart.get_total(cart))
    total_centimes = verify_total(total_articles, add_insurance, add_shipping, front_total)
    metadata = build_metadata(cart, add_insurance, add_shipping, total_centimes, total_articles)

    try:
        url = create_stripe_session(cart, metadata, success_url, cancel_url, total_centimes)
    
    except AmountMismatchError:
        return JsonResponse({'error': 'Montant incohérent'}, status=400)
    
    except StripeSessionError:
        return JsonResponse({'error': 'Erreur de paiement'}, status=500)
    
    return redirect(url)

    
@csrf_exempt  # Désactive la protection CSRF pour recevoir les requêtes Stripe
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get('Stripe-Signature', '')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse("Invalid payload", status=400)
    except stripe.SignatureVerificationError:
        return HttpResponse("Invalid signature", status=400)
    
    # if payment is completed
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        if session.get("payment_link"):
            logger.warning("Payment via Payment Link ignored")
            return JsonResponse({'status': 'ignored - payment link'}, status=200)
        metadata = session.get("metadata", {})
        cart_uuid = metadata.get("cart_uuid")
        
        if not cart_uuid:
            logger.error("Cart UUID manquant.")
            return JsonResponse({'status': 'error - missing cart UUID'}, status=400)

        cart = get_object_or_404(Cart, uuid=cart_uuid)
        process_successful_payment(cart)

        logger.info(f"Payment received for cart {cart_uuid}")

        data = extract_session_data(session, metadata)
        if data['list_products'] is None:
            logger.error("Invalid list_products")
            return JsonResponse({'status': 'error - invalid products'}, status=400)

        send_email_to_owner(order_id=cart.id, **data)
    return JsonResponse({'status': 'success'}, status=200)
