from django.db import models
from cloudinary.models import CloudinaryField
from .choices import Category, ProductType

class Product(models.Model):
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=58)
    categorie = models.CharField(max_length=50, choices=Category.choices)
    type = models.CharField(max_length=50, choices=ProductType.choices)
    description = models.CharField(max_length=135, blank=True, null=True)
    prix = models.FloatField(default=0.0)
    discount = models.FloatField(default=0.0)
    image1 = CloudinaryField(default='', blank=True, null=True)
    image2 = CloudinaryField(default='', blank=True, null=True)
    image3 = CloudinaryField(default='', blank=True, null=True)
    image4 = CloudinaryField(default='', blank=True, null=True)
    image5 = CloudinaryField(default='', blank=True, null=True)
    image6 = CloudinaryField(default='', blank=True, null=True)
    disponible = models.BooleanField(default=True)
    en_attente_dans_panier = models.BooleanField(default=False)
    sur_commande = models.BooleanField(default=False)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def nouveau_prix(self):
        return self.prix - self.discount

    def __str__(self):
        return self.nom