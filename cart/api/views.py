import logging

import stripe
from django.conf import settings
from django.db import transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from cart.services import (
    build_metadata,
    create_stripe_session,
    extract_session_data,
    process_successful_payment,
    register_cgv_acceptance,
    verify_total,
)
from cart.services.cart_services import (
    add_product_to_cart,
    empty_cart_and_release_products,
    get_cart_items_data,
    get_or_create_active_cart,
    remove_product_from_cart,
)
from cart.services.email_services import send_email_to_owner
from cart.services.pricing_services import (
    AmountMismatchError,
    AmountNegatifError,
    calculate_total_centimes,
    convert_euros_to_centimes,
)
from cart.services.stripe_services import StripeSessionError
from catalog.models import Product
from legal.choices import DocumentType
from legal.models import LegalDocument

from ..models import Cart

logger = logging.getLogger(__name__)
endpoint_secret = settings.STRIPE_WEBHOOK_SECRET


def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    if not product.available or product.pending_in_cart:
        return JsonResponse(
            {"success": False, "message": "Product not available or pending in cart"},
            status=400,
        )

    cart = get_or_create_active_cart(request)
    add_product_to_cart(cart, product)

    return JsonResponse(
        {
            "success": True,
            "message": f"{product.name} ajouté au panier",
            "cart_uuid": str(cart.uuid),
        }
    )


def cart_detail(request):
    session_id = request.session.session_key
    if not session_id:
        return JsonResponse({"cart": []})

    cart = Cart.objects.filter(session_id=session_id, paid=False).first()
    if not cart:
        return JsonResponse({"cart": []})

    return JsonResponse({"cart": get_cart_items_data(cart)})


def empty_cart(request):
    session_id = request.session.session_key
    if not session_id:
        return JsonResponse({"success": False, "message": "No cart found"})

    cart = Cart.objects.filter(session_id=session_id, paid=False).first()
    if not cart:
        return JsonResponse({"success": False, "message": "Cart already empty"})
    empty_cart_and_release_products(cart)

    return JsonResponse({"success": True, "message": "Le panier a été vide"})


def remove_from_cart(request, product_id):
    session_id = request.session.session_key
    if not session_id:
        return JsonResponse({"success": False, "message": "Aucun panier trouvé"})
    cart = Cart.objects.filter(session_id=session_id, paid=False).first()
    if not cart:
        return JsonResponse({"success": False, "message": "No cart found"})

    product_data = remove_product_from_cart(cart, product_id)
    if not product_data:
        return JsonResponse({"success": False, "message": "Item not found in cart"})

    return JsonResponse(
        {"success": True, "message": "Item removed from cart", "article": product_data}
    )


def checkout(request):
    front_total_euros = float(request.GET.get("front_total"))
    is_optional_insurance = request.GET.get("insurance") == "1"
    is_home_delivery = request.GET.get("shipping") == "1"
    accept_cgv = request.GET.get("acceptCGV") == "1"
    success_url = request.build_absolute_uri(reverse("cart:success"))
    cancel_url = request.build_absolute_uri(reverse("cart:cancel"))
    cart_uuid = request.GET.get("cart_uuid")

    if not cart_uuid:
        return JsonResponse({"error": "Cart UUID manquant"}, status=400)

    cart = Cart.objects.filter(uuid=cart_uuid, paid=False).first()
    if not cart:
        return JsonResponse({"error": "Panier invalide ou expiré."}, status=400)

    if not accept_cgv:
        logger.error("L'utilisateur n'a pas accepté les conditions générales de vente.")
        return JsonResponse(
            {"error": "Vous devez accepter les conditions générales de vente"},
            status=400,
        )
    accepted_terms = LegalDocument.objects.filter(
        document_type=DocumentType.TERMS
    ).latest("created_at")

    accepted_terms_version = register_cgv_acceptance(cart, accepted_terms)

    total_articles_euros = float(Cart.get_total(cart))
    total_articles_centimes = convert_euros_to_centimes(total_articles_euros)
    total_centimes = calculate_total_centimes(
        total_articles_centimes, is_optional_insurance, is_home_delivery
    )
    front_total_centimes = convert_euros_to_centimes(front_total_euros)
    metadata = build_metadata(
        cart,
        is_optional_insurance,
        is_home_delivery,
        total_centimes,
        total_articles_centimes,
        accepted_terms_version,
    )

    try:
        verify_total(total_centimes, front_total_centimes)
        url = create_stripe_session(
            cart, metadata, success_url, cancel_url, total_centimes
        )

    except AmountNegatifError:
        return JsonResponse({"error": "Montant total négatif"}, status=400)

    except AmountMismatchError:
        return JsonResponse({"error": "Montant incohérent"}, status=400)

    except StripeSessionError:
        return JsonResponse({"error": "Erreur de paiement"}, status=500)

    return redirect(url)


@csrf_exempt  # Désactive la protection CSRF pour recevoir les requêtes Stripe
def stripe_webhook(request):
    payload = request.body
    sig_header = request.headers.get("Stripe-Signature", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except ValueError:
        return HttpResponse("Invalid payload", status=400)
    except stripe.SignatureVerificationError:
        return HttpResponse("Invalid signature", status=400)

    # if payment is not completed
    if event["type"] != "checkout.session.completed":
        return JsonResponse({"status": "ignored"})

    session = event["data"]["object"]
    if session.get("payment_link"):
        logger.warning("Payment via Payment Link ignored")
        return JsonResponse({"status": "ignored - payment link"}, status=200)
    metadata = session.get("metadata", {})
    cart_uuid = metadata.get("cart_uuid")

    if not cart_uuid:
        logger.error("Cart UUID manquant.")
        return JsonResponse({"status": "error - missing cart UUID"}, status=400)
    try:
        with transaction.atomic():
            cart = Cart.objects.select_for_update().get(uuid=cart_uuid)
            if cart.paid:
                logger.info(f"Already processed {cart_uuid}")
                return JsonResponse({"status": "already processed"}, status=200)
            process_successful_payment(cart)

        data = extract_session_data(session, metadata)

        if data["list_products"] is None:
            logger.error("Invalid list_products")
            return JsonResponse({"status": "error - invalid products"}, status=400)

        send_email_to_owner(order_id=cart.id, **data)
        logger.info(f"Payment processed {cart_uuid}")
        return JsonResponse({"status": "success"}, status=200)

    except Cart.DoesNotExist:
        return JsonResponse({"status": "cart not found"}, status=404)

    except Exception:
        logger.exception("Stripe webhook failed")

        return JsonResponse({"status": "error"}, status=500)
