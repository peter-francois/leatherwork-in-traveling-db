from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation
from django.utils.text import slugify

from catalog.models import Product


class ProductDetailSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.9

    def __init__(self, language="fr"):
        self.language = language

    def items(self):
        return Product.objects.filter(seo_ready=True).order_by("id")

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        with translation.override(self.language):
            category = obj.category_slug
            slug = slugify(obj.name)

            return reverse(
                "catalog:product_detail",
                kwargs={
                    "category": category,
                    "slug": slug,
                    "product_id": obj.id,
                },
            )
