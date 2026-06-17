from django.urls import path
from . import views
from django.utils.translation import gettext_lazy as _



app_name = 'cart'


urlpatterns = [
    path(_('panier/'), views.cart, name="cart"),
    path(_('paiement_reussi/'), views.success_view, name='success'),
    path(_('paiement_annule/'), views.cancel_view, name='cancel'),
    path('count/', views.cart_count, name='cart_count'),
]