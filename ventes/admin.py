
from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import Vente, LigneVente, Paiement
from .services import valider_vente


class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 1


@admin.register(Vente)
class VenteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "client",
        "date_vente",
        "statut",
        "total",
        "utilisateur",
    )

    list_filter = ("statut", "date_vente")
    readonly_fields = ("date_vente", "statut")
    inlines = [LigneVenteInline]
    actions = ["valider_ventes"]

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return (
                "client",
                "utilisateur",
                "date_vente",
                "statut",
            )
        return ("date_vente", "statut")

    def get_inlines(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return []
        return [LigneVenteInline]

    def has_delete_permission(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return False
        return super().has_delete_permission(request, obj)

    @admin.action(description="Valider les ventes sélectionnées")
    def valider_ventes(self, request, queryset):
        if not request.user.has_perm("ventes.change_vente"):
            self.message_user(
                request,
                "Permission insuffisante.",
                level=messages.ERROR,
            )
            return

        for vente in queryset:
            try:
                valider_vente(vente.pk)
            except ValidationError as erreur:
                self.message_user(
                    request,
                    f"Vente {vente.pk} : {erreur}",
                    level=messages.ERROR,
                )
            else:
                self.message_user(
                    request,
                    f"Vente {vente.pk} validée.",
                    level=messages.SUCCESS,
                )


@admin.register(Paiement)
class PaiementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vente",
        "montant",
        "mode",
        "date_paiement",
        "utilisateur",
    )

    list_filter = ("mode", "date_paiement")
    readonly_fields = ("date_paiement",)
