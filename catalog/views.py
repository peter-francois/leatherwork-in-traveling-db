from django.shortcuts import render
from .models import Product
from .choices import Category
from .utils import use_filter, pagination

def product_list(request, category=None):
    products = Product.objects.filter(available=True)
    
    if category:
        products = products.filter(category=category)

    products = sorted(products, key=lambda p: (p.pending_in_cart, -p.id))
    products, form, number_of_products_in_filter, filter_used = use_filter(
        request, products, is_all_products=category is None
    )
    page_obj = pagination(request, products)

    return render(request, 'catalog/product_list.html', {
        'products': page_obj,
        'form': form,
        'category': category,
        'number_of_products_in_filter': number_of_products_in_filter,
        'filter_used': filter_used,
    })


def produits(request):
    return product_list(request)

def maroquinerie(request):
    return product_list(request, category=Category.MAROQUINERIE)

def macrames(request):
    return product_list(request, category=Category.MACRAME)

def hybride(request):
    return product_list(request, category=Category.HYBRIDE)
