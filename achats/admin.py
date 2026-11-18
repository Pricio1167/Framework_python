
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import ValidationError
from .services import valider_reception
from .models import (
    CommandeAchat,
    LigneAchat,
    ReceptionAchat,
    LigneReception,
)


class LigneAchatInline(admin.TabularInline):
    model = LigneAchat
    extra = 1


@admin.register(CommandeAchat)
class CommandeAchatAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "fournisseur",
        "date_commande",
        "statut",
        "utilisateur",
    )
    def has_change_permission(self, request, obj=None):
        if obj and obj.statut != "BROUILLON":
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        return False

    list_filter = ("statut", "date_commande")
    search_fields = ("fournisseur__nom",)
    inlines = [LigneAchatInline]
    readonly_fields = ("date_commande",)
    def get_readonly_fields(self, request, obj=None):
        return ("date_commande", "statut", "instantane_document")


class LigneReceptionInline(admin.TabularInline):
    model = LigneReception
    extra = 1

    def has_add_permission(self, request, obj=None):
        if obj and obj.validee:
            return False
        return super().has_add_permission(request, obj)

    def has_change_permission(self, request, obj=None):
        if obj and obj.validee:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj and obj.validee:
            return False
        return super().has_delete_permission(request, obj)


@admin.register(ReceptionAchat)
class ReceptionAchatAdmin(admin.ModelAdmin):
    
    @admin.action(description="Valider les réceptions sélectionnées")
    def valider_receptions(self, request, queryset):
        if not request.user.has_perm("achats.change_receptionachat"):
            self.message_user(
                request,
                "Permission insuffisante.",
                level=messages.ERROR,
            )
            return

        for reception in queryset:
            try:
                valider_reception(reception.pk)
            except ValidationError as erreur:
                self.message_user(
                    request,
                    f"Réception {reception.pk} : {erreur}",
                    level=messages.ERROR,
                )
            else:
                self.message_user(
                    request,
                    f"Réception {reception.pk} validée.",
                    level=messages.SUCCESS,
                )
                
    list_display = (
        "id",
        "commande",
        "date_reception",
        "validee",
        "utilisateur",
    )

    list_filter = ("validee", "date_reception")
    readonly_fields = ("date_reception", "validee")
    inlines = [LigneReceptionInline]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_readonly_fields(self, request, obj=None):
        if obj and obj.validee:
            return [
                "commande",
                "utilisateur",
                "date_reception",
                "validee",
            ]

        return ["date_reception", "validee"]

    def get_inlines(self, request, obj=None):
        if obj and obj.validee:
            return []

        return [LigneReceptionInline]
    actions = ["valider_receptions"]
