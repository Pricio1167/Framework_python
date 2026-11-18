from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase
from django.utils import timezone

from medicaments.models import Categorie, Medicament
from stock.models import LotStock
from ventes.models import Vente, LigneVente, RetourVente, LigneRetour, Paiement, Remboursement
from ventes.operations import confirmer_vente, confirmer_retour, payer, rembourser
from .templatetags.pharmagest import ariary


class FinalisationInterfaceTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.acteur = get_user_model().objects.create_superuser("finalisation")
        categorie = Categorie.objects.create(nom="Catégorie finale")
        cls.medicament = Medicament.objects.create(
            nom_commercial="Produit final", categorie=categorie, forme="comprime", dosage="1 mg",
            prix_achat=100, prix_vente=150,
        )
        LotStock.objects.create(medicament=cls.medicament, numero_lot="FINAL", quantite=20,
                               date_peremption=timezone.localdate()+timedelta(days=90))
        cls.vente = Vente.objects.create(utilisateur=cls.acteur)
        LigneVente.objects.create(vente=cls.vente, medicament=cls.medicament, quantite=4, prix_unitaire=150)

    def test_connexion_et_navigation_hors_ligne(self):
        reponse = self.client.get("/connexion/")
        self.assertContains(reponse, "Votre pharmacie.")
        self.assertContains(reponse, "/static/vendor/bootstrap/bootstrap.min.css")
        self.assertNotContains(reponse, "cdn.jsdelivr")
        self.client.force_login(self.acteur)
        reponse = self.client.get("/gestion/medicaments/")
        self.assertContains(reponse, 'aria-current="page"')
        self.assertContains(reponse, 'aria-controls="navigation-principale"')
        self.assertContains(reponse, "Stock disponible")

    def test_graphique_reel_et_masquage_sans_droits(self):
        confirmer_vente(self.vente.pk, self.acteur)
        self.client.force_login(self.acteur)
        reponse = self.client.get("/")
        self.assertEqual(reponse.status_code, 200)
        self.assertEqual(len(reponse.context["evolution"]), 7)
        self.assertEqual(Decimal(reponse.context["evolution"][-1]["brut"]), Decimal("600"))
        self.assertContains(reponse, 'id="evolution-ventes"')
        sans_droits = get_user_model().objects.create_user("aucun-droit-final")
        self.client.force_login(sans_droits)
        reponse = self.client.get("/")
        self.assertNotContains(reponse, 'id="evolution-ventes"')
        self.assertNotContains(reponse, "chart.umd.js")

    def test_filtre_et_recherche_relationnelle(self):
        self.client.force_login(self.acteur)
        reponse = self.client.get("/gestion/stocks/", {"q": "Produit final", "tri": "peremption"})
        self.assertEqual(reponse.context["page"].paginator.count, 1)
        reponse = self.client.get("/gestion/ventes/", {"etat": "VALIDEE"})
        self.assertEqual(reponse.context["page"].paginator.count, 0)
        self.assertEqual(self.client.get("/gestion/ventes/", {"tri": "statut;DROP"}).status_code, 200)

    def test_paiement_rejoue_une_seule_fois(self):
        confirmer_vente(self.vente.pk, self.acteur)
        cle = uuid4()
        premier = payer(self.vente.pk, "100", "ESPECES", self.acteur, cle_operation=cle)
        second = payer(self.vente.pk, "100", "ESPECES", self.acteur, cle_operation=cle)
        self.assertEqual(premier.pk, second.pk)
        self.assertEqual(Paiement.objects.count(), 1)
        with self.assertRaises(ValidationError):
            payer(self.vente.pk, "200", "ESPECES", self.acteur, cle_operation=cle)

    def test_remboursement_rejoue_une_seule_fois(self):
        confirmer_vente(self.vente.pk, self.acteur)
        payer(self.vente.pk, "600", "ESPECES", self.acteur)
        retour = RetourVente.objects.create(vente=self.vente, utilisateur=self.acteur, motif="Retour")
        LigneRetour.objects.create(retour=retour, ligne_vente=self.vente.lignes.get(), quantite=2)
        confirmer_retour(retour.pk, self.acteur)
        cle = uuid4()
        premier = rembourser(retour.pk, "100", "Retour", self.acteur, cle_operation=cle)
        second = rembourser(retour.pk, "100", "Retour", self.acteur, cle_operation=cle)
        self.assertEqual(premier.pk, second.pk)
        self.assertEqual(Remboursement.objects.count(), 1)

    def test_double_soumission_web(self):
        confirmer_vente(self.vente.pk, self.acteur)
        self.client.force_login(self.acteur)
        contexte = self.client.get(f"/ventes/{self.vente.pk}/").context
        donnees = {"montant": "100", "mode": "ESPECES", "cle_operation": str(contexte["cle_paiement"])}
        for _ in range(2):
            self.assertEqual(self.client.post(f"/ventes/{self.vente.pk}/payer/", donnees).status_code, 302)
        self.assertEqual(Paiement.objects.count(), 1)

    def test_format_montant(self):
        self.assertEqual(ariary(Decimal("12000.50")), "12 000,50 Ar")
        self.assertEqual(ariary("NaN"), "—")
