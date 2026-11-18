
from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from stock.models import LotStock, MouvementStock
from .models import Vente
from .models import Vente, LigneVenteLot

from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from stock.models import LotStock, MouvementStock
from .models import Vente, LigneVenteLot


@transaction.atomic
def valider_vente(vente_id):
    vente = Vente.objects.select_for_update().get(pk=vente_id)

    if vente.statut != "BROUILLON":
        raise ValidationError(
            "Seule une vente en brouillon peut être validée."
        )

    lignes = list(
        vente.lignes.select_related("medicament").order_by("pk")
    )

    if not lignes:
        raise ValidationError("Impossible de valider une vente vide.")

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
        if ligne.medicament.prescription_requise and not vente.controle_delivrance.get("reference"):
            raise ValidationError("Le contrôle professionnel de la prescription n’a pas été enregistré.")

        demandes[ligne.medicament_id] += ligne.quantite

    aujourd_hui = timezone.localdate()
    lots_par_medicament = {}

    # Vérifier tout le stock avant de modifier les quantités
    for medicament_id in sorted(demandes):
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

        if sum(lot.quantite for lot in lots) < demandes[medicament_id]:
            raise ValidationError(
                f"Stock insuffisant pour le médicament "
                f"n°{medicament_id}."
            )

        lots_par_medicament[medicament_id] = lots

    # Affecter les lots à chaque ligne de vente
    reserves = defaultdict(int)
    for ligne in lignes:
        if ligne.lot_demande_id:
            candidats = {lot.pk: lot for lot in lots_par_medicament[ligne.medicament_id]}
            if ligne.lot_demande_id not in candidats:
                raise ValidationError("Le lot demandé est bloqué, périmé ou ne correspond pas au médicament.")
            reserves[ligne.lot_demande_id] += ligne.quantite
            if reserves[ligne.lot_demande_id] > candidats[ligne.lot_demande_id].quantite:
                raise ValidationError("Stock insuffisant dans le lot demandé.")
    for ligne in lignes:
        quantite_restante = ligne.quantite

        for lot in lots_par_medicament[ligne.medicament_id]:
            if ligne.lot_demande_id and lot.pk != ligne.lot_demande_id:
                continue
            if quantite_restante == 0:
                break

            if lot.quantite == 0:
                continue

            quantite_prelevee = min(
                lot.quantite if ligne.lot_demande_id else max(0, lot.quantite - reserves[lot.pk]),
                quantite_restante,
            )
            if quantite_prelevee == 0:
                continue
            if ligne.lot_demande_id:
                reserves[lot.pk] -= quantite_prelevee

            lot.quantite -= quantite_prelevee
            lot.save(update_fields=["quantite"])

            LigneVenteLot.objects.create(
                ligne_vente=ligne,
                lot=lot,
                quantite=quantite_prelevee,
            )

            MouvementStock.objects.create(
                lot=lot,
                type_mouvement="SORTIE",
                quantite=quantite_prelevee,
                motif=f"Vente numéro {vente.pk}",
                utilisateur=vente.utilisateur,
            )

            quantite_restante -= quantite_prelevee

    vente.statut = "VALIDEE"
    from dashboard.parametres import identite_pharmacie
    vente.instantane_facture = {
        **identite_pharmacie(),
        "client": str(vente.client) if vente.client else "Client de passage",
        "lignes": [{"medicament": str(ligne.medicament), "quantite": ligne.quantite,
                    "prix_unitaire": str(ligne.prix_unitaire), "sous_total": str(ligne.sous_total)}
                   for ligne in lignes],
    }
    vente.save(update_fields=["statut", "instantane_facture"])

    return vente
