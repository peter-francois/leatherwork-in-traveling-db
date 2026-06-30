from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import timezone, translation


class CategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def __init__(self, language="fr"):
        self.language = language

        self.categories = [
            "catalog:product_list",
            "catalog:leather_list",
            "catalog:macrame_list",
            "catalog:hybrid_list",
        ]

    def items(self):
        return self.categories

    def lastmod(self, item):
        return timezone.now()

    def location(self, item):
        with translation.override(self.language):
            return reverse(item)
