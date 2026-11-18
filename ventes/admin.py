
from django.contrib import admin, messages
from django.core.exceptions import ValidationError

from .models import Vente, LigneVente, Paiement
from .operations import confirmer_vente, confirmer_retour
from .models import RetourVente, LigneRetour
from .retours import valider_retour
from .models import LigneVenteLot


class LigneVenteInline(admin.TabularInline):
    model = LigneVente
    extra = 1

    def has_add_permission(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return False
        return super().has_delete_permission(request, obj)



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
        return False

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
                confirmer_vente(vente.pk, request.user)
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

    list_filter = (
        "mode",
        "date_paiement",
    )

    search_fields = (
        "vente__id",
        "utilisateur__username",
    )

    readonly_fields = (
        "vente",
        "montant",
        "mode",
        "date_paiement",
        "utilisateur",
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


class LigneRetourInline(admin.TabularInline):
    model = LigneRetour
    extra = 1

    def has_add_permission(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return False
        return super().has_delete_permission(request, obj)


@admin.register(RetourVente)
class RetourVenteAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "vente",
        "date_retour",
        "statut",
        "utilisateur",
    )

    list_filter = ("statut", "date_retour")
    readonly_fields = ("date_retour", "statut")
    inlines = [LigneRetourInline]
    actions = ["valider_retours"]

    def has_change_permission(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    @admin.action(description="Valider les retours sélectionnés")
    def valider_retours(self, request, queryset):
        if not request.user.has_perm("ventes.change_retourvente"):
            self.message_user(
                request,
                "Permission insuffisante.",
                level=messages.ERROR,
            )
            return

        for retour in queryset:
            try:
                confirmer_retour(retour.pk, request.user)
            except ValidationError as erreur:
                self.message_user(
                    request,
                    f"Retour {retour.pk} : {erreur}",
                    level=messages.ERROR,
                )
            else:
                self.message_user(
                    request,
                    f"Retour {retour.pk} validé.",
                    level=messages.SUCCESS,
                )

class LigneVenteLotInline(admin.TabularInline):
    model = LigneVenteLot
    extra = 0
    can_delete = False

    fields = ("lot", "quantite")
    readonly_fields = ("lot", "quantite")

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
