"""Données fictives et PDF de contrôle dans tmp/revue, jamais dans la base locale."""
from datetime import timedelta
import json
import os
from pathlib import Path
import secrets
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
DOSSIER = ROOT / "tmp" / "revue"
DOSSIER.mkdir(parents=True, exist_ok=True)
acces = DOSSIER / "acces.json"
if not acces.exists():
    acces.write_text(json.dumps({"secret": secrets.token_urlsafe(60), "password": secrets.token_urlsafe(20)}), encoding="utf-8")
identifiants = json.loads(acces.read_text(encoding="utf-8"))
os.environ.update({"DJANGO_SETTINGS_MODULE": "config.settings", "DB_ENGINE": "sqlite",
                   "SQLITE_PATH": str(DOSSIER / "revue.sqlite3"), "DEBUG": "true",
                   "SECRET_KEY": identifiants["secret"]})

import django
django.setup()

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import RequestFactory
from django.utils import timezone
from clients.models import Client
from fournisseurs.models import Fournisseur
from medicaments.models import Categorie, Medicament
from stock.models import LotStock
from ventes.models import Vente, LigneVente, RetourVente, LigneRetour
from ventes.operations import confirmer_vente, payer, confirmer_retour, rembourser
from ventes.documents import facture, recu, justificatif_retour, justificatif_remboursement
from rapports.pdf import generer_pdf_ventes, generer_pdf_stock
from achats.models import CommandeAchat, LigneAchat, ReceptionAchat, LigneReception
from achats.operations import commander
from achats.services import valider_reception
from achats.documents import bon_commande, bon_reception
from rapports.views import telecharger_achats, telecharger_peremptions

call_command("migrate", verbosity=0)
call_command("configurer_roles", verbosity=0)
acteur, _ = get_user_model().objects.get_or_create(username="revue_locale", defaults={"is_staff": True, "is_superuser": True})
acteur.set_password(identifiants["password"])
acteur.save()
client, _ = Client.objects.get_or_create(nom="Client fictif de vérification")
fournisseur, _ = Fournisseur.objects.get_or_create(nom="Fournisseur fictif")
categorie, _ = Categorie.objects.get_or_create(nom="Produits de démonstration")
medicament, _ = Medicament.objects.get_or_create(
    nom_commercial="Paracétamol de démonstration", defaults={"categorie": categorie, "forme": "comprime",
    "dosage": "500 mg", "prix_achat": 100, "prix_vente": 150, "seuil_alerte": 10})
lot, _ = LotStock.objects.get_or_create(medicament=medicament, numero_lot="DEMO-001", defaults={
    "date_peremption": timezone.localdate() + timedelta(days=90), "quantite": 40, "quantite_recue": 40})
LotStock.objects.get_or_create(medicament=medicament, numero_lot="DEMO-ALERTE", defaults={
    "date_peremption": timezone.localdate() + timedelta(days=15), "quantite": 5, "quantite_recue": 5})
LotStock.objects.get_or_create(medicament=medicament, numero_lot="DEMO-PERIME", defaults={
    "date_peremption": timezone.localdate() - timedelta(days=1), "quantite": 2, "quantite_recue": 2})
vente = Vente.objects.filter(utilisateur=acteur).first()
if vente is None:
    vente = Vente.objects.create(utilisateur=acteur, client=client)
    ligne = LigneVente.objects.create(vente=vente, medicament=medicament, quantite=4, prix_unitaire=150)
    confirmer_vente(vente.pk, acteur)
    payer(vente.pk, "600", "ESPECES", acteur)
    retour = RetourVente.objects.create(vente=vente, utilisateur=acteur, motif="Exemple fictif : emballage endommagé")
    LigneRetour.objects.create(retour=retour, ligne_vente=ligne, quantite=1)
    confirmer_retour(retour.pk, acteur)
    rembourser(retour.pk, "150", "Remboursement de démonstration", acteur)
retour = vente.retours.get()
paiement = vente.paiements.get()
remboursement = retour.remboursements.get()
commande = CommandeAchat.objects.filter(utilisateur=acteur).first()
if commande is None:
    commande = CommandeAchat.objects.create(fournisseur=fournisseur, utilisateur=acteur)
    ligne_achat = LigneAchat.objects.create(commande=commande, medicament=medicament, quantite=20, prix_unitaire=100)
    commander(commande.pk, acteur)
    reception = ReceptionAchat.objects.create(commande=commande, utilisateur=acteur)
    LigneReception.objects.create(reception=reception, ligne_achat=ligne_achat, numero_lot="DEMO-RECEPTION",
        date_peremption=timezone.localdate()+timedelta(days=365), quantite_recue=20)
    valider_reception(reception.pk)
reception = commande.receptions.filter(validee=True).first()
requete = RequestFactory().get("/")
requete.user = acteur
documents = {
    "facture": lambda: facture(requete, vente.pk, "facture"),
    "recu": lambda: recu(requete, paiement.pk),
    "retour": lambda: justificatif_retour(requete, retour.pk),
    "remboursement": lambda: justificatif_remboursement(requete, remboursement.pk),
    "rapport-ventes": generer_pdf_ventes,
    "rapport-stocks": generer_pdf_stock,
    "bon-commande": lambda: bon_commande(requete, commande.pk),
    "bon-reception": lambda: bon_reception(requete, reception.pk),
    "rapport-achats": lambda: telecharger_achats(requete),
    "liste-peremptions": lambda: telecharger_peremptions(requete),
}
import pymupdf
for nom, generer in documents.items():
    reponse = generer()
    fichier = DOSSIER / f"{nom}.pdf"
    fichier.write_bytes(b"".join(reponse.streaming_content))
    reponse.close()
    with pymupdf.open(fichier) as pdf:
        for numero, page in enumerate(pdf):
            page.get_pixmap(matrix=pymupdf.Matrix(1.2, 1.2)).save(DOSSIER / f"{nom}-{numero+1}.png")
    print(f"PDF rendu : {nom}")

if "--serve" in sys.argv:
    print("Revue sur http://127.0.0.1:8001/connexion/ — base fictive isolée.", flush=True)
    print(f"Compte temporaire : revue_locale ; mot de passe : {identifiants['password']}", flush=True)
    call_command("runserver", "127.0.0.1:8001", use_reloader=False)
