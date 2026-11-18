from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from uuid import uuid4

from utilisateurs.permissions import exiger_permission
from .models import Vente, RetourVente, LigneRetour
from .forms import CreationVenteForm, LigneVenteForm
from django.db import transaction
from .operations import solde, confirmer_vente, payer, confirmer_retour, rembourser, annuler_vente, refuser_retour, decider_quarantaine


def identifiant(valeur):
    try:
        return int(valeur)
    except (ValueError, TypeError):
        raise ValidationError("Identifiant invalide.")


@login_required
def detail(request, pk):
    exiger_permission(request.user, "ventes.view_vente")
    vente = get_object_or_404(Vente, pk=pk)
    return render(request, "ventes/detail.html", {
        "vente": vente, "solde": solde(vente),
        "ligne_form": LigneVenteForm(recherche=request.GET.get("produit", "").strip()[:150]),
        "recherche_produit": request.GET.get("produit", ""),
        "cle_paiement": uuid4(), "cle_remboursement": uuid4(),
    })


@login_required
def creer(request):
    exiger_permission(request.user, "ventes.add_vente")
    form = CreationVenteForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        vente = Vente.objects.create(utilisateur=request.user, client=form.cleaned_data["client"])
        return redirect("vente_detail", pk=vente.pk)
    return render(request, "ventes/creation.html", {"form": form})


@login_required
@require_POST
def ligne_ajouter(request, pk):
    from .operations import ajouter_ligne
    exiger_permission(request.user, "ventes.add_lignevente")
    vente = get_object_or_404(Vente, pk=pk)
    form = LigneVenteForm(request.POST)
    if form.is_valid():
        try:
            ajouter_ligne(vente.pk, acteur=request.user, **form.cleaned_data)
        except ValidationError as erreur:
            form.add_error(None, " ; ".join(erreur.messages))
        else:
            messages.success(request, "Ligne ajoutée à la vente.")
            return redirect("vente_detail", pk=pk)
    return render(request, "ventes/detail.html", {
        "vente": vente, "solde": solde(vente), "ligne_form": form,
        "cle_paiement": uuid4(), "cle_remboursement": uuid4(),
    }, status=400)


@login_required
@require_POST
def ligne_supprimer(request, pk, ligne_id):
    from .operations import supprimer_ligne
    exiger_permission(request.user, "ventes.delete_lignevente")
    vente = get_object_or_404(Vente, pk=pk)
    get_object_or_404(vente.lignes, pk=ligne_id)
    try:
        supprimer_ligne(pk, ligne_id, request.user)
    except ValidationError as erreur:
        messages.error(request, " ; ".join(erreur.messages))
    return redirect("vente_detail", pk=pk)


@login_required
@require_POST
@transaction.atomic
def demander_retour(request, pk):
    exiger_permission(request.user, "ventes.add_retourvente")
    exiger_permission(request.user, "ventes.add_ligneretour")
    vente = get_object_or_404(Vente.objects.select_for_update(), pk=pk)
    motif = request.POST.get("motif", "").strip()
    try:
        if vente.statut != "VALIDEE" or not motif:
            raise ValidationError("Une vente validée et un motif sont obligatoires.")
        selections = []
        for ligne in vente.lignes.all():
            quantite = identifiant(request.POST.get(f"quantite_{ligne.pk}", "0") or "0")
            if quantite < 0 or quantite > ligne.quantite:
                raise ValidationError("Quantité de retour invalide.")
            if quantite:
                from django.db.models import Sum
                deja = ligne.lignes_retour.filter(retour__statut="VALIDE").aggregate(total=Sum("quantite"))["total"] or 0
                if quantite + deja > ligne.quantite:
                    raise ValidationError("La quantité dépasse le restant retournable.")
                lots = list(ligne.lots_utilises.select_related("lot"))
                choix = request.POST.get(f"lot_{ligne.pk}", "")
                if choix:
                    lot = next((allocation.lot for allocation in lots if str(allocation.lot_id) == choix), None)
                else:
                    lot = lots[0].lot if len(lots) == 1 else None
                if lot is None:
                    raise ValidationError("Sélectionnez le lot réellement retourné pour chaque ligne concernée.")
                selections.append((ligne, quantite, lot))
        if not selections:
            raise ValidationError("Sélectionnez au moins une quantité à retourner.")
        retour = RetourVente.objects.create(vente=vente, utilisateur=request.user, motif=motif)
        LigneRetour.objects.bulk_create([LigneRetour(retour=retour, ligne_vente=ligne, quantite=q, lot_origine=lot)
                                        for ligne, q, lot in selections])
    except ValidationError as erreur:
        messages.error(request, " ; ".join(erreur.messages))
    else:
        messages.success(request, "Demande de retour créée, en attente de validation.")
    return redirect("vente_detail", pk=pk)


@login_required
@require_POST
def action(request, pk, operation):
    vente = get_object_or_404(Vente, pk=pk)
    try:
        if operation == "valider":
            confirmer_vente(pk, request.user, controle=request.POST.get("controle_delivrance", ""))
        elif operation == "payer":
            payer(pk, request.POST.get("montant"), request.POST.get("mode"), request.user,
                  cle_operation=request.POST.get("cle_operation"))
        elif operation == "annuler":
            annuler_vente(pk, request.POST.get("motif", ""), request.user)
        elif operation in ("confirmer-paiement", "refuser-paiement"):
            from .operations import verifier_paiement
            paiement = get_object_or_404(vente.paiements, pk=identifiant(request.POST.get("paiement")))
            if request.POST.get("verification_effectuee") != "oui":
                raise ValidationError("Attestez la vérification du statut auprès du moyen de paiement.")
            verifier_paiement(paiement.pk, request.user, request.POST.get("reference", ""), operation == "confirmer-paiement")
        elif operation in ("retour", "rembourser", "refuser", "quarantaine"):
            retour = get_object_or_404(vente.retours, pk=identifiant(request.POST.get("retour")))
            if operation == "retour":
                confirmer_retour(retour.pk, request.user)
            elif operation == "refuser":
                refuser_retour(retour.pk, request.POST.get("motif", ""), request.user)
            elif operation == "quarantaine":
                ligne = get_object_or_404(retour.lignes, pk=identifiant(request.POST.get("ligne")))
                decider_quarantaine(ligne.pk, request.POST.get("decision"), request.POST.get("motif", ""), request.user, request.POST.get("lot") or None)
            else:
                rembourser(retour.pk, request.POST.get("montant"), request.POST.get("motif", ""), request.user,
                           cle_operation=request.POST.get("cle_operation"))
        else:
            from django.http import Http404
            raise Http404
    except ValidationError as erreur:
        messages.error(request, " ; ".join(erreur.messages))
    else:
        messages.success(request, "Opération effectuée.")
    return redirect("vente_detail", pk=pk)
