
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum
from django.utils import timezone

from .models import CommandeAchat, ReceptionAchat, LigneReception
from stock.models import LotStock, MouvementStock


@transaction.atomic
def valider_reception(reception_id):
    # Recuperer la reception
    reception = ReceptionAchat.objects.select_for_update().get(
        pk=reception_id
    )

    # Verrouiller la commande associee
    commande = CommandeAchat.objects.select_for_update().get(
        pk=reception.commande_id
    )

    # Eviter une double validation
    if reception.validee:
        raise ValidationError(
            "Cette reception a deja ete validee."
        )

    # Verifier le statut de la commande
    if commande.statut not in ("COMMANDEE", "PARTIELLE"):
        raise ValidationError(
            "Cette commande ne peut pas etre receptionnee."
        )

    # Recuperer les lignes de reception
    lignes = list(
        LigneReception.objects.filter(
            reception=reception
        ).select_related(
            "ligne_achat",
            "ligne_achat__medicament"
        )
    )

    if not lignes:
        raise ValidationError(
            "La reception ne contient aucun medicament."
        )

    # Verifier les quantites commandees et recues
    for ligne in lignes:
        if ligne.ligne_achat.commande_id != commande.pk:
            raise ValidationError(
                "La ligne ne correspond pas a la commande."
            )

        if ligne.quantite_recue <= 0:
            raise ValidationError(
                "La quantite recue doit etre positive."
            )

        if ligne.date_peremption <= timezone.localdate():
            raise ValidationError(
                "Impossible de receptionner un lot perime."
            )

    # Regrouper les quantites de cette reception
    quantites = {}

    for ligne in lignes:
        identifiant = ligne.ligne_achat_id
        quantites[identifiant] = (
            quantites.get(identifiant, 0)
            + ligne.quantite_recue
        )

    # Controler les quantites restantes
    for ligne_achat_id, quantite in quantites.items():
        ligne_achat = next(
            ligne.ligne_achat
            for ligne in lignes
            if ligne.ligne_achat_id == ligne_achat_id
        )

        deja_recu = (
            LigneReception.objects.filter(
                ligne_achat_id=ligne_achat_id,
                reception__validee=True
            ).aggregate(
                total=Sum("quantite_recue")
            )["total"]
            or 0
        )

        if deja_recu + quantite > ligne_achat.quantite:
            raise ValidationError(
                "La quantite recue depasse la quantite commandee."
            )

    # Mettre a jour les lots
    for ligne in lignes:
        lot, cree = LotStock.objects.select_for_update().get_or_create(
            medicament=ligne.ligne_achat.medicament,
            numero_lot=ligne.numero_lot,
            defaults={
                "date_peremption": ligne.date_peremption,
                "quantite": 0,
                "quantite_recue": 0,
            }
        )

        if lot.date_peremption != ligne.date_peremption:
            raise ValidationError(
                "Date de peremption incoherente pour ce lot."
            )

        if lot.bloque:
            raise ValidationError(
                "Impossible de modifier un lot bloque."
            )

        lot.quantite += ligne.quantite_recue
        lot.quantite_recue += ligne.quantite_recue
        lot.save()

        # Enregistrer le mouvement de stock
        MouvementStock.objects.create(
            lot=lot,
            type_mouvement="ENTREE",
            quantite=ligne.quantite_recue,
            motif=f"Reception numero {reception.pk}",
            utilisateur=reception.utilisateur
        )

    # Confirmer la reception
    reception.validee = True
    from dashboard.parametres import identite_pharmacie
    reception.instantane_document = {
        **identite_pharmacie(), "fournisseur": commande.instantane_document.get("fournisseur", str(commande.fournisseur)),
        "commande": commande.pk,
        "lignes": [{"medicament": str(l.ligne_achat.medicament), "quantite": l.quantite_recue,
                    "numero_lot": l.numero_lot, "peremption": l.date_peremption.isoformat(),
                    "prix_unitaire": str(l.ligne_achat.prix_unitaire),
                    "sous_total": str(l.quantite_recue*l.ligne_achat.prix_unitaire)} for l in lignes],
        "total": str(reception.total),
    }
    reception.save(update_fields=["validee", "instantane_document"])

    # Actualiser le statut de la commande
    lignes_commande = list(commande.lignes.all())

    reception_complete = bool(lignes_commande) and all(
        (
            LigneReception.objects.filter(
                ligne_achat=ligne_achat,
                reception__validee=True
            ).aggregate(
                total=Sum("quantite_recue")
            )["total"]
            or 0
        ) == ligne_achat.quantite
        for ligne_achat in lignes_commande
    )

    commande.statut = (
        "RECUE" if reception_complete else "PARTIELLE"
    )
    commande.save(update_fields=["statut"])

    return reception
