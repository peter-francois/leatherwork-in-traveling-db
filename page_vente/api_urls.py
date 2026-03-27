from django.urls import path
from . import views
from legal import views as legal_views


urlpatterns = [
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart_detail/', views.cart_detail, name='cart_detail'),
    path('vider_panier/', views.vider_panier, name='vider_panier'),
    path('remove_from_cart/<int:product_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('get_product_images/<int:article_id>/', views.get_product_images, name='get_product_images'),
    path('get_number_of_products_in_cart/', views.get_number_of_products_in_cart, name='get_number_of_products_in_cart'),
    path('get_document_content/<str:document_type>/<str:lang>/', legal_views.get_document_content, name='get_document_content'),
    path('checkout/', views.checkout, name='checkout'),
    path('webhook_stripe/', views.stripe_webhook, name='webhook_stripe'),
]