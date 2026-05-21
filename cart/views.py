from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from cart.services import convert_centimes_to_euros, get_stripe_session
from legal.choices import DocumentType
from legal.models import LegalDocument
from .models import Cart, CartItem
from core.services import get_session_expiration
import stripe
import logging

logger = logging.getLogger(__name__)

def cart(request):
    session_key = request.session.session_key
    latest_cgv = LegalDocument.objects.filter(document_type=DocumentType.TERMS).latest('created_at')
    cart = Cart.objects.filter(session_id=session_key, paid=False).first() if session_key else None
    items = CartItem.objects.filter(cart=cart) if cart else []
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
        session, cart_uuid = get_stripe_session(session_id) 
        cart = get_object_or_404(Cart, uuid=cart_uuid)
        total_verified_euros = convert_centimes_to_euros(session.amount_total)

        return render(request, 'cart/success.html', {
            'order_id': cart.id,
            'total_amount': total_verified_euros,
            'payment_date': cart.paid_at if cart.paid_at else "Non disponible",
        })
        
    except ValueError as e:
        logger.error(f"Error: {e}")
        return redirect('/')


def cancel_view(request):
    return render(request, 'cart/cancel.html')

def cart_count(request):
    session_key = request.session.session_key
    count = CartItem.objects.filter(
        cart__session_id=session_key,
        cart__paid=False
    ).count() if session_key else 0
    return HttpResponse(count)