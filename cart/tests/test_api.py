import json
import uuid
from unittest.mock import patch

import stripe
from django.test import Client, TestCase
from django.urls import reverse

from cart.models import Cart, CartItem
from cart.tests.helpers import make_product, make_stripe_checkout_event
from legal.choices import DocumentType
from legal.models import LegalDocument
from legal.tests import make_terms_document


class AddToCartTest(TestCase):
    """Tests for add_to_cart API view"""

    def setUp(self):
        self.client = Client()
        self.product = make_product(available=True)

    def test_rejects_non_post_requests(self):
        """Should reject GET requests with a 405"""
        response = self.client.get(
            reverse("cart_api:add_to_cart", args=[self.product.id])
        )
        self.assertEqual(response.status_code, 405)

    def test_adds_product_and_renders_card_when_available(self):
        """Should add the product and render the updated product card"""
        response = self.client.post(
            reverse("cart_api:add_to_cart", args=[self.product.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "catalog/components/_product_card.html")
        self.assertEqual(CartItem.objects.count(), 1)

    def test_marks_product_pending_on_success(self):
        """Should mark the product as pending in cart after adding it"""
        self.client.post(reverse("cart_api:add_to_cart", args=[self.product.id]))

        self.product.refresh_from_db()
        self.assertTrue(self.product.pending_in_cart)

    def test_returns_error_partial_when_product_unavailable(self):
        """Should render the error partial when the product isn't available"""
        self.product.available = False
        self.product.save()

        response = self.client.post(
            reverse("cart_api:add_to_cart", args=[self.product.id])
        )
        self.assertTemplateUsed(response, "core/components/_error.html")

    def test_returns_error_partial_when_product_pending(self):
        """Should render the error partial when the product is already pending"""
        self.product.pending_in_cart = True
        self.product.save()

        response = self.client.post(
            reverse("cart_api:add_to_cart", args=[self.product.id])
        )
        self.assertTemplateUsed(response, "core/components/_error.html")

    def test_triggers_cart_updated_event_on_success(self):
        """Should set the HX-Trigger header so the navbar count refreshes"""
        response = self.client.post(
            reverse("cart_api:add_to_cart", args=[self.product.id])
        )
        self.assertEqual(response.headers.get("HX-Trigger"), "cartUpdated")

    def test_does_not_trigger_cart_updated_on_error(self):
        """Should not set HX-Trigger when the product couldn't be added"""
        self.product.pending_in_cart = True
        self.product.save()

        response = self.client.post(
            reverse("cart_api:add_to_cart", args=[self.product.id])
        )
        self.assertIsNone(response.headers.get("HX-Trigger"))

    def test_returns_error_partial_when_product_not_found(self):
        """Should render the error partial when the product doesn't exist"""
        response = self.client.post(reverse("cart_api:add_to_cart", args=[9999]))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "core/components/_error.html")


class EmptyCartTest(TestCase):
    """Tests for empty_cart API view"""

    def setUp(self):
        self.client = Client()
        LegalDocument.objects.create(document_type=DocumentType.TERMS, version="1.0")

        session = self.client.session
        session.save()
        self.session_key = session.session_key

        self.product = make_product(pending_in_cart=True)
        self.cart = Cart.objects.create(session_id=self.session_key)
        self.cart_item = CartItem.objects.create(
            cart=self.cart, product=self.product, quantity=1
        )

    def test_rejects_non_post_requests(self):
        """Should reject GET requests with a 405"""
        response = self.client.get(reverse("cart_api:empty_cart"))
        self.assertEqual(response.status_code, 405)

    def test_returns_error_partial_when_no_session(self):
        """Should render the error partial when no session exists"""
        client = Client()  # fresh client, no session cookie at all
        response = client.post(reverse("cart_api:empty_cart"))
        self.assertTemplateUsed(response, "core/components/_error.html")

    def test_returns_error_partial_when_no_cart(self):
        """Should render the error partial when no cart exists for the session"""
        self.cart.delete()  # session exists, but its cart is gone
        response = self.client.post(reverse("cart_api:empty_cart"))
        self.assertTemplateUsed(response, "core/components/_error.html")

    def test_returns_error_partial_when_cart_already_empty(self):
        """Should render the error partial when the cart has no items"""
        self.cart_item.delete()  # cart exists, but it's empty
        response = self.client.post(reverse("cart_api:empty_cart"))
        self.assertTemplateUsed(response, "core/components/_error.html")

    def test_empties_cart_successfully(self):
        """Should delete the cart and render the updated (empty) cart content"""
        response = self.client.post(reverse("cart_api:empty_cart"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Cart.objects.filter(id=self.cart.id).count(), 0)
        self.assertTemplateUsed(response, "cart/components/_cart_content.html")

    def test_releases_product_on_success(self):
        """Should reset pending_in_cart on the product after emptying the cart"""
        self.client.post(reverse("cart_api:empty_cart"))

        self.product.refresh_from_db()
        self.assertFalse(self.product.pending_in_cart)

    def test_triggers_cart_updated_event_on_success(self):
        """Should set the HX-Trigger header so the navbar count refreshes"""
        response = self.client.post(reverse("cart_api:empty_cart"))
        self.assertEqual(response.headers.get("HX-Trigger"), "cartUpdated")

    def test_does_not_trigger_cart_updated_on_error(self):
        """Should not set HX-Trigger when there was nothing to empty"""
        self.cart_item.delete()
        response = self.client.post(reverse("cart_api:empty_cart"))
        self.assertIsNone(response.headers.get("HX-Trigger"))


class RemoveFromCartTest(TestCase):
    """Tests for remove_from_cart API view"""

    def setUp(self):
        self.client = Client()
        self.product = make_product()
        session = self.client.session
        session.save()
        self.cart = Cart.objects.create(session_id=session.session_key)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)
        LegalDocument.objects.create(document_type=DocumentType.TERMS, version="1.0")

    def test_rejects_non_post_requests(self):
        """Should reject GET requests with a 405"""
        response = self.client.get(
            reverse("cart_api:remove_from_cart", args=[self.product.id])
        )
        self.assertEqual(response.status_code, 405)

    def test_removes_product_successfully(self):
        """Should remove the cart item and render the updated cart content"""
        response = self.client.post(
            reverse("cart_api:remove_from_cart", args=[self.product.id])
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(CartItem.objects.count(), 0)
        self.assertTemplateUsed(response, "cart/components/_cart_content.html")

    def test_resets_pending_in_cart_on_product(self):
        """Should reset pending_in_cart on the product after removal"""
        self.product.pending_in_cart = True
        self.product.save()

        self.client.post(reverse("cart_api:remove_from_cart", args=[self.product.id]))

        self.product.refresh_from_db()
        self.assertFalse(self.product.pending_in_cart)

    def test_triggers_cart_updated_event(self):
        """Should set the HX-Trigger header so the navbar count refreshes"""
        response = self.client.post(
            reverse("cart_api:remove_from_cart", args=[self.product.id])
        )
        self.assertEqual(response.headers.get("HX-Trigger"), "cartUpdated")

    def test_returns_error_partial_when_no_session(self):
        """Should render the error partial when no session exists"""
        client = Client()  # fresh client without session
        response = client.post(
            reverse("cart_api:remove_from_cart", args=[self.product.id])
        )
        self.assertTemplateUsed(response, "core/components/_error.html")

    def test_returns_error_partial_when_cart_not_found(self):
        """Should render the error partial when the session has no active cart"""
        client = Client()
        session = client.session
        session.save()
        # session exists, but no Cart was ever created for it
        response = client.post(
            reverse("cart_api:remove_from_cart", args=[self.product.id])
        )
        self.assertTemplateUsed(response, "core/components/_error.html")

    def test_returns_error_partial_when_product_not_in_cart(self):
        """Should render the error partial when the product isn't in the cart"""
        response = self.client.post(reverse("cart_api:remove_from_cart", args=[9999]))
        self.assertTemplateUsed(response, "core/components/_error.html")

    def test_does_not_trigger_cart_updated_on_error(self):
        """Should not set HX-Trigger when the removal failed"""
        response = self.client.post(reverse("cart_api:remove_from_cart", args=[9999]))
        self.assertIsNone(response.headers.get("HX-Trigger"))


class CartCountTest(TestCase):
    """Tests for cart_count view"""

    def setUp(self):
        self.client = Client()

    def test_returns_zero_when_no_session(self):
        """Should return 0 when no session exists"""
        response = self.client.get(reverse("cart:cart_count"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.content), 0)

    def test_returns_correct_count(self):
        """Should return correct number of products"""
        session = self.client.session
        session.save()
        product1 = make_product(name="Product 1")
        product2 = make_product(name="Product 2")
        cart = Cart.objects.create(session_id=session.session_key)
        CartItem.objects.create(cart=cart, product=product1, quantity=1)
        CartItem.objects.create(cart=cart, product=product2, quantity=1)

        response = self.client.get(reverse("cart:cart_count"))
        self.assertEqual(int(response.content), 2)

    def test_returns_zero_for_paid_cart(self):
        """Should return 0 for paid cart"""
        session = self.client.session
        session.save()
        product = make_product()
        cart = Cart.objects.create(session_id=session.session_key, paid=True)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        response = self.client.get(reverse("cart:cart_count"))
        self.assertEqual(int(response.content), 0)


class CheckoutTest(TestCase):
    """Tests for checkout API view"""

    def setUp(self):
        self.client = Client()
        session = self.client.session
        session.save()
        self.product = make_product(price=100.0, discount=0.0)
        self.cart = Cart.objects.create(
            session_id=session.session_key, uuid=uuid.uuid4()
        )
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)

    def test_returns_error_when_no_cart_uuid(self):
        """Should return 400 when cart UUID is missing"""
        response = self.client.get(
            reverse("cart_api:checkout"),
            {
                "front_total": "105.00",
                "insurance": "0",
                "shipping": "0",
                "acceptCGV": "1",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_returns_error_when_cgv_not_accepted(self):
        """Should return 400 when CGV not accepted"""
        response = self.client.get(
            reverse("cart_api:checkout"),
            {
                "front_total": "105.00",
                "cart_uuid": str(self.cart.uuid),
                "insurance": "0",
                "shipping": "0",
                "acceptCGV": "0",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_returns_error_when_amount_mismatch(self):
        """Should return 400 when front total doesn't match back total"""
        make_terms_document()
        response = self.client.get(
            reverse("cart_api:checkout"),
            {
                "front_total": "999.00",  # wrong amount
                "cart_uuid": str(self.cart.uuid),
                "insurance": "0",
                "shipping": "0",
                "acceptCGV": "1",
            },
        )
        self.assertEqual(response.status_code, 400)

    def test_redirects_to_stripe_on_success(self):
        """Should redirect to Stripe URL on success"""
        make_terms_document()
        with patch(
            "cart.api.views.create_stripe_session",
            return_value="https://stripe.com/pay",
        ):
            with patch("cart.api.views.verify_total"):
                response = self.client.get(
                    reverse("cart_api:checkout"),
                    {
                        "front_total": "105.00",
                        "cart_uuid": str(self.cart.uuid),
                        "insurance": "0",
                        "shipping": "0",
                        "acceptCGV": "1",
                    },
                )
                self.assertRedirects(
                    response, "https://stripe.com/pay", fetch_redirect_response=False
                )


class StripeWebhookTest(TestCase):
    """Tests for stripe_webhook API view"""

    def setUp(self):
        self.client = Client()
        self.cart = Cart.objects.create(session_id="webhook_session", uuid=uuid.uuid4())

    def test_returns_400_on_invalid_payload(self):
        """Should return 400 on invalid payload"""
        with patch("stripe.Webhook.construct_event", side_effect=ValueError):
            response = self.client.post(
                reverse("cart_api:webhook_stripe"),
                data="invalid",
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400)

    def test_returns_400_on_invalid_signature(self):
        """Should return 400 on invalid signature"""
        with patch(
            "stripe.Webhook.construct_event",
            side_effect=stripe.SignatureVerificationError("", ""),
        ):
            response = self.client.post(
                reverse("cart_api:webhook_stripe"),
                data="invalid",
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400)

    def test_ignores_payment_link_events(self):
        """Should ignore payment link events"""
        event = {
            "type": "checkout.session.completed",
            "data": {"object": {"payment_link": "link_123", "metadata": {}}},
        }
        with patch("stripe.Webhook.construct_event", return_value=event):
            response = self.client.post(
                reverse("cart_api:webhook_stripe"),
                data=json.dumps(event),
                content_type="application/json",
            )
            self.assertEqual(response.json()["status"], "ignored - payment link")

    def test_returns_error_when_cart_uuid_missing(self):
        """Should return error when cart UUID is missing from metadata"""
        event = {
            "type": "checkout.session.completed",
            "data": {"object": {"metadata": {}}},
        }
        with patch("stripe.Webhook.construct_event", return_value=event):
            response = self.client.post(
                reverse("cart_api:webhook_stripe"),
                data=json.dumps(event),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 400)

    def test_processes_successful_payment(self):
        """Should process payment and send email on success"""
        event = make_stripe_checkout_event(str(self.cart.uuid))
        with patch("stripe.Webhook.construct_event", return_value=event):
            with patch("cart.api.views.send_email_to_owner") as mock_email:
                response = self.client.post(
                    reverse("cart_api:webhook_stripe"),
                    data=json.dumps(event),
                    content_type="application/json",
                )
                self.assertEqual(response.json()["status"], "success")
                mock_email.assert_called_once()
