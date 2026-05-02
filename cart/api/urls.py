from django.urls import path
from . import views

urlpatterns = [
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart_detail/', views.cart_detail, name='cart_detail'),
    path('empty_cart/', views.empty_cart, name='empty_cart'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('get_number_of_products/', views.get_number_of_products, name='get_number_of_products'),
    path('checkout/', views.checkout, name='checkout'),
    path('webhook_stripe/', views.stripe_webhook, name='webhook_stripe'),
]