from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from django.utils import translation

class StaticSitemap(Sitemap):
    priority = 1.0
    changefreq = "monthly"
    
    def __init__(self, language = None):
        self.language = language
        self.static_urls = {
            'index': 'core:index',
            'creation-sur-mesure': 'boutique:creation-sur-mesure',
            # 'a_propos': 'boutique:a_propos',
        }

    def items(self):
        return list(self.static_urls.keys())

    def location(self, item):
        with translation.override(self.language):
            return reverse(self.static_urls[item])
