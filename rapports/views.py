
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from .pdf import generer_pdf_ventes, generer_pdf_stock
from .forms import PeriodeForm
from .services import rapport_ventes, rapport_stock, rapport_achats
from django.shortcuts import render
from django.http import HttpResponseBadRequest


@login_required
def accueil(request):
    if not any(request.user.has_perm(p) for p in ("ventes.view_vente", "stock.view_lotstock", "achats.view_commandeachat")):
        raise PermissionDenied("Accès aux rapports non autorisé.")
    form = PeriodeForm(request.GET)
    contexte = {"form": form}
    if form.is_valid():
        if request.user.has_perm("ventes.view_vente"):
            contexte["ventes"] = rapport_ventes(**form.cleaned_data)
        if request.user.has_perm("stock.view_lotstock"):
            contexte["stocks"] = rapport_stock()
        if request.user.has_perm("achats.view_commandeachat"):
            contexte["achats"] = rapport_achats(**form.cleaned_data)
    return render(request, "rapports/accueil.html", contexte)


@login_required
def telecharger_rapport_ventes(request):
    if not request.user.has_perm("ventes.view_vente"):
        raise PermissionDenied(
            "Vous n'avez pas la permission de consulter les ventes."
        )

    form = PeriodeForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest("Période invalide.")
    return generer_pdf_ventes(**form.cleaned_data)


@login_required
def telecharger_rapport_stock(request):
    if not request.user.has_perm("stock.view_lotstock"):
        raise PermissionDenied(
            "Vous n'avez pas la permission de consulter les stocks."
        )

    return generer_pdf_stock()


@login_required
def telecharger_achats(request):
    from utilisateurs.permissions import exiger_permission
    from ventes.documents import document
    from django.utils import timezone
    exiger_permission(request.user, "achats.view_commandeachat")
    form = PeriodeForm(request.GET)
    if not form.is_valid():
        return HttpResponseBadRequest("Période invalide.")
    rapport = rapport_achats(**form.cleaned_data)
    lignes = [["Commande et fournisseur", "Date", "État", "Total"]]
    lignes += [[f"BC-{c.pk:08d} · {c.fournisseur}", timezone.localtime(c.date_commande).strftime("%d/%m/%Y"),
                c.get_statut_display(), f"{c.total} Ar"] for c in rapport["commandes"]]
    return document("Rapport des achats", "ACH-" + timezone.localdate().strftime("%Y%m%d"), [
        f"Date d’édition : {timezone.localdate():%d/%m/%Y}",
        f"Période : {form.cleaned_data['date_debut'] or 'début de l’historique'} - {form.cleaned_data['date_fin'] or 'aujourd’hui'}",
        f"Commandes confirmées : {rapport['nombre_commandes']} · Total : {rapport['montant_commandes']} Ar",
        f"Réceptions validées par date de réception : {rapport['nombre_receptions']} · Montant : {rapport['montant_receptionne']} Ar",
    ], lignes)


@login_required
def telecharger_peremptions(request):
    from utilisateurs.permissions import exiger_permission
    from ventes.documents import document
    from django.utils import timezone
    exiger_permission(request.user, "stock.view_lotstock")
    lots = rapport_stock()["lots_proches_peremption"]
    return document("Lots proches de la péremption", "EXP-" + timezone.localdate().strftime("%Y%m%d"),
                    [f"Date : {timezone.localdate():%d/%m/%Y}", "Lots avec stock expirant dans les trente prochains jours."],
                    [["Médicament", "Quantité", "Lot", "Péremption"]] + [
                        [l.medicament, l.quantite, l.numero_lot, l.date_peremption.strftime("%d/%m/%Y")] for l in lots])
