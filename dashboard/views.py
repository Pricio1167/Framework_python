from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Sum

from achats.models import CommandeAchat
from rapports.services import rapport_ventes, rapport_stock, evolution_ventes, rapport_achats
from rapports.forms import PeriodeForm
from medicaments.models import Medicament
from ventes.models import Vente, LigneVente, LigneRetour


@login_required
def accueil(request):
    periode = PeriodeForm(request.GET)
    contexte = {"periode_form": periode}
    if request.user.has_perm("medicaments.view_medicament"):
        contexte["nombre_medicaments_actifs"] = Medicament.objects.filter(actif=True).count()
    if periode.is_valid():
        if request.user.has_perm("ventes.view_vente"):
            contexte["ventes_periode"] = rapport_ventes(**periode.cleaned_data)
        if request.user.has_perm("achats.view_commandeachat"):
            contexte["achats_periode"] = rapport_achats(**periode.cleaned_data)
    if request.user.has_perm("ventes.view_vente"):
        jour = timezone.localdate()
        contexte.update({"jour": rapport_ventes(jour, jour),
                         "mois": rapport_ventes(jour.replace(day=1), jour),
                         "ventes": Vente.objects.select_related("client").prefetch_related("lignes")[:6],
                         "evolution": evolution_ventes()})
        classement = list(LigneVente.objects.filter(vente__statut="VALIDEE").values(
            "medicament_id", "medicament__nom_commercial").annotate(quantite=Sum("quantite")))
        retours = dict(LigneRetour.objects.filter(retour__statut="VALIDE").values_list(
            "ligne_vente__medicament_id").annotate(total=Sum("quantite")))
        for ligne in classement:
            ligne["quantite"] -= retours.get(ligne["medicament_id"], 0)
        contexte["produits_populaires"] = sorted(classement, key=lambda x: x["quantite"], reverse=True)[:5]
    if request.user.has_perm("stock.view_lotstock"):
        contexte["stock"] = rapport_stock()
    if request.user.has_perm("achats.view_commandeachat"):
        contexte["achats"] = CommandeAchat.objects.select_related("fournisseur")[:5]
    return render(request, "dashboard/accueil.html", contexte)
