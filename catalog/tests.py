from django.test import TestCase, RequestFactory
from django.urls import reverse
from .models import Product
from .choices import Category, ProductType
from .services import use_filter, pagination
from .constants import PRODUCTS_PER_PAGE


# ── Helpers ───────────────────────────────────────────────────────────────────

def make_product(**kwargs):
    """Create a Product with sensible defaults, overridable via kwargs."""
    defaults = {
        'name': 'Test product',
        'category': Category.MAROQUINERIE,
        'product_type': ProductType.BRACELET,
        'price': 50.0,
        'discount': 0.0,
        'available': True,
        'pending_in_cart': False,
        'on_demand': False,
    }
    defaults.update(kwargs)
    return Product.objects.create(**defaults)


# ── use_filter ────────────────────────────────────────────────────────────────

class UseFilterTestCase(TestCase):
    """Tests for the use_filter utility function."""

    def setUp(self):
        """Create a base set of products for filter tests."""
        self.factory = RequestFactory()
        self.p1 = make_product(name='Bracelet rouge', price=30.0, product_type=ProductType.BRACELET)
        self.p2 = make_product(name='Collier bleu', price=60.0, product_type=ProductType.COLLIER)
        self.p3 = make_product(name='Sac noir', price=100.0, product_type=ProductType.SAC_DIVERS)
        self.products = list(Product.objects.filter(available=True))

    def _request(self, params=None):
        """Build a GET request with optional query params."""
        return self.factory.get('/', params)

    def test_empty_products_returns_early(self):
        """Should return immediately with empty results when no products given."""
        request = self._request()
        result, form, count, filter_used = use_filter(request, [], is_all_products=True)
        self.assertEqual(result, [])
        self.assertIsNone(form)
        self.assertEqual(count, 0)
        self.assertFalse(filter_used)

    def test_no_filter_returns_all(self):
        """Should return all products when no filter params are provided."""
        request = self._request()
        result, form, count, filter_used = use_filter(request, self.products, is_all_products=True)
        self.assertEqual(count, len(self.products))
        self.assertFalse(filter_used)

    def test_search_filter(self):
        """Should filter products by name (case-insensitive)."""
        request = self._request({'search': 'bracelet'})
        result, _, count, filter_used = use_filter(request, self.products, is_all_products=True)
        self.assertEqual(count, 1)
        self.assertEqual(result[0], self.p1) # p1 = 'Bracelet rouge'
        self.assertTrue(filter_used)

    def test_product_type_filter(self):
        """Should filter products by product_type."""
        request = self._request({'product_type': ProductType.COLLIER})
        result, _, count, filter_used = use_filter(request, self.products, is_all_products=True)
        self.assertEqual(count, 1)
        self.assertEqual(result[0], self.p2) # p2.product_type = ProductType.COLLIER
        self.assertTrue(filter_used)

    def test_min_price_filter(self):
        """Should exclude products below min_price."""
        min_price = 50
        request = self._request({'min_price': min_price})
        result, _, count, filter_used = use_filter(request, self.products, is_all_products=True)
        self.assertEqual(count, 2)
        self.assertGreaterEqual(result[0].price, min_price)  # p2 = 60.0
        self.assertGreaterEqual(result[1].price, min_price)  # p3 = 100.0
        self.assertTrue(filter_used)

    def test_max_price_filter(self):
        """Should exclude products above max_price."""
        max_price = 60
        request = self._request({'max_price': max_price})
        result, _, count, filter_used = use_filter(request, self.products, is_all_products=True)
        self.assertEqual(count, 2)
        self.assertLessEqual(result[0].price, max_price)  # p1 = 30.0
        self.assertLessEqual(result[1].price, max_price)  # p2 = 60.0
        self.assertTrue(filter_used)

    def test_sort_by_price_asc(self):
        """Should return products sorted by price ascending."""
        request = self._request({'sort_by_price': 'price'})
        result, _, _, _ = use_filter(request, self.products, is_all_products=True)
        prices = [p.price for p in result]
        self.assertEqual(prices, sorted(prices))

    def test_sort_by_price_desc(self):
        """Should return products sorted by price descending."""
        request = self._request({'sort_by_price': '-price'})
        result, _, _, _ = use_filter(request, self.products, is_all_products=True)
        prices = [p.price for p in result]
        self.assertEqual(prices, sorted(prices, reverse=True))

    def test_category_filter_is_all_products_false(self):
        """Should return all products unchanged when no filter and is_all_products is False."""
        request = self._request()
        result, _, count, _ = use_filter(request, self.products, is_all_products=False)
        self.assertEqual(count, 3)
        self.assertEqual(result[0], self.p1)
        self.assertEqual(result[1], self.p2)
        self.assertEqual(result[2], self.p3)


# ── pagination ────────────────────────────────────────────────────────────────

class PaginationTestCase(TestCase):
    """Tests for the pagination utility function."""

    def setUp(self):
        """Create enough products to span multiple pages."""
        self.factory = RequestFactory()
        for i in range(30):
            make_product(name=f'Product {i}', price=10.0)

    def test_first_page_has_correct_count(self):
        """First page should contain exactly PRODUCTS_PER_PAGE items."""
        request = self.factory.get('/')
        products = list(Product.objects.filter(available=True))
        page = pagination(request, products)
        self.assertEqual(len(page.object_list), PRODUCTS_PER_PAGE)

    def test_second_page(self):
        """Second page should exist and have a previous page."""
        request = self.factory.get('/', {'page': 2})
        products = list(Product.objects.filter(available=True))
        page = pagination(request, products)
        self.assertTrue(page.has_previous())


# ── Views ─────────────────────────────────────────────────────────────────────

class CatalogViewsTestCase(TestCase):
    """Integration tests for catalog views."""

    def setUp(self):
        """Create one product per category."""
        make_product(name='Bracelet test', category=Category.MAROQUINERIE, price=40.0)
        make_product(name='Collier macramé', category=Category.MACRAME, price=25.0)
        make_product(name='Sac hybride', category=Category.HYBRIDE, price=80.0)

    def test_produits_view(self):
        """Products page should return 200 and include products in context."""
        response = self.client.get(reverse('catalog:product_list'))
        self.assertEqual(response.status_code, 200)
        self.assertIn('products', response.context)

    def test_maroquinerie_view(self):
        """Leather page should only show Maroquinerie products."""
        response = self.client.get(reverse('catalog:leather_list'))
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'].object_list)
        self.assertTrue(all(p.category == Category.MAROQUINERIE for p in products))

    def test_macrames_view(self):
        """Macrame page should only show Macrame products."""
        response = self.client.get(reverse('catalog:macrame_list'))
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'].object_list)
        self.assertTrue(all(p.category == Category.MACRAME for p in products))

    def test_hybride_view(self):
        """Hybrid page should only show Hybride products."""
        response = self.client.get(reverse('catalog:hybrid_list'))
        self.assertEqual(response.status_code, 200)
        products = list(response.context['products'].object_list)
        self.assertTrue(all(p.category == Category.HYBRIDE for p in products))

    def test_unavailable_product_not_shown(self):
        """Unavailable products should never appear in any listing."""
        make_product(name='Invisible', available=False, category=Category.MAROQUINERIE)
        response = self.client.get(reverse('catalog:leather_list'))
        products = list(response.context['products'].object_list)
        self.assertFalse(any(p.name == 'Invisible' for p in products))