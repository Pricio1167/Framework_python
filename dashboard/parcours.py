from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db import transaction
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render

from achats.models import CommandeAchat, LigneAchat, ReceptionAchat, LigneReception
from stock.models import LotStock
from utilisateurs.permissions import exiger_permission
from .catalogue import permission
from .gestion import verifier_brouillon


@login_required
@transaction.atomic
def detail(request, slug, pk):
    definition = {
        "achats": (CommandeAchat, LigneAchat, "commande", ["medicament", "quantite", "prix_unitaire"]),
        "receptions": (ReceptionAchat, LigneReception, "reception", ["ligne_achat", "numero_lot", "date_peremption", "quantite_recue"]),
        "stocks": (LotStock, None, None, []),
    }
    if slug not in definition:
        raise Http404
    model, model_ligne, relation, champs = definition[slug]
    exiger_permission(request.user, permission(model, "view"))
    objet = get_object_or_404(model.objects.select_for_update(), pk=pk)
    form = None
    if model_ligne and request.user.has_perm(permission(model_ligne, "add")):
        instance = model_ligne(**{relation: objet})
        classe = modelform_factory(model_ligne, fields=champs)
        form = classe(request.POST or None, instance=instance)
        if slug == "receptions":
            form.fields["ligne_achat"].queryset = objet.commande.lignes.all()
        for champ in form.fields.values():
            champ.widget.attrs["class"] = "form-control"
        if request.method == "POST" and form.is_valid():
            try:
                verifier_brouillon(instance)
                instance.full_clean()
                instance.save()
            except ValidationError as erreur:
                form.add_error(None, " ; ".join(erreur.messages))
            else:
                messages.success(request, "Ligne enregistrée.")
                return redirect("gestion_detail", slug=slug, pk=pk)
    elif request.method == "POST":
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied
    modifiable = getattr(objet, "statut", "BROUILLON") == "BROUILLON" and not getattr(objet, "validee", False)
    return render(request, "gestion/detail.html", {
        "objet": objet, "slug": slug, "form": form if modifiable else None,
        "lignes": objet.lignes.all() if model_ligne else [],
        "mouvements": objet.mouvements.select_related("utilisateur").order_by("-pk")[:100] if slug == "stocks" else [],
    })
