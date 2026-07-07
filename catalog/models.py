from cloudinary.models import CloudinaryField
from django.db import models
from django.utils.text import slugify

from .choices import Category, ProductType


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, verbose_name="Nom", default="")
    category = models.CharField(
        max_length=50, choices=Category.choices, verbose_name="Catégorie", default=""
    )
    product_type = models.CharField(
        max_length=50, choices=ProductType.choices, verbose_name="Type", default=""
    )
    meta_description = models.CharField(
        default="", max_length=135, blank=True, verbose_name="Meta-description"
    )
    description = models.CharField(
        default="", max_length=300, blank=True, verbose_name="Description"
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
    slug = models.SlugField(max_length=150, blank=True)
    seo_ready = models.BooleanField(default=False, verbose_name="Prêt pour le SEO")

    class Meta:
        verbose_name = "Produit"
        verbose_name_plural = "Produits"

    def __str__(self):
        return f"Product {self.id}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def image_urls(self):
        return [
            img.url
            for img in [
                self.image1,
                self.image2,
                self.image3,
                self.image4,
                self.image5,
                self.image6,
            ]
            if img
        ]
