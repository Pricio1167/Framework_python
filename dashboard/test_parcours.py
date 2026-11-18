from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from achats.models import CommandeAchat, ReceptionAchat
from fournisseurs.models import Fournisseur
from medicaments.models import Categorie, Medicament
from stock.models import LotStock
from ventes.models import Vente, RetourVente, Remboursement
from ventes.operations import solde


class ParcoursCompletsTests(TestCase):
    def setUp(self):
        self.utilisateur = get_user_model().objects.create_superuser("parcours", password="mot-de-passe-test")
        self.client.force_login(self.utilisateur)
        self.fournisseur = Fournisseur.objects.create(nom="Fournisseur test")
        categorie = Categorie.objects.create(nom="Catégorie test")
        self.medicament = Medicament.objects.create(
            nom_commercial="Médicament parcours", categorie=categorie, forme="comprime", dosage="500 mg",
            prix_achat=100, prix_vente=150,
        )

    def test_achat_reception_vente_retour_remboursement(self):
        reponse = self.client.post("/gestion/achats/ajouter/", {"fournisseur": self.fournisseur.pk})
        commande = CommandeAchat.objects.get()
        self.assertRedirects(reponse, reverse("gestion_detail", args=["achats", commande.pk]))
        self.assertEqual(self.client.post(reponse.url, {
            "medicament": self.medicament.pk, "quantite": 10, "prix_unitaire": "100",
        }).status_code, 302)
        self.client.post(reverse("gestion_operation", args=["achats", commande.pk]))
        commande.refresh_from_db()
        self.assertEqual(commande.statut, "COMMANDEE")

        reponse = self.client.post("/gestion/receptions/ajouter/", {"commande": commande.pk})
        reception = ReceptionAchat.objects.get()
        self.assertRedirects(reponse, reverse("gestion_detail", args=["receptions", reception.pk]))
        self.assertEqual(self.client.post(reponse.url, {
            "ligne_achat": commande.lignes.get().pk, "numero_lot": "PARCOURS-001",
            "date_peremption": (timezone.localdate() + timedelta(days=365)).isoformat(), "quantite_recue": 10,
        }).status_code, 302)
        self.client.post(reverse("gestion_operation", args=["receptions", reception.pk]))
        reception.refresh_from_db()
        self.assertTrue(reception.validee)
        lot = LotStock.objects.get()
        self.assertEqual(lot.quantite, 10)
        self.assertEqual(self.client.get(reverse("gestion_detail", args=["stocks", lot.pk])).status_code, 200)

        reponse = self.client.post(reverse("vente_creation"), {})
        vente = Vente.objects.get()
        self.assertRedirects(reponse, reverse("vente_detail", args=[vente.pk]))
        self.client.post(reverse("vente_ligne_ajouter", args=[vente.pk]), {
            "medicament": self.medicament.pk, "quantite": 4,
        })
        self.assertEqual(vente.lignes.count(), 1)
        self.client.post(reverse("vente_action", args=[vente.pk, "valider"]))
        vente.refresh_from_db()
        self.assertEqual(vente.statut, "VALIDEE")
        self.client.post(reverse("vente_action", args=[vente.pk, "payer"]), {"montant": "600", "mode": "ESPECES"})
        self.assertEqual(solde(vente)["reste"], Decimal("0"))

        self.client.post(reverse("vente_demander_retour", args=[vente.pk]), {
            f"quantite_{vente.lignes.get().pk}": 2, "motif": "Emballage altéré",
        })
        retour = RetourVente.objects.get()
        self.client.post(reverse("vente_action", args=[vente.pk, "retour"]), {"retour": retour.pk})
        self.client.post(reverse("vente_action", args=[vente.pk, "rembourser"]), {
            "retour": retour.pk, "montant": "300", "motif": "Remboursement du retour",
        })
        self.assertEqual(Remboursement.objects.get().montant, Decimal("300"))
        lot.refresh_from_db()
        self.assertEqual(lot.quantite, 6)
        self.assertEqual(self.client.get(reverse("vente_detail", args=[vente.pk])).status_code, 200)

    def test_rapports_filtres_et_periode_invalide(self):
        self.assertEqual(self.client.get(reverse("rapports_accueil")).status_code, 200)
        reponse = self.client.get(reverse("rapports_accueil"), {"date_debut": "2026-12-31", "date_fin": "2026-01-01"})
        self.assertContains(reponse, "La date de début doit précéder la date de fin.")
        self.assertEqual(self.client.get(reverse("rapport_ventes_pdf"), {"date_debut": "invalide"}).status_code, 400)

    def test_ajout_ligne_invalide_sans_erreur_serveur(self):
        vente = Vente.objects.create(utilisateur=self.utilisateur)
        reponse = self.client.post(reverse("vente_ligne_ajouter", args=[vente.pk]), {
            "medicament": self.medicament.pk, "quantite": -1,
        })
        self.assertEqual(reponse.status_code, 400)
        self.assertFalse(vente.lignes.exists())

    def test_suppression_ligne_depuis_la_vente(self):
        LotStock.objects.create(medicament=self.medicament, numero_lot="SUPPRESSION-BROUILLON", quantite=5,
                               date_peremption=timezone.localdate()+timedelta(days=30))
        vente = Vente.objects.create(utilisateur=self.utilisateur)
        self.client.post(reverse("vente_ligne_ajouter", args=[vente.pk]), {
            "medicament": self.medicament.pk, "quantite": 2,
        })
        ligne = vente.lignes.get()
        reponse = self.client.post(reverse("vente_ligne_supprimer", args=[vente.pk, ligne.pk]))
        self.assertRedirects(reponse, reverse("vente_detail", args=[vente.pk]))
        self.assertFalse(vente.lignes.exists())
