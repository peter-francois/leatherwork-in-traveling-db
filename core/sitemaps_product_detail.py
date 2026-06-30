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
        return Product.objects.all()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        with translation.override(self.language):
            category = slugify(obj.category)
            slug = obj.slug or slugify(obj.name)

            if not category or not slug:
                return None

            return reverse(
                "catalog:product_detail",
                kwargs={
                    "category": category,
                    "slug": slug,
                    "product_id": obj.id,
                },
            )
