"""Registre explicite des écrans et des champs modifiables."""
from achats.models import CommandeAchat, LigneAchat, ReceptionAchat, LigneReception
from clients.models import Client
from fournisseurs.models import Fournisseur
from medicaments.models import Categorie, Medicament
from stock.models import LotStock, MouvementStock
from ventes.models import Vente, LigneVente, Paiement, RetourVente, LigneRetour, Remboursement, EvenementAudit


ECRANS = {
    "medicaments": (Medicament, "Médicaments", ["nom_commercial", "denomination_generique", "categorie", "forme", "dosage", "laboratoire", "code_barres", "photo", "prix_achat", "prix_vente", "seuil_alerte", "actif", "prescription_requise"]),
    "categories": (Categorie, "Catégories", ["nom", "description"]),
    "fournisseurs": (Fournisseur, "Fournisseurs", ["nom", "adresse", "telephone", "email", "numero_fiscal", "contact_principal", "actif"]),
    "clients": (Client, "Clients", ["nom", "telephone", "email", "adresse", "actif"]),
    "achats": (CommandeAchat, "Achats", ["fournisseur"]),
    "lignes-achats": (LigneAchat, "Lignes d’achat", ["commande", "medicament", "quantite", "prix_unitaire"]),
    "receptions": (ReceptionAchat, "Réceptions", ["commande"]),
    "lignes-receptions": (LigneReception, "Lignes de réception", ["reception", "ligne_achat", "numero_lot", "date_peremption", "quantite_recue"]),
    "stocks": (LotStock, "Stocks et lots", []),
    "mouvements": (MouvementStock, "Mouvements de stock", []),
    "ventes": (Vente, "Ventes", ["client"]),
    "lignes-ventes": (LigneVente, "Lignes de vente", ["vente", "medicament", "quantite", "lot_demande"]),
    "paiements": (Paiement, "Paiements", []),
    "retours": (RetourVente, "Retours en quarantaine", ["vente", "motif"]),
    "lignes-retours": (LigneRetour, "Lignes de retour", ["retour", "ligne_vente", "quantite", "lot_origine"]),
    "remboursements": (Remboursement, "Remboursements", []),
    "audit": (EvenementAudit, "Journal d’audit", []),
}


def permission(model, action):
    return f"{model._meta.app_label}.{action}_{model._meta.model_name}"
