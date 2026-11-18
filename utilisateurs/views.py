from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm
from django.forms import modelform_factory
from django.shortcuts import get_object_or_404, redirect, render
from django.db import transaction
from ventes.audit import journaliser

from .permissions import exiger_permission


@login_required
def liste(request):
    exiger_permission(request.user, "utilisateurs.view_utilisateur")
    return render(request, "utilisateurs/liste.html", {
        "utilisateurs": get_user_model().objects.prefetch_related("groups").order_by("username"),
    })


@login_required
@transaction.atomic
def modifier(request, pk=None):
    exiger_permission(request.user, "utilisateurs.change_utilisateur" if pk else "utilisateurs.add_utilisateur")
    exiger_permission(request.user, "auth.change_group")
    model = get_user_model()
    obj = get_object_or_404(model, pk=pk) if pk else None
    if obj and obj.is_superuser and not request.user.is_superuser:
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied("Seul un superutilisateur peut modifier ce compte.")
    if pk:
        classe = modelform_factory(model, fields=["first_name", "last_name", "email", "telephone", "is_active", "groups"])
    else:
        class CreationUtilisateur(UserCreationForm):
            class Meta(UserCreationForm.Meta):
                model = get_user_model()
                fields = ("username", "first_name", "last_name", "email", "telephone", "groups")
        classe = CreationUtilisateur
    form = classe(request.POST or None, instance=obj)
    for champ in form.fields.values():
        champ.widget.attrs["class"] = "form-control"
    if request.method == "POST" and form.is_valid():
        compte = form.save()
        journaliser(request.user, "modification_compte" if pk else "creation_compte", compte,
                    "Gestion des informations du compte et de ses rôles")
        return redirect("utilisateurs_liste")
    return render(request, "utilisateurs/formulaire.html", {"form": form})
