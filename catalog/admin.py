from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils.html import format_html
from modeltranslation.admin import TranslationAdmin

from .models import Product


class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = [
            "name",
            "category",
            "product_type",
            "description",
            "price",
            "discount",
            "image1",
            "image2",
            "image3",
            "image4",
            "image5",
            "image6",
            "available",
            "on_demand",
        ]

    def clean(self):
        cleaned_data = super().clean()
        for field in [f"image{i}" for i in range(1, 7)]:
            image_file = cleaned_data.get(field)
            if image_file:
                if hasattr(image_file, "size") and image_file.size > 10 * 1024 * 1024:
                    raise ValidationError(
                        {
                            field: "Le fichier est trop volumineux. La taille maximale est de 10 Mo."
                        }
                    )
        return cleaned_data


def image_thumbnail(image_field):
    if image_field:
        return format_html(
            '<img src="{}" width="100" height="100" style="object-fit: cover;" />',
            image_field.url,
        )
    return "Aucune image"


def _make_thumbnail(i):
    def thumbnail(self, obj):
        return image_thumbnail(getattr(obj, f"image{i}"))

    thumbnail.short_description = f"Miniature {i}"
    return thumbnail


class ProductAdmin(TranslationAdmin):
    actions = ["make_available", "make_unavailable", "remove_from_cart"]
    list_display = (
        "name",
        "description",
        "category",
        "available",
        "pending_in_cart",
        "on_demand",
        "product_type",
        "price",
        "seo_ready",
    )
    search_fields = ["name", "category", "product_type"]
    list_filter = ["category", "available", "seo_ready"]
    form = ProductForm
    list_per_page = 20
    readonly_fields = tuple(f"image{i}_thumbnail" for i in range(1, 7))
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "name",
                    "meta_description",
                    "description",
                    "category",
                    "product_type",
                    "price",
                    "discount",
                    "available",
                    "pending_in_cart",
                    "on_demand",
                    "seo_ready",
                )
            },
        ),
        (
            "Images",
            {
                "fields": tuple(
                    field
                    for i in range(1, 7)
                    for field in (f"image{i}", f"image{i}_thumbnail")
                )
            },
        ),
    )

    def make_available(self, request, queryset):
        queryset.update(available=True)

    make_available.short_description = "Rendre disponible"

    def make_unavailable(self, request, queryset):
        queryset.update(available=False)

    make_unavailable.short_description = "Rendre indisponible"

    def remove_from_cart(self, request, queryset):
        try:
            from cart.models import CartItem

            articles_id = list(queryset.values_list("id", flat=True))
            with transaction.atomic():
                deleted_count, _ = CartItem.objects.filter(
                    product__in=articles_id
                ).delete()
                queryset.update(pending_in_cart=False)
            if deleted_count > 0:
                messages.success(
                    request,
                    "{count} article(s) retiré(s) du panier.".format(
                        count=deleted_count
                    ),
                )
        except Exception:
            messages.warning(request, "Fonctionnalité panier pas encore disponible.")

    remove_from_cart.short_description = "Retirer du panier"


for i in range(1, 7):
    setattr(ProductAdmin, f"image{i}_thumbnail", _make_thumbnail(i))


admin.site.register(Product, ProductAdmin)
