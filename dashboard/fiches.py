from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models.deletion import ProtectedError
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator

from achats.models import CommandeAchat
from stock.services import stock_disponible
from utilisateurs.permissions import exiger_permission
from ventes.audit import journaliser
from ventes.models import Vente
from .catalogue import ECRANS, permission


@login_required
def detail(request, slug, pk):
    if slug not in ("medicaments", "fournisseurs", "clients", "categories"):
        raise Http404
    model, titre, _ = ECRANS[slug]
    exiger_permission(request.user, permission(model, "view"))
    objet = get_object_or_404(model, pk=pk)
    contexte = {"objet": objet, "slug": slug, "titre": titre,
                "peut_modifier": request.user.has_perm(permission(model, "change")),
                "peut_supprimer": request.user.has_perm(permission(model, "delete"))}
    if slug == "medicaments":
        contexte["disponible"] = stock_disponible(objet)
        if request.user.has_perm("stock.view_lotstock"):
            contexte["lots"] = objet.lots.all()
    if slug == "fournisseurs" and request.user.has_perm("achats.view_commandeachat"):
        commandes = CommandeAchat.objects.filter(fournisseur=objet).prefetch_related("lignes", "receptions__lignes__ligne_achat")
        contexte["page_historique"] = Paginator(commandes, 20).get_page(request.GET.get("page"))
        contexte["commandes"] = contexte["page_historique"]
        contexte["receptions"] = contexte["page_historique"]
    if slug == "clients" and request.user.has_perm("ventes.view_vente"):
        ventes = Vente.objects.filter(client=objet).prefetch_related("lignes")
        contexte["page_historique"] = Paginator(ventes, 20).get_page(request.GET.get("page"))
        contexte["ventes_client"] = contexte["page_historique"]
    if slug == "categories":
        contexte["nombre_medicaments"] = objet.medicaments.count()
    return render(request, "gestion/fiche.html", contexte)


@login_required
@require_POST
@transaction.atomic
def action(request, slug, pk):
    if slug not in ("medicaments", "fournisseurs", "clients", "categories"):
        raise Http404
    model, _, _ = ECRANS[slug]
    supprimer = request.POST.get("action") == "supprimer"
    exiger_permission(request.user, permission(model, "delete" if supprimer else "change"))
    objet = get_object_or_404(model.objects.select_for_update(), pk=pk)
    try:
        if supprimer:
            objet.delete()
            objet.pk = pk
            journaliser(request.user, "suppression_reference", objet, "Suppression d’une fiche sans dépendance protégée")
        else:
            if not hasattr(objet, "actif"):
                raise ValidationError("Cette fiche ne possède pas de statut d’archivage.")
            objet.actif = False
            objet.save(update_fields=["actif"])
            journaliser(request.user, "archivage_reference", objet, "Désactivation sans effacer l’historique")
    except ProtectedError:
        messages.error(request, "Suppression interdite : cette fiche est utilisée dans l’historique. Archivez-la si possible.")
    except ValidationError as erreur:
        messages.error(request, " ; ".join(erreur.messages))
    else:
        messages.success(request, "Fiche supprimée." if supprimer else "Fiche archivée, historique conservé.")
        return redirect("gestion_liste", slug=slug)
    return redirect("fiche_detail", slug=slug, pk=pk)
