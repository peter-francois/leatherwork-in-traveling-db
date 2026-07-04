from django.db import models
from django.utils.translation import gettext_lazy as _


class Category(models.TextChoices):
    HYBRIDE = "Hybride", _("Hybride")
    MACRAME = "Macrame", _("Macramé")
    MAROQUINERIE = "Maroquinerie", _("Maroquinerie")

    @classmethod
    def get_category_url_name(cls, category):
        return {
            cls.HYBRIDE: "catalog:hybrid_list",
            cls.MACRAME: "catalog:macrame_list",
            cls.MAROQUINERIE: "catalog:leather_list",
        }[category]


class ProductType(models.TextChoices):
    BLAGUE_TABAC = "Blague à tabac", "Blague à tabac"
    BOUCLES_OREILLES = "Boucles d'oreilles", "Boucles d'oreilles"
    BRACELET = "Bracelet", "Bracelet"
    CEINTURE = "Ceinture", "Ceinture"
    CHAINE_CORPS = "Chaine de corps", "Chaine de corps"
    CHEVILLERE = "Chevillère", "Chevillère"
    COLLIER = "Collier", "Collier"
    COLLIER_CHIEN = "Collier chien", "Collier chien"
    DIVERS = "Divers", "Divers"
    ENTRETIEN = "Entretien", "Entretien"
    MURALE = "Murale", "Murale"
    PORTEFEUILLE = "Portefeuille, Porte carte", "Portefeuille, Porte carte"
    SAC_DIVERS = "Sac divers", "Sac divers"
