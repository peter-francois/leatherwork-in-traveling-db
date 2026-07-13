from django.db import models
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _


class Category(models.TextChoices):
    HYBRIDE = "Hybride", _("Hybride")
    MACRAME = "Macrame", _("Macramé")
    MAROQUINERIE = "Maroquinerie", _("Maroquinerie")

    @classmethod
    def from_slug(cls, slug):
        """Resolve a URL slug to a Category value for the current language or legacy values."""
        if not slug:
            return None

        aliases = {
            cls.HYBRIDE: {
                "hybride",
                "hybrid",
            },
            cls.MACRAME: {
                "macrame",
                "macramé",
                "macrame",
            },
            cls.MAROQUINERIE: {
                "maroquinerie",
                "leather-goods",
                "leather goods",
            },
        }

        normalized = slugify(slug).lower()
        for member, values in aliases.items():
            if normalized in {slugify(value).lower() for value in values}:
                return member
        return None

    @classmethod
    def get_slug(cls, category):
        if isinstance(category, cls):
            member = category
        else:
            try:
                member = cls(category)
            except ValueError:
                return None

        return slugify(member.label)

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
