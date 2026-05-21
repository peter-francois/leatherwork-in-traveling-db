from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch
import stripe
from cart.models import Cart, CartItem
from cart.tests.helpers import make_product, make_session, make_stripe_checkout_event
from datetime import timedelta
import json
import uuid
from legal.tests import make_terms_document


class AddToCartTest(TestCase):
    """Tests for add_to_cart API view"""

    def setUp(self):
        self.client = Client()
        self.session = make_session(expire_delta=timedelta(hours=24))
        self.product = make_product()

    def test_returns_success_when_product_available(self):
        """Should return success when product is available"""
        response = self.client.post(
            reverse('cart_api:add_to_cart', args=[self.product.id])
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])

    def test_returns_error_when_product_unavailable(self):
        """Should return 400 when product is not available"""
        self.product.available = False
        self.product.save()
        response = self.client.post(
            reverse('cart_api:add_to_cart', args=[self.product.id])
        )
        self.assertEqual(response.status_code, 400)
        self.assertFalse(response.json()['success'])

    def test_returns_error_when_product_pending(self):
        """Should return 400 when product is pending in cart"""
        self.product.pending_in_cart = True
        self.product.save()
        response = self.client.post(
            reverse('cart_api:add_to_cart', args=[self.product.id])
        )
        self.assertEqual(response.status_code, 400)

    def test_returns_cart_uuid(self):
        """Should return cart UUID in response"""
        response = self.client.post(
            reverse('cart_api:add_to_cart', args=[self.product.id])
        )
        self.assertIn('cart_uuid', response.json())

    def test_returns_404_when_product_not_found(self):
        """Should return 404 when product does not exist"""
        response = self.client.post(
            reverse('cart_api:add_to_cart', args=[9999])
        )
        self.assertEqual(response.status_code, 404)


class CartDetailTest(TestCase):
    """Tests for cart_detail API view"""

    def setUp(self):
        self.client = Client()

    def test_returns_empty_cart_when_no_session(self):
        """Should return empty cart when no session exists"""
        response = self.client.get(reverse('cart_api:cart_detail'))
        self.assertEqual(response.json(), {'cart': []})

    def test_returns_empty_cart_when_no_cart(self):
        """Should return empty cart when no cart exists for session"""
        session = self.client.session
        session.save()
        response = self.client.get(reverse('cart_api:cart_detail'))
        self.assertEqual(response.json(), {'cart': []})

    def test_returns_cart_items(self):
        """Should return cart items when cart exists"""
        session = self.client.session
        session.save()
        product = make_product()
        cart = Cart.objects.create(session_id=session.session_key)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        response = self.client.get(reverse('cart_api:cart_detail'))
        data = response.json()
        self.assertEqual(len(data['cart']), 1)
        self.assertEqual(data['cart'][0]['name'], product.name)


class EmptyCartTest(TestCase):
    """Tests for empty_cart API view"""

    def setUp(self):
        self.client = Client()

    def test_returns_error_when_no_session(self):
        """Should return error when no session exists"""
        response = self.client.post(reverse('cart_api:empty_cart'))
        self.assertFalse(response.json()['success'])

    def test_returns_error_when_no_cart(self):
        """Should return error when no cart exists"""
        session = self.client.session
        session.save()
        response = self.client.post(reverse('cart_api:empty_cart'))
        self.assertFalse(response.json()['success'])

    def test_empties_cart_successfully(self):
        """Should empty cart and return success"""
        session = self.client.session
        session.save()
        product = make_product()
        cart = Cart.objects.create(session_id=session.session_key)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        response = self.client.post(reverse('cart_api:empty_cart'))
        self.assertTrue(response.json()['success'])
        self.assertEqual(Cart.objects.count(), 0)


class RemoveFromCartTest(TestCase):
    """Tests for remove_from_cart API view"""

    def setUp(self):
        self.client = Client()
        self.product = make_product()
        session = self.client.session
        session.save()
        self.cart = Cart.objects.create(session_id=session.session_key)
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)

    def test_removes_product_successfully(self):
        """Should remove product and return success"""
        response = self.client.post(
            reverse('cart_api:remove_from_cart', args=[self.product.id])
        )
        self.assertTrue(response.json()['success'])
        self.assertEqual(CartItem.objects.count(), 0)

    def test_returns_error_when_no_session(self):
        """Should return error when no session exists"""
        client = Client()  # fresh client without session
        response = client.post(
            reverse('cart_api:remove_from_cart', args=[self.product.id])
        )
        self.assertFalse(response.json()['success'])

    def test_returns_error_when_product_not_in_cart(self):
        """Should return error when product not in cart"""
        response = self.client.post(
            reverse('cart_api:remove_from_cart', args=[9999])
        )
        self.assertFalse(response.json()['success'])

    def test_returns_product_data(self):
        """Should return product data in response"""
        response = self.client.post(
            reverse('cart_api:remove_from_cart', args=[self.product.id])
        )
        data = response.json()
        self.assertIn('article', data)
        self.assertEqual(data['article']['id'], self.product.id)


class CartCountTest(TestCase):
    """Tests for cart_count view"""

    def setUp(self):
        self.client = Client()

    def test_returns_zero_when_no_session(self):
        """Should return 0 when no session exists"""
        response = self.client.get(reverse('cart:cart_count'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(response.content), 0)

    def test_returns_correct_count(self):
        """Should return correct number of products"""
        session = self.client.session
        session.save()
        product1 = make_product(name='Product 1')
        product2 = make_product(name='Product 2')
        cart = Cart.objects.create(session_id=session.session_key)
        CartItem.objects.create(cart=cart, product=product1, quantity=1)
        CartItem.objects.create(cart=cart, product=product2, quantity=1)

        response = self.client.get(reverse('cart:cart_count'))
        self.assertEqual(int(response.content), 2)

    def test_returns_zero_for_paid_cart(self):
        """Should return 0 for paid cart"""
        session = self.client.session
        session.save()
        product = make_product()
        cart = Cart.objects.create(session_id=session.session_key, paid=True)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        response = self.client.get(reverse('cart:cart_count'))
        self.assertEqual(int(response.content), 0)


class CheckoutTest(TestCase):
    """Tests for checkout API view"""

    def setUp(self):
        self.client = Client()
        session = self.client.session
        session.save()
        self.product = make_product(price=100.0, discount=0.0)
        self.cart = Cart.objects.create(
            session_id=session.session_key,
            uuid=uuid.uuid4()
        )
        CartItem.objects.create(cart=self.cart, product=self.product, quantity=1)

    def test_returns_error_when_no_cart_uuid(self):
        """Should return 400 when cart UUID is missing"""
        response = self.client.get(reverse('cart_api:checkout'), {
            'front_total': '105.00',
            'insurance': '0',
            'shipping': '0',
            'acceptCGV': '1',
        })
        self.assertEqual(response.status_code, 400)

    def test_returns_error_when_cgv_not_accepted(self):
        """Should return 400 when CGV not accepted"""
        response = self.client.get(reverse('cart_api:checkout'), {
            'front_total': '105.00',
            'cart_uuid': str(self.cart.uuid),
            'insurance': '0',
            'shipping': '0',
            'acceptCGV': '0',
        })
        self.assertEqual(response.status_code, 400)

    def test_returns_error_when_amount_mismatch(self):
        """Should return 400 when front total doesn't match back total"""
        make_terms_document()
        response = self.client.get(reverse('cart_api:checkout'), {
            'front_total': '999.00',  # wrong amount
            'cart_uuid': str(self.cart.uuid),
            'insurance': '0',
            'shipping': '0',
            'acceptCGV': '1',
        })
        self.assertEqual(response.status_code, 400)

    def test_redirects_to_stripe_on_success(self):
        """Should redirect to Stripe URL on success"""
        make_terms_document()
        with patch('cart.api.views.create_stripe_session', return_value='https://stripe.com/pay'):
            with patch('cart.api.views.verify_total'):
                response = self.client.get(reverse('cart_api:checkout'), {
                    'front_total': '105.00',
                    'cart_uuid': str(self.cart.uuid),
                    'insurance': '0',
                    'shipping': '0',
                    'acceptCGV': '1',
                })
                self.assertRedirects(
                    response,
                    'https://stripe.com/pay',
                    fetch_redirect_response=False
                )


class StripeWebhookTest(TestCase):
    """Tests for stripe_webhook API view"""

    def setUp(self):
        self.client = Client()
        self.cart = Cart.objects.create(
            session_id='webhook_session',
            uuid=uuid.uuid4()
        )

    def test_returns_400_on_invalid_payload(self):
        """Should return 400 on invalid payload"""
        with patch('stripe.Webhook.construct_event', side_effect=ValueError):
            response = self.client.post(
                reverse('cart_api:webhook_stripe'),
                data='invalid',
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 400)

    def test_returns_400_on_invalid_signature(self):
        """Should return 400 on invalid signature"""
        with patch('stripe.Webhook.construct_event',
                   side_effect=stripe.SignatureVerificationError('', '')):
            response = self.client.post(
                reverse('cart_api:webhook_stripe'),
                data='invalid',
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 400)

    def test_ignores_payment_link_events(self):
        """Should ignore payment link events"""
        event = {
            'type': 'checkout.session.completed',
            'data': {'object': {'payment_link': 'link_123', 'metadata': {}}}
        }
        with patch('stripe.Webhook.construct_event', return_value=event):
            response = self.client.post(
                reverse('cart_api:webhook_stripe'),
                data=json.dumps(event),
                content_type='application/json',
            )
            self.assertEqual(response.json()['status'], 'ignored - payment link')

    def test_returns_error_when_cart_uuid_missing(self):
        """Should return error when cart UUID is missing from metadata"""
        event = {
            'type': 'checkout.session.completed',
            'data': {'object': {'metadata': {}}}
        }
        with patch('stripe.Webhook.construct_event', return_value=event):
            response = self.client.post(
                reverse('cart_api:webhook_stripe'),
                data=json.dumps(event),
                content_type='application/json',
            )
            self.assertEqual(response.status_code, 400)

    def test_processes_successful_payment(self):
        """Should process payment and send email on success"""
        event = make_stripe_checkout_event(str(self.cart.uuid))
        with patch('stripe.Webhook.construct_event', return_value=event):
            with patch('cart.api.views.send_email_to_owner') as mock_email:
                response = self.client.post(
                    reverse('cart_api:webhook_stripe'),
                    data=json.dumps(event),
                    content_type='application/json',
                )
                self.assertEqual(response.json()['status'], 'success')
                mock_email.assert_called_once()