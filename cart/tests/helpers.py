from django.utils.timezone import now
from django.contrib.sessions.models import Session
from cart.models import Cart
from catalog.models import Product
from catalog.choices import Category, ProductType
from django.core.management import call_command
from io import StringIO

def make_product(**kwargs) -> Product:
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


def make_session(expire_delta) -> Session:
    """Create a Session expiring in expire_delta from now."""
    return Session.objects.create(
        session_key=f'test_session_{now().timestamp()}',
        session_data='{}',
        expire_date=now() + expire_delta,
    )


def make_cart(session, paid=False, **kwargs) -> Cart:
    """Create a Cart linked to a session."""
    return Cart.objects.create(
        session_id=session.session_key,
        paid=paid,
        **kwargs,
    )

def call_management_command(command: str) -> str:
    """Call a management command and return stdout."""
    out = StringIO()
    call_command(command, stdout=out)
    return out.getvalue()