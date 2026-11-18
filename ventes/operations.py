"""Points d'entrée autorisés pour les opérations interactives."""
from decimal import Decimal, InvalidOperation
from uuid import UUID

from django.core.exceptions import ValidationError
from django.db import transaction, IntegrityError
from django.db.models import Sum

from utilisateurs.permissions import exiger_permission
from .models import Vente, RetourVente, Remboursement, Paiement
from .services import valider_vente
from .retours import valider_retour
from .paiements import enregistrer_paiement
from .finance import somme, total_retours, solde


def lire_cle_operation(valeur):
    if not valeur:
        return None
    try:
        return UUID(str(valeur))
    except (ValueError, TypeError, AttributeError):
        raise ValidationError("La référence de l’opération est invalide. Rechargez la page.")


def retrouver_operation(model, cle, **valeurs):
    if cle is None:
        return None
    precedent = model.objects.filter(cle_operation=cle).first()
    if precedent and any(getattr(precedent, champ) != valeur for champ, valeur in valeurs.items()):
        raise ValidationError("Cette référence a déjà été utilisée pour une autre opération. Rechargez la page.")
    return precedent


@transaction.atomic
def ajouter_ligne(pk, medicament, quantite, acteur, ligne_id=None, lot_demande=None):
    from .models import LigneVente
    exiger_permission(acteur, "ventes.change_lignevente" if ligne_id else "ventes.add_lignevente")
    vente = Vente.objects.select_for_update().get(pk=pk)
    if vente.statut != "BROUILLON":
        raise ValidationError("Cette vente n’est plus modifiable.")
    if not medicament.actif:
        raise ValidationError("Ce médicament est inactif.")
    ligne = vente.lignes.select_for_update().get(pk=ligne_id) if ligne_id else LigneVente(vente=vente)
    ligne.medicament = medicament
    ligne.quantite = quantite
    if lot_demande is not None:
        from django.utils import timezone
        if lot_demande.medicament_id != medicament.pk or lot_demande.bloque or lot_demande.date_peremption <= timezone.localdate() or lot_demande.quantite < quantite:
            raise ValidationError("Le lot sélectionné n’est pas vendable pour cette quantité.")
    ligne.lot_demande = lot_demande
    ligne.prix_unitaire = medicament.prix_vente
    ligne.full_clean()
    ligne.save()
    return ligne


@transaction.atomic
def supprimer_ligne(pk, ligne_id, acteur):
    exiger_permission(acteur, "ventes.delete_lignevente")
    vente = Vente.objects.select_for_update().get(pk=pk)
    if vente.statut != "BROUILLON":
        raise ValidationError("Les lignes d’une vente confirmée ne peuvent plus être supprimées.")
    vente.lignes.get(pk=ligne_id).delete()


@transaction.atomic
def confirmer_vente(pk, acteur, controle=""):
    exiger_permission(acteur, "ventes.change_vente")
    vente = Vente.objects.select_for_update().get(pk=pk)
    if vente.lignes.filter(medicament__prescription_requise=True).exists():
        if not controle.strip():
            raise ValidationError("Un contrôle professionnel de la prescription est requis pour cette vente.")
        from django.utils import timezone
        vente.controle_delivrance = {"acteur": acteur.pk, "date": timezone.now().isoformat(), "reference": controle.strip()}
        vente.save(update_fields=["controle_delivrance"])
    vente = valider_vente(pk)
    from .audit import journaliser
    journaliser(acteur, "validation_vente", vente, "Déstockage FEFO")
    return vente


@transaction.atomic
def payer(pk, montant, mode, acteur, cle_operation=None):
    exiger_permission(acteur, "ventes.add_paiement")
    vente = Vente.objects.select_for_update().get(pk=pk)
    try:
        valeur = Decimal(str(montant))
        if not valeur.is_finite():
            raise ValidationError("Montant invalide.")
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError("Montant invalide.")
    cle = lire_cle_operation(cle_operation)
    precedent = retrouver_operation(Paiement, cle, vente_id=vente.pk, montant=valeur, mode=mode)
    if precedent:
        return precedent
    if valeur > solde(vente)["encaissable"]:
        raise ValidationError("Le paiement dépasse le solde dû.")
    try:
        return enregistrer_paiement(pk, valeur, mode, acteur, cle_operation=cle)
    except IntegrityError:
        raise ValidationError("Cette référence de paiement a déjà été utilisée. Rechargez la page.")


@transaction.atomic
def verifier_paiement(pk, acteur, reference, accepter=True):
    from django.utils import timezone
    exiger_permission(acteur, "ventes.confirmer_paiement")
    vente_id = Paiement.objects.values_list("vente_id", flat=True).get(pk=pk)
    vente = Vente.objects.select_for_update().get(pk=vente_id)
    paiement = Paiement.objects.select_for_update().get(pk=pk)
    if paiement.statut != "EN_ATTENTE" or not reference.strip():
        raise ValidationError("Paiement en attente et preuve de vérification obligatoires.")
    bilan = solde(vente)
    if accepter and paiement.montant > vente.total - bilan["paye"] + bilan["rembourse"]:
        raise ValidationError("La confirmation dépasserait le montant initialement payable.")
    paiement.statut = "CONFIRME" if accepter else "REFUSE"
    paiement.reference_verification = reference.strip()
    paiement.verifie_par = acteur
    paiement.date_verification = timezone.now()
    paiement.full_clean()
    try:
        with transaction.atomic():
            paiement.save(update_fields=["statut", "reference_verification", "verifie_par", "date_verification"])
    except IntegrityError:
        raise ValidationError("Cette référence électronique a déjà confirmé un autre paiement.")
    from .audit import journaliser
    journaliser(acteur, "verification_paiement", paiement, reference)
    return paiement


@transaction.atomic
def confirmer_retour(pk, acteur):
    exiger_permission(acteur, "ventes.change_retourvente")
    retour = RetourVente.objects.get(pk=pk)
    Vente.objects.select_for_update().get(pk=retour.vente_id)
    if not retour.motif.strip():
        raise ValidationError("Un motif est obligatoire.")
    retour = valider_retour(pk)
    from .audit import journaliser
    journaliser(acteur, "validation_retour", retour, retour.motif)
    return retour


@transaction.atomic
def rembourser(pk, montant, motif, acteur, cle_operation=None):
    exiger_permission(acteur, "ventes.add_remboursement")
    retour = RetourVente.objects.get(pk=pk)
    vente = Vente.objects.select_for_update().get(pk=retour.vente_id)
    retour = RetourVente.objects.select_for_update().get(pk=pk)
    if retour.statut != "VALIDE" or not motif.strip():
        raise ValidationError("Un retour validé et un motif sont obligatoires.")
    try:
        valeur = Decimal(str(montant))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("Montant invalide.")
    if not valeur.is_finite() or valeur <= 0 or valeur.as_tuple().exponent < -2:
        raise ValidationError("Montant positif à deux décimales maximum requis.")
    cle = lire_cle_operation(cle_operation)
    precedent = retrouver_operation(Remboursement, cle, retour_id=retour.pk, montant=valeur, motif=motif)
    if precedent:
        return precedent
    montant_retour = sum((l.quantite * l.ligne_vente.prix_unitaire
                          for l in retour.lignes.select_related("ligne_vente")), Decimal("0"))
    disponible_retour = montant_retour - somme(retour.remboursements.all())
    bilan = solde(vente)
    trop_percu = max(Decimal("0"), bilan["paye"] - bilan["rembourse"] - (vente.total - bilan["retours"]))
    if valeur > min(disponible_retour, trop_percu):
        raise ValidationError("Remboursement supérieur au trop-perçu encaissé ou au retour.")
    remboursement = Remboursement(retour=retour, montant=valeur, motif=motif, utilisateur=acteur, cle_operation=cle)
    remboursement.full_clean()
    try:
        with transaction.atomic():
            remboursement.save()
    except IntegrityError:
        raise ValidationError("Cette référence de remboursement a déjà été utilisée. Rechargez la page.")
    from .audit import journaliser
    journaliser(acteur, "remboursement", remboursement, motif)
    return remboursement


@transaction.atomic
def refuser_retour(pk, motif, acteur):
    exiger_permission(acteur, "ventes.change_retourvente")
    retour = RetourVente.objects.select_for_update().get(pk=pk)
    if retour.statut != "BROUILLON" or not motif.strip():
        raise ValidationError("Retour en brouillon et motif requis.")
    retour.statut = "REFUSE"
    retour.save(update_fields=["statut"])
    from .audit import journaliser
    journaliser(acteur, "refus_retour", retour, motif)
    return retour


@transaction.atomic
def annuler_vente(pk, motif, acteur):
    exiger_permission(acteur, "ventes.change_vente")
    vente = Vente.objects.select_for_update().get(pk=pk)
    if vente.statut != "BROUILLON" or not motif.strip():
        raise ValidationError("Seul un brouillon peut être annulé, avec un motif.")
    vente.statut = "ANNULEE"
    vente.save(update_fields=["statut"])
    from .audit import journaliser
    journaliser(acteur, "annulation", vente, motif)
    return vente


@transaction.atomic
def decider_quarantaine(ligne_id, decision, motif, acteur, lot_id=None):
    from django.conf import settings
    from stock.models import LotStock, MouvementStock
    from .models import LigneRetour, DecisionQuarantaine
    exiger_permission(acteur, "ventes.add_decisionquarantaine")
    ligne = LigneRetour.objects.select_for_update().select_related("retour", "ligne_vente").get(pk=ligne_id)
    if ligne.retour.statut != "VALIDE" or not motif.strip():
        raise ValidationError("Retour validé et justification obligatoires.")
    if DecisionQuarantaine.objects.filter(ligne_retour=ligne).exists():
        raise ValidationError("Une décision a déjà été enregistrée.")
    if decision not in dict(DecisionQuarantaine._meta.get_field("decision").choices):
        raise ValidationError("Décision inconnue.")
    lot = None
    if decision == "REINTEGRER":
        if not settings.AUTORISER_REMISE_STOCK_RETOURS:
            raise ValidationError("La remise en stock nécessite une politique métier explicitement activée dans la configuration.")
        exiger_permission(acteur, "stock.change_lotstock")
        from django.utils import timezone
        try:
            lot_id = lot_id or ligne.lot_origine_id
            if ligne.lot_origine_id and int(lot_id) != ligne.lot_origine_id:
                raise ValidationError("La remise en stock doit concerner le lot réellement retourné.")
            lot = LotStock.objects.select_for_update().get(pk=int(lot_id))
        except (ValueError, TypeError, LotStock.DoesNotExist):
            raise ValidationError("Lot d’origine invalide.")
        if lot.bloque or lot.date_peremption <= timezone.localdate():
            raise ValidationError("Ce lot est bloqué ou périmé.")
        utilise = ligne.ligne_vente.lots_utilises.filter(lot=lot).aggregate(total=Sum("quantite"))["total"] or 0
        reintegre = DecisionQuarantaine.objects.filter(
            ligne_retour__ligne_vente=ligne.ligne_vente, lot=lot, decision="REINTEGRER",
        ).aggregate(total=Sum("ligne_retour__quantite"))["total"] or 0
        if reintegre + ligne.quantite > utilise:
            raise ValidationError("Quantité non justifiée par les lots de la vente. Scindez la demande par lot.")
        lot.quantite += ligne.quantite
        lot.save(update_fields=["quantite"])
        MouvementStock.objects.create(lot=lot, type_mouvement="RETOUR", quantite=ligne.quantite,
                                     motif=f"Décision retour {ligne.retour_id} : {motif}", utilisateur=acteur)
    resultat = DecisionQuarantaine.objects.create(ligne_retour=ligne, decision=decision,
                                                motif=motif, utilisateur=acteur, lot=lot)
    from .audit import journaliser
    journaliser(acteur, "decision_quarantaine", resultat, motif)
    return resultat
