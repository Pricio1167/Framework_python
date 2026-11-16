from django.contrib import admin
from .models import Categorie, Medicament


@admin.register(Categorie)
class CategorieAdmin(admin.ModelAdmin):
    list_display = ("id", "nom")
    search_fields = ("nom",)


@admin.register(Medicament)
class MedicamentAdmin(admin.ModelAdmin):

    list_display = (
        "id",
        "nom_commercial",
        "categorie",
        "forme",
        "dosage",
        "prix_vente",
        "seuil_alerte",
        "actif",
    )

    list_filter = (
        "categorie",
        "forme",
        "actif",
    )

    search_fields = (
        "nom_commercial",
        "denomination_generique",
        "code_barres",
    )

    list_per_page = 20

    readonly_fields = ("date_creation",)
