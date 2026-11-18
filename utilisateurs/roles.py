"""Attributions minimales des rôles PHARMAGEST, sans retrait de droits locaux."""
from django.contrib.auth.models import Group, Permission
from django.db import transaction


ROLES = {
    "Responsable de gestion": {
        "ventes": ("view_vente", "view_lignevente", "view_paiement", "view_retourvente", "view_remboursement"),
        "achats": ("view_commandeachat", "view_ligneachat", "view_receptionachat", "view_lignereception"),
        "medicaments": ("view_medicament", "view_categorie"),
        "stock": ("view_lotstock", "view_mouvementstock"),
    },
    "Pharmacien": {
        "medicaments": ("view_medicament", "view_categorie"),
        "stock": ("view_lotstock",),
        "clients": ("view_client", "add_client", "change_client"),
        "ventes": ("view_vente", "add_vente", "change_vente", "view_lignevente",
                   "add_lignevente", "change_lignevente", "delete_lignevente",
                   "view_retourvente", "add_retourvente", "change_retourvente",
                   "add_ligneretour", "view_ligneretour", "view_paiement", "confirmer_paiement"),
    },
    "Gestionnaire de stock": {
        "medicaments": ("view_medicament", "add_medicament", "change_medicament",
                        "view_categorie", "add_categorie", "change_categorie"),
        "fournisseurs": ("view_fournisseur", "add_fournisseur", "change_fournisseur"),
        "achats": ("view_commandeachat", "add_commandeachat", "change_commandeachat",
                   "view_ligneachat", "add_ligneachat", "change_ligneachat",
                   "view_receptionachat", "add_receptionachat", "change_receptionachat",
                   "view_lignereception", "add_lignereception"),
        "stock": ("view_lotstock", "change_lotstock", "view_mouvementstock", "add_mouvementstock"),
    },
    "Caissier": {
        "medicaments": ("view_medicament", "view_categorie"),
        "clients": ("view_client", "add_client", "change_client"),
        "ventes": ("view_vente", "add_vente", "view_lignevente", "add_lignevente",
                   "delete_lignevente", "view_paiement", "add_paiement"),
    },
}


@transaction.atomic
def configurer_roles():
    groupes = []
    administrateur, _ = Group.objects.get_or_create(name="Administrateur")
    administrateur.permissions.add(*Permission.objects.filter(
        content_type__app_label__in=[
            "utilisateurs", "auth", "medicaments", "clients", "fournisseurs",
            "achats", "stock", "ventes", "rapports", "dashboard",
        ]
    ))
    groupes.append(administrateur)
    for nom, applications in ROLES.items():
        groupe, _ = Group.objects.get_or_create(name=nom)
        for application, codes in applications.items():
            groupe.permissions.add(*Permission.objects.filter(
                content_type__app_label=application, codename__in=codes,
            ))
        groupes.append(groupe)
    return groupes
