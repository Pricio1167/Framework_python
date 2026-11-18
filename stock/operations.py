from django.core.exceptions import ValidationError
from django.db import transaction
from decimal import Decimal, InvalidOperation

from utilisateurs.permissions import exiger_permission
from .models import LotStock, MouvementStock


def quantite_entiere(valeur):
    try:
        nombre = Decimal(str(valeur))
        if not nombre.is_finite() or nombre != nombre.to_integral_value() or nombre < 0 or nombre > 2147483647:
            raise ValueError
        return int(nombre)
    except (ValueError, InvalidOperation, TypeError):
        raise ValidationError("Quantité entière comprise entre 0 et 2 147 483 647 requise.")


@transaction.atomic
def inventorier(pk, quantite, motif, acteur):
    exiger_permission(acteur, "stock.change_lotstock")
    lot = LotStock.objects.select_for_update().get(pk=pk)
    nouvelle = quantite_entiere(quantite)
    if nouvelle < 0 or not motif.strip():
        raise ValidationError("Quantité positive ou nulle et justification obligatoires.")
    ecart = nouvelle - lot.quantite
    if not ecart:
        raise ValidationError("Aucun écart d’inventaire.")
    MouvementStock.objects.create(
        lot=lot, type_mouvement="CORRECTION", quantite=abs(ecart),
        motif=f"Inventaire {lot.quantite} → {nouvelle} ; écart {ecart:+d} : {motif}",
        utilisateur=acteur,
    )
    lot.quantite = nouvelle
    lot.save(update_fields=["quantite"])
    return lot


@transaction.atomic
def mouvement_manuel(pk, type_mouvement, quantite, motif, acteur):
    from django.utils import timezone
    exiger_permission(acteur, "stock.change_lotstock")
    exiger_permission(acteur, "stock.add_mouvementstock")
    lot = LotStock.objects.select_for_update().get(pk=pk)
    nombre = quantite_entiere(quantite)
    if not nombre or not motif.strip() or type_mouvement not in ("ENTREE", "SORTIE"):
        raise ValidationError("Type, quantité strictement positive et motif obligatoires.")
    if type_mouvement == "ENTREE":
        if lot.bloque or lot.date_peremption <= timezone.localdate():
            raise ValidationError("Impossible d’ajouter du stock vendable à un lot bloqué ou périmé.")
        lot.quantite = quantite_entiere(lot.quantite + nombre)
    else:
        if nombre > lot.quantite:
            raise ValidationError("La sortie dépasse la quantité du lot.")
        lot.quantite -= nombre
    lot.save(update_fields=["quantite"])
    return MouvementStock.objects.create(lot=lot, type_mouvement=type_mouvement,
                                         quantite=nombre, motif=motif, utilisateur=acteur)
