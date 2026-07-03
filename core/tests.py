from django.contrib.sessions.backends.db import SessionStore
from django.test import Client, RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone, translation

from catalog.models import Product
from catalog.tests import make_product
from core.sitemaps_category import CategorySitemap
from core.sitemaps_product_detail import ProductDetailSitemap

from .services import generate_sitemap_index, get_session_expiration


class IndexViewTest(TestCase):
    """Tests for the index/homepage view"""

    def setUp(self):
        self.client = Client()

    def test_returns_200(self):
        """Should return a 200 status code"""
        response = self.client.get(reverse("core:index"))
        self.assertEqual(response.status_code, 200)

    def test_sets_csrf_cookie(self):
        """Should set a CSRF cookie (required for JS requests)"""
        response = self.client.get(reverse("core:index"))
        self.assertIn("csrftoken", response.cookies)

    def test_uses_correct_template(self):
        """Should render core/index.html"""
        response = self.client.get(reverse("core:index"))
        self.assertTemplateUsed(response, "core/index.html")


class RobotsTxtTest(TestCase):
    """Tests for robots.txt SEO file"""

    def test_returns_200(self):
        """Should return a 200 status code"""
        response = self.client.get(reverse("robots_txt"))
        self.assertEqual(response.status_code, 200)

    def test_content_type_is_plain_text(self):
        """Should return a plain text content type"""
        response = self.client.get(reverse("robots_txt"))
        self.assertEqual(response["Content-Type"], "text/plain")

    def test_disallows_admin(self):
        """Should disallow admin crawling"""
        response = self.client.get(reverse("robots_txt"))
        self.assertIn(b"Disallow: /admin/", response.content)


class GenerateSitemapIndexTest(TestCase):
    """Tests for the sitemap index XML generation service"""

    def test_returns_string(self):
        """Should return a string"""
        result = generate_sitemap_index("https://example.com/", ["fr", "en"])
        self.assertIsInstance(result, str)

    def test_contains_xml_declaration(self):
        """Should start with XML declaration"""
        result = generate_sitemap_index("https://example.com/", ["fr", "en"])
        self.assertIn('<?xml version="1.0" encoding="UTF-8"?>', result)

    def test_contains_sitemapindex_tag(self):
        """Should contain sitemapindex root tag"""
        result = generate_sitemap_index("https://example.com/", ["fr", "en"])
        self.assertIn("<sitemapindex", result)

    def test_generates_correct_urls(self):
        """Should generate one sitemap URL per language"""
        result = generate_sitemap_index("https://example.com/", ["fr", "en"])
        self.assertIn("https://example.com/sitemap-fr.xml", result)
        self.assertIn("https://example.com/sitemap-en.xml", result)

    def test_single_language(self):
        """Should work with a single language"""
        result = generate_sitemap_index("https://example.com/", ["fr"])
        self.assertIn("sitemap-fr.xml", result)
        self.assertNotIn("sitemap-en.xml", result)

    def test_empty_langs(self):
        """Should return valid XML with no sitemaps for empty lang list"""
        result = generate_sitemap_index("https://example.com/", [])
        self.assertIn("<sitemapindex", result)
        self.assertNotIn("<sitemap>", result)


class GetSessionExpirationTest(TestCase):
    """Tests for the get_session_expiration service"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_returns_none_when_no_session_key(self):
        """Should return None when request has no session key"""
        request = self.factory.get("/")
        request.session = SessionStore()
        # SessionStore have no saved session
        result = get_session_expiration(request)
        self.assertIsNone(result)

    def test_returns_expiration_date_when_session_exists(self):
        """Should return the session expiration date"""
        # Create a session in db
        session = SessionStore()
        session.create()

        request = self.factory.get("/")
        request.session = session

        result = get_session_expiration(request)
        self.assertIsNotNone(result)
        self.assertIsInstance(result, timezone.datetime)

    def test_expiration_date_is_in_future(self):
        """Should return a future expiration date for active session"""
        session = SessionStore()
        session.create()

        request = self.factory.get("/")
        request.session = session

        result = get_session_expiration(request)

        self.assertIsNotNone(result)
        # Confirm to pytest that result is not None
        assert result is not None
        self.assertGreater(result, timezone.now())

    def test_returns_none_when_session_does_not_exist_in_db(self):
        """Should return None when session key exists but not in DB"""
        session = SessionStore()
        session._session_key = "fake_session_key_not_in_db"  # type: ignore # Force private attribute to simulate a non-existent session key

        request = self.factory.get("/")
        request.session = session

        result = get_session_expiration(request)
        self.assertIsNone(result)


class ProductDetailSitemapTest(TestCase):
    """Tests for ProductDetailSitemap"""

    def setUp(self):
        self.product = make_product(available=True)
        setattr(self.product, "name_fr", "Bracelet tressage magique")
        setattr(self.product, "name_en", "Magic braided bracket")
        self.product.save()

        self.sitemap_fr = ProductDetailSitemap(language="fr")
        self.sitemap_en = ProductDetailSitemap(language="en")

    def test_items_returns_all_products(self):
        """Should return all products"""
        self.assertEqual(
            list(self.sitemap_fr.items()),
            list(Product.objects.all()),
        )

    def test_lastmod_returns_updated_at(self):
        """Should return the product's updated_at date"""
        self.assertEqual(
            self.sitemap_fr.lastmod(self.product),
            self.product.updated_at,
        )

    def test_location_fr_uses_french_slug(self):
        """Should generate URL with French slug"""
        url = self.sitemap_fr.location(self.product)
        self.assertIn("bracelet-tressage-magique", url)
        self.assertIn(str(self.product.id), url)
        self.assertIn("maroquinerie", url)

    def test_location_en_uses_english_slug(self):
        """Should generate URL with English slug"""
        url = self.sitemap_en.location(self.product)
        self.assertIn("magic-braided-bracket", url)
        self.assertIn(str(self.product.id), url)

    def test_location_uses_lowercase_category(self):
        """Should use lowercase category in URL"""
        url = self.sitemap_fr.location(self.product)
        self.assertNotIn("Maroquinerie", url)
        self.assertIn("maroquinerie", url)

    def test_priority(self):
        """Should have priority 0.9"""
        self.assertEqual(self.sitemap_fr.priority, 0.9)

    def test_changefreq(self):
        """Should have weekly changefreq"""
        self.assertEqual(self.sitemap_fr.changefreq, "weekly")


class CategorySitemapTest(TestCase):
    """Tests for CategorySitemap"""

    def setUp(self):
        self.sitemap_fr = CategorySitemap(language="fr")
        self.sitemap_en = CategorySitemap(language="en")

    def test_items_returns_all_category_urls(self):
        """Should return all four category URL names"""
        items = self.sitemap_fr.items()
        self.assertIn("catalog:product_list", items)
        self.assertIn("catalog:leather_list", items)
        self.assertIn("catalog:macrame_list", items)
        self.assertIn("catalog:hybrid_list", items)
        self.assertEqual(len(items), 4)

    def test_location_fr_returns_french_url(self):
        """Should return French URL for product_list"""
        with translation.override("fr"):
            url = self.sitemap_fr.location("catalog:product_list")
        self.assertIn("/fr/", url)

    def test_location_en_returns_english_url(self):
        """Should return English URL for product_list"""
        with translation.override("en"):
            url = self.sitemap_en.location("catalog:product_list")
        self.assertIn("/en/", url)

    def test_priority(self):
        """Should have priority 0.8"""
        self.assertEqual(self.sitemap_fr.priority, 0.8)

    def test_changefreq(self):
        """Should have weekly changefreq"""
        self.assertEqual(self.sitemap_fr.changefreq, "weekly")

    def test_lastmod_returns_current_time(self):
        """Should return a recent datetime for lastmod"""
        from django.utils import timezone

        before = timezone.now()
        lastmod = self.sitemap_fr.lastmod("catalog:product_list")
        after = timezone.now()
        self.assertGreaterEqual(lastmod, before)
        self.assertLessEqual(lastmod, after)
