from django import forms

from clients.models import Client
from medicaments.models import Medicament
from .models import Paiement
from stock.models import LotStock
from django.utils import timezone


class CreationVenteForm(forms.Form):
    client = forms.ModelChoiceField(queryset=Client.objects.filter(actif=True), required=False)


class LigneVenteForm(forms.Form):
    medicament = forms.ModelChoiceField(queryset=Medicament.objects.filter(actif=True), label="Médicament")
    quantite = forms.IntegerField(min_value=1, label="Quantité")
    lot_demande = forms.ModelChoiceField(queryset=LotStock.objects.none(), required=False, label="Lot (facultatif)",
                                         empty_label="Allocation automatique FEFO")

    def __init__(self, *args, recherche="", **kwargs):
        super().__init__(*args, **kwargs)
        lots = LotStock.objects.filter(bloque=False, date_peremption__gt=timezone.localdate(), quantite__gt=0)
        medicaments = Medicament.objects.filter(actif=True, lots__in=lots).distinct()
        if recherche:
            from django.db.models import Q
            medicaments = medicaments.filter(Q(nom_commercial__icontains=recherche) | Q(code_barres__iexact=recherche))
        self.fields["medicament"].queryset = medicaments
        valeur = self.data.get("medicament") if self.is_bound else None
        if valeur and str(valeur).isdecimal() and len(str(valeur)) < 19:
            lots = lots.filter(medicament_id=valeur)
        else:
            lots = lots.filter(medicament__in=medicaments)
        self.fields["lot_demande"].queryset = lots.select_related("medicament")


class PaiementForm(forms.Form):
    montant = forms.DecimalField(min_value="0.01", max_digits=12, decimal_places=2, label="Montant (Ar)")
    mode = forms.ChoiceField(choices=Paiement.MODES)
