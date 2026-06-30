from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _

from .choices import Category
from .constants import CATEGORY_LABELS, CATEGORY_SLUG_TO_VALUE, CATEGORY_URL_NAMES
from .models import Product
from .services import pagination, use_filter


def product_list(request, category=None, template="catalog/product_list.html"):
    products = Product.objects.filter(available=True)

    if category:
        products = products.filter(category=category)

    products = products.order_by("pending_in_cart", "-id")
    products, form, number_of_products_in_filter, filter_used = use_filter(
        request, products, is_all_products=category is None
    )
    page_obj = pagination(request, products)

    return render(
        request,
        template,
        {
            "products": page_obj,
            "form": form,
            "category": category,
            "number_of_products_in_filter": number_of_products_in_filter,
            "filter_used": filter_used,
        },
    )


def product(request):
    return product_list(request)


def leatherwork(request):
    return product_list(
        request, category=Category.MAROQUINERIE, template="catalog/leatherwork.html"
    )


def macrame(request):
    return product_list(
        request, category=Category.MACRAME, template="catalog/macrame.html"
    )


def hybrid(request):
    return product_list(
        request, category=Category.HYBRIDE, template="catalog/hybrid.html"
    )


def product_detail(request, category, slug, product_id):
    real_category = CATEGORY_SLUG_TO_VALUE.get(category.lower())
    if not real_category:
        raise Http404

    product = get_object_or_404(Product, id=product_id, category=real_category)

    expected_slug = slugify(product.name)
    expected_category_slug = category.lower()
    if slug != expected_slug or category != expected_category_slug:
        return redirect(
            "catalog:product_detail",
            category=expected_category_slug,
            slug=expected_slug,
            product_id=product.id,
            permanent=True,
        )

    return render(
        request,
        "catalog/product_detail.html",
        {
            "product": product,
            "category_url_name": CATEGORY_URL_NAMES.get(
                real_category, "catalog:product_list"
            ),
            "category_label": CATEGORY_LABELS.get(real_category, _("Produits")),
        },
    )
