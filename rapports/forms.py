from django import forms


class PeriodeForm(forms.Form):
    date_debut = forms.DateField(required=False, label="Du", widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))
    date_fin = forms.DateField(required=False, label="Au", widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}))

    def clean(self):
        valeurs = super().clean()
        debut, fin = valeurs.get("date_debut"), valeurs.get("date_fin")
        if debut and fin and debut > fin:
            raise forms.ValidationError("La date de début doit précéder la date de fin.")
        return valeurs
