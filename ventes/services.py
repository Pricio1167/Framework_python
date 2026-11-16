
from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from stock.models import LotStock, MouvementStock
from .models import Vente


@transaction.atomic
def valider_vente(vente_id):
    vente = Vente.objects.select_for_update().get(pk=vente_id)

    if vente.statut != "BROUILLON":
        raise ValidationError(
            "Seule une vente en brouillon peut être validée."
        )

    lignes = list(
        vente.lignes.select_related("medicament")
    )

    if not lignes:
        raise ValidationError(
            "Impossible de valider une vente vide."
        )

    # Regrouper les quantités par médicament.
    demandes = defaultdict(int)

    for ligne in lignes:
        if ligne.quantite <= 0:
            raise ValidationError("Quantité invalide.")

        if ligne.prix_unitaire < 0:
            raise ValidationError("Prix invalide.")

        if not ligne.medicament.actif:
            raise ValidationError(
                f"{ligne.medicament} est inactif."
            )

        demandes[ligne.medicament_id] += ligne.quantite

    # Verrouiller les lots et préparer les sorties FEFO.
    aujourd_hui = timezone.localdate()
    allocations = []

    for medicament_id in sorted(demandes):
        quantite_restante = demandes[medicament_id]

        lots = list(
            LotStock.objects.select_for_update()
            .filter(
                medicament_id=medicament_id,
                bloque=False,
                date_peremption__gt=aujourd_hui,
                quantite__gt=0,
            )
            .order_by("date_peremption", "pk")
        )

        for lot in lots:
            if quantite_restante == 0:
                break

            quantite_prelevee = min(
                lot.quantite,
                quantite_restante
            )

            allocations.append(
                (lot, quantite_prelevee)
            )

            quantite_restante -= quantite_prelevee

        if quantite_restante > 0:
            raise ValidationError(
                "Stock insuffisant pour le médicament "
                f"n°{medicament_id}."
            )

    # Déduire le stock uniquement après vérification.
    for lot, quantite in allocations:
        lot.quantite -= quantite
        lot.save(update_fields=["quantite"])

        MouvementStock.objects.create(
            lot=lot,
            type_mouvement="SORTIE",
            quantite=quantite,
            motif=f"Vente numéro {vente.pk}",
            utilisateur=vente.utilisateur,
        )

    vente.statut = "VALIDEE"
    vente.save(update_fields=["statut"])

    return vente
