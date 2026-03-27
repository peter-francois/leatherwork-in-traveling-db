from django import forms
from .models import *
from django.utils.translation import gettext_lazy as _



class ProductFilterForm(forms.Form):
    
    search = forms.CharField(required=False, label=_("Recherche"), widget=forms.TextInput(attrs={'placeholder': _('Rechercher...'), 'id': 'search_field'}))
    type = forms.CharField(required=False, label=_("Type"), widget=forms.Select(choices= [('---', '---')]))
    min_price = forms.DecimalField(required=False, label=_("Prix min"), min_value=0)
    max_price = forms.DecimalField(required=False, label=_("Prix max"), min_value=0)
    sort_by_price = forms.ChoiceField(required=False, label=_("Trier par prix"), choices=[('---', '---'), ('price', _('Prix croissant')), ('-price', _('Prix décroissant'))])
    
    def __init__(self, *args, **kwargs):
        categorie = kwargs.pop('categorie', None)  # Récupérer la catégorie depuis les arguments
        super().__init__(*args, **kwargs)
      
        # Si une catégorie est fournie, filtrer les types disponibles
        if categorie:
            types = AllProducts.objects.filter(categorie=categorie).values_list('type', flat=True).distinct()
            self.fields['type'].widget.choices = [('---', '---')] +[(t, t) for t in types]  # Mettre à jour les choix
        else:
            self.fields['type'].widget.choices = [('---', '---')] + [(type, type) for type in AllProducts.objects.values_list('type', flat=True).distinct()]
