from django.contrib import admin
from .models import *
from django.contrib import messages
from .forms import *
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.utils.html import format_html



class AllProductsForm(forms.ModelForm):
    class Meta:
        model = AllProducts
        fields = '__all__'

    def clean(self):
        cleaned_data = super().clean()
        for field in ['image1', 'image2', 'image3', 'image4', 'image5', 'image6']:
            image_file = cleaned_data.get(field)
            if image_file:
                if hasattr(image_file, 'size') and image_file.size > 10 * 1024 * 1024:  # 10 Mo
                    raise ValidationError({field: _('Le fichier est trop volumineux. La taille maximale est de 10 Mo.')})
        return cleaned_data

def image_thumbnail(image_field):
    if image_field:
        return format_html('<img src="{}" width="100" height="100" style="object-fit: cover;" />', image_field.url)
    return "Aucune image"

class AllProductsAdmin(admin.ModelAdmin):
    actions = ['rendre_disponible', 'rendre_indisponible','retirer_du_panier']
    list_display = ('nom','categorie','disponible','en_attente_dans_panier','sur_commande', 'type', 'description', 'prix')
    search_fields = ['nom','categorie', 'type']
    list_filter = ['categorie', 'disponible']
    form = AllProductsForm
    list_per_page = 20
    readonly_fields = ('image1_thumbnail', 'image2_thumbnail', 'image3_thumbnail', 'image4_thumbnail', 'image5_thumbnail', 'image6_thumbnail')
    fieldsets = (
        (None, {
            'fields': ('nom', 'categorie', 'type', 'description', 'prix', 'discount', 'disponible', 'en_attente_dans_panier', 'sur_commande')
        }),
        ('Images', {
            'fields': ('image1', 'image1_thumbnail', 'image2', 'image2_thumbnail', 
                      'image3', 'image3_thumbnail', 'image4', 'image4_thumbnail',
                      'image5','image5_thumbnail', 'image6', 'image6_thumbnail')
        }),
    )

    def image1_thumbnail(self, obj):
        return image_thumbnail(obj.image1)
    image1_thumbnail.short_description = 'Miniature 1'

    def image2_thumbnail(self, obj):
        return image_thumbnail(obj.image2)
    image2_thumbnail.short_description = 'Miniature 2'

    def image3_thumbnail(self, obj):
        return image_thumbnail(obj.image3)
    image3_thumbnail.short_description = 'Miniature 3'

    def image4_thumbnail(self, obj):
        return image_thumbnail(obj.image4)
    image4_thumbnail.short_description = 'Miniature 4'

    def image5_thumbnail(self, obj):
        return image_thumbnail(obj.image5)
    image5_thumbnail.short_description = 'Miniature 5'

    def image6_thumbnail(self, obj):
        return image_thumbnail(obj.image6)
    image6_thumbnail.short_description = 'Miniature 6'

    def rendre_disponible(self,  request, queryset):
        queryset.update(disponible=True)

    def rendre_indisponible(self, request, queryset):
        queryset.update(disponible=False)

    def retirer_du_panier(self, request, queryset):
        articles_id = list(queryset.values_list('id', flat=True))

        with transaction.atomic():
            # Suppression des articles du panier liés aux produits
            deleted_count, _ = CartItem.objects.filter(product__in=articles_id).delete()

            # Mise à jour du statut en attente
            queryset.update(en_attente_dans_panier=False)

        # Message pour l’utilisateur
        if deleted_count > 0:
            messages.success(request, f"{deleted_count} article(s) n'est plus disponible dans votre panier.")    
        

    def on_save_model(self, request, obj, form, change):
        super().on_save_model(request, obj, form, change)  # Appeler la méthode parente
        forms.update_type(self)
    

class ForceNewVersionAdmin(admin.ModelAdmin):
    def save_model(self, request, obj, form, change):
        if change:
            obj.pk = None  # Force la création d’un nouvel enregistrement
        super().save_model(request, obj, form, change)
    
    def has_delete_permission(self, request, obj=None):
        return False  # Empêche la suppression
        
@admin.register(CGV)
class CGVAdmin(ForceNewVersionAdmin):
    list_display = ('version', 'created_at')
    ordering = ('-created_at',)

@admin.register(CookiesPolicy)
class CookiesPolicyAdmin(ForceNewVersionAdmin):
    list_display = ('version', 'created_at')
    ordering = ('-created_at',)

@admin.register(LegalMention)
class LegalMentionAdmin(ForceNewVersionAdmin):
    list_display = ('version', 'created_at')
    ordering = ('-created_at',)

@admin.register(PrivacyPolicy)
class PrivacyPolicyAdmin(ForceNewVersionAdmin):
    list_display = ('version', 'created_at')
    ordering = ('-created_at',)

    
admin.site.register(AllProducts, AllProductsAdmin)