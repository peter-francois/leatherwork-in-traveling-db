from django.db import models
from cloudinary.models import CloudinaryField
from .choices import Category, ProductType
from django.utils.translation import gettext_lazy as _

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=58, verbose_name=_('Nom'), default='')
    category = models.CharField(max_length=50, choices=Category.choices, verbose_name=_('Catégorie'), default='')
    product_type = models.CharField(max_length=50, choices=ProductType.choices, verbose_name=_('Type'), default='')
    description = models.CharField(max_length=135, blank=True, null=True, verbose_name=_('Description'))
    price = models.FloatField(default=0.0, verbose_name=_('Prix'))
    discount = models.FloatField(default=0.0, verbose_name=_('Remise'))
    image1 = CloudinaryField(default='', blank=True, null=True, verbose_name=_('Image 1'))
    image2 = CloudinaryField(default='', blank=True, null=True, verbose_name=_('Image 2'))
    image3 = CloudinaryField(default='', blank=True, null=True, verbose_name=_('Image 3'))
    image4 = CloudinaryField(default='', blank=True, null=True, verbose_name=_('Image 4'))
    image5 = CloudinaryField(default='', blank=True, null=True, verbose_name=_('Image 5'))
    image6 = CloudinaryField(default='', blank=True, null=True, verbose_name=_('Image 6'))
    available = models.BooleanField(default=True, verbose_name=_('Disponible'))
    pending_in_cart = models.BooleanField(default=False, verbose_name=_('En attente dans panier'))
    on_demand = models.BooleanField(default=False, verbose_name=_('Sur commande'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Mis à jour le'))

    class Meta:
        verbose_name = _('Produit')
        verbose_name_plural = _('Produits')