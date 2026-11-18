"""Définitions communes des encaissements, retours et soldes de vente."""
from decimal import Decimal
from django.db.models import Sum

from .models import Remboursement


def somme(queryset):
    return queryset.aggregate(total=Sum("montant"))["total"] or Decimal("0.00")


def total_retours(vente):
    return sum((ligne.quantite * ligne.ligne_vente.prix_unitaire
                for retour in vente.retours.filter(statut="VALIDE")
                for ligne in retour.lignes.select_related("ligne_vente")), Decimal("0.00"))


def solde(vente):
    rembourse = somme(Remboursement.objects.filter(retour__vente=vente))
    encaisse = somme(vente.paiements.filter(statut="CONFIRME"))
    attente = somme(vente.paiements.filter(statut="EN_ATTENTE"))
    retours = total_retours(vente)
    reste = max(Decimal("0.00"), vente.total - retours - encaisse + rembourse)
    return {"retours": retours, "paye": encaisse, "en_attente": attente, "rembourse": rembourse,
            "reste": reste, "encaissable": max(Decimal("0.00"), reste - attente)}
