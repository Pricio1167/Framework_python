from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.forms import modelform_factory
from django.shortcuts import redirect, render

from utilisateurs.permissions import exiger_permission
from .models import ParametresPharmacie


def identite_pharmacie():
    parametres = ParametresPharmacie.objects.filter(pk=1).first()
    return {"pharmacie": parametres.nom if parametres else settings.PHARMACIE_NOM,
            "adresse": parametres.adresse if parametres else settings.PHARMACIE_ADRESSE,
            "mentions": parametres.mentions if parametres else settings.PHARMACIE_MENTIONS}


@login_required
def modifier(request):
    exiger_permission(request.user, "dashboard.change_parametrespharmacie")
    instance = ParametresPharmacie.objects.filter(pk=1).first()
    if not instance:
        instance = ParametresPharmacie(pk=1, nom=settings.PHARMACIE_NOM,
                                       adresse=settings.PHARMACIE_ADRESSE, mentions=settings.PHARMACIE_MENTIONS)
    classe = modelform_factory(ParametresPharmacie, fields=["nom", "adresse", "mentions"])
    form = classe(request.POST or None, instance=instance)
    for champ in form.fields.values():
        champ.widget.attrs["class"] = "form-control"
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Paramètres enregistrés.")
        return redirect("parametres_pharmacie")
    return render(request, "gestion/parametres.html", {"form": form})
