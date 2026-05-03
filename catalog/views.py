from django.shortcuts import render
from .models import Product
from .choices import Category
from .services import use_filter, pagination

def product_list(request, category=None, template='catalog/product_list.html'):
    products = Product.objects.filter(available=True)

    if category:
        products = products.filter(category=category)

    products = products.order_by('pending_in_cart', '-id')
    products, form, number_of_products_in_filter, filter_used = use_filter(
        request, products, is_all_products=category is None
    )
    page_obj = pagination(request, products)

    return render(request, template, {
        'products': page_obj,
        'form': form,
        'category': category,
        'number_of_products_in_filter': number_of_products_in_filter,
        'filter_used': filter_used,
    })

def product(request):
    return product_list(request)

def leatherwork(request):
    return product_list(request, category=Category.MAROQUINERIE, template='catalog/leatherwork.html')

def macrame(request):
    return product_list(request, category=Category.MACRAME, template='catalog/macrame.html')

def hybrid(request):
    return product_list(request, category=Category.HYBRIDE, template='catalog/hybrid.html')
