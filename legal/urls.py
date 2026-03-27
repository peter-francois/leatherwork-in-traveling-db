from django.urls import path
from . import views
from page_vente.views import *
from django.utils.translation import gettext_lazy as _



app_name = 'legal'


urlpatterns = [
    path(_('terms/'), views.terms_view, name="terms"),
    path(_('cookies/'), views.cookies_view, name="cookies"),
    path(_('legal-mentions/'), views.legal_mentions_view, name="legal_mentions"),
    path(_('privacy-policy/'), views.privacy_policy_view, name="privacy_policy"),
]