
from decimal import Decimal, InvalidOperation

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Vente, Paiement
from .finance import solde


@transaction.atomic
def enregistrer_paiement(vente_id, montant, mode, utilisateur, cle_operation=None):
    vente = Vente.objects.select_for_update().get(pk=vente_id)

    if vente.statut != "VALIDEE":
        raise ValidationError(
            "Impossible de payer une vente non validée."
        )

    try:
        montant = Decimal(str(montant))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("Montant invalide.")

    if not montant.is_finite():
        raise ValidationError("Le montant doit être fini.")

    if montant <= 0:
        raise ValidationError(
            "Le montant doit être strictement positif."
        )

    if montant.as_tuple().exponent < -2:
        raise ValidationError(
            "Le montant ne peut pas dépasser deux décimales."
        )

    modes_autorises = {
        code for code, _ in Paiement.MODES
    }

    if mode not in modes_autorises:
        raise ValidationError("Mode de paiement invalide.")

    reste = solde(vente)["encaissable"]

    if montant > reste:
        raise ValidationError(
            f"Paiement refusé. Reste à payer : {reste}"
        )

    paiement = Paiement(
        cle_operation=cle_operation,
        vente=vente,
        montant=montant,
        mode=mode,
        utilisateur=utilisateur,
        statut="CONFIRME" if mode == "ESPECES" else "EN_ATTENTE",
    )
    paiement.full_clean()
    paiement.save()

    return paiement
