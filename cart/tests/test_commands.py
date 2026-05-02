from django.test import TestCase
from django.utils.timezone import now
from django.contrib.sessions.models import Session
from django.core.management import call_command
from datetime import timedelta
from io import StringIO
from cart.models import Cart, CartItem
from catalog.models import Product
from catalog.choices import Category, ProductType


# ── Helpers ───────────────────────────────────────────────────────────────────

def _call_command(self, command):
    """Call the command and return stdout."""
    out = StringIO()
    call_command(command, stdout=out)
    return out.getvalue()

def make_product(**kwargs):
    """Create a Product with sensible defaults."""
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


def make_session(expire_delta):
    """Create a Session expiring in expire_delta from now."""
    session = Session.objects.create(
        session_key=f'test_session_{now().timestamp()}',
        session_data='{}',
        expire_date=now() + expire_delta,
    )
    return session


def make_cart(session, paid=False, **kwargs):
    """Create a Cart linked to a session."""
    return Cart.objects.create(
        session_id=session.session_key,
        paid=paid,
        **kwargs,
    )


# ── release_expiring_carts ────────────────────────────────────────────────────

class ReleaseExpiringCartsCommandTest(TestCase):
    """Tests for the release_expiring_carts management command."""
    command = 'release_expiring_carts'

    def test_no_expiring_sessions(self):
        """Should report nothing to release when no sessions are expiring."""
        # Session expires in 24h — well outside the 1h threshold
        make_session(expire_delta=timedelta(hours=24))
        output = _call_command(self, self.command)
        self.assertIn("Aucun panier expiré à libérer", output)

    def test_no_carts_for_expiring_session(self):
        """Should report nothing when expiring session has no associated cart."""
        make_session(expire_delta=timedelta(minutes=30))
        output = _call_command(self, self.command)
        self.assertIn("Aucun panier à libérer", output)

    def test_paid_cart_not_deleted(self):
        """Should not delete carts that are already paid."""
        session = make_session(expire_delta=timedelta(minutes=30))
        make_cart(session, paid=True)
        _call_command(self, self.command)
        self.assertEqual(Cart.objects.count(), 1)  # cart still exists

    def test_unpaid_cart_deleted(self):
        """Should delete unpaid carts linked to expiring sessions."""
        session = make_session(expire_delta=timedelta(minutes=30))
        make_cart(session, paid=False)
        _call_command(self, self.command)
        self.assertEqual(Cart.objects.count(), 0)

    def test_product_pending_in_cart_released(self):
        """Should set pending_in_cart=False for products in expiring carts."""
        session = make_session(expire_delta=timedelta(minutes=30))
        cart = make_cart(session, paid=False)
        product = make_product(pending_in_cart=True)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        _call_command(self, self.command)

        product.refresh_from_db()
        self.assertFalse(product.pending_in_cart)

    def test_product_not_pending_unchanged(self):
        """Should not modify products that are not pending in cart."""
        session = make_session(expire_delta=timedelta(minutes=30))
        cart = make_cart(session, paid=False)
        product = make_product(pending_in_cart=False)
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        _call_command(self, self.command)

        product.refresh_from_db()
        self.assertFalse(product.pending_in_cart)

    def test_session_deleted_after_command(self):
        """Should delete expiring sessions after processing."""
        session = make_session(expire_delta=timedelta(minutes=30))
        make_cart(session, paid=False)
        _call_command(self, self.command)
        self.assertFalse(Session.objects.filter(session_key=session.session_key).exists())

    def test_output_reports_correct_counts(self):
        """Should report correct number of products liberated and carts deleted."""
        session = make_session(expire_delta=timedelta(minutes=30))
        cart = make_cart(session, paid=False)
        product1 = make_product(pending_in_cart=True)
        product2 = make_product(pending_in_cart=True)
        CartItem.objects.create(cart=cart, product=product1, quantity=1)
        CartItem.objects.create(cart=cart, product=product2, quantity=1)

        output = _call_command(self, self.command)

        self.assertIn("2 produit(s) libéré(s)", output)
        self.assertIn("1 panier(s) supprimé(s)", output)

class ReleaseExpiringCarts10YearsCommandTest(TestCase):
    """Tests for the release_expiring_carts_10_years management command."""
    command = 'release_expiring_carts_10_years'

    def test_no_expired_carts(self):
        """Should report nothing to delete when no carts have expired."""
        Cart.objects.create(
            cart_expires_at=now() + timedelta(days=365),
        )
        output = _call_command(self, self.command)
        self.assertIn("Aucun panier expiré à supprimer", output)
        self.assertEqual(Cart.objects.count(), 1)

    def test_expired_cart_deleted(self):
        """Should delete carts whose cart_expires_at is in the past."""
        Cart.objects.create(
            cart_expires_at=now() - timedelta(days=1),
        )
        output = _call_command(self, self.command)
        self.assertIn("1 panier(s) supprimé(s)", output)
        self.assertEqual(Cart.objects.count(), 0)

    def test_cart_items_deleted_by_cascade(self):
        """Should delete CartItems automatically via CASCADE when cart is deleted."""
        cart = Cart.objects.create(
            cart_expires_at=now() - timedelta(days=1),
        )
        product = make_product()
        CartItem.objects.create(cart=cart, product=product, quantity=1)

        _call_command(self, self.command)

        self.assertEqual(Cart.objects.count(), 0)
        self.assertEqual(CartItem.objects.count(), 0)

    def test_non_expired_cart_not_deleted(self):
        """Should not delete carts that have not yet expired."""
        Cart.objects.create(cart_expires_at=now() + timedelta(days=365))
        Cart.objects.create(cart_expires_at=now() - timedelta(days=1))

        _call_command(self, self.command)

        self.assertEqual(Cart.objects.count(), 1)  # only the future one remains

    def test_output_reports_correct_count(self):
        """Should report the correct number of deleted carts."""
        for i in range(3):
            Cart.objects.create(cart_expires_at=now() - timedelta(days=i + 1))

        output = _call_command(self, self.command)

        self.assertIn("3 panier(s) supprimé(s)", output)


# ── release_expiring_term_acceptation ────────────────────────────────────────

class ReleaseExpiringCGVCommandTest(TestCase):
    """Tests for the release_expiring_CGV_Acceptation management command."""
    command = 'release_expiring_terms_acceptation'

    def test_no_expired_cgv(self):
        """Should report nothing when no CGV have expired."""
        Cart.objects.create(
            cgv_expires_at=now() + timedelta(days=365),
        )
        output = _call_command(self, self.command)
        self.assertIn("Aucun CGV expiré à libérer", output)

    def test_expired_cgv_reset(self):
        """Should reset CGV fields for carts whose CGV have expired."""
        cart = Cart.objects.create(
            cgv_expires_at=now() - timedelta(days=1),
            cgv_accepted_at=now() - timedelta(days=365),
        )
        _call_command(self, self.command)

        cart.refresh_from_db()
        self.assertIsNone(cart.cgv_accepted)
        self.assertIsNone(cart.cgv_accepted_at)
        self.assertIsNone(cart.cgv_expires_at)

    def test_non_expired_cgv_unchanged(self):
        """Should not modify carts whose CGV have not yet expired."""
        cgv_expires_at = now() + timedelta(days=365)
        cart = Cart.objects.create(cgv_expires_at=cgv_expires_at)

        _call_command(self, self.command)

        cart.refresh_from_db()
        self.assertEqual(cart.cgv_expires_at, cgv_expires_at)

    def test_cart_not_deleted(self):
        """Should reset CGV fields but not delete the cart."""
        Cart.objects.create(cgv_expires_at=now() - timedelta(days=1))
        _call_command(self, self.command)
        self.assertEqual(Cart.objects.count(), 1)

    def test_output_reports_correct_count(self):
        """Should report the correct number of carts reset."""
        for i in range(3):
            Cart.objects.create(cgv_expires_at=now() - timedelta(days=i + 1))

        output = _call_command(self, self.command)

        self.assertIn("3 panier(s)", output)