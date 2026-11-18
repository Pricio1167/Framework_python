from django.core.exceptions import ValidationError
from django.db import transaction

from dashboard.parametres import identite_pharmacie
from utilisateurs.permissions import exiger_permission
from ventes.audit import journaliser
from .models import CommandeAchat


@transaction.atomic
def commander(pk, acteur):
    exiger_permission(acteur, "achats.change_commandeachat")
    commande = CommandeAchat.objects.select_for_update().get(pk=pk)
    if commande.statut != "BROUILLON" or not commande.fournisseur.actif:
        raise ValidationError("Commande en brouillon et fournisseur actif requis.")
    lignes = list(commande.lignes.select_related("medicament"))
    if not lignes:
        raise ValidationError("Ajoutez au moins une ligne à la commande.")
    for ligne in lignes:
        ligne.full_clean()
    commande.instantane_document = {
        **identite_pharmacie(), "fournisseur": str(commande.fournisseur),
        "adresse_fournisseur": commande.fournisseur.adresse,
        "lignes": [{"medicament": str(l.medicament), "quantite": l.quantite,
                    "prix_unitaire": str(l.prix_unitaire), "sous_total": str(l.sous_total)} for l in lignes],
        "total": str(commande.total),
    }
    commande.statut = "COMMANDEE"
    commande.save(update_fields=["statut", "instantane_document"])
    journaliser(acteur, "confirmation_commande", commande, "Commande validée pour approvisionnement")
    return commande


@transaction.atomic
def annuler_commande(pk, acteur, motif):
    exiger_permission(acteur, "achats.change_commandeachat")
    commande = CommandeAchat.objects.select_for_update().get(pk=pk)
    if commande.statut not in ("BROUILLON", "COMMANDEE") or commande.receptions.filter(validee=True).exists() or not motif.strip():
        raise ValidationError("Seule une commande sans réception validée peut être annulée, avec un motif.")
    commande.statut = "ANNULEE"
    commande.save(update_fields=["statut"])
    journaliser(acteur, "annulation_commande", commande, motif)
    return commande
