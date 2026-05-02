from django.shortcuts import render, get_object_or_404, redirect
from cart.services import get_total_centimes
from legal.choices import DocumentType
from legal.models import LegalDocument
from .models import Cart, CartItem
import uuid
from core.services import get_session_expiration
import stripe
import logging
from django.urls import reverse
from datetime import timedelta
from django.utils.timezone import now
from django.http import JsonResponse
from django.conf import settings
import json

logger = logging.getLogger(__name__)

def cart(request):
    session_key = request.session.session_key
    latest_cgv = LegalDocument.objects.filter(document_type=DocumentType.TERMS).latest('created_at')
    cart = Cart.objects.filter(session_id=session_key, paid=False).first()
    items = CartItem.objects.filter(cart=cart)
    total = sum((item.product.price - item.product.discount) * item.quantity for item in items)
    expiration_date = get_session_expiration(request)

    return render(request, "cart/cart.html", {
        "expiration_date": expiration_date,
        "items": items,
        "total": total,
        "latest_cgv": latest_cgv,
    })


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
        return render(request, 'cart/success.html', {
            'order_id': cart.id,
            'total_amount': total_verified,
            'payment_date': cart.paid_at if cart.paid_at else "Non disponible",
        })

    except stripe.error.StripeError:
        logger.error("Erreur Stripe lors de la récupération de la session.")
        return redirect('/')

def cancel_view(request):
    return render(request, 'cart/cancel.html')