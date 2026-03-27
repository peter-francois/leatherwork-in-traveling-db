from django.urls import path
from . import views
from page_vente.views import *
from django.utils.translation import gettext_lazy as _



app_name = 'boutique'


urlpatterns = [
    path(_('produits/macrames/'), views.macrames, name="macrames"),
    path(_('produits/maroquinerie/'), views.maroquinerie, name="maroquinerie"),
    path(_('creation-sur-mesure/'), views.creation_sur_mesure, name="creation-sur-mesure"),
    path(_('produits/hybride/'), views.hybride, name="hybride"),
    path(_('produits/'), views.produits, name="produits"),
    path(_('panier/'), views.panier, name="panier"),
    path(_('paiement_reussi/'), views.success_view, name='paiement_reussi'),
    path(_('paiement_annule/'), views.cancel_view, name='paiement_annule'),
]