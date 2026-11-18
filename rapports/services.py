
from datetime import timedelta
from decimal import Decimal

from django.db.models import Sum
from django.utils import timezone

from ventes.models import Vente, Paiement
from stock.models import LotStock
from stock.services import medicaments_stock_faible


def rapport_ventes(date_debut=None, date_fin=None):
    ventes = Vente.objects.filter(statut="VALIDEE")

    if date_debut:
        ventes = ventes.filter(date_vente__date__gte=date_debut)

    if date_fin:
        ventes = ventes.filter(date_vente__date__lte=date_fin)

    chiffre_affaires = Decimal("0.00")

    for vente in ventes.prefetch_related("lignes"):
        chiffre_affaires += vente.total

    paiements = Paiement.objects.filter(
        vente__in=ventes, statut="CONFIRME"
    )

    montant_encaisse = (
        paiements.aggregate(total=Sum("montant"))["total"]
        or Decimal("0.00")
    )
    from ventes.operations import solde
    bilans = [solde(vente) for vente in ventes]
    retours = sum((b["retours"] for b in bilans), Decimal("0"))
    remboursements = sum((b["rembourse"] for b in bilans), Decimal("0"))

    return {
        "nombre_ventes": ventes.count(),
        "chiffre_affaires": chiffre_affaires,
        "chiffre_affaires_net": chiffre_affaires - retours,
        "retours": retours,
        "remboursements": remboursements,
        "encaissement_net": montant_encaisse - remboursements,
        "montant_encaisse": montant_encaisse,
        "reste_a_payer": sum((b["reste"] for b in bilans), Decimal("0")),
    }


def rapport_stock(jours_alerte=30):
    aujourd_hui = timezone.localdate()
    date_limite = aujourd_hui + timedelta(days=jours_alerte)

    lots_perimes = LotStock.objects.filter(
        date_peremption__lte=aujourd_hui,
        quantite__gt=0,
    ).select_related("medicament")

    lots_proches = LotStock.objects.filter(
        date_peremption__gt=aujourd_hui,
        date_peremption__lte=date_limite,
        quantite__gt=0,
    ).select_related("medicament")

    return {
        "medicaments_stock_faible": medicaments_stock_faible(),
        "lots_proches_peremption": lots_proches,
        "lots_perimes": lots_perimes,
    }


def evolution_ventes(jours=7):
    """Même définition des montants que les rapports, regroupée par jour de vente."""
    aujourd_hui = timezone.localdate()
    resultats = []
    for recul in range(jours - 1, -1, -1):
        date = aujourd_hui - timedelta(days=recul)
        bilan = rapport_ventes(date, date)
        resultats.append({"date": date.strftime("%d/%m"),
                          "brut": str(bilan["chiffre_affaires"]),
                          "net": str(bilan["chiffre_affaires_net"])})
    return resultats


def rapport_achats(date_debut=None, date_fin=None):
    from achats.models import CommandeAchat, ReceptionAchat
    commandes = CommandeAchat.objects.exclude(statut__in=["BROUILLON", "ANNULEE"])
    receptions = ReceptionAchat.objects.filter(validee=True)
    if date_debut:
        commandes = commandes.filter(date_commande__date__gte=date_debut)
        receptions = receptions.filter(date_reception__date__gte=date_debut)
    if date_fin:
        commandes = commandes.filter(date_commande__date__lte=date_fin)
        receptions = receptions.filter(date_reception__date__lte=date_fin)
    commandes = commandes.select_related("fournisseur").prefetch_related("lignes")
    receptions = receptions.select_related("commande__fournisseur").prefetch_related("lignes__ligne_achat")
    return {"nombre_commandes": commandes.count(), "nombre_receptions": receptions.count(),
            "montant_commandes": sum((c.total for c in commandes), Decimal("0.00")),
            "montant_receptionne": sum((r.total for r in receptions), Decimal("0.00")),
            "commandes": commandes, "receptions": receptions}
