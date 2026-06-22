from cloudinary.models import CloudinaryField
from django.db import models

from .choices import Category, ProductType


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=58, verbose_name="Nom", default="")
    category = models.CharField(
        max_length=50, choices=Category.choices, verbose_name="Catégorie", default=""
    )
    product_type = models.CharField(
        max_length=50, choices=ProductType.choices, verbose_name="Type", default=""
    )
    description = models.CharField(
        default="", max_length=135, blank=True, verbose_name="Description"
    )
    price = models.FloatField(default=0.0, verbose_name="Prix")
    discount = models.FloatField(default=0.0, verbose_name="Remise")
    image1 = CloudinaryField(default="", blank=True, null=True, verbose_name="Image 1")
    image2 = CloudinaryField(default="", blank=True, null=True, verbose_name="Image 2")
    image3 = CloudinaryField(default="", blank=True, null=True, verbose_name="Image 3")
    image4 = CloudinaryField(default="", blank=True, null=True, verbose_name="Image 4")
    image5 = CloudinaryField(default="", blank=True, null=True, verbose_name="Image 5")
    image6 = CloudinaryField(default="", blank=True, null=True, verbose_name="Image 6")
    available = models.BooleanField(default=True, verbose_name="Disponible")
    pending_in_cart = models.BooleanField(
        default=False, verbose_name="En attente dans panier"
    )
    on_demand = models.BooleanField(default=False, verbose_name="Sur commande")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Mis à jour le")

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    def __str__(self):
        return f"Product {self.id}"
