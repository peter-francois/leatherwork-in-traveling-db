from django.http import HttpResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie
from core.sitemaps import StaticSitemap
from core.sitemaps_paginated import PaginatedCategorySitemap
from django.contrib.sitemaps.views import sitemap as django_sitemap
from .services import generate_sitemap_index

@ensure_csrf_cookie
def index(request):
    return render(request, 'core/index.html')

def contact(request):
    return render(request, 'core/contact.html')

def about(request):
    return render(request, 'core/about.html')

def sitemap_lang(request, lang):
    sitemaps = {
        'static': StaticSitemap(lang),
        'paginated_categories': PaginatedCategorySitemap(lang),
    }
    return django_sitemap(request, sitemaps)

def sitemap_index(request):
    base_url = request.build_absolute_uri('/')
    xml = generate_sitemap_index(base_url, ['fr', 'en'])
    return HttpResponse(xml, content_type='application/xml')

def robots_txt(request):
    return HttpResponse(
        "User-agent: *\nDisallow: /admin/\nDisallow: /private/\nSitemap: https://www.leatherworkintravelingdb.com/sitemap.xml",
        content_type='text/plain'
    )