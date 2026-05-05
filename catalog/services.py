from .forms import ProductFilterForm
from django.core.paginator import Paginator
from catalog.constants import PRODUCTS_PER_PAGE

def use_filter(request, products, is_all_products):
    filter_used = False

    if not products:
        return products, None, 0, filter_used

    category = None if is_all_products else products[0].category
    if not is_all_products and not category:
        return products, None, 0, filter_used

    form = ProductFilterForm(request.GET, category=category)

    if form.is_valid():
        search = form.cleaned_data.get('search')
        product_type = form.cleaned_data.get('product_type')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        sort_by_price = form.cleaned_data.get('sort_by_price')

        if search:
            products = [p for p in products if search.lower() in p.name.lower()]
            filter_used = True

        if product_type and product_type != '---':
            products = [p for p in products if p.product_type == product_type]
            filter_used = True

        if min_price is not None:
            products = [p for p in products if p.price >= min_price]
            filter_used = True

        if max_price is not None:
            products = [p for p in products if p.price <= max_price]
            filter_used = True

        if sort_by_price == 'price':
            products = sorted(products, key=lambda p: p.price)
            filter_used = True
        elif sort_by_price == '-price':
            products = sorted(products, key=lambda p: p.price, reverse=True)
            filter_used = True

    return products, form, len(products), filter_used


def pagination(request, products):
    paginator = Paginator(products, PRODUCTS_PER_PAGE)
    page_number = request.GET.get('page', 1)
    return paginator.get_page(page_number)
