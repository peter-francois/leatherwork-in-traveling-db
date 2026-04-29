from django.db import models

class Category(models.TextChoices):
    HYBRIDE = 'Hybride', 'Hybride'
    MACRAME = 'Macrame', 'Macrame'
    MAROQUINERIE = 'Maroquinerie', 'Maroquinerie'

class ProductType(models.TextChoices):
    BLAGUE_TABAC = 'Blague à tabac', 'Blague à tabac'
    BOUCLES_OREILLES = "Boucles d'oreilles", "Boucles d'oreilles"
    BRACELET = 'Bracelet', 'Bracelet'
    CEINTURE = 'Ceinture', 'Ceinture'
    CHAINE_CORPS = 'Chaine de corps', 'Chaine de corps'
    CHEVILLERE = 'Chevillère', 'Chevillère'
    COLLIER = 'Collier', 'Collier'
    COLLIER_CHIEN = 'Collier chien', 'Collier chien'
    DIVERS = 'Divers', 'Divers'
    ENTRETIEN = 'Entretien', 'Entretien'
    MURALE = 'Murale', 'Murale'
    PORTEFEUILLE = 'Portefeuille, Porte carte', 'Portefeuille, Porte carte'
    SAC_DIVERS = 'Sac divers', 'Sac divers'