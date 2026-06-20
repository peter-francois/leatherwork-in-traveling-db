from django.urls import path
from django.utils.translation import gettext_lazy as _

from . import views

app_name = "catalog"


urlpatterns = [
    path(_("produits/macrames/"), views.macrame, name="macrame_list"),
    path(_("produits/maroquinerie/"), views.leatherwork, name="leather_list"),
    path(_("produits/hybride/"), views.hybrid, name="hybrid_list"),
    path(_("produits/"), views.product, name="product_list"),
]
