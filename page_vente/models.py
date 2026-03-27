from django.db import models
import uuid
from cloudinary.models import CloudinaryField
from django.core.validators import RegexValidator

class AllProducts(models.Model):

    CATEGORY_CHOICES = [
        ('Hybride', 'Hybride'),
        ('Macrame', 'Macrame'),
        ('Maroquinerie', 'Maroquinerie'),
    ]
    TYPE_CHOICES = [

        ('Blague à tabac', 'Blague à tabac'),
        ('Boucles d\'oreilles', 'Boucles d\'oreilles'),
        ('Bracelet', 'Bracelet'),
        ('Ceinture', 'Ceinture'),
        ('Chaine de corps', 'Chaine de corps'),
        ('Chevillère', 'Chevillère'),
        ('Collier', 'Collier'),
        ('Collier chien', 'Collier chien'),
        ('Divers', 'Divers'),
        ('Entretien', 'Entretien'),
        ('Murale', 'Murale'),
        ('Portefeuille, Porte carte', 'Portefeuille, Porte carte'),
        ('Sac divers', 'Sac divers'),
    ]
    id = models.AutoField(primary_key=True)
    nom = models.CharField(max_length=58)
    categorie = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
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
    
class Cart(models.Model):
    session_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    uuid = models.UUIDField(default=uuid.uuid4,unique=True, editable=False)
    cgv_accepted = models.ForeignKey('CGV', on_delete=models.PROTECT, null=True, blank=True)
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
    product = models.ForeignKey(AllProducts, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

class CGV(models.Model):
    version_validator = RegexValidator(regex=r'^\d{4}-\d{2}-\d{2}$', message="Format de version incorrect, utilisez YYYY-MM-DD.")
    version = models.CharField(max_length=20, unique=True, help_text="Ex : 2024-06-01", validators=[version_validator])
    content_fr = models.TextField(default='', help_text="Texte complet des CGV en français")
    content_en = models.TextField(default='', help_text="Texte complet des CGV en anglais")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"CGV {self.version}"

    class Meta:
        ordering = ['-created_at']

class CookiesPolicy(models.Model):
    version_validator = RegexValidator(regex=r'^\d{4}-\d{2}-\d{2}$', message="Format de version incorrect, utilisez YYYY-MM-DD.")
    version = models.CharField(max_length=20, unique=True, help_text="Ex : 2024-06-01", validators=[version_validator])
    content_fr = models.TextField(default='', help_text="Texte complet des cookies en français")
    content_en = models.TextField(default='', help_text="Texte complet des cookies en anglais")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Cookies Policy {self.version}"

    class Meta:
        ordering = ['-created_at']

class LegalMention(models.Model):
    version_validator = RegexValidator(regex=r'^\d{4}-\d{2}-\d{2}$', message="Format de version incorrect, utilisez YYYY-MM-DD.")
    version = models.CharField(max_length=20, unique=True, help_text="Ex : 2024-06-01", validators=[version_validator])
    content_fr = models.TextField(default='', help_text="Texte complet des mentions légales en français")
    content_en = models.TextField(default='', help_text="Texte complet des mentions légales en anglais")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Legal Mentions {self.version}"

    class Meta:
        ordering = ['-created_at']

class PrivacyPolicy(models.Model):
    version_validator = RegexValidator(regex=r'^\d{4}-\d{2}-\d{2}$', message="Format de version incorrect, utilisez YYYY-MM-DD.")
    version = models.CharField(max_length=20, unique=True, help_text="Ex : 2024-06-01", validators=[version_validator])
    content_fr = models.TextField(default='', help_text="Texte complet de la politique de confidentialité en français")
    content_en = models.TextField(default='', help_text="Texte complet de la politique de confidentialité en anglais")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Privacy Policy {self.version}"

    class Meta:
        ordering = ['-created_at']