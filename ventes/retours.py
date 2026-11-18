
from collections import defaultdict

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Sum

from .models import RetourVente, LigneRetour, Vente
from ventes.models import RetourVente, LigneRetour

@transaction.atomic
def valider_retour(retour_id):
    vente_id = RetourVente.objects.values_list("vente_id", flat=True).get(pk=retour_id)
    Vente.objects.select_for_update().get(pk=vente_id)
    retour = (
        RetourVente.objects
        .select_for_update()
        .select_related("vente")
        .get(pk=retour_id)
    )

    vente = retour.vente
    if not retour.motif.strip():
        raise ValidationError("Un motif de retour est obligatoire.")

    # Verifier le statut du retour.
    if retour.statut != "BROUILLON":
        raise ValidationError(
            "Ce retour a deja ete valide."
        )

    # Verifier la vente d'origine.
    if vente.statut != "VALIDEE":
        raise ValidationError(
            "Seule une vente validee peut faire l'objet d'un retour."
        )

    lignes = list(
        LigneRetour.objects.filter(retour=retour)
        .select_related("ligne_vente")
    )

    if not lignes:
        raise ValidationError(
            "Impossible de valider un retour vide."
        )

    # Regrouper les quantites par ligne de vente.
    quantites = defaultdict(int)

    for ligne in lignes:
        if ligne.quantite <= 0:
            raise ValidationError(
                "La quantite retournee doit etre positive."
            )

        if ligne.ligne_vente.vente_id != vente.pk:
            raise ValidationError(
                "Le medicament ne correspond pas a la vente."
            )
        if ligne.lot_origine_id:
            delivre = ligne.ligne_vente.lots_utilises.filter(lot_id=ligne.lot_origine_id).aggregate(total=Sum("quantite"))["total"] or 0
            retourne = LigneRetour.objects.filter(ligne_vente=ligne.ligne_vente, lot_origine_id=ligne.lot_origine_id,
                                                  retour__statut="VALIDE").aggregate(total=Sum("quantite"))["total"] or 0
            en_cours = sum(l.quantite for l in lignes if l.ligne_vente_id == ligne.ligne_vente_id and l.lot_origine_id == ligne.lot_origine_id)
            if retourne + en_cours > delivre:
                raise ValidationError("La quantité de ce lot dépasse les unités réellement délivrées.")

        quantites[ligne.ligne_vente_id] += ligne.quantite

    # Controler les retours deja valides.
    for ligne_vente_id, quantite in quantites.items():
        ligne_vente = next(
            ligne.ligne_vente
            for ligne in lignes
            if ligne.ligne_vente_id == ligne_vente_id
        )

        deja_retourne = (
            LigneRetour.objects.filter(
                ligne_vente_id=ligne_vente_id,
                retour__statut="VALIDE",
            )
            .aggregate(total=Sum("quantite"))["total"]
            or 0
        )

        if deja_retourne + quantite > ligne_vente.quantite:
            raise ValidationError(
                "La quantite retournee depasse "
                "la quantite vendue."
            )

    # Valider sans remettre les produits dans le stock.
    retour.statut = "VALIDE"
    retour.save(update_fields=["statut"])

    return retour


