from django.test import TestCase

from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from medicaments.models import Categorie, Medicament
from stock.models import LotStock
from ventes.models import Vente, LigneVente
from ventes.services import valider_vente
from ventes.paiements import enregistrer_paiement

from .services import rapport_ventes, rapport_stock
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission

class RapportTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.utilisateur = User.objects.create_user(
            username="test_rapports",
            password="TestPassword123!"
        )

        self.categorie = Categorie.objects.create(
            nom="Categorie Rapports"
        )

        self.medicament = Medicament.objects.create(
            nom_commercial="Paracetamol Rapports",
            categorie=self.categorie,
            forme="comprime",
            dosage="500 mg",
            prix_achat=Decimal("100.00"),
            prix_vente=Decimal("150.00"),
            seuil_alerte=10,
        )

        self.lot = LotStock.objects.create(
            medicament=self.medicament,
            numero_lot="RAPPORT-001",
            date_peremption=timezone.localdate()
            + timedelta(days=20),
            quantite=20,
            quantite_recue=20,
        )

        self.vente = Vente.objects.create(
            utilisateur=self.utilisateur
        )

        LigneVente.objects.create(
            vente=self.vente,
            medicament=self.medicament,
            quantite=5,
            prix_unitaire=Decimal("150.00"),
        )

        valider_vente(self.vente.pk)

    def test_chiffre_affaires(self):
        rapport = rapport_ventes()

        self.assertEqual(
            rapport["chiffre_affaires"],
            Decimal("750.00"),
        )

    def test_nombre_ventes(self):
        rapport = rapport_ventes()

        self.assertEqual(rapport["nombre_ventes"], 1)

    def test_paiements(self):
        enregistrer_paiement(
            self.vente.pk,
            Decimal("300.00"),
            "ESPECES",
            self.utilisateur,
        )

        rapport = rapport_ventes()

        self.assertEqual(
            rapport["montant_encaisse"],
            Decimal("300.00"),
        )

        self.assertEqual(
            rapport["reste_a_payer"],
            Decimal("450.00"),
        )

    def test_lots_proches_peremption(self):
        rapport = rapport_stock()

        self.assertIn(
            self.lot,
            rapport["lots_proches_peremption"],
        )

    def test_lots_perimes(self):
        self.lot.date_peremption = (
            timezone.localdate() - timedelta(days=1)
        )
        self.lot.save(update_fields=["date_peremption"])

        rapport = rapport_stock()

        self.assertIn(
            self.lot,
            rapport["lots_perimes"],
        )

class RapportPermissionsTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.utilisateur = User.objects.create_user(
            username="employe_rapports",
            password="TestPassword123!"
        )

        self.url_ventes = reverse("rapport_ventes_pdf")
        self.url_stocks = reverse("rapport_stocks_pdf")

    def test_anonyme_redirige(self):
        response = self.client.get(self.url_ventes)
        self.assertEqual(response.status_code, 302)

    def test_ventes_interdit_sans_permission(self):
        self.client.force_login(self.utilisateur)

        response = self.client.get(self.url_ventes)

        self.assertEqual(response.status_code, 403)

    def test_stocks_interdit_sans_permission(self):
        self.client.force_login(self.utilisateur)

        response = self.client.get(self.url_stocks)

        self.assertEqual(response.status_code, 403)

    def test_ventes_autorise_avec_permission(self):
        permission = Permission.objects.get(
            codename="view_vente",
            content_type__app_label="ventes",
        )

        self.utilisateur.user_permissions.add(permission)
        self.client.force_login(self.utilisateur)

        response = self.client.get(self.url_ventes)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )
        self.assertTrue(b"".join(response.streaming_content).startswith(b"%PDF-"))
        response.close()

    def test_stocks_autorise_avec_permission(self):
        permission = Permission.objects.get(
            codename="view_lotstock",
            content_type__app_label="stock",
        )

        self.utilisateur.user_permissions.add(permission)
        self.client.force_login(self.utilisateur)

        response = self.client.get(self.url_stocks)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response["Content-Type"],
            "application/pdf",
        )
        self.assertTrue(b"".join(response.streaming_content).startswith(b"%PDF-"))
        response.close()

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class RapportPDFTests(TestCase):

    def setUp(self):
        User = get_user_model()

        self.admin = User.objects.create_superuser(
            username="admin_pdf_test",
            email="admin@example.com",
            password="TestPassword123!"
        )

        self.client.force_login(self.admin)

    def verifier_pdf(self, nom_url):
        response = self.client.get(reverse(nom_url))

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response["Content-Type"],
            "application/pdf"
        )

        contenu = b"".join(response.streaming_content)

        self.assertTrue(
            contenu.startswith(b"%PDF-"),
            "Le fichier généré n'est pas un PDF valide."
        )

        self.assertGreater(len(contenu), 100)

        response.close()

    def test_pdf_ventes(self):
        self.verifier_pdf("rapport_ventes_pdf")

    def test_pdf_stocks(self):
        self.verifier_pdf("rapport_stocks_pdf")
