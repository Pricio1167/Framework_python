from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from utilisateurs.permissions import exiger_permission
from .catalogue import ECRANS, permission


def ecran(slug):
    if slug not in ECRANS:
        raise Http404
    return ECRANS[slug]


def verifier_brouillon(obj):
    """Les parents sont verrouillés dans la transaction appelante."""
    relations = {
        "LigneVente": ("vente",), "LigneAchat": ("commande",),
        "LigneReception": ("reception",), "LigneRetour": ("retour",),
    }
    for nom in relations.get(type(obj).__name__, ()):
        if hasattr(obj, nom):
            parent = getattr(obj, nom)
            parent = type(parent).objects.select_for_update().get(pk=parent.pk)
            if getattr(parent, "statut", "BROUILLON") != "BROUILLON" or getattr(parent, "validee", False):
                raise ValidationError("Cette opération est déjà confirmée et ne peut plus être modifiée.")
    if getattr(obj, "statut", "BROUILLON") != "BROUILLON" or getattr(obj, "validee", False):
        raise ValidationError("Seuls les brouillons sont modifiables.")


@login_required
def liste(request, slug):
    model, titre, champs = ecran(slug)
    exiger_permission(request.user, permission(model, "view"))
    objets = model.objects.all().order_by("-pk")
    relations = [champ.name for champ in model._meta.fields if champ.many_to_one]
    if relations:
        objets = objets.select_related(*relations)
    if slug == "ventes":
        objets = objets.prefetch_related("lignes")
    elif slug == "achats":
        objets = objets.prefetch_related("lignes")
    elif slug == "receptions":
        objets = objets.prefetch_related("lignes__ligne_achat")
    tris = {"recent": ("Plus récents", "-pk"), "ancien": ("Plus anciens", "pk")}
    noms = {champ.name for champ in model._meta.fields}
    if "nom_commercial" in noms or "nom" in noms:
        tris["nom"] = ("Nom de A à Z", "nom_commercial" if "nom_commercial" in noms else "nom")
    if "date_peremption" in noms:
        tris["peremption"] = ("Péremption la plus proche", "date_peremption")
    tri = request.GET.get("tri", "recent")
    if tri not in tris:
        tri = "recent"
    objets = objets.order_by(tris[tri][1], "pk")
    etats = []
    categories = []
    categorie = request.GET.get("categorie", "")
    if slug == "medicaments":
        from medicaments.models import Categorie
        categories = Categorie.objects.all()
        if categorie.isdecimal() and len(categorie) < 19:
            objets = objets.filter(categorie_id=int(categorie))
    if "statut" in noms:
        etats = list(model._meta.get_field("statut").choices)
        if request.GET.get("etat") in dict(etats):
            objets = objets.filter(statut=request.GET["etat"])
    filtre_stock = request.GET.get("stock", "")
    if slug == "stocks" and filtre_stock:
        from datetime import timedelta
        from django.utils import timezone
        jour = timezone.localdate()
        if filtre_stock == "perimes":
            objets = objets.filter(date_peremption__lte=jour, quantite__gt=0)
        elif filtre_stock == "proches":
            objets = objets.filter(date_peremption__gt=jour, date_peremption__lte=jour+timedelta(days=30), quantite__gt=0)
        elif filtre_stock == "bloques":
            objets = objets.filter(bloque=True)
    recherche = request.GET.get("q", "").strip()[:150]
    if recherche:
        filtre = Q()
        for champ in model._meta.fields:
            if champ.get_internal_type() in ("CharField", "TextField"):
                filtre |= Q(**{f"{champ.name}__icontains": recherche})
        relations_recherche = {
            "stocks": ("medicament__nom_commercial",),
            "ventes": ("client__nom",), "achats": ("fournisseur__nom",),
            "mouvements": ("lot__numero_lot", "lot__medicament__nom_commercial"),
        }
        for nom in relations_recherche.get(slug, ()):
            filtre |= Q(**{f"{nom}__icontains": recherche})
        objets = objets.filter(filtre)
    colonnes = [f for f in model._meta.fields if f.name not in ("id", "utilisateur", "instantane_facture", "instantane_document", "controle_delivrance", "cle_operation")][:7]
    if slug == "medicaments":
        colonnes = [model._meta.get_field(nom) for nom in (
            "nom_commercial", "categorie", "dosage", "prix_vente", "seuil_alerte", "actif",
        )]
    page = Paginator(objets, 20).get_page(request.GET.get("page"))
    lignes = []
    for obj in page:
        valeurs = []
        cellules = []
        for champ in colonnes:
            valeur = getattr(obj, champ.name)
            type_cellule = "texte"
            ton = ""
            if champ.choices:
                code = valeur
                valeur = getattr(obj, f"get_{champ.name}_display")()
                if champ.name == "statut":
                    type_cellule = "etat"
                    ton = "success" if code in ("VALIDEE", "VALIDE", "RECUE", "CONFIRME") else "danger" if code in ("ANNULEE", "REFUSE") else "warning"
            elif champ.get_internal_type() == "BooleanField":
                valeur = "Oui" if valeur else "Non"
                type_cellule = "etat"
                ton = "danger" if champ.name == "bloque" and getattr(obj, champ.name) else "success" if getattr(obj, champ.name) else ""
            elif champ.get_internal_type() == "DecimalField":
                type_cellule = "montant"
            valeurs.append(valeur)
            cellules.append({"valeur": valeur, "type": type_cellule, "ton": ton})
        if slug == "medicaments":
            from stock.services import stock_disponible
            cellules.append({"valeur": stock_disponible(obj), "type": "texte"})
        elif slug in ("ventes", "achats", "receptions"):
            cellules.append({"valeur": obj.total, "type": "montant"})
        modifiable = getattr(obj, "statut", "BROUILLON") == "BROUILLON" and not getattr(obj, "validee", False)
        parents = {"lignes-ventes": "vente", "lignes-achats": "commande",
                   "lignes-receptions": "reception", "lignes-retours": "retour"}
        if slug in parents:
            parent = getattr(obj, parents[slug])
            modifiable = modifiable and getattr(parent, "statut", "BROUILLON") == "BROUILLON" and not getattr(parent, "validee", False)
        lignes.append({"objet": obj, "valeurs": valeurs, "cellules": cellules, "modifiable": modifiable})
    if slug in ("medicaments", "ventes", "achats", "receptions"):
        colonnes.append({"verbose_name": "Stock disponible" if slug == "medicaments" else "Total"})
    parametres = request.GET.copy()
    parametres.pop("page", None)
    return render(request, "gestion/liste.html", {
        "titre": titre, "slug": slug, "colonnes": colonnes,
        "lignes": lignes, "page": page, "q": recherche,
        "parametres_pagination": parametres.urlencode(),
        "tris": [(cle, valeur[0]) for cle, valeur in tris.items()], "tri": tri,
        "etats": etats, "etat": request.GET.get("etat", ""), "filtre_stock": filtre_stock,
        "categories": categories, "categorie": categorie,
        "ajout": bool(champs) and request.user.has_perm(permission(model, "add")),
        "modification": bool(champs) and request.user.has_perm(permission(model, "change")),
    })


@login_required
@transaction.atomic
def formulaire(request, slug, pk=None):
    model, titre, champs = ecran(slug)
    if not champs:
        raise Http404
    exiger_permission(request.user, permission(model, "change" if pk else "add"))
    obj = get_object_or_404(model.objects.select_for_update(), pk=pk) if pk else model()
    form_class = modelform_factory(model, fields=champs)
    initial = {}
    for nom in ("commande", "reception", "vente", "retour"):
        valeur = request.GET.get(nom, "")
        if nom in champs and valeur.isdecimal():
            initial[nom] = valeur
    form = form_class(request.POST if request.method == "POST" else None,
                      request.FILES if request.method == "POST" else None, instance=obj, initial=initial)
    if pk:
        for nom in ("vente", "commande", "reception", "retour", "ligne_vente", "ligne_achat"):
            if nom in form.fields:
                form.fields[nom].disabled = True
    for champ in form.fields.values():
        champ.widget.attrs["class"] = "form-control"
    if "photo" in form.fields:
        form.fields["photo"].widget.attrs["accept"] = "image/jpeg,image/png,image/webp"
        form.fields["photo"].help_text = "JPEG, PNG ou WebP · 5 Mo maximum."
    if slug == "lignes-ventes":
        from ventes.forms import LigneVenteForm
        choix = LigneVenteForm(request.POST if request.method == "POST" else None)
        form.fields["medicament"].queryset = choix.fields["medicament"].queryset
        form.fields["lot_demande"].queryset = choix.fields["lot_demande"].queryset
    if request.method == "POST" and form.is_valid():
        try:
            nouveau = form.save(commit=False)
            if hasattr(nouveau, "utilisateur_id") and not pk:
                nouveau.utilisateur = request.user
            verifier_brouillon(nouveau)
            if slug == "lignes-ventes":
                from ventes.operations import ajouter_ligne
                nouveau = ajouter_ligne(nouveau.vente_id, nouveau.medicament, nouveau.quantite, request.user,
                                        ligne_id=pk, lot_demande=nouveau.lot_demande)
            else:
                nouveau.full_clean()
                nouveau.save()
        except ValidationError as erreur:
            form.add_error(None, " ; ".join(erreur.messages))
        else:
            messages.success(request, "Enregistrement effectué.")
            if slug in ("achats", "receptions"):
                return redirect("gestion_detail", slug=slug, pk=nouveau.pk)
            if slug == "ventes":
                return redirect("vente_detail", pk=nouveau.pk)
            return redirect("gestion_liste", slug=slug)
    return render(request, "gestion/formulaire.html", {"titre": titre, "form": form, "slug": slug})


@login_required
@require_POST
@transaction.atomic
def operation(request, slug, pk):
    model, _, _ = ecran(slug)
    exiger_permission(request.user, permission(model, "change"))
    obj = get_object_or_404(model.objects.select_for_update(), pk=pk)
    try:
        if slug == "receptions":
            from achats.services import valider_reception
            valider_reception(obj.pk)
            from ventes.audit import journaliser
            journaliser(request.user, "validation_reception", obj, "Entrées de stock confirmées")
        elif slug == "achats":
            from achats.operations import commander, annuler_commande
            if request.POST.get("action") == "annuler":
                annuler_commande(obj.pk, request.user, request.POST.get("motif", ""))
            else:
                commander(obj.pk, request.user)
        elif slug == "stocks":
            from stock.operations import inventorier, mouvement_manuel
            if request.POST.get("action") == "inventaire":
                inventorier(pk, request.POST.get("quantite"), request.POST.get("motif", ""), request.user)
            elif request.POST.get("action") in ("ENTREE", "SORTIE"):
                mouvement_manuel(pk, request.POST["action"], request.POST.get("quantite"),
                                 request.POST.get("motif", ""), request.user)
            else:
                if not request.POST.get("motif", "").strip():
                    raise ValidationError("Motif obligatoire.")
                obj.bloque = not obj.bloque
                obj.save(update_fields=["bloque"])
                from ventes.audit import journaliser
                journaliser(request.user, "blocage" if obj.bloque else "déblocage", obj, request.POST["motif"])
        else:
            raise Http404
    except ValidationError as erreur:
        messages.error(request, " ; ".join(erreur.messages))
    else:
        messages.success(request, "Opération effectuée.")
    if slug in ("achats", "receptions", "stocks"):
        return redirect("gestion_detail", slug=slug, pk=pk)
    return redirect("gestion_liste", slug=slug)


@login_required
@require_POST
@transaction.atomic
def supprimer_ligne(request, slug, pk):
    if slug != "lignes-ventes":
        raise Http404
    model, _, _ = ecran(slug)
    exiger_permission(request.user, permission(model, "delete"))
    obj = get_object_or_404(model.objects.select_for_update(), pk=pk)
    try:
        from ventes.operations import supprimer_ligne
        supprimer_ligne(obj.vente_id, obj.pk, request.user)
    except ValidationError as erreur:
        messages.error(request, " ; ".join(erreur.messages))
    return redirect("gestion_liste", slug=slug)
