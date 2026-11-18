from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils import timezone

from utilisateurs.permissions import exiger_permission
from ventes.documents import document
from .models import CommandeAchat, ReceptionAchat


@login_required
def bon_commande(request, pk):
    exiger_permission(request.user, "achats.view_commandeachat")
    commande = get_object_or_404(CommandeAchat, pk=pk)
    if commande.statut == "BROUILLON":
        raise Http404
    instantane = commande.instantane_document
    lignes = instantane.get("lignes") or [{"medicament": str(l.medicament), "quantite": l.quantite,
        "prix_unitaire": str(l.prix_unitaire), "sous_total": str(l.sous_total)} for l in commande.lignes.select_related("medicament")]
    return document("Bon de commande", f"BC-{pk:08d}", [
        f"Date : {timezone.localtime(commande.date_commande):%d/%m/%Y}",
        f"Fournisseur : {instantane.get('fournisseur', str(commande.fournisseur))}",
        f"État actuel : {commande.get_statut_display()}", f"Total commandé : {instantane.get('total', commande.total)} Ar",
    ], [["Médicament", "Quantité", "Prix d’achat", "Total"]] + [
        [l["medicament"], l["quantite"], f"{l['prix_unitaire']} Ar", f"{l['sous_total']} Ar"] for l in lignes], instantane)


@login_required
def bon_reception(request, pk):
    exiger_permission(request.user, "achats.view_receptionachat")
    reception = get_object_or_404(ReceptionAchat, pk=pk, validee=True)
    instantane = reception.instantane_document
    lignes = instantane.get("lignes") or [{"medicament": str(l.ligne_achat.medicament), "quantite": l.quantite_recue,
        "numero_lot": l.numero_lot, "peremption": str(l.date_peremption),
        "prix_unitaire": str(l.ligne_achat.prix_unitaire), "sous_total": str(l.quantite_recue*l.ligne_achat.prix_unitaire)}
        for l in reception.lignes.select_related("ligne_achat__medicament")]
    return document("Bon de réception", f"BR-{pk:08d}", [
        f"Date : {timezone.localtime(reception.date_reception):%d/%m/%Y}", f"Commande : {reception.commande_id}",
        f"Fournisseur : {instantane.get('fournisseur', str(reception.commande.fournisseur))}",
        f"Total réceptionné : {instantane.get('total', reception.total)} Ar",
    ], [["Médicament et lot", "Quantité", "Prix d’achat", "Total"]] + [
        [f"{l['medicament']} · Lot {l['numero_lot']} · Expiration {l['peremption']}", l["quantite"],
         f"{l['prix_unitaire']} Ar", f"{l['sous_total']} Ar"] for l in lignes], instantane)
