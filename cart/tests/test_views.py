from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from cart.models import Cart, CartItem
from catalog.models import Product
from legal.choices import DocumentType
from legal.models import LegalDocument
from legal.tests import make_terms_document


class CartViewTest(TestCase):
    """Tests for the cart view"""

    def setUp(self):
        self.client = Client()
        self.cgv = make_terms_document()

    def test_returns_200(self):
        """Should return 200"""
        response = self.client.get(reverse("cart:cart"))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        """Should render cart/cart.html"""
        response = self.client.get(reverse("cart:cart"))
        self.assertTemplateUsed(response, "cart/cart.html")

    def test_empty_cart_when_no_session(self):
        """Should return empty items when no session exists"""
        response = self.client.get(reverse("cart:cart"))
        self.assertEqual(list(response.context["items"]), [])
        self.assertEqual(response.context["total"], 0)

    def test_cart_with_items(self):
        """Should return items and correct total when cart exists"""
        session = self.client.session
        session.save()
        product = Product.objects.create(
            name="Test Product",
            category="Maroquinerie",
            price=100,
            discount=10,
            available=True,
        )
        cart = Cart.objects.create(session_id=session.session_key)
        CartItem.objects.create(cart=cart, product=product, quantity=2)

        response = self.client.get(reverse("cart:cart"))
        self.assertEqual(response.context["total"], 180)  # (100-10) * 2

    def test_latest_cgv_in_context(self):
        """Should pass latest CGV to template"""
        future = timezone.now() + timedelta(days=180)
        with patch("django.utils.timezone.now", return_value=future):
            new_doc = LegalDocument.objects.create(
                document_type=DocumentType.TERMS,
                version="2024-06-01",
                content_fr="Nouveau contenu",
                content_en="New content",
            )
        response = self.client.get(reverse("cart:cart"))
        self.assertEqual(response.context["latest_cgv"].version, new_doc.version)


class SuccessViewTest(TestCase):
    """Tests for the success view"""

    def test_redirects_when_no_session_id(self):
        """Should redirect to home when no session_id"""
        response = self.client.get(reverse("cart:success"))
        self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_redirects_on_stripe_error(self):
        """Should redirect to home on Stripe error"""
        with patch("cart.views.get_stripe_session") as mock:
            mock.side_effect = ValueError("Stripe error")
            response = self.client.get(reverse("cart:success"), {"session_id": "fake"})
            self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_redirects_on_invalid_payment(self):
        """Should redirect to home when payment not completed"""
        with patch("cart.views.get_stripe_session") as mock:
            mock.side_effect = ValueError("Payment not completed")
            response = self.client.get(reverse("cart:success"), {"session_id": "fake"})
            self.assertRedirects(response, "/", fetch_redirect_response=False)

    def test_returns_200_on_valid_session(self):
        """Should return 200 with valid Stripe session"""
        cart = Cart.objects.create(
            session_id="test_session",
            paid=True,
        )
        mock_session = MagicMock()
        mock_session.amount_total = 10000

        with patch(
            "cart.views.get_stripe_session", return_value=(mock_session, cart.uuid)
        ):
            response = self.client.get(
                reverse("cart:success"), {"session_id": "valid_id"}
            )
            self.assertEqual(response.status_code, 200)
            self.assertTemplateUsed(response, "cart/success.html")

    def test_context_contains_order_data(self):
        """Should pass order data to template"""
        cart = Cart.objects.create(session_id="test_session", paid=True)
        mock_session = MagicMock()
        mock_session.amount_total = 10000

        with patch(
            "cart.views.get_stripe_session", return_value=(mock_session, cart.uuid)
        ):
            response = self.client.get(
                reverse("cart:success"), {"session_id": "valid_id"}
            )
            self.assertEqual(response.context["order_id"], cart.id)
            self.assertEqual(response.context["total_amount"], 100.0)


class CancelViewTest(TestCase):
    """Tests for the cancel view"""

    def test_returns_200(self):
        """Should return 200"""
        response = self.client.get(reverse("cart:cancel"))
        self.assertEqual(response.status_code, 200)

    def test_uses_correct_template(self):
        """Should render cart/cancel.html"""
        response = self.client.get(reverse("cart:cancel"))
        self.assertTemplateUsed(response, "cart/cancel.html")
