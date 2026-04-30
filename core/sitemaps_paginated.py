from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation
from django.core.paginator import Paginator
from catalog.models import Product
from catalog.constants import PRODUCTS_PER_PAGE

class PaginatedCategorySitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.8

    def __init__(self, language='fr'):
        self.language = language
        self.categories = [
            ('boutique:produits', Product.objects.order_by('-id')),
            ('boutique:maroquinerie', Product.objects.filter(category='Maroquinerie').order_by('-id')),
            ('boutique:macrames', Product.objects.filter(category='Macrame').order_by('-id')),
            ('boutique:hybride', Product.objects.filter(category='Hybride').order_by('-id')),
        ]

    def items(self):
        items = []
        for view_name, queryset in self.categories:
            paginator = Paginator(queryset, PRODUCTS_PER_PAGE)
            for page_number in range(1, paginator.num_pages + 1):
                items.append((view_name, page_number))
        return items

    def location(self, item):
        view_name, page_number = item
        with translation.override(self.language):
            url = reverse(view_name)
        if page_number == 1:
            return url  
        return f"{url}?page={page_number}"