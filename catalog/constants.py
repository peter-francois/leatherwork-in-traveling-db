from django.utils.translation import gettext_lazy as _

from catalog.choices import Category

PRODUCTS_PER_PAGE = 24

CATEGORY_SLUG_TO_VALUE = {
    "hybride": Category.HYBRIDE,
    "macrame": Category.MACRAME,
    "maroquinerie": Category.MAROQUINERIE,
}

CATEGORY_URL_NAMES = {
    Category.HYBRIDE: "catalog:hybrid_list",
    Category.MACRAME: "catalog:macrame_list",
    Category.MAROQUINERIE: "catalog:leather_list",
}

CATEGORY_LABELS = {
    Category.HYBRIDE: _("Hybride"),
    Category.MACRAME: _("Macramés"),
    Category.MAROQUINERIE: _("Maroquinerie"),
}
