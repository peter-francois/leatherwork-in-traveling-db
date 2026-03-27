from django.test import TestCase, Client
from django.urls import reverse
from .services import generate_sitemap_index


class IndexViewTest(TestCase):
    """Tests for the index/homepage view"""

    def setUp(self):
        self.client = Client()

    def test_returns_200(self):
        """Should return a 200 status code"""
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)

    def test_sets_csrf_cookie(self):
        """Should set a CSRF cookie (required for JS requests)"""
        response = self.client.get(reverse('core:index'))
        self.assertIn('csrftoken', response.cookies)

    def test_uses_correct_template(self):
        """Should render core/index.html"""
        response = self.client.get(reverse('core:index'))
        self.assertTemplateUsed(response, 'core/index.html')

class RobotsTxtTest(TestCase):
    """Tests for robots.txt SEO file"""

    def test_returns_200(self):
        """Should return a 200 status code"""
        response = self.client.get(reverse('robots_txt'))
        self.assertEqual(response.status_code, 200)

    def test_content_type_is_plain_text(self):
        """Should return a plain text content type"""
        response = self.client.get(reverse('robots_txt'))
        self.assertEqual(response['Content-Type'], 'text/plain')

    def test_disallows_admin(self):
        """Should disallow admin crawling"""
        response = self.client.get(reverse('robots_txt'))
        self.assertIn(b'Disallow: /admin/', response.content)

class GenerateSitemapIndexTest(TestCase):
    """Tests for the sitemap index XML generation service"""

    def test_returns_string(self):
        """Should return a string"""
        result = generate_sitemap_index('https://example.com/', ['fr', 'en'])
        self.assertIsInstance(result, str)

    def test_contains_xml_declaration(self):
        """Should start with XML declaration"""
        result = generate_sitemap_index('https://example.com/', ['fr', 'en'])
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', result)

    def test_contains_sitemapindex_tag(self):
        """Should contain sitemapindex root tag"""
        result = generate_sitemap_index('https://example.com/', ['fr', 'en'])
        self.assertIn('<sitemapindex', result)

    def test_generates_correct_urls(self):
        """Should generate one sitemap URL per language"""
        result = generate_sitemap_index('https://example.com/', ['fr', 'en'])
        self.assertIn('https://example.com/sitemap-fr.xml', result)
        self.assertIn('https://example.com/sitemap-en.xml', result)

    def test_single_language(self):
        """Should work with a single language"""
        result = generate_sitemap_index('https://example.com/', ['fr'])
        self.assertIn('sitemap-fr.xml', result)
        self.assertNotIn('sitemap-en.xml', result)

    def test_empty_langs(self):
        """Should return valid XML with no sitemaps for empty lang list"""
        result = generate_sitemap_index('https://example.com/', [])
        self.assertIn('<sitemapindex', result)
        self.assertNotIn('<sitemap>', result)