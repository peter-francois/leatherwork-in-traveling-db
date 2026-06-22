from django.urls import path

from . import views

app_name = "cart_api"

urlpatterns = [
    path("add_to_cart/<int:product_id>/", views.add_to_cart, name="add_to_cart"),
    path("empty_cart/", views.empty_cart, name="empty_cart"),
    path(
        "remove_from_cart/<int:product_id>/",
        views.remove_from_cart,
        name="remove_from_cart",
    ),
    path("checkout/", views.checkout, name="checkout"),
    path("webhook_stripe/", views.stripe_webhook, name="webhook_stripe"),
]
