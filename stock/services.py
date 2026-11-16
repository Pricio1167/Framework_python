
from datetime import timedelta

from django.db.models import Sum
from django.utils import timezone

from medicaments.models import Medicament
from .models import LotStock


def stock_disponible(medicament):
    """Calcule le stock vendable d'un medicament."""
    aujourd_hui = timezone.localdate()

    return (
        LotStock.objects.filter(
            medicament=medicament,
            bloque=False,
            date_peremption__gt=aujourd_hui,
            quantite__gt=0,
        ).aggregate(total=Sum("quantite"))["total"]
        or 0
    )


def medicaments_stock_faible():
    """Retourne les medicaments sous leur seuil d'alerte."""
    resultats = []

    for medicament in Medicament.objects.filter(actif=True):
        quantite = stock_disponible(medicament)

        if quantite <= medicament.seuil_alerte:
            resultats.append({
                "medicament": medicament,
                "quantite": quantite,
                "seuil": medicament.seuil_alerte,
            })

    return resultats


def lots_proches_peremption(jours=30):
    """Liste les lots expirant dans les prochains jours."""
    aujourd_hui = timezone.localdate()
    limite = aujourd_hui + timedelta(days=jours)

    return LotStock.objects.filter(
        date_peremption__gt=aujourd_hui,
        date_peremption__lte=limite,
        quantite__gt=0,
    ).select_related("medicament").order_by("date_peremption")


def lots_perimes():
    """Liste les lots perimes ayant encore du stock."""
    return LotStock.objects.filter(
        date_peremption__lte=timezone.localdate(),
        quantite__gt=0,
    ).select_related("medicament").order_by("date_peremption")


def lots_fefo(medicament):
    """Retourne les lots vendables par date de peremption."""
    return LotStock.objects.filter(
        medicament=medicament,
        bloque=False,
        date_peremption__gt=timezone.localdate(),
        quantite__gt=0,
    ).order_by("date_peremption", "pk")
