from unittest.mock import Mock, patch
from django.test import TestCase
from cart.services.stripe_services import (
    StripeAmountError,
    StripeMetadataError,
    StripePaymentNotCompletedError,
    StripeSessionUrlMissingError,
    create_stripe_session,
    build_metadata,
    get_stripe_session,
    extract_session_data,
    _parse_list_products,
    _format_shipping_address,
    StripeSessionError,
)
import stripe
import json
import uuid


class CreateStripeSessionTest(TestCase):
    """Tests for create_stripe_session"""

    @patch("cart.services.stripe_services.stripe.checkout.Session.create")
    def test_returns_session_url_when_successful(self, mock_create):
        """Should return Stripe session URL when creation succeeds"""

        cart = Mock()
        cart.cartitem_set.count.return_value = 2

        mock_session = Mock()
        mock_session.url = "https://stripe-session-url"
        mock_create.return_value = mock_session

        result = create_stripe_session(
            cart=cart,
            metadata={"cart_uuid": "123"},
            success_url="https://success.com",
            cancel_url="https://cancel.com",
            total_centimes=1000,
        )

        self.assertEqual(result, "https://stripe-session-url")

    @patch("cart.services.stripe_services.stripe.checkout.Session.create")
    def test_raises_StripeSessionUrlMissingError_when_session_url_is_missing(self, mock_create):
        """Should raise StripeSessionUrlMissingError when Stripe session URL is missing"""

        cart = Mock()
        cart.cartitem_set.count.return_value = 1

        mock_session = Mock()
        mock_session.url = None
        mock_create.return_value = mock_session

        with self.assertRaises(StripeSessionUrlMissingError):
            create_stripe_session(
                cart=cart,
                metadata={},
                success_url="https://success.com",
                cancel_url="https://cancel.com",
                total_centimes=1000,
            )

    @patch("cart.services.stripe_services.stripe.checkout.Session.create")
    def test_raises_stripe_session_error_when_stripe_fails(self, mock_create):
        """Should raise StripeSessionError on Stripe API error"""

        cart = Mock()
        cart.cartitem_set.count.return_value = 1

        mock_create.side_effect = stripe.StripeError("Stripe failure")

        with self.assertRaises(StripeSessionError):
            create_stripe_session(
                cart=cart,
                metadata={},
                success_url="https://success.com",
                cancel_url="https://cancel.com",
                total_centimes=1000,
            )


class BuildMetadataTest(TestCase):
    """Tests for build_metadata"""

    @patch("cart.services.stripe_services._build_product_list")
    def test_returns_valid_metadata(self, mock_build_product_list):
        """Should return formatted metadata dictionary"""

        mock_build_product_list.return_value = [{"name": "Product"}]

        cart = Mock()
        cart.uuid = uuid.uuid4()

        cart.cgv_accepted.version = "v1"

        result = build_metadata(
            cart=cart,
            is_optional_insurance=True,
            is_home_delivery=False,
            total_centimes=2000,
            total_articles_centimes=1500,
            accepted_terms_version= cart.cgv_accepted.version
        )

        self.assertEqual(result["cart_uuid"], str(cart.uuid))
        self.assertEqual(result["is_optional_insurance"], "True")
        self.assertEqual(result["is_home_delivery"], "False")
        self.assertEqual(result["total_verified_centimes"], "2000")
        self.assertEqual(result["total_articles_centimes"], "1500")
        self.assertEqual(result["cgv_version"], "v1")
        self.assertEqual(
            json.loads(result["list_products"]),
            [{"name": "Product"}]
        )


class GetStripeSessionTest(TestCase):
    """Tests for get_stripe_session"""

    @patch("cart.services.stripe_services.stripe.checkout.Session.retrieve")
    def test_returns_session_and_cart_uuid_when_valid(self, mock_retrieve):
        """Should return session and parsed cart UUID"""

        cart_uuid = uuid.uuid4()

        session = Mock()
        session.payment_status = "paid"
        session.metadata = {"cart_uuid": str(cart_uuid)}
        session.amount_total = 1000

        mock_retrieve.return_value = session

        result_session, result_uuid = get_stripe_session("session_id")

        self.assertEqual(result_session, session)
        self.assertEqual(result_uuid, cart_uuid)

    @patch("cart.services.stripe_services.stripe.checkout.Session.retrieve")
    def test_raises_StripePaymentNotCompletedError_when_payment_not_completed(self, mock_retrieve):
        """Should raise StripePaymentNotCompletedError when payment is not paid"""

        session = Mock()
        session.payment_status = "unpaid"
        session.metadata = {"cart_uuid": str(uuid.uuid4())}
        session.amount_total = 1000

        mock_retrieve.return_value = session

        with self.assertRaises(StripePaymentNotCompletedError):
            get_stripe_session("session_id")

    @patch("cart.services.stripe_services.stripe.checkout.Session.retrieve")
    def test_raises_StripeMetadataError_when_metadata_is_missing(self, mock_retrieve):
        """Should raise StripeMetadataError when metadata is invalid"""

        session = Mock()
        session.payment_status = "paid"
        session.metadata = {}
        session.amount_total = 1000

        mock_retrieve.return_value = session

        with self.assertRaises(StripeMetadataError):
            get_stripe_session("session_id")

    @patch("cart.services.stripe_services.stripe.checkout.Session.retrieve")
    def test_raises_StripeMetadataError_when_cart_uuid_is_invalid(self, mock_retrieve):
        """Should raise StripeMetadataError when cart UUID is invalid"""

        session = Mock()
        session.payment_status = "paid"
        session.metadata = {"cart_uuid": "invalid-uuid"}
        session.amount_total = 1000

        mock_retrieve.return_value = session

        with self.assertRaises(StripeMetadataError):
            get_stripe_session("session_id")

    @patch("cart.services.stripe_services.stripe.checkout.Session.retrieve")
    def test_raises_StripeAmountError_when_amount_total_is_missing(self, mock_retrieve):
        """Should raise StripeAmountError when amount_total is None"""

        session = Mock()
        session.payment_status = "paid"
        session.metadata = {"cart_uuid": str(uuid.uuid4())}
        session.amount_total = None

        mock_retrieve.return_value = session

        with self.assertRaises(StripeAmountError):
            get_stripe_session("session_id")


class ExtractSessionDataTest(TestCase):
    """Tests for extract_session_data"""

    def test_extracts_session_data_correctly(self):
        """Should return formatted session data"""

        metadata = {
            "list_products": json.dumps([{"name": "Product"}]),
            "cart_uuid": "123",
            "total_articles_centimes": "1000",
            "cgv_version": "v1",
            "is_optional_insurance": "True",
            "is_home_delivery": "False",
            "total_verified_centimes": "1200",
        }

        session = {
            "customer_details": {
                "email": "test@test.com",
                "name": "John Doe",
            },
            "collected_information": {
                "shipping_details": {
                    "address": {
                        "line1": "10 rue test",
                        "line2": "Batiment A",
                    }
                }
            }
        }

        result = extract_session_data(session, metadata)

        self.assertEqual(result["customer_email"], "test@test.com")
        self.assertEqual(result["customer_name"], "John Doe")
        self.assertEqual(result["cart_uuid"], "123")
        self.assertEqual(result["total_articles_centimes"], 1000)
        self.assertEqual(result["total_verified_centimes"], 1200)
        self.assertEqual(
            result["shipping_address"]["formatted_shipping_address"],
            "10 rue test, Batiment A"
        )


class ParseListProductsTest(TestCase):
    """Tests for _parse_list_products"""

    def test_returns_list_when_json_string_is_valid(self):
        """Should deserialize valid JSON string"""

        result = _parse_list_products('[{"name": "Product"}]')

        self.assertEqual(result, [{"name": "Product"}])

    def test_returns_none_when_json_is_invalid(self):
        """Should return None when JSON is invalid"""

        result = _parse_list_products("invalid-json")

        self.assertIsNone(result)

    def test_returns_none_when_value_is_not_list(self):
        """Should return None when parsed value is not a list"""

        result = _parse_list_products('{"name": "Product"}')

        self.assertIsNone(result)


class FormatShippingAddressTest(TestCase):
    """Tests for _format_shipping_address"""

    def test_formats_address_with_line2(self):
        """Should include line2 in formatted address"""

        address = {
            "line1": "10 rue test",
            "line2": "Batiment A",
        }

        result = _format_shipping_address(address)

        self.assertEqual(
            result["formatted_shipping_address"],
            "10 rue test, Batiment A"
        )

    def test_formats_address_without_line2(self):
        """Should only use line1 when line2 is missing"""

        address = {
            "line1": "10 rue test",
        }

        result = _format_shipping_address(address)

        self.assertEqual(
            result["formatted_shipping_address"],
            "10 rue test"
        )

    def test_formats_unknown_address_when_line1_missing(self):
        """Should fallback to Unknown when line1 is missing"""

        address = {}

        result = _format_shipping_address(address)

        self.assertEqual(
            result["formatted_shipping_address"],
            "Unknown"
        )