from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def ariary(valeur):
    try:
        montant = Decimal(str(valeur))
        if not montant.is_finite():
            return "—"
        return f"{montant:,.2f}".replace(",", " ").replace(".", ",") + " Ar"
    except (InvalidOperation, TypeError, ValueError):
        return "—"
