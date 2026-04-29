from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Product


class ProductFilterForm(forms.Form):
    search = forms.CharField(required=False, label=_("Recherche"), widget=forms.TextInput(attrs={'placeholder': _('Rechercher...'), 'id': 'search_field'}))
    product_type = forms.CharField(required=False, label=_("Type"), widget=forms.Select(choices=[('---', '---')]))
    min_price = forms.DecimalField(required=False, label=_("Prix min"), min_value=0)
    max_price = forms.DecimalField(required=False, label=_("Prix max"), min_value=0)
    sort_by_price = forms.ChoiceField(required=False, label=_("Trier par prix"), choices=[('---', '---'), ('price', _('Prix croissant')), ('-price', _('Prix décroissant'))])

    def __init__(self, *args, **kwargs):
        category = kwargs.pop('category', None)
        super().__init__(*args, **kwargs)

        if category:
            types = Product.objects.filter(category=category).values_list('product_type', flat=True).distinct()
        else:
            types = Product.objects.values_list('product_type', flat=True).distinct()
        
        self.fields['product_type'].widget.choices = [('---', '---')] + [(t, t) for t in types]