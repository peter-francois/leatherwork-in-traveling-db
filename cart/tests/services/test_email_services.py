from unittest.mock import patch

from django.test import TestCase

from cart.services.email_services import _build_email_message, send_email_to_owner


class BuildEmailMessageTest(TestCase):
    """Tests for _build_email_message helper"""

    def setUp(self):
        self.shipping_address = {
            "country": "FR",
            "formatted_shipping_address": "1 rue de la Paix",
            "postal_code": "75001",
            "city": "Paris",
        }
        self.list_products = [
            {"name": "Product 1", "image_url": "http://example.com/img1.jpg"},
            {"name": "Product 2", "image_url": "http://example.com/img2.jpg"},
        ]

    def test_contains_customer_name(self):
        """Should contain customer name"""
        message = _build_email_message(
            "John Doe",
            "john@example.com",
            1,
            "uuid-123",
            "2024-01-01",
            self.shipping_address,
            "Oui",
            "Non",
            5.0,
            100.0,
            3.5,
            108.5,
            self.list_products,
        )
        self.assertIn("John Doe", message)

    def test_contains_order_id(self):
        """Should contain order ID"""
        message = _build_email_message(
            "John Doe",
            "john@example.com",
            42,
            "uuid-123",
            "2024-01-01",
            self.shipping_address,
            "Oui",
            "Non",
            5.0,
            100.0,
            3.5,
            108.5,
            self.list_products,
        )
        self.assertIn("42", message)

    def test_contains_product_names(self):
        """Should contain all product names"""
        message = _build_email_message(
            "John Doe",
            "john@example.com",
            1,
            "uuid-123",
            "2024-01-01",
            self.shipping_address,
            "Oui",
            "Non",
            5.0,
            100.0,
            3.5,
            108.5,
            self.list_products,
        )
        self.assertIn("Product 1", message)
        self.assertIn("Product 2", message)

    def test_contains_shipping_address(self):
        """Should contain shipping address details"""
        message = _build_email_message(
            "John Doe",
            "john@example.com",
            1,
            "uuid-123",
            "2024-01-01",
            self.shipping_address,
            "Oui",
            "Non",
            5.0,
            100.0,
            3.5,
            108.5,
            self.list_products,
        )
        self.assertIn("1 rue de la Paix", message)
        self.assertIn("Paris", message)
        self.assertIn("75001", message)

    def test_contains_totals(self):
        """Should contain order totals"""
        message = _build_email_message(
            "John Doe",
            "john@example.com",
            1,
            "uuid-123",
            "2024-01-01",
            self.shipping_address,
            "Oui",
            "Non",
            5.0,
            100.0,
            3.5,
            108.5,
            self.list_products,
        )
        self.assertIn("100.0", message)
        self.assertIn("108.5", message)

    def test_handles_invalid_product(self):
        """Should handle invalid product gracefully"""
        invalid_products = [{"name": "Valid product"}, "invalid_string"]
        message = _build_email_message(
            "John Doe",
            "john@example.com",
            1,
            "uuid-123",
            "2024-01-01",
            self.shipping_address,
            "Non",
            "Non",
            5.0,
            100.0,
            0.0,
            105.0,
            invalid_products,
        )
        self.assertIn("Valid product", message)
        self.assertIn("Error with product", message)


class SendEmailToOwnerTest(TestCase):
    """Tests for send_email_to_owner service"""

    def setUp(self):
        self.shipping_address = {
            "country": "FR",
            "formatted_shipping_address": "1 rue de la Paix",
            "postal_code": "75001",
            "city": "Paris",
        }
        self.list_products = [
            {"name": "Product 1", "image_url": "http://example.com/img1.jpg"},
        ]
        self.base_kwargs = {
            "customer_email": "customer@example.com",
            "customer_name": "John Doe",
            "shipping_address": self.shipping_address,
            "list_products": self.list_products,
            "cart_uuid": "uuid-123",
            "total_articles_centimes": 10000,
            "cgv_version": "2024-01-01",
            "is_optional_insurance": "False",
            "total_verified_centimes": 10500,
            "order_id": 1,
            "is_home_delivery": "False",
        }

    def test_does_not_send_when_list_products_is_none(self):
        """Should not send email when list_products is None"""
        with patch("cart.services.email_services.send_mail") as mock_send:
            send_email_to_owner(**{**self.base_kwargs, "list_products": None})
            mock_send.assert_not_called()

    def test_sends_email_with_valid_data(self):
        """Should send email when all data is valid"""
        with patch("cart.services.email_services.send_mail") as mock_send:
            send_email_to_owner(**self.base_kwargs)
            mock_send.assert_called_once()

    def test_sends_to_correct_recipient(self):
        """Should send email to CLIENT_EMAIL"""
        with patch("cart.services.email_services.send_mail") as mock_send:
            with patch("cart.services.email_services.settings") as mock_settings:
                mock_settings.CLIENT_EMAIL = "owner@example.com"
                mock_settings.EMAIL_HOST_USER = "host@example.com"
                send_email_to_owner(**self.base_kwargs)
                call_args = mock_send.call_args
                first_client_email_arg = call_args[0][3]
                self.assertIn("owner@example.com", first_client_email_arg)

    def test_handles_send_mail_exception(self):
        """Should log error and not raise when send_mail fails"""
        with patch(
            "cart.services.email_services.send_mail",
            side_effect=Exception("SMTP error"),
        ):
            try:
                send_email_to_owner(**self.base_kwargs)
            except Exception:
                self.fail("send_email_to_owner raised an exception unexpectedly")

    def test_insurance_is_oui_when_mandatory(self):
        """Should set insurance to Oui when total exceeds mandatory threshold"""
        with patch("cart.services.email_services.send_mail"):
            with patch(
                "cart.services.email_services._build_email_message"
            ) as mock_build:
                mock_build.return_value = "<html></html>"
                send_email_to_owner(
                    **{**self.base_kwargs, "total_articles_centimes": 6000}
                )
                call_args = mock_build.call_args[0]
                insurance_arg = call_args[6]
                self.assertEqual(insurance_arg, "Oui")

    def test_shipping_cost_is_express_when_is_home_delivery(self):
        """Should use express shipping cost when is_home_delivery is True"""
        with patch("cart.services.email_services.send_mail"):
            with patch(
                "cart.services.email_services._build_email_message"
            ) as mock_build:
                mock_build.return_value = "<html></html>"
                send_email_to_owner(**{**self.base_kwargs, "is_home_delivery": "True"})
                call_args = mock_build.call_args[0]
                shipping_cost_arg = call_args[8]
                self.assertEqual(
                    shipping_cost_arg, 10.0
                )  # HOME_DELIVERY_SHIPPING_COST / 100

    def test_shipping_cost_is_standard_when_no_shipping(self):
        """Should use standard shipping cost when is_home_delivery is False"""
        with patch("cart.services.email_services.send_mail"):
            with patch(
                "cart.services.email_services._build_email_message"
            ) as mock_build:
                mock_build.return_value = "<html></html>"
                send_email_to_owner(**self.base_kwargs)
                call_args = mock_build.call_args[0]
                shipping_cost_arg = call_args[8]
                self.assertEqual(shipping_cost_arg, 5.0)  # STANDARD_SHIPPING_COST / 100
