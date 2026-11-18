from .catalogue import ECRANS, permission
from django.urls import reverse


def navigation(request):
    liens = [
        {"slug": slug, "titre": titre, "url": reverse("gestion_liste", args=[slug])}
        for slug, (model, titre, _) in ECRANS.items()
        if request.user.has_perm(permission(model, "view"))
    ]
    rubriques = [
        ("Au quotidien", ("medicaments", "ventes", "clients", "stocks")),
        ("Approvisionnement", ("achats", "receptions", "fournisseurs")),
        ("Suivi des opérations", ("paiements", "retours", "remboursements", "mouvements", "audit")),
        ("Référentiels et lignes", ("categories", "lignes-achats", "lignes-receptions", "lignes-ventes", "lignes-retours")),
    ]
    icones = {
        "medicaments": "capsule", "ventes": "receipt", "clients": "people",
        "stocks": "boxes", "achats": "bag", "receptions": "box-arrow-in-down",
        "fournisseurs": "truck", "paiements": "credit-card", "retours": "arrow-return-left",
        "remboursements": "cash-coin", "mouvements": "arrow-left-right", "audit": "shield-check",
    }
    for lien in liens:
        lien["actif"] = request.path.startswith(lien["url"])
        lien["icone"] = icones.get(lien["slug"], "list-ul")
    groupes = []
    for titre, slugs in rubriques:
        elements = [lien for lien in liens if lien["slug"] in slugs]
        if elements:
            groupes.append({"titre": titre, "liens": elements,
                            "avance": titre == "Référentiels et lignes",
                            "ouvert": any(lien["actif"] for lien in elements)})
    return {"navigation": liens, "navigation_groupes": groupes}
