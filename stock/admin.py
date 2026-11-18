from django.contrib import admin

from .models import LotStock, MouvementStock


@admin.register(LotStock)
class LotStockAdmin(admin.ModelAdmin):
    list_display = ("medicament", "numero_lot", "date_peremption", "quantite", "bloque")
    readonly_fields = ("medicament", "numero_lot", "date_peremption", "quantite", "quantite_recue", "bloque", "date_creation")

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(MouvementStock)
class MouvementStockAdmin(admin.ModelAdmin):
    list_display = ("lot", "type_mouvement", "quantite", "motif", "utilisateur", "date_mouvement")
    readonly_fields = ("lot", "type_mouvement", "quantite", "motif", "utilisateur", "date_mouvement")

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
