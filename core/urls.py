from django.urls import path
from . import views
from page_vente.views import *
from django.utils.translation import gettext_lazy as _



app_name = 'core'

urlpatterns = [
    path('', views.index, name="index"),
    # path(_('contact/'), views.contact, name="contact"),
    # path(_('a_propos/'), views.a_propos, name="a_propos"),
]