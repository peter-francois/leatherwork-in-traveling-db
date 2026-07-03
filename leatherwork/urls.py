"""
URL configuration for leatherwork project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.conf import settings
from django.conf.urls.i18n import i18n_patterns
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from core import views as core_views
from core.sitemaps import StaticSitemap
from core.sitemaps_category import CategorySitemap
from core.sitemaps_product_detail import ProductDetailSitemap

app_name = "main"

sitemaps = {
    "static": StaticSitemap("fr"),
    "static_en": StaticSitemap("en"),
    "categories_fr": CategorySitemap("fr"),
    "categories_en": CategorySitemap("en"),
    "products_fr": ProductDetailSitemap("fr"),
    "products_en": ProductDetailSitemap("en"),
}

urlpatterns = i18n_patterns(
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("", include("legal.urls")),
    path("", include("catalog.urls")),
    path("", include("cart.urls")),
    path(
        "i18n/", include("django.conf.urls.i18n")
    ),  # Activation du changement de langue
)

urlpatterns += [
    path("sitemap.xml", core_views.sitemap_index, name="sitemap-index"),
    path("sitemap-fr.xml", core_views.sitemap_lang, {"lang": "fr"}, name="sitemap-fr"),
    path("sitemap-en.xml", core_views.sitemap_lang, {"lang": "en"}, name="sitemap-en"),
    path("robots.txt", core_views.robots_txt, name="robots_txt"),
    path("api/legal/", include("legal.api.urls")),
    path("api/cart/", include("cart.api.urls", "cart_api")),
    path("api/catalog/", include("catalog.api.urls")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
