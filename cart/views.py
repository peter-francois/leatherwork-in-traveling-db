from django.shortcuts import render, get_object_or_404, redirect
from cart.services import convert_centimes_to_euros
from legal.choices import DocumentType
from legal.models import LegalDocument
from .models import Cart, CartItem
import uuid
from core.services import get_session_expiration
import stripe
import logging

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

        # ✅ Convertir cart_uuid en format UUID
        try:
            cart_uuid = uuid.UUID(cart_uuid)  # Transforme la string en UUID valide
        except ValueError:
            logger.error("UUID du panier invalide.")
            return redirect('/')

        cart = get_object_or_404(Cart, uuid=cart_uuid)

        # Vérifier que le total correspond bien
        total_verified_centimes = session.amount_total
        if total_verified_centimes is None:
            raise ValueError("Total verified is missing")

        total_verified_euros = convert_centimes_to_euros(total_verified_centimes)

        return render(request, 'cart/success.html', {
            'order_id': cart.id,
            'total_amount': total_verified_euros,
            'payment_date': cart.paid_at if cart.paid_at else "Non disponible",
        })

    except stripe.error.StripeError:
        logger.error("Erreur Stripe lors de la récupération de la session.")
        return redirect('/')

def cancel_view(request):
    return render(request, 'cart/cancel.html')