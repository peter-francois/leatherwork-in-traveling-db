from django.urls import path
from django.utils.translation import gettext_lazy as _

from . import views

app_name = "core"

urlpatterns = [
    path("", views.index, name="index"),
    path(_("creation-sur-mesure/"), views.custom_creation, name="custom_creation"),
    # path(_('contact/'), views.contact, name="contact"),
    # path(_('a_propos/'), views.a_propos, name="a_propos"),
]
