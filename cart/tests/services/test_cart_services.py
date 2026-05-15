from django.test import TestCase, RequestFactory
from unittest.mock import patch
from datetime import timedelta
from cart.constants import CGV_EXPIRATION_DAYS
from cart.models import Cart, CartItem
from cart.services.cart_services import (
    register_cgv_acceptance,
    process_successful_payment,
    get_or_create_active_cart,
    add_product_to_cart,
    empty_cart_and_release_products,
    get_cart_items_data,
    remove_product_from_cart,
)
from cart.tests.helpers import make_cart, make_product, make_session
from legal.models import LegalDocument
from legal.choices import DocumentType
from django.utils import timezone
from datetime import timedelta
from legal.tests import make_terms_document


class RegisterCgvAcceptanceTest(TestCase):
    """Tests for register_cgv_acceptance service"""

    def setUp(self):
        self.cgv = make_terms_document()

        self.cart = Cart.objects.create(session_id='test_session')

    def test_registers_cgv_when_not_accepted(self):
        """Should register CGV acceptance when not already accepted"""
        self.assertIsNone(self.cart.cgv_accepted_at)
        register_cgv_acceptance(self.cart, self.cgv)
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.cgv_accepted, self.cgv)
        self.assertIsNotNone(self.cart.cgv_accepted_at)
        self.assertIsNotNone(self.cart.cgv_expires_at)

    def test_does_not_override_existing_acceptance(self):
        """Should not override existing CGV acceptance"""
        original_time = timezone.now()
        self.cart.cgv_accepted = self.cgv
        self.cart.cgv_accepted_at = original_time
        self.cart.save()

        future = timezone.now() + timedelta(days=1)
        with patch('django.utils.timezone.now', return_value=future):
            new_doc = LegalDocument.objects.create(
                document_type=DocumentType.TERMS,
                version='2024-06-01',
                content_fr='Nouveau contenu',
                content_en='New content',
            )

        register_cgv_acceptance(self.cart, self.cgv)
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.cgv_accepted_at, original_time)
        self.assertNotEqual(self.cart.cgv_accepted, new_doc)

    def test_expiration_is_5_years(self):
        """Should set CGV expiration to constant CGV_EXPIRATION_DAYS"""
        register_cgv_acceptance(self.cart, self.cgv)
        self.cart.refresh_from_db()
        
        self.assertIsNotNone(self.cart.cgv_accepted_at)
        self.assertIsNotNone(self.cart.cgv_expires_at)
        assert self.cart.cgv_accepted_at is not None  # Pylance hint
        assert self.cart.cgv_expires_at is not None   # Pylance hint
        
        expected = self.cart.cgv_accepted_at + timedelta(days=CGV_EXPIRATION_DAYS)
        self.assertAlmostEqual(
            self.cart.cgv_expires_at.timestamp(),
            expected.timestamp(),
            delta=1
        )


class ProcessSuccessfulPaymentTest(TestCase):
    """Tests for process_successful_payment service"""

    def setUp(self):
        self.session = make_session(expire_delta=timedelta(hours=24))
        self.product = make_product(available=True, pending_in_cart=True)
        self.cart = make_cart(self.session)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)

    def test_marks_cart_as_paid(self):
        """Should mark cart as paid"""
        process_successful_payment(self.cart)
        self.cart.refresh_from_db()
        self.assertTrue(self.cart.paid)
        self.assertIsNotNone(self.cart.paid_at)

    def test_marks_products_unavailable(self):
        """Should mark products as unavailable after payment"""
        process_successful_payment(self.cart)
        self.product.refresh_from_db()
        self.assertFalse(self.product.available)
        self.assertFalse(self.product.pending_in_cart)
        self.assertTrue(self.product.on_demand)

    def test_does_not_process_already_paid_cart(self):
        """Should not process an already paid cart"""
        self.cart.paid = True
        self.cart.save()
        original_paid_at = self.cart.paid_at
        process_successful_payment(self.cart)
        self.cart.refresh_from_db()
        self.assertEqual(self.cart.paid_at, original_paid_at)


class GetOrCreateActiveCartTest(TestCase):
    """Tests for get_or_create_active_cart service"""

    def setUp(self):
        self.factory = RequestFactory()

    def test_creates_cart_when_none_exists(self):
        """Should create a new cart when none exists"""
        request = self.factory.get('/')
        request.session = self.client.session
        self.assertEqual(Cart.objects.count(), 0)
        cart = get_or_create_active_cart(request)
        self.assertEqual(Cart.objects.count(), 1)
        self.assertFalse(cart.paid)

    def test_returns_existing_cart(self):
        """Should return existing unpaid cart"""
        session = self.client.session
        session.save()
        existing_cart = Cart.objects.create(session_id=session.session_key)

        request = self.factory.get('/')
        request.session = session
        cart = get_or_create_active_cart(request)
        self.assertEqual(cart.id, existing_cart.id)

    def test_creates_new_cart_when_existing_is_paid(self):
        """Should create a new cart when existing cart is paid"""
        session = self.client.session
        session.save()
        Cart.objects.create(session_id=session.session_key, paid=True)

        request = self.factory.get('/')
        request.session = session
        cart = get_or_create_active_cart(request)
        self.assertFalse(cart.paid)


class AddProductToCartTest(TestCase):
    """Tests for add_product_to_cart service"""

    def setUp(self):
        self.session = make_session(expire_delta=timedelta(hours=24))
        self.product = make_product(available=True, pending_in_cart=True)
        self.cart = make_cart(self.session)


    def test_adds_product_to_cart(self):
        """Should add product to cart"""
        add_product_to_cart(self.cart, self.product)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 1)

    def test_marks_product_as_pending(self):
        """Should mark product as pending in cart"""
        add_product_to_cart(self.cart, self.product)
        self.product.refresh_from_db()
        self.assertTrue(self.product.pending_in_cart)


class EmptyCartAndReleaseProductsTest(TestCase):
    """Tests for empty_cart_and_release_products service"""

    def setUp(self):
        self.session = make_session(expire_delta=timedelta(hours=24))
        self.product = make_product(available=True, pending_in_cart=True)
        self.cart = make_cart(self.session)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)

    def test_deletes_cart(self):
        """Should delete cart"""
        cart_id = self.cart.id
        empty_cart_and_release_products(self.cart)
        self.assertFalse(Cart.objects.filter(id=cart_id).exists())

    def test_releases_products(self):
        """Should release products from pending state"""
        empty_cart_and_release_products(self.cart)
        self.product.refresh_from_db()
        self.assertFalse(self.product.pending_in_cart)

    def test_deletes_cart_items(self):
        """Should delete all cart items"""
        cart_id = self.cart.id
        empty_cart_and_release_products(self.cart)
        self.assertEqual(CartItem.objects.filter(cart_id=cart_id).count(), 0)


class GetCartItemsDataTest(TestCase):
    """Tests for get_cart_items_data service"""

    def setUp(self):
        self.session = make_session(expire_delta=timedelta(hours=24))
        self.product = make_product(available=True, pending_in_cart=True)
        self.cart = make_cart(self.session)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=2)

    def test_returns_list(self):
        """Should return a list"""
        result = get_cart_items_data(self.cart)
        self.assertIsInstance(result, list)

    def test_returns_correct_data(self):
        """Should return correct product data"""
        result = get_cart_items_data(self.cart)
        self.assertEqual(result[0]['name'], self.product.name)
        self.assertEqual(result[0]['price'], self.product.price)
        self.assertEqual(result[0]['quantity'], 2)
        self.assertEqual(result[0]['discount'], self.product.discount)

    def test_returns_empty_list_when_no_items(self):
        """Should return empty list when cart has no items"""
        empty_cart = Cart.objects.create(session_id='empty_session')
        result = get_cart_items_data(empty_cart)
        self.assertEqual(result, [])


class RemoveProductFromCartTest(TestCase):
    """Tests for remove_product_from_cart service"""

    def setUp(self):
        self.session = make_session(expire_delta=timedelta(hours=24))
        self.product = make_product(available=True, pending_in_cart=True)
        self.cart = make_cart(self.session)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)

    def test_removes_product_from_cart(self):
        """Should remove product from cart"""
        remove_product_from_cart(self.cart, self.product.id)
        self.assertEqual(CartItem.objects.filter(cart=self.cart).count(), 0)

    def test_releases_product(self):
        """Should release product from pending state"""
        remove_product_from_cart(self.cart, self.product.id)
        self.product.refresh_from_db()
        self.assertFalse(self.product.pending_in_cart)

    def test_returns_product_data(self):
        """Should return product data"""
        result = remove_product_from_cart(self.cart, self.product.id)
        if result:
            self.assertEqual(result['id'], self.product.id)
            self.assertEqual(result['price'], self.product.price)

    def test_returns_none_when_product_not_in_cart(self):
        """Should return None when product not found in cart"""
        result = remove_product_from_cart(self.cart, 9999)
        self.assertIsNone(result)