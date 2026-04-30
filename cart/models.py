from django.db import models
import uuid
from catalog.models import Product
from legal.models import LegalDocument

class Cart(models.Model):
    session_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4,unique=True, editable=False)
    cgv_accepted  = models.ForeignKey(LegalDocument, on_delete=models.PROTECT, null=True, limit_choices_to={'document_type': 'terms'},related_name='carts',)
    cgv_accepted_at = models.DateTimeField(null=True, blank=True)
    cgv_expires_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    cart_expires_at = models.DateTimeField(null=True, blank=True)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)
    def get_total(self):
        return sum((item.product.prix - item.product.discount) * item.quantity for item in self.cartitem_set.all())
    def __str__(self):
        return f"Cart {self.uuid}"

class CartItem(models.Model):
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)
